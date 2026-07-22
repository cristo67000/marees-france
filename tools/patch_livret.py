# -*- coding: utf-8 -*-
"""
Corrige les 7 phares mal appariés par la recherche automatique et
re-télécharge leur photo. Vérifié manuellement page par page.
"""
import json, os, re, time, urllib.parse, urllib.request

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
API = "https://fr.wikipedia.org/w/api.php"
UA = {"User-Agent": "MareesFranceApp/1.0 (usage personnel; cristo67000@gmail.com)"}
GEO = os.path.join(HERE, "livret_geo.json")

# id -> (titre exact vérifié, lat, lon, photo_fiable)
# photo_fiable=False : pas d'article dédié au phare, la photo de la page
# représenterait l'île/le lieu-dit -> on n'en met pas (coords approchées).
CORRECTIONS = {
    "pen-men":      ("Phare de Pen-Men", 47.6475, -3.509166, True),
    "four-croisic": ("Phare du plateau du Four", 47.29778, -2.63417, True),
    "lanildut":     ("Feu de l'Aber-Ildut", 48.471119, -4.759188, True),
    "morees":       ("Balise des Morées", 47.2508, -2.2169, True),
    "corbeaux":     ("Phare de la pointe des Corbeaux", 46.69, -2.285, True),
    # sans article dédié : coordonnées de l'île / du lieu-dit (~1 km près)
    "goulenez":     ("Île de Sein", 48.0367, -4.8494, False),
    "fromentine":   ("Fromentine", 46.891, -2.137, False),
}


def api(params):
    url = API + "?" + urllib.parse.urlencode(dict(params, format="json"))
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                timeout=30) as r:
        return json.load(r)


def photo(title, pid):
    d = api({"action": "query", "titles": title, "redirects": 1,
             "prop": "pageimages", "piprop": "thumbnail|name",
             "pithumbsize": 320})
    page = next(iter(d["query"]["pages"].values()))
    thumb = page.get("thumbnail", {}).get("source")
    if not thumb:
        return None, None
    rel = f"photos/{pid}.jpg"
    with urllib.request.urlopen(urllib.request.Request(thumb, headers=UA),
                                timeout=60) as r:
        open(os.path.join(ROOT, rel), "wb").write(r.read())
    credit = None
    try:
        d2 = api({"action": "query", "titles": "File:" + page["pageimage"],
                  "prop": "imageinfo", "iiprop": "extmetadata"})
        meta = next(iter(d2["query"]["pages"].values()))["imageinfo"][0]["extmetadata"]
        artist = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", ""))[:60].strip()
        lic = meta.get("LicenseShortName", {}).get("value", "")
        credit = ", ".join(x for x in (artist, lic) if x)
    except Exception:
        pass
    return rel, credit


geo = json.load(open(GEO, encoding="utf-8"))
for pid, (title, lat, lon, fiable) in CORRECTIONS.items():
    g = geo[pid]
    g.update({"wiki": title, "lat": lat, "lon": lon, "suspect": False,
              "approx": not fiable})
    if fiable:
        img, credit = photo(title, pid)
        g["img"], g["credit"] = img, credit
    else:
        # supprime une éventuelle photo trompeuse déjà téléchargée
        old = os.path.join(ROOT, f"photos/{pid}.jpg")
        if os.path.exists(old):
            os.remove(old)
        g["img"], g["credit"] = None, None
    print(f"{pid:16s} {lat:9.5f} {lon:9.5f} "
          f"{'photo' if g['img'] else 'SANS photo (coords approchees)':30s} {title}")
    time.sleep(0.3)

json.dump(geo, open(GEO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
sans_coord = [k for k, v in geo.items() if v["lat"] is None]
print(f"\n{len(geo)} phares | sans coordonnees : {sans_coord or 'AUCUN'}")
