# -*- coding: utf-8 -*-
"""
Coefficients de marée — version finale :
 1. table officielle (maree.info/SHOM, jan..oct 2026) embarquée telle quelle
    dans ports.json (clé coefTable, dates locales Europe/Paris) ;
 2. régression de secours C = slope * A_semi-diurne(PM) + intercept où A est
    l'enveloppe des composantes semi-diurnes de Brest (utilisée au-delà de la
    table). rms ~2 points.
"""
import json, math, os, datetime as dt

HERE = os.path.dirname(__file__)
PORTS_JSON = os.path.join(HERE, "..", "data", "ports.json")
data = json.load(open(PORTS_JSON, encoding="utf-8"))
cal = json.load(open(os.path.join(HERE, "coef_calendar.json"), encoding="utf-8"))
brest = next(p for p in data["ports"] if p["id"] == "brest")
EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
DS, DE = dt.date(2026, 3, 29), dt.date(2026, 10, 25)
D = math.pi / 180

semi = [(sp, a, ph) for n, sp, a, ph in brest["C"] if 26 < sp < 32]


def env(t):
    tr = t - brest["dt"]
    re = im = 0.0
    for sp, a, ph in semi:
        re += a * math.cos(sp * D * tr - ph * D)
        im += a * math.sin(sp * D * tr - ph * D)
    return brest["a"] * math.hypot(re, im)


def h_corr(t):
    tr = t - brest["dt"]
    v = brest["z0"]
    for n, sp, a, ph in brest["C"]:
        v += a * math.cos(sp * D * tr - ph * D)
    return brest["a"] * v + brest["b"]


def events(t0, t1):
    out, st = [], 1 / 30
    prev, cur, t = h_corr(t0 - st), h_corr(t0), t0
    while t <= t1:
        nxt = h_corr(t + st)
        if cur >= prev and cur >= nxt:
            out.append((t, cur, "PM"))
        elif cur <= prev and cur <= nxt:
            out.append((t, cur, "BM"))
        prev, cur, t = cur, nxt, t + st
    return out


pairs = []
table = {}
for mkey, days in cal.items():
    y, mo = int(mkey[:4]), int(mkey[4:6])
    t0 = (dt.datetime(y, mo, 1, tzinfo=dt.timezone.utc) - EPOCH).total_seconds() / 3600 - 24
    evs = events(t0, t0 + 24 * 33 + 48)
    pms = [(i, t, h) for i, (t, h, k) in enumerate(evs) if k == "PM"]
    for day, coefs in days:
        date = dt.date(y, mo, day)
        table[date.isoformat()] = coefs
        off = 2 if DS <= date < DE else 1
        dp = [(i, t, h) for i, t, h in pms
              if (EPOCH + dt.timedelta(hours=t + off)).date() == date]
        if len(dp) != len(coefs):
            continue
        for (i, t, h), c in zip(dp, coefs):
            pairs.append((env(t), c))

n = len(pairs)
sx = sum(x for x, c in pairs); sy = sum(c for x, c in pairs)
sxx = sum(x * x for x, c in pairs); sxy = sum(x * c for x, c in pairs)
slope = (n * sxy - sx * sy) / (n * sxx - sx * sx)
inter = (sy - slope * sx) / n
res = [c - (slope * x + inter) for x, c in pairs]
rms = math.sqrt(sum(r * r for r in res) / n)
print(f"modèle enveloppe: n={n}  C = {slope:.3f}*A {inter:+.3f}  "
      f"rms={rms:.2f} max={max(abs(r) for r in res):.1f}")
print(f"table officielle: {len(table)} jours "
      f"({min(table)} .. {max(table)})")

data["coef"] = {"slope": round(slope, 3), "intercept": round(inter, 3),
                "type": "envelope"}
data["coefTable"] = table
json.dump(data, open(PORTS_JSON, "w", encoding="utf-8"),
          ensure_ascii=False, separators=(",", ":"))
print(f"Ecrit: {PORTS_JSON} ({os.path.getsize(PORTS_JSON)} octets)")
