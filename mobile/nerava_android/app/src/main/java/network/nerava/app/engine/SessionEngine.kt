package network.nerava.app.engine

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.location.Location
import android.os.Handler
import android.os.Looper
import android.util.Log
import com.google.android.gms.location.Geofence
import network.nerava.app.auth.SecureTokenStore
import network.nerava.app.bridge.BridgeMessage
import network.nerava.app.bridge.NativeBridge
import network.nerava.app.location.GeofenceBroadcastReceiver
import network.nerava.app.location.GeofenceManager
import network.nerava.app.location.LocationForegroundService
import network.nerava.app.location.LocationService
import network.nerava.app.network.APIClient
import java.util.Date
import java.util.UUID
import java.util.concurrent.Executors
import kotlin.math.*

/**
 * Core session state machine. Mirrors iOS SessionEngine exactly.
 *
 * States: IDLE → NEAR_CHARGER → ANCHORED → SESSION_ACTIVE → IN_TRANSIT → AT_MERCHANT → SESSION_ENDED
 */
class SessionEngine(
    private val context: Context,
    private val locationService: LocationService,
    private val geofenceManager: GeofenceManager,
    private val tokenStore: SecureTokenStore,
    private val apiClient: APIClient,
) {
    var bridge: NativeBridge? = null

    var currentState: SessionState = SessionState.IDLE
        private set

    private var config = SessionConfig.DEFAULTS
    private val dwellDetector = DwellDetector(config)
    private val snapshot = SessionSnapshot(context)
    private val mainHandler = Handler(Looper.getMainLooper())
    private val ioExecutor = Executors.newSingleThreadExecutor()

    private var chargerTarget: ChargerTarget? = null
    private var merchantTarget: MerchantTarget? = null
    private var activeSession: ActiveSessionInfo? = null

    private var gracePeriodDeadline: Long? = null
    private var hardTimeoutDeadline: Long? = null
    private var gracePeriodRunnable: Runnable? = null
    private var hardTimeoutRunnable: Runnable? = null

    // Geofence broadcast receiver
    private val geofenceReceiver = object : BroadcastReceiver() {
        override fun onReceive(ctx: Context, intent: Intent) {
            val regionId = intent.getStringExtra(GeofenceBroadcastReceiver.EXTRA_REGION_ID) ?: return
            val transition = intent.getIntExtra(GeofenceBroadcastReceiver.EXTRA_TRANSITION, -1)
            handleGeofenceEvent(regionId, transition)
        }
    }

    fun start() {
        // Register for geofence events
        context.registerReceiver(
            geofenceReceiver,
            IntentFilter(GeofenceBroadcastReceiver.ACTION_GEOFENCE_EVENT),
            Context.RECEIVER_NOT_EXPORTED,
        )

        // Set up location callback
        locationService.onLocationUpdate = { location -> onLocationUpdate(location) }

        // Fetch remote config
        ioExecutor.execute {
            try {
                config = apiClient.fetchConfig()
                Log.i(TAG, "Remote config loaded")
            } catch (e: Exception) {
                Log.w(TAG, "Using default config: ${e.message}")
            }
        }

        // Restore from snapshot
        restoreFromSnapshot()

        // Start location updates
        locationService.startLocationUpdates()
    }

    fun stop() {
        try { context.unregisterReceiver(geofenceReceiver) } catch (_: Exception) {}
        locationService.stopLocationUpdates()
        cancelGracePeriod()
        cancelHardTimeout()
    }

    // MARK: - Web → Native Actions

    fun setChargerTarget(chargerId: String, lat: Double, lng: Double) {
        val target = ChargerTarget(chargerId, lat, lng)
        chargerTarget = target

        // Switch to high-accuracy location
        locationService.switchToHighAccuracy()

        // Set up charger geofence
        geofenceManager.addChargerGeofence(chargerId, lat, lng, config.chargerIntentRadiusM.toFloat())

        // Emit event
        emitPreSessionEvent(SessionEvent.CHARGER_TARGETED, chargerId)

        if (currentState == SessionState.IDLE) {
            // Check if already within intent radius
            locationService.currentLocation?.let { loc ->
                val dist = haversineM(loc.latitude, loc.longitude, lat, lng)
                if (dist <= config.chargerIntentRadiusM) {
                    transition(SessionState.NEAR_CHARGER, SessionEvent.ENTERED_CHARGER_INTENT_ZONE)
                }
            }
        }
    }

    fun setAuthToken(token: String) {
        tokenStore.setAccessToken(token)
        apiClient.accessToken = token
    }

    fun webConfirmsExclusiveActivated(sessionId: String, merchantId: String, merchantLat: Double, merchantLng: Double) {
        if (currentState != SessionState.ANCHORED) {
            bridge?.sendToWeb(BridgeMessage.SessionStartRejected("NOT_ANCHORED"))
            emitPreSessionEvent(SessionEvent.ACTIVATION_REJECTED, chargerTarget?.id)
            return
        }

        val chargerId = chargerTarget?.id ?: return
        merchantTarget = MerchantTarget(merchantId, merchantLat, merchantLng)
        activeSession = ActiveSessionInfo(sessionId, chargerId, merchantId, System.currentTimeMillis())

        // Set up merchant geofence
        geofenceManager.addMerchantGeofence(merchantId, merchantLat, merchantLng, config.merchantUnlockRadiusM.toFloat())

        transition(SessionState.SESSION_ACTIVE, SessionEvent.EXCLUSIVE_ACTIVATED)

        // Start hard timeout
        startHardTimeout()

        // Start foreground service for background location
        startForegroundService()
    }

    fun webConfirmsVisitVerified(sessionId: String, verificationCode: String) {
        transition(SessionState.SESSION_ENDED, SessionEvent.VISIT_VERIFIED)
        cleanupSession()
    }

    fun webRequestsSessionEnd() {
        transition(SessionState.SESSION_ENDED, SessionEvent.WEB_REQUESTED_END)
        cleanupSession()
    }

    // MARK: - Location Callback

    private fun onLocationUpdate(location: Location) {
        val target = chargerTarget ?: return

        if (location.accuracy > config.locationAccuracyThresholdM) return

        val distToCharger = haversineM(location.latitude, location.longitude, target.latitude, target.longitude)

        when (currentState) {
            SessionState.IDLE -> {
                if (distToCharger <= config.chargerIntentRadiusM) {
                    transition(SessionState.NEAR_CHARGER, SessionEvent.ENTERED_CHARGER_INTENT_ZONE)
                }
            }

            SessionState.NEAR_CHARGER -> {
                dwellDetector.recordLocation(location, distToCharger)
                if (dwellDetector.isAnchored) {
                    transition(SessionState.ANCHORED, SessionEvent.ANCHOR_DWELL_COMPLETE)
                }
                if (distToCharger > config.chargerIntentRadiusM + config.locationAccuracyThresholdM) {
                    dwellDetector.reset()
                    transition(SessionState.IDLE, SessionEvent.EXITED_CHARGER_INTENT_ZONE)
                }
            }

            SessionState.ANCHORED -> {
                if (distToCharger > config.chargerAnchorRadiusM + config.locationAccuracyThresholdM) {
                    dwellDetector.reset()
                    transition(SessionState.NEAR_CHARGER, SessionEvent.ANCHOR_LOST)
                }
            }

            SessionState.SESSION_ACTIVE -> {
                if (distToCharger > config.chargerAnchorRadiusM + config.locationAccuracyThresholdM) {
                    transition(SessionState.IN_TRANSIT, SessionEvent.DEPARTED_CHARGER)
                    startGracePeriod()
                }
            }

            SessionState.IN_TRANSIT -> {
                val merchant = merchantTarget
                if (merchant != null) {
                    val distToMerchant = haversineM(location.latitude, location.longitude, merchant.latitude, merchant.longitude)
                    if (distToMerchant <= config.merchantUnlockRadiusM) {
                        cancelGracePeriod()
                        transition(SessionState.AT_MERCHANT, SessionEvent.ENTERED_MERCHANT_ZONE)
                    }
                }
            }

            SessionState.AT_MERCHANT -> {
                // Waiting for web to confirm visit
            }

            SessionState.SESSION_ENDED -> {
                // Terminal state
            }
        }

        saveSnapshot()
    }

    // MARK: - Geofence Handling

    private fun handleGeofenceEvent(regionId: String, transition: Int) {
        Log.i(TAG, "Geofence event: $regionId, transition=$transition")

        when {
            regionId.startsWith("charger_") && transition == Geofence.GEOFENCE_TRANSITION_ENTER -> {
                if (currentState == SessionState.IDLE) {
                    transition(SessionState.NEAR_CHARGER, SessionEvent.ENTERED_CHARGER_INTENT_ZONE)
                }
            }
            regionId.startsWith("charger_") && transition == Geofence.GEOFENCE_TRANSITION_EXIT -> {
                if (currentState == SessionState.SESSION_ACTIVE) {
                    transition(SessionState.IN_TRANSIT, SessionEvent.DEPARTED_CHARGER)
                    startGracePeriod()
                }
            }
            regionId.startsWith("merchant_") && transition == Geofence.GEOFENCE_TRANSITION_ENTER -> {
                if (currentState == SessionState.IN_TRANSIT) {
                    cancelGracePeriod()
                    transition(SessionState.AT_MERCHANT, SessionEvent.ENTERED_MERCHANT_ZONE)
                }
            }
        }
    }

    // MARK: - State Transitions

    private fun transition(newState: SessionState, event: SessionEvent) {
        val oldState = currentState
        if (oldState == newState) return

        Log.i(TAG, "Transition: ${oldState.raw} → ${newState.raw} (${event.raw})")
        currentState = newState

        // Notify web via bridge
        bridge?.sendToWeb(BridgeMessage.SessionStateChanged(newState.raw))

        // Emit event to backend
        val metadata = mapOf("previous_state" to oldState.raw, "new_state" to newState.raw)
        if (event.requiresSessionId) {
            val sessionId = activeSession?.sessionId
            if (sessionId != null) {
                emitSessionEvent(sessionId, event, metadata)
            }
        } else {
            emitPreSessionEvent(event, chargerTarget?.id, metadata)
        }

        saveSnapshot()
    }

    // MARK: - Timer Management

    private fun startGracePeriod() {
        cancelGracePeriod()
        val delayMs = config.gracePeriodSeconds * 1000L
        gracePeriodDeadline = System.currentTimeMillis() + delayMs

        val runnable = Runnable {
            if (currentState == SessionState.IN_TRANSIT) {
                transition(SessionState.SESSION_ENDED, SessionEvent.GRACE_PERIOD_EXPIRED)
                cleanupSession()
            }
        }
        gracePeriodRunnable = runnable
        mainHandler.postDelayed(runnable, delayMs)
    }

    private fun cancelGracePeriod() {
        gracePeriodRunnable?.let { mainHandler.removeCallbacks(it) }
        gracePeriodRunnable = null
        gracePeriodDeadline = null
    }

    private fun startHardTimeout() {
        cancelHardTimeout()
        val delayMs = config.hardTimeoutSeconds * 1000L
        hardTimeoutDeadline = System.currentTimeMillis() + delayMs

        val runnable = Runnable {
            if (currentState != SessionState.IDLE && currentState != SessionState.SESSION_ENDED) {
                transition(SessionState.SESSION_ENDED, SessionEvent.HARD_TIMEOUT_EXPIRED)
                cleanupSession()
            }
        }
        hardTimeoutRunnable = runnable
        mainHandler.postDelayed(runnable, delayMs)
    }

    private fun cancelHardTimeout() {
        hardTimeoutRunnable?.let { mainHandler.removeCallbacks(it) }
        hardTimeoutRunnable = null
        hardTimeoutDeadline = null
    }

    // MARK: - Session Cleanup

    private fun cleanupSession() {
        cancelGracePeriod()
        cancelHardTimeout()
        geofenceManager.removeAllGeofences()
        dwellDetector.reset()
        locationService.switchToLowAccuracy()
        stopForegroundService()

        chargerTarget = null
        merchantTarget = null
        activeSession = null

        snapshot.clear()
    }

    // MARK: - Foreground Service

    private fun startForegroundService() {
        val intent = Intent(context, LocationForegroundService::class.java).apply {
            action = LocationForegroundService.ACTION_START
        }
        context.startForegroundService(intent)
    }

    private fun stopForegroundService() {
        val intent = Intent(context, LocationForegroundService::class.java).apply {
            action = LocationForegroundService.ACTION_STOP
        }
        context.startService(intent)
    }

    // MARK: - Event Emission

    private fun emitSessionEvent(sessionId: String, event: SessionEvent, metadata: Map<String, String>? = null) {
        val eventId = UUID.randomUUID().toString()
        val appState = "foreground" // Simplified; could check ProcessLifecycleOwner
        ioExecutor.execute {
            try {
                apiClient.emitSessionEvent(sessionId, event.raw, eventId, Date(), appState, metadata)
            } catch (e: APIClient.AuthRequiredException) {
                bridge?.sendToWeb(BridgeMessage.AuthRequired)
            } catch (e: Exception) {
                Log.e(TAG, "Failed to emit session event: ${event.raw}", e)
                bridge?.sendToWeb(BridgeMessage.EventEmissionFailed(event.raw, e.message ?: "Unknown error"))
            }
        }
    }

    private fun emitPreSessionEvent(event: SessionEvent, chargerId: String?, metadata: Map<String, String>? = null) {
        val eventId = UUID.randomUUID().toString()
        ioExecutor.execute {
            try {
                apiClient.emitPreSessionEvent(event.raw, chargerId, eventId, Date(), metadata)
            } catch (e: APIClient.AuthRequiredException) {
                bridge?.sendToWeb(BridgeMessage.AuthRequired)
            } catch (e: Exception) {
                Log.e(TAG, "Failed to emit pre-session event: ${event.raw}", e)
                bridge?.sendToWeb(BridgeMessage.EventEmissionFailed(event.raw, e.message ?: "Unknown error"))
            }
        }
    }

    // MARK: - Snapshot Persistence

    private fun saveSnapshot() {
        snapshot.save(
            state = currentState,
            chargerTarget = chargerTarget,
            merchantTarget = merchantTarget,
            activeSession = activeSession,
            gracePeriodDeadline = gracePeriodDeadline,
            hardTimeoutDeadline = hardTimeoutDeadline,
        )
    }

    private fun restoreFromSnapshot() {
        val data = snapshot.restore() ?: return

        // Check if snapshot is stale (>2 hours)
        if (System.currentTimeMillis() - data.savedAt > 2 * 60 * 60 * 1000) {
            Log.w(TAG, "Snapshot too old, discarding")
            snapshot.clear()
            return
        }

        currentState = data.state
        chargerTarget = data.chargerTarget
        merchantTarget = data.merchantTarget
        activeSession = data.activeSession

        // Rebuild timers
        val now = System.currentTimeMillis()
        data.gracePeriodDeadline?.let { deadline ->
            if (deadline > now) {
                gracePeriodDeadline = deadline
                val remaining = deadline - now
                val runnable = Runnable {
                    if (currentState == SessionState.IN_TRANSIT) {
                        transition(SessionState.SESSION_ENDED, SessionEvent.GRACE_PERIOD_EXPIRED)
                        cleanupSession()
                    }
                }
                gracePeriodRunnable = runnable
                mainHandler.postDelayed(runnable, remaining)
            } else {
                // Deadline passed while app was dead
                if (currentState == SessionState.IN_TRANSIT) {
                    transition(SessionState.SESSION_ENDED, SessionEvent.GRACE_PERIOD_EXPIRED)
                    cleanupSession()
                    return
                }
            }
        }

        data.hardTimeoutDeadline?.let { deadline ->
            if (deadline > now) {
                hardTimeoutDeadline = deadline
                val remaining = deadline - now
                val runnable = Runnable {
                    transition(SessionState.SESSION_ENDED, SessionEvent.HARD_TIMEOUT_EXPIRED)
                    cleanupSession()
                }
                hardTimeoutRunnable = runnable
                mainHandler.postDelayed(runnable, remaining)
            } else {
                transition(SessionState.SESSION_ENDED, SessionEvent.HARD_TIMEOUT_EXPIRED)
                cleanupSession()
                return
            }
        }

        // Rebuild geofences
        chargerTarget?.let {
            geofenceManager.addChargerGeofence(it.id, it.latitude, it.longitude, config.chargerIntentRadiusM.toFloat())
        }
        merchantTarget?.let {
            geofenceManager.addMerchantGeofence(it.id, it.latitude, it.longitude, config.merchantUnlockRadiusM.toFloat())
        }

        // Re-emit session restored if in an active state
        if (currentState != SessionState.IDLE && currentState != SessionState.SESSION_ENDED) {
            activeSession?.sessionId?.let { sid ->
                emitSessionEvent(sid, SessionEvent.SESSION_RESTORED)
            }
            if (currentState.ordinal >= SessionState.SESSION_ACTIVE.ordinal) {
                startForegroundService()
                locationService.switchToHighAccuracy()
            }
        }

        // Notify web
        bridge?.sendToWeb(BridgeMessage.SessionStateChanged(currentState.raw))

        Log.i(TAG, "Restored session: ${currentState.raw}")
    }

    companion object {
        private const val TAG = "SessionEngine"

        /**
         * Haversine distance in meters between two lat/lng points.
         */
        fun haversineM(lat1: Double, lng1: Double, lat2: Double, lng2: Double): Double {
            val r = 6_371_000.0 // Earth radius in meters
            val dLat = Math.toRadians(lat2 - lat1)
            val dLng = Math.toRadians(lng2 - lng1)
            val a = sin(dLat / 2).pow(2) +
                    cos(Math.toRadians(lat1)) * cos(Math.toRadians(lat2)) * sin(dLng / 2).pow(2)
            return 2 * r * asin(sqrt(a))
        }
    }
}
