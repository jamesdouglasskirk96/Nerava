// Service Worker for Nerava PWA
const CACHE_VERSION = 'v5';
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
                // Only cache successful GET responses
                if (response.status === 200 && request.method === 'GET') {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, responseClone).catch(err => {
                            console.warn('Service Worker: Failed to cache', request.url, err);
                        });
                    });
                }
                return response;
            })
            .catch(() => {
                // Offline: return cached version or offline page
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
