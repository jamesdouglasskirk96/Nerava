/**
 * Auth utilities for token storage and refresh
 */
const AUTH_STORAGE_KEYS = {
    ACCESS_TOKEN: 'access_token',
    REFRESH_TOKEN: 'refresh_token'
};

/**
 * Get stored access token
 */
export function getAccessToken() {
    return localStorage.getItem(AUTH_STORAGE_KEYS.ACCESS_TOKEN);
}

/**
 * Get stored refresh token
 */
export function getRefreshToken() {
    return localStorage.getItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN);
}

/**
 * Store tokens in localStorage
 */
export function setTokens(accessToken, refreshToken) {
    localStorage.setItem(AUTH_STORAGE_KEYS.ACCESS_TOKEN, accessToken);
    localStorage.setItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
}

/**
 * Clear tokens from localStorage
 */
export function clearTokens() {
    localStorage.removeItem(AUTH_STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN);
    // Also clear legacy user storage
    localStorage.removeItem('NERAVA_USER');
    localStorage.removeItem('NERAVA_USER_ID');
    if (typeof window !== 'undefined') {
        window.NERAVA_USER = null;
    }
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated() {
    return !!getAccessToken();
}

/**
 * Refresh access token using refresh token
 * Returns new access token or null if refresh fails
 */
export async function refreshAccessToken() {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
        return null;
    }
    
    try {
        const { apiRefresh } = await import('./api.js');
        const response = await apiRefresh(refreshToken);
        
        if (response.access_token && response.refresh_token) {
            setTokens(response.access_token, response.refresh_token);
            return response.access_token;
        }
        
        return null;
    } catch (error) {
        console.error('[Auth] Refresh token failed:', error);
        
        // If refresh_reuse_detected, clear tokens and force re-login
        if (error.message && error.message.includes('refresh_reuse_detected')) {
            clearTokens();
        }
        
        return null;
    }
}






