# -*- coding: utf-8 -*-
"""
Construit dist/marees-france.html : l'application complète en UN SEUL fichier
(Leaflet, données des ports, fond de carte, moteur, styles inlinés).
À copier sur un téléphone et ouvrir avec Chrome/Firefox — fonctionne
entièrement hors-ligne, aucun serveur nécessaire.
"""
import base64, json, os, re

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")


def read(p):
    return open(os.path.join(ROOT, p), encoding="utf-8").read()


html = read("index.html")

# données inlinées avant les scripts
ports = json.dumps(json.loads(read("data/ports.json")),
                   ensure_ascii=False, separators=(",", ":"))
france = json.dumps(json.loads(read("data/france.geojson")),
                    separators=(",", ":"))
rivers = json.dumps(json.loads(read("data/rivers.json")),
                    ensure_ascii=False, separators=(",", ":"))
iles = json.dumps(json.loads(read("data/iles.json")),
                  ensure_ascii=False, separators=(",", ":"))
data_tag = ("<script>window.PORTS_DATA=" + ports +
            ";window.FRANCE_GEOJSON=" + france +
            ";window.RIVERS_DATA=" + rivers +
            ";window.ILES_DATA=" + iles + ";</script>")

# favicon en data-uri
icon_b64 = base64.b64encode(read("icons/icon.svg").encode()).decode()

html = re.sub(r'<link rel="manifest"[^>]*>\n?', "", html)
html = re.sub(r'<link rel="apple-touch-icon"[^>]*>\n?', "", html)
html = html.replace('<link rel="icon" href="icons/icon.svg" type="image/svg+xml">',
                    f'<link rel="icon" href="data:image/svg+xml;base64,{icon_b64}">')
html = html.replace('<link rel="stylesheet" href="lib/leaflet.css">',
                    "<style>\n" + read("lib/leaflet.css") + "\n</style>")
html = html.replace('<link rel="stylesheet" href="css/app.css">',
                    "<style>\n" + read("css/app.css") + "\n</style>")
html = html.replace('<script src="lib/leaflet.js"></script>',
                    data_tag + "\n<script>\n" + read("lib/leaflet.js") + "\n</script>")
for src in ("js/tide.js", "js/moon.js", "js/astro.js", "js/portinfo.js",
             "js/phares.js", "js/phares_extra.js", "js/labels.js",
             "js/app.js"):
    html = html.replace(f'<script src="{src}"></script>',
                        "<script>\n" + read(src) + "\n</script>")

# photos des phares -> data URI (l'app reste un fichier unique)
def _img(m):
    p = os.path.join(ROOT, "photos", m.group(1) + ".jpg")
    if not os.path.exists(p):
        return m.group(0)
    return ("data:image/jpeg;base64,"
            + base64.b64encode(open(p, "rb").read()).decode())

html = re.sub(r"photos/([a-z0-9-]+)\.jpg", _img, html)

# confidentialite.html n'existe pas à côté du fichier unique : le lien pointerait
# dans le vide. Le texte de la politique est de toute façon repris dans la boîte.
html = re.sub(r'\s*<p class="geo-note geo-lien">.*?</p>', "", html, flags=re.S)

assert "src=\"js/" not in html and "stylesheet" not in html, "inline incomplet"
assert "confidentialite.html" not in html, "lien mort dans le fichier unique"

out = os.path.join(ROOT, "dist", "marees-france.html")
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w", encoding="utf-8").write(html)
print(f"Ecrit: {out} ({os.path.getsize(out) / 1024:.0f} Ko)")
