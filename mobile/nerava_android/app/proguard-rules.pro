# Keep JavaScript interface methods
-keepclassmembers class network.nerava.app.bridge.NativeBridge$JsBridge {
    @android.webkit.JavascriptInterface <methods>;
}

# Keep OkHttp
-dontwarn okhttp3.**
-keep class okhttp3.** { *; }

# Keep Firebase
-keep class com.google.firebase.** { *; }
