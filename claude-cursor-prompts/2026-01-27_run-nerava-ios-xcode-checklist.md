CURSOR PROMPT — Run Nerava iOS in Xcode (Validation Checklist)

Goal: build/run the iOS app in Xcode and validate launch + critical behaviors. No code changes.

1) Open the Project
- Command:
  open /Users/jameskirk/Desktop/Nerava/Nerava/Nerava.xcodeproj
- Use .xcodeproj (no workspace).

2) Select Scheme & Destination
- Scheme: Nerava (Product → Scheme → Nerava)
- Destination: physical iPhone preferred (WKWebView + haptics + swipe-back fidelity)
  - If no device: iPhone 15 Pro simulator (iOS 17+)
- If prompted: set Signing & Capabilities → Team

3) Build & Run
- Cmd+B (clean build)
- Cmd+R (run)

4) Validation Checklist
#1 Launch screen
- How: cold start (swipe-kill then relaunch)
- Expect: logo on correct background, smooth transition, no flash

#2 App icon
- How: check home screen + Xcode Assets → AppIcon
- Expect: icon visible, no yellow warnings

#3 Back navigation gesture
- How: Account → Privacy Policy → swipe back
- Expect: returns to Account

#4 Background permission icon
- How: fresh install → trigger background rationale (or preview view)
- Expect: location.fill.viewfinder (not bell.badge.fill)

#5 No notification prompt at launch
- How: delete app → reinstall → launch
- Expect: no system notification prompt

#6 Pull-to-refresh
- How: pull down on web content
- Expect: refresh control appears, reloads, dismisses

#7 Offline → error → retry
- How: Airplane Mode → launch → see overlay → disable → Retry
- Expect: overlay + retry successfully reloads

#8 Haptics (device only)
- How: activate exclusive
- Expect: success haptic

5) If AppIcon Shows a Warning in Xcode
- Check alpha/dimensions with:
  sips -g pixelWidth -g pixelHeight -g hasAlpha /Users/jameskirk/Desktop/Nerava/Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/AppIcon.png
- All 3 PNGs must be 1024x1024 and hasAlpha: no

6) Quick Terminal Sanity Checks (optional)
- No CloudKit entitlements:
  grep -i icloud /Users/jameskirk/Desktop/Nerava/Nerava/Nerava/Nerava.entitlements
- No launch permission request:
  grep "requestPermission()" /Users/jameskirk/Desktop/Nerava/Nerava/Nerava/NeravaApp.swift
- Icons present:
  ls /Users/jameskirk/Desktop/Nerava/Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/*.png

No code changes needed. This is build-and-verify only.
