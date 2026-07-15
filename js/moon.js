/* Phase de lune — formules solaires/lunaires tronquées de Meeus.
   Précision ~1° d'élongation, largement suffisante pour l'affichage. */
"use strict";

const Moon = (() => {
  const DEG = Math.PI / 180;
  const SYNODIC = 29.530588853; // jours

  // élongation Lune-Soleil en degrés [0..360)
  function elongation(ms) {
    const T = (ms / 86400000 - 10957.5) / 36525; // siècles juliens depuis J2000
    const g = (357.529 + 35999.050 * T) * DEG;          // anomalie moyenne soleil
    const sun = 280.466 + 36000.770 * T
              + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g);
    const lp = (134.963 + 477198.868 * T) * DEG;        // anomalie moyenne lune
    const dm = (297.850 + 445267.115 * T) * DEG;        // élongation moyenne
    const moon = 218.316 + 481267.881 * T
               + 6.289 * Math.sin(lp)
               + 1.274 * Math.sin(2 * dm - lp)
               + 0.658 * Math.sin(2 * dm);
    return ((moon - sun) % 360 + 360) % 360;
  }

  function phase(ms) {
    const D = elongation(ms);
    const illum = (1 - Math.cos(D * DEG)) / 2;
    const waxing = D < 180;
    let name;
    if (D < 22.5 || D >= 337.5) name = "Nouvelle lune";
    else if (D < 67.5) name = "Premier croissant";
    else if (D < 112.5) name = "Premier quartier";
    else if (D < 157.5) name = "Lune gibbeuse";
    else if (D < 202.5) name = "Pleine lune";
    else if (D < 247.5) name = "Lune gibbeuse";
    else if (D < 292.5) name = "Dernier quartier";
    else name = "Dernier croissant";
    return { D, illum, waxing, name,
             nextNew: nextCrossing(ms, 0), nextFull: nextCrossing(ms, 180) };
  }

  // prochaine date où l'élongation croise `target` (0=NL, 180=PL)
  function nextCrossing(ms, target) {
    const step = 6 * 3600000; // 6 h
    let prev = ((elongation(ms) - target) % 360 + 360) % 360;
    for (let t = ms + step; t < ms + 32 * 86400000; t += step) {
      const cur = ((elongation(t) - target) % 360 + 360) % 360;
      if (cur < prev) prev = cur;
      else if (prev < 30) {
        // on vient de passer le zéro entre t-2*step et t : bissection
        let lo = t - 2 * step, hi = t - step + step;
        for (let i = 0; i < 24; i++) {
          const mid = (lo + hi) / 2;
          const d = ((elongation(mid) - target + 180) % 360 + 360) % 360 - 180;
          if (d < 0) lo = mid; else hi = mid;
        }
        return (lo + hi) / 2;
      } else prev = cur;
    }
    return null;
  }

  /* Icône SVG de la phase (hémisphère nord : croissante éclairée à droite).
     size en px. */
  function svg(D, size) {
    const r = 10;
    const k = Math.cos(D * DEG); // +1 NL, -1 PL
    const rx = Math.abs(k) * r;
    const right = D < 180; // partie éclairée côté droit si croissante
    // disque sombre + partie éclairée = demi-cercle + demi-ellipse
    const sweepOuter = right ? 1 : 0;
    const sweepInner = (k < 0) === right ? 1 : 0;
    const lit = `M 12 2 A ${r} ${r} 0 0 ${sweepOuter} 12 22 ` +
                `A ${rx} ${r} 0 0 ${sweepInner} 12 2 Z`;
    return `<svg viewBox="0 0 24 24" width="${size}" height="${size}" aria-hidden="true">
      <circle cx="12" cy="12" r="${r}" class="moon-dark"/>
      <path d="${lit}" class="moon-lit"/>
      <circle cx="12" cy="12" r="${r}" class="moon-ring" fill="none"/>
    </svg>`;
  }

  return { phase, svg };
})();
