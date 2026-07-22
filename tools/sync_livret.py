# -*- coding: utf-8 -*-
"""
Aligne les caractéristiques de feu sur la source officielle (livret DIRM NAMO).

Pour les 20 phares bretons présents dans l'app avant l'ajout du livret, les
données venaient de Wikipédia et divergent du livret officiel sur plusieurs
points réels (période des Sept-Îles, de Batz, de Kéréon ; nature du feu des
Héaux ; plusieurs portées). Le livret fait foi : on remplace `feux` et
`portee`, et on recalcule `sig` (animation) pour toutes les entrées issues
du livret.
"""
import json, os, re, sys

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import importlib
import fetch_phares
importlib.reload(fetch_phares)
from fetch_phares import parse_feux

# phares déjà présents avant le livret -> nom dans le livret
PRE = {
    "frehel": "Cap Fréhel", "heaux": "Héaux de Bréhat", "sept-iles": "Sept-Îles",
    "ploumanach": "Mean Ruz", "batz": "Île de Batz", "ile-vierge": "Île Vierge",
    "le-four": "Four", "jument": "La Jument", "stiff": "Stiff",
    "creach": "Créac'h", "kereon": "Kéréon", "saint-mathieu": "Saint-Mathieu",
    "petit-minou": "Petit Minou", "ar-men": "Ar-Men", "la-vieille": "Vieille",
    "eckmuhl": "Eckmühl", "port-navalo": "Port Navalo", "poulains": "Poulains",
    "goulphar": "Goulphar", "pilier": "Pilier",
}

liv = {x["nom"]: x for x in json.load(
    open(os.path.join(HERE, "livret_phares.json"), encoding="utf-8"))}
geo = json.load(open(os.path.join(HERE, "livret_geo.json"), encoding="utf-8"))

pe = os.path.join(ROOT, "js", "phares_extra.js")
raw = open(pe, encoding="utf-8").read()
data = json.loads(re.search(r"=\s*(\{.*\});", raw, re.S).group(1))

maj_pre, maj_sig = 0, 0

# 1) bascule des 20 pré-existants sur le livret (feu + portée)
for pid, nom in PRE.items():
    x = liv[nom]
    e = data[pid]
    if x["feu"] and e.get("feux") != x["feu"]:
        e["feux"] = x["feu"]
        maj_pre += 1
    if x["portee"]:
        e["portee"] = x["portee"]
    e["src_feu"] = "DIRM NAMO 2025"

# 2) recalcul du signal pour toutes les entrées issues du livret
for pid in list(PRE) + list(geo):
    e = data[pid]
    sig = parse_feux(e.get("feux"))
    if sig != e.get("sig"):
        e["sig"] = sig
        maj_sig += 1

open(pe, "w", encoding="utf-8").write(
    "/* Donnees Wikipedia/Wikimedia Commons (licences libres, credits inclus)\n"
    "   + caracteristiques des feux du livret officiel DIRM NAMO 2025. */\n"
    '"use strict";\nconst PHARES_EXTRA = '
    + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")

print(f"feux realignes sur le livret : {maj_pre}")
print(f"signaux recalcules          : {maj_sig}")
