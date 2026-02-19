package network.nerava.app.webview

import android.annotation.SuppressLint
import android.content.Context
import android.util.AttributeSet
import android.webkit.CookieManager
import android.webkit.WebSettings
import android.webkit.WebView
import network.nerava.app.BuildConfig

/**
 * Preconfigured WebView for the Nerava driver app.
 * Mirrors iOS WKWebView configuration.
 */
@SuppressLint("SetJavaScriptEnabled")
class NeravaWebView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : WebView(context, attrs) {

    init {
        configureSettings()
        configureCookies()
    }

    private fun configureSettings() {
        settings.apply {
            // JavaScript required for React app
            javaScriptEnabled = true

            // DOM storage for localStorage/sessionStorage
            domStorageEnabled = true

            // Allow file access for camera uploads
            allowFileAccess = true

            // Cache
            cacheMode = WebSettings.LOAD_DEFAULT

            // Mixed content: block in release, allow in debug for localhost
            mixedContentMode = if (BuildConfig.DEBUG) {
                WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            } else {
                WebSettings.MIXED_CONTENT_NEVER_ALLOW
            }

            // User agent: append Nerava identifier so web can detect native shell
            userAgentString = "$userAgentString NeravaAndroid/${BuildConfig.VERSION_NAME}"

            // Media playback
            mediaPlaybackRequiresUserGesture = false

            // Viewport
            useWideViewPort = true
            loadWithOverviewMode = true

            // Text zoom: prevent system font size from breaking layout
            textZoom = 100

            // Database
            databaseEnabled = true
        }
    }

    private fun configureCookies() {
        val cookieManager = CookieManager.getInstance()
        cookieManager.setAcceptCookie(true)
        cookieManager.setAcceptThirdPartyCookies(this, true)
    }

    /**
     * Flush cookies to persistent storage.
     * Call this in onPause to ensure session cookies survive process death.
     */
    fun flushCookies() {
        CookieManager.getInstance().flush()
    }
}
