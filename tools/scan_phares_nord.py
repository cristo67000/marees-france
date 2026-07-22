# -*- coding: utf-8 -*-
"""
Relevé des caractéristiques des phares MEMN manquants dans l'app.

Référence de la SÉLECTION : la liste alphabétique officielle des phares de la
DIRM Manche Est - Mer du Nord (21 phares, site sous licence Etalab 2.0) —
c'est elle qui dit quels phares existent et sont en service sur ces côtes.

Référence des CARACTÉRISTIQUES : les fiches techniques DIRM quand elles
existent (8 phares seulement), sinon les balises seamark d'OpenStreetMap,
tenues à jour d'après les listes officielles de feux. Wikipédia n'est utilisé
que pour l'histoire et la photo : il se trompe régulièrement sur les rythmes
et les portées (cf. contrôles menés sur la façade NAMO).

Sortie : tools/osm_phares_nord.json
"""
import json, os, time, urllib.request

HERE = os.path.dirname(__file__)
UA = {"User-Agent": "MareesFranceApp/1.0 (usage personnel; cristo67000@gmail.com)"}
MIROIRS = ["https://overpass-api.de/api/interpreter",
           "https://overpass.kumi.systems/api/interpreter"]


def overpass(q):
    """Overpass limite le débit par IP et répond alors 429 — ou 504 quand le
    créneau est saturé. On alterne les miroirs en espaçant les tentatives."""
    dernier = None
    for essai in range(6):
        url = MIROIRS[essai % len(MIROIRS)]
        try:
            req = urllib.request.Request(url, data=q.encode(), headers=UA)
            return json.load(urllib.request.urlopen(req, timeout=90))
        except urllib.error.HTTPError as e:
            if e.code not in (429, 504):
                raise
            dernier = e
            attente = 10 * (essai + 1)
            print(f"  {e.code} sur {url.split('/')[2]}, nouvelle tentative "
                  f"dans {attente} s")
            time.sleep(attente)
    raise dernier

# Les 7 phares de la liste DIRM MEMN absents de js/phares.js, avec une petite
# fenêtre autour de leur position connue (recherche ciblée = requête légère).
CIBLES = {
    "ault":          (50.1055, 1.4542, "Phare d'Ault", "Somme (80)"),
    "berck":         (50.3983, 1.5608, "Phare de Berck", "Pas-de-Calais (62)"),
    "carnot":        (50.7406, 1.5676, "Phare de la digue Carnot", "Pas-de-Calais (62)"),
    "ouistreham":    (49.2790, -0.2480, "Phare de Ouistreham", "Calvados (14)"),
    "ver-sur-mer":   (49.3401, -0.5189, "Phare de Ver-sur-Mer", "Calvados (14)"),
    "fort-ouest":    (49.6743, -1.6478, "Phare du Fort de l'Ouest", "Manche (50)"),
    "chausey":       (48.8695, -1.8224, "Phare de l'île Chausey", "Manche (50)"),
}
# Contrôle : la position enregistrée pour Cayeux (phare de Brighton) semble
# décalée d'environ 1,5 km vers l'ouest — à confronter à OSM.
CIBLES["cayeux-controle"] = (50.1943, 1.5121, "Phare de Brighton (Cayeux)", "Somme (80)")

D = 0.02  # ± ~2 km


def requete(lat, lon):
    # Une requête par cible : la même requête groupée sur 8 fenêtres fait
    # tomber Overpass en 504.
    # Valeurs exactes plutôt qu'une regex sur seamark:type : la regex n'utilise
    # aucun index et fait tomber Overpass en 504, même sur une petite fenêtre.
    bb = f"{lat - D},{lon - D},{lat + D},{lon + D}"
    filtres = "".join(
        f'nwr["seamark:type"="{v}"]({bb});'
        for v in ("light_major", "light_minor", "light_vessel", "light"))
    return ("[out:json][timeout:60];("
            + filtres
            + f'nwr["man_made"="lighthouse"]({bb});'
            ");out center tags;")


def main():
    elements = []
    for cle, (lat, lon, *_ ) in CIBLES.items():
        d = overpass(requete(lat, lon))
        print(f"{cle:16} {len(d['elements'])} éléments")
        elements += d["elements"]
        time.sleep(8)   # rester sous la limite de débit d'Overpass
    out = []
    for e in elements:
        t = e.get("tags", {})
        lat = e.get("lat") or e.get("center", {}).get("lat")
        lon = e.get("lon") or e.get("center", {}).get("lon")
        if lat is None:
            continue
        cible = min(CIBLES.items(),
                    key=lambda kv: abs(kv[1][0] - lat) + abs(kv[1][1] - lon))
        out.append({
            "cible": cible[0],
            "osm": f"{e['type']}/{e['id']}",
            "nom": t.get("name") or t.get("seamark:name") or "",
            "lat": round(lat, 4), "lon": round(lon, 4),
            "car": t.get("seamark:light:character")
                   or t.get("seamark:light:1:character"),
            "periode": t.get("seamark:light:period")
                       or t.get("seamark:light:1:period"),
            "portee": t.get("seamark:light:range")
                      or t.get("seamark:light:1:range"),
            "hauteur": t.get("seamark:light:height") or t.get("height"),
            "couleur": t.get("seamark:light:colour")
                       or t.get("seamark:light:1:colour"),
            "groupe": t.get("seamark:light:group")
                      or t.get("seamark:light:1:group"),
            "type": t.get("seamark:type"),
            "wikipedia": t.get("wikipedia"),
        })
    out.sort(key=lambda x: x["cible"])
    p = os.path.join(HERE, "osm_phares_nord.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(out)} feux relevés -> {p}")
    for x in out:
        if x["car"]:
            print(f"  {x['cible']:16} {x['nom'][:32]:34} {x['lat']:8.4f} "
                  f"{x['lon']:8.4f}  {x['car']}{x.get('groupe') or ''} "
                  f"{x['periode'] or '?'}s  {x['couleur'] or '?'}  "
                  f"p={x['portee'] or '?'}  h={x['hauteur'] or '?'}")


if __name__ == "__main__":
    main()
