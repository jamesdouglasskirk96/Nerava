package network.nerava.app.engine

import android.location.Location

/**
 * Detects whether a user has "dwelled" (stayed stationary) near a charger.
 * Mirrors iOS DwellDetector: 120s within 30m, speed < 1.5 m/s.
 */
class DwellDetector(private val config: SessionConfig = SessionConfig.DEFAULTS) {

    private var dwellStartTime: Long? = null

    /**
     * Record a location update and check if dwell criteria are met.
     * @param location The current location
     * @param distanceToAnchor Distance in meters to the charger anchor point
     */
    fun recordLocation(location: Location, distanceToAnchor: Double) {
        val isWithinRadius = distanceToAnchor <= config.chargerAnchorRadiusM
        val isStationary = !location.hasSpeed() || location.speed < config.speedThresholdForDwellMps

        if (isWithinRadius && isStationary) {
            if (dwellStartTime == null) {
                dwellStartTime = System.currentTimeMillis()
            }
        } else {
            dwellStartTime = null
        }
    }

    val isAnchored: Boolean
        get() {
            val start = dwellStartTime ?: return false
            val elapsed = (System.currentTimeMillis() - start) / 1000.0
            return elapsed >= config.chargerDwellSeconds
        }

    fun reset() {
        dwellStartTime = null
    }
}
