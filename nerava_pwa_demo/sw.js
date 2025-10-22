self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('nerava-v1').then(cache => {
      return cache.addAll(['/', '/index.html', '/styles.css', '/app.js']);
    })
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(caches.match(e.request).then(resp => resp || fetch(e.request)));
});
