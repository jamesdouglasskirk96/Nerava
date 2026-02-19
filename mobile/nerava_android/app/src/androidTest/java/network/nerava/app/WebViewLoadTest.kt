package network.nerava.app

import android.webkit.WebView
import androidx.test.ext.junit.rules.ActivityScenarioRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/**
 * Instrumentation test verifying basic WebView loading behavior.
 */
@RunWith(AndroidJUnit4::class)
class WebViewLoadTest {

    @get:Rule
    val activityRule = ActivityScenarioRule(MainActivity::class.java)

    @Test
    fun webViewIsPresent() {
        activityRule.scenario.onActivity { activity ->
            val webView = activity.findViewById<WebView>(R.id.webView)
            assertNotNull("WebView should be present", webView)
        }
    }

    @Test
    fun webViewHasJavaScriptEnabled() {
        activityRule.scenario.onActivity { activity ->
            val webView = activity.findViewById<WebView>(R.id.webView)
            assertTrue("JavaScript should be enabled", webView.settings.javaScriptEnabled)
        }
    }

    @Test
    fun webViewHasDomStorageEnabled() {
        activityRule.scenario.onActivity { activity ->
            val webView = activity.findViewById<WebView>(R.id.webView)
            assertTrue("DOM storage should be enabled", webView.settings.domStorageEnabled)
        }
    }

    @Test
    fun webViewUserAgentContainsNerava() {
        activityRule.scenario.onActivity { activity ->
            val webView = activity.findViewById<WebView>(R.id.webView)
            assertTrue(
                "User agent should contain NeravaAndroid",
                webView.settings.userAgentString.contains("NeravaAndroid")
            )
        }
    }

    @Test
    fun applicationContextIsValid() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        assertEquals("network.nerava.app", context.packageName)
    }
}
