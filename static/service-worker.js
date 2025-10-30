self.addEventListener('install', event => {
  event.waitUntil(
    caches.open('ai-resume-parser-v1').then(cache => {
      return cache.addAll(['/', '/manifest.json', '/app-icon.png']);
    })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});
