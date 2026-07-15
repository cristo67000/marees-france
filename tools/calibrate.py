# -*- coding: utf-8 -*-
"""
Calibration des prédictions harmoniques sur les références SHOM (via maree.info).

Pour chaque port de référence :
  - décalage temporel dt (min) : médiane (heure officielle - heure prédite)
  - correction affine des hauteurs : h_corr = a * h_pred + b (moindres carrés)
Pour les autres ports : interpolation linéaire le long de la côte (ordre de la
liste) entre les deux ports de référence encadrants. Méditerranée : identité.

Coefficient de marée : régression linéaire C = s * H_PM_Brest_corrigée + i
sur les coefficients officiels du 14 au 20/07/2026.

Écrit les champs "dt" (heures), "a", "b" dans data/ports.json + bloc "coef".
"""
import json, math, os, datetime as dt

HERE = os.path.dirname(__file__)
PORTS_JSON = os.path.join(HERE, "..", "data", "ports.json")
REF_JSON = os.path.join(HERE, "reference_maree_info.json")

data = json.load(open(PORTS_JSON, encoding="utf-8"))
ref = json.load(open(REF_JSON, encoding="utf-8"))
EPOCH = dt.datetime(2026, 1, 1, 0, 0, tzinfo=dt.timezone.utc)
TZ = dt.timezone(dt.timedelta(hours=ref["tz_offset_hours"]))
ports_by_id = {p["id"]: p for p in data["ports"]}


def predict(port, t):
    v = port["z0"]
    for name, sp, a, ph in port["C"]:
        v += a * math.cos(math.radians(sp) * t - math.radians(ph))
    return v


def extrema(port, t_start, t_end):
    """Balayage 1 min -> [(t_h, hauteur, 'PM'|'BM')]"""
    out = []
    step = 1 / 60
    prev = predict(port, t_start - step)
    cur = predict(port, t_start)
    t = t_start
    while t <= t_end:
        nxt = predict(port, t + step)
        if cur >= prev and cur >= nxt and cur != nxt:
            out.append((t, cur, "PM"))
        elif cur <= prev and cur <= nxt and cur != nxt:
            out.append((t, cur, "BM"))
        prev, cur = cur, nxt
        t += step
    return out


def parse_ref(rows, start_date):
    """[(t_h_epoch, hauteur, 'PM'|'BM', coeff_ou_None)]"""
    events = []
    d0 = dt.date.fromisoformat(start_date)
    for i, (day, times, heights, coeffs) in enumerate(rows):
        date = d0 + dt.timedelta(days=i)
        ts = [times[j:j + 5] for j in range(0, len(times), 5)]
        hs = [float(x.replace(",", ".")) for x in heights.rstrip("m").split("m")]
        cs = coeffs.split("|")
        mid = (max(hs) + min(hs)) / 2
        ci = 0
        for tstr, h in zip(ts, hs):
            hh, mm = int(tstr[:2]), int(tstr[3:])
            when = dt.datetime(date.year, date.month, date.day, hh, mm, tzinfo=TZ)
            th = (when - EPOCH).total_seconds() / 3600
            kind = "PM" if h > mid else "BM"
            coef = None
            if kind == "PM":
                while ci < len(cs) and not cs[ci].strip():
                    ci += 1
                if ci < len(cs):
                    coef = int(cs[ci]); ci += 1
            events.append((th, h, kind, coef))
    return events


# --- calibration des ports de référence ---
t_lo = (dt.datetime(2026, 7, 13, 18, 0, tzinfo=dt.timezone.utc) - EPOCH).total_seconds() / 3600
t_hi = (dt.datetime(2026, 7, 21, 2, 0, tzinfo=dt.timezone.utc) - EPOCH).total_seconds() / 3600

calib = {}
brest_matches = []  # (h_pred_corrigee_PM, coeff officiel)
for pid, rows in ref["ports"].items():
    port = ports_by_id[pid]
    pred = extrema(port, t_lo, t_hi)
    refs = parse_ref(rows, ref["start_date"])
    matches = []
    for th, h, kind, coef in refs:
        best = min((p for p in pred if p[2] == kind), key=lambda p: abs(p[0] - th),
                   default=None)
        if best and abs(best[0] - th) < 2.5:
            matches.append((th, h, kind, coef, best[0], best[1]))
    dts = sorted(th - tp for th, h, k, c, tp, hp in matches)
    dt_med = dts[len(dts) // 2]
    # affine h_ref ~ a*h_pred + b
    n = len(matches)
    sx = sum(hp for *_, hp in matches); sy = sum(m[1] for m in matches)
    sxx = sum(hp * hp for *_, hp in matches); sxy = sum(m[1] * m[5] for m in matches)
    a = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    b = (sy - a * sx) / n
    t_rms = math.sqrt(sum((th - tp - dt_med) ** 2 for th, h, k, c, tp, hp in matches) / n) * 60
    h_rms = math.sqrt(sum((h - (a * hp + b)) ** 2 for th, h, k, c, tp, hp in matches) / n)
    calib[pid] = (dt_med, a, b)
    print(f"{pid:20s} n={n:2d}  dt={dt_med * 60:+6.1f} min  a={a:.3f} b={b:+.3f}"
          f"  résidus: t={t_rms:4.1f} min  h={h_rms * 100:4.1f} cm")
    if pid == "brest":
        for th, h, kind, coef, tp, hp in matches:
            if kind == "PM" and coef:
                brest_matches.append((a * hp + b, coef))

# --- régression coefficient sur PM Brest corrigées ---
n = len(brest_matches)
sx = sum(x for x, c in brest_matches); sy = sum(c for x, c in brest_matches)
sxx = sum(x * x for x, c in brest_matches); sxy = sum(x * c for x, c in brest_matches)
cs = (n * sxy - sx * sy) / (n * sxx - sx * sx)
ci = (sy - cs * sx) / n
c_rms = math.sqrt(sum((c - (cs * x + ci)) ** 2 for x, c in brest_matches) / n)
print(f"\nCoefficient: C = {cs:.2f} * H_PM_Brest {ci:+.2f}   (rms {c_rms:.1f}, n={n})")

# --- interpolation le long de la côte ---
coastal_order = [p["id"] for p in data["ports"]]
MED = {"port-vendres", "sete", "marseille", "toulon", "saint-tropez", "cannes",
       "nice", "ajaccio", "bastia"}
ref_idx = [i for i, pid in enumerate(coastal_order) if pid in calib]
for i, p in enumerate(data["ports"]):
    pid = p["id"]
    if pid in calib:
        d, a, b = calib[pid]
    elif pid in MED:
        d, a, b = 0.0, 1.0, 0.0
    else:
        lo = max((j for j in ref_idx if j < i), default=None)
        hi = min((j for j in ref_idx if j > i and coastal_order[j] not in MED),
                 default=None)
        if lo is None:
            d, a, b = calib[coastal_order[hi]]
        elif hi is None:
            d, a, b = calib[coastal_order[lo]]
        else:
            w = (i - lo) / (hi - lo)
            d1, a1, b1 = calib[coastal_order[lo]]
            d2, a2, b2 = calib[coastal_order[hi]]
            d, a, b = d1 + w * (d2 - d1), a1 + w * (a2 - a1), b1 + w * (b2 - b1)
    p["dt"] = round(d, 4)
    p["a"] = round(a, 4)
    p["b"] = round(b, 4)

data["coef"] = {"slope": round(cs, 3), "intercept": round(ci, 3)}
data["calibrated"] = "maree.info 2026-07-14..20"
json.dump(data, open(PORTS_JSON, "w", encoding="utf-8"),
          ensure_ascii=False, separators=(",", ":"))
print(f"\nEcrit: {PORTS_JSON} ({os.path.getsize(PORTS_JSON)} octets)")
