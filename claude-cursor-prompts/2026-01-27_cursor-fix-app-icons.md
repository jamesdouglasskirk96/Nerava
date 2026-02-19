CLAUDE PROMPT — Cursor Fix for Remaining Blocker (App Icons)

You are Claude Code. Implement the final blocker from the post‑validation regrade: missing AppIcon PNGs. This is a design asset task, not a code change. Use a Cursor‑ready prompt that clearly instructs the developer/designer on what to add and where.

Regrade Summary:
- Score: 9.2/10
- Only blocker: App icon PNGs missing.
- Code is already submission‑ready.

What to implement:
1) Add three 1024x1024 PNG files (no alpha, sRGB) into:
   Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/

   Filenames MUST match Contents.json:
   - AppIcon.png
   - AppIcon-Dark.png
   - AppIcon-Tinted.png

2) Confirm in Xcode:
   - No yellow warnings for AppIcon
   - Icon shows correctly in light/dark mode on device

Output format (STRICT):
- Scope & Priorities
- Step-by-step Implementation (exact path + filenames)
- QA / Verification checklist (Xcode + device)
- Guardrails (no code refactors, no new deps)

Keep it tight. This is the final gate to 10/10.
