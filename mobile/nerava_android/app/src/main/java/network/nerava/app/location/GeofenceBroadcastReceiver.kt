package network.nerava.app.location

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.google.android.gms.location.Geofence
import com.google.android.gms.location.GeofencingEvent
import network.nerava.app.auth.SecureTokenStore
import network.nerava.app.network.APIClient

/**
 * Receives geofence transition events from the OS.
 * Forwards them to the session engine via a local broadcast or callback.
 *
 * For charger ENTER transitions, also sends a background-ping directly to the
 * backend. This handles the killed-app case where SessionEngine may not be
 * running to receive the local broadcast. Uses goAsync() to extend execution
 * beyond the default 10-second BroadcastReceiver limit.
 */
class GeofenceBroadcastReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        val event = GeofencingEvent.fromIntent(intent)

        if (event == null) {
            Log.e(TAG, "GeofencingEvent is null")
            return
        }

        if (event.hasError()) {
            Log.e(TAG, "Geofence error: ${event.errorCode}")
            return
        }

        val transition = event.geofenceTransition
        val transitionName = when (transition) {
            Geofence.GEOFENCE_TRANSITION_ENTER -> "ENTER"
            Geofence.GEOFENCE_TRANSITION_EXIT -> "EXIT"
            Geofence.GEOFENCE_TRANSITION_DWELL -> "DWELL"
            else -> "UNKNOWN($transition)"
        }

        val lat = event.triggeringLocation?.latitude ?: 0.0
        val lng = event.triggeringLocation?.longitude ?: 0.0
        var hasChargerEntry = false

        for (geofence in event.triggeringGeofences ?: emptyList()) {
            val id = geofence.requestId
            Log.i(TAG, "Geofence transition: $transitionName for $id")

            // Broadcast locally so SessionEngine can pick it up
            val localIntent = Intent(ACTION_GEOFENCE_EVENT).apply {
                putExtra(EXTRA_REGION_ID, id)
                putExtra(EXTRA_TRANSITION, transition)
                putExtra(EXTRA_LAT, lat)
                putExtra(EXTRA_LNG, lng)
            }
            context.sendBroadcast(localIntent)

            if (id.startsWith("charger_") && transition == Geofence.GEOFENCE_TRANSITION_ENTER) {
                hasChargerEntry = true
            }
        }

        // For charger entries, send background-ping directly to backend.
        // This ensures charging detection works even if the app process was killed
        // and SessionEngine isn't running to handle the local broadcast.
        if (hasChargerEntry && lat != 0.0 && lng != 0.0) {
            val pendingResult = goAsync()
            Thread {
                try {
                    val tokenStore = SecureTokenStore(context)
                    val authToken = tokenStore.getAccessToken()
                    if (authToken != null) {
                        val apiClient = APIClient()
                        apiClient.sendBackgroundPing(lat, lng, authToken = authToken)
                    } else {
                        Log.w(TAG, "No auth token for background ping, skipping")
                    }
                } catch (e: Exception) {
                    Log.w(TAG, "Background ping from receiver failed: ${e.message}")
                } finally {
                    pendingResult.finish()
                }
            }.start()
        }
    }

    companion object {
        private const val TAG = "GeofenceReceiver"
        const val ACTION_GEOFENCE_EVENT = "network.nerava.app.GEOFENCE_EVENT"
        const val EXTRA_REGION_ID = "region_id"
        const val EXTRA_TRANSITION = "transition"
        const val EXTRA_LAT = "lat"
        const val EXTRA_LNG = "lng"
    }
}
