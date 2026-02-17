import SwiftUI
import CoreLocation

struct ContentView: View {
    @EnvironmentObject private var locationService: LocationService
    @EnvironmentObject private var sessionEngine: SessionEngine
    @Binding var pendingDeepLinkURL: URL?

    @State private var showWhenInUseRationale = false
    @State private var showAlwaysRationale = false

    var body: some View {
        ZStack {
            WebViewContainer(pendingDeepLinkURL: $pendingDeepLinkURL)
                .environmentObject(locationService)
                .environmentObject(sessionEngine)

            // Rationale overlays (shown BEFORE system prompt)
            if showWhenInUseRationale {
                LocationPermissionView(
                    onContinue: {
                        showWhenInUseRationale = false
                        locationService.requestWhenInUsePermission()
                    },
                    onNotNow: {
                        showWhenInUseRationale = false
                    }
                )
            } else if showAlwaysRationale {
                BackgroundPermissionView(
                    onContinue: {
                        showAlwaysRationale = false
                        locationService.requestAlwaysPermission()
                    },
                    onNotNow: {
                        showAlwaysRationale = false
                    }
                )
            } else if sessionEngine.shouldShowNotificationRationale {
                NotificationPermissionView(
                    onContinue: {
                        sessionEngine.shouldShowNotificationRationale = false
                        NotificationService.shared.requestPermissionIfNeeded()
                    },
                    onNotNow: {
                        sessionEngine.shouldShowNotificationRationale = false
                    }
                )
            }
        }
        .onAppear {
            // Fresh install: show rationale BEFORE prompting
            if locationService.authorizationStatus == .notDetermined {
                showWhenInUseRationale = true
            }
        }
        .onChange(of: locationService.authorizationStatus) { status in
            // If user granted when-in-use, app works. Later you can trigger Always rationale
            if status == .authorizedWhenInUse {
                // Do nothing automatically; web can request Always.
                // But we keep the view hooks for a later UX trigger.
            }
        }
    }
}
