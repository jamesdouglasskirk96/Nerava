package network.nerava.app.deeplink

import android.content.Intent
import android.net.Uri
import android.util.Log

/**
 * Handles deep links and Android App Links.
 *
 * Supported schemes:
 * - nerava://merchant/{id} → loads web app at /merchant/{id}
 * - nerava://session/{id} → loads web app at /session/{id}
 * - https://app.nerava.network/{path} → loads directly in WebView
 *
 * Note: iOS does NOT implement deep links yet. This is Android-first but
 * follows the same URL patterns the web app router already handles.
 */
object DeepLinkHandler {

    private const val TAG = "DeepLinkHandler"

    /**
     * Extract a web URL from an incoming deep link intent.
     * Returns null if the intent doesn't contain a valid deep link.
     */
    fun resolveWebUrl(intent: Intent?, webAppBaseUrl: String): String? {
        val uri = intent?.data ?: return null
        return resolveUri(uri, webAppBaseUrl)
    }

    fun resolveUri(uri: Uri, webAppBaseUrl: String): String? {
        Log.i(TAG, "Resolving deep link: $uri")

        return when (uri.scheme) {
            "nerava" -> resolveCustomScheme(uri, webAppBaseUrl)
            "https" -> resolveAppLink(uri, webAppBaseUrl)
            else -> {
                Log.w(TAG, "Unknown scheme: ${uri.scheme}")
                null
            }
        }
    }

    private fun resolveCustomScheme(uri: Uri, webAppBaseUrl: String): String? {
        val path = uri.pathSegments
        if (path.isEmpty()) return webAppBaseUrl

        return when (path[0]) {
            "merchant" -> {
                val merchantId = path.getOrNull(1) ?: return webAppBaseUrl
                "$webAppBaseUrl/merchant/$merchantId"
            }
            "session" -> {
                val sessionId = path.getOrNull(1) ?: return webAppBaseUrl
                "$webAppBaseUrl/session/$sessionId"
            }
            "exclusive" -> {
                val exclusiveId = path.getOrNull(1) ?: return webAppBaseUrl
                "$webAppBaseUrl/exclusive/$exclusiveId"
            }
            else -> {
                // Pass through: nerava://path → webAppBaseUrl/path
                "$webAppBaseUrl/${path.joinToString("/")}"
            }
        }
    }

    private fun resolveAppLink(uri: Uri, webAppBaseUrl: String): String? {
        val host = uri.host
        if (host != "app.nerava.network") {
            Log.w(TAG, "App link from unexpected host: $host")
            return null
        }

        // The URL is already the web app URL — load it directly
        return uri.toString()
    }
}
