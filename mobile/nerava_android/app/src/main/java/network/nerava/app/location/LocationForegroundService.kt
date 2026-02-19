package network.nerava.app.location

import android.app.Notification
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import network.nerava.app.MainActivity
import network.nerava.app.NeravaApplication
import network.nerava.app.R

/**
 * Foreground service for background location updates.
 * Required on Android 10+ for continuous location access when the app is backgrounded.
 *
 * Started when a session becomes active; stopped when session ends.
 */
class LocationForegroundService : Service() {

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> {
                Log.i(TAG, "Starting foreground location service")
                startForeground(NOTIFICATION_ID, buildNotification())
            }
            ACTION_STOP -> {
                Log.i(TAG, "Stopping foreground location service")
                stopForeground(STOP_FOREGROUND_REMOVE)
                stopSelf()
            }
        }
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun buildNotification(): Notification {
        val tapIntent = Intent(this, MainActivity::class.java)
        val pendingTap = PendingIntent.getActivity(
            this, 0, tapIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, NeravaApplication.CHANNEL_FOREGROUND)
            .setContentTitle(getString(R.string.foreground_service_title))
            .setContentText(getString(R.string.foreground_service_text))
            .setSmallIcon(R.drawable.ic_notification)
            .setContentIntent(pendingTap)
            .setOngoing(true)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .build()
    }

    companion object {
        private const val TAG = "LocationFgService"
        private const val NOTIFICATION_ID = 1001
        const val ACTION_START = "network.nerava.app.location.START"
        const val ACTION_STOP = "network.nerava.app.location.STOP"
    }
}
