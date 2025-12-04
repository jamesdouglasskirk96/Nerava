# Nerava Flutter Mobile App (v1)

A lightweight Flutter shell that wraps the Nerava web app with native authentication, QR scanning, and settings.

## Architecture

- **Native Auth**: Email/password login using `/v1/auth/*` endpoints
- **WebView Shell**: Loads `https://nerava.network` after authentication
- **QR Scanner**: Native camera-based QR code scanning
- **Native Settings**: Account management and app info

## Setup

### Prerequisites
- Flutter SDK (>=3.0.0)
- Xcode (for iOS development)
- Android Studio / Android SDK (for Android development)

### Installation

```bash
cd mobile/nerava_flutter
flutter pub get
```

### Run

```bash
# iOS
flutter run -d ios

# Android
flutter run -d android
```

## Project Structure

```
lib/
  ├── config/
  │   └── app_config.dart          # App configuration (URLs, etc.)
  ├── models/
  │   └── user.dart                # User model
  ├── services/
  │   ├── auth_service.dart        # Authentication service
  │   └── api_client.dart          # HTTP client with interceptors
  ├── providers/
  │   └── auth_provider.dart       # Riverpod auth state
  ├── screens/
  │   ├── splash_screen.dart
  │   ├── login_screen.dart
  │   ├── main_shell.dart          # Bottom nav shell
  │   ├── webview_screen.dart
  │   ├── qr_scanner_screen.dart
  │   └── settings_screen.dart
  └── main.dart                    # App entry point
```

## Configuration

Edit `lib/config/app_config.dart` to change:
- API base URL
- Web app URL
- Other environment-specific settings

## Notes

See `MOBILE_V1_NOTES.md` for detailed implementation notes and findings.

