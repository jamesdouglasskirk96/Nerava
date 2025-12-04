import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:webview_flutter/webview_flutter.dart';

/// Provider for WebView controller to enable navigation from other screens (e.g., QR scanner)
final webViewControllerProvider =
    StateNotifierProvider<WebViewControllerNotifier, WebViewController?>(
  (ref) => WebViewControllerNotifier(),
);

class WebViewControllerNotifier extends StateNotifier<WebViewController?> {
  WebViewControllerNotifier() : super(null);

  void setController(WebViewController controller) {
    state = controller;
  }

  Future<void> navigateToUrl(String url) async {
    if (state != null) {
      await state!.loadRequest(Uri.parse(url));
    }
  }

  void clearController() {
    state = null;
  }
}

