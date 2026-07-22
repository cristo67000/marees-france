# -*- coding: utf-8 -*-
"""
Extraction des données factuelles du livret DIRM NAMO
« Phares & feux de Bretagne et des Pays de la Loire » (éd. déc. 2025).

Le livret est © DIRM NAMO : on n'en reprend QUE les données factuelles
(hauteur, feu, portée, optique, département, dates) — jamais la prose.
Les descriptions de l'app sont rédigées séparément, et les photos
proviennent de Wikimedia Commons (licences libres).

Sortie : tools/livret_phares.json
"""
import json, os, re, sys

HERE = os.path.dirname(__file__)
PDF = r"C:\Users\crist\Downloads\livret_phares_2025_export_web_mini_cle527eb3.pdf"
OUT = os.path.join(HERE, "livret_phares.json")

# (numéro, nom du sommaire, page PDF)
INDEX = [
    (1, "Pierre de Herpin", 5), (2, "Rochebonne", 6), (3, "Balue", 7),
    (4, "Bas Sablons", 8), (5, "Grand Jardin", 9), (6, "Cap Fréhel", 10),
    (7, "Grand Léjon", 11), (8, "Rosédo", 12), (9, "Roches-Douvres", 13),
    (10, "Héaux de Bréhat", 14), (11, "Bodic", 15), (12, "Sept-Îles", 16),
    (13, "Mean Ruz", 17), (14, "Triagoz", 18), (15, "Lande", 19),
    (16, "Roscoff", 20), (17, "Île de Batz", 21), (18, "Pontusval", 22),
    (19, "Lanvaon", 23), (20, "Île Vierge", 24), (21, "Île Wrac'h", 25),
    (22, "Four", 26), (23, "La Jument", 27), (24, "Stiff", 28),
    (25, "Créac'h", 29), (26, "Nividic", 30), (27, "Kéréon", 31),
    (28, "Lanildut", 32), (29, "Trézien", 33), (30, "Kermorvan", 34),
    (31, "Pierres Noires", 35), (32, "Saint-Mathieu", 36),
    (33, "Petit Minou", 37), (34, "Portzic", 38), (35, "Millier", 39),
    (36, "Tévennec", 40), (37, "Ar-Men", 41), (38, "Île de Sein (Goulenez)", 42),
    (39, "Vieille", 43), (40, "Eckmühl", 44), (41, "Sainte-Marine", 45),
    (42, "Bénodet (Pyramide)", 46), (43, "Moutons", 47), (44, "Penfret", 48),
    (45, "Pen Men", 49), (46, "Pointe des Chats", 50), (47, "Port Maria", 51),
    (48, "Teignouse", 52), (49, "Port Navalo", 53), (50, "Poulains", 54),
    (51, "Goulphar", 55), (52, "Kerdonis", 56), (53, "Grands Cardinaux", 57),
    (54, "Penlan", 58), (55, "Four du Croisic", 59), (56, "Morées", 60),
    (57, "Aiguillon", 61), (58, "Grand Charpentier", 62), (59, "Banche", 63),
    (60, "Pointe Saint-Gildas", 64), (61, "Pilier", 65),
    (62, "Pointe des Dames", 66), (63, "Fromentine", 67),
    (64, "Grand phare de l'Île d'Yeu", 68), (65, "Corbeaux", 69),
    (66, "Barges", 70), (67, "Armandèche", 71), (68, "Grouin du Cou", 72),
]

DEPS = ["Ille-et-Vilaine", "Côtes-d'Armor", "Finistère", "Morbihan",
        "Loire-Atlantique", "Vendée"]


def flat(t):
    t = re.sub(r"\s+", " ", t).replace("’", "'")
    # l'extraction PDF insère une espace dans les décimales : « 27 ,10 mètres »
    t = re.sub(r"(\d)\s+([,.])\s*(\d)", r"\1\2\3", t)
    return t


LABELS = r"Hauteur(?:\s*totale)?|Feu|Portée|Optique|Automatis\w*|Classé|Inscrit|P\s?hare|M\s?aison-feu"


# débuts de prose : la mise en page colle parfois le texte descriptif
# juste après la dernière valeur d'un champ.
PROSE = (r"P\s?hare\s+d|M\s?aison-feu|Le\s+phare|La\s+tour|Il\s+est\s|"
         r"Elle\s+est\s|Ce\s+phare|Cette\s+tour|Le\s+feu\s+est|Construit|"
         r"Situé|Classé|Inscrit")


def field(txt, label, maxlen=240):
    """Valeur d'un champ 'Label : valeur', bornée au champ ou à la prose suivante.

    Pas de \\b avant le libellé : la mise en page colle parfois le mot au
    précédent (« Ille-et-VilaineHauteur : … »).
    """
    m = re.search(r"(?:" + label + r")\s*:\s*", txt)
    if not m:
        return None
    reste = txt[m.end():m.end() + maxlen]
    stop = re.search(r"\s*(?:(?:" + LABELS + r")\s*:|" + PROSE + r")", reste)
    if stop:
        reste = reste[:stop.start()]
    val = reste.strip(" .;,-")
    if re.match(r"^(?:" + LABELS + r")\b", val):
        return None
    return val or None


def main():
    import pypdf
    r = pypdf.PdfReader(PDF)
    texts = {i + 1: flat(p.extract_text() or "") for i, p in enumerate(r.pages)}
    out = []
    for num, name, page in INDEX:
        t = texts.get(page, "")
        dep = next((d for d in DEPS if d.split("-")[0] in t), None)
        h = field(t, r"Hauteur(?:\s*totale)?")
        feu = field(t, r"Feu")
        portee = field(t, r"Portée")
        optique = field(t, r"Optique")
        # années citées (construction / allumage)
        annees = sorted(set(int(x) for x in re.findall(r"\b(1[5-9]\d{2}|20[0-2]\d)\b", t)))
        # année d'allumage : on retient la DERNIÈRE citée — pour les phares
        # détruits puis reconstruits (guerre), c'est celle du feu actuel.
        ma = re.findall(r"allumé\w*\s+(?:le\s+)?(?:\d{1,2}\s*(?:er)?\s*[a-zéû]+\s+)?"
                        r"(1[5-9]\d{2}|20[0-2]\d)", t)
        allumage = int(ma[-1]) if ma else None
        out.append({
            "n": num, "nom": name, "page": page, "dep": dep,
            "hauteur": h, "feu": feu, "portee": portee, "optique": optique,
            "annees": annees, "allumage": allumage,
            "mer": bool(re.search(r"en mer|sur (?:un |le |la )?(?:îlot|ilôt|roche|récif|plateau)", t, re.I)),
            "mh": bool(re.search(r"monuments? historiques?", t, re.I)),
        })
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ok = sum(1 for x in out if x["hauteur"])
    print(f"{len(out)} phares, {ok} avec hauteur -> {OUT}")
    for x in out[:6]:
        print(f"  {x['n']:2d} {x['nom'][:26]:26s} {str(x['dep'])[:16]:16s} "
              f"h={str(x['hauteur'])[:14]:14s} feu={str(x['feu'])[:34]}")


if __name__ == "__main__":
    main()
