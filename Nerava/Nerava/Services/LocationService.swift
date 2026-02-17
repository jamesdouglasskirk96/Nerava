import CoreLocation
import Combine
import os

final class LocationService: NSObject, ObservableObject {
    private let locationManager = CLLocationManager()

    @Published private(set) var currentLocation: CLLocation?
    @Published private(set) var authorizationStatus: CLAuthorizationStatus = .notDetermined

    private var isHighAccuracyMode = false

    var locationUpdates: AnyPublisher<CLLocation, Never> {
        $currentLocation.compactMap { $0 }.eraseToAnyPublisher()
    }

    override init() {
        super.init()
        locationManager.delegate = self
        locationManager.allowsBackgroundLocationUpdates = true
        locationManager.pausesLocationUpdatesAutomatically = false
        authorizationStatus = locationManager.authorizationStatus

        // Initialize to low accuracy mode settings (but don't start yet)
        locationManager.desiredAccuracy = kCLLocationAccuracyHundredMeters
        locationManager.distanceFilter = 100

        // Start monitoring on init if already authorized
        // This ensures we get location updates even in When-In-Use mode
        if authorizationStatus == .authorizedAlways || authorizationStatus == .authorizedWhenInUse {
            startMonitoring()
        }
    }

    func requestWhenInUsePermission() {
        locationManager.requestWhenInUseAuthorization()
    }

    func requestAlwaysPermission() {
        locationManager.requestAlwaysAuthorization()
    }

    func startMonitoring() {
        // Always start standard location updates to get at least one fix
        // This works for both Always and When-In-Use authorization
        locationManager.startUpdatingLocation()

        // For Always authorization, also use significant location changes for background
        if authorizationStatus == .authorizedAlways {
            locationManager.startMonitoringSignificantLocationChanges()
        }

        Log.location.info("Started monitoring (auth=\(self.authorizationStatus.description), highAccuracy=\(self.isHighAccuracyMode))")
    }

    func stopMonitoring() {
        locationManager.stopUpdatingLocation()
        locationManager.stopMonitoringSignificantLocationChanges()
    }

    func setHighAccuracyMode(_ enabled: Bool) {
        guard enabled != isHighAccuracyMode else { return }
        isHighAccuracyMode = enabled

        if enabled {
            locationManager.desiredAccuracy = kCLLocationAccuracyBest
            locationManager.distanceFilter = 5
            Log.location.info("High accuracy mode ON")
        } else {
            locationManager.desiredAccuracy = kCLLocationAccuracyHundredMeters
            locationManager.distanceFilter = 100
            Log.location.info("High accuracy mode OFF")
        }

        // Restart updates to apply new settings
        if authorizationStatus == .authorizedAlways || authorizationStatus == .authorizedWhenInUse {
            locationManager.stopUpdatingLocation()
            locationManager.startUpdatingLocation()
        }
    }
}

extension LocationService: CLLocationManagerDelegate {
    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        currentLocation = locations.last
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        authorizationStatus = manager.authorizationStatus
        Log.location.info("Authorization changed: \(self.authorizationStatus.description)")

        if authorizationStatus == .authorizedAlways || authorizationStatus == .authorizedWhenInUse {
            startMonitoring()
        }
    }
}

extension CLAuthorizationStatus {
    var description: String {
        switch self {
        case .notDetermined: return "notDetermined"
        case .restricted: return "restricted"
        case .denied: return "denied"
        case .authorizedAlways: return "authorizedAlways"
        case .authorizedWhenInUse: return "authorizedWhenInUse"
        @unknown default: return "unknown"
        }
    }
}
