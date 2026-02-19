package network.nerava.app.location

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.os.Looper
import android.util.Log
import androidx.core.content.ContextCompat
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority

/**
 * Wraps FusedLocationProviderClient. Mirrors iOS LocationService.
 *
 * Two modes:
 * - Low accuracy: 100m filter, BALANCED_POWER (default)
 * - High accuracy: 5m filter, HIGH_ACCURACY (when near charger)
 */
class LocationService(private val context: Context) {

    private val fusedClient: FusedLocationProviderClient =
        LocationServices.getFusedLocationProviderClient(context)

    @Volatile
    var currentLocation: Location? = null
        private set

    private var locationCallback: LocationCallback? = null
    private var isHighAccuracy = false

    var onLocationUpdate: ((Location) -> Unit)? = null

    // Listener for permission request trigger (activity handles the actual request)
    var onRequestBackgroundPermission: (() -> Unit)? = null

    val hasForegroundPermission: Boolean
        get() = ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) ==
                PackageManager.PERMISSION_GRANTED

    val hasBackgroundPermission: Boolean
        get() = ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_BACKGROUND_LOCATION) ==
                PackageManager.PERMISSION_GRANTED

    fun requestBackgroundPermission() {
        onRequestBackgroundPermission?.invoke()
    }

    fun startLocationUpdates(highAccuracy: Boolean = false) {
        if (!hasForegroundPermission) {
            Log.w(TAG, "No location permission, cannot start updates")
            return
        }

        // Stop existing if accuracy mode changed
        if (locationCallback != null && isHighAccuracy != highAccuracy) {
            stopLocationUpdates()
        }

        if (locationCallback != null) return // Already running

        isHighAccuracy = highAccuracy

        val request = if (highAccuracy) {
            LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 2000L)
                .setMinUpdateDistanceMeters(5f)
                .setMinUpdateIntervalMillis(1000L)
                .build()
        } else {
            LocationRequest.Builder(Priority.PRIORITY_BALANCED_POWER_ACCURACY, 10000L)
                .setMinUpdateDistanceMeters(100f)
                .setMinUpdateIntervalMillis(5000L)
                .build()
        }

        val callback = object : LocationCallback() {
            override fun onLocationResult(result: LocationResult) {
                result.lastLocation?.let { location ->
                    currentLocation = location
                    onLocationUpdate?.invoke(location)
                }
            }
        }

        locationCallback = callback

        try {
            fusedClient.requestLocationUpdates(request, callback, Looper.getMainLooper())
            Log.i(TAG, "Location updates started (highAccuracy=$highAccuracy)")
        } catch (e: SecurityException) {
            Log.e(TAG, "SecurityException starting location updates", e)
            locationCallback = null
        }
    }

    fun stopLocationUpdates() {
        locationCallback?.let {
            fusedClient.removeLocationUpdates(it)
            locationCallback = null
            Log.i(TAG, "Location updates stopped")
        }
    }

    fun switchToHighAccuracy() {
        if (!isHighAccuracy) {
            startLocationUpdates(highAccuracy = true)
        }
    }

    fun switchToLowAccuracy() {
        if (isHighAccuracy) {
            startLocationUpdates(highAccuracy = false)
        }
    }

    companion object {
        private const val TAG = "LocationService"
    }
}
