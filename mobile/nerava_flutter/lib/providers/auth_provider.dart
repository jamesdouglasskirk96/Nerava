import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/user.dart';
import '../services/auth_service.dart';
import '../services/api_client.dart';

/// Auth service provider
final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService(apiClient);
});

/// Current user provider (nullable)
final currentUserProvider = StateNotifierProvider<CurrentUserNotifier, User?>(
  (ref) {
    final authService = ref.watch(authServiceProvider);
    return CurrentUserNotifier(authService);
  },
);

/// Notifier for current user state
class CurrentUserNotifier extends StateNotifier<User?> {
  final AuthService _authService;

  CurrentUserNotifier(this._authService) : super(null) {
    // Try to load user on initialization if authenticated
    _loadCurrentUser();
  }

  Future<void> _loadCurrentUser() async {
    if (await _authService.isAuthenticated()) {
      final user = await _authService.getCurrentUser();
      state = user;
    }
  }

  /// Set user (called after successful login/register)
  void setUser(User user) {
    state = user;
  }

  /// Clear user (called after logout)
  void clearUser() {
    state = null;
  }

  /// Refresh user from API
  Future<void> refreshUser() async {
    final user = await _authService.getCurrentUser();
    state = user;
  }
}

/// Authentication state provider (true if logged in, false otherwise)
final isAuthenticatedProvider = Provider<bool>((ref) {
  final user = ref.watch(currentUserProvider);
  return user != null;
});

