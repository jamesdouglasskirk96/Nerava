package network.nerava.app.engine

import android.location.Location
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.JUnit4

@RunWith(JUnit4::class)
class DwellDetectorTest {

    private lateinit var detector: DwellDetector

    @Before
    fun setUp() {
        val config = SessionConfig(
            chargerAnchorRadiusM = 30.0,
            chargerDwellSeconds = 2, // Short for testing
            speedThresholdForDwellMps = 1.5,
        )
        detector = DwellDetector(config)
    }

    private fun makeLocation(speed: Float = 0f, hasSpeed: Boolean = true): Location {
        return Location("test").apply {
            latitude = 29.42
            longitude = -98.49
            this.speed = speed
            // Note: Location.hasSpeed() is based on whether speed was set
        }
    }

    @Test
    fun `not anchored initially`() {
        assertFalse(detector.isAnchored)
    }

    @Test
    fun `not anchored when outside radius`() {
        val location = makeLocation(speed = 0f)
        detector.recordLocation(location, 50.0) // 50m > 30m radius
        assertFalse(detector.isAnchored)
    }

    @Test
    fun `not anchored when moving fast within radius`() {
        val location = makeLocation(speed = 5.0f) // 5 m/s > 1.5 m/s threshold
        detector.recordLocation(location, 10.0)
        assertFalse(detector.isAnchored)
    }

    @Test
    fun `anchored after dwell time within radius and stationary`() {
        val location = makeLocation(speed = 0.5f)
        detector.recordLocation(location, 10.0) // Within 30m, slow

        // Wait for dwell time (2 seconds in test config)
        Thread.sleep(2100)

        assertTrue(detector.isAnchored)
    }

    @Test
    fun `reset clears dwell state`() {
        val location = makeLocation(speed = 0f)
        detector.recordLocation(location, 10.0)
        Thread.sleep(2100)
        assertTrue(detector.isAnchored)

        detector.reset()
        assertFalse(detector.isAnchored)
    }

    @Test
    fun `leaving radius resets dwell timer`() {
        val location = makeLocation(speed = 0f)
        detector.recordLocation(location, 10.0)
        Thread.sleep(1000) // Half the dwell time

        // Leave radius
        detector.recordLocation(location, 50.0)
        Thread.sleep(1200) // More than remaining dwell time

        assertFalse(detector.isAnchored) // Timer was reset
    }
}
