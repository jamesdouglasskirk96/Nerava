# Tesla Fleet API — Request & Response Examples

Reference for the Tesla Fleet API endpoints used by Nerava's charging verification system.

**Base URL (North America):** `https://fleet-api.prd.na.vn.cloud.tesla.com`

All requests require `Authorization: Bearer {access_token}` header.

---

## GET /api/1/vehicles — List Vehicles

Returns all vehicles on the account.

**Request:**
```
GET /api/1/vehicles
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Response (200 OK):**
```json
{
  "response": [
    {
      "id": 3744582737186151,
      "vehicle_id": 1234567890,
      "vin": "5YJ3E1EA5HF000123",
      "display_name": "My Model 3",
      "color": null,
      "access_type": "OWNER",
      "tokens": ["abcdef1234567890", "1234567890abcdef"],
      "state": "online",
      "in_service": false,
      "id_s": "3744582737186151",
      "calendar_enabled": true,
      "api_version": 71
    },
    {
      "id": 9988776655443322,
      "vehicle_id": 9876543210,
      "vin": "5YJSA1E21HF111456",
      "display_name": "Model Y",
      "color": null,
      "access_type": "OWNER",
      "tokens": ["fedcba0987654321", "0987654321fedcba"],
      "state": "asleep",
      "in_service": false,
      "id_s": "9988776655443322",
      "calendar_enabled": true,
      "api_version": 71
    }
  ],
  "count": 2
}
```

**Note:** The `id` field is used for all Fleet API vehicle endpoints. The `vehicle_id` field is for the streaming API only.

### Vehicle `state` values

| Value | Meaning |
|-------|---------|
| `"online"` | Awake, can receive API calls |
| `"asleep"` | Deep sleep, returns 408 on data calls. Must call `wake_up` |
| `"offline"` | No internet connectivity (underground, no cell signal). Cannot be woken |
| `"waking"` | Transitional — coming online after `wake_up` call |

---

## POST /api/1/vehicles/{id}/wake_up — Wake Vehicle

Wakes a sleeping vehicle. Returns immediately, but the vehicle may take 15-30 seconds to report telemetry.

**Request:**
```
POST /api/1/vehicles/3744582737186151/wake_up
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Response (200 OK) — vehicle woke up:**
```json
{
  "response": {
    "id": 3744582737186151,
    "vehicle_id": 1234567890,
    "vin": "5YJ3E1EA5HF000123",
    "display_name": "My Model 3",
    "color": null,
    "access_type": "OWNER",
    "tokens": ["abcdef1234567890", "1234567890abcdef"],
    "state": "online",
    "in_service": false,
    "id_s": "3744582737186151",
    "calendar_enabled": true,
    "api_version": 71
  }
}
```

**Response (200 OK) — still waking:**
Same structure but `"state": "asleep"` or `"state": "waking"`. Poll until `"state": "online"`.

---

## GET /api/1/vehicles/{id}/vehicle_data — Get Vehicle Data

Live call to the vehicle. The `endpoints` query parameter controls which data subsets are returned (semicolon-separated).

**Request:**
```
GET /api/1/vehicles/3744582737186151/vehicle_data?endpoints=charge_state;drive_state;location_data
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Valid `endpoints` values:** `charge_state`, `climate_state`, `closures_state`, `drive_state`, `gui_settings`, `location_data`, `vehicle_config`, `vehicle_state`

**Note:** On firmware 2023.38+, `location_data` must be explicitly included to get GPS coordinates. This shows a location-sharing icon on the vehicle screen.

---

### Scenario A: Supercharger (DC Fast Charging)

**Response (200 OK):**
```json
{
  "response": {
    "id": 3744582737186151,
    "vehicle_id": 1234567890,
    "vin": "5YJ3E1EA5HF000123",
    "display_name": "My Model 3",
    "state": "online",
    "charge_state": {
      "battery_heater_on": true,
      "battery_level": 42,
      "battery_range": 106.23,
      "charge_amps": 227,
      "charge_current_request": 227,
      "charge_current_request_max": 227,
      "charge_enable_request": true,
      "charge_energy_added": 18.73,
      "charge_limit_soc": 80,
      "charge_limit_soc_max": 100,
      "charge_limit_soc_min": 50,
      "charge_limit_soc_std": 90,
      "charge_miles_added_ideal": 93.5,
      "charge_miles_added_rated": 75.0,
      "charge_port_cold_weather_mode": false,
      "charge_port_color": "FlashingGreen",
      "charge_port_door_open": true,
      "charge_port_latch": "Engaged",
      "charge_rate": 492.0,
      "charge_to_max_range": false,
      "charger_actual_current": 227,
      "charger_phases": null,
      "charger_pilot_current": 227,
      "charger_power": 150,
      "charger_voltage": 400,
      "charging_state": "Charging",
      "conn_charge_cable": "IEC",
      "est_battery_range": 93.41,
      "fast_charger_brand": "Tesla",
      "fast_charger_present": true,
      "fast_charger_type": "MCSingleWireCAN",
      "ideal_battery_range": 132.79,
      "managed_charging_active": false,
      "managed_charging_start_time": null,
      "managed_charging_user_canceled": false,
      "max_range_charge_counter": 0,
      "minutes_to_full_charge": 25,
      "not_enough_power_to_heat": false,
      "off_peak_charging_enabled": false,
      "off_peak_charging_times": "all_week",
      "off_peak_hours_end_time": 360,
      "preconditioning_enabled": false,
      "preconditioning_times": "all_week",
      "scheduled_charging_mode": "Off",
      "scheduled_charging_pending": false,
      "scheduled_charging_start_time": null,
      "scheduled_charging_start_time_app": 0,
      "scheduled_departure_time": null,
      "scheduled_departure_time_minutes": null,
      "supercharger_session_trip_planner": true,
      "time_to_full_charge": 0.42,
      "timestamp": 1708372800000,
      "trip_charging": true,
      "usable_battery_level": 42,
      "user_charge_enable_request": null
    },
    "drive_state": {
      "active_route_destination": "Tesla Supercharger - Canyon Ridge",
      "active_route_energy_at_arrival": 42,
      "active_route_latitude": 33.4255,
      "active_route_longitude": -111.9400,
      "active_route_miles_to_arrival": 0.0,
      "active_route_minutes_to_arrival": 0.0,
      "active_route_traffic_minutes_delay": 0.0,
      "gps_as_of": 1708372798,
      "heading": 175,
      "latitude": 33.425500,
      "longitude": -111.940000,
      "native_latitude": 33.425500,
      "native_location_supported": 1,
      "native_longitude": -111.940000,
      "native_type": "wgs",
      "power": -150,
      "shift_state": "P",
      "speed": null,
      "timestamp": 1708372800000
    }
  }
}
```

**Key indicators:** `charging_state: "Charging"`, `fast_charger_present: true`, `fast_charger_brand: "Tesla"`, `charger_power: 150` (kW), `charger_phases: null` (DC has no AC phases), `drive_state.power: -150` (negative = energy into battery).

---

### Scenario B: Level 2 / AC Charging (Home or Destination Charger)

**Response (200 OK):**
```json
{
  "response": {
    "id": 3744582737186151,
    "vehicle_id": 1234567890,
    "vin": "5YJ3E1EA5HF000123",
    "display_name": "My Model 3",
    "state": "online",
    "charge_state": {
      "battery_heater_on": false,
      "battery_level": 59,
      "battery_range": 149.92,
      "charge_amps": 40,
      "charge_current_request": 40,
      "charge_current_request_max": 48,
      "charge_enable_request": true,
      "charge_energy_added": 2.42,
      "charge_limit_soc": 90,
      "charge_limit_soc_max": 100,
      "charge_limit_soc_min": 50,
      "charge_limit_soc_std": 90,
      "charge_miles_added_ideal": 10.0,
      "charge_miles_added_rated": 8.0,
      "charge_port_cold_weather_mode": null,
      "charge_port_color": "FlashingGreen",
      "charge_port_door_open": true,
      "charge_port_latch": "Engaged",
      "charge_rate": 28.0,
      "charge_to_max_range": false,
      "charger_actual_current": 40,
      "charger_phases": 1,
      "charger_pilot_current": 40,
      "charger_power": 9,
      "charger_voltage": 243,
      "charging_state": "Charging",
      "conn_charge_cable": "SAE",
      "est_battery_range": 132.98,
      "fast_charger_brand": "<invalid>",
      "fast_charger_present": false,
      "fast_charger_type": "<invalid>",
      "ideal_battery_range": 187.40,
      "managed_charging_active": false,
      "managed_charging_start_time": null,
      "managed_charging_user_canceled": false,
      "max_range_charge_counter": 0,
      "minutes_to_full_charge": 165,
      "not_enough_power_to_heat": false,
      "off_peak_charging_enabled": true,
      "off_peak_charging_times": "all_week",
      "off_peak_hours_end_time": 360,
      "preconditioning_enabled": false,
      "preconditioning_times": "all_week",
      "scheduled_charging_mode": "Off",
      "scheduled_charging_pending": false,
      "scheduled_charging_start_time": null,
      "scheduled_charging_start_time_app": 665,
      "scheduled_departure_time": 1652090400,
      "scheduled_departure_time_minutes": 720,
      "supercharger_session_trip_planner": false,
      "time_to_full_charge": 2.75,
      "timestamp": 1708392000000,
      "trip_charging": false,
      "usable_battery_level": 59,
      "user_charge_enable_request": null
    },
    "drive_state": {
      "gps_as_of": 1708391990,
      "heading": 340,
      "latitude": 33.459728,
      "longitude": -111.923447,
      "native_latitude": 33.459729,
      "native_location_supported": 1,
      "native_longitude": -111.923444,
      "native_type": "wgs",
      "power": -9,
      "shift_state": null,
      "speed": null,
      "timestamp": 1708392000000
    }
  }
}
```

**Key indicators:** `charging_state: "Charging"`, `fast_charger_present: false`, `fast_charger_brand: "<invalid>"`, `charger_power: 9` (kW, typical 240V/40A), `charger_phases: 1`, `charger_voltage: 243` (AC), `conn_charge_cable: "SAE"` (J1772/NACS).

---

### Scenario C: Plugged In, Charging Complete

**Response (200 OK):**
```json
{
  "response": {
    "id": 3744582737186151,
    "vehicle_id": 1234567890,
    "vin": "5YJ3E1EA5HF000123",
    "display_name": "My Model 3",
    "state": "online",
    "charge_state": {
      "battery_heater_on": false,
      "battery_level": 90,
      "battery_range": 224.47,
      "charge_amps": 12,
      "charge_current_request": 40,
      "charge_current_request_max": 40,
      "charge_enable_request": true,
      "charge_energy_added": 29.41,
      "charge_limit_soc": 90,
      "charge_limit_soc_max": 100,
      "charge_limit_soc_min": 50,
      "charge_limit_soc_std": 90,
      "charge_miles_added_ideal": 118.5,
      "charge_miles_added_rated": 95.0,
      "charge_port_cold_weather_mode": null,
      "charge_port_color": "Green",
      "charge_port_door_open": true,
      "charge_port_latch": "Engaged",
      "charge_rate": 0.0,
      "charge_to_max_range": false,
      "charger_actual_current": 0,
      "charger_phases": null,
      "charger_pilot_current": 40,
      "charger_power": 0,
      "charger_voltage": 0,
      "charging_state": "Complete",
      "conn_charge_cable": "SAE",
      "est_battery_range": 171.24,
      "fast_charger_brand": "<invalid>",
      "fast_charger_present": false,
      "fast_charger_type": "<invalid>",
      "ideal_battery_range": 280.59,
      "managed_charging_active": false,
      "managed_charging_start_time": null,
      "managed_charging_user_canceled": false,
      "max_range_charge_counter": 0,
      "minutes_to_full_charge": 0,
      "not_enough_power_to_heat": false,
      "off_peak_charging_enabled": false,
      "off_peak_charging_times": "all_week",
      "off_peak_hours_end_time": 360,
      "preconditioning_enabled": false,
      "preconditioning_times": "all_week",
      "scheduled_charging_mode": "Off",
      "scheduled_charging_pending": false,
      "scheduled_charging_start_time": null,
      "scheduled_charging_start_time_app": 665,
      "scheduled_departure_time": 1652090400,
      "scheduled_departure_time_minutes": 720,
      "supercharger_session_trip_planner": false,
      "time_to_full_charge": 0.0,
      "timestamp": 1708400000000,
      "trip_charging": false,
      "usable_battery_level": 90,
      "user_charge_enable_request": null
    },
    "drive_state": {
      "gps_as_of": 1708399990,
      "heading": 340,
      "latitude": 33.459728,
      "longitude": -111.923447,
      "native_latitude": 33.459729,
      "native_location_supported": 1,
      "native_longitude": -111.923444,
      "native_type": "wgs",
      "power": 0,
      "shift_state": null,
      "speed": null,
      "timestamp": 1708400000000
    }
  }
}
```

**Key indicators:** `charging_state: "Complete"`, `battery_level` matches `charge_limit_soc`, `charger_power: 0`, `charge_rate: 0.0`, `charge_port_latch: "Engaged"` (still plugged in), `charge_port_color: "Green"`.

**"Stopped" variant:** Same structure but `charging_state: "Stopped"` — charging was manually stopped or paused by a schedule. `battery_level` will be below `charge_limit_soc`.

---

### Scenario D: Not Plugged In (Disconnected)

**Response (200 OK):**
```json
{
  "response": {
    "id": 3744582737186151,
    "vehicle_id": 1234567890,
    "vin": "5YJ3E1EA5HF000123",
    "display_name": "My Model 3",
    "state": "online",
    "charge_state": {
      "battery_heater_on": false,
      "battery_level": 74,
      "battery_range": 186.57,
      "charge_amps": 48,
      "charge_current_request": 48,
      "charge_current_request_max": 48,
      "charge_enable_request": true,
      "charge_energy_added": 0.0,
      "charge_limit_soc": 90,
      "charge_limit_soc_max": 100,
      "charge_limit_soc_min": 50,
      "charge_limit_soc_std": 90,
      "charge_miles_added_ideal": 0.0,
      "charge_miles_added_rated": 0.0,
      "charge_port_cold_weather_mode": null,
      "charge_port_color": "<invalid>",
      "charge_port_door_open": false,
      "charge_port_latch": "Disengaged",
      "charge_rate": 0.0,
      "charge_to_max_range": false,
      "charger_actual_current": 0,
      "charger_phases": null,
      "charger_pilot_current": 0,
      "charger_power": 0,
      "charger_voltage": 0,
      "charging_state": "Disconnected",
      "conn_charge_cable": "<invalid>",
      "est_battery_range": 146.18,
      "fast_charger_brand": "<invalid>",
      "fast_charger_present": false,
      "fast_charger_type": "<invalid>",
      "ideal_battery_range": 238.93,
      "managed_charging_active": false,
      "managed_charging_start_time": null,
      "managed_charging_user_canceled": false,
      "max_range_charge_counter": 0,
      "minutes_to_full_charge": 0,
      "not_enough_power_to_heat": false,
      "off_peak_charging_enabled": false,
      "off_peak_charging_times": "all_week",
      "off_peak_hours_end_time": 360,
      "preconditioning_enabled": false,
      "preconditioning_times": "all_week",
      "scheduled_charging_mode": "Off",
      "scheduled_charging_pending": false,
      "scheduled_charging_start_time": null,
      "scheduled_charging_start_time_app": 0,
      "scheduled_departure_time": null,
      "scheduled_departure_time_minutes": null,
      "supercharger_session_trip_planner": false,
      "time_to_full_charge": 0.0,
      "timestamp": 1708410000000,
      "trip_charging": false,
      "usable_battery_level": 74,
      "user_charge_enable_request": null
    },
    "drive_state": {
      "gps_as_of": 1708409990,
      "heading": 220,
      "latitude": 33.512345,
      "longitude": -111.876543,
      "native_latitude": 33.512345,
      "native_location_supported": 1,
      "native_longitude": -111.876543,
      "native_type": "wgs",
      "power": 0,
      "shift_state": null,
      "speed": null,
      "timestamp": 1708410000000
    }
  }
}
```

**Key indicators:** `charging_state: "Disconnected"`, `charge_port_door_open: false`, `charge_port_latch: "Disengaged"`, `conn_charge_cable: "<invalid>"`, all charger fields zeroed.

---

### Scenario E: Vehicle Asleep / Unreachable (408)

When the vehicle is asleep, the Fleet API cannot reach it to get live data.

**Response (408 Request Timeout):**
```json
{
  "response": null,
  "error": "vehicle unavailable: {:error=>\"vehicle unavailable:\"}",
  "error_description": ""
}
```

This is what happened in today's production bug — the vehicle woke up (wake_up returned 200) but hadn't finished its internal telemetry refresh. The vehicle_data call returned 408 because the vehicle wasn't ready to report data yet. A retry after 3-5 seconds would have succeeded.

---

## HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| **200** | Success | Parse response |
| **401** | Unauthorized | Token expired or revoked — refresh or re-auth |
| **403** | Forbidden | Insufficient OAuth scopes, or command needs signed protocol |
| **404** | Not Found | Vehicle ID doesn't exist |
| **408** | Device Not Available | Vehicle asleep/offline — wake it first, then retry |
| **412** | Precondition Failed | Fleet API partner not registered, or wrong region |
| **421** | Incorrect Region | Vehicle registered to different regional server |
| **429** | Rate Limited | Too many requests. Check `RateLimit-Reset` header |
| **500** | Internal Server Error | Tesla server issue — retry with backoff |
| **503** | Service Unavailable | Tesla internal timeout — retry with backoff |
| **540** | Device Unexpected Response | Vehicle error — may need reboot |

---

## `charging_state` Values

| Value | Meaning |
|-------|---------|
| `"Charging"` | Actively receiving energy (AC or DC) |
| `"Complete"` | Reached `charge_limit_soc`, still plugged in |
| `"Stopped"` | Charging interrupted (user stopped, schedule paused, or error) |
| `"Disconnected"` | No cable connected |
| `"NoPower"` | Cable connected but no power from source (charger off, breaker tripped) |
| `"Starting"` | Session initializing (brief transitional state) |

**Note:** Tesla uses PascalCase for these values. Always `"Charging"`, never `"charging"` or `"CHARGING"`.

---

## `charge_state` Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `charging_state` | string | See table above |
| `battery_level` | int | State of charge 0-100% |
| `usable_battery_level` | int | Usable SoC (differs in cold weather) |
| `battery_range` | float | EPA rated range in miles |
| `charge_rate` | float | Miles of range added per hour |
| `charger_power` | int | Charging power in kW |
| `charger_voltage` | int | Charger voltage |
| `charger_actual_current` | int | Actual current in amps |
| `charger_phases` | int/null | AC phases (1/2/3), null for DC |
| `charge_limit_soc` | int | Target charge % |
| `charge_energy_added` | float | kWh added this session |
| `minutes_to_full_charge` | int | Minutes to reach limit |
| `fast_charger_present` | bool | DC fast charger connected |
| `fast_charger_brand` | string | `"Tesla"`, or `"<invalid>"` |
| `conn_charge_cable` | string | `"SAE"` (J1772/NACS), `"IEC"` (Type 2), `"<invalid>"` (none) |
| `charge_port_door_open` | bool | Charge port open |
| `charge_port_latch` | string | `"Engaged"`, `"Disengaged"`, `"Blocking"` |
| `charge_port_color` | string | `"FlashingGreen"` (charging), `"Green"` (complete), `"Blue"` (ready) |
| `trip_charging` | bool | En-route Supercharger stop |
| `timestamp` | long | Unix ms |

## `drive_state` Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `latitude` | float | Vehicle latitude |
| `longitude` | float | Vehicle longitude |
| `heading` | int | Compass heading 0-360 |
| `speed` | int/null | Speed in mph, null when parked |
| `power` | int | kW (positive = driving, negative = charging) |
| `shift_state` | string/null | `"P"`, `"R"`, `"N"`, `"D"`, or null |
| `gps_as_of` | long | Unix seconds of last GPS fix |
| `timestamp` | long | Unix ms |
