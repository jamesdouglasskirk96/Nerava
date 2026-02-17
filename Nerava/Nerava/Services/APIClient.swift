import Foundation
import UIKit
import os

final class APIClient: APIClientProtocol {
    private let baseURL: URL
    private var accessToken: String?
    private let session: URLSession
    private let maxRetries = 3
    private let baseRetryDelay: TimeInterval = 1.0
    private static let iso8601Formatter = ISO8601DateFormatter()

    init(baseURL: URL = Environment.current.apiBaseURL) {
        self.baseURL = baseURL
        self.accessToken = KeychainService.shared.getAccessToken()

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
        self.session = URLSession(configuration: config)
    }

    func setAuthToken(_ token: String) {
        self.accessToken = token
    }

    // MARK: - Session Events

    func emitSessionEvent(
        sessionId: String,
        event: String,
        eventId: String,
        occurredAt: Date,
        metadata: [String: String]? = nil
    ) async throws {
        let url = baseURL.appendingPathComponent("/v1/native/session-events")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let token = accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let appState: String = await MainActor.run {
            UIApplication.shared.applicationState == .background ? "background" : "foreground"
        }

        var body: [String: Any] = [
            "schema_version": "1.0",
            "event_id": eventId,
            "idempotency_key": eventId,
            "session_id": sessionId,
            "event": event,
            "occurred_at": Self.iso8601Formatter.string(from: occurredAt),
            "timestamp": Self.iso8601Formatter.string(from: Date()),
            "source": "ios_native",
            "app_state": appState
        ]
        if let metadata = metadata {
            body["metadata"] = metadata
        }

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        try await executeWithRetry(request: request, eventId: eventId, event: event)
    }

    // MARK: - Pre-Session Events

    func emitPreSessionEvent(
        event: String,
        chargerId: String?,
        eventId: String,
        occurredAt: Date,
        metadata: [String: String]? = nil
    ) async throws {
        let url = baseURL.appendingPathComponent("/v1/native/pre-session-events")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let token = accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        var body: [String: Any] = [
            "schema_version": "1.0",
            "event_id": eventId,
            "idempotency_key": eventId,
            "event": event,
            "occurred_at": Self.iso8601Formatter.string(from: occurredAt),
            "timestamp": Self.iso8601Formatter.string(from: Date()),
            "source": "ios_native"
        ]
        if let chargerId = chargerId {
            body["charger_id"] = chargerId
        }
        if let metadata = metadata {
            body["metadata"] = metadata
        }

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        try await executeWithRetry(request: request, eventId: eventId, event: event)
    }

    // MARK: - Config

    func fetchConfig() async throws -> SessionConfig {
        let url = baseURL.appendingPathComponent("/v1/native/config")
        var request = URLRequest(url: url)

        if let token = accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let (data, _) = try await session.data(for: request)
        return try JSONDecoder().decode(SessionConfig.self, from: data)
    }

    // MARK: - Retry Logic

    private func executeWithRetry(request: URLRequest, eventId: String, event: String) async throws {
        // CRITICAL: Do NOT modify `request` or its `httpBody` in this method.
        // The request body contains `event_id` which MUST remain identical across retries.
        // Any mutation would break backend idempotency deduplication.
        var lastError: Error?

        for attempt in 0..<maxRetries {
            do {
                let (data, response) = try await session.data(for: request)

                guard let httpResponse = response as? HTTPURLResponse else {
                    throw APIError.invalidResponse
                }

                switch httpResponse.statusCode {
                case 200...299:
                    if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let status = json["status"] as? String,
                       status == "already_processed" {
                        Log.api.info("Event already processed: \(event) (id=\(eventId.suffix(6)))")
                    } else {
                        Log.api.info("Event sent: \(event) (id=\(eventId.suffix(6)))")
                    }
                    return

                case 401, 403:
                    Log.api.error("Auth error (\(httpResponse.statusCode)) for event: \(event)")
                    throw APIError.authRequired

                case 429:
                    let delay = baseRetryDelay * pow(2.0, Double(attempt)) + Double.random(in: 0...0.5)
                    Log.api.warning("Rate limited, retrying in \(String(format: "%.1f", delay))s (attempt \(attempt + 1)/\(self.maxRetries))")
                    try await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
                    continue

                case 500...599:
                    let delay = baseRetryDelay * pow(2.0, Double(attempt)) + Double.random(in: 0...0.5)
                    Log.api.warning("Server error \(httpResponse.statusCode), retrying in \(String(format: "%.1f", delay))s")
                    try await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
                    continue

                default:
                    throw APIError.requestFailed(statusCode: httpResponse.statusCode)
                }

            } catch let error as APIError {
                throw error
            } catch {
                lastError = error
                if attempt < maxRetries - 1 {
                    let delay = baseRetryDelay * pow(2.0, Double(attempt))
                    Log.api.warning("Network error, retrying in \(String(format: "%.1f", delay))s: \(error.localizedDescription)")
                    try? await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
                }
            }
        }

        Log.api.error("Event emission failed after \(self.maxRetries) attempts: \(event)")
        throw lastError ?? APIError.requestFailed(statusCode: 0)
    }

    enum APIError: Error {
        case requestFailed(statusCode: Int)
        case invalidResponse
        case authRequired
    }
}

// MARK: - Protocol for Testing

protocol APIClientProtocol {
    func setAuthToken(_ token: String)
    func emitSessionEvent(sessionId: String, event: String, eventId: String, occurredAt: Date, metadata: [String: String]?) async throws
    func emitPreSessionEvent(event: String, chargerId: String?, eventId: String, occurredAt: Date, metadata: [String: String]?) async throws
    func fetchConfig() async throws -> SessionConfig
}
