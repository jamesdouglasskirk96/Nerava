package network.nerava.app.engine

/**
 * Mirror of iOS SessionState enum.
 * Raw values match the strings sent over the bridge and to the backend.
 */
enum class SessionState(val raw: String) {
    IDLE("IDLE"),
    NEAR_CHARGER("NEAR_CHARGER"),
    ANCHORED("ANCHORED"),
    SESSION_ACTIVE("SESSION_ACTIVE"),
    IN_TRANSIT("IN_TRANSIT"),
    AT_MERCHANT("AT_MERCHANT"),
    SESSION_ENDED("SESSION_ENDED");

    companion object {
        fun fromRaw(raw: String): SessionState? = entries.find { it.raw == raw }
    }
}

/**
 * Mirror of iOS SessionEvent enum.
 * Each event has exactly one enum case. Use requiresSessionId to route to the correct endpoint.
 */
enum class SessionEvent(val raw: String, val requiresSessionId: Boolean) {
    // Pre-session events (no session_id)
    CHARGER_TARGETED("charger_targeted", false),
    ENTERED_CHARGER_INTENT_ZONE("entered_charger_intent_zone", false),
    EXITED_CHARGER_INTENT_ZONE("exited_charger_intent_zone", false),
    ANCHOR_DWELL_COMPLETE("anchor_dwell_complete", false),
    ANCHOR_LOST("anchor_lost", false),
    ACTIVATION_REJECTED("activation_rejected", false),

    // Session events (has session_id)
    EXCLUSIVE_ACTIVATED("exclusive_activated", true),
    DEPARTED_CHARGER("departed_charger", true),
    ENTERED_MERCHANT_ZONE("entered_merchant_zone", true),
    VISIT_VERIFIED("visit_verified", true),
    GRACE_PERIOD_EXPIRED("grace_period_expired", true),
    HARD_TIMEOUT_EXPIRED("hard_timeout_expired", true),
    WEB_REQUESTED_END("web_requested_end", true),
    SESSION_RESTORED("session_restored", true),
}

data class ChargerTarget(
    val id: String,
    val latitude: Double,
    val longitude: Double,
)

data class MerchantTarget(
    val id: String,
    val latitude: Double,
    val longitude: Double,
)

data class ActiveSessionInfo(
    val sessionId: String,
    val chargerId: String,
    val merchantId: String,
    val startedAt: Long, // epoch millis
)
