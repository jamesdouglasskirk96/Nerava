# Asadas Grill Photos from Google Places

This directory contains photos downloaded from Google Places API for Asadas Grill.

## To Download Photos

1. Make sure you have a Google Places API key set:
   ```bash
   export GOOGLE_PLACES_API_KEY='your-api-key-here'
   ```

2. Run the download script:
   ```bash
   cd backend
   python3 scripts/download_asadas_photos.py
   ```

3. Photos will be saved to this directory as:
   - `asadas_grill_01.jpg`
   - `asadas_grill_02.jpg`
   - `asadas_grill_03.jpg`
   - etc.

4. Place details will be saved to `place_details.json`

## Location

- **Name**: Asadas Grill
- **Address**: 501 W Canyon Ridge Dr, Austin, TX 78753
- **Coordinates**: 30.3839, -97.6900

## Notes

- Photos are downloaded at 1200px width (configurable via `GOOGLE_PLACES_PHOTO_MAXWIDTH`)
- The script will download all available photos from Google Places
- Photos are cached by Google Places API, so re-running is safe



