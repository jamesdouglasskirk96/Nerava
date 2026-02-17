import Foundation
import os.log

enum Log {
    static let session = Logger(subsystem: "network.nerava.app", category: "SessionEngine")
    static let location = Logger(subsystem: "network.nerava.app", category: "LocationService")
    static let geofence = Logger(subsystem: "network.nerava.app", category: "GeofenceManager")
    static let bridge = Logger(subsystem: "network.nerava.app", category: "NativeBridge")
    static let api = Logger(subsystem: "network.nerava.app", category: "APIClient")

    /// Scrub session ID to last 6 chars for logging
    static func scrubSessionId(_ id: String) -> String {
        guard id.count > 6 else { return id }
        return "...\(id.suffix(6))"
    }

    /// Scrub coordinates to 2 decimal places
    static func scrubCoordinate(_ value: Double) -> String {
        return String(format: "%.2f", value)
    }
}
