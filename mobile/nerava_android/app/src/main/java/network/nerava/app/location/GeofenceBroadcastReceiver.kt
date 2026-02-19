package network.nerava.app.location

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.google.android.gms.location.Geofence
import com.google.android.gms.location.GeofencingEvent

/**
 * Receives geofence transition events from the OS.
 * Forwards them to the session engine via a local broadcast or callback.
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

        for (geofence in event.triggeringGeofences ?: emptyList()) {
            val id = geofence.requestId
            Log.i(TAG, "Geofence transition: $transitionName for $id")

            // Broadcast locally so SessionEngine can pick it up
            val localIntent = Intent(ACTION_GEOFENCE_EVENT).apply {
                putExtra(EXTRA_REGION_ID, id)
                putExtra(EXTRA_TRANSITION, transition)
                putExtra(EXTRA_LAT, event.triggeringLocation?.latitude ?: 0.0)
                putExtra(EXTRA_LNG, event.triggeringLocation?.longitude ?: 0.0)
            }
            context.sendBroadcast(localIntent)
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
