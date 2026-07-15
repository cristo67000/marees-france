/* Marées France — interface. */
"use strict";

(async function () {
  // --- chargement des données (inlinées en version 1 fichier, sinon fetch) ---
  const ports = window.PORTS_DATA ||
    await (await fetch("data/ports.json")).json();
  const france = window.FRANCE_GEOJSON ||
    await (await fetch("data/france.geojson")).json();
  const rivers = window.RIVERS_DATA ||
    await (await fetch("data/rivers.json")).json();
  Tide.init(ports);

  const $ = (s) => document.querySelector(s);
  const fmtH = (ms) => new Date(ms).toLocaleTimeString("fr-FR",
    { hour: "2-digit", minute: "2-digit" });
  const fmtDay = (ms) => new Date(ms).toLocaleDateString("fr-FR",
    { weekday: "short", day: "numeric" });
  const fmtM = (v) => v.toLocaleString("fr-FR",
    { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " m";

  function fmtDelta(ms) {
    const m = Math.max(0, Math.round(ms / 60000));
    const h = Math.floor(m / 60), mm = m % 60;
    return h > 0 ? `${h} h ${String(mm).padStart(2, "0")}` : `${mm} min`;
  }

  function dms(v, pos, neg) {
    const d = Math.floor(Math.abs(v)), m = Math.round((Math.abs(v) - d) * 60);
    return `${d}°${String(m).padStart(2, "0")}′ ${v >= 0 ? pos : neg}`;
  }

  function coefClass(c) {
    return c >= 95 ? "c-ve2" : c >= 70 ? "c-ve" : c >= 45 ? "c-mid" : "c-me";
  }

  // niveaux d'affichage des ports selon le zoom
  const TIER0 = new Set(["boulogne", "le-havre", "saint-malo",
    "brest", "saint-nazaire", "la-rochelle", "arcachon",
    "saint-jean-de-luz", "marseille", "nice"]);
  const TIER1 = new Set(["dunkerque", "dieppe", "cherbourg", "granville",
    "roscoff", "lorient", "les-sables", "royan", "sete", "toulon",
    "ajaccio", "bastia"]);
  const tier = (p) => TIER0.has(p.id) ? 0 : TIER1.has(p.id) ? 1 : 2;

  // --- carte ---
  const map = L.map("map", {
    zoomControl: false, attributionControl: false,
    minZoom: 5, maxZoom: 11, zoomSnap: 0.25,
    maxBounds: [[39.5, -9.5], [53.5, 13.5]], maxBoundsViscosity: 0.7,
  });
  L.geoJSON(france, { style: { className: "france-shape", stroke: true,
    weight: 1.2, fill: true, fillOpacity: 1 } }).addTo(map);
  function fitFrance() {
    map.invalidateSize();
    map.fitBounds([[42.2, -5.2], [51.2, 8.4]], { padding: [4, 4] });
  }
  fitFrance();
  // Le conteneur peut être (re)dimensionné après l'init (onglet en arrière-plan,
  // rotation, barre d'adresse mobile). On ne recadre la France que si la taille
  // change fortement ; sinon simple invalidateSize pour préserver la vue.
  // --- habillage : fleuves, mers, côtes, villes ---
  map.createPane("labels");
  map.getPane("labels").style.zIndex = 590;      // sous les marqueurs (600)
  map.getPane("labels").style.pointerEvents = "none";
  const riverStyle = { className: "river-line", weight: 1.6, opacity: 0.85,
    color: "#4a86c2", interactive: false };
  for (const segs of Object.values(rivers))
    for (const seg of segs) L.polyline(seg, riverStyle).addTo(map);

  const labelMarkers = []; // étiquettes fixes {m, minZ, maxZ}
  function addLabel(cls, name, lat, lon, minZ, maxZ) {
    const m = L.marker([lat, lon], { pane: "labels", interactive: false,
      keyboard: false,
      icon: L.divIcon({ className: "lbl-wrap",
        html: `<div class="${cls}">${name}</div>`, iconSize: [0, 0] }) });
    labelMarkers.push({ m, minZ, maxZ: maxZ || 99 });
  }
  if (typeof MAP_LABELS !== "undefined") {
    MAP_LABELS.seas.forEach(s => addLabel("sea-lbl", s.name, s.lat, s.lon, s.minZ, s.maxZ));
    MAP_LABELS.coasts.forEach(c => addLabel("coast-lbl", c.name, c.lat, c.lon, 6.2));
    MAP_LABELS.rivers.forEach(r => addLabel("river-lbl", r.name, r.lat, r.lon, 6.2));
  }
  function updateLabels() {
    const z = map.getZoom() ?? 5;
    for (const { m, minZ, maxZ } of labelMarkers) {
      const show = z >= minZ && z < maxZ;
      if (show && !map.hasLayer(m)) m.addTo(map);
      else if (!show && map.hasLayer(m)) m.remove();
    }
  }

  // villes côtières : point + nom, soumis à l'écrémage (priorité aux ports).
  // L'étiquette essaie sous le point, sinon au-dessus.
  const cityMarkers = [];
  function cityIcon(c, dy) {
    const dx = c.dx || 0;
    return L.divIcon({ className: "lbl-wrap", html:
      `<div class="city-wrap">${c.dot ? '<div class="city-dot"></div>' : ""}` +
      `<div class="city-txt" style="transform:translate(calc(-50% + ${dx}px),${dy}px)">${c.name}</div></div>`,
      iconSize: [0, 0] });
  }
  if (typeof MAP_LABELS !== "undefined") {
    for (const c of MAP_LABELS.cities) {
      // ville portuaire : s'accroche aux coordonnées exactes du port
      for (const p of Tide.ports)
        if (Math.abs(p.lat - c.lat) < 0.05 && Math.abs(p.lon - c.lon) < 0.06) {
          c.lat = p.lat; c.lon = p.lon; c.onPort = true; break;
        }
      const m = L.marker([c.lat, c.lon], { pane: "labels", interactive: false,
        keyboard: false, icon: cityIcon(c, c.dot ? 4 : 18) });
      m._dy = null;
      cityMarkers.push({ c, m });
    }
  }

  let lastW = 0, lastH = 0, rszT;
  new ResizeObserver((entries) => {
    const { width: w, height: h } = entries[0].contentRect;
    if (w === 0 || h === 0) return;
    const big = lastW === 0 || Math.abs(w - lastW) / lastW > 0.3 ||
                Math.abs(h - lastH) / lastH > 0.3;
    lastW = w; lastH = h;
    clearTimeout(rszT);
    rszT = setTimeout(big ? fitFrance : () => map.invalidateSize(), 120);
  }).observe(document.getElementById("map"));

  // --- marqueurs ---
  const markers = new Map(); // id -> L.marker
  function badgeHtml(p, compact) {
    const st = Tide.state(p, Date.now());
    if (!st.next) return "";
    const dir = st.rising ? "up" : "down";
    const arrow = st.rising ? "▲" : "▼";
    if (compact) {
      return `<div class="dot-hit"><div class="dot b-${dir}" data-id="${p.id}">
        <span class="b-arrow">${arrow}</span></div></div>`;
    }
    return `<div class="badge b-${dir}" data-id="${p.id}">
      <span class="b-arrow">${arrow}</span>
      <span class="b-time">${st.next.type} ${fmtH(Tide.toMs(st.next.t))}</span>
    </div>`;
  }
  function makeIcon(p, compact) {
    return compact
      ? L.divIcon({ className: "badge-wrap", html: badgeHtml(p, true),
          iconSize: [40, 40], iconAnchor: [20, 20] })
      : L.divIcon({ className: "badge-wrap", html: badgeHtml(p, false),
          iconSize: null, iconAnchor: [8, 8] });
  }
  for (const p of Tide.ports) {
    const m = L.marker([p.lat, p.lon], { icon: makeIcon(p, true),
      keyboard: false });
    m.on("click", () => openSheet(p.id));
    markers.set(p.id, m);
  }
  // --- bascule de la couche ports ---
  let portsOn = localStorage.getItem("portsOn") !== "0";
  $("#port-btn").addEventListener("click", () => {
    portsOn = !portsOn;
    localStorage.setItem("portsOn", portsOn ? "1" : "0");
    $("#port-btn").setAttribute("aria-pressed", String(portsOn));
    $("#port-btn").classList.toggle("off", !portsOn);
    refreshMarkers();
    if (!portsOn) closeSheet();
  });
  $("#port-btn").classList.toggle("off", !portsOn);

  // --- phares ---
  let pharesOn = localStorage.getItem("pharesOn") !== "0";
  const phareMarkers = new Map(); // id -> L.marker
  const PHARE_SVG = `<svg viewBox="0 0 24 24" width="24" height="24">
    <g class="ph-rays"><path d="M7 6.4 3.6 5.1M17 6.4l3.4-1.3"/></g>
    <path class="ph-tower" d="M9.7 8.8h4.6l1.7 11.4H8z"/>
    <rect class="ph-lamp" x="9.3" y="4.9" width="5.4" height="3.9" rx="0.9"/>
    <g class="ph-bands"><path d="M9.35 12.4h5.3M8.85 15.9h6.3"/></g>
  </svg>`;
  for (const f of (typeof PHARES !== "undefined" ? PHARES : [])) {
    const m = L.marker([f.lat, f.lon], {
      icon: L.divIcon({ className: "badge-wrap", html:
        `<div class="ph-hit" data-id="${f.id}">${PHARE_SVG}</div>`,
        iconSize: [36, 36], iconAnchor: [18, 22] }),
      keyboard: false, zIndexOffset: -100,
    });
    m.on("click", () => openPhare(f.id));
    phareMarkers.set(f.id, m);
  }
  $("#phare-btn").addEventListener("click", () => {
    pharesOn = !pharesOn;
    localStorage.setItem("pharesOn", pharesOn ? "1" : "0");
    $("#phare-btn").setAttribute("aria-pressed", String(pharesOn));
    $("#phare-btn").classList.toggle("off", !pharesOn);
    refreshMarkers();
    if (!pharesOn) closePhare();
  });
  $("#phare-btn").classList.toggle("off", !pharesOn);

  /* Affichage adaptatif : par ordre de priorité, chaque port tente son badge
     complet (horaire), sinon une pastille, sinon rien — sans chevauchement.
     Les phares se placent ensuite dans l'espace restant. */
  const BADGE_W = 88, BADGE_H = 28, DOT_S = 28, PH_S = 30, MARGIN = 2;
  function refreshMarkers() {
    const z = map.getZoom() ?? 5;
    const maxTier = z >= 7.5 ? 2 : z >= 6.4 ? 1 : 0;
    const forceDots = z < 6.4;
    const cand = (portsOn ? Tide.ports.filter(p => tier(p) <= maxTier) : [])
      .sort((a, b) => tier(a) - tier(b));
    const kept = [];
    const fits = (b) => kept.every(k =>
      b.x + b.w + MARGIN <= k.x || k.x + k.w + MARGIN <= b.x ||
      b.y + b.h + MARGIN <= k.y || k.y + k.h + MARGIN <= b.y);
    const plan = new Map(); // id -> "full" | "dot" | null
    for (const p of cand) {
      const pt = map.latLngToContainerPoint([p.lat, p.lon]);
      const full = { x: pt.x - 12, y: pt.y - 12, w: BADGE_W, h: BADGE_H };
      const dot = { x: pt.x - DOT_S / 2, y: pt.y - DOT_S / 2, w: DOT_S, h: DOT_S };
      if (!forceDots && fits(full)) { plan.set(p.id, "full"); kept.push(full); }
      else if (fits(dot)) { plan.set(p.id, "dot"); kept.push(dot); }
      else plan.set(p.id, null);
    }
    for (const p of Tide.ports) {
      const m = markers.get(p.id);
      const mode = plan.get(p.id) || null;
      if (mode) {
        m.setIcon(makeIcon(p, mode === "dot"));
        if (!map.hasLayer(m)) m.addTo(map);
      } else if (map.hasLayer(m)) m.remove();
    }
    // villes côtières : après les ports, avant les phares
    for (const { c, m } of cityMarkers) {
      let show = c.tier === 0 ? true : z >= 6.4;
      if (show) {
        const pt = map.latLngToContainerPoint([c.lat, c.lon]);
        const w = c.name.length * 6.6 + 8;
        const dyBelow = c.onPort ? 18 : 4;
        const dyAbove = c.onPort ? -32 : -20;
        let placed = null;
        for (const dy of [dyBelow, dyAbove]) {
          const box = { x: pt.x - w / 2 + (c.dx || 0), y: pt.y + dy - 2, w, h: 16 };
          if (fits(box)) { kept.push(box); placed = dy; break; }
        }
        if (placed !== null) {
          if (m._dy !== placed) { m.setIcon(cityIcon(c, placed)); m._dy = placed; }
        } else show = false;
      }
      if (show && !map.hasLayer(m)) m.addTo(map);
      else if (!show && map.hasLayer(m)) m.remove();
    }

    // phares : après les ports et les villes, dans l'espace libre
    const maxRank = z >= 7.5 ? 2 : z >= 6.4 ? 1 : 0;
    const phS = forceDots ? 20 : PH_S; // boîte plus tolérante en vue nationale
    const pharesByRank = (typeof PHARES !== "undefined" ? [...PHARES] : [])
      .sort((a, b) => a.rank - b.rank);
    const showPh = new Set();
    for (const f of pharesByRank) {
      if (!pharesOn || f.rank > maxRank) continue;
      const pt = map.latLngToContainerPoint([f.lat, f.lon]);
      const box = { x: pt.x - phS / 2, y: pt.y - phS / 2, w: phS, h: phS };
      if (fits(box)) { kept.push(box); showPh.add(f.id); }
    }
    for (const [id, m] of phareMarkers) {
      if (showPh.has(id)) { if (!map.hasLayer(m)) m.addTo(map); }
      else if (map.hasLayer(m)) m.remove();
    }
    updateLabels();
  }
  map.on("zoomend", refreshMarkers);
  refreshMarkers();
  window._map = map; window._tide = Tide; // débogage console

  // --- entête : horloge, lune, coefficient ---
  function refreshHeader() {
    const now = Date.now();
    $("#clock").textContent = new Date(now).toLocaleTimeString("fr-FR",
      { hour: "2-digit", minute: "2-digit" });
    $("#date").textContent = new Date(now).toLocaleDateString("fr-FR",
      { weekday: "long", day: "numeric", month: "long" });
    const ph = Moon.phase(now);
    $("#moon-icon").innerHTML = Moon.svg(ph.D, 30);
    $("#moon-name").textContent = ph.name;
    $("#moon-pct").textContent = Math.round(ph.illum * 100) + " %";
    const d0 = new Date(now); d0.setHours(0, 0, 0, 0);
    const coefs = Tide.dayCoefficients(d0.getTime(), d0.getTime() + 86400000);
    const el = $("#coef-vals");
    el.innerHTML = coefs.map(c =>
      `<span class="coef ${coefClass(c.coef)}">${c.coef}</span>`).join("");
    $("#coef-label").textContent = coefs.length > 1 ? "Coefs" : "Coef";
  }

  // --- fiche port (bottom sheet) ---
  let openPortId = null;
  let lastPortId = null;
  const sheet = $("#sheet");

  function openSheet(id) {
    closeCal(); closePhare();
    openPortId = lastPortId = id;
    // module « À propos » replié à chaque ouverture
    $("#about-body").hidden = true;
    $("#about-head").setAttribute("aria-expanded", "false");
    renderSheet();
    sheet.classList.add("open");
    document.body.classList.add("sheet-open");
  }
  function closeSheet() {
    openPortId = null;
    sheet.classList.remove("open");
    document.body.classList.remove("sheet-open");
  }
  $("#sheet-close").addEventListener("click", closeSheet);
  map.on("click", () => { closeSheet(); closeCal(); closePhare(); });
  $("#about-head").addEventListener("click", () => {
    const body = $("#about-body");
    body.hidden = !body.hidden;
    $("#about-head").setAttribute("aria-expanded", String(!body.hidden));
  });

  // --- fiche phare ---
  let openPhareId = null;
  let sigTimer = null;

  /* Animation du feu : construit les intervalles « allumé » sur une période,
     puis les rejoue en boucle à la vraie cadence. */
  function sigIntervals(sig) {
    const p = sig.period;
    if (sig.mode === "fixe") return [[0, p]];
    if (sig.mode === "iso") return [[0, p / 2]];
    const F = 0.5, G = 0.9, GRP = 1.6; // éclat, espace, espace inter-groupe
    const marks = [];
    let t = 0.4;
    for (let i = 0; i < sig.n; i++) { marks.push([t, t + F]); t += F + G; }
    if (sig.n2) {
      t += GRP - G;
      for (let i = 0; i < sig.n2; i++) { marks.push([t, t + F]); t += F + G; }
    }
    if (t > p) { // compresse si la période est courte
      const k = (p - 0.4) / t;
      marks.forEach(m => { m[0] *= k; m[1] *= k; });
    }
    if (sig.mode === "occ") { // occultations : l'inverse (noir aux marques)
      const on = []; let prev = 0;
      for (const [a, b] of marks) { if (a > prev) on.push([prev, a]); prev = b; }
      if (prev < p) on.push([prev, p]);
      return on;
    }
    return marks;
  }

  function startSignal(sig, rawTxt) {
    stopSignal();
    const box = $("#phare-signal");
    box.hidden = false;
    const colors = { blanc: "#ffedb0", rouge: "#ff6a5a", vert: "#5ce08d" };
    const c = colors[sig.color] || colors.blanc;
    box.style.setProperty("--sig-c", c);
    $(".sig-caption").textContent =
      (rawTxt || "") + ` — période ${String(sig.period).replace(".", ",")} s`;
    const on = sigIntervals(sig);
    const lamp = $(".sig-lamp"), scene = $(".sig-scene");
    const loop = () => {
      const t = (Date.now() / 1000) % sig.period;
      const lit = on.some(([a, b]) => t >= a && t < b);
      lamp.classList.toggle("on", lit);
      scene.classList.toggle("on", lit);
      sigTimer = requestAnimationFrame(loop);
    };
    sigTimer = requestAnimationFrame(loop);
  }
  function stopSignal() {
    if (sigTimer) { cancelAnimationFrame(sigTimer); sigTimer = null; }
    $("#phare-signal").hidden = true;
  }

  function openPhare(id) {
    const f = PHARES.find(x => x.id === id);
    if (!f) return;
    closeSheet(); closeCal();
    openPhareId = id;
    const X = (typeof PHARES_EXTRA !== "undefined" && PHARES_EXTRA[id]) || {};
    $("#phare-name").textContent = f.name;
    $("#phare-loc").textContent =
      `${f.dep} · ${dms(f.lat, "N", "S")} · ${dms(f.lon, "E", "O")}`;

    // photo (toucher = agrandir)
    const photo = $("#phare-photo");
    if (X.img) {
      photo.hidden = false;
      photo.classList.remove("big");
      photo.innerHTML = `<img src="${X.img}" alt="${f.name}">
        <span class="ph-credit">Photo : ${X.credit || "Wikimedia Commons"}</span>`;
      photo.onclick = () => photo.classList.toggle("big");
    } else { photo.hidden = true; photo.innerHTML = ""; }

    // signal lumineux animé
    if (X.sig) startSignal(X.sig, X.feux); else stopSignal();

    // chips : hauteur, marches, portée, année, mer/terre
    const chips = [];
    const hM = X.hauteur && X.hauteur.match(/\d+[.,]?\d*\s*m/);
    if (hM) chips.push(hM[0].replace(".", ","));
    else if (f.h) chips.push(`${String(f.h).replace(".", ",")} m`);
    if (X.marches) chips.push(`${X.marches} marches`);
    const pM = X.portee && X.portee.match(/\d+[.,]?\d*\s*milles?/);
    if (pM) chips.push(`portée ${pM[0]}`);
    if (f.year) chips.push(`allumé en ${f.year}`);
    chips.push(f.sea ? "🌊 en mer" : "à terre");
    $("#phare-meta").innerHTML = chips.map(x =>
      `<span class="chip">${x}</span>`).join("");

    $("#phare-txt").textContent = f.txt;

    // caractéristiques détaillées
    const facts = [];
    if (X.construction) facts.push(["Construction", X.construction]);
    if (X.service) facts.push(["Mise en service", X.service]);
    if (X.feux) facts.push(["Feux", X.feux]);
    if (X.optique) facts.push(["Optique", X.optique]);
    $("#phare-facts").innerHTML = facts.map(([k, v]) =>
      `<div class="fact"><dt>${k}</dt><dd>${v}</dd></div>`).join("");

    const near = Tide.nearestPort(f.lat, f.lon);
    const btn = $("#phare-port");
    btn.textContent = `Marées à ${near.name} →`;
    btn.onclick = () => openSheet(near.id);
    $("#phare-sheet").classList.add("open");
    document.body.classList.add("sheet-open");
  }
  function closePhare() {
    openPhareId = null;
    stopSignal();
    $("#phare-sheet").classList.remove("open");
    if (!openPortId) document.body.classList.remove("sheet-open");
  }
  $("#phare-close").addEventListener("click", closePhare);

  function renderSheet() {
    const p = Tide.byId[openPortId];
    if (!p) return;
    const now = Date.now();
    const st = Tide.state(p, now);
    const ph = Moon.phase(now);
    const coef = Tide.currentCoef(now);
    const nextMs = Tide.toMs(st.next.t);

    $("#sheet-port").textContent = p.name;
    const info = typeof PORT_INFO !== "undefined" ? PORT_INFO[p.id] : null;
    const carac = typeof PORT_CARAC !== "undefined" ? PORT_CARAC[p.id] : null;
    $("#sheet-loc").textContent =
      `${info ? info.dep + " · " : ""}${dms(p.lat, "N", "S")} · ${dms(p.lon, "E", "O")}`;
    // module « À propos du port »
    $("#about-loc").textContent =
      `${p.name} — ${info ? info.dep + " · " : ""}${dms(p.lat, "N", "S")} · ${dms(p.lon, "E", "O")}`;
    $("#about-chips").innerHTML = carac && carac.act
      ? carac.act.map(a => `<span class="chip">${a}</span>`).join("") : "";
    $("#about-acc").textContent = carac && carac.acc ? carac.acc : "";
    const micro = st.range != null && st.range < 0.6
      ? `<span class="micro">Méditerranée : marée très faible (marnage &lt; 0,5 m), l'heure PM/BM reste indicative.</span>` : "";
    $("#sheet-info").innerHTML = info ? info.txt + micro : micro;
    const dirTxt = st.rising ? "Marée montante" : "Marée descendante";
    $("#sheet-state").innerHTML =
      `<span class="dir ${st.rising ? "up" : "down"}">${st.rising ? "▲" : "▼"} ${dirTxt}</span>
       <span class="next-ev">${st.next.type === "PM" ? "Pleine mer" : "Basse mer"}
         à <b>${fmtH(nextMs)}</b> · dans ${fmtDelta(nextMs - now)}</span>`;

    $("#tile-height .tile-val").textContent = fmtM(st.now);
    $("#tile-range .tile-val").textContent =
      st.range != null ? fmtM(st.range) : "—";
    $("#tile-coef .tile-val").innerHTML = coef != null
      ? `<span class="coef ${coefClass(coef)}">${coef}</span>` : "—";
    $("#tile-moon .tile-val").innerHTML = Moon.svg(ph.D, 26) +
      `<span class="moon-mini">${Math.round(ph.illum * 100)} %</span>`;
    $("#tile-moon .tile-lbl").textContent = ph.name;

    // 4 prochains extrêmes
    $("#events").innerHTML = st.upcoming.slice(0, 4).map(e => {
      const ms = Tide.toMs(e.t);
      return `<div class="ev">
        <span class="ev-type ${e.type === "PM" ? "pm" : "bm"}">${e.type}</span>
        <span class="ev-day">${fmtDay(ms)}</span>
        <span class="ev-time">${fmtH(ms)}</span>
        <span class="ev-h">${fmtM(e.h)}</span>
      </div>`;
    }).join("");

    drawCurve(p, now);
  }

  // --- courbe du jour (SVG) ---
  function drawCurve(p, nowMs) {
    const d0 = new Date(nowMs); d0.setHours(0, 0, 0, 0);
    const start = d0.getTime(), end = start + 86400000;
    const pts = Tide.curve(p, start, end, 0.2);
    const W = 360, H = 132, padL = 6, padR = 6, padT = 16, padB = 26;
    let hMin = Infinity, hMax = -Infinity;
    for (const q of pts) { hMin = Math.min(hMin, q.h); hMax = Math.max(hMax, q.h); }
    const span = Math.max(0.5, hMax - hMin);
    hMin -= span * 0.08; hMax += span * 0.08;
    const X = (ms) => padL + (ms - start) / 86400000 * (W - padL - padR);
    const Y = (h) => padT + (1 - (h - hMin) / (hMax - hMin)) * (H - padT - padB);

    const line = pts.map((q, i) =>
      `${i ? "L" : "M"}${X(q.ms).toFixed(1)},${Y(q.h).toFixed(1)}`).join("");
    const area = line + `L${X(end).toFixed(1)},${H - padB} L${padL},${H - padB} Z`;

    // extrêmes du jour, étiquetés directement
    const evs = Tide.extrema(p, Tide.toH(start), Tide.toH(end))
      .filter(e => Tide.toMs(e.t) >= start && Tide.toMs(e.t) < end);
    const marks = evs.map(e => {
      const x = X(Tide.toMs(e.t)), y = Y(e.h);
      const above = e.type === "PM";
      const ty = above ? Math.max(10, y - 7) : Math.min(H - padB + 8, y + 14);
      const tx = Math.min(W - 17, Math.max(17, x));
      return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3" class="ev-dot ${e.type === "PM" ? "pm" : "bm"}"/>
        <text x="${tx.toFixed(1)}" y="${ty.toFixed(1)}" class="ev-txt" text-anchor="middle">${fmtH(Tide.toMs(e.t))}</text>`;
    }).join("");

    const xNow = X(nowMs), yNow = Y(Tide.heightAt(p, nowMs));
    const hours = [3, 6, 9, 12, 15, 18, 21].map(h => {
      const x = X(start + h * 3600000);
      return `<line x1="${x}" y1="${padT}" x2="${x}" y2="${H - padB}" class="grid"/>` +
        (h % 6 === 0 ? `<text x="${x}" y="${H - 5}" class="ax-txt" text-anchor="middle">${h}h</text>` : "");
    }).join("");

    $("#curve").innerHTML =
      `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" id="curve-svg">
        ${hours}
        <path d="${area}" class="water-area"/>
        <path d="${line}" class="water-line"/>
        <rect x="${padL}" y="${padT}" width="${Math.max(0, xNow - padL)}" height="${H - padT - padB}" class="past-veil"/>
        ${marks}
        <line x1="${xNow}" y1="${padT}" x2="${xNow}" y2="${H - padB}" class="now-line"/>
        <circle cx="${xNow}" cy="${yNow}" r="4" class="now-dot"/>
      </svg>
      <div id="scrub" hidden></div>`;

    // lecture tactile : glisser sur la courbe -> heure + hauteur
    const svg = $("#curve-svg");
    const scrub = $("#scrub");
    const box = () => svg.getBoundingClientRect();
    function onMove(ev) {
      const b = box();
      const frac = Math.min(1, Math.max(0,
        ((ev.touches ? ev.touches[0].clientX : ev.clientX) - b.left) / b.width));
      const ms = start + frac * 86400000;
      scrub.hidden = false;
      scrub.textContent = `${fmtH(ms)} — ${fmtM(Tide.heightAt(p, ms))}`;
    }
    function onEnd() { scrub.hidden = true; }
    svg.addEventListener("pointermove", onMove);
    svg.addEventListener("pointerdown", onMove);
    svg.addEventListener("pointerleave", onEnd);
    svg.addEventListener("pointerup", onEnd);
  }

  // --- calendrier soleil & lune ---
  const calSheet = $("#cal-sheet");
  let calOpen = false;

  function calReference() {
    const pid = openPortId || lastPortId;
    if (pid) { const p = Tide.byId[pid]; return { name: p.name, lat: p.lat, lon: p.lon }; }
    const c = map.getCenter();
    return { name: "centre de la carte", lat: c.lat, lon: c.lng };
  }

  const fmtT = (ms) => ms ? fmtH(ms) : "—";

  function renderCal() {
    const ref = calReference();
    $("#cal-ref").textContent =
      `Heures locales pour ${ref.name} · coefficient de marée à droite`;
    const now = Date.now();
    const ph = Moon.phase(now);
    const sunNow = Astro.sunTimes(now, ref.lat, ref.lon);
    const moonNow = Astro.moonTimes(now, ref.lat, ref.lon);
    const fmtDate = (ms) => new Date(ms).toLocaleDateString("fr-FR",
      { weekday: "long", day: "numeric", month: "long" });
    const nn = ph.nextNew, nf = ph.nextFull;
    const nextTxt = nf < nn
      ? `Pleine lune le ${fmtDate(nf)} · nouvelle lune le ${fmtDate(nn)}`
      : `Nouvelle lune le ${fmtDate(nn)} · pleine lune le ${fmtDate(nf)}`;
    $("#cal-today").innerHTML = `
      <div class="ct-moon">${Moon.svg(ph.D, 44)}
        <div class="ct-name">${ph.name}<br>${Math.round(ph.illum * 100)} %</div></div>
      <div class="ct-times">
        <span>☀️ lever <b>${fmtT(sunNow.rise)}</b> · coucher <b>${fmtT(sunNow.set)}</b></span>
        <span>🌙 lever <b>${fmtT(moonNow.rise)}</b> · coucher <b>${fmtT(moonNow.set)}</b></span>
        <span class="ct-next">${nextTxt}</span>
      </div>`;

    const d0 = new Date(now); d0.setHours(0, 0, 0, 0);
    let rows = "";
    for (let i = 0; i < 14; i++) {
      const start = d0.getTime() + i * 86400000;
      const noon = start + 12 * 3600000;
      const sun = Astro.sunTimes(noon, ref.lat, ref.lon);
      const moon = Astro.moonTimes(noon, ref.lat, ref.lon);
      const mph = Moon.phase(noon);
      const coefs = Tide.dayCoefficients(start, start + 86400000);
      const day = new Date(start).toLocaleDateString("fr-FR",
        { weekday: "short", day: "numeric", month: "short" }).replace(".", "");
      rows += `<div class="cd${i === 0 ? " today" : ""}">
        <span class="cd-day">${day}</span>
        <span class="cd-moon">${Moon.svg(mph.D, 24)}
          <span class="cd-moonpct">${Math.round(mph.illum * 100)}%</span></span>
        <span class="cd-sun"><span class="ico">☀︎</span>${fmtT(sun.rise)} ${fmtT(sun.set)}</span>
        <span class="cd-lune"><span class="ico">☾</span>${fmtT(moon.rise)} ${fmtT(moon.set)}</span>
        <span class="cd-coefs">${coefs.map(c =>
          `<span class="coef ${coefClass(c.coef)}">${c.coef}</span>`).join("")}</span>
      </div>`;
    }
    $("#cal-days").innerHTML = rows;
  }

  function openCal() {
    closeSheet(); closePhare();
    calOpen = true;
    renderCal();
    calSheet.classList.add("open");
    document.body.classList.add("sheet-open");
  }
  function closeCal() {
    calOpen = false;
    calSheet.classList.remove("open");
    if (!openPortId) document.body.classList.remove("sheet-open");
  }
  $("#cal-btn").addEventListener("click", openCal);
  $("#cal-close").addEventListener("click", closeCal);
  $("#moon").addEventListener("click", openCal);

  // --- rafraîchissement périodique ---
  function tick() {
    refreshHeader();
    refreshMarkers();
    if (openPortId) renderSheet();
    if (calOpen) renderCal();
  }
  tick();
  setInterval(tick, 30000);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) tick();
  });

  // service worker (uniquement en mode hébergé http(s))
  const DEV = location.hostname === "localhost";
  if (!DEV && "serviceWorker" in navigator && location.protocol.startsWith("http")) {
    navigator.serviceWorker.register("sw.js").catch(() => {});
  }
})();
