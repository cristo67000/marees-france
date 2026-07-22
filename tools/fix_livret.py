# -*- coding: utf-8 -*-
"""Recherche ciblée des phares mal appariés : affiche les candidats + coords."""
import json, urllib.parse, urllib.request

API = "https://fr.wikipedia.org/w/api.php"
UA = {"User-Agent": "MareesFranceApp/1.0 (usage personnel; cristo67000@gmail.com)"}

# id -> (requête, zone attendue (lat_min, lat_max, lon_min, lon_max))
CAS = {
    "pen-men":      ("phare Pen Men Groix", (47.5, 47.8, -3.7, -3.2)),
    "four-croisic": ("phare du Four Le Croisic", (47.2, 47.4, -2.7, -2.4)),
    "goulenez":     ("phare Goulenez île de Sein", (47.9, 48.2, -5.0, -4.7)),
    "lanildut":     ("phare Lanildut", (48.3, 48.6, -4.9, -4.6)),
    "morees":       ("phare des Morées Saint-Nazaire", (47.1, 47.4, -2.4, -2.0)),
    "fromentine":   ("phare de Fromentine Vendée", (46.7, 47.0, -2.3, -2.0)),
    "corbeaux":     ("phare des Corbeaux île d'Yeu", (46.6, 46.8, -2.5, -2.2)),
}


def api(params):
    url = API + "?" + urllib.parse.urlencode(dict(params, format="json"))
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.load(r)


for pid, (q, box) in CAS.items():
    print(f"=== {pid}  (attendu lat {box[0]}..{box[1]}, lon {box[2]}..{box[3]})")
    try:
        d = api({"action": "query", "list": "search", "srsearch": q, "srlimit": 6})
        titres = [h["title"] for h in d["query"]["search"]]
        if not titres:
            print("   aucun resultat"); continue
        d2 = api({"action": "query", "titles": "|".join(titres),
                  "prop": "coordinates", "redirects": 1})
        pages = d2["query"]["pages"]
        for p in pages.values():
            c = (p.get("coordinates") or [{}])[0]
            lat, lon = c.get("lat"), c.get("lon")
            dans = (lat is not None and box[0] <= lat <= box[1]
                    and box[2] <= lon <= box[3])
            flag = "  <== OK" if dans else ""
            print(f"   {p['title'][:46]:46s} {str(lat)[:9]:9s} {str(lon)[:9]:9s}{flag}")
    except Exception as e:
        print("   erreur:", e)
    print()
