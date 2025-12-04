/// App configuration with environment-specific URLs and settings
class AppConfig {
  // Web app base URL
  static const String baseWebUrl = 'https://nerava.network';

  // API base URL (production)
  static const String apiBaseUrl = 'https://web-production-526f6.up.railway.app';

  // API base URL (development - can override in dev builds)
  static const String apiBaseUrlDev = 'http://127.0.0.1:8001';

  // Get API base URL based on environment
  static String get apiUrl {
    // In production, use production URL
    // In development, you can switch this or use environment variables
    const String env = String.fromEnvironment('ENV', defaultValue: 'production');
    return env == 'dev' ? apiBaseUrlDev : apiBaseUrl;
  }

  // API endpoints
  static const String authLoginEndpoint = '/v1/auth/login';
  static const String authRegisterEndpoint = '/v1/auth/register';
  static const String authMeEndpoint = '/v1/auth/me';
  static const String authLogoutEndpoint = '/v1/auth/logout';

  // Legal URLs
  static const String privacyPolicyUrl = 'https://nerava.network/privacy';
  static const String termsOfServiceUrl = 'https://nerava.network/terms';

  // Support
  static const String supportEmail = 'support@nerava.network';
  static const String supportUrl = 'https://nerava.network/support';

  // WebView domain whitelist (URLs that stay in WebView)
  static const List<String> webViewDomains = [
    'nerava.network',
    'www.nerava.network',
  ];

  // Check if URL should be opened in WebView or external browser
  static bool shouldOpenInWebView(String url) {
    try {
      final uri = Uri.parse(url);
      final host = uri.host.toLowerCase();

      for (final domain in webViewDomains) {
        if (host == domain || host.endsWith('.$domain')) {
          return true;
        }
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  // App info
  static const String appName = 'Nerava';
  static const String appTagline = 'EV Charging & Rewards';
}

