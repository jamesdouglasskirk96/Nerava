package network.nerava.app.notifications

import android.util.Log
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import network.nerava.app.NeravaApplication
import network.nerava.app.bridge.NativeBridge

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

        // Cache for later forwarding and send to web bridge
        cachedToken = token
        NativeBridge.activeBridge?.sendDeviceToken(token)
    }

    override fun onMessageReceived(message: RemoteMessage) {
        Log.i(TAG, "FCM message received: ${message.data}")

        val data = message.data

        // Check for session-related push
        val type = data["type"]
        val deepLink = data["deep_link"]

        // Forward deep link to web bridge if present
        if (type != null && deepLink != null) {
            NativeBridge.activeBridge?.sendToWeb(
                network.nerava.app.bridge.BridgeMessage.PushDeepLink(type, deepLink)
            )
        }

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

        /** Cached FCM token for forwarding to web bridge after bridge is ready. */
        @Volatile
        var cachedToken: String? = null
    }
}
