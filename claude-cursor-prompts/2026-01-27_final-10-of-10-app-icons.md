# Cursor Prompt — Final 10/10: Generate App Icon Assets

## Context

The Nerava iOS app scores 9.2/10. All code is submission-ready. The **sole remaining blocker** is 3 missing app icon PNGs. The asset catalog manifest (`Contents.json`) is already correct — only the image files need to be created.

**Source logo:** `apps/driver/public/nerava-logo.png` (4718x1194, landscape, has alpha)
**Target directory:** `Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/`

## Scope

Generate 3 app icon PNGs from the existing Nerava logo. No code changes. No dependency installs.

## Step-by-Step Implementation

### Step 1: Generate the 3 icon PNGs

Write and run a Swift script (uses only built-in macOS frameworks — no dependencies) that:

1. Loads the source logo from `apps/driver/public/nerava-logo.png`
2. Creates 3 separate 1024x1024 opaque PNG images:
   - **AppIcon.png** — White background (#FFFFFF), logo centered with padding
   - **AppIcon-Dark.png** — Near-black background (#0A0A0A), logo centered with padding
   - **AppIcon-Tinted.png** — White background, logo rendered as a **solid gray silhouette** (#808080) for iOS 18 automatic tinting
3. Writes all 3 to `Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/`

**Script requirements:**
- Canvas: 1024x1024 pixels, sRGB, **no alpha channel**
- Logo should be scaled to fit within ~60-70% of the canvas width, centered both horizontally and vertically
- The logo has transparency — the background color must fill the entire canvas behind it
- For the tinted variant, replace all non-transparent logo pixels with a single gray (#808080). iOS will recolor this automatically.
- Use `CoreGraphics` and `Foundation` only (both ship with Xcode, no installs needed)
- Output format: PNG, no alpha

Here is the exact Swift script to create, save as `generate_app_icons.swift` in the repo root, then run with `swift generate_app_icons.swift`:

```swift
import Foundation
import CoreGraphics
import UniformTypeIdentifiers

let size = 1024
let logoPath = "apps/driver/public/nerava-logo.png"
let outputDir = "Nerava/Nerava/Assets.xcassets/AppIcon.appiconset"

struct IconSpec {
    let filename: String
    let bgRed: CGFloat
    let bgGreen: CGFloat
    let bgBlue: CGFloat
    let tinted: Bool  // If true, render logo as solid gray silhouette
}

let specs: [IconSpec] = [
    IconSpec(filename: "AppIcon.png",        bgRed: 1.0,    bgGreen: 1.0,    bgBlue: 1.0,    tinted: false),
    IconSpec(filename: "AppIcon-Dark.png",   bgRed: 0.039,  bgGreen: 0.039,  bgBlue: 0.039,  tinted: false),
    IconSpec(filename: "AppIcon-Tinted.png", bgRed: 1.0,    bgGreen: 1.0,    bgBlue: 1.0,    tinted: true),
]

// Load source logo
guard let logoData = FileManager.default.contents(atPath: logoPath),
      let dataProvider = CGDataProvider(data: logoData as CFData),
      let logoImage = CGImage(pngDataProviderSource: dataProvider, decode: nil, shouldInterpolate: true, intent: .defaultIntent) else {
    print("ERROR: Could not load logo from \(logoPath)")
    exit(1)
}

let logoW = CGFloat(logoImage.width)
let logoH = CGFloat(logoImage.height)
let canvasSize = CGFloat(size)

// Scale logo to fit ~65% of canvas width, maintain aspect ratio
let targetWidth = canvasSize * 0.65
let scale = targetWidth / logoW
let drawW = logoW * scale
let drawH = logoH * scale
let drawX = (canvasSize - drawW) / 2.0
let drawY = (canvasSize - drawH) / 2.0

let colorSpace = CGColorSpaceCreateDeviceRGB()

for spec in specs {
    // Create opaque bitmap context (no alpha)
    guard let ctx = CGContext(
        data: nil,
        width: size,
        height: size,
        bitsPerComponent: 8,
        bytesPerRow: size * 4,
        space: colorSpace,
        bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue
    ) else {
        print("ERROR: Could not create context for \(spec.filename)")
        continue
    }

    // Fill background
    ctx.setFillColor(red: spec.bgRed, green: spec.bgGreen, blue: spec.bgBlue, alpha: 1.0)
    ctx.fill(CGRect(x: 0, y: 0, width: canvasSize, height: canvasSize))

    let drawRect = CGRect(x: drawX, y: drawY, width: drawW, height: drawH)

    if spec.tinted {
        // Draw logo as a clipping mask, fill with gray
        ctx.saveGState()
        ctx.clip(to: drawRect, mask: logoImage)
        ctx.setFillColor(red: 0.5, green: 0.5, blue: 0.5, alpha: 1.0)
        ctx.fill(drawRect)
        ctx.restoreGState()
    } else {
        // Draw logo normally
        ctx.draw(logoImage, in: drawRect)
    }

    // Write PNG
    guard let outputImage = ctx.makeImage() else {
        print("ERROR: Could not create image for \(spec.filename)")
        continue
    }

    let outputPath = "\(outputDir)/\(spec.filename)" as NSString
    guard let dest = CGImageDestinationCreateWithURL(
        URL(fileURLWithPath: outputPath as String) as CFURL,
        UTType.png.identifier as CFString,
        1,
        nil
    ) else {
        print("ERROR: Could not create destination for \(spec.filename)")
        continue
    }

    CGImageDestinationAddImage(dest, outputImage, nil)
    if CGImageDestinationFinalize(dest) {
        print("OK: \(spec.filename)")
    } else {
        print("ERROR: Failed to write \(spec.filename)")
    }
}

print("Done. Check \(outputDir)/")
```

### Step 2: Run the script

```bash
cd /Users/jameskirk/Desktop/Nerava
swift generate_app_icons.swift
```

Expected output:
```
OK: AppIcon.png
OK: AppIcon-Dark.png
OK: AppIcon-Tinted.png
Done. Check Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/
```

### Step 3: Verify files exist

```bash
ls -la Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/
```

Should show `AppIcon.png`, `AppIcon-Dark.png`, `AppIcon-Tinted.png`, and `Contents.json`.

### Step 4: Clean up

```bash
rm generate_app_icons.swift
```

## QA / Verification Checklist

- [ ] All 3 PNGs exist in `AppIcon.appiconset/`
- [ ] Each is 1024x1024 (`sips -g pixelWidth -g pixelHeight <file>`)
- [ ] Each has no alpha (`sips -g hasAlpha <file>` → `no`)
- [ ] Xcode → Assets → AppIcon → no yellow/red warnings
- [ ] `xcodebuild clean build -scheme Nerava -configuration Release -quiet` → zero errors
- [ ] Install on device → icon visible on home screen (not blank)
- [ ] Switch to dark mode → dark variant shows
- [ ] Contents.json was NOT modified (already correct)

## App Store Submission Checklist (Complete)

- [x] Launch screen: branded, no flash
- [x] No permission prompt at launch
- [x] Privacy policy in-app (Account page + error overlays)
- [x] Error recovery on all failure paths
- [x] Entitlements clean (no CloudKit)
- [x] PrivacyInfo.xcprivacy present
- [x] Accessibility labels on all native views
- [x] Back navigation gesture enabled
- [x] Permission icons correctly differentiated
- [ ] **App icon: 3 variants in asset catalog** ← THIS PROMPT

## Guardrails

- Do NOT modify `Contents.json` — it is already correct
- Do NOT modify any Swift source file
- Do NOT modify any TypeScript/HTML file
- Do NOT install any dependencies (script uses only built-in macOS frameworks)
- Do NOT change the Xcode project file
- The ONLY change is adding 3 PNG files to an existing directory
- Delete the generator script after running it

## Post-Completion

Once the 3 PNGs are in place: **10/10 — unconditional GO for App Store submission.**

If the generated icons are placeholder quality, swap them with designer-produced versions later. The filenames and specs (1024x1024, no alpha, sRGB) must remain the same.
