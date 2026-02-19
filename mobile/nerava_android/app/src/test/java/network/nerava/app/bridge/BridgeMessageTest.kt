package network.nerava.app.bridge

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class BridgeMessageTest {

    // ---- IncomingBridgeAction parsing ----

    @Test
    fun `parse valid SET_CHARGER_TARGET message`() {
        val json = """{"action":"SET_CHARGER_TARGET","payload":{"chargerId":"ch_123","chargerLat":29.42,"chargerLng":-98.49}}"""
        val msg = IncomingBridgeAction.parse(json)
        assertNotNull(msg)
        assertEquals("SET_CHARGER_TARGET", msg!!.action)
        assertEquals("ch_123", msg.payload.getString("chargerId"))
        assertEquals(29.42, msg.payload.getDouble("chargerLat"), 0.001)
    }

    @Test
    fun `parse valid SET_AUTH_TOKEN message`() {
        val json = """{"action":"SET_AUTH_TOKEN","payload":{"token":"eyJhbG..."}}"""
        val msg = IncomingBridgeAction.parse(json)
        assertNotNull(msg)
        assertEquals("SET_AUTH_TOKEN", msg!!.action)
        assertEquals("eyJhbG...", msg.payload.getString("token"))
    }

    @Test
    fun `parse EXCLUSIVE_ACTIVATED with all fields`() {
        val json = """{"action":"EXCLUSIVE_ACTIVATED","payload":{"sessionId":"s1","merchantId":"m1","merchantLat":29.5,"merchantLng":-98.5}}"""
        val msg = IncomingBridgeAction.parse(json)
        assertNotNull(msg)
        assertEquals("EXCLUSIVE_ACTIVATED", msg!!.action)
        assertEquals("s1", msg.payload.getString("sessionId"))
        assertEquals("m1", msg.payload.getString("merchantId"))
    }

    @Test
    fun `parse request with requestId`() {
        val json = """{"action":"GET_LOCATION","payload":{"requestId":"req_1_1706000000"}}"""
        val msg = IncomingBridgeAction.parse(json)
        assertNotNull(msg)
        assertEquals("req_1_1706000000", msg!!.requestId)
    }

    @Test
    fun `parse returns null for invalid JSON`() {
        assertNull(IncomingBridgeAction.parse("not json"))
        assertNull(IncomingBridgeAction.parse(""))
        assertNull(IncomingBridgeAction.parse("{}")) // missing action
    }

    @Test
    fun `parse handles missing payload gracefully`() {
        val json = """{"action":"END_SESSION"}"""
        val msg = IncomingBridgeAction.parse(json)
        assertNotNull(msg)
        assertEquals("END_SESSION", msg!!.action)
        // payload should be empty JSONObject
        assertEquals(0, msg.payload.length())
    }

    // ---- Outgoing BridgeMessage serialization ----

    @Test
    fun `SessionStateChanged serializes correctly`() {
        val msg = BridgeMessage.SessionStateChanged("SESSION_ACTIVE")
        assertEquals("SESSION_STATE_CHANGED", msg.action)
        assertEquals("SESSION_ACTIVE", msg.toPayloadJson().getString("state"))
    }

    @Test
    fun `LocationResponse serializes with all fields`() {
        val msg = BridgeMessage.LocationResponse("req_1", 29.42, -98.49, 10.5)
        val json = msg.toPayloadJson()
        assertEquals("req_1", json.getString("requestId"))
        assertEquals(29.42, json.getDouble("lat"), 0.001)
        assertEquals(-98.49, json.getDouble("lng"), 0.001)
        assertEquals(10.5, json.getDouble("accuracy"), 0.001)
    }

    @Test
    fun `PermissionStatus serializes correctly`() {
        val msg = BridgeMessage.PermissionStatus("req_2", "authorizedAlways", true)
        val json = msg.toPayloadJson()
        assertEquals("PERMISSION_STATUS", msg.action)
        assertTrue(json.getBoolean("alwaysGranted"))
    }

    @Test
    fun `AuthTokenResponse serializes with token`() {
        val msg = BridgeMessage.AuthTokenResponse("req_3", "my_token")
        val json = msg.toPayloadJson()
        assertTrue(json.getBoolean("hasToken"))
        assertEquals("my_token", json.getString("token"))
    }

    @Test
    fun `AuthTokenResponse serializes without token`() {
        val msg = BridgeMessage.AuthTokenResponse("req_4", null)
        val json = msg.toPayloadJson()
        assertFalse(json.getBoolean("hasToken"))
        assertFalse(json.has("token"))
    }

    @Test
    fun `Ready has empty payload`() {
        val msg = BridgeMessage.Ready
        assertEquals("NATIVE_READY", msg.action)
        assertEquals(0, msg.toPayloadJson().length())
    }

    @Test
    fun `Error with requestId`() {
        val msg = BridgeMessage.Error("req_5", "Location unavailable")
        val json = msg.toPayloadJson()
        assertEquals("req_5", json.getString("requestId"))
        assertEquals("Location unavailable", json.getString("message"))
    }

    @Test
    fun `Error without requestId`() {
        val msg = BridgeMessage.Error(null, "Unknown error")
        val json = msg.toPayloadJson()
        assertFalse(json.has("requestId"))
        assertEquals("Unknown error", json.getString("message"))
    }
}
