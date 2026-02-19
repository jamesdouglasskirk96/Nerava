Nerava iOS App — App Store Readiness Audit                          
                                                                      
  1. Executive Summary                                                
                                                                      
  The Nerava iOS app is a native SwiftUI shell wrapping a             
  WKWebView-hosted driver web application. The native layer is        
  architecturally sound: a clean 7-state session engine with snapshot 
  persistence, geofencing, dwell detection, Keychain-based auth       
  storage, and a well-typed JavaScript bridge. The codebase is ~2,200 
  lines of Swift across 19 source files — compact and focused.        
                                                                      
  However, the app is not yet ready for App Store submission. There   
  are several critical gaps (missing splash screen, no error recovery 
  in the webview, missing App Store metadata, entitlements referencing
   unused services) and numerous polish items required for a "10/10"  
  launch. The native shell feels functional but early-stage — the     
  permission rationale screens are minimal, there's no haptic         
  feedback, no dynamic type support, no accessibility labels on native
   views, and the offline experience is a static overlay with no retry
   mechanism.                                                         
                                                                      
  Overall Readiness: 5/10 — Strong foundations, significant work      
  remaining.                                                          
                                                                      
  ---                                                                 
  2. Strengths                                                        
                                                                      
  Architecture (Native)                                               
  - Clean separation: Views/, Services/, Engine/, Support/ — easy to  
  navigate and maintain                                               
  - SessionEngine is a robust state machine (7 states, 13 canonical   
  events) with snapshot persistence via SessionSnapshot for crash     
  recovery                                                            
  - Idempotent event emission with PendingEvent — events survive app  
  termination and retry on launch                                     
  - GeofenceManager has FIFO region management (max 2), handles iOS   
  region limits correctly                                             
  - DwellDetector combines radius + speed checks with 5-minute history
   pruning                                                            
  - APIClient has exponential backoff with jitter for retries, proper 
  401/429 handling                                                    
  - APIClientProtocol enables dependency injection for testing        
                                                                      
  Security                                                            
  - Auth tokens stored in iOS Keychain with                           
  kSecAttrAccessibleAfterFirstUnlock — correct protection level       
  - NativeBridge validates origin with exact string matching (not     
  substring)                                                          
  - Debug-only localhost origins via #if DEBUG                        
  - NSAllowsArbitraryLoads is false in ATS config — all traffic is    
  HTTPS                                                               
  - PrivacyInfo.xcprivacy properly declares location collection and   
  UserDefaults access                                                 
                                                                      
  JavaScript Bridge                                                   
  - Injection at atDocumentStart + forMainFrameOnly: true — correct   
  security posture                                                    
  - Dual ready signals (JS event + native message) — robust handshake 
  - Promise-based request() with 10-second timeout                    
  - Web-side useNativeBridge.ts has clean fallback to                 
  navigator.geolocation when native bridge is unavailable             
                                                                      
  Testing                                                             
  - 6 unit tests covering: state transitions, dwell detection,        
  snapshot restore with pending events, grace period expiration,      
  geofence FIFO, event ID passthrough                                 
  - MockAPIClient enables isolated SessionEngine testing              
  - CI-skip annotation on wall-clock-dependent dwell test             
                                                                      
  ---                                                                 
  3. Areas for Improvement (Prioritized)                              
                                                                      
  Critical (P0) — Must Fix Before Submission                          
                                                                      
  P0-1: No Launch/Splash Screen                                       
                                                                      
  The app has no LaunchScreen.storyboard or SwiftUI launch screen     
  configuration. When the app opens, the user sees a black/white      
  screen with a spinner overlay until the webview loads. App Store    
  Guideline 4.0 (Design) requires a polished launch experience.       
                                                                      
  Actionable Steps:                                                   
  - Add LaunchScreen.storyboard with Nerava branding (logo centered on
   brand-color background)                                            
  - OR use the SwiftUI-based launch screen approach in Info.plist     
  (UILaunchScreen key)                                                
  - Ensure the transition from launch screen → webview is seamless    
  (match background colors)                                           
                                                                      
  P0-2: Entitlements Reference Unused CloudKit                        
                                                                      
  Nerava.entitlements declares com.apple.developer.icloud-services:   
  CloudKit and com.apple.developer.icloud-container-identifiers       
  (empty). The app doesn't use CloudKit anywhere. Apple will reject   
  the app for declaring capabilities not used (Guideline 2.5.9).      
                                                                      
  Actionable Steps:                                                   
  - Remove com.apple.developer.icloud-container-identifiers and       
  com.apple.developer.icloud-services from Nerava.entitlements        
  - Only keep aps-environment for push notifications                  
                                                                      
  P0-3: Push Notification Entitlement is "development"                
                                                                      
  The entitlements file has aps-environment: development. This must be
   production for App Store builds. Xcode usually handles this        
  automatically with archive builds, but verify this is configured    
  correctly in the release scheme.                                    
                                                                      
  Actionable Steps:                                                   
  - Confirm the archive/release build configuration uses production   
  APS environment                                                     
  - If using manual signing, update the entitlements for release      
  builds                                                              
                                                                      
  P0-4: Notification Permission Requested at Launch Without Context   
                                                                      
  NeravaApp.init() calls                                              
  NotificationService.shared.requestPermission() immediately at app   
  launch — before the user has any context. Apple will flag this      
  (Guideline 5.1.1(iv)). iOS also tends to suppress prompts if shown  
  before the user has interacted with the app.                        
                                                                      
  Actionable Steps:                                                   
  - Remove requestPermission() from NeravaApp.init()                  
  - Request notification permission contextually — e.g., after the    
  user activates their first exclusive deal, show a rationale screen  
  explaining "We'll notify you when you arrive at the merchant", then 
  prompt                                                              
                                                                      
  P0-5: No Privacy Policy Link in App or App Store Connect            
                                                                      
  No privacy policy URL is referenced in the native iOS app or the    
  driver web app's visible UI. The Flutter app has                    
  https://nerava.network/privacy but this isn't surfaced in the native
   app. App Store Guideline 5.1.1 requires a privacy policy link both 
  in the app and in App Store Connect.                                
                                                                      
  Actionable Steps:                                                   
  - Add privacy policy link to the web app's Account/Settings page    
  - Register https://nerava.network/privacy in App Store Connect      
  - Verify the URL resolves and the content accurately describes      
  location data collection, PostHog analytics, and OTP phone number   
  usage                                                               
                                                                      
  P0-6: App Icon Assets Missing                                       
                                                                      
  Assets.xcassets/AppIcon.appiconset/Contents.json exists but no      
  actual icon image files were found. App Store requires a complete   
  set of app icons.                                                   
                                                                      
  Actionable Steps:                                                   
  - Design and add app icon at 1024x1024 (single-size approach for    
  modern Xcode)                                                       
  - Ensure no alpha channel (App Store rejects icons with             
  transparency)                                                       
                                                                      
  P0-7: WebView Error Recovery is Missing                             
                                                                      
  WebViewRepresentable.Coordinator.webView(_:didFail:) only logs the  
  error and hides the spinner. The user sees a blank white screen with
   no way to recover. No didFailProvisionalNavigation handler exists  
  at all (so DNS failures, TLS errors, etc. are silently swallowed).  
                                                                      
  Actionable Steps:                                                   
  - Add didFailProvisionalNavigation handler                          
  - Show a native error view with "Retry" button when the webview     
  fails to load                                                       
  - Include the error type in the message ("No internet connection" vs
   "Server error")                                                    
  - Add pull-to-refresh on the webview for manual reload              
                                                                      
  P0-8: onChange(of:) Uses Deprecated API                             
                                                                      
  ContentView.swift:46 uses .onChange(of:                             
  locationService.authorizationStatus) { status in — this is the iOS  
  16 closure signature. iOS 17+ requires the two-parameter form:      
  .onChange(of:) { oldValue, newValue in }. If deployment target is   
  iOS 17+, this will produce warnings or fail.                        
                                                                      
  Actionable Steps:                                                   
  - Update to .onChange(of: locationService.authorizationStatus) {    
  oldValue, newValue in }                                             
  - Alternatively, if supporting iOS 16, add if #available or use the 
  appropriate modifier                                                
                                                                      
  ---                                                                 
  High (P1) — Strongly Recommended Pre-Launch                         
                                                                      
  P1-1: No App Store Metadata Prepared                                
                                                                      
  No screenshots, app description, keywords, promotional text, or app 
  preview videos exist. These are required for submission.            
                                                                      
  Actionable Steps:                                                   
  - Write app name ("Nerava"), subtitle ("Exclusive Deals While You   
  Charge"), and description                                           
  - Capture screenshots on iPhone 6.7" (Pro Max) and 6.1" (Pro) —     
  minimum 3, ideally 5-8                                              
  - Feature the Live Coordination UI (stall indicators, social proof, 
  fullscreen ticket)                                                  
  - Add keywords: "EV charging, electric vehicle, charger deals,      
  exclusive offers, merchant deals"                                   
  - Set primary category: "Lifestyle" or "Navigation"                 
                                                                      
  P1-2: No Universal Links / Deep Linking                             
                                                                      
  No apple-app-site-association file, no Associated Domains           
  entitlement. The app can't handle links from emails, SMS, or other  
  apps.                                                               
                                                                      
  Actionable Steps:                                                   
  - Add applinks:app.nerava.network to Associated Domains entitlement 
  - Host /.well-known/apple-app-site-association on app.nerava.network
  - Handle incoming URLs in the SwiftUI app lifecycle                 
                                                                      
  P1-3: Accessibility — No VoiceOver Support on Native Views          
                                                                      
  The permission rationale views (LocationPermissionView,             
  BackgroundPermissionView) and loading/offline overlays have no      
  accessibility labels, hints, or traits. The webview content relies  
  entirely on web-side ARIA attributes.                               
                                                                      
  Actionable Steps:                                                   
  - Add .accessibilityLabel() and .accessibilityHint() to all native  
  buttons                                                             
  - Mark the loading overlay as .accessibilityElement(children:       
  .ignore) with a summary label                                       
  - Test the full flow with VoiceOver enabled on a real device        
                                                                      
  P1-4: No Dynamic Type Support                                       
                                                                      
  All native views use fixed font sizes (.title2, .headline, system   
  defaults). They don't respond to Dynamic Type settings. HIG strongly
   recommends supporting Dynamic Type.                                
                                                                      
  Actionable Steps:                                                   
  - Use .font(.title2) (already works with Dynamic Type) — verify text
   doesn't clip                                                       
  - Ensure buttons and containers scale with text size                
  - Test with Accessibility Inspector at "Extra Extra Extra Large"    
  text                                                                
                                                                      
  P1-5: Offline Experience is a Dead End                              
                                                                      
  The OfflineOverlay shows "No internet connection" with no retry     
  button. The user is stuck until connectivity returns and the overlay
   auto-dismisses. There's also no caching strategy for webview       
  content.                                                            
                                                                      
  Actionable Steps:                                                   
  - Add a "Retry" button to OfflineOverlay that triggers              
  webView.reload()                                                    
  - Consider WKWebsiteDataStore caching policy to allow basic offline 
  browsing of previously loaded content                               
  - Show the last loaded state rather than a blank screen when        
  connectivity drops mid-session                                      
                                                                      
  P1-6: Bundle ID Format                                              
                                                                      
  The bundle ID is EVcharging.Nerava — this uses non-standard         
  capitalization. Apple recommends reverse-DNS format                 
  (network.nerava.app or com.nerava.driver). While not a rejection    
  reason, it looks unprofessional and can cause signing issues.       
                                                                      
  Actionable Steps:                                                   
  - Consider updating to network.nerava.driver or com.nerava.app      
  before first submission (changing bundle ID after submission is much
   harder)                                                            
                                                                      
  P1-7: Web App Auth Stores Token in localStorage                     
                                                                      
  auth.ts:124 stores access_token in localStorage. In a WKWebView     
  context, localStorage is more ephemeral than in Safari — it can be  
  purged by iOS under memory pressure. The native side correctly uses 
  Keychain, but if the webview's localStorage is cleared, the user is 
  silently logged out with no recovery mechanism.                     
                                                                      
  Actionable Steps:                                                   
  - After OTP verification, call                                      
  window.neravaNative?.setAuthToken(token) (already done in           
  useNativeBridge)                                                    
  - On webview reload, inject the Keychain token back into the webview
   via the bridge                                                     
  - Add a GET_AUTH_TOKEN bridge action so the web app can request the 
  token from Keychain on startup                                      
                                                                      
  P1-8: No Haptic Feedback                                            
                                                                      
  No UIImpactFeedbackGenerator, UINotificationFeedbackGenerator, or   
  SwiftUI .sensoryFeedback() calls anywhere. Key moments (session     
  activated, arrived at merchant, exclusive redeemed) should have     
  haptics.                                                            
                                                                      
  Actionable Steps:                                                   
  - Add success haptic in webConfirmsExclusiveActivated and           
  webConfirmsVisitVerified                                            
  - Add light impact on geofence entry/exit events                    
  - Web-side: use navigator.vibrate() API for the "Show Host" button  
  tap (Safari/WKWebView support varies — test)                        
                                                                      
  ---                                                                 
  Medium (P2) — Recommended for 10/10                                 
                                                                      
  P2-1: Permission Rationale Screens Lack Polish                      
                                                                      
  LocationPermissionView and BackgroundPermissionView are minimal text
   boxes with .ultraThinMaterial backgrounds. They don't match the web
   app's design language (rounded corners, brand colors,              
  illustrations).                                                     
                                                                      
  Actionable Steps:                                                   
  - Add an SF Symbol icon (e.g., location.fill) above the title       
  - Use the brand blue (#1877F2) for the Continue button              
  - Add a brief visual (map illustration or charger icon) to make the 
  value proposition tangible                                          
  - Match the rounded-3xl style from the web app                      
                                                                      
  P2-2: SessionSnapshot Uses UserDefaults.synchronize()               
                                                                      
  SessionSnapshot.swift:29 calls .synchronize() which Apple has       
  deprecated and says is unnecessary since iOS 12. It's a no-op but   
  signals dated code.                                                 
                                                                      
  Actionable Steps:                                                   
  - Remove the .synchronize() call                                    
                                                                      
  P2-3: Separate CLLocationManager Instances in LocationService and   
  GeofenceManager                                                     
                                                                      
  Both LocationService and GeofenceManager create their own           
  CLLocationManager. While functional, Apple's docs recommend using a 
  single CLLocationManager instance per app. Multiple instances can   
  cause subtle bugs with authorization status propagation.            
                                                                      
  Actionable Steps:                                                   
  - Consider sharing a single CLLocationManager instance, with        
  GeofenceManager only handling region monitoring methods through     
  delegation                                                          
                                                                      
  P2-4: No WKUIDelegate                                               
                                                                      
  The webview has no WKUIDelegate assigned. This means JavaScript     
  alert(), confirm(), and prompt() calls are silently swallowed. The  
  web app uses alert() in FullScreenTicket.tsx for copy feedback      
  (before Gemini's fix), and may use it elsewhere.                    
                                                                      
  Actionable Steps:                                                   
  - Implement WKUIDelegate on the Coordinator                         
  - Handle runJavaScriptAlertPanelWithMessage and                     
  runJavaScriptConfirmPanelWithMessage                                
  - Present native UIAlertController for these calls                  
                                                                      
  P2-5: ISO8601DateFormatter Created on Every API Call                
                                                                      
  APIClient.swift creates a new ISO8601DateFormatter() instance on    
  every event emission (lines 53-54). These are expensive to create.  
                                                                      
  Actionable Steps:                                                   
  - Create a static ISO8601DateFormatter instance on APIClient and    
  reuse it                                                            
                                                                      
  P2-6: Web App Title is "nerava-ui"                                  
                                                                      
  index.html:14 has <title>nerava-ui</title>. While the native shell  
  hides the title bar, this shows up in the iOS App Switcher and is   
  visible to reviewers.                                               
                                                                      
  Actionable Steps:                                                   
  - Change to <title>Nerava</title>                                   
                                                                      
  P2-7: Favicon is Vite Logo                                          
                                                                      
  index.html:5 references /vite.svg as the favicon. Visible in webview
   debug tools and potentially in error screens.                      
                                                                      
  Actionable Steps:                                                   
  - Replace with Nerava logo/icon                                     
                                                                      
  P2-8: No Swipe-Back Gesture in WebView                              
                                                                      
  Standard WKWebView doesn't support swipe-back navigation. The web   
  app handles its own navigation with modals and screens, so there's  
  no browser-style history stack. However, if the user navigates      
  within the webview (e.g., deep-linked content), there's no way to go
   back.                                                              
                                                                      
  Actionable Steps:                                                   
  - Set webView.allowsBackForwardNavigationGestures = true if web     
  navigation history is relevant                                      
  - OR ensure the web app always provides a close/back button for     
  every screen                                                        
                                                                      
  P2-9: No @Sendable Compliance for Concurrency                       
                                                                      
  Several closures passed to DispatchQueue.main.async and timer       
  handlers aren't marked @Sendable. As Swift strict concurrency       
  checking advances, these will produce warnings.                     
                                                                      
  Actionable Steps:                                                   
  - Audit closures crossing isolation boundaries                      
  - Add @Sendable where needed, particularly in BackgroundTimer and   
  APIClient                                                           
                                                                      
  ---                                                                 
  Low (P3) — Post-Launch Enhancements                                 
                                                                      
  P3-1: No iPad Layout Optimization                                   
  The project's SUPPORTED_PLATFORMS includes iPad (device families    
  1,2). The web app is designed mobile-first with max-w-md. On iPad,  
  the user sees a narrow column centered on a large screen.           
                                                                      
  Actionable Steps:                                                   
  - Either optimize the web layout for iPad, or restrict to           
  iPhone-only in Xcode project settings                               
                                                                      
  P3-2: No Fastlane/CI/CD Pipeline                                    
  No automated build, test, or distribution pipeline.                 
                                                                      
  P3-3: Test Coverage is Minimal                                      
  6 unit tests for SessionEngine, 0 for NativeBridge, LocationService,
   APIClient, KeychainService, NetworkMonitor. The default            
  NeravaTests.swift is still a template. No UI tests beyond the       
  template.                                                           
                                                                      
  P3-4: No Remote Config Fetch on Launch                              
  APIClient.fetchConfig() exists but is never called. SessionEngine   
  uses hardcoded .defaults. The /v1/native/config endpoint could      
  provide updated parameters.                                         
                                                                      
  P3-5: Log.scrubSessionId() and Log.scrubCoordinate() Are Defined But
   Never Used                                                         
  These privacy-preserving log helpers exist in Log.swift but none of 
  the actual logging calls use them. Raw session IDs and coordinates  
  appear in logs.                                                     
                                                                      
  P3-6: No Analytics in Native Layer                                  
  All analytics (PostHog) are in the web app. Native-side events      
  (geofence triggers, background state transitions, app lifecycle)    
  have no analytics pipeline.                                         
                                                                      
  ---                                                                 
  4. Summary Table                                                    
  #: P0-1                                                             
  Issue: No launch screen                                             
  Priority: Critical                                                  
  Guideline: HIG: Launch Screen, Guideline 4.0                        
  ────────────────────────────────────────                            
  #: P0-2                                                             
  Issue: Unused CloudKit entitlement                                  
  Priority: Critical                                                  
  Guideline: Guideline 2.5.9                                          
  ────────────────────────────────────────                            
  #: P0-3                                                             
  Issue: APS environment = development                                
  Priority: Critical                                                  
  Guideline: Build configuration                                      
  ────────────────────────────────────────                            
  #: P0-4                                                             
  Issue: Notification prompt at launch                                
  Priority: Critical                                                  
  Guideline: Guideline 5.1.1(iv)                                      
  ────────────────────────────────────────                            
  #: P0-5                                                             
  Issue: No privacy policy link                                       
  Priority: Critical                                                  
  Guideline: Guideline 5.1.1                                          
  ────────────────────────────────────────                            
  #: P0-6                                                             
  Issue: Missing app icon assets                                      
  Priority: Critical                                                  
  Guideline: App Store requirement                                    
  ────────────────────────────────────────                            
  #: P0-7                                                             
  Issue: No webview error recovery                                    
  Priority: Critical                                                  
  Guideline: Guideline 2.1 (completeness)                             
  ────────────────────────────────────────                            
  #: P0-8                                                             
  Issue: Deprecated onChange API                                      
  Priority: Critical                                                  
  Guideline: Build warning / crash risk                               
  ────────────────────────────────────────                            
  #: P1-1                                                             
  Issue: No App Store metadata                                        
  Priority: High                                                      
  Guideline: Guideline 2.3                                            
  ────────────────────────────────────────                            
  #: P1-2                                                             
  Issue: No universal links                                           
  Priority: High                                                      
  Guideline: HIG: Navigation                                          
  ────────────────────────────────────────                            
  #: P1-3                                                             
  Issue: No VoiceOver on native views                                 
  Priority: High                                                      
  Guideline: HIG: Accessibility                                       
  ────────────────────────────────────────                            
  #: P1-4                                                             
  Issue: No Dynamic Type support                                      
  Priority: High                                                      
  Guideline: HIG: Typography                                          
  ────────────────────────────────────────                            
  #: P1-5                                                             
  Issue: Offline is a dead end                                        
  Priority: High                                                      
  Guideline: Guideline 2.1                                            
  ────────────────────────────────────────                            
  #: P1-6                                                             
  Issue: Non-standard bundle ID                                       
  Priority: High                                                      
  Guideline: Best practice                                            
  ────────────────────────────────────────                            
  #: P1-7                                                             
  Issue: localStorage token fragility                                 
  Priority: High                                                      
  Guideline: Security / UX                                            
  ────────────────────────────────────────                            
  #: P1-8                                                             
  Issue: No haptic feedback                                           
  Priority: High                                                      
  Guideline: HIG: Feedback                                            
  ────────────────────────────────────────                            
  #: P2-1                                                             
  Issue: Permission screens need polish                               
  Priority: Medium                                                    
  Guideline: HIG: Permission                                          
  ────────────────────────────────────────                            
  #: P2-2                                                             
  Issue: Deprecated .synchronize()                                    
  Priority: Medium                                                    
  Guideline: Best practice                                            
  ────────────────────────────────────────                            
  #: P2-3                                                             
  Issue: Dual CLLocationManager                                       
  Priority: Medium                                                    
  Guideline: Apple docs                                               
  ────────────────────────────────────────                            
  #: P2-4                                                             
  Issue: No WKUIDelegate                                              
  Priority: Medium                                                    
  Guideline: Guideline 2.1                                            
  ────────────────────────────────────────                            
  #: P2-5                                                             
  Issue: ISO8601 formatter per call                                   
  Priority: Medium                                                    
  Guideline: Performance                                              
  ────────────────────────────────────────                            
  #: P2-6                                                             
  Issue: Title is "nerava-ui"                                         
  Priority: Medium                                                    
  Guideline: Guideline 2.3                                            
  ────────────────────────────────────────                            
  #: P2-7                                                             
  Issue: Vite favicon                                                 
  Priority: Medium                                                    
  Guideline: Polish                                                   
  ────────────────────────────────────────                            
  #: P2-8                                                             
  Issue: No swipe-back gesture                                        
  Priority: Medium                                                    
  Guideline: HIG: Navigation                                          
  ────────────────────────────────────────                            
  #: P2-9                                                             
  Issue: @Sendable compliance                                         
  Priority: Medium                                                    
  Guideline: Future-proofing                                          
  ────────────────────────────────────────                            
  #: P3-1                                                             
  Issue: No iPad optimization                                         
  Priority: Low                                                       
  Guideline: HIG: Layout                                              
  ────────────────────────────────────────                            
  #: P3-2                                                             
  Issue: No CI/CD pipeline                                            
  Priority: Low                                                       
  Guideline: Best practice                                            
  ────────────────────────────────────────                            
  #: P3-3                                                             
  Issue: Minimal test coverage                                        
  Priority: Low                                                       
  Guideline: Best practice                                            
  ────────────────────────────────────────                            
  #: P3-4                                                             
  Issue: Config never fetched remotely                                
  Priority: Low                                                       
  Guideline: Feature gap                                              
  ────────────────────────────────────────                            
  #: P3-5                                                             
  Issue: Log scrubbers unused                                         
  Priority: Low                                                       
  Guideline: Privacy                                                  
  ────────────────────────────────────────                            
  #: P3-6                                                             
  Issue: No native analytics                                          
  Priority: Low                                                       
  Guideline: Observability                                            
  ---                                                                 
  5. Roadmap Suggestion                                               
                                                                      
  Phase 1: Submission Blockers (P0)                                   
                                                                      
  - Add launch screen and app icon                                    
  - Remove CloudKit entitlement, fix APS environment                  
  - Move notification permission to contextual trigger                
  - Add webview error recovery + didFailProvisionalNavigation         
  - Add privacy policy link                                           
  - Fix onChange deprecation                                          
                                                                      
  Phase 2: Pre-Launch Polish (P1)                                     
                                                                      
  - Prepare App Store metadata (screenshots, description, keywords)   
  - Add VoiceOver labels to native views                              
  - Improve offline experience with retry button                      
  - Add token sync via bridge (Keychain → webview on reload)          
  - Add haptic feedback at key moments                                
  - Fix bundle ID before first submission                             
  - Add universal links support                                       
                                                                      
  Phase 3: Post-Launch Enhancement (P2+)                              
                                                                      
  - Polish permission rationale screens                               
  - Implement WKUIDelegate for JS alerts                              
  - Performance optimizations (formatter caching, single              
  CLLocationManager)                                                  
  - Expand test coverage                                              
  - Add CI/CD with Fastlane                                           
  - iPad layout optimization                                          
                                                                      
⏺ That's the complete audit. Every finding is grounded in a specific  
  file and line number I read during this analysis. The 8 P0 items are
   the minimum bar for submission; the P1 items differentiate         
  "approved" from "10/10."
