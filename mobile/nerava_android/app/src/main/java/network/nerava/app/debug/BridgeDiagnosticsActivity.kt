package network.nerava.app.debug

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import network.nerava.app.BuildConfig
import network.nerava.app.R

/**
 * Debug-only screen showing bridge diagnostics:
 * - Last 20 bridge messages
 * - Current location permission state
 * - Last geofence trigger time
 * - Loaded web URL and environment
 *
 * Only accessible in debug builds.
 */
class BridgeDiagnosticsActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        if (!BuildConfig.DEBUG) {
            finish()
            return
        }

        val textView = TextView(this).apply {
            setPadding(32, 32, 32, 32)
            textSize = 13f
            setTextIsSelectable(true)
        }

        setContentView(textView)
        title = getString(R.string.diagnostics_title)

        val sb = StringBuilder()

        // Environment
        sb.appendLine("=== Environment ===")
        sb.appendLine("Web URL: ${BuildConfig.WEB_APP_URL}")
        sb.appendLine("API URL: ${BuildConfig.API_BASE_URL}")
        sb.appendLine("Build: ${BuildConfig.BUILD_TYPE}")
        sb.appendLine("Version: ${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})")
        sb.appendLine()

        // Permissions
        sb.appendLine("=== Permissions ===")
        val fineLocation = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
        sb.appendLine("Fine Location: ${if (fineLocation == PackageManager.PERMISSION_GRANTED) "GRANTED" else "DENIED"}")
        val bgLocation = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_BACKGROUND_LOCATION)
        sb.appendLine("Background Location: ${if (bgLocation == PackageManager.PERMISSION_GRANTED) "GRANTED" else "DENIED"}")
        val notifications = ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
        sb.appendLine("Notifications: ${if (notifications == PackageManager.PERMISSION_GRANTED) "GRANTED" else "DENIED"}")
        sb.appendLine()

        // Auth
        sb.appendLine("=== Auth ===")
        val tokenStore = (application as network.nerava.app.NeravaApplication).tokenStore
        val hasToken = tokenStore.getAccessToken() != null
        sb.appendLine("Access Token: ${if (hasToken) "present" else "none"}")
        val fcmToken = tokenStore.getFCMToken()
        sb.appendLine("FCM Token: ${fcmToken?.take(20) ?: "none"}...")
        sb.appendLine()

        // Bridge messages will need to be passed in via intent extras or a shared reference.
        // For now, show placeholder.
        sb.appendLine("=== Bridge Log ===")
        sb.appendLine("(Launch from main activity for live log)")
        sb.appendLine()

        // Geofence
        sb.appendLine("=== Geofence ===")
        sb.appendLine("(Active geofences tracked in GeofenceManager)")
        sb.appendLine()

        textView.text = sb.toString()
    }
}
