# Keep JavaScript interface methods
-keepclassmembers class network.nerava.app.bridge.NativeBridge$JsBridge {
    @android.webkit.JavascriptInterface <methods>;
}

# Keep all bridge classes (referenced by name from JavaScript)
-keep class network.nerava.app.bridge.** { *; }

# Keep all classes with @JavascriptInterface methods
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# Keep OkHttp
-dontwarn okhttp3.**
-keep class okhttp3.** { *; }

# Keep Firebase
-keep class com.google.firebase.** { *; }
-dontwarn com.google.firebase.**
