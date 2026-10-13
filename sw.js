/* Dateline Atlas service worker: keeps the app usable offline and the news feed fresh.
   App files: served from cache, refreshed in the background (new versions show on next launch).
   News feed: network first, falling back to the last saved sweep when offline. */
const SHELL_CACHE = "atlas-shell-v1";
const DATA_CACHE = "atlas-data";
const FONT_CACHE = "atlas-fonts";
const SHELL = [
  "./",
  "index.html",
  "manifest.webmanifest",
  "lib/d3.min.js",
  "earth-relief-2k.jpg",
  "icons/icon-192.png",
  "icons/icon-512.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(SHELL_CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  const keep = new Set([SHELL_CACHE, DATA_CACHE, FONT_CACHE]);
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => !keep.has(k)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  // news feed: always try the network; offline, answer from the last saved copy and say so
  if (url.origin === self.location.origin && url.pathname.endsWith("/data/feed.json")) {
    event.respondWith((async () => {
      const cache = await caches.open(DATA_CACHE);
      const key = new Request(url.origin + url.pathname);
      try {
        const res = await fetch(req);
        if (res.ok) await cache.put(key, res.clone());
        return res;
      } catch (err) {
        const hit = await cache.match(key);
        if (!hit) throw err;
        const headers = new Headers(hit.headers);
        headers.set("x-atlas-offline", "1");
        return new Response(await hit.blob(), { status: 200, headers });
      }
    })());
    return;
  }

  // Google Fonts: cache once, reuse forever
  if (url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com") {
    event.respondWith((async () => {
      const cache = await caches.open(FONT_CACHE);
      const hit = await cache.match(req);
      if (hit) return hit;
      const res = await fetch(req);
      if (res.ok || res.type === "opaque") cache.put(req, res.clone());
      return res;
    })());
    return;
  }

  // app files: cache first, refresh in the background
  if (url.origin === self.location.origin) {
    event.respondWith((async () => {
      const cache = await caches.open(SHELL_CACHE);
      const hit = (await cache.match(req, { ignoreSearch: true })) ||
        (req.mode === "navigate" ? await cache.match("index.html") : undefined);
      const fresh = fetch(req).then((res) => {
        if (res.ok) cache.put(req, res.clone());
        return res;
      }).catch(() => undefined);
      if (hit) { event.waitUntil(fresh); return hit; }
      return (await fresh) || Response.error();
    })());
  }
});
