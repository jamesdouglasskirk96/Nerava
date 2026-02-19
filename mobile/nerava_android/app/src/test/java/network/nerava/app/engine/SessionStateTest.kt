package network.nerava.app.engine

import org.junit.Assert.*
import org.junit.Test

class SessionStateTest {

    @Test
    fun `SessionState fromRaw returns correct state`() {
        assertEquals(SessionState.IDLE, SessionState.fromRaw("IDLE"))
        assertEquals(SessionState.NEAR_CHARGER, SessionState.fromRaw("NEAR_CHARGER"))
        assertEquals(SessionState.ANCHORED, SessionState.fromRaw("ANCHORED"))
        assertEquals(SessionState.SESSION_ACTIVE, SessionState.fromRaw("SESSION_ACTIVE"))
        assertEquals(SessionState.IN_TRANSIT, SessionState.fromRaw("IN_TRANSIT"))
        assertEquals(SessionState.AT_MERCHANT, SessionState.fromRaw("AT_MERCHANT"))
        assertEquals(SessionState.SESSION_ENDED, SessionState.fromRaw("SESSION_ENDED"))
    }

    @Test
    fun `SessionState fromRaw returns null for unknown`() {
        assertNull(SessionState.fromRaw("INVALID"))
        assertNull(SessionState.fromRaw(""))
    }

    @Test
    fun `SessionState raw values match iOS convention`() {
        // These must exactly match the strings in useNativeBridge.ts
        assertEquals("IDLE", SessionState.IDLE.raw)
        assertEquals("NEAR_CHARGER", SessionState.NEAR_CHARGER.raw)
        assertEquals("ANCHORED", SessionState.ANCHORED.raw)
        assertEquals("SESSION_ACTIVE", SessionState.SESSION_ACTIVE.raw)
        assertEquals("IN_TRANSIT", SessionState.IN_TRANSIT.raw)
        assertEquals("AT_MERCHANT", SessionState.AT_MERCHANT.raw)
        assertEquals("SESSION_ENDED", SessionState.SESSION_ENDED.raw)
    }

    @Test
    fun `SessionEvent raw values match iOS convention`() {
        assertEquals("charger_targeted", SessionEvent.CHARGER_TARGETED.raw)
        assertEquals("entered_charger_intent_zone", SessionEvent.ENTERED_CHARGER_INTENT_ZONE.raw)
        assertEquals("exited_charger_intent_zone", SessionEvent.EXITED_CHARGER_INTENT_ZONE.raw)
        assertEquals("anchor_dwell_complete", SessionEvent.ANCHOR_DWELL_COMPLETE.raw)
        assertEquals("exclusive_activated", SessionEvent.EXCLUSIVE_ACTIVATED.raw)
        assertEquals("departed_charger", SessionEvent.DEPARTED_CHARGER.raw)
        assertEquals("entered_merchant_zone", SessionEvent.ENTERED_MERCHANT_ZONE.raw)
        assertEquals("visit_verified", SessionEvent.VISIT_VERIFIED.raw)
        assertEquals("grace_period_expired", SessionEvent.GRACE_PERIOD_EXPIRED.raw)
        assertEquals("hard_timeout_expired", SessionEvent.HARD_TIMEOUT_EXPIRED.raw)
        assertEquals("web_requested_end", SessionEvent.WEB_REQUESTED_END.raw)
        assertEquals("session_restored", SessionEvent.SESSION_RESTORED.raw)
    }

    @Test
    fun `Pre-session events do not require session id`() {
        assertFalse(SessionEvent.CHARGER_TARGETED.requiresSessionId)
        assertFalse(SessionEvent.ENTERED_CHARGER_INTENT_ZONE.requiresSessionId)
        assertFalse(SessionEvent.EXITED_CHARGER_INTENT_ZONE.requiresSessionId)
        assertFalse(SessionEvent.ANCHOR_DWELL_COMPLETE.requiresSessionId)
        assertFalse(SessionEvent.ANCHOR_LOST.requiresSessionId)
        assertFalse(SessionEvent.ACTIVATION_REJECTED.requiresSessionId)
    }

    @Test
    fun `Session events require session id`() {
        assertTrue(SessionEvent.EXCLUSIVE_ACTIVATED.requiresSessionId)
        assertTrue(SessionEvent.DEPARTED_CHARGER.requiresSessionId)
        assertTrue(SessionEvent.ENTERED_MERCHANT_ZONE.requiresSessionId)
        assertTrue(SessionEvent.VISIT_VERIFIED.requiresSessionId)
        assertTrue(SessionEvent.GRACE_PERIOD_EXPIRED.requiresSessionId)
        assertTrue(SessionEvent.HARD_TIMEOUT_EXPIRED.requiresSessionId)
        assertTrue(SessionEvent.WEB_REQUESTED_END.requiresSessionId)
        assertTrue(SessionEvent.SESSION_RESTORED.requiresSessionId)
    }

    @Test
    fun `Haversine distance calculation`() {
        // San Antonio coordinates: roughly 29.42, -98.49
        // Two points about 100m apart
        val dist = SessionEngine.haversineM(29.4200, -98.4900, 29.4209, -98.4900)
        assertTrue("Distance should be ~100m, got $dist", dist in 90.0..110.0)
    }

    @Test
    fun `Haversine same point returns zero`() {
        val dist = SessionEngine.haversineM(29.42, -98.49, 29.42, -98.49)
        assertEquals(0.0, dist, 0.1)
    }

    @Test
    fun `SessionConfig defaults match iOS`() {
        val config = SessionConfig.DEFAULTS
        assertEquals(400.0, config.chargerIntentRadiusM, 0.1)
        assertEquals(30.0, config.chargerAnchorRadiusM, 0.1)
        assertEquals(120, config.chargerDwellSeconds)
        assertEquals(40.0, config.merchantUnlockRadiusM, 0.1)
        assertEquals(900, config.gracePeriodSeconds)
        assertEquals(3600, config.hardTimeoutSeconds)
        assertEquals(50.0, config.locationAccuracyThresholdM, 0.1)
        assertEquals(1.5, config.speedThresholdForDwellMps, 0.01)
    }

    @Test
    fun `SessionConfig fromJson parses correctly`() {
        val json = org.json.JSONObject().apply {
            put("chargerIntentRadius_m", 500.0)
            put("chargerAnchorRadius_m", 25.0)
            put("chargerDwellSeconds", 60)
            put("merchantUnlockRadius_m", 50.0)
            put("gracePeriodSeconds", 600)
            put("hardTimeoutSeconds", 1800)
            put("locationAccuracyThreshold_m", 30.0)
            put("speedThresholdForDwell_mps", 2.0)
        }
        val config = SessionConfig.fromJson(json)
        assertEquals(500.0, config.chargerIntentRadiusM, 0.1)
        assertEquals(25.0, config.chargerAnchorRadiusM, 0.1)
        assertEquals(60, config.chargerDwellSeconds)
    }
}
