package network.nerava.app.notifications

import android.app.NotificationManager
import android.content.Context
import androidx.core.app.NotificationCompat
import network.nerava.app.NeravaApplication
import network.nerava.app.R

/**
 * Helper for showing local notifications. Mirrors iOS NotificationService.
 */
object NotificationHelper {

    private const val SESSION_NOTIFICATION_ID = 2001
    private const val MERCHANT_NOTIFICATION_ID = 2002

    fun showSessionActive(context: Context) {
        show(
            context,
            id = SESSION_NOTIFICATION_ID,
            title = "You're all set!",
            body = "Head to the merchant to unlock your exclusive deal.",
            channel = NeravaApplication.CHANNEL_SESSION,
        )
    }

    fun showAtMerchant(context: Context) {
        show(
            context,
            id = MERCHANT_NOTIFICATION_ID,
            title = "You've arrived!",
            body = "Show your code to the merchant to redeem your exclusive.",
            channel = NeravaApplication.CHANNEL_SESSION,
        )
    }

    private fun show(context: Context, id: Int, title: String, body: String, channel: String) {
        val notification = NotificationCompat.Builder(context, channel)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(body)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .build()

        val manager = context.getSystemService(NotificationManager::class.java)
        manager.notify(id, notification)
    }
}
