const CACHE_NAME = "winimarket-static-v1"

const STATIC_ASSET = [
    "/",
    "/offline/",
    "/static/css/main/index.css",
    "/static/css/js_files/index.js",
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
    if (event.request.method !== "GET") return;

    event.respondWith((async () => {
        const cached = await caches.match(event.request)
        if (cached) return cached;

        try{
            const response = await fetch(event.request)
            const cache = await caches.open(CACHE_NAME)
            cache.put(event.request, response.clone())
            return response
        } catch(err){
            return caches.match('/offline/')
        }
    })())
})