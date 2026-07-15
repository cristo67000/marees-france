# -*- coding: utf-8 -*-
"""
Calage des constantes harmoniques de marée pour les ports français.

Récupère 1 an de hauteurs d'eau horaires (Open-Meteo Marine API, variable
sea_level_height_msl) pour chaque port, puis ajuste par moindres carrés
22 composantes harmoniques. Le résultat est écrit dans ../data/ports.json.

Convention de prédiction (identique dans l'app JS) :
    h(t) = z0 + somme_i A_i * cos( w_i * dt - phi_i )
    dt   = heures écoulées depuis EPOCH (2026-01-01T00:00Z)
    z0   = niveau moyen au-dessus du zéro des cartes (~ plus basse mer de l'année)
"""
import json, math, time, urllib.request, os, sys

EPOCH = "2026-01-01T00:00"          # référence de phase (UTC)
START, END = "2025-07-01", "2026-06-30"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "ports.json")

# Vitesses angulaires en degrés/heure (constantes astronomiques exactes).
# K2/T2/P1 ne sont PAS ajustés librement : la modulation saisonnière de S2/K1
# dans les données du modèle s'aliase exactement sur leurs fréquences
# (S2±Ssa = K2, S2±Sa = T2/R2, K1−Ssa = P1). On les infère par les ratios
# d'équilibre : K2 = 0.2725*S2, T2 = 0.0592*S2, P1 = 0.3309*K1 (même phase).
CONSTITUENTS = [
    ("Sa",   0.0410686), ("Ssa",  0.0821373), ("Mm",   0.5443747),
    ("Mf",   1.0980331), ("Q1",  13.3986609), ("O1",  13.9430356),
    ("K1",  15.0410686), ("2N2", 27.8953548),
    ("MU2", 27.9682084), ("N2",  28.4397295), ("NU2", 28.5125831),
    ("M2",  28.9841042), ("L2",  29.5284789),
    ("S2",  30.0000000), ("MN4", 57.4238337),
    ("M4",  57.9682084), ("MS4", 58.9841042), ("M6",  86.9523127),
]
SPEED = dict(CONSTITUENTS + [("K2", 30.0821373), ("T2", 29.9589333),
                             ("P1", 14.9589314)])


def _v0():
    """Arguments astronomiques V0 (degrés) à EPOCH, polynômes de Schureman."""
    import datetime as dt
    d = (dt.datetime.fromisoformat(EPOCH) - dt.datetime(2000, 1, 1, 12)).total_seconds() / 86400
    T = d / 36525.0
    h = (280.46646 + 36000.76983 * T) % 360      # longitude moyenne du soleil
    p1 = (282.94 + 1.719 * T) % 360              # périgée solaire
    # à 00:00 UT : V0(S2)=0 ; V0(K2)=2h ; V0(T2)=-h+p1 ; V0(K1)=h+90 ; V0(P1)=-h-90
    return {"S2": 0.0, "K2": (2 * h) % 360, "T2": (-h + p1) % 360,
            "K1": (h + 90) % 360, "P1": (-h - 90) % 360}


_V = _v0()
# phase inférée : phi_inf = phi_maître + V0(maître) - V0(inféré)
INFER = {
    "S2": [("K2", 0.2725, _V["S2"] - _V["K2"]), ("T2", 0.0592, _V["S2"] - _V["T2"])],
    "K1": [("P1", 0.3309, _V["K1"] - _V["P1"])],
}

PORTS = [
    # (id, nom, lat, lon)  — côte Manche/mer du Nord, d'est en ouest
    ("dunkerque", "Dunkerque", 51.06, 2.35),
    ("calais", "Calais", 50.97, 1.84),
    ("boulogne", "Boulogne-sur-Mer", 50.74, 1.57),
    ("le-treport", "Le Tréport", 50.06, 1.37),
    ("dieppe", "Dieppe", 49.94, 1.07),
    ("fecamp", "Fécamp", 49.77, 0.36),
    ("le-havre", "Le Havre", 49.48, 0.10),
    ("trouville", "Deauville-Trouville", 49.37, 0.08),
    ("ouistreham", "Ouistreham", 49.30, -0.25),
    ("saint-vaast", "Saint-Vaast-la-Hougue", 49.59, -1.26),
    ("cherbourg", "Cherbourg", 49.66, -1.62),
    ("carteret", "Barneville-Carteret", 49.37, -1.80),
    ("granville", "Granville", 48.84, -1.61),
    ("cancale", "Cancale", 48.68, -1.85),
    ("saint-malo", "Saint-Malo", 48.65, -2.03),
    ("erquy", "Erquy", 48.64, -2.47),
    ("paimpol", "Paimpol", 48.79, -3.04),
    ("perros-guirec", "Perros-Guirec", 48.82, -3.44),
    ("roscoff", "Roscoff", 48.73, -3.97),
    ("aber-wrach", "L'Aber Wrac'h", 48.60, -4.56),
    ("le-conquet", "Le Conquet", 48.36, -4.78),
    ("brest", "Brest", 48.38, -4.49),
    ("douarnenez", "Douarnenez", 48.10, -4.33),
    ("audierne", "Audierne", 48.01, -4.54),
    ("guilvinec", "Le Guilvinec", 47.79, -4.28),
    ("concarneau", "Concarneau", 47.87, -3.91),
    ("lorient", "Lorient", 47.74, -3.36),
    ("quiberon", "Quiberon", 47.48, -3.12),
    ("crouesty", "Le Crouesty", 47.54, -2.92),
    ("le-croisic", "Le Croisic", 47.30, -2.51),
    ("saint-nazaire", "Saint-Nazaire", 47.27, -2.20),
    ("pornic", "Pornic", 47.11, -2.11),
    ("noirmoutier", "Noirmoutier (L'Herbaudière)", 47.03, -2.30),
    ("saint-gilles", "Saint-Gilles-Croix-de-Vie", 46.69, -1.95),
    ("les-sables", "Les Sables-d'Olonne", 46.49, -1.80),
    ("ile-de-re", "Île de Ré (Saint-Martin)", 46.20, -1.37),
    ("la-rochelle", "La Rochelle", 46.15, -1.22),
    ("oleron", "Oléron (La Cotinière)", 45.91, -1.34),
    ("royan", "Royan", 45.62, -1.03),
    ("arcachon", "Arcachon", 44.66, -1.17),
    ("capbreton", "Capbreton", 43.65, -1.45),
    ("bayonne", "Bayonne-Anglet", 43.53, -1.53),
    ("saint-jean-de-luz", "Saint-Jean-de-Luz", 43.39, -1.67),
    ("hendaye", "Hendaye", 43.36, -1.79),
    # Méditerranée (marées faibles)
    ("port-vendres", "Port-Vendres", 42.52, 3.11),
    ("sete", "Sète", 43.39, 3.70),
    ("marseille", "Marseille", 43.29, 5.36),
    ("toulon", "Toulon", 43.10, 5.93),
    ("saint-tropez", "Saint-Tropez", 43.27, 6.64),
    ("cannes", "Cannes", 43.55, 7.02),
    ("nice", "Nice", 43.69, 7.28),
    ("ajaccio", "Ajaccio", 41.92, 8.73),
    ("bastia", "Bastia", 42.70, 9.46),
]


CACHE = os.path.join(os.path.dirname(__file__), "cache")


def fetch(lat, lon):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{lat}_{lon}.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    url = (f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}"
           f"&hourly=sea_level_height_msl&start_date={START}&end_date={END}&timezone=UTC")
    with urllib.request.urlopen(url, timeout=60) as r:
        data = json.load(r)
    json.dump(data, open(path, "w", encoding="utf-8"))
    return data


def hours_since_epoch(iso):
    # iso "2025-07-01T00:00" ; calcul purement arithmétique (tout est UTC)
    import datetime as dt
    t = dt.datetime.fromisoformat(iso)
    e = dt.datetime.fromisoformat(EPOCH)
    return (t - e).total_seconds() / 3600.0


def fit_port(times_h, heights):
    import numpy as np
    t = np.asarray(times_h)
    y = np.asarray(heights, dtype=float)
    ok = ~np.isnan(y)
    t, y = t[ok], y[ok]
    cols = [np.ones_like(t)]
    for name, speed in CONSTITUENTS:
        w = math.radians(speed)
        c_col, s_col = np.cos(w * t), np.sin(w * t)
        for iname, ratio, dphi in INFER.get(name, []):
            wi = math.radians(SPEED[iname])
            dp = math.radians(dphi)
            c_col = c_col + ratio * np.cos(wi * t - dp)
            s_col = s_col + ratio * np.sin(wi * t - dp)
        cols.append(c_col)
        cols.append(s_col)
    A = np.column_stack(cols)
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    resid = y - A @ coef
    rms = float(np.sqrt(np.mean(resid ** 2)))
    z0_msl = float(coef[0])
    consts = []
    for i, (name, speed) in enumerate(CONSTITUENTS):
        c, s = coef[1 + 2 * i], coef[2 + 2 * i]
        amp = float(math.hypot(c, s))
        phi = float(math.degrees(math.atan2(s, c))) % 360.0
        consts.append((name, speed, amp, phi))
        for iname, ratio, dphi in INFER.get(name, []):
            consts.append((iname, SPEED[iname], amp * ratio, (phi + dphi) % 360))
    # zéro des cartes ~ plus basse mer prédite sur l'année (pas 10 min)
    tt = np.arange(t.min(), t.max(), 1 / 6)
    pred = np.full_like(tt, z0_msl)
    for name, speed, amp, phi in consts:
        pred += amp * np.cos(np.radians(speed) * tt - math.radians(phi))
    datum = float(pred.min())
    z0 = z0_msl - datum          # niveau moyen au-dessus du zéro des cartes
    kept = [(n, sp, round(a, 4), round(p, 2)) for n, sp, a, p in consts if a >= 0.003]
    return z0, kept, rms, float(pred.max() - datum)


def main():
    out = {"epoch": EPOCH + "Z", "source": f"Open-Meteo Marine API, ajustement {START}..{END}",
           "ports": []}
    for pid, name, lat, lon in PORTS:
        for attempt in range(3):
            try:
                d = fetch(lat, lon)
                break
            except Exception as e:
                print(f"  retry {pid}: {e}", flush=True)
                time.sleep(3)
        else:
            print(f"ECHEC {pid}", flush=True)
            continue
        times = [hours_since_epoch(x) for x in d["hourly"]["time"]]
        heights = [float("nan") if v is None else v
                   for v in d["hourly"]["sea_level_height_msl"]]
        z0, consts, rms, hmax = fit_port(times, heights)
        m2 = next((a for n, s, a, p in consts if n == "M2"), 0)
        print(f"{name:32s} z0={z0:5.2f}  M2={m2:5.2f}  max={hmax:5.2f}  rms={rms * 100:5.1f} cm",
              flush=True)
        out["ports"].append({
            "id": pid, "name": name, "lat": lat, "lon": lon,
            "z0": round(z0, 3),
            "C": [[n, s, a, p] for n, s, a, p in consts],
        })
        time.sleep(0.4)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"\nEcrit: {OUT} ({os.path.getsize(OUT)} octets, {len(out['ports'])} ports)")


if __name__ == "__main__":
    main()
