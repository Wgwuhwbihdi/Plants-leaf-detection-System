// Service Worker for Phyto Lab PWA
const CACHE_NAME = 'phyto lab-v1';
const STATIC_CACHE = 'phyto lab-static-v1';
const DYNAMIC_CACHE = 'phyto lab-dynamic-v1';

// Assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/about',
  '/help',
  '/history',
  '/settings',
  '/static/css/bootstrap.min.css',
  '/static/css/style.css',
  '/static/js/bootstrap.bundle.min.js',
  '/static/js/app.js',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/offline'
];

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('Service Worker: Installing');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .catch(error => {
        console.log('Service Worker: Caching failed', error);
      })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker: Activating');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
            console.log('Service Worker: Deleting old cache', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip external requests
  if (!url.origin.includes(self.location.origin)) return;

  // Handle upload/prediction requests differently
  if (url.pathname.startsWith('/upload/') || url.pathname.startsWith('/batch-upload/')) {
    // For prediction requests, try network first, fallback to offline page
    event.respondWith(
      fetch(request)
        .catch(() => {
          return caches.match('/offline');
        })
    );
    return;
  }

  // For static assets, cache-first strategy
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request)
        .then(response => {
          if (response) {
            return response;
          }
          return fetch(request)
            .then(response => {
              // Cache successful responses
              if (response.status === 200) {
                const responseClone = response.clone();
                caches.open(STATIC_CACHE)
                  .then(cache => cache.put(request, responseClone));
              }
              return response;
            });
        })
    );
    return;
  }

  // For pages, network-first with cache fallback
  event.respondWith(
    fetch(request)
      .then(response => {
        // Cache successful HTML responses
        const acceptsHtml = (request.headers.get('accept') || '').includes('text/html');
        if (response.status === 200 && acceptsHtml) {
          const responseClone = response.clone();
          caches.open(DYNAMIC_CACHE)
            .then(cache => cache.put(request, responseClone));
        }
        return response;
      })
      .catch(() => {
        return caches.match(request)
          .then(response => {
            if (response) {
              return response;
            }
            // Return offline page for HTML requests
            const acceptsHtml = (request.headers.get('accept') || '').includes('text/html');
            if (acceptsHtml) {
              return caches.match('/offline');
            }
          });
      })
  );
});

// Background sync for when connection is restored
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

async function doBackgroundSync() {
  // Implement background sync logic if needed
  console.log('Background sync triggered');
}
