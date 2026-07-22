# -*- coding: utf-8 -*-
"""
Répare les valeurs issues du PDF où l'extraction a inséré une espace dans
les décimales (« 27 ,10 mètres »), pour les phares du livret déjà injectés.
Met à jour hauteur/portee/optique/feux dans phares_extra.js et h dans phares.js.
"""
import json, os, re

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")

livret = {x["n"]: x for x in json.load(
    open(os.path.join(HERE, "livret_phares.json"), encoding="utf-8"))}
geo = json.load(open(os.path.join(HERE, "livret_geo.json"), encoding="utf-8"))

# --- phares_extra.js : champs texte ---
pe = os.path.join(ROOT, "js", "phares_extra.js")
raw = open(pe, encoding="utf-8").read()
data = json.loads(re.search(r"=\s*(\{.*\});", raw, re.S).group(1))

corr = 0
for pid, g in geo.items():
    x = livret[g["n"]]
    for champ, src in (("hauteur", "hauteur"), ("portee", "portee"),
                       ("feux", "feu"), ("optique", "optique")):
        if data[pid].get(champ) != x[src]:
            data[pid][champ] = x[src]
            corr += 1

open(pe, "w", encoding="utf-8").write(
    "/* Donnees Wikipedia/Wikimedia Commons (licences libres, credits inclus)\n"
    "   + donnees techniques du livret DIRM NAMO 2025 (faits bruts). */\n"
    '"use strict";\nconst PHARES_EXTRA = '
    + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
print(f"phares_extra.js : {corr} champs corriges")

# --- phares.js : hauteur numerique ---
pj = os.path.join(ROOT, "js", "phares.js")
src = open(pj, encoding="utf-8").read()
n = 0
for pid, g in geo.items():
    h = livret[g["n"]]["hauteur"]
    m = re.search(r"(\d+(?:[.,]\d+)?)", h or "")
    if not m:
        continue
    val = float(m.group(1).replace(",", "."))
    pat = r'(\{ id: "' + re.escape(pid) + r'",[^\n]*?)h: [\d.]+'
    new, k = re.subn(pat, lambda mm: mm.group(1) + f"h: {val}", src)
    if k:
        src, _ = new, None
        n += k
open(pj, "w", encoding="utf-8").write(src)
print(f"phares.js : {n} hauteurs mises a jour")

# controle
apres = json.loads(re.search(r"=\s*(\{.*\});",
                             open(pe, encoding="utf-8").read(), re.S).group(1))
susp = [(k, apres[k]["hauteur"]) for k in geo
        if apres[k]["hauteur"] and len(re.findall(r"\d+(?:[.,]\d+)?",
                                                  apres[k]["hauteur"])) > 1]
print("hauteurs encore ambigues :", susp or "AUCUNE")
