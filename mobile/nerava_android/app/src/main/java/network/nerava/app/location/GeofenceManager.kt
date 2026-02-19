package network.nerava.app.location

import android.Manifest
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.util.Log
import androidx.core.content.ContextCompat
import com.google.android.gms.location.Geofence
import com.google.android.gms.location.GeofencingClient
import com.google.android.gms.location.GeofencingRequest
import com.google.android.gms.location.LocationServices

/**
 * Manages geofence regions for charger and merchant zones.
 * Mirrors iOS GeofenceManager:
 * - Max 2 active regions (FIFO eviction)
 * - Charger: entry + exit
 * - Merchant: entry only
 */
class GeofenceManager(private val context: Context) {

    private val geofencingClient: GeofencingClient =
        LocationServices.getGeofencingClient(context)

    private val regionOrder = mutableListOf<String>()

    private val geofencePendingIntent: PendingIntent by lazy {
        val intent = Intent(context, GeofenceBroadcastReceiver::class.java)
        PendingIntent.getBroadcast(
            context, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE
        )
    }

    var onGeofenceEvent: ((String, Int) -> Unit)? = null

    fun addChargerGeofence(id: String, lat: Double, lng: Double, radiusM: Float) {
        val identifier = "charger_$id"
        addGeofence(
            identifier = identifier,
            lat = lat,
            lng = lng,
            radiusM = radiusM.coerceAtMost(MAX_RADIUS),
            transitionTypes = Geofence.GEOFENCE_TRANSITION_ENTER or Geofence.GEOFENCE_TRANSITION_EXIT,
        )
    }

    fun addMerchantGeofence(id: String, lat: Double, lng: Double, radiusM: Float) {
        val identifier = "merchant_$id"
        addGeofence(
            identifier = identifier,
            lat = lat,
            lng = lng,
            radiusM = radiusM.coerceAtMost(MAX_RADIUS),
            transitionTypes = Geofence.GEOFENCE_TRANSITION_ENTER,
        )
    }

    private fun addGeofence(
        identifier: String,
        lat: Double,
        lng: Double,
        radiusM: Float,
        transitionTypes: Int,
    ) {
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION)
            != PackageManager.PERMISSION_GRANTED
        ) {
            Log.w(TAG, "No location permission for geofencing")
            return
        }

        // FIFO eviction: max 2 active regions
        while (regionOrder.size >= MAX_ACTIVE_REGIONS) {
            val oldest = regionOrder.removeAt(0)
            removeGeofence(oldest)
        }

        val geofence = Geofence.Builder()
            .setRequestId(identifier)
            .setCircularRegion(lat, lng, radiusM)
            .setExpirationDuration(Geofence.NEVER_EXPIRE)
            .setTransitionTypes(transitionTypes)
            // Dwell detection: 120s loiter delay to avoid drive-by triggers
            .setLoiteringDelay(DWELL_DELAY_MS)
            .build()

        val request = GeofencingRequest.Builder()
            .setInitialTrigger(GeofencingRequest.INITIAL_TRIGGER_ENTER)
            .addGeofence(geofence)
            .build()

        geofencingClient.addGeofences(request, geofencePendingIntent)
            .addOnSuccessListener {
                regionOrder.add(identifier)
                Log.i(TAG, "Geofence added: $identifier (${String.format("%.4f", lat)}, ${String.format("%.4f", lng)}, r=${radiusM}m)")
            }
            .addOnFailureListener { e ->
                Log.e(TAG, "Failed to add geofence: $identifier", e)
            }
    }

    fun removeGeofence(identifier: String) {
        geofencingClient.removeGeofences(listOf(identifier))
            .addOnSuccessListener {
                regionOrder.remove(identifier)
                Log.i(TAG, "Geofence removed: $identifier")
            }
            .addOnFailureListener { e ->
                Log.e(TAG, "Failed to remove geofence: $identifier", e)
            }
    }

    fun removeAllGeofences() {
        geofencingClient.removeGeofences(geofencePendingIntent)
            .addOnSuccessListener {
                regionOrder.clear()
                Log.i(TAG, "All geofences removed")
            }
            .addOnFailureListener { e ->
                Log.e(TAG, "Failed to remove all geofences", e)
            }
    }

    val activeRegionCount: Int get() = regionOrder.size
    val activeRegions: List<String> get() = regionOrder.toList()

    companion object {
        private const val TAG = "GeofenceManager"
        private const val MAX_ACTIVE_REGIONS = 2
        private const val MAX_RADIUS = 1000f // meters
        private const val DWELL_DELAY_MS = 120_000 // 120 seconds — matches iOS dwell detection
    }
}
