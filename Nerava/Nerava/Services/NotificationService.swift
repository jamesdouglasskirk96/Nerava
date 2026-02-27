import Foundation
import UserNotifications
import UIKit

final class NotificationService {
    static let shared = NotificationService()
    private init() {}

    private let permissionRequestedKey = "notification_permission_requested"
    private let rationaleShownKey = "notification_permission_rationale_shown"

    /// Stored APNs device token (hex string), set by AppDelegate
    var apnsDeviceToken: String?

    func shouldShowRationale(completion: @escaping (Bool) -> Void) {
        let defaults = UserDefaults.standard
        if defaults.bool(forKey: rationaleShownKey) || defaults.bool(forKey: permissionRequestedKey) {
            completion(false)
            return
        }

        UNUserNotificationCenter.current().getNotificationSettings { settings in
            completion(settings.authorizationStatus == .notDetermined)
        }
    }

    func markRationaleShown() {
        UserDefaults.standard.set(true, forKey: rationaleShownKey)
    }

    func requestPermissionIfNeeded(completion: ((Bool) -> Void)? = nil) {
        let defaults = UserDefaults.standard
        if defaults.bool(forKey: permissionRequestedKey) {
            completion?(false)
            return
        }

        UNUserNotificationCenter.current().getNotificationSettings { settings in
            guard settings.authorizationStatus == .notDetermined else {
                completion?(false)
                return
            }

            defaults.set(true, forKey: self.permissionRequestedKey)
            UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, _ in
                if granted {
                    // Register for remote notifications after permission granted
                    DispatchQueue.main.async {
                        UIApplication.shared.registerForRemoteNotifications()
                    }
                }
                completion?(granted)
            }
        }
    }

    func showSessionActiveNotification() {
        let content = UNMutableNotificationContent()
        content.title = "You're all set!"
        content.body = "Head to the merchant to unlock your exclusive deal."
        content.sound = .default

        let request = UNNotificationRequest(
            identifier: "session_active",
            content: content,
            trigger: nil
        )
        UNUserNotificationCenter.current().add(request)
    }

    func showAtMerchantNotification() {
        let content = UNMutableNotificationContent()
        content.title = "You've arrived!"
        content.body = "Show your code to the merchant to redeem your exclusive."
        content.sound = .default

        let request = UNNotificationRequest(
            identifier: "at_merchant",
            content: content,
            trigger: nil
        )
        UNUserNotificationCenter.current().add(request)
    }
}
