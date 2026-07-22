# -*- coding: utf-8 -*-
"""
Contours des îles manquantes du fond de carte : îles bretonnes, anglo-normandes
et quelques îles qui portent des phares de l'app (Chausey, Yeu).

data/france.geojson ne contient que le continent, la Corse, Ré, Oléron,
Noirmoutier et Belle-Île : Ouessant, Molène, Sein, Batz ou Groix étaient des
phares posés sur de l'eau vide, et le golfe Normand-Breton était troué.

Source : contours OpenStreetMap servis par Nominatim (polygon_geojson=1),
simplifiés Douglas-Peucker comme les fleuves. Les îles anglo-normandes ne sont
pas françaises : elles sortent dans un groupe distinct pour pouvoir les dessiner
autrement (ce sont des dépendances de la Couronne, pas du territoire national).

ATTENTION : Nominatim renvoie volontiers un homonyme à l'autre bout du monde
(« Jersey » → Jersey County, Illinois). Chaque résultat est donc validé sur la
position attendue avant d'être retenu.

Sortie : data/iles.json
"""
import json, math, os, time, urllib.parse, urllib.request

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
UA = {"User-Agent": "MareesFranceApp/1.0 (usage personnel; cristo67000@gmail.com)"}
NOMINATIM = "https://nominatim.openstreetmap.org/search"

# id, requête, position attendue (contrôle), étiquette, groupe, zoom mini
ILES = [
    ("ouessant",  "Ouessant, Finistère",            48.46, -5.09, "Ouessant",   "bretonne", 6.5),
    ("molene",    "Île Molène, Finistère",          48.40, -4.96, "Molène",     "bretonne", 8.5),
    ("sein",      "Île de Sein, Finistère",         48.04, -4.85, "île de Sein", "bretonne", 8),
    ("batz",      "Île de Batz, Finistère",         48.74, -4.01, "île de Batz", "bretonne", 8.5),
    ("glenan",    "Îles Glénan, Fouesnant",         47.72, -3.99, "les Glénan", "bretonne", 8.5),
    # « Île de Groix » ne ramène que des POI (parking, camping, et même une rue
    # de Léhon à 130 km) : c'est « Groix » seul qui sort l'île.
    ("groix",     "Groix",                          47.64, -3.45, "Groix",      "bretonne", 7.5),
    ("houat",     "Houat, Morbihan",                47.39, -2.96, "Houat",      "bretonne", 8.5),
    ("hoedic",    "Hoedic, Morbihan",               47.33, -2.87, "Hoëdic",     "bretonne", 9),
    ("brehat",    "Île-de-Bréhat, Côtes-d'Armor",   48.85, -3.00, "Bréhat",     "bretonne", 8),
    ("yeu",       "Île d'Yeu, Vendée",              46.71, -2.34, "île d'Yeu",  "atlantique", 7.5),
    ("chausey",   "Îles Chausey, Granville",        48.87, -1.82, "Chausey",    "normande", 8.5),
    ("jersey",    "Jersey",                         49.21, -2.13, "Jersey",     "anglo-normande", 6.5),
    ("guernesey", "Guernsey",                       49.46, -2.58, "Guernesey",  "anglo-normande", 6.5),
    ("aurigny",   "Alderney",                       49.71, -2.20, "Aurigny",    "anglo-normande", 8),
    ("sercq",     "Sark",                           49.43, -2.36, "Sercq",      "anglo-normande", 8.5),
]

TOL_POS = 0.35        # degrés : au-delà, ce n'est pas l'île demandée
TOL_SIMPL = 0.00035   # ~35 m : suffisant au zoom maximal de l'app (11)


def nominatim(q):
    url = (NOMINATIM + "?format=jsonv2&polygon_geojson=1&limit=6&q="
           + urllib.parse.quote(q))
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=60))


def anneaux(geom):
    """Polygon/MultiPolygon -> liste d'anneaux extérieurs en [lat, lon]."""
    polys = ([geom["coordinates"]] if geom["type"] == "Polygon"
             else geom["coordinates"])
    return [[[round(c[1], 5), round(c[0], 5)] for c in p[0]] for p in polys]


def simplifie_anneau(ring, tol):
    """Douglas-Peucker sur un contour FERMÉ.

    Appliqué tel quel à un anneau, l'algorithme part d'un segment de longueur
    nulle (premier point = dernier) : toutes les distances valent 0, et l'île
    entière se réduit à deux points. On coupe donc l'anneau en deux au point le
    plus éloigné du premier, on simplifie chaque moitié, puis on referme.
    """
    pts = ring[:-1] if ring[0] == ring[-1] else ring[:]
    if len(pts) < 4:
        return ring
    p0 = pts[0]
    loin = max(range(len(pts)),
               key=lambda i: (pts[i][0] - p0[0]) ** 2 + (pts[i][1] - p0[1]) ** 2)
    a = simplifie(pts[:loin + 1], tol)
    b = simplifie(pts[loin:] + [p0], tol)
    return a[:-1] + b


def simplifie(pts, tol):
    """Douglas-Peucker, comme pour les tracés de fleuves."""
    if len(pts) < 3:
        return pts
    dmax, imax = 0.0, 0
    (y0, x0), (y1, x1) = pts[0], pts[-1]
    for i in range(1, len(pts) - 1):
        y, x = pts[i]
        num = abs((x1 - x0) * (y0 - y) - (x0 - x) * (y1 - y0))
        den = math.hypot(x1 - x0, y1 - y0) or 1e-12
        d = num / den
        if d > dmax:
            dmax, imax = d, i
    if dmax <= tol:
        return [pts[0], pts[-1]]
    return (simplifie(pts[:imax + 1], tol)[:-1] + simplifie(pts[imax:], tol))


def main():
    out, total_avant, total_apres = {}, 0, 0
    for iid, q, lat, lon, label, groupe, minz in ILES:
        res = nominatim(q)
        # Contrôle de position : « Jersey » sort d'abord un comté d'Illinois.
        # Et le bon nom ne suffit pas : « Île de Groix » ramène un *parking*
        # de l'île, polygone parfaitement placé mais large de 40 m. D'où le
        # filtrage sur le type d'objet, avec repli sur la commune homonyme.
        plausibles = [r for r in res
                      if r.get("geojson", {}).get("type") in ("Polygon",
                                                              "MultiPolygon")
                      and abs(float(r["lat"]) - lat) < TOL_POS
                      and abs(float(r["lon"]) - lon) < TOL_POS]
        garde = (next((r for r in plausibles
                       if r.get("type") in ("island", "islet", "archipelago")),
                      None)
                 or next((r for r in plausibles
                          if r.get("type") in ("administrative", "territory")),
                         None))
        if not garde:
            print(f"!! {iid}: aucun contour plausible "
                  f"({[r.get('display_name','')[:40] for r in res]})")
            continue
        rings = anneaux(garde["geojson"])
        total_avant += sum(len(r) for r in rings)
        rings = [simplifie_anneau(r, TOL_SIMPL) for r in rings]
        rings = [r for r in rings if len(r) >= 4]
        total_apres += sum(len(r) for r in rings)
        out[iid] = {"name": label, "group": groupe, "minZ": minz,
                    "at": [lat, lon], "rings": rings,
                    "osm": f"{garde.get('osm_type')}/{garde.get('osm_id')}"}
        print(f"{iid:11} {garde['display_name'][:44]:46} "
              f"{len(rings)} anneau(x), {sum(len(r) for r in rings)} pts")
        time.sleep(1.2)   # politique d'usage de Nominatim : 1 requête/s

    p = os.path.join(ROOT, "data", "iles.json")
    json.dump(out, open(p, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"\n{len(out)} îles, {total_avant} -> {total_apres} points, "
          f"{os.path.getsize(p) // 1024} Ko -> {p}")


if __name__ == "__main__":
    main()
