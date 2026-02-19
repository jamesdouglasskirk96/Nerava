CLAUDE PROMPT — Run Nerava iOS in Xcode (Post‑Fix Validation)

You are Claude Code. Provide a Cursor‑ready, step‑by‑step checklist to run the Nerava iOS app in Xcode for validation after the latest fixes. Assume the code is already updated; this is about launching and verifying behavior, not making code changes.

Context:
- The app is a SwiftUI shell with a WKWebView (Nerava iOS).
- Latest fixes include WebView back navigation gestures + clarified background permission icon.
- Remaining blocker: AppIcon PNGs may still be missing.

Your output MUST include:
1) Steps to open the Xcode project/workspace and select the correct scheme.
2) How to choose a simulator vs physical device, and recommended choice for WKWebView testing.
3) Build/run steps.
4) A short validation checklist focused on:
   - Back navigation gesture works after tapping Privacy Policy (target=_blank).
   - Background permission screen icon is location‑specific.
   - Launch screen looks correct.
   - Optional: if AppIcon PNGs are missing, how to confirm the warning and where to add them.

Constraints:
- Keep it concise and actionable.
- No code edits, no refactors.
- If you need to mention file paths, use:
  - Nerava/Nerava/Views/WebViewContainer.swift
  - Nerava/Nerava/Views/BackgroundPermissionView.swift
  - Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/
