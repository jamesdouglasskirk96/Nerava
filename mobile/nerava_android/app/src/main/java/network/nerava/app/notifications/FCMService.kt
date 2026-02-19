package network.nerava.app.notifications

import android.util.Log
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import network.nerava.app.NeravaApplication

/**
 * Firebase Cloud Messaging service.
 * Handles incoming push notifications and device token refresh.
 *
 * Note: iOS does NOT currently wire APNs tokens to backend.
 * This implementation is ready for when backend adds token registration.
 */
class FCMService : FirebaseMessagingService() {

    override fun onNewToken(token: String) {
        Log.i(TAG, "FCM token refreshed: ${token.take(10)}...")

        // Store token locally
        val app = application as NeravaApplication
        app.tokenStore.setFCMToken(token)

        // TODO: When backend adds POST /v1/notifications/register-device,
        // send { platform: "android", token: token } here.
    }

    override fun onMessageReceived(message: RemoteMessage) {
        Log.i(TAG, "FCM message received: ${message.data}")

        val data = message.data

        // Check for session-related push
        val type = data["type"]
        val sessionId = data["session_id"]

        when (type) {
            "session_update" -> {
                NotificationHelper.showSessionActive(this)
            }
            "merchant_arrival" -> {
                NotificationHelper.showAtMerchant(this)
            }
            else -> {
                // Show generic notification from the message payload
                message.notification?.let { notification ->
                    val title = notification.title ?: "Nerava"
                    val body = notification.body ?: ""
                    showGenericNotification(title, body)
                }
            }
        }
    }

    private fun showGenericNotification(title: String, body: String) {
        val notification = androidx.core.app.NotificationCompat.Builder(this, NeravaApplication.CHANNEL_GENERAL)
            .setSmallIcon(network.nerava.app.R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(body)
            .setPriority(androidx.core.app.NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .build()

        val manager = getSystemService(android.app.NotificationManager::class.java)
        manager.notify(System.currentTimeMillis().toInt(), notification)
    }

    companion object {
        private const val TAG = "FCMService"
    }
}
