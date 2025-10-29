// Service Worker for Nerava PWA
const CACHE_VERSION = 'v1.0.1';
const CACHE_NAME = `nerava-${CACHE_VERSION}`;
const OFFLINE_URL = './offline.html';

// Install event: cache essential files
self.addEventListener('install', (event) => {
    console.log('Service Worker: Installing...', CACHE_VERSION);
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('Service Worker: Caching essential files');
            return cache.addAll([
                './',
                './index.html',
                './css/tokens.css',
                './css/style.css',
                './js/app.js',
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
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip API requests (always go to network)
    if (request.url.includes('/v1/')) {
        return;
    }
    
    event.respondWith(
        fetch(request)
            .then((response) => {
                // Cache successful responses
                if (response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, responseClone);
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
