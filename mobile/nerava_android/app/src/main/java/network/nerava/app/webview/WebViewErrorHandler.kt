package network.nerava.app.webview

import android.net.http.SslError
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest

/**
 * Classifies WebView errors and provides user-facing messages.
 * Mirrors iOS error handling in WebViewContainer.swift.
 */
object WebViewErrorHandler {

    enum class ErrorType {
        OFFLINE,
        SERVER,
        SSL,
        GENERIC,
    }

    data class WebError(
        val type: ErrorType,
        val messageResId: Int,
    )

    fun classifyError(error: WebResourceError?): ErrorType {
        if (error == null) return ErrorType.GENERIC

        return when (error.errorCode) {
            android.webkit.WebViewClient.ERROR_HOST_LOOKUP,
            android.webkit.WebViewClient.ERROR_CONNECT,
            android.webkit.WebViewClient.ERROR_TIMEOUT -> ErrorType.OFFLINE

            android.webkit.WebViewClient.ERROR_FAILED_SSL_HANDSHAKE -> ErrorType.SSL

            else -> ErrorType.GENERIC
        }
    }

    fun classifySslError(error: SslError?): ErrorType = ErrorType.SSL

    fun classifyHttpError(statusCode: Int): ErrorType? {
        return when (statusCode) {
            in 500..599 -> ErrorType.SERVER
            else -> null // Don't show error overlay for 4xx (web app handles those)
        }
    }

    fun isMainFrameRequest(request: WebResourceRequest?): Boolean {
        return request?.isForMainFrame == true
    }
}
