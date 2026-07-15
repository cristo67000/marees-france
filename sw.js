/* Service worker — cache-first : l'app fonctionne entièrement hors-ligne. */
importScripts("./js/phares_extra.js"); // fournit PHARES_EXTRA (photos)
const CACHE = "marees-france-v6";
const PHOTOS = Object.values(PHARES_EXTRA)
  .map((x) => x.img && "./" + x.img).filter(Boolean);
const ASSETS = [
  ...PHOTOS,
  "./", "./index.html", "./manifest.webmanifest",
  "./css/app.css", "./lib/leaflet.css", "./lib/leaflet.js",
  "./js/tide.js", "./js/moon.js", "./js/astro.js", "./js/portinfo.js",
  "./js/phares.js", "./js/phares_extra.js", "./js/labels.js", "./js/app.js",
  "./data/rivers.json",
  "./data/ports.json", "./data/france.geojson",
  "./icons/icon.svg", "./icons/icon-192.png", "./icons/icon-512.png",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) =>
    Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
  ).then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then((hit) =>
      hit || fetch(e.request).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
        return res;
      })
    )
  );
});
