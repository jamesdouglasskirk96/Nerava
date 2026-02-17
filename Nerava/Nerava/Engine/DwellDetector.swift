import CoreLocation

final class DwellDetector {
    private let anchorRadius: Double
    private let dwellDuration: TimeInterval
    private let speedThreshold: Double

    private var dwellStartTime: Date?
    private var locationHistory: [(location: CLLocation, timestamp: Date)] = []

    var isAnchored: Bool {
        guard let startTime = dwellStartTime else { return false }
        return Date().timeIntervalSince(startTime) >= dwellDuration
    }

    init(anchorRadius: Double, dwellDuration: TimeInterval, speedThreshold: Double) {
        self.anchorRadius = anchorRadius
        self.dwellDuration = dwellDuration
        self.speedThreshold = speedThreshold
    }

    func recordLocation(_ location: CLLocation, distanceToAnchor: Double) {
        let now = Date()

        locationHistory = locationHistory.filter { now.timeIntervalSince($0.timestamp) < 300 }
        locationHistory.append((location, now))

        let isWithinRadius = distanceToAnchor <= anchorRadius
        let isStationary = location.speed < 0 || location.speed < speedThreshold

        if isWithinRadius && isStationary {
            if dwellStartTime == nil {
                dwellStartTime = now
            }
        } else {
            dwellStartTime = nil
        }
    }

    func reset() {
        dwellStartTime = nil
        locationHistory.removeAll()
    }
}
