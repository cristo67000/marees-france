# -*- coding: utf-8 -*-
"""Contrôle que chaque page Wikipédia trouvée correspond bien au phare visé."""
import json, os, re, unicodedata

HERE = os.path.dirname(__file__)
geo = json.load(open(os.path.join(HERE, "livret_geo.json"), encoding="utf-8"))
livret = {x["n"]: x for x in
          json.load(open(os.path.join(HERE, "livret_phares.json"), encoding="utf-8"))}

VIDES = {"phare", "grand", "grands", "pointe", "ile", "des", "du", "de",
         "la", "le", "les", "saint"}


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", s)


douteux = []
for pid, g in geo.items():
    attendu = livret[g["n"]]["nom"]
    mots = [m for m in norm(attendu).split() if len(m) > 3 and m not in VIDES]
    trouve = norm(g["wiki"])
    ok = any(m in trouve for m in mots) if mots else True
    if not ok or g["suspect"]:
        douteux.append(pid)
        print(f"  {pid:20s} attendu={attendu!r:34s} -> trouve={g['wiki']!r} "
              f"({g['lat']}, {g['lon']})")

print()
print(f"A CORRIGER : {len(douteux)} / {len(geo)}")
print(douteux)
