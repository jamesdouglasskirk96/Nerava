import CoreLocation
import os

protocol GeofenceManagerDelegate: AnyObject {
    func geofenceManager(_ manager: GeofenceManager, didEnterRegion identifier: String)
    func geofenceManager(_ manager: GeofenceManager, didExitRegion identifier: String)
}

final class GeofenceManager: NSObject {
    private let locationManager: CLLocationManager
    private var activeRegions: [String: CLCircularRegion] = [:]
    private var regionOrder: [String] = []  // FIFO order tracking
    private let maxRegions = 2

    weak var delegate: GeofenceManagerDelegate?

    override init() {
        self.locationManager = CLLocationManager()
        super.init()
        locationManager.delegate = self
    }

    func addChargerGeofence(id: String, coordinate: CLLocationCoordinate2D, radius: Double) {
        let identifier = "charger_\(id)"
        addRegion(identifier: identifier, coordinate: coordinate, radius: radius, notifyOnExit: true)
    }

    func addMerchantGeofence(id: String, coordinate: CLLocationCoordinate2D, radius: Double) {
        let identifier = "merchant_\(id)"
        addRegion(identifier: identifier, coordinate: coordinate, radius: radius, notifyOnExit: false)
    }

    private func addRegion(identifier: String, coordinate: CLLocationCoordinate2D, radius: Double, notifyOnExit: Bool) {
        if activeRegions.count >= maxRegions {
            // FIFO: remove oldest region
            if let oldestKey = regionOrder.first {
                removeRegion(identifier: oldestKey)
            }
        }

        let clampedRadius = min(radius, locationManager.maximumRegionMonitoringDistance)
        let region = CLCircularRegion(
            center: coordinate,
            radius: clampedRadius,
            identifier: identifier
        )
        region.notifyOnEntry = true
        region.notifyOnExit = notifyOnExit

        activeRegions[identifier] = region
        regionOrder.append(identifier)
        locationManager.startMonitoring(for: region)
        locationManager.requestState(for: region)

        Log.geofence.info("Added region: \(identifier)")
    }

    func removeRegion(identifier: String) {
        guard let region = activeRegions[identifier] else { return }
        locationManager.stopMonitoring(for: region)
        activeRegions.removeValue(forKey: identifier)
        regionOrder.removeAll { $0 == identifier }
        Log.geofence.info("Removed region: \(identifier)")
    }

    func clearAll() {
        for (_, region) in activeRegions {
            locationManager.stopMonitoring(for: region)
        }
        activeRegions.removeAll()
        regionOrder.removeAll()
        Log.geofence.info("Cleared all regions")
    }

    /// For testing: get current FIFO order
    var currentRegionOrder: [String] { regionOrder }
}

extension GeofenceManager: CLLocationManagerDelegate {
    func locationManager(_ manager: CLLocationManager, didEnterRegion region: CLRegion) {
        Log.geofence.info("Entered: \(region.identifier)")
        delegate?.geofenceManager(self, didEnterRegion: region.identifier)
    }

    func locationManager(_ manager: CLLocationManager, didExitRegion region: CLRegion) {
        Log.geofence.info("Exited: \(region.identifier)")
        delegate?.geofenceManager(self, didExitRegion: region.identifier)
    }

    func locationManager(_ manager: CLLocationManager, didDetermineState state: CLRegionState, for region: CLRegion) {
        if state == .inside {
            Log.geofence.info("Already inside: \(region.identifier)")
            delegate?.geofenceManager(self, didEnterRegion: region.identifier)
        }
    }

    func locationManager(_ manager: CLLocationManager, monitoringDidFailFor region: CLRegion?, withError error: Error) {
        Log.geofence.error("Monitoring failed: \(region?.identifier ?? "unknown") - \(error.localizedDescription)")
    }
}
