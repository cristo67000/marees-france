# -*- coding: utf-8 -*-
"""
Enrichissement des phares depuis Wikipédia (fr) / Wikimedia Commons :
photo (miniature 320 px, licence libre + crédit), construction, mise en
service, hauteur, portée, feux (caractéristique lumineuse), optique, nombre
de marches (extrait du texte de l'article).

Sorties :
  - photos/<id>.jpg
  - js/phares_extra.js  (const PHARES_EXTRA = {...})
"""
import json, os, re, sys, time, html, urllib.request, urllib.parse

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
API = "https://fr.wikipedia.org/w/api.php"
UA = {"User-Agent": "MareesFranceApp/1.0 (usage personnel; contact: cristo67000@gmail.com)"}

TITLES = {
    "risban": "Phare du Risban", "calais-ph": "Phare de Calais",
    "gris-nez": "Phare du cap Gris-Nez", "alprech": "Phare d'Alprech",
    "touquet": "Phare de la Canche", "cayeux": "Phare de Cayeux",
    "ailly": "Phare d'Ailly", "antifer": "Phare d'Antifer",
    "la-heve": "Phare de la Hève", "gatteville": "Phare de Gatteville",
    "cap-levi": "Phare du cap Lévi", "goury": "Phare de la Hague",
    "carteret-ph": "Phare de Carteret", "granville-ph": "Phare de Granville",
    "frehel": "Phare du cap Fréhel", "heaux": "Phare des Héaux de Bréhat",
    "ploumanach": "Phare de Ploumanac'h", "sept-iles": "Phare des Sept-Îles",
    "batz": "Phare de l'île de Batz", "ile-vierge": "Phare de l'île Vierge",
    "le-four": "Phare du Four", "stiff": "Phare du Stiff",
    "creach": "Phare du Créac'h", "jument": "Phare de la Jument",
    "kereon": "Phare de Kéréon", "saint-mathieu": "Phare de Saint-Mathieu",
    "petit-minou": "Phare du Petit Minou", "ar-men": "Phare d'Ar-Men",
    "la-vieille": "Phare de la Vieille", "eckmuhl": "Phare d'Eckmühl",
    "goulphar": "Phare de Goulphar", "poulains": "Phare des Poulains",
    "port-navalo": "Phare de Port-Navalo", "pilier": "Phare du Pilier",
    "baleines": "Phare des Baleines", "chassiron": "Phare de Chassiron",
    "coubre": "Phare de la Coubre", "cordouan": "Phare de Cordouan",
    "grave": "Phare de Grave", "cap-ferret": "Phare du cap Ferret",
    "contis": "Phare de Contis", "biarritz": "Phare de Biarritz",
    "cap-bear": "Phare du cap Béar", "sete-ph": "Phare du môle Saint-Louis",
    "espiguette": "Phare de l'Espiguette", "faraman": "Phare de Faraman",
    "planier": "Phare du Planier", "porquerolles": "Phare du cap d'Arme",
    "camarat": "Phare du cap Camarat", "garoupe": "Phare de la Garoupe",
    "cap-ferrat-ph": "Phare du cap Ferrat", "revellata": "Phare de la Revellata",
    "sanguinaires": "Phare des Sanguinaires", "pertusato": "Phare de Pertusato",
    "alistro": "Phare d'Alistro",
}

FIELDS = ["Construction", "Mise en service", "Hauteur", "Élévation",
          "Hauteur focale", "Portée", "Feux", "Optique", "Automatisation"]


def api(params):
    params = dict(params, format="json")
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_bytes(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def strip_html(s):
    s = re.sub(r"<style.*?</style>", "", s, flags=re.S)
    s = re.sub(r"<sup[^>]*class=\"reference\".*?</sup>", "", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).replace(" ,", ",").strip(" ,;")


def resolve_title(title):
    """Titre exact (suit les redirections) ou recherche."""
    d = api({"action": "query", "titles": title, "redirects": 1})
    pages = d["query"]["pages"]
    page = next(iter(pages.values()))
    if "missing" not in page:
        return page["title"]
    d = api({"action": "query", "list": "search", "srsearch": title,
             "srlimit": 1})
    hits = d["query"]["search"]
    return hits[0]["title"] if hits else None


def get_photo(title, pid):
    d = api({"action": "query", "titles": title, "prop": "pageimages",
             "piprop": "thumbnail|name", "pithumbsize": 320, "redirects": 1})
    page = next(iter(d["query"]["pages"].values()))
    thumb = page.get("thumbnail", {}).get("source")
    imgname = page.get("pageimage")
    if not thumb:
        return None, None
    os.makedirs(os.path.join(ROOT, "photos"), exist_ok=True)
    ext = ".jpg"
    path = os.path.join(ROOT, "photos", pid + ext)
    data = fetch_bytes(thumb)
    open(path, "wb").write(data)
    credit = ""
    if imgname:
        try:
            d2 = api({"action": "query", "titles": "File:" + imgname,
                      "prop": "imageinfo", "iiprop": "extmetadata"})
            p2 = next(iter(d2["query"]["pages"].values()))
            meta = p2["imageinfo"][0]["extmetadata"]
            artist = strip_html(meta.get("Artist", {}).get("value", ""))[:60]
            lic = meta.get("LicenseShortName", {}).get("value", "")
            credit = ", ".join(x for x in (artist, lic) if x)
        except Exception:
            pass
    return "photos/" + pid + ext, credit


def get_infobox_and_text(title):
    d = api({"action": "parse", "page": title, "prop": "text",
             "redirects": 1})
    htm = d["parse"]["text"]["*"]
    fields = {}
    for m in re.finditer(
            r"<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>", htm, flags=re.S):
        key = strip_html(m.group(1))
        for f in FIELDS:
            if key.lower().startswith(f.lower()):
                val = strip_html(m.group(2))
                if val and f not in fields:
                    fields[f] = val[:120]
    text = strip_html(htm)
    marches = None
    m = re.search(r"(\d{2,3})\s+marches", text)
    if m and 40 <= int(m.group(1)) <= 500:
        marches = int(m.group(1))
    return fields, marches


_NOMBRES = [("vingt-cinq", "25"), ("vingt", "20"), ("trente", "30"),
            ("quinze", "15"), ("douze", "12"), ("dix", "10"),
            ("quatre", "4"), ("cinq", "5"), ("trois", "3"), ("deux", "2"),
            ("une", "1"), ("un", "1"), ("six", "6"), ("sept", "7"),
            ("huit", "8"), ("neuf", "9")]


def parse_feux(s):
    """'2 éclats blancs, 10 s', 'Fl(2) W 10s', 'FI(2)' (coquille), 'deux
    éclats', '2+1 occ., 12 s', '20 secondes' -> {mode, n, n2, color, period}."""
    if not s:
        return None
    t = s.lower()
    for w, d in _NOMBRES:
        t = re.sub(r"\b" + w + r"\b", d, t)
    # couleur : blanc prioritaire (feux à secteurs : le blanc est le feu
    # principal), sinon mots français puis lettres internationales
    if "blanc" in t or re.search(r"\bw\b", t):
        color = "blanc"
    elif "rouge" in t or re.search(r"\br\b", t):
        color = "rouge"
    elif "vert" in t or re.search(r"\bg\b", t):
        color = "vert"
    else:
        color = "blanc"
    per = None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*s(?:ec|\b)", t)
    if m:
        per = float(m.group(1).replace(",", "."))
    n, n2 = 1, 0
    # 'fi' = coquille fréquente pour 'fl' ; 'gp.fl.(2)' ; '(2+1) occultations'
    m = (re.search(r"(?:gp[.\s]*)?(?:fl|fi|oc|occ|iso|q)[.\s]*\(\s*(\d+)(?:\s*\+\s*(\d+))?\s*\)", t)
         or re.search(r"\(?(\d+)(?:\s*\+\s*(\d+))?\)?\s*(?:éclats?|occultations?|occ\b)", t)
         or re.search(r"\((\d+)\s*\+\s*(\d+)\)", t)
         or re.search(r"group[ée]s?\s+par\s+(\d+)", t))
    if m:
        n = int(m.group(1))
        n2 = int(m.group(2)) if m.lastindex and m.lastindex >= 2 and m.group(2) else 0
    if "occultation" in t or re.search(r"\bocc?\b[.\s]|\boc[c]?[.\s]*\(", t):
        mode = "occ"
    elif "isophase" in t or re.search(r"\biso\b", t):
        mode = "iso"
    elif "fixe" in t:
        mode = "fixe"
    elif "scintillant" in t or re.search(r"\bq\b", t):
        mode, n = "flash", max(n, 6)
    else:
        mode = "flash"
    if per is None:
        per = 5 if mode == "flash" else 10
    return {"mode": mode, "n": n, "n2": n2, "color": color, "period": per}


def main(only=None):
    out = {}
    for pid, title in TITLES.items():
        if only and pid not in only:
            continue
        try:
            real = resolve_title(title)
            if not real:
                print(f"!! {pid}: page introuvable"); continue
            img, credit = get_photo(real, pid)
            fields, marches = get_infobox_and_text(real)
            sig = parse_feux(fields.get("Feux"))
            out[pid] = {
                "wiki": real, "img": img, "credit": credit,
                "construction": fields.get("Construction"),
                "service": fields.get("Mise en service"),
                "hauteur": fields.get("Hauteur"),
                "portee": fields.get("Portée"),
                "feux": fields.get("Feux"),
                "optique": fields.get("Optique"),
                "marches": marches,
                "sig": sig,
            }
            size = os.path.getsize(os.path.join(ROOT, img)) // 1024 if img else 0
            print(f"{pid:16s} {real[:34]:34s} img={size:3d}Ko marches={marches} "
                  f"feux={fields.get('Feux', '')[:48]}")
            time.sleep(0.3)
        except Exception as e:
            print(f"!! {pid}: {e}")
    mode = "r+" if only and os.path.exists(os.path.join(ROOT, "js", "phares_extra.js")) else "w"
    path = os.path.join(ROOT, "js", "phares_extra.js")
    if only and os.path.exists(path):
        cur = re.search(r"=\s*(\{.*\});", open(path, encoding="utf-8").read(), re.S)
        if cur:
            old = json.loads(cur.group(1))
            old.update(out)
            out = old
    body = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    open(path, "w", encoding="utf-8").write(
        '/* Données Wikipédia/Wikimedia Commons (licences libres, crédits inclus). */\n'
        '"use strict";\nconst PHARES_EXTRA = ' + body + ";\n")
    print(f"\nEcrit: {path} ({len(out)} phares)")


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
