CURSOR PROMPT — Re-run Nerava iOS Build in Xcode

Goal: rebuild and run the Nerava iOS app after the two build fixes.

1) Open project (if not already open)
open /Users/jameskirk/Desktop/Nerava/Nerava/Nerava.xcodeproj

2) Build
- Cmd+B
- Confirm no errors

3) Run
- Cmd+R on selected device

4) Quick smoke checks
- Launch screen transition
- App icon visible on home screen
- Privacy Policy → swipe back
- Notification prompt does NOT appear at launch

No code changes. Build and verify only.
