CLAUDE PROMPT — Validate Last‑Mile iOS Launch Fixes

You are Claude Code. Validate the last‑mile changes for Nerava iOS and confirm nothing is missing for 10/10 readiness.

What was changed:
1) WebView back navigation gestures
   - File: Nerava/Nerava/Views/WebViewContainer.swift
   - Expect: webView.allowsBackForwardNavigationGestures = true added in makeUIView.

2) Background permission icon clarification
   - File: Nerava/Nerava/Views/BackgroundPermissionView.swift
   - Expect: icon changed from bell.badge.fill to location.fill.viewfinder.

3) App icon assets (manual requirement)
   - Folder: Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/
   - Expect: Contents.json already references files.
   - Required designer handoff: add AppIcon.png, AppIcon-Dark.png, AppIcon-Tinted.png (1024x1024, no alpha, sRGB).

Your output should include:
- Confirmed/Missing for each of the three items
- Any regressions or additional gaps you notice
- A short “ready for submission?” verdict
- If blocked, the exact steps required to clear the block

Keep it brief and focused.
