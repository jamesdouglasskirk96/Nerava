import SwiftUI
import UIKit
import UserNotifications

// MARK: - AppDelegate for Remote Notification Handling

class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {

    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        UNUserNotificationCenter.current().delegate = self
        return true
    }

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

    // MARK: - UNUserNotificationCenterDelegate

    /// Handle notification tap (app was in background or closed)
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        let userInfo = response.notification.request.content.userInfo
        let pushType = userInfo["type"] as? String ?? "unknown"
        let deepLink = userInfo["deep_link"] as? String

        Log.app.info("Push notification tapped: type=\(pushType)")

        // Forward to web app via NativeBridge
        NotificationCenter.default.post(
            name: .didReceivePushDeepLink,
            object: nil,
            userInfo: [
                "type": pushType,
                "deep_link": deepLink ?? "",
                "data": userInfo,
            ]
        )
        completionHandler()
    }

    /// Show notification banner even when app is in foreground
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        completionHandler([.banner, .sound])
    }
}

extension Notification.Name {
    static let didReceiveAPNsToken = Notification.Name("didReceiveAPNsToken")
    static let didReceivePushDeepLink = Notification.Name("didReceivePushDeepLink")
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
