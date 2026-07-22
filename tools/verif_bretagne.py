# -*- coding: utf-8 -*-
"""
Contrôle de conformité de l'app avec le PDF « Phares de Bretagne »
(54 phares bretons, caractéristiques des feux + portées).

Référence saisie depuis le PDF ; comparaison avec PHARES_EXTRA (sig/feux/portée).
mode : flash (éclats) | occ (occultations) | iso | fixe | scint
n    : nombre d'éclats/occultations groupés ; T : période en secondes
"""
import json, os, re

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")

# id app -> (mode, n, période, couleur principale, portée blanche en milles)
# None = non précisé par le PDF
REF = {
    # Ille-et-Vilaine
    "pierre-herpin":   ("iso",   1, 4,  "blanc", 12),
    "rochebonne":      ("fixe",  1, None, "rouge", 24),
    "balue":           ("fixe",  1, None, "vert",  25),
    "bas-sablons":     ("fixe",  1, None, "vert",  20),
    "grand-jardin":    ("flash", 2, 10, "rouge", 17),
    # Côtes-d'Armor
    "frehel":          ("flash", 2, 10, "blanc", 29),
    "grand-lejon":     ("flash", 3, 12, "blanc", 11),
    "rosedo":          ("flash", 1, 5,  "blanc", 20),
    "roches-douvres":  ("flash", 1, 5,  "blanc", 24),
    "heaux":           ("flash", 4, 15, "blanc", 15),
    "bodic":           ("scint", 1, None, "blanc", 22),
    "sept-iles":       ("flash", 3, 20, "blanc", 23),
    "ploumanach":      ("occ",   1, 4,  "blanc", 12),
    "triagoz":         ("flash", 2, 6,  "blanc", 14),
    # Finistère
    "la-lande":        ("flash", 1, 5,  "blanc", 23),
    "roscoff-ph":      ("occ",   3, 12, "blanc", 15),
    "batz":            ("flash", 4, 25, "blanc", 23),
    "pontusval":       ("occ",   3, 12, "blanc", 12),
    "lanvaon":         ("scint", 1, None, "blanc", 13),
    "ile-vierge":      ("flash", 1, 5,  "blanc", 26),
    "ile-wrach":       ("scint", 1, 1.2, "rouge", 7),
    "le-four":         ("flash", 5, 15, "blanc", 23),
    "jument":          ("flash", 3, 12, "rouge", 10),
    "stiff":           ("flash", 2, 20, "rouge", 22),
    "creach":          ("flash", 2, 10, "blanc", 31),
    "nividic":         ("scint", 9, None, "blanc", 6),
    "kereon":          ("occ",   3, 12, "blanc", 17),
    "lanildut":        ("occ",   2, None, "blanc", 12),
    "trezien":         ("occ",   2, 6,  "blanc", 20),
    "kermorvan":       ("flash", 1, 5,  "blanc", 22),
    "pierres-noires":  ("flash", 1, 5,  "rouge", 20),
    "saint-mathieu":   ("flash", 1, 15, "blanc", 25),
    "petit-minou":     ("flash", 2, 6,  "blanc", 8),
    "portzic":         ("occ",   2, 12, "blanc", 18),
    "millier":         ("occ",   2, 6,  "blanc", 16),
    "tevennec":        ("scint", 1, None, "blanc", 10),
    "ar-men":          ("flash", 3, 20, "blanc", 21),
    "goulenez":        ("flash", 4, 25, "blanc", 28),
    "la-vieille":      ("iso",   1, 4,  "blanc", 15),
    "eckmuhl":         ("flash", 1, 5,  "blanc", 23),
    "sainte-marine":   ("occ",   2, 6,  "blanc", 13),
    "benodet":         ("occ",   3, None, "blanc", 15),
    "moutons":         ("occ",   2, None, "blanc", 15),
    "penfret":         ("flash", 1, 5,  "rouge", 20),
    # Morbihan
    "pen-men":         ("flash", 4, 25, "blanc", 29),
    "pointe-des-chats": ("flash", 1, 4, None,    13),
    "port-maria":      ("scint", 1, None, "blanc", 14),
    "teignouse":       ("flash", 1, 4,  "blanc", 15),
    "port-navalo":     ("occ",   3, None, "blanc", 14),
    "poulains":        ("flash", 1, 5,  "blanc", 23),
    "goulphar":        ("flash", 2, 10, "blanc", 27),
    "kerdonis":        ("flash", 3, None, "blanc", 19),  # période non donnée
    "grands-cardinaux": ("flash", 4, 15, "blanc", 14),
    "penlan":          ("occ",   2, None, "blanc", 15),
}


def charge_extra():
    raw = open(os.path.join(ROOT, "js", "phares_extra.js"), encoding="utf-8").read()
    return json.loads(re.search(r"=\s*(\{.*\});", raw, re.S).group(1))


def mode_app(sig):
    """mode tel que l'app l'anime (scintillant = flash avec n>=6)."""
    if not sig:
        return None
    m = sig["mode"]
    if m == "flash" and sig.get("n", 1) >= 6:
        return "scint"
    return m


def portee_app(txt):
    """Même convention que l'app : pour un feu à secteurs, le secteur blanc."""
    if not txt:
        return None
    m = (re.search(r"(\d+(?:[.,]\d+)?)\s*milles?[^.;,]{0,26}blanc", txt, re.I)
         or re.search(r"blanc[^.;,]{0,20}?(\d+(?:[.,]\d+)?)\s*milles?", txt, re.I)
         or re.search(r"(\d+(?:[.,]\d+)?)\s*mille", txt))
    return float(m.group(1).replace(",", ".")) if m else None


def main():
    extra = charge_extra()
    absents, ecarts, ok = [], [], 0
    for pid, (rmode, rn, rT, rcol, rport) in REF.items():
        if pid not in extra:
            absents.append(pid)
            continue
        e = extra[pid]
        sig = e.get("sig")
        pbs = []
        am = mode_app(sig)
        if am != rmode:
            pbs.append(f"mode app={am} / PDF={rmode}")
        if sig and rn is not None and rmode != "scint":
            an = sig.get("n", 1) + (sig.get("n2") or 0)
            if an != rn:
                pbs.append(f"nb éclats app={an} / PDF={rn}")
        if sig and rT is not None:
            if abs(sig.get("period", 0) - rT) > 0.51:
                pbs.append(f"période app={sig.get('period')}s / PDF={rT}s")
        if sig and rcol and sig.get("color") != rcol:
            pbs.append(f"couleur app={sig.get('color')} / PDF={rcol}")
        ap = portee_app(e.get("portee"))
        if rport is not None and ap is not None and abs(ap - rport) > 0.6:
            pbs.append(f"portée app={ap} / PDF={rport} milles")
        if pbs:
            ecarts.append((pid, pbs, e.get("feux")))
        else:
            ok += 1

    print(f"Phares du PDF presents dans l'app : {len(REF) - len(absents)}/{len(REF)}")
    if absents:
        print("  ABSENTS :", absents)
    print(f"Conformes : {ok}   Ecarts : {len(ecarts)}\n")
    for pid, pbs, feux in ecarts:
        print(f"--- {pid}")
        print(f"    app  : {feux!r}")
        for p in pbs:
            print(f"    !! {p}")


if __name__ == "__main__":
    main()
