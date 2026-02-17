import SwiftUI

struct LocationPermissionView: View {
    let onContinue: () -> Void
    let onNotNow: () -> Void
    private let brandBlue = Color(red: 0.09, green: 0.47, blue: 0.95)

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "location.fill")
                .font(.system(size: 40))
                .foregroundColor(brandBlue)
                .accessibilityHidden(true)

            Text("Enable Location")
                .font(.title2)
                .bold()
                .multilineTextAlignment(.center)
                .accessibilityAddTraits(.isHeader)

            Text("Nerava needs your location to detect when you arrive at an EV charger and unlock nearby merchant exclusives.")
                .font(.body)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
                .fixedSize(horizontal: false, vertical: true)

            HStack(spacing: 12) {
                Button("Not now") { onNotNow() }
                    .padding()
                    .frame(maxWidth: .infinity)
                    .accessibilityHint("Dismiss location permission prompt")

                Button("Continue") { onContinue() }
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(brandBlue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                    .accessibilityHint("Open the system location permission prompt")
            }
            .padding(.horizontal)
        }
        .padding()
        .background(.ultraThinMaterial)
        .cornerRadius(16)
        .padding()
    }
}
