import SwiftUI

struct NotificationPermissionView: View {
    let onContinue: () -> Void
    let onNotNow: () -> Void

    private let brandBlue = Color(red: 0.09, green: 0.47, blue: 0.95)

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "bell.badge.fill")
                .font(.system(size: 40))
                .foregroundColor(brandBlue)
                .accessibilityHidden(true)

            Text("Enable Notifications")
                .font(.title2)
                .bold()
                .multilineTextAlignment(.center)
                .accessibilityAddTraits(.isHeader)

            Text("Turn on notifications so Nerava can alert you when your exclusive is activated or when you arrive at the merchant.")
                .font(.body)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
                .fixedSize(horizontal: false, vertical: true)

            HStack(spacing: 12) {
                Button("Not now") { onNotNow() }
                    .padding()
                    .frame(maxWidth: .infinity)
                    .accessibilityHint("Dismiss notification permission")

                Button("Continue") { onContinue() }
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(brandBlue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                    .accessibilityHint("Open the system notification prompt")
            }
            .padding(.horizontal)
        }
        .padding()
        .background(.ultraThinMaterial)
        .cornerRadius(16)
        .padding()
    }
}
