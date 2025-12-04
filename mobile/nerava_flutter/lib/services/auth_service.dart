import 'package:dio/dio.dart';
import '../config/app_config.dart';
import '../models/user.dart';
import 'api_client.dart';

/// Authentication service for login, register, logout
class AuthService {
  final ApiClient _apiClient;

  AuthService(this._apiClient);

  /// Login with email and password
  Future<LoginResult> login(String email, String password) async {
    try {
      final response = await _apiClient.dio.post(
        AppConfig.authLoginEndpoint,
        data: {
          'email': email,
          'password': password,
        },
      );

      final accessToken = response.data['access_token'] as String;
      await _apiClient.setToken(accessToken);

      // Fetch user info
      final user = await getCurrentUser();

      return LoginResult.success(user: user);
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        return LoginResult.failure(
          error: 'Invalid email or password',
        );
      }
      return LoginResult.failure(
        error: e.response?.data?['detail'] as String? ??
            'Login failed. Please try again.',
      );
    } catch (e) {
      return LoginResult.failure(
        error: 'An unexpected error occurred. Please try again.',
      );
    }
  }

  /// Register a new user
  Future<RegisterResult> register({
    required String email,
    required String password,
    String? displayName,
    String role = 'driver',
  }) async {
    try {
      final response = await _apiClient.dio.post(
        AppConfig.authRegisterEndpoint,
        data: {
          'email': email,
          'password': password,
          if (displayName != null) 'display_name': displayName,
          'role': role,
        },
      );

      final accessToken = response.data['access_token'] as String;
      await _apiClient.setToken(accessToken);

      // Fetch user info
      final user = await getCurrentUser();

      return RegisterResult.success(user: user);
    } on DioException catch (e) {
      if (e.response?.statusCode == 400) {
        return RegisterResult.failure(
          error: e.response?.data?['detail'] as String? ??
              'Registration failed. Email may already be in use.',
        );
      }
      return RegisterResult.failure(
        error: e.response?.data?['detail'] as String? ??
            'Registration failed. Please try again.',
      );
    } catch (e) {
      return RegisterResult.failure(
        error: 'An unexpected error occurred. Please try again.',
      );
    }
  }

  /// Get current user info
  Future<User?> getCurrentUser() async {
    try {
      final response = await _apiClient.dio.get(AppConfig.authMeEndpoint);
      return User.fromJson(response.data);
    } catch (e) {
      return null;
    }
  }

  /// Logout current user
  Future<void> logout() async {
    try {
      await _apiClient.dio.post(AppConfig.authLogoutEndpoint);
    } catch (e) {
      // Ignore errors on logout
    } finally {
      await _apiClient.clearToken();
    }
  }

  /// Check if user is authenticated
  Future<bool> isAuthenticated() async {
    return await _apiClient.isAuthenticated();
  }
}

/// Login result
class LoginResult {
  final bool success;
  final User? user;
  final String? error;

  LoginResult.success({required this.user})
      : success = true,
        error = null;

  LoginResult.failure({required this.error})
      : success = false,
        user = null;
}

/// Register result
class RegisterResult {
  final bool success;
  final User? user;
  final String? error;

  RegisterResult.success({required this.user})
      : success = true,
        error = null;

  RegisterResult.failure({required this.error})
      : success = false,
        user = null;
}

