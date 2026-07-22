# -*- coding: utf-8 -*-
"""Rétablit les noms français corrects (articles) des phares du livret."""
import os, re

NOMS = {
    "pierre-herpin": "Phare de la Pierre de Herpin",
    "rochebonne": "Phare de Rochebonne",
    "balue": "Phare de la Balue",
    "bas-sablons": "Phare des Bas-Sablons",
    "grand-jardin": "Phare du Grand Jardin",
    "grand-lejon": "Phare du Grand Léjon",
    "rosedo": "Phare du Rosédo (Bréhat)",
    "roches-douvres": "Phare des Roches-Douvres",
    "bodic": "Phare de Bodic",
    "triagoz": "Phare des Triagoz",
    "la-lande": "Phare de la Lande",
    "roscoff-ph": "Phare de Roscoff",
    "pontusval": "Phare de Pontusval",
    "lanvaon": "Phare de Lanvaon",
    "ile-wrach": "Phare de l'île Wrac'h",
    "nividic": "Phare de Nividic (Ouessant)",
    "lanildut": "Feu de l'Aber-Ildut (Lanildut)",
    "trezien": "Phare de Trézien",
    "kermorvan": "Phare de Kermorvan",
    "pierres-noires": "Phare des Pierres Noires",
    "portzic": "Phare du Portzic",
    "millier": "Phare de la pointe du Millier",
    "tevennec": "Phare de Tévennec",
    "goulenez": "Grand phare de l'île de Sein (Goulenez)",
    "sainte-marine": "Phare de Sainte-Marine",
    "benodet": "Phare de Bénodet (la Pyramide)",
    "moutons": "Phare de l'île aux Moutons",
    "penfret": "Phare de Penfret (Glénan)",
    "pen-men": "Phare de Pen Men (Groix)",
    "pointe-des-chats": "Phare de la pointe des Chats (Groix)",
    "port-maria": "Phare de Port-Maria (Quiberon)",
    "teignouse": "Phare de la Teignouse",
    "kerdonis": "Phare de Kerdonis (Belle-Île)",
    "grands-cardinaux": "Phare des Grands Cardinaux",
    "penlan": "Phare de Penlan",
    "four-croisic": "Phare du plateau du Four (Le Croisic)",
    "morees": "Phare des Morées",
    "aiguillon": "Phare d'Aiguillon",
    "grand-charpentier": "Phare du Grand Charpentier",
    "banche": "Phare de la Banche",
    "pointe-saint-gildas": "Phare de la pointe Saint-Gildas",
    "pointe-des-dames": "Phare de la pointe des Dames (Noirmoutier)",
    "fromentine": "Phare de Fromentine",
    "yeu": "Grand phare de l'île d'Yeu",
    "corbeaux": "Phare de la pointe des Corbeaux (Yeu)",
    "barges": "Phare des Barges",
    "armandeche": "Phare de l'Armandèche",
    "grouin-du-cou": "Phare du Grouin du Cou",
}

p = os.path.join(os.path.dirname(__file__), "..", "js", "phares.js")
src = open(p, encoding="utf-8").read()
n = 0
for pid, nom in NOMS.items():
    pat = r'(\{ id: "' + re.escape(pid) + r'", name: ")[^"]*(")'
    src, k = re.subn(pat, lambda m: m.group(1) + nom + m.group(2), src)
    n += k
    if k != 1:
        print(f"  !! {pid} : {k} remplacement(s)")
open(p, "w", encoding="utf-8").write(src)
print(f"{n} noms corriges")
