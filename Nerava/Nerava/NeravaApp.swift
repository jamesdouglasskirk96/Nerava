import SwiftUI
import UIKit

// MARK: - AppDelegate for Remote Notification Handling

class AppDelegate: NSObject, UIApplicationDelegate {
    func application(
        _ application: UIApplication,
        didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data
    ) {
        let tokenString = deviceToken.map { String(format: "%02x", $0) }.joined()
        Log.app.info("APNs device token: \(tokenString)")
        // Store token for forwarding to web app via native bridge
        NotificationService.shared.apnsDeviceToken = tokenString
        // Post notification so any active bridge can forward the token
        NotificationCenter.default.post(
            name: .didReceiveAPNsToken,
            object: nil,
            userInfo: ["token": tokenString]
        )
    }

    func application(
        _ application: UIApplication,
        didFailToRegisterForRemoteNotificationsWithError error: Error
    ) {
        Log.app.error("Failed to register for remote notifications: \(error.localizedDescription)")
    }
}

extension Notification.Name {
    static let didReceiveAPNsToken = Notification.Name("didReceiveAPNsToken")
}

@main
struct NeravaApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
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
