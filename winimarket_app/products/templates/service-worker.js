const CACHE_NAME = "winimarket-static-v1"

const STATIC_ASSET = [
    "/",
    "/offline/",
    "/static/css/main/index.css",
    "/static/js_files/main/index.js",
    "/static/pwa/manifest.json"
]

//INSTALL
self.addEventListener("install", event=> {
    event.waitUntil((async ()=> {
        const cache = await caches.open(CACHE_NAME)
        await cache.addAll(STATIC_ASSET)
        self.skipWaiting()
    })())
})

//ACTIVATE
self.addEventListener("activate", event=> {
    event.waitUntil((async ()=> {
        const keys = await caches.keys()
        await Promise.all(
            keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
        )

        self.clients.claim()
    })())
})

//FETCH (SAFE BASE)
self.addEventListener("fetch", event => {
    const url = new URL(event.request.url)

    if (event.request.method !== "GET" || (url.protocol !== "http" && url.protocol !== "https")){
        return;
    }

    if (
        url.pathname.startsWith("/products") ||
        url.pathname.startsWith("/categories")
    ) {
        event.respondWith(networkFirst(event.request));
        return;
    }

     // Static assets
    if (url.pathname.startsWith("/static/")) {
        event.respondWith(cacheFirst(event.request));
        return;
    }

    // Default: page navigation
    event.respondWith(pageFallback(event.request));
})

/* ---------- STRATEGIES ---------- */

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    const cache = await caches.open(CACHE_NAME);
    cache.put(request, response.clone());
    return response;
  } catch {
    const cached = await caches.match(request);
    return cached || caches.match("/offline/");
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  const response = await fetch(request);
  const cache = await caches.open(CACHE_NAME);
  cache.put(request, response.clone());
  return response;
}

async function pageFallback(request) {
  try {
    const response = await fetch(request);
    return response;
  } catch {
    return caches.match("/offline/");
  }
}

//PUSH NOTIFICATION
self.addEventListener("push", event => {
    const data = event.data ? event.data.json() : {};

    const options = {
        body: data.body,
        icon: "/static/pwa/icons/android-chrome-192x192.png",
        badge: "/static/pwa/android-chrome-512x512.png",
        data: {
            url: data.url || "/"
        }
    };

    event.waitUntil(
        self.registration.showNotification(data.title || "Winimarket", options)
    );
});

self.addEventListener("notificationclick", event => {
    event.notification.close();

    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});
