import Foundation

// MARK: - Session State

enum SessionState: String, Codable {
    case idle = "IDLE"
    case nearCharger = "NEAR_CHARGER"
    case anchored = "ANCHORED"
    case sessionActive = "SESSION_ACTIVE"
    case inTransit = "IN_TRANSIT"
    case atMerchant = "AT_MERCHANT"
    case sessionEnded = "SESSION_ENDED"
}

// MARK: - Session Events (Canonical - No Duplicates)

/// Each semantic event has exactly ONE enum case.
/// Use `requiresSessionId` to determine routing (pre-session vs session endpoint).
enum SessionEvent: String, Codable {
    // Pre-session events (no session_id yet)
    case chargerTargeted = "charger_targeted"
    case enteredChargerIntentZone = "entered_charger_intent_zone"
    case exitedChargerIntentZone = "exited_charger_intent_zone"
    case anchorDwellComplete = "anchor_dwell_complete"
    case anchorLost = "anchor_lost"
    case activationRejected = "activation_rejected"

    // Session events (has session_id)
    case exclusiveActivatedByWeb = "exclusive_activated"
    case departedCharger = "departed_charger"
    case enteredMerchantZone = "entered_merchant_zone"
    case visitVerifiedByWeb = "visit_verified"
    case gracePeriodExpired = "grace_period_expired"
    case hardTimeoutExpired = "hard_timeout_expired"
    case webRequestedEnd = "web_requested_end"
    case sessionRestored = "session_restored"

    /// Determines whether this event requires a session_id (routes to session endpoint)
    /// or can be sent without one (routes to pre-session endpoint).
    var requiresSessionId: Bool {
        switch self {
        case .chargerTargeted,
             .enteredChargerIntentZone,
             .exitedChargerIntentZone,
             .anchorDwellComplete,
             .anchorLost,
             .activationRejected:
            return false
        case .exclusiveActivatedByWeb,
             .departedCharger,
             .enteredMerchantZone,
             .visitVerifiedByWeb,
             .gracePeriodExpired,
             .hardTimeoutExpired,
             .webRequestedEnd,
             .sessionRestored:
            return true
        }
    }
}

// MARK: - Supporting Types

struct ChargerTarget: Codable, Equatable {
    let id: String
    let latitude: Double
    let longitude: Double
}

struct MerchantTarget: Codable, Equatable {
    let id: String
    let latitude: Double
    let longitude: Double
}

struct ActiveSessionInfo: Codable, Equatable {
    let sessionId: String
    let chargerId: String
    let merchantId: String
    let startedAt: Date
}

/// Full pending event payload for retry on restore.
/// Persisted in snapshot so we can resend if crash/kill before ack.
struct PendingEvent: Codable, Equatable {
    let eventId: String
    let eventName: String
    let requiresSessionId: Bool
    let sessionId: String?
    let chargerId: String?
    let occurredAt: Date
    let metadata: [String: String]  // Simplified for Codable
}
