import Foundation
import os

/// Persisted state for recovery after app termination.
/// Saved on every state transition and target change.
///
/// NOTE: Geofences are NOT stored here. They are derived from state on restore.
/// Snapshot stores inputs (state, targets, deadlines), not outputs (geofences).
struct SessionSnapshot: Codable {
    let state: SessionState
    let targetedCharger: ChargerTarget?
    let merchantTarget: MerchantTarget?
    let activeSession: ActiveSessionInfo?
    let gracePeriodDeadline: Date?
    let hardTimeoutDeadline: Date?
    let savedAt: Date

    /// Full pending event for idempotent retry. If set, the last transition's event
    /// may not have been acknowledged. Retry with same eventId on restore.
    let pendingEvent: PendingEvent?

    private static let storageKey = "com.nerava.sessionSnapshot"

    // MARK: - Persistence

    static func save(_ snapshot: SessionSnapshot) {
        do {
            let data = try JSONEncoder().encode(snapshot)
            UserDefaults.standard.set(data, forKey: storageKey)
            UserDefaults.standard.synchronize()
        } catch {
            Log.session.error("Failed to save snapshot: \(error.localizedDescription)")
        }
    }

    static func load() -> SessionSnapshot? {
        guard let data = UserDefaults.standard.data(forKey: storageKey) else {
            return nil
        }
        do {
            return try JSONDecoder().decode(SessionSnapshot.self, from: data)
        } catch {
            Log.session.error("Failed to load snapshot: \(error.localizedDescription)")
            return nil
        }
    }

    static func clear() {
        UserDefaults.standard.removeObject(forKey: storageKey)
    }
}
