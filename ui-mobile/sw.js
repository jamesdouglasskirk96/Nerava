// Service Worker for Nerava PWA
const CACHE_VERSION = 'v9'; // Updated to force refresh after removing "Found closest" toast
const CACHE_NAME = `nerava-${CACHE_VERSION}`;
const OFFLINE_URL = './offline.html';

// Install event: cache essential files
self.addEventListener('install', (event) => {
    console.log('Service Worker: Installing...', CACHE_VERSION);
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('Service Worker: Caching essential files');
            // Don't cache JS files - always fetch fresh to avoid stale code
            return cache.addAll([
                './',
                './index.html',
                './css/tokens.css',
                './css/style.css',
                // JS files are NOT cached - always fetch from network
                './offline.html'
            ]).catch(err => {
                console.warn('Service Worker: Some files failed to cache:', err);
            });
        })
    );
    // Force activate immediately to take control
    self.skipWaiting();
});

// Activate event: clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker: Activating...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Service Worker: Deleting old cache', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            // Take control of all pages immediately
            return self.clients.claim();
        })
    );
});

// Fetch event: network-first strategy with offline fallback
self.addEventListener('fetch', (event) => {
    const { request } = event;
    
    // Extract URL and check protocol - do this FIRST before any processing
    let url;
    try {
        url = new URL(request.url);
    } catch (e) {
        // Invalid URL - don't handle
        return;
    }
    
    // Ignore browser extension, about:, file:, and other unsupported schemes
    if (url.protocol !== 'http:' && url.protocol !== 'https:') {
        return; // do not intercept or cache these requests
    }
    
    // Skip non-GET requests (always go to network)
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip API requests (always go to network, don't cache)
    if (request.url.includes('/v1/')) {
        return; // Let the request pass through to network without service worker intervention
    }
    
    // Skip JavaScript files - always fetch fresh to avoid stale code
    if (request.url.endsWith('.js') || request.url.includes('/js/')) {
        return; // Don't cache JS files - always go to network
    }
    
    // Continue with existing caching logic
    event.respondWith(
        fetch(request)
            .then((response) => {
                // Only cache successful GET responses (200-299 status codes)
                // NEVER cache error responses (4xx, 5xx) - they might be temporary backend issues
                if (response.status >= 200 && response.status < 300 && request.method === 'GET') {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, responseClone).catch(err => {
                            console.warn('Service Worker: Failed to cache', request.url, err);
                        });
                    });
                } else if (response.status >= 400) {
                    // For 404s on assets, return without logging (not an error)
                    if (response.status === 404 && request.url.includes('/assets/')) {
                        return response; // Don't log or cache 404s
                    }
                    // For error responses, try to get from cache if available, but don't cache the error
                    console.warn('Service Worker: Error response', response.status, 'for', request.url);
                    return caches.match(request).then(async (cachedResponse) => {
                        // If we have a cached version, use it instead of the error
                        if (cachedResponse && cachedResponse.status < 400) {
                            console.log('Service Worker: Using cached version instead of error response');
                            return cachedResponse;
                        }
                        // For 500 errors on static assets, delete from cache and retry once
                        if (response.status === 500 && (request.url.includes('/app/') || request.url.includes('/static/'))) {
                            console.log('Service Worker: 500 error on static file, deleting from cache and retrying');
                            const cache = await caches.open(CACHE_NAME);
                            await cache.delete(request).catch(() => {});
                            // Retry the request once
                            try {
                                const retryResponse = await fetch(request);
                                if (retryResponse.status < 400) {
                                    console.log('Service Worker: Retry succeeded, returning successful response');
                                    return retryResponse;
                                }
                            } catch (retryError) {
                                console.warn('Service Worker: Retry failed:', retryError);
                            }
                        }
                        // Otherwise, return the error response (don't cache it)
                        return response;
                    });
                }
                return response;
            })
            .catch((error) => {
                // Network error: return cached version or offline page
                console.warn('Service Worker: Network error for', request.url, error);
                return caches.match(request).then((cachedResponse) => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    // For navigation requests, return offline page
                    if (request.mode === 'navigate') {
                        return caches.match(OFFLINE_URL).then((offlinePage) => {
                            if (offlinePage) {
                                return offlinePage;
                            }
                            // Fallback: return basic offline response
                            return new Response('You are offline', {
                                headers: { 'Content-Type': 'text/html' },
                                status: 503
                            });
                        });
                    }
                    // For other requests, return a basic response
                    return new Response('Offline', { status: 503 });
                });
            })
    );
});
