import Foundation

enum Environment {
    case development
    case staging
    case production

    static var current: Environment {
        #if DEBUG
        return .development
        #else
        return .production
        #endif
    }

    var webAppURL: URL {
        switch self {
        case .development:
            // Use production for screenshots/testing
            return URL(string: "https://app.nerava.network")!
        case .staging:
            return URL(string: "https://staging.nerava.network")!
        case .production:
            return URL(string: "https://app.nerava.network")!
        }
    }

    var apiBaseURL: URL {
        switch self {
        case .development:
            // Use production for screenshots/testing
            return URL(string: "https://api.nerava.network")!
        case .staging:
            return URL(string: "https://staging-api.nerava.network")!
        case .production:
            return URL(string: "https://api.nerava.network")!
        }
    }

    var allowedWebOrigins: Set<String> {
        var origins: Set<String> = [
            "https://app.nerava.network",
            "https://staging.nerava.network"
        ]
        #if DEBUG
        origins.insert("http://localhost:5173")
        origins.insert("http://localhost:5174")
        origins.insert("http://127.0.0.1:5173")
        #endif
        return origins
    }

    var isDebug: Bool {
        #if DEBUG
        return true
        #else
        return false
        #endif
    }
}
