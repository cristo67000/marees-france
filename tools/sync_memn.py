# -*- coding: utf-8 -*-
"""
Réaligne les caractéristiques des feux de la façade MEMN (Nord, Picardie,
Normandie) sur les sources officielles, par-dessus ce que fetch_phares.py a
moissonné dans Wikipédia.

Pourquoi : Wikipédia se trompe régulièrement sur les rythmes et les portées
(déjà constaté sur toute la façade NAMO). Ici deux erreurs franches :
  - Ouistreham : l'article donne « 1 occultation, 4 s », qui est le rythme d'un
    AUTRE feu de l'avant-port ; le phare bat 3+1 occultations en 12 s ;
  - fort de l'Ouest : « éclats réguliers », sans le groupe de 3.

Sources, par ordre d'autorité :
  1. fiches techniques de la DIRM Manche Est - Mer du Nord (licence Etalab 2.0)
     — n'existent que pour 8 phares de la façade, dont Ault ;
  2. balises seamark d'OpenStreetMap, tenues d'après les listes officielles de
     feux (relevées par tools/scan_phares_nord.py).
"""
import json, os, re

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")

# feux : libellé affiché ; sig : animation de la lanterne (mode, n éclats,
# n2 éclats du groupe secondaire, couleur, période en s).
OFFICIEL = {
    # Fiche technique DIRM MEMN (phare-de-ault-a116.html) : « 3 occultations
    # groupées 12 s », feu blanc et rouge, portée 17 milles, hauteur 28 m.
    "ault": {
        "feux": "Oc(3) WR 12s", "portee": "17 milles (31 km)", "hauteur": "28 m",
        "sig": {"mode": "occ", "n": 3, "n2": 0, "color": "blanc", "period": 12.0},
        "src": "DIRM MEMN",
    },
    # OSM : Oc(3+1) 12s, portée 17 M. Wikipédia donne le rythme d'un autre feu.
    "ouistreham": {
        "feux": "Oc(3+1) WR 12s", "portee": "17 milles (31 km)",
        "sig": {"mode": "occ", "n": 3, "n2": 1, "color": "blanc", "period": 12.0},
        "src": "OSM seamark",
    },
    # OSM : Fl(3) 15s, portée 24 M. Wikipédia omet le groupe de 3.
    "fort-ouest": {
        "feux": "Fl(3) WR 15s", "portee": "24 milles (44 km)",
        "sig": {"mode": "flash", "n": 3, "n2": 0, "color": "blanc",
                "period": 15.0},
        "src": "OSM seamark",
    },
    # Les quatre suivants : Wikipédia et OSM concordent, on normalise seulement
    # l'écriture du rythme (« FI » pour « Fl », « éclats blancs/ 5 s »…).
    "berck": {
        "feux": "Fl W 5s",
        "sig": {"mode": "flash", "n": 1, "n2": 0, "color": "blanc", "period": 5.0},
        "src": "Wikipédia = OSM",
    },
    "carnot": {
        "feux": "Fl(2+1) W 15s",
        "sig": {"mode": "flash", "n": 2, "n2": 1, "color": "blanc",
                "period": 15.0},
        "src": "Wikipédia = OSM",
    },
    "ver-sur-mer": {
        "feux": "Fl(3) W 15s",
        "sig": {"mode": "flash", "n": 3, "n2": 0, "color": "blanc",
                "period": 15.0},
        "src": "Wikipédia = OSM",
    },
    "chausey": {
        "feux": "Fl W 5s",
        "sig": {"mode": "flash", "n": 1, "n2": 0, "color": "blanc", "period": 5.0},
        "src": "Wikipédia = OSM",
    },
}


def main():
    path = os.path.join(ROOT, "js", "phares_extra.js")
    src = open(path, encoding="utf-8").read()
    data = json.loads(re.search(r"=\s*(\{.*\});", src, re.S).group(1))

    for pid, ref in OFFICIEL.items():
        if pid not in data:
            print(f"!! {pid} absent de phares_extra.js"); continue
        avant = data[pid].get("feux")
        for champ in ("feux", "portee", "hauteur", "sig"):
            if champ in ref:
                data[pid][champ] = ref[champ]
        marque = "=" if avant == ref["feux"] else "->"
        print(f"{pid:14} {str(avant)[:38]:40} {marque} {ref['feux']:16} "
              f"[{ref['src']}]")

    body = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    open(path, "w", encoding="utf-8").write(
        "/* Donnees Wikipedia/Wikimedia Commons (licences libres, credits inclus)\n"
        "   + caracteristiques des feux des livrets officiels DIRM NAMO 2025\n"
        "   et DIRM MEMN (facade Nord/Normandie). */\n"
        '"use strict";\nconst PHARES_EXTRA = ' + body + ";\n")
    print(f"\nEcrit: {path} ({len(data)} phares)")


if __name__ == "__main__":
    main()
