package network.nerava.app

import android.Manifest
import android.annotation.SuppressLint
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.Uri
import android.net.http.SslError
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.util.Log
import android.view.View
import android.webkit.*
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import com.google.android.material.button.MaterialButton
import com.google.firebase.messaging.FirebaseMessaging
import network.nerava.app.auth.SecureTokenStore
import network.nerava.app.bridge.BridgeInjector
import network.nerava.app.bridge.NativeBridge
import network.nerava.app.deeplink.DeepLinkHandler
import network.nerava.app.engine.SessionEngine
import network.nerava.app.location.GeofenceManager
import network.nerava.app.location.LocationService
import network.nerava.app.network.APIClient
import network.nerava.app.webview.WebViewErrorHandler

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var errorView: View
    private lateinit var errorMessage: TextView
    private lateinit var retryButton: MaterialButton

    private lateinit var tokenStore: SecureTokenStore
    private lateinit var locationService: LocationService
    private lateinit var geofenceManager: GeofenceManager
    private lateinit var apiClient: APIClient
    private lateinit var bridge: NativeBridge
    private lateinit var sessionEngine: SessionEngine

    private var pendingDeepLinkUrl: String? = null

    // Permission launchers
    private val locationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val fineGranted = permissions[Manifest.permission.ACCESS_FINE_LOCATION] == true
        if (fineGranted) {
            locationService.startLocationUpdates()
        }
    }

    private val backgroundLocationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        Log.i(TAG, "Background location permission: $granted")
    }

    private val notificationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        Log.i(TAG, "Notification permission: $granted")
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Bind views
        webView = findViewById(R.id.webView)
        swipeRefresh = findViewById(R.id.swipeRefresh)
        errorView = findViewById(R.id.errorView)
        errorMessage = errorView.findViewById(R.id.errorMessage)
        retryButton = errorView.findViewById(R.id.retryButton)

        // Initialize services
        tokenStore = (application as NeravaApplication).tokenStore
        locationService = LocationService(this)
        geofenceManager = GeofenceManager(this)
        apiClient = APIClient(
            baseUrl = BuildConfig.API_BASE_URL,
            onAuthRequired = { bridge.sendToWeb(network.nerava.app.bridge.BridgeMessage.AuthRequired) }
        )

        // Load saved auth token
        tokenStore.getAccessToken()?.let { apiClient.accessToken = it }

        // Initialize bridge and engine
        bridge = NativeBridge(locationService, tokenStore)
        sessionEngine = SessionEngine(this, locationService, geofenceManager, tokenStore, apiClient)
        bridge.sessionEngine = sessionEngine
        sessionEngine.bridge = bridge

        // Set up location permission callback
        locationService.onRequestBackgroundPermission = { requestBackgroundLocation() }

        // Configure WebView
        configureWebView()

        // Set up pull-to-refresh
        swipeRefresh.setOnRefreshListener {
            webView.reload()
        }

        // Retry button
        retryButton.setOnClickListener {
            hideError()
            webView.reload()
        }

        // Request permissions
        requestInitialPermissions()

        // Start session engine
        sessionEngine.start()

        // Register FCM
        registerFCM()

        // Handle deep link (if launched via one)
        handleIntent(intent)

        // Load web app
        val deepLinkUrl = pendingDeepLinkUrl
        val url = deepLinkUrl ?: BuildConfig.WEB_APP_URL
        pendingDeepLinkUrl = null
        webView.loadUrl(url)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIntent(intent)
        pendingDeepLinkUrl?.let { url ->
            webView.loadUrl(url)
            pendingDeepLinkUrl = null
        }
    }

    override fun onPause() {
        super.onPause()
        // Flush cookies so session survives
        CookieManager.getInstance().flush()
    }

    override fun onDestroy() {
        super.onDestroy()
        sessionEngine.stop()
        webView.destroy()
    }

    @Deprecated("Use OnBackPressedCallback")
    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            @Suppress("DEPRECATION")
            super.onBackPressed()
        }
    }

    // MARK: - WebView Configuration

    private fun configureWebView() {
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = true
            cacheMode = WebSettings.LOAD_DEFAULT
            mixedContentMode = if (BuildConfig.DEBUG) {
                WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            } else {
                WebSettings.MIXED_CONTENT_NEVER_ALLOW
            }
            userAgentString = "$userAgentString NeravaAndroid/${BuildConfig.VERSION_NAME}"
            mediaPlaybackRequiresUserGesture = false
            useWideViewPort = true
            loadWithOverviewMode = true
            textZoom = 100
            databaseEnabled = true
        }

        // Cookie persistence
        val cookieManager = CookieManager.getInstance()
        cookieManager.setAcceptCookie(true)
        cookieManager.setAcceptThirdPartyCookies(webView, true)

        // Setup bridge
        bridge.setupWebView(webView)

        webView.webViewClient = object : WebViewClient() {

            override fun onPageStarted(view: WebView, url: String?, favicon: Bitmap?) {
                // Inject bridge script at page start (matches iOS atDocumentStart)
                bridge.injectBridgeScript()
            }

            override fun onPageFinished(view: WebView, url: String?) {
                swipeRefresh.isRefreshing = false
                bridge.didFinishNavigation()

                // Re-inject and send NATIVE_READY for SPA navigation
                view.evaluateJavascript(
                    "if(window.neravaNativeCallback) window.neravaNativeCallback('NATIVE_READY', {});",
                    null
                )
            }

            override fun onReceivedError(
                view: WebView,
                request: WebResourceRequest?,
                error: WebResourceError?,
            ) {
                if (WebViewErrorHandler.isMainFrameRequest(request)) {
                    val type = WebViewErrorHandler.classifyError(error)
                    showError(type)
                }
            }

            override fun onReceivedSslError(view: WebView, handler: SslErrorHandler, error: SslError?) {
                // Never proceed on SSL errors in release
                if (BuildConfig.DEBUG) {
                    Log.w(TAG, "SSL error in debug: ${error?.primaryError}")
                    handler.proceed()
                } else {
                    handler.cancel()
                    showError(WebViewErrorHandler.ErrorType.SSL)
                }
            }

            override fun onReceivedHttpError(
                view: WebView,
                request: WebResourceRequest?,
                errorResponse: WebResourceResponse?,
            ) {
                if (WebViewErrorHandler.isMainFrameRequest(request)) {
                    val statusCode = errorResponse?.statusCode ?: return
                    val type = WebViewErrorHandler.classifyHttpError(statusCode)
                    if (type != null) showError(type)
                }
            }

            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val url = request.url
                val host = url.host

                // Allow navigation within the app's domain
                if (host == "app.nerava.network" || host == "localhost" ||
                    host == "10.0.2.2" || host == "10.0.2.127"
                ) {
                    return false
                }

                // External links: open in browser
                try {
                    startActivity(Intent(Intent.ACTION_VIEW, url))
                } catch (e: Exception) {
                    Log.e(TAG, "Failed to open external URL: $url", e)
                }
                return true
            }

            override fun onRenderProcessGone(view: WebView, detail: RenderProcessGoneDetail?): Boolean {
                Log.e(TAG, "WebView render process gone, reloading")
                webView.loadUrl(BuildConfig.WEB_APP_URL)
                return true
            }
        }

        // Handle file uploads / camera
        webView.webChromeClient = object : WebChromeClient() {
            override fun onShowFileChooser(
                webView: WebView,
                filePathCallback: ValueCallback<Array<Uri>>?,
                fileChooserParams: FileChooserParams?,
            ): Boolean {
                // Basic file chooser — extend with camera intent if needed
                val intent = fileChooserParams?.createIntent() ?: return false
                try {
                    fileUploadCallback?.onReceiveValue(null)
                    fileUploadCallback = filePathCallback
                    fileUploadLauncher.launch(intent)
                } catch (e: Exception) {
                    fileUploadCallback = null
                    return false
                }
                return true
            }
        }
    }

    private var fileUploadCallback: ValueCallback<Array<Uri>>? = null
    private val fileUploadLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        val data = result.data
        val results = if (result.resultCode == RESULT_OK && data != null) {
            WebChromeClient.FileChooserParams.parseResult(result.resultCode, data)
        } else {
            null
        }
        fileUploadCallback?.onReceiveValue(results)
        fileUploadCallback = null
    }

    // MARK: - Error Handling

    private fun showError(type: WebViewErrorHandler.ErrorType) {
        val msgRes = when (type) {
            WebViewErrorHandler.ErrorType.OFFLINE -> R.string.error_offline
            WebViewErrorHandler.ErrorType.SERVER -> R.string.error_server
            WebViewErrorHandler.ErrorType.SSL -> R.string.error_ssl
            WebViewErrorHandler.ErrorType.GENERIC -> R.string.error_generic
        }
        runOnUiThread {
            errorMessage.setText(msgRes)
            errorView.visibility = View.VISIBLE
        }
    }

    private fun hideError() {
        runOnUiThread {
            errorView.visibility = View.GONE
        }
    }

    // MARK: - Permissions

    private fun requestInitialPermissions() {
        // Location (foreground)
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
            != PackageManager.PERMISSION_GRANTED
        ) {
            locationPermissionLauncher.launch(
                arrayOf(
                    Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION,
                )
            )
        } else {
            locationService.startLocationUpdates()
        }

        // Notifications (Android 13+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED
            ) {
                notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
    }

    private fun requestBackgroundLocation() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_BACKGROUND_LOCATION)
            != PackageManager.PERMISSION_GRANTED
        ) {
            backgroundLocationPermissionLauncher.launch(Manifest.permission.ACCESS_BACKGROUND_LOCATION)
        }
    }

    // MARK: - FCM

    private fun registerFCM() {
        FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
            if (task.isSuccessful) {
                val token = task.result
                Log.i(TAG, "FCM token: ${token.take(10)}...")
                tokenStore.setFCMToken(token)
            } else {
                Log.w(TAG, "FCM token fetch failed", task.exception)
            }
        }
    }

    // MARK: - Deep Links

    private fun handleIntent(intent: Intent?) {
        val url = DeepLinkHandler.resolveWebUrl(intent, BuildConfig.WEB_APP_URL)
        if (url != null) {
            pendingDeepLinkUrl = url
            Log.i(TAG, "Deep link resolved: $url")
        }
    }

    // MARK: - Debug

    fun launchDiagnostics() {
        if (BuildConfig.DEBUG) {
            startActivity(Intent(this, network.nerava.app.debug.BridgeDiagnosticsActivity::class.java))
        }
    }

    companion object {
        private const val TAG = "MainActivity"
    }
}
