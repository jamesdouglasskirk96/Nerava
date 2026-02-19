package network.nerava.app

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import network.nerava.app.auth.SecureTokenStore

class NeravaApplication : Application() {

    lateinit var tokenStore: SecureTokenStore
        private set

    override fun onCreate() {
        super.onCreate()
        tokenStore = SecureTokenStore(this)
        createNotificationChannels()
    }

    private fun createNotificationChannels() {
        val manager = getSystemService(NotificationManager::class.java)

        val sessionChannel = NotificationChannel(
            CHANNEL_SESSION,
            getString(R.string.notification_channel_session),
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = getString(R.string.notification_channel_session_desc)
            enableVibration(true)
        }

        val generalChannel = NotificationChannel(
            CHANNEL_GENERAL,
            getString(R.string.notification_channel_general),
            NotificationManager.IMPORTANCE_DEFAULT
        ).apply {
            description = getString(R.string.notification_channel_general_desc)
        }

        val foregroundChannel = NotificationChannel(
            CHANNEL_FOREGROUND,
            "Location Service",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "Ongoing notification for location monitoring"
            setShowBadge(false)
        }

        manager.createNotificationChannels(listOf(sessionChannel, generalChannel, foregroundChannel))
    }

    companion object {
        const val CHANNEL_SESSION = "session_updates"
        const val CHANNEL_GENERAL = "general"
        const val CHANNEL_FOREGROUND = "foreground_service"
    }
}
