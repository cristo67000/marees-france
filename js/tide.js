/* Moteur de marées — prédiction harmonique locale (aucun réseau requis).
   h(t) = a * [ z0 + somme A_i cos(w_i (t - dt) - phi_i) ] + b
   t en heures écoulées depuis l'epoch du jeu de données (UTC).
   Les constantes proviennent d'un ajustement sur 1 an de données de niveau
   de la mer, recalées sur les horaires officiels (voir tools/). */
"use strict";

const Tide = (() => {
  const DEG = Math.PI / 180;
  let epochMs = 0;
  let ports = [];
  let byId = {};
  let coefReg = { slope: 32.8, intercept: -2.3 };
  let coefTable = {};   // "AAAA-MM-JJ" (Europe/Paris) -> [coef, ...] officiels
  let semiBrest = [];   // composantes semi-diurnes de Brest (enveloppe)

  const parisDay = new Intl.DateTimeFormat("fr-CA",
    { timeZone: "Europe/Paris", year: "numeric", month: "2-digit", day: "2-digit" });

  function init(data) {
    epochMs = Date.parse(data.epoch);
    ports = data.ports;
    coefReg = data.coef;
    coefTable = data.coefTable || {};
    byId = {};
    for (const p of ports) {
      byId[p.id] = p;
      // pré-calcul : vitesses et phases en radians
      p._c = p.C.map(([n, sp, a, ph]) => [sp * DEG, a, ph * DEG]);
    }
    semiBrest = byId.brest._c.filter(([w]) => w > 26 * DEG && w < 32 * DEG);
  }

  const toH = (ms) => (ms - epochMs) / 3.6e6;
  const toMs = (tH) => epochMs + tH * 3.6e6;

  function height(port, tH) {
    const tr = tH - port.dt;
    let v = port.z0;
    for (const [w, a, ph] of port._c) v += a * Math.cos(w * tr - ph);
    return port.a * v + port.b;
  }

  /* Extrema entre t0 et t1 (heures epoch) : échantillonnage 6 min puis
     affinage parabolique -> précision < 1 min. */
  function extrema(port, t0, t1) {
    const step = 0.1;
    const n = Math.ceil((t1 - t0) / step) + 2;
    const s = new Array(n);
    for (let i = 0; i < n; i++) s[i] = height(port, t0 + i * step);
    const out = [];
    for (let i = 1; i < n - 1; i++) {
      const isMax = s[i] >= s[i - 1] && s[i] >= s[i + 1];
      const isMin = s[i] <= s[i - 1] && s[i] <= s[i + 1];
      if (!isMax && !isMin) continue;
      const d = s[i - 1] - 2 * s[i] + s[i + 1];
      const off = d !== 0 ? 0.5 * step * (s[i - 1] - s[i + 1]) / d : 0;
      const t = t0 + i * step + Math.max(-step, Math.min(step, off));
      out.push({ t, h: height(port, t), type: isMax ? "PM" : "BM" });
    }
    // dédoublonne (paliers plats possibles en Méditerranée)
    return out.filter((e, i) => i === 0 || e.t - out[i - 1].t > 0.5);
  }

  /* État courant + événements voisins autour de nowMs. */
  function state(port, nowMs) {
    const tn = toH(nowMs);
    const evs = extrema(port, tn - 16, tn + 30);
    let prev = null, next = null, next2 = null;
    for (const e of evs) {
      if (e.t <= tn) prev = e;
      else if (!next) next = e;
      else if (!next2) { next2 = e; break; }
    }
    const rising = height(port, tn + 0.03) > height(port, tn);
    const range = prev && next ? Math.abs(next.h - prev.h) : null;
    return { now: height(port, tn), rising, prev, next, next2, range,
             upcoming: evs.filter(e => e.t > tn) };
  }

  /* Coefficient de marée (défini à Brest) pour la PM d'indice i de evs.
     Table officielle SHOM si la date est couverte, sinon modèle :
     C = slope * enveloppe semi-diurne + intercept. */
  function envBrest(tH) {
    const brest = byId.brest;
    const tr = tH - brest.dt;
    let re = 0, im = 0;
    for (const [w, a, ph] of semiBrest) {
      re += a * Math.cos(w * tr - ph);
      im += a * Math.sin(w * tr - ph);
    }
    return brest.a * Math.hypot(re, im);
  }

  function coefForPm(evs, i) {
    const e = evs[i];
    const day = parisDay.format(toMs(e.t));
    const official = coefTable[day];
    if (official) {
      // rang de cette PM parmi les PM de Brest du même jour civil (Paris)
      const sameDay = evs.filter(x => x.type === "PM" &&
        parisDay.format(toMs(x.t)) === day);
      const idx = sameDay.findIndex(x => Math.abs(x.t - e.t) < 0.05);
      if (idx >= 0 && idx < official.length && sameDay.length === official.length)
        return official[idx];
    }
    const c = Math.round(coefReg.slope * envBrest(e.t) + coefReg.intercept);
    return Math.max(20, Math.min(120, c));
  }

  /* Coefficients des PM de Brest comprises dans [dayStartMs, dayEndMs). */
  function dayCoefficients(dayStartMs, dayEndMs) {
    const brest = byId.brest;
    const t0 = toH(dayStartMs), t1 = toH(dayEndMs);
    const evs = extrema(brest, t0 - 9, t1 + 9);
    const out = [];
    evs.forEach((e, i) => {
      if (e.type === "PM" && e.t >= t0 && e.t < t1) {
        const c = coefForPm(evs, i);
        if (c !== null) out.push({ t: e.t, coef: c });
      }
    });
    return out;
  }

  /* Coefficient de la marée en cours/à venir (PM de Brest la plus proche
     de nowMs, cycle courant). */
  function currentCoef(nowMs) {
    const brest = byId.brest;
    const tn = toH(nowMs);
    const evs = extrema(brest, tn - 30, tn + 30);
    let best = null, bi = -1;
    evs.forEach((e, i) => {
      if (e.type === "PM" && (best === null || Math.abs(e.t - tn) < Math.abs(best.t - tn))) {
        best = e; bi = i;
      }
    });
    return best ? coefForPm(evs, bi) : null;
  }

  /* Courbe sur [t0, t1] échantillonnée toutes les `stepH` heures. */
  function curve(port, t0Ms, t1Ms, stepH) {
    const t0 = toH(t0Ms), t1 = toH(t1Ms);
    const pts = [];
    for (let t = t0; t <= t1 + 1e-9; t += stepH)
      pts.push({ ms: toMs(t), h: height(port, t) });
    return pts;
  }

  const heightAt = (port, ms) => height(port, toH(ms));

  function nearestPort(lat, lon) {
    let best = null, bd = Infinity;
    for (const p of ports) {
      const dLat = (p.lat - lat) * DEG, dLon = (p.lon - lon) * DEG;
      const x = dLon * Math.cos(((p.lat + lat) / 2) * DEG);
      const d = dLat * dLat + x * x;
      if (d < bd) { bd = d; best = p; }
    }
    return best;
  }

  return { init, state, extrema, dayCoefficients, currentCoef, curve,
           heightAt, nearestPort, toH, toMs,
           get ports() { return ports; }, get byId() { return byId; } };
})();
