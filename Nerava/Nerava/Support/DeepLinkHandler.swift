import Foundation

enum DeepLinkHandler {
    /// Resolves incoming URL to web app URL for loading in WebView
    /// Supports:
    /// - Universal Links: https://app.nerava.network/...
    /// - Custom scheme: nerava://merchant/{id}, nerava://session/{id}
    static func resolveWebURL(from url: URL) -> URL? {
        // Universal Link - use as-is if it's our domain
        if url.scheme == "https" && isOurDomain(url.host) {
            return url
        }

        // Custom scheme: nerava://
        if url.scheme == "nerava" {
            return resolveCustomScheme(url)
        }

        return nil
    }

    private static func isOurDomain(_ host: String?) -> Bool {
        guard let host = host else { return false }
        return host == "app.nerava.network" || host == "link.nerava.network"
    }

    private static func resolveCustomScheme(_ url: URL) -> URL? {
        let baseURL = Environment.current.webAppURL
        let path = url.path

        // nerava://merchant/123 -> https://app.nerava.network/merchant/123
        // nerava://session/abc -> https://app.nerava.network/session/abc
        // nerava://exclusive/xyz -> https://app.nerava.network/exclusive/xyz
        if !path.isEmpty {
            return baseURL.appendingPathComponent(path)
        }

        // Fallback to base URL
        return baseURL
    }

    /// Supported deep link paths
    static let supportedPaths = [
        "/merchant/",      // Merchant detail: /merchant/{id}
        "/session/",       // Active session: /session/{id}
        "/exclusive/",     // Exclusive detail: /exclusive/{id}
        "/s/",             // Short link: /s/{code}
        "/m/"              // Short merchant link: /m/{merchantId}
    ]
}
