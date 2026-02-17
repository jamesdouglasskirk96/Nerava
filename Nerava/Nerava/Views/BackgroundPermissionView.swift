import SwiftUI

struct BackgroundPermissionView: View {
    let onContinue: () -> Void
    let onNotNow: () -> Void
    private let brandBlue = Color(red: 0.09, green: 0.47, blue: 0.95)

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "location.fill.viewfinder")
                .font(.system(size: 40))
                .foregroundColor(brandBlue)
                .accessibilityHidden(true)

            Text("Allow Background Location")
                .font(.title2)
                .bold()
                .multilineTextAlignment(.center)
                .accessibilityAddTraits(.isHeader)

            Text("This lets Nerava notify you when you arrive at the merchant while your phone is in your pocket.")
                .font(.body)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
                .fixedSize(horizontal: false, vertical: true)

            HStack(spacing: 12) {
                Button("Not now") { onNotNow() }
                    .padding()
                    .frame(maxWidth: .infinity)
                    .accessibilityHint("Dismiss background location permission prompt")

                Button("Continue") { onContinue() }
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(brandBlue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                    .accessibilityHint("Open the system background location permission prompt")
            }
            .padding(.horizontal)
        }
        .padding()
        .background(.ultraThinMaterial)
        .cornerRadius(16)
        .padding()
    }
}
