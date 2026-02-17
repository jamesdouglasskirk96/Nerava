import SwiftUI

@main
struct NeravaApp: App {
    @StateObject private var locationService: LocationService
    @StateObject private var sessionEngine: SessionEngine
    @State private var pendingDeepLinkURL: URL?

    init() {
        // Single instance creation - these are the ONLY instances
        let location = LocationService()
        let geofence = GeofenceManager()
        let api = APIClient()

        _locationService = StateObject(wrappedValue: location)
        _sessionEngine = StateObject(wrappedValue: SessionEngine(
            locationService: location,
            geofenceManager: geofence,
            apiClient: api,
            config: .defaults
        ))
    }

    var body: some Scene {
        WindowGroup {
            ContentView(pendingDeepLinkURL: $pendingDeepLinkURL)
                .environmentObject(locationService)
                .environmentObject(sessionEngine)
                .onOpenURL { url in
                    // Handle Universal Links and custom scheme deep links
                    if let resolvedURL = DeepLinkHandler.resolveWebURL(from: url) {
                        pendingDeepLinkURL = resolvedURL
                    }
                }
        }
    }
}
