import Foundation

struct SessionConfig: Codable {
    let chargerIntentRadius_m: Double
    let chargerAnchorRadius_m: Double
    let chargerDwellSeconds: Int
    let merchantUnlockRadius_m: Double
    let gracePeriodSeconds: Int
    let hardTimeoutSeconds: Int
    let locationAccuracyThreshold_m: Double
    let speedThresholdForDwell_mps: Double

    /// Default config used when remote fetch fails
    static let defaults = SessionConfig(
        chargerIntentRadius_m: 400.0,
        chargerAnchorRadius_m: 30.0,
        chargerDwellSeconds: 120,
        merchantUnlockRadius_m: 40.0,
        gracePeriodSeconds: 900,
        hardTimeoutSeconds: 3600,
        locationAccuracyThreshold_m: 50.0,
        speedThresholdForDwell_mps: 1.5
    )
}
