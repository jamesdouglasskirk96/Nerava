import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../config/app_config.dart';

/// HTTP client with authentication interceptors
class ApiClient {
  late final Dio _dio;
  static const _storage = FlutterSecureStorage();
  static const _tokenKey = 'access_token';

  ApiClient() {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConfig.apiUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    // Add auth interceptor
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          // Get token from secure storage
          final token = await _storage.read(key: _tokenKey);
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          return handler.next(options);
        },
        onError: (error, handler) {
          // Handle 401 unauthorized - clear token and redirect to login
          if (error.response?.statusCode == 401) {
            _storage.delete(key: _tokenKey);
          }
          return handler.next(error);
        },
      ),
    );
  }

  /// Get the underlying Dio instance
  Dio get dio => _dio;

  /// Store access token
  Future<void> setToken(String token) async {
    await _storage.write(key: _tokenKey, value: token);
  }

  /// Get stored access token
  Future<String?> getToken() async {
    return await _storage.read(key: _tokenKey);
  }

  /// Clear stored token
  Future<void> clearToken() async {
    await _storage.delete(key: _tokenKey);
  }

  /// Check if user is authenticated
  Future<bool> isAuthenticated() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }
}

// Singleton instance
final apiClient = ApiClient();

