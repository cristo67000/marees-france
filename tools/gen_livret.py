# -*- coding: utf-8 -*-
"""
Génère les 48 nouvelles entrées de phares (livret DIRM NAMO) :
  - ajoute les objets dans js/phares.js
  - ajoute les fiches détaillées dans js/phares_extra.js

Sources : données factuelles du livret DIRM NAMO (hauteur, feu, portée,
optique, dates) + coordonnées et photos Wikipédia/Wikimedia Commons.
Les textes de présentation sont rédigés pour l'app (le livret est
© DIRM NAMO, sa prose n'est pas reprise).
"""
import json, os, re, sys

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
from fetch_phares import parse_feux  # réutilise le parseur de caractéristiques

DEPS = {
    "Ille-et-Vilaine": "Ille-et-Vilaine (35)", "Côtes-d'Armor": "Côtes-d'Armor (22)",
    "Finistère": "Finistère (29)", "Morbihan": "Morbihan (56)",
    "Loire-Atlantique": "Loire-Atlantique (44)", "Vendée": "Vendée (85)",
}

# id -> (rang de zoom, description rédigée pour l'app)
FICHES = {
    "pierre-herpin": (1, "Sentinelle de l'entrée de la baie du Mont-Saint-Michel, au large de la pointe du Grouin ; son embase évasée encaisse les vagues."),
    "rochebonne": (2, "Tour carrée d'après-guerre ; elle forme un alignement avec le Grand Jardin pour entrer à Saint-Malo par la Grande Porte."),
    "balue": (2, "Domine Saint-Servan au sud-est de Saint-Malo ; son feu vert directionnel balise le chenal intérieur."),
    "bas-sablons": (2, "À Saint-Servan, en alignement avec le phare de la Balue pour guider l'accès au port de Saint-Malo."),
    "grand-jardin": (1, "Dressé sur un récif devant Saint-Malo, reconstruit après sa destruction en 1944."),
    "grand-lejon": (2, "En pleine baie de Saint-Brieuc, à neuf milles au large ; sa tour rouge et blanche est un repère de la baie."),
    "rosedo": (2, "Au nord de l'île de Bréhat, il veille sur l'archipel et le chenal du Ferlas."),
    "roches-douvres": (1, "Le plus isolé des phares français : à mi-chemin entre Bréhat et Guernesey, en pleine Manche."),
    "bodic": (2, "Sur la rive gauche de l'estuaire du Trieux, il guide la remontée vers Lézardrieux."),
    "triagoz": (1, "Sur les récifs au nord de la baie de Lannion, face à la côte de granit rose."),
    "la-lande": (2, "En arrière du littoral léonard, il forme un alignement pour l'approche de Roscoff."),
    "roscoff-ph": (2, "Balise l'entrée du port de Roscoff, porte de l'île de Batz et des ferries d'Angleterre."),
    "pontusval": (2, "Petite tour carrée posée au milieu des chaos granitiques de Brignogan-Plages."),
    "lanvaon": (2, "Feu d'alignement arrière pour l'entrée dans l'Aber-Wrac'h, l'un des mouillages les plus sûrs du Léon."),
    "ile-wrach": (2, "Maison-phare sur l'îlot Wrac'h, à l'entrée de l'Aber-Wrac'h ; désormais lieu de résidence d'artistes."),
    "nividic": (1, "Le plus occidental des phares de France, à la pointe d'Ouessant ; il fut longtemps ravitaillé par téléphérique."),
    "lanildut": (2, "Feu de l'Aber-Ildut, à l'entrée du premier port goémonier d'Europe."),
    "trezien": (2, "À Plouarzel ; son feu directionnel guide les navires dans le chenal du Four."),
    "kermorvan": (1, "Au Conquet : le phare à terre le plus occidental de France, relié par un isthme étroit."),
    "pierres-noires": (1, "Sur un récif battu au sud-ouest de la mer d'Iroise, à l'entrée du goulet de Brest."),
    "portzic": (2, "Sur la rive nord du goulet de Brest, il commande l'entrée de la rade."),
    "millier": (2, "Maison-feu de la pointe du Millier, accrochée au cap Sizun au-dessus de la baie de Douarnenez."),
    "tevennec": (1, "Dans le raz de Sein, sur un îlot réputé maudit : ses gardiens y devinrent fous, il fut automatisé dès 1910."),
    "goulenez": (1, "Grand phare de l'île de Sein, reconstruit après-guerre ; il veille sur la chaussée de Sein."),
    "sainte-marine": (2, "Maison-feu à l'entrée de l'Odet, face à Bénodet."),
    "benodet": (2, "Dit « la Pyramide », il forme l'alignement d'entrée de la rivière de l'Odet."),
    "moutons": (2, "Sur l'île aux Moutons, entre les Glénan et Bénodet, au cœur d'une réserve d'oiseaux marins."),
    "penfret": (2, "Sur la plus orientale des îles de l'archipel des Glénan."),
    "pen-men": (1, "À la pointe nord-ouest de l'île de Groix, au-dessus des falaises."),
    "pointe-des-chats": (2, "À la pointe sud-est de Groix, dans la réserve géologique ; l'un des phares les plus bas de Bretagne."),
    "port-maria": (2, "Au port de Quiberon, d'où embarquent les navires pour Belle-Île, Houat et Hoëdic."),
    "teignouse": (2, "Dans le passage de la Teignouse, chenal étroit et agité entre Quiberon et Houat."),
    "kerdonis": (2, "À la pointe est de Belle-Île, il marque l'entrée sud du golfe du Morbihan."),
    "grands-cardinaux": (2, "Sur un récif au large de Hoëdic, il signale les hauts-fonds des Cardinaux."),
    "penlan": (2, "À Billiers, il commande l'entrée de la Vilaine et de son estuaire."),
    "four-croisic": (2, "Sur le plateau du Four, écueil redouté au large du Croisic."),
    "morees": (2, "Dans l'estuaire de la Loire, il balise le chenal d'accès à Saint-Nazaire."),
    "aiguillon": (2, "À Saint-Nazaire, il marque l'entrée du port et l'embouchure de la Loire."),
    "grand-charpentier": (2, "Sur un rocher de l'estuaire de la Loire, entre Saint-Nazaire et Pornichet."),
    "banche": (2, "À l'ouest de l'embouchure de la Loire, sur le plateau de la Banche."),
    "pointe-saint-gildas": (2, "À Préfailles, il garde l'entrée sud de l'estuaire de la Loire."),
    "pointe-des-dames": (2, "À la pointe nord-est de Noirmoutier, au-dessus du bois de la Chaise."),
    "fromentine": (2, "À La Barre-de-Monts, face au goulet de Fromentine et au pont de Noirmoutier."),
    "yeu": (1, "Grand phare de l'île d'Yeu, reconstruit après 1944 ; sa lanterne domine toute l'île."),
    "corbeaux": (2, "À la pointe sud-est de l'île d'Yeu, au-dessus de la côte sauvage."),
    "barges": (1, "Sur le rocher des Barges, au large des Sables-d'Olonne, isolé en pleine mer."),
    "armandeche": (1, "Aux Sables-d'Olonne : l'un des derniers grands phares construits en France, à la silhouette blanche et rouge."),
    "grouin-du-cou": (2, "Entre La Tranche-sur-Mer et La Faute, il signale les hauts-fonds du pertuis Breton."),
}


def num(txt):
    """'23,77 mètres' -> 23.77"""
    if not txt:
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)", txt)
    return float(m.group(1).replace(",", ".")) if m else None


def main():
    livret = {x["n"]: x for x in json.load(
        open(os.path.join(HERE, "livret_phares.json"), encoding="utf-8"))}
    geo = json.load(open(os.path.join(HERE, "livret_geo.json"), encoding="utf-8"))

    lignes, extra_new = [], {}
    for pid, g in sorted(geo.items(), key=lambda kv: -kv[1]["lat"]):
        x = livret[g["n"]]
        rank, txt = FICHES[pid]
        h = num(x["hauteur"])
        dep = DEPS.get(x["dep"], x["dep"] or "")
        champs = [f'id: "{pid}"', f'name: "Phare {x["nom"]}"'
                  if not x["nom"].lower().startswith(("grand phare",))
                  else f'name: "{x["nom"]}"',
                  f'lat: {g["lat"]}', f'lon: {g["lon"]}']
        if x["mer"]:
            champs.append("sea: true")
        champs.append(f'dep: "{dep}"')
        if h:
            champs.append(f"h: {h}")
        if x["allumage"]:
            champs.append(f'year: {x["allumage"]}')
        champs.append(f"rank: {rank}")
        champs.append(f'txt: "{txt}"')
        lignes.append("  { " + ", ".join(champs) + " },")

        extra_new[pid] = {
            "wiki": g["wiki"], "img": g["img"], "credit": g["credit"],
            "construction": None,
            "service": str(x["allumage"]) if x["allumage"] else None,
            "hauteur": x["hauteur"], "portee": x["portee"],
            "feux": x["feu"], "optique": x["optique"], "marches": None,
            "sig": parse_feux(x["feu"]),
            "src": "DIRM NAMO, livret Phares & feux Bretagne / Pays de la Loire, 2025",
        }
        if g.get("approx"):
            extra_new[pid]["approx"] = True

    # --- injection dans js/phares.js ---
    p = os.path.join(ROOT, "js", "phares.js")
    src = open(p, encoding="utf-8").read()
    bloc = ("\n  // --- Bretagne & Pays de la Loire (livret DIRM NAMO 2025) ---\n"
            + "\n".join(lignes) + "\n")
    src = src.rstrip()
    assert src.endswith("];"), "fin de phares.js inattendue"
    src = src[:-2].rstrip() + "\n" + bloc + "];\n"
    open(p, "w", encoding="utf-8").write(src)

    # --- fusion dans js/phares_extra.js ---
    pe = os.path.join(ROOT, "js", "phares_extra.js")
    cur = json.loads(re.search(r"=\s*(\{.*\});", open(pe, encoding="utf-8").read(),
                               re.S).group(1))
    cur.update(extra_new)
    open(pe, "w", encoding="utf-8").write(
        "/* Donnees Wikipedia/Wikimedia Commons (licences libres, credits inclus)\n"
        "   + donnees techniques du livret DIRM NAMO 2025 (faits bruts). */\n"
        '"use strict";\nconst PHARES_EXTRA = '
        + json.dumps(cur, ensure_ascii=False, separators=(",", ":")) + ";\n")

    print(f"{len(lignes)} phares ajoutes a js/phares.js")
    print(f"phares_extra.js : {len(cur)} fiches")
    sans_sig = [k for k, v in extra_new.items() if not v["sig"]]
    print("sans signal lumineux :", sans_sig or "aucun")


if __name__ == "__main__":
    main()
