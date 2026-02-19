CLAUDE PROMPT — Fix LocationService Build Errors (iOS)

You are Claude Code. Fix the Xcode build errors shown in LocationService. The errors include missing import of module `os` (Logger) and “explicit self” capture warnings in closures.

Observed errors (from Xcode):
- Instance method 'info' / 'appendLiteral' / 'appendInterpolation' not available due to missing import of module 'os'
- Initializer 'init(stringInterpolation:)' not available due to missing import of module 'os'
- Reference to property 'authorizationStatus' requires explicit use of 'self' in closure
- Reference to property 'isHighAccuracyMode' requires explicit use of 'self' in closure

Your tasks:
1) Open the LocationService file in the iOS app and add the correct import(s) so Logger methods compile.
2) Add explicit `self.` inside closures where required.
3) Ensure no other files are affected; keep changes minimal.

Output:
- List the exact file path(s) edited.
- Provide a minimal diff or snippet for each fix.
- Note any remaining errors if found.

Constraints:
- No refactors.
- No new dependencies.
- Keep changes minimal and targeted to compile errors.
