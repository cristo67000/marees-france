# -*- coding: utf-8 -*-
"""
Complète les phares du livret DIRM NAMO avec coordonnées + photo Wikipédia.

Contrôle de cohérence : les coordonnées doivent tomber dans la façade
Bretagne / Pays de la Loire, sinon l'entrée est signalée (homonymes).

Sortie : tools/livret_geo.json  (+ photos/<id>.jpg)
"""
import json, os, re, time, urllib.parse, urllib.request

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
API = "https://fr.wikipedia.org/w/api.php"
UA = {"User-Agent": "MareesFranceApp/1.0 (usage personnel; cristo67000@gmail.com)"}
OUT = os.path.join(HERE, "livret_geo.json")

# façade DIRM NAMO (lat_min, lat_max, lon_min, lon_max), marge large
BBOX = (46.0, 49.3, -5.6, -1.0)

# n° livret -> (id app, titre Wikipédia)
CIBLES = {
    1: ("pierre-herpin", "Phare de la Pierre de Herpin"),
    2: ("rochebonne", "Phare de Rochebonne"),
    3: ("balue", "Phare de la Balue"),
    4: ("bas-sablons", "Phare des Bas-Sablons"),
    5: ("grand-jardin", "Phare du Grand Jardin"),
    7: ("grand-lejon", "Phare du Grand Léjon"),
    8: ("rosedo", "Phare du Rosédo"),
    9: ("roches-douvres", "Phare des Roches-Douvres"),
    11: ("bodic", "Phare de Bodic"),
    14: ("triagoz", "Phare des Triagoz"),
    15: ("la-lande", "Phare de la Lande"),
    16: ("roscoff-ph", "Phare de Roscoff"),
    18: ("pontusval", "Phare de Pontusval"),
    19: ("lanvaon", "Phare de Lanvaon"),
    21: ("ile-wrach", "Phare de l'île Wrac'h"),
    26: ("nividic", "Phare de Nividic"),
    28: ("lanildut", "Phare de Lanildut"),
    29: ("trezien", "Phare de Trézien"),
    30: ("kermorvan", "Phare de Kermorvan"),
    31: ("pierres-noires", "Phare des Pierres Noires"),
    34: ("portzic", "Phare du Portzic"),
    35: ("millier", "Phare du Millier"),
    36: ("tevennec", "Phare de Tévennec"),
    38: ("goulenez", "Phare de Goulenez"),
    41: ("sainte-marine", "Phare de Sainte-Marine"),
    42: ("benodet", "Phare de Bénodet"),
    43: ("moutons", "Phare de l'île aux Moutons"),
    44: ("penfret", "Phare de Penfret"),
    45: ("pen-men", "Phare de Pen Men"),
    46: ("pointe-des-chats", "Phare de la Pointe des Chats"),
    47: ("port-maria", "Phare de Port-Maria"),
    48: ("teignouse", "Phare de la Teignouse"),
    52: ("kerdonis", "Phare de Kerdonis"),
    53: ("grands-cardinaux", "Phare des Grands Cardinaux"),
    54: ("penlan", "Phare de Penlan"),
    55: ("four-croisic", "Phare du Four (Le Croisic)"),
    56: ("morees", "Phare des Morées"),
    57: ("aiguillon", "Phare de l'Aiguillon"),
    58: ("grand-charpentier", "Phare du Grand Charpentier"),
    59: ("banche", "Phare de la Banche"),
    60: ("pointe-saint-gildas", "Phare de la pointe Saint-Gildas"),
    62: ("pointe-des-dames", "Phare de la Pointe des Dames"),
    63: ("fromentine", "Phare de Fromentine"),
    64: ("yeu", "Grand phare de l'île d'Yeu"),
    65: ("corbeaux", "Phare des Corbeaux"),
    66: ("barges", "Phare des Barges"),
    67: ("armandeche", "Phare de l'Armandèche"),
    68: ("grouin-du-cou", "Phare du Grouin du Cou"),
}


def api(params):
    url = API + "?" + urllib.parse.urlencode(dict(params, format="json"))
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def resolve(title):
    """Titre exact, en suivant redirections ; sinon recherche."""
    d = api({"action": "query", "titles": title, "redirects": 1})
    page = next(iter(d["query"]["pages"].values()))
    if "missing" not in page:
        return page["title"]
    d = api({"action": "query", "list": "search",
             "srsearch": title + " phare", "srlimit": 3})
    for h in d["query"]["search"]:
        if "phare" in h["title"].lower():
            return h["title"]
    hits = d["query"]["search"]
    return hits[0]["title"] if hits else None


def geo_and_photo(title, pid):
    d = api({"action": "query", "titles": title, "redirects": 1,
             "prop": "coordinates|pageimages",
             "piprop": "thumbnail|name", "pithumbsize": 320})
    page = next(iter(d["query"]["pages"].values()))
    coord = (page.get("coordinates") or [{}])[0]
    lat, lon = coord.get("lat"), coord.get("lon")
    thumb = page.get("thumbnail", {}).get("source")
    imgname = page.get("pageimage")
    img = credit = None
    if thumb:
        os.makedirs(os.path.join(ROOT, "photos"), exist_ok=True)
        rel = f"photos/{pid}.jpg"
        req = urllib.request.Request(thumb, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            open(os.path.join(ROOT, rel), "wb").write(r.read())
        img = rel
        try:
            d2 = api({"action": "query", "titles": "File:" + imgname,
                      "prop": "imageinfo", "iiprop": "extmetadata"})
            meta = next(iter(d2["query"]["pages"].values()))["imageinfo"][0]["extmetadata"]
            artist = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", ""))[:60].strip()
            lic = meta.get("LicenseShortName", {}).get("value", "")
            credit = ", ".join(x for x in (artist, lic) if x)
        except Exception:
            pass
    return lat, lon, img, credit


def main():
    res, alertes = {}, []
    for n, (pid, title) in CIBLES.items():
        try:
            real = resolve(title)
            if not real:
                alertes.append(f"{pid}: page introuvable"); continue
            lat, lon, img, credit = geo_and_photo(real, pid)
            hors = lat is None or not (BBOX[0] <= lat <= BBOX[1]
                                       and BBOX[2] <= lon <= BBOX[3])
            if hors:
                alertes.append(f"{pid}: coords suspectes {lat},{lon} ({real})")
            res[pid] = {"n": n, "wiki": real, "lat": lat, "lon": lon,
                        "img": img, "credit": credit, "suspect": hors}
            print(f"{pid:20s} {str(lat)[:8]:8s} {str(lon)[:8]:8s} "
                  f"{'IMG' if img else '---'} {'!! ' if hors else '   '}{real[:40]}",
                  flush=True)
            time.sleep(0.3)
        except Exception as e:
            alertes.append(f"{pid}: {e}")
            print(f"!! {pid}: {e}", flush=True)
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n{len(res)} fiches -> {OUT}")
    if alertes:
        print("\nALERTES:")
        for a in alertes:
            print("  -", a)


if __name__ == "__main__":
    main()
