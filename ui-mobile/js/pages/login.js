/**
 * Login page with Google, Apple, and Phone OTP options
 */
import { apiGoogleLogin, apiAppleLogin, apiOtpStart, apiOtpVerify } from '../core/api.js';
import { setTokens } from '../core/auth.js';
import { setTab } from '../app.js';

let currentStep = 'provider'; // 'provider', 'phone-input', 'otp-input'

export async function initLoginPage(rootEl) {
    console.log('[Login] Initializing login page...');
    
    renderLoginPage(rootEl);
    wireLoginHandlers(rootEl);
}

function renderLoginPage(rootEl) {
    rootEl.innerHTML = `
        <div class="login-container" style="
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        ">
            <div class="login-card" style="
                background: white;
                border-radius: 24px;
                padding: 40px 32px;
                width: 100%;
                max-width: 400px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            ">
                <div class="login-header" style="text-align: center; margin-bottom: 32px;">
                    <h1 style="font-size: 28px; font-weight: 700; color: #111827; margin: 0 0 8px 0;">
                        Welcome to Nerava
                    </h1>
                    <p style="font-size: 14px; color: #6b7280; margin: 0;">
                        Sign in to continue
                    </p>
                </div>
                
                <!-- Provider Selection -->
                <div id="login-provider-step" class="login-step" style="display: ${currentStep === 'provider' ? 'block' : 'none'};">
                    <div class="login-buttons" style="display: flex; flex-direction: column; gap: 12px;">
                        <button id="btn-google-login" class="login-btn" style="
                            width: 100%;
                            padding: 14px;
                            border: 1px solid #e5e7eb;
                            border-radius: 12px;
                            background: white;
                            color: #111827;
                            font-size: 16px;
                            font-weight: 600;
                            cursor: pointer;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            gap: 12px;
                            transition: all 0.2s;
                        ">
                            <svg width="20" height="20" viewBox="0 0 24 24">
                                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                            </svg>
                            Continue with Google
                        </button>
                        
                        <button id="btn-apple-login" class="login-btn" style="
                            width: 100%;
                            padding: 14px;
                            border: 1px solid #e5e7eb;
                            border-radius: 12px;
                            background: #000;
                            color: white;
                            font-size: 16px;
                            font-weight: 600;
                            cursor: pointer;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            gap: 12px;
                            transition: all 0.2s;
                        ">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/>
                            </svg>
                            Continue with Apple
                        </button>
                        
                        <div style="display: flex; align-items: center; gap: 12px; margin: 20px 0;">
                            <div style="flex: 1; height: 1px; background: #e5e7eb;"></div>
                            <span style="font-size: 14px; color: #6b7280;">or</span>
                            <div style="flex: 1; height: 1px; background: #e5e7eb;"></div>
                        </div>
                        
                        <button id="btn-phone-login" class="login-btn" style="
                            width: 100%;
                            padding: 14px;
                            border: 1px solid #e5e7eb;
                            border-radius: 12px;
                            background: white;
                            color: #111827;
                            font-size: 16px;
                            font-weight: 600;
                            cursor: pointer;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            gap: 12px;
                        ">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                            </svg>
                            Continue with Phone
                        </button>
                    </div>
                </div>
                
                <!-- Phone Input Step -->
                <div id="login-phone-step" class="login-step" style="display: ${currentStep === 'phone' ? 'block' : 'none'};">
                    <div style="margin-bottom: 20px;">
                        <label style="display: block; font-size: 14px; font-weight: 600; color: #111827; margin-bottom: 8px;">
                            Phone Number
                        </label>
                        <input 
                            type="tel" 
                            id="phone-input" 
                            placeholder="+1 (555) 123-4567"
                            style="
                                width: 100%;
                                padding: 12px;
                                border: 1px solid #e5e7eb;
                                border-radius: 8px;
                                font-size: 16px;
                            "
                        />
                    </div>
                    <button id="btn-request-otp" class="login-btn" style="
                        width: 100%;
                        padding: 14px;
                        border: none;
                        border-radius: 12px;
                        background: #667eea;
                        color: white;
                        font-size: 16px;
                        font-weight: 600;
                        cursor: pointer;
                    ">
                        Send Verification Code
                    </button>
                    <button id="btn-back-provider" class="login-btn" style="
                        width: 100%;
                        padding: 12px;
                        border: none;
                        background: transparent;
                        color: #6b7280;
                        font-size: 14px;
                        cursor: pointer;
                        margin-top: 12px;
                    ">
                        ← Back
                    </button>
                </div>
                
                <!-- OTP Input Step -->
                <div id="login-otp-step" class="login-step" style="display: ${currentStep === 'otp' ? 'block' : 'none'};">
                    <div style="margin-bottom: 20px;">
                        <label style="display: block; font-size: 14px; font-weight: 600; color: #111827; margin-bottom: 8px;">
                            Verification Code
                        </label>
                        <input 
                            type="text" 
                            id="otp-input" 
                            placeholder="123456"
                            maxlength="6"
                            style="
                                width: 100%;
                                padding: 12px;
                                border: 1px solid #e5e7eb;
                                border-radius: 8px;
                                font-size: 24px;
                                text-align: center;
                                letter-spacing: 8px;
                            "
                        />
                        <p style="font-size: 12px; color: #6b7280; margin-top: 8px;">
                            Enter the 6-digit code sent to your phone
                        </p>
                    </div>
                    <button id="btn-verify-otp" class="login-btn" style="
                        width: 100%;
                        padding: 14px;
                        border: none;
                        border-radius: 12px;
                        background: #667eea;
                        color: white;
                        font-size: 16px;
                        font-weight: 600;
                        cursor: pointer;
                    ">
                        Verify Code
                    </button>
                    <button id="btn-back-phone" class="login-btn" style="
                        width: 100%;
                        padding: 12px;
                        border: none;
                        background: transparent;
                        color: #6b7280;
                        font-size: 14px;
                        cursor: pointer;
                        margin-top: 12px;
                    ">
                        ← Back
                    </button>
                </div>
                
                <div id="login-error" style="
                    margin-top: 16px;
                    padding: 12px;
                    background: #fee2e2;
                    color: #dc2626;
                    border-radius: 8px;
                    font-size: 14px;
                    display: none;
                "></div>
            </div>
        </div>
    `;
}

function wireLoginHandlers(rootEl) {
    const errorEl = rootEl.querySelector('#login-error');
    
    function showError(message) {
        errorEl.textContent = message;
        errorEl.style.display = 'block';
    }
    
    function hideError() {
        errorEl.style.display = 'none';
    }
    
    function showStep(step) {
        currentStep = step;
        rootEl.querySelectorAll('.login-step').forEach(el => el.style.display = 'none');
        rootEl.querySelector(`#login-${step}-step`).style.display = 'block';
        hideError();
    }
    
    let googleClientId = null;
    let googleInitialized = false;
    
    // Initialize Google Sign-In when page loads
    async function initGoogleSignIn() {
        // Wait for Google Identity Services to load
        if (typeof google === 'undefined' || !google.accounts) {
            // Retry after a short delay
            setTimeout(initGoogleSignIn, 100);
            return;
        }
        
        // Get Google Client ID from backend config API
        try {
            // Get API base - use getApiBase from api.js if available, otherwise fallback
            let apiBase;
            try {
                const { getApiBase } = await import('../core/api.js');
                apiBase = getApiBase();
            } catch {
                // Fallback if api.js not available - check meta tag first
                const apiBaseMeta = document.querySelector('meta[name="nerava-api-base"]');
                apiBase = window.NERAVA_API_BASE || (apiBaseMeta && apiBaseMeta.content) || window.API_BASE_URL || '';
            }
            const configResponse = await fetch(`${apiBase}/v1/public/config`);
            if (configResponse.ok) {
                const config = await configResponse.json();
                googleClientId = config.google_client_id || '';
            } else {
                console.warn('[Login] Failed to fetch config from backend, falling back to localStorage');
                googleClientId = localStorage.getItem('GOOGLE_CLIENT_ID') || '';
            }
        } catch (error) {
            console.warn('[Login] Error fetching config from backend, falling back to localStorage:', error);
            googleClientId = localStorage.getItem('GOOGLE_CLIENT_ID') || '';
        }
        
        if (!googleClientId) {
            console.warn('[Login] Google Client ID not configured. Google Sign-In will show an error when clicked.');
            console.warn('[Login] The Google Client ID should be configured via GOOGLE_CLIENT_ID environment variable on the backend.');
            googleInitialized = false;
            
            // Show UI message if Google sign-in is not configured
            const googleBtn = rootEl.querySelector('#btn-google-login');
            if (googleBtn) {
                googleBtn.disabled = true;
                googleBtn.style.opacity = '0.5';
                googleBtn.style.cursor = 'not-allowed';
            }
            return;
        }
        
        // Initialize Google Identity Services with callback
        google.accounts.id.initialize({
            client_id: googleClientId,
            callback: handleGoogleSignIn,
        });
        
        googleInitialized = true;
        console.log('[Login] Google Sign-In initialized with client ID:', googleClientId.substring(0, 20) + '...');
    }
    
    // Handle Google Sign-In callback
    async function handleGoogleSignIn(response) {
        try {
            hideError();
            const btn = rootEl.querySelector('#btn-google-login');
            if (btn) {
                btn.disabled = true;
                btn.textContent = 'Signing in...';
            }
            
            // Extract ID token from credential response
            const idToken = response.credential;
            
            if (!idToken) {
                throw new Error('No ID token received from Google');
            }
            
            console.log('[Login] Google Sign-In successful, sending ID token to backend...');
            
            // Call backend with ID token
            const result = await apiGoogleLogin(idToken);
            
            console.log('[Login] Backend authentication successful');
            
            // Store tokens
            setTokens(result.access_token, result.refresh_token);
            
            // Redirect to app
            window.location.hash = '#/wallet';
            window.location.reload();
            
        } catch (error) {
            console.error('[Login] Google sign-in callback error:', error);
            showError(error.message || 'Google Sign-In failed');
            const btn = rootEl.querySelector('#btn-google-login');
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Continue with Google';
            }
        }
    }
    
    // Google login button click handler
    rootEl.querySelector('#btn-google-login')?.addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        try {
            hideError();
            
            // Check if Google Identity Services is loaded
            if (typeof google === 'undefined' || !google.accounts) {
                showError('Google Sign-In is still loading. Please wait a moment and try again.');
                return;
            }
            
            // Check if initialized
            if (!googleInitialized) {
                // Try to fetch client ID from backend if not already loaded
                if (!googleClientId) {
                    try {
                        let apiBase;
                        try {
                            const { getApiBase } = await import('../core/api.js');
                            apiBase = getApiBase();
                        } catch {
                            // Fallback if api.js not available - check meta tag first
                            const apiBaseMeta = document.querySelector('meta[name="nerava-api-base"]');
                            apiBase = window.NERAVA_API_BASE || (apiBaseMeta && apiBaseMeta.content) || window.API_BASE_URL || '';
                        }
                        const configResponse = await fetch(`${apiBase}/v1/public/config`);
                        if (configResponse.ok) {
                            const config = await configResponse.json();
                            googleClientId = config.google_client_id || '';
                        }
                    } catch (error) {
                        console.warn('[Login] Error fetching config:', error);
                    }
                }
                
                if (!googleClientId) {
                    showError('Google Sign-In is not configured. Please use Phone OTP or contact support.');
                    return;
                }
                // Initialize now
                google.accounts.id.initialize({
                    client_id: googleClientId,
                    callback: handleGoogleSignIn,
                });
                googleInitialized = true;
            }
            
            // Trigger Google Sign-In popup/flow
            // Use prompt() which will show One Tap or a popup
            google.accounts.id.prompt((notification) => {
                if (notification.isNotDisplayed()) {
                    // One Tap can't be displayed, try alternative flow
                    console.log('[Login] One Tap not available, trying alternative flow...');
                    // For button clicks, we can use the OAuth2 code flow
                    // But the ID token flow is simpler - trigger it manually
                    // The prompt() should still work, but if not, show helpful error
                    showError('Google Sign-In popup was blocked or unavailable. Please allow popups and try again.');
                } else if (notification.isSkippedMoment()) {
                    // User dismissed One Tap - that's OK, they can click button again
                    console.log('[Login] One Tap skipped by user');
                } else if (notification.isDismissedMoment()) {
                    console.log('[Login] One Tap dismissed by user');
                }
            });
            
        } catch (error) {
            console.error('[Login] Google login error:', error);
            showError(error.message || 'Google login failed');
        }
    });
    
    // Initialize Google Sign-In after a short delay to ensure script is loaded
    setTimeout(initGoogleSignIn, 500);
    
    // Apple login - check if configured and hide button if not
    async function initAppleSignIn() {
        // Get Apple Client ID from backend config API
        try {
            let apiBase;
            try {
                const { getApiBase } = await import('../core/api.js');
                apiBase = getApiBase();
            } catch {
                const apiBaseMeta = document.querySelector('meta[name="nerava-api-base"]');
                apiBase = window.NERAVA_API_BASE || (apiBaseMeta && apiBaseMeta.content) || window.API_BASE_URL || '';
            }
            const configResponse = await fetch(`${apiBase}/v1/public/config`);
            if (configResponse.ok) {
                const config = await configResponse.json();
                const appleClientId = config.apple_client_id || '';
                
                const appleBtn = rootEl.querySelector('#btn-apple-login');
                if (!appleClientId && appleBtn) {
                    // Hide button if Apple not configured
                    appleBtn.style.display = 'none';
                    console.log('[Login] Apple Sign-In not configured - button hidden');
                } else if (appleClientId) {
                    console.log('[Login] Apple Sign-In configured');
                }
            }
        } catch (error) {
            console.warn('[Login] Error fetching config for Apple Sign-In:', error);
            // Hide button on error to be safe
            const appleBtn = rootEl.querySelector('#btn-apple-login');
            if (appleBtn) {
                appleBtn.style.display = 'none';
            }
        }
    }
    
    // Initialize Apple Sign-In check
    setTimeout(initAppleSignIn, 500);
    
    rootEl.querySelector('#btn-apple-login')?.addEventListener('click', async () => {
        try {
            hideError();
            // Apple Sign-In is intentionally disabled for launch
            // Backend endpoint exists but requires Apple Developer account configuration
            showError('Apple Sign-In is coming soon. Please use Phone OTP or Google Sign-In for now.');
        } catch (error) {
            console.error('[Login] Apple login error:', error);
            showError(error.message || 'Apple login failed');
        }
    });
    
    // Phone login - check for dev mode first
    const phoneBtn = rootEl.querySelector('#btn-phone-login');
    console.log('[Login] Phone button found:', phoneBtn);
    
    if (phoneBtn) {
        phoneBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('[Login] Phone login button clicked');
            
            // Check if we're in dev mode (DEMO_MODE, localhost, or S3 staging site)
            const hostname = window.location.hostname;
            const isS3StagingSite = hostname.includes('s3-website') ||
                                    hostname.includes('.s3.') ||
                                    hostname.includes('nerava-ui-prod');
            const isDevMode = window.NERAVA_DEMO_MODE === true ||
                              hostname === 'localhost' ||
                              hostname === '127.0.0.1' ||
                              isS3StagingSite;
            
            console.log('[Login] Dev mode check:', {
                NERAVA_DEMO_MODE: window.NERAVA_DEMO_MODE,
                hostname: hostname,
                isS3StagingSite: isS3StagingSite,
                isDevMode: isDevMode
            });
            
            if (isDevMode) {
            // Dev mode: auto-login as dev user
            try {
                hideError();
                const btn = rootEl.querySelector('#btn-phone-login');
                if (btn) {
                    btn.disabled = true;
                    btn.textContent = 'Logging in as dev user...';
                }
                
                console.log('[Login] Dev mode detected - auto-logging in as dev@nerava.local');
                
                // Call dev login endpoint
                const { apiDevLogin } = await import('../core/api.js');
                const response = await apiDevLogin();
                
                console.log('[Login] Dev login successful');
                
                // Store tokens
                setTokens(response.access_token, response.refresh_token);
                
                // Redirect to app
                window.location.hash = '#/wallet';
                window.location.reload();
            } catch (error) {
                console.error('[Login] Dev login failed:', error);
                // Fall back to normal phone OTP flow
                showError('Dev login failed, falling back to phone OTP');
                const btn = rootEl.querySelector('#btn-phone-login');
                if (btn) {
                    btn.disabled = false;
                    btn.textContent = 'Continue with Phone';
                }
                // Only show phone input step if button still exists and we're not already on it
                try {
                    showStep('phone');
                } catch (e) {
                    console.warn('[Login] Could not show phone input step:', e);
                }
            }
            } else {
                // Normal mode: show phone input
                console.log('[Login] Not in dev mode, showing phone input');
                showStep('phone');
            }
        });
    } else {
        console.error('[Login] Phone login button not found!');
    }
    
    // Back to provider selection
    rootEl.querySelector('#btn-back-provider')?.addEventListener('click', () => {
        showStep('provider');
    });
    
    rootEl.querySelector('#btn-back-phone')?.addEventListener('click', () => {
        showStep('phone');
    });
    
    // Request OTP
    rootEl.querySelector('#btn-request-otp')?.addEventListener('click', async () => {
        const phoneInput = rootEl.querySelector('#phone-input');
        const phone = phoneInput.value.trim();
        
        if (!phone) {
            showError('Please enter your phone number');
            return;
        }
        
        try {
            hideError();
            const btn = rootEl.querySelector('#btn-request-otp');
            btn.disabled = true;
            btn.textContent = 'Sending...';
            
            await apiOtpStart(phone);
            
            showStep('otp');
        } catch (error) {
            showError(error.message || 'Failed to send verification code');
        } finally {
            const btn = rootEl.querySelector('#btn-request-otp');
            btn.disabled = false;
            btn.textContent = 'Send Verification Code';
        }
    });
    
    // Verify OTP
    rootEl.querySelector('#btn-verify-otp')?.addEventListener('click', async () => {
        const phoneInput = rootEl.querySelector('#phone-input');
        const otpInput = rootEl.querySelector('#otp-input');
        const phone = phoneInput.value.trim();
        const code = otpInput.value.trim();
        
        if (!code || code.length !== 6) {
            showError('Please enter the 6-digit verification code');
            return;
        }
        
        try {
            hideError();
            const btn = rootEl.querySelector('#btn-verify-otp');
            btn.disabled = true;
            btn.textContent = 'Verifying...';
            
            const response = await apiOtpVerify(phone, code);
            
            // Store tokens
            setTokens(response.access_token, response.refresh_token);
            
            // Redirect to app
            window.location.hash = '#/wallet';
            window.location.reload();
        } catch (error) {
            showError(error.message || 'Invalid verification code');
        } finally {
            const btn = rootEl.querySelector('#btn-verify-otp');
            btn.disabled = false;
            btn.textContent = 'Verify Code';
        }
    });
}

