/* Lever/coucher du soleil (algorithme NOAA) et de la lune (série tronquée,
   balayage d'altitude). Précision : ~1 min soleil, ~3 min lune. */
"use strict";

const Astro = (() => {
  const DEG = Math.PI / 180;
  const J2000 = Date.UTC(2000, 0, 1, 12);

  const centuries = (ms) => (ms - J2000) / 86400000 / 36525;

  // --- soleil ---
  function sunEphem(ms) {
    const T = centuries(ms);
    const L0 = (280.46646 + 36000.76983 * T) % 360;
    const M = (357.52911 + 35999.05029 * T) * DEG;
    const e = 0.016708634 - 0.000042037 * T;
    const C = (1.914602 - 0.004817 * T) * Math.sin(M)
            + (0.019993 - 0.000101 * T) * Math.sin(2 * M)
            + 0.000289 * Math.sin(3 * M);
    const omega = (125.04 - 1934.136 * T) * DEG;
    const lambda = (L0 + C - 0.00569 - 0.00478 * Math.sin(omega)) * DEG;
    const eps = (23.4392911 - 0.0130042 * T + 0.00256 * Math.cos(omega)) * DEG;
    const decl = Math.asin(Math.sin(eps) * Math.sin(lambda));
    const y = Math.tan(eps / 2) ** 2;
    const L0r = L0 * DEG;
    const E = 4 / DEG * (y * Math.sin(2 * L0r) - 2 * e * Math.sin(M)
      + 4 * e * y * Math.sin(M) * Math.cos(2 * L0r)
      - 0.5 * y * y * Math.sin(4 * L0r)
      - 1.25 * e * e * Math.sin(2 * M));           // équation du temps, minutes
    return { decl, E };
  }

  /* Lever/coucher du soleil pour le jour civil local contenant dayMs.
     Retourne {rise, set} en ms (null si soleil toujours levé/couché). */
  function sunTimes(dayMs, lat, lon) {
    const d0 = new Date(dayMs); d0.setHours(12, 0, 0, 0);
    let rise = null, set = null;
    for (const which of ["rise", "set"]) {
      let t = d0.getTime();
      for (let i = 0; i < 2; i++) {              // deux passes de raffinement
        const { decl, E } = sunEphem(t);
        const phi = lat * DEG;
        const cosw = (Math.cos(90.833 * DEG) - Math.sin(phi) * Math.sin(decl))
                   / (Math.cos(phi) * Math.cos(decl));
        if (cosw < -1 || cosw > 1) { t = null; break; }
        const w = Math.acos(cosw) / DEG;         // demi-arc diurne en degrés
        const noonUTCmin = 720 - 4 * lon - E;
        const evMin = which === "rise" ? noonUTCmin - 4 * w : noonUTCmin + 4 * w;
        const d = new Date(d0); d.setHours(0, 0, 0, 0);
        // minuit local -> minuit UTC du même jour civil
        const utcMidnight = Date.UTC(d.getFullYear(), d.getMonth(), d.getDate());
        t = utcMidnight + evMin * 60000;
      }
      if (which === "rise") rise = t; else set = t;
    }
    return { rise, set };
  }

  // --- lune ---
  function moonEquatorial(ms) {
    const T = centuries(ms);
    const lp = (134.963 + 477198.8676 * T) * DEG;   // anomalie moyenne lune
    const D = (297.850 + 445267.1115 * T) * DEG;    // élongation moyenne
    const F = (93.272 + 483202.0175 * T) * DEG;     // argument de latitude
    const M = (357.529 + 35999.0503 * T) * DEG;     // anomalie moyenne soleil
    const lon = (218.316 + 481267.8813 * T) * DEG
      + (6.289 * Math.sin(lp) + 1.274 * Math.sin(2 * D - lp)
       + 0.658 * Math.sin(2 * D) + 0.214 * Math.sin(2 * lp)
       - 0.186 * Math.sin(M) - 0.114 * Math.sin(2 * F)) * DEG;
    const beta = (5.128 * Math.sin(F) + 0.281 * Math.sin(lp + F)) * DEG;
    const eps = (23.4392911 - 0.0130042 * T) * DEG;
    const sd = Math.sin(beta) * Math.cos(eps)
             + Math.cos(beta) * Math.sin(eps) * Math.sin(lon);
    const decl = Math.asin(sd);
    const ra = Math.atan2(Math.sin(lon) * Math.cos(eps) - Math.tan(beta) * Math.sin(eps),
                          Math.cos(lon));
    return { ra, decl };
  }

  function moonAltitude(ms, lat, lon) {
    const { ra, decl } = moonEquatorial(ms);
    const d = (ms - J2000) / 86400000;
    const gmst = (280.46061837 + 360.98564736629 * d) % 360;
    const H = ((gmst + lon) * DEG - ra);
    const phi = lat * DEG;
    return Math.asin(Math.sin(phi) * Math.sin(decl)
                   + Math.cos(phi) * Math.cos(decl) * Math.cos(H)) / DEG;
  }

  /* Lever/coucher de lune du jour civil local. h0 = +0.125° (parallaxe
     - réfraction - demi-diamètre). Peut être null (pas d'événement ce jour). */
  function moonTimes(dayMs, lat, lon) {
    const H0 = 0.125;
    const d0 = new Date(dayMs); d0.setHours(0, 0, 0, 0);
    const start = d0.getTime(), end = start + 86400000;
    let rise = null, set = null;
    const step = 10 * 60000;
    let prev = moonAltitude(start, lat, lon) - H0;
    for (let t = start + step; t <= end; t += step) {
      const cur = moonAltitude(t, lat, lon) - H0;
      if (prev <= 0 && cur > 0 || prev > 0 && cur <= 0) {
        let lo = t - step, hi = t;
        for (let i = 0; i < 20; i++) {
          const mid = (lo + hi) / 2;
          const v = moonAltitude(mid, lat, lon) - H0;
          if ((v > 0) === (cur > 0)) hi = mid; else lo = mid;
        }
        if (cur > 0) rise = rise ?? (lo + hi) / 2;
        else set = set ?? (lo + hi) / 2;
      }
      prev = cur;
    }
    return { rise, set };
  }

  return { sunTimes, moonTimes };
})();
