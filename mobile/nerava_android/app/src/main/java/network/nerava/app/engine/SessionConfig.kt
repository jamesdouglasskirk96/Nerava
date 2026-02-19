package network.nerava.app.engine

import org.json.JSONObject

/**
 * Runtime configuration for session engine. Mirrors iOS SessionConfig.
 * Fetched from GET /v1/native/config; falls back to defaults on failure.
 */
data class SessionConfig(
    val chargerIntentRadiusM: Double = 400.0,
    val chargerAnchorRadiusM: Double = 30.0,
    val chargerDwellSeconds: Int = 120,
    val merchantUnlockRadiusM: Double = 40.0,
    val gracePeriodSeconds: Int = 900,
    val hardTimeoutSeconds: Int = 3600,
    val locationAccuracyThresholdM: Double = 50.0,
    val speedThresholdForDwellMps: Double = 1.5,
) {
    companion object {
        val DEFAULTS = SessionConfig()

        fun fromJson(json: JSONObject): SessionConfig = SessionConfig(
            chargerIntentRadiusM = json.optDouble("chargerIntentRadius_m", 400.0),
            chargerAnchorRadiusM = json.optDouble("chargerAnchorRadius_m", 30.0),
            chargerDwellSeconds = json.optInt("chargerDwellSeconds", 120),
            merchantUnlockRadiusM = json.optDouble("merchantUnlockRadius_m", 40.0),
            gracePeriodSeconds = json.optInt("gracePeriodSeconds", 900),
            hardTimeoutSeconds = json.optInt("hardTimeoutSeconds", 3600),
            locationAccuracyThresholdM = json.optDouble("locationAccuracyThreshold_m", 50.0),
            speedThresholdForDwellMps = json.optDouble("speedThresholdForDwell_mps", 1.5),
        )
    }
}
