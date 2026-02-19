package network.nerava.app.engine

import android.content.Context
import android.util.Log
import org.json.JSONObject

/**
 * Persists session state to SharedPreferences for crash/kill recovery.
 * Mirrors iOS SessionSnapshot stored in UserDefaults.
 */
class SessionSnapshot(context: Context) {

    private val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun save(
        state: SessionState,
        chargerTarget: ChargerTarget?,
        merchantTarget: MerchantTarget?,
        activeSession: ActiveSessionInfo?,
        gracePeriodDeadline: Long?,
        hardTimeoutDeadline: Long?,
    ) {
        val json = JSONObject().apply {
            put("state", state.raw)
            put("savedAt", System.currentTimeMillis())

            chargerTarget?.let {
                put("chargerTarget", JSONObject().apply {
                    put("id", it.id)
                    put("lat", it.latitude)
                    put("lng", it.longitude)
                })
            }

            merchantTarget?.let {
                put("merchantTarget", JSONObject().apply {
                    put("id", it.id)
                    put("lat", it.latitude)
                    put("lng", it.longitude)
                })
            }

            activeSession?.let {
                put("activeSession", JSONObject().apply {
                    put("sessionId", it.sessionId)
                    put("chargerId", it.chargerId)
                    put("merchantId", it.merchantId)
                    put("startedAt", it.startedAt)
                })
            }

            gracePeriodDeadline?.let { put("gracePeriodDeadline", it) }
            hardTimeoutDeadline?.let { put("hardTimeoutDeadline", it) }
        }

        prefs.edit().putString(KEY_SNAPSHOT, json.toString()).apply()
    }

    fun restore(): SnapshotData? {
        val raw = prefs.getString(KEY_SNAPSHOT, null) ?: return null

        return try {
            val json = JSONObject(raw)

            val state = SessionState.fromRaw(json.getString("state")) ?: return null
            val savedAt = json.getLong("savedAt")

            val chargerTarget = json.optJSONObject("chargerTarget")?.let {
                ChargerTarget(it.getString("id"), it.getDouble("lat"), it.getDouble("lng"))
            }

            val merchantTarget = json.optJSONObject("merchantTarget")?.let {
                MerchantTarget(it.getString("id"), it.getDouble("lat"), it.getDouble("lng"))
            }

            val activeSession = json.optJSONObject("activeSession")?.let {
                ActiveSessionInfo(
                    it.getString("sessionId"),
                    it.getString("chargerId"),
                    it.getString("merchantId"),
                    it.getLong("startedAt"),
                )
            }

            SnapshotData(
                state = state,
                savedAt = savedAt,
                chargerTarget = chargerTarget,
                merchantTarget = merchantTarget,
                activeSession = activeSession,
                gracePeriodDeadline = if (json.has("gracePeriodDeadline")) json.getLong("gracePeriodDeadline") else null,
                hardTimeoutDeadline = if (json.has("hardTimeoutDeadline")) json.getLong("hardTimeoutDeadline") else null,
            )
        } catch (e: Exception) {
            Log.e(TAG, "Failed to restore snapshot", e)
            null
        }
    }

    fun clear() {
        prefs.edit().remove(KEY_SNAPSHOT).apply()
    }

    data class SnapshotData(
        val state: SessionState,
        val savedAt: Long,
        val chargerTarget: ChargerTarget?,
        val merchantTarget: MerchantTarget?,
        val activeSession: ActiveSessionInfo?,
        val gracePeriodDeadline: Long?,
        val hardTimeoutDeadline: Long?,
    )

    companion object {
        private const val TAG = "SessionSnapshot"
        private const val PREFS_NAME = "nerava_session_snapshot"
        private const val KEY_SNAPSHOT = "snapshot"
    }
}
