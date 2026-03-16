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
    private let maxRegions = 20

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

    /// Replace all charger geofences with a new set from the web app's visible chargers.
    /// Prioritizes target charger (tighter 200m radius), then nearest chargers (250m).
    func updateChargerGeofences(_ chargers: [(id: String, lat: Double, lng: Double)],
                                 targetChargerId: String? = nil) {
        // Remove existing charger geofences (keep merchant geofences)
        let chargerKeys = activeRegions.keys.filter { $0.hasPrefix("charger_") }
        for key in chargerKeys {
            removeRegion(identifier: key)
        }

        // Add target charger first with tighter radius
        var added = 0
        let maxChargerRegions = maxRegions - activeRegions.count  // leave room for merchant geofences

        if let targetId = targetChargerId,
           let target = chargers.first(where: { $0.id == targetId }) {
            addChargerGeofence(
                id: target.id,
                coordinate: CLLocationCoordinate2D(latitude: target.lat, longitude: target.lng),
                radius: 200  // tighter for primary target
            )
            added += 1
        }

        // Add remaining chargers with standard radius
        for charger in chargers where charger.id != targetChargerId && added < maxChargerRegions {
            addChargerGeofence(
                id: charger.id,
                coordinate: CLLocationCoordinate2D(latitude: charger.lat, longitude: charger.lng),
                radius: 250
            )
            added += 1
        }

        Log.geofence.info("Updated charger geofences: \(added) chargers registered")
    }

    private func addRegion(identifier: String, coordinate: CLLocationCoordinate2D, radius: Double, notifyOnExit: Bool) {
        // If this region already exists, remove it first to update
        if activeRegions[identifier] != nil {
            removeRegion(identifier: identifier)
        }

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
