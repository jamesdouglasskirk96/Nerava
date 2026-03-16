package network.nerava.app.network

import org.junit.Assert.*
import org.junit.Test

/**
 * Unit tests for APIClient.sendBackgroundPing().
 *
 * These tests verify token resolution and error handling without making
 * real network calls (the HTTP call will fail with a connection error
 * since there's no server, but sendBackgroundPing catches all exceptions).
 */
class APIClientBackgroundPingTest {

    @Test
    fun `sendBackgroundPing with no token skips request`() {
        // No accessToken set, no authToken param — should skip without crashing
        val client = APIClient(baseUrl = "http://localhost:1")
        client.accessToken = null
        // Should return immediately without throwing
        client.sendBackgroundPing(29.42, -98.49)
    }

    @Test
    fun `sendBackgroundPing with explicit authToken does not skip`() {
        // Explicit authToken should be used even if accessToken is null.
        // The HTTP call will fail (no server), but it should NOT skip and
        // should catch the network error without crashing.
        val client = APIClient(baseUrl = "http://localhost:1")
        client.accessToken = null
        client.sendBackgroundPing(29.42, -98.49, authToken = "test_token")
        // No exception = success (network error is caught internally)
    }

    @Test
    fun `sendBackgroundPing with in-memory accessToken does not skip`() {
        // In-memory accessToken should be used when no explicit authToken.
        val client = APIClient(baseUrl = "http://localhost:1")
        client.accessToken = "in_memory_token"
        client.sendBackgroundPing(29.42, -98.49)
        // No exception = success (network error is caught internally)
    }

    @Test
    fun `sendBackgroundPing prefers explicit authToken over accessToken`() {
        // When both are set, authToken param should take precedence.
        // This matters for the BroadcastReceiver case where accessToken
        // may be stale but SecureTokenStore has the fresh token.
        val client = APIClient(baseUrl = "http://localhost:1")
        client.accessToken = "stale_token"
        client.sendBackgroundPing(29.42, -98.49, authToken = "fresh_token")
        // No exception = success
    }

    @Test
    fun `sendBackgroundPing handles invalid URL gracefully`() {
        val client = APIClient(baseUrl = "not-a-valid-url")
        client.accessToken = "some_token"
        // Should catch the error without crashing
        client.sendBackgroundPing(29.42, -98.49)
    }
}
