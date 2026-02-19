package network.nerava.app.auth

import android.content.Context
import android.util.Log
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/**
 * Secure token storage using EncryptedSharedPreferences.
 * Android equivalent of iOS Keychain with kSecAttrAccessibleAfterFirstUnlock.
 */
class SecureTokenStore(context: Context) {

    private val prefs = try {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

        EncryptedSharedPreferences.create(
            context,
            PREFS_NAME,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    } catch (e: Exception) {
        Log.e(TAG, "Failed to create EncryptedSharedPreferences, falling back to regular prefs", e)
        context.getSharedPreferences(PREFS_NAME_FALLBACK, Context.MODE_PRIVATE)
    }

    fun setAccessToken(token: String) {
        prefs.edit().putString(KEY_ACCESS_TOKEN, token).apply()
    }

    fun getAccessToken(): String? {
        return prefs.getString(KEY_ACCESS_TOKEN, null)
    }

    fun clearAccessToken() {
        prefs.edit().remove(KEY_ACCESS_TOKEN).apply()
    }

    fun setFCMToken(token: String) {
        prefs.edit().putString(KEY_FCM_TOKEN, token).apply()
    }

    fun getFCMToken(): String? {
        return prefs.getString(KEY_FCM_TOKEN, null)
    }

    companion object {
        private const val TAG = "SecureTokenStore"
        private const val PREFS_NAME = "nerava_secure_prefs"
        private const val PREFS_NAME_FALLBACK = "nerava_prefs_fallback"
        private const val KEY_ACCESS_TOKEN = "access_token"
        private const val KEY_FCM_TOKEN = "fcm_token"
    }
}
