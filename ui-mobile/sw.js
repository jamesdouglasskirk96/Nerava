// Service Worker for Nerava PWA
const CACHE_VERSION = 'v1.0.3';
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
    
    // Skip chrome-extension:// and other unsupported schemes - do this FIRST before any URL parsing
    try {
        const url = new URL(request.url);
        
        // Skip unsupported schemes immediately - don't even try to handle them
        if (url.protocol === 'chrome-extension:' || 
            url.protocol === 'moz-extension:' || 
            url.protocol === 'chrome-search:' ||
            url.protocol === 'chrome:' ||
            !url.protocol.startsWith('http')) {
            // Silently ignore - don't handle these requests at all
            return;
        }
        
        // Skip non-GET requests (always go to network)
        if (request.method !== 'GET') {
            return;
        }
        
        // Skip API requests (always go to network, don't cache)
        if (request.url.includes('/v1/')) {
            // Let the request pass through to network without service worker intervention
            return;
        }
        
        // Skip JavaScript files - always fetch fresh to avoid stale code
        if (request.url.endsWith('.js') || request.url.includes('/js/')) {
            // Don't cache JS files - always go to network
            return;
        }
        
        // Only process http/https requests
        if (url.protocol !== 'http:' && url.protocol !== 'https:') {
            return;
        }
        
        event.respondWith(
            fetch(request)
                .then((response) => {
                    // Only cache successful http/https responses
                    if (response.status === 200 && 
                        !request.url.endsWith('.js') && 
                        !request.url.includes('/js/') &&
                        (url.protocol === 'http:' || url.protocol === 'https:')) {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            // Final safety check before caching
                            try {
                                const checkUrl = new URL(request.url);
                                if (checkUrl.protocol === 'http:' || checkUrl.protocol === 'https:') {
                                    cache.put(request, responseClone).catch(err => {
                                        // Silently ignore caching errors for unsupported schemes
                                        if (!err.message.includes('chrome-extension')) {
                                            console.warn('Service Worker: Failed to cache', request.url, err);
                                        }
                                    });
                                }
                            } catch (e) {
                                // Ignore URL parsing errors
                            }
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
    } catch (error) {
        // If URL parsing fails (e.g., for chrome-extension://), silently ignore
        return;
    }
});
