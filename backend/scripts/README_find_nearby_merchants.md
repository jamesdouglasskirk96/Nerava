# Find Nearby Merchants Script

This script finds merchants within walking distance of EV chargers, suitable for outreach to local businesses that could benefit from EV charging customers.

## Overview

The script:
1. Geocodes your home address to get coordinates
2. Fetches EV chargers within a configurable radius (default: 90 miles, proxy for 90-min drive)
3. For each charger, searches for nearby merchants using Google Places API
4. Filters merchants by:
   - Phone number required (for outreach)
   - Walking distance <= 5 minutes from a charger
5. Classifies merchants as "corporate" vs "non-corporate" using:
   - A configurable denylist of chain names
   - Place type heuristics
   - Name pattern matching
6. Outputs ranked results to CSV and JSON

## Prerequisites

- Python 3.9+
- Google Cloud Platform account with Places API enabled
- (Optional) NREL API key for charger data

## Installation

```bash
# From the backend directory
pip install requests
```

No additional dependencies beyond `requests` are needed.

## API Keys

### Required: Google Places API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select an existing one
3. Enable the following APIs:
   - Places API (New)
   - Geocoding API
4. Create an API key in "Credentials"
5. (Recommended) Restrict the key to only these APIs

### Optional: NREL API Key

For better EV charger data, get a free NREL API key:

1. Go to [NREL Developer Portal](https://developer.nrel.gov/signup/)
2. Sign up for a free account
3. Your API key will be emailed to you

If no NREL key is provided, the script falls back to OpenChargeMap (no key required).

## Environment Variables

```bash
# Required
export GOOGLE_PLACES_API_KEY="your_google_api_key"

# Optional (recommended)
export NREL_API_KEY="your_nrel_api_key"

# Optional overrides
export HOME_ADDRESS="11621 Timber Heights Dr, Austin, TX"
export CHARGER_RADIUS_MILES="90"
export WALK_TIME_MINUTES="5"
```

## Usage

```bash
# From the backend directory
python scripts/find_nearby_merchants.py
```

## Output Files

The script creates three files in `outputs/`:

### `merchants_top100.csv`
Top 100 non-corporate merchants, ranked by:
1. Walking time to nearest charger (lower is better)
2. Score: rating * log(1 + review_count) (higher is better)

### `merchants_top100.json`
Same data in JSON format, useful for programmatic access.

### `merchants_review_needed.csv`
Merchants that are either:
- Classified as corporate (for verification)
- Flagged as "needs_review" (borderline cases)

## CSV Schema

| Column | Description |
|--------|-------------|
| `place_id` | Google Places unique ID |
| `name` | Business name |
| `address` | Full formatted address |
| `phone` | International phone number |
| `website` | Website URL |
| `types` | Comma-separated place types |
| `rating` | Google rating (1-5) |
| `user_ratings_total` | Number of reviews |
| `price_level` | Price level if available |
| `open_now` | yes/no/unknown |
| `merchant_lat` | Merchant latitude |
| `merchant_lng` | Merchant longitude |
| `nearest_charger_id` | ID of nearest EV charger |
| `nearest_charger_name` | Name of nearest charger |
| `charger_lat` | Charger latitude |
| `charger_lng` | Charger longitude |
| `distance_to_charger_m` | Distance in meters |
| `walk_time_min` | Walking time in minutes |
| `corporate_likely` | True/False classification |
| `corporate_reason` | Why classified as corporate |
| `needs_review` | True if borderline case |
| `source` | Data source (google_places) |
| `discovered_via_chargers` | Charger IDs where found |

## Customization

### Editing the Chain Denylist

Edit `data/chain_denylist.txt` to add or remove corporate chains:

```
# One pattern per line
# Lines starting with # are comments

McDonald's
Starbucks
Walmart

# Regex patterns start with "regex:"
regex:.*\s+#\d+$
```

### Modifying Search Types

Edit the `merchant_types` list in the script's `Config` class:

```python
merchant_types: list = field(default_factory=lambda: [
    "restaurant",
    "cafe",
    "bar",
    # Add more types...
])
```

See [Google Place Types](https://developers.google.com/maps/documentation/places/web-service/place-types) for available types.

## Caching

The script caches API responses in `.cache/` to avoid re-billing while iterating. To force fresh data, delete the cache directory:

```bash
rm -rf .cache/
```

## Cost Estimates

### Google Places API
- Nearby Search: $0.032 per request (up to 20 results)
- Geocoding: $0.005 per request

For ~500 chargers with 14 place types each:
- ~7,000 Nearby Search requests = ~$224

To reduce costs:
- Reduce `max_chargers` in Config
- Reduce `merchant_types` list
- Use cached results

### NREL API
- Free (no cost)

### OpenChargeMap API
- Free (no cost)

## Troubleshooting

### "GOOGLE_PLACES_API_KEY environment variable is required"
Set the environment variable:
```bash
export GOOGLE_PLACES_API_KEY="your_key"
```

### "Rate limited, waiting 60 seconds..."
The script handles rate limiting automatically. This is normal.

### No chargers found
- Check your NREL API key is valid
- Increase `charger_search_radius_miles`
- Verify the home address geocodes correctly

### Very few merchants found
- Increase `merchant_search_radius_m` (default: 500m)
- Add more `merchant_types`
- Check the area actually has businesses

## HubSpot Import

The CSV is formatted for easy HubSpot import:

1. Go to HubSpot > Contacts > Import
2. Select "Import from file"
3. Map fields:
   - `name` -> Company name
   - `phone` -> Phone number
   - `website` -> Website
   - `address` -> Address
   - `rating` -> Custom property
   - `walk_time_min` -> Custom property

## VAPI Integration

To use with VAPI for automated calling:

```python
import csv
import json

# Load merchants
with open('outputs/merchants_top100.csv') as f:
    merchants = list(csv.DictReader(f))

# Format for VAPI
calls = [{
    'phone_number': m['phone'],
    'variables': {
        'business_name': m['name'],
        'charger_distance': f"{m['walk_time_min']} minutes walk",
    }
} for m in merchants]

# Save for VAPI import
with open('outputs/vapi_calls.json', 'w') as f:
    json.dump(calls, f, indent=2)
```
