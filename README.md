# Phares et Marées en France 🌊

Application de marées **hors-ligne** pour smartphone : carte de France des côtes,
horaires de pleine/basse mer, coefficient de marée, marnage et phase de lune —
**en tout point du littoral, sans connexion internet**.

Tout est calculé localement sur le téléphone (prédiction harmonique, 53 ports,
22 composantes de marée par port). Aucune donnée n'est envoyée nulle part.

## Installer sur le téléphone

### Option A — le plus simple : le fichier unique
1. Copier `dist/marees-france.html` sur le téléphone (câble USB, e-mail à
   soi-même, WhatsApp, Google Drive…).
2. L'ouvrir avec **Chrome** ou **Firefox** (via l'appli Fichiers).
3. Menu ⋮ → « Ajouter à l'écran d'accueil » pour créer un raccourci.

→ Fonctionne ensuite **sans aucune connexion**, même en pleine mer.

### Option B — vraie appli installée (PWA), si on peut héberger
1. Déposer tout le dossier sur un hébergement statique gratuit
   (GitHub Pages, Netlify Drop…).
2. Ouvrir l'adresse sur le téléphone → Chrome propose **« Installer
   l'application »** : icône, plein écran, hors-ligne automatique
   (service worker).

### Tester sur PC
```
python -m http.server 8123 --directory marees-france
```
puis ouvrir http://localhost:8123

## Lecture d'un seul coup d'œil

- **En haut** : heure, date, phase de lune (icône + % éclairé) et
  **coefficient du jour** (couleur : gris = morte-eau, bleu = moyen,
  orange = vive-eau, rouge = grande marée ≥ 95).
- **Sur la carte** : chaque port porte une flèche **▲ montante / ▼ descendante** ;
  en zoomant, l'heure de la prochaine pleine/basse mer s'affiche.
- **Toucher un port** : marée en cours et compte à rebours, hauteur d'eau
  actuelle, marnage, coefficient, courbe de la journée (glisser le doigt pour
  lire la hauteur à toute heure), 4 prochaines pleines/basses mers, puis un
  module repliable **« À propos du port »** : localisation (département,
  coordonnées), activités (pêche, plaisance, ferry…), accès et particularités
  (bassin à flot/écluse, échouage, accès permanent…) pour les principaux
  ports, et fiche descriptive.
- **Couches à la carte** : deux boutons ronds (ancre = ports, phare = phares)
  activent/désactivent chaque couche ; le choix est mémorisé. Ports masqués,
  les phares profitent de toute la place.
- **Îles** : le fond de carte ne comportait que le continent, la Corse, Ré,
  Oléron, Noirmoutier et Belle-Île — les phares d'Ouessant, Sein ou Batz
  flottaient sur de l'eau vide. Sont ajoutées **15 îles** (`data/iles.json`,
  contours OpenStreetMap via `tools/fetch_iles.py`) : bretonnes (Ouessant,
  Molène, Sein, Batz, Glénan, Groix, Houat, Hoëdic, Bréhat), Yeu, Chausey et
  les **anglo-normandes** (Jersey, Guernesey, Aurigny, Sercq) — celles-ci d'une
  teinte plus sourde et au trait pointillé, n'étant pas françaises. Elles
  apparaissent à partir du zoom régional, comme les côtes nommées ; les petits
  archipels attendent le zoom local.
- **Habillage géographique** : les 10 grands fleuves (tracés réels Natural
  Earth : Seine, Somme, Loire, Vilaine, Charente, Garonne, Dordogne, Adour,
  Rhône, Aude), les mers et golfes (Manche, Atlantique, Méditerranée,
  Gascogne, Lion, Iroise…), les **20 côtes nommées** (côte d'Opale, d'Albâtre,
  d'Émeraude, de Granit Rose, d'Argent, Vermeille, d'Azur…) et **35 villes
  côtières** (point + nom, l'étiquette bascule au-dessus du point si la place
  manque). Tout est soumis au même écrémage anti-chevauchement, priorité aux
  ports, et rien n'est cliquable — l'habillage ne gêne jamais les marées.
- **Bouton soleil** (ou toucher la lune en haut) : **calendrier Soleil & Lune**
  escamotable — lever/coucher du soleil et de la lune sur 14 jours, phase de
  lune dessinée jour par jour, % d'éclairement, coefficients, prochaines
  pleine/nouvelle lunes. Les heures s'adaptent au lieu (port ouvert ou centre
  de la carte).
- **Phares** : **110 phares** (Cordouan, Créac'h, la Jument, Ar-Men, l'île
  Vierge, les Roches-Douvres, Tévennec, Nividic…) apparaissent en zoomant sur
  la côte (icône tour + faisceaux ; le bouton phare les masque/affiche).
  Toucher un phare ouvre sa fiche : **photo** (Wikimedia Commons, crédit
  affiché, toucher pour agrandir), localisation, **hauteur, nombre de marches,
  portée, dates de construction et de mise en service, optique**, anecdote, et
  une **animation de la lanterne qui rejoue le vrai rythme du feu**
  (« 2 éclats blancs, 10 s », occultations, isophase… couleur comprise). Un
  bouton renvoie vers les marées du port le plus proche. Les ports gardent la
  priorité d'affichage : aucun chevauchement.

  Sources : `tools/fetch_phares.py` (Wikipédia/Commons) pour la sélection
  initiale, et `tools/parse_livret.py` + `fetch_livret.py` + `gen_livret.py`
  pour les **68 phares et feux de Bretagne et Pays de la Loire** du livret
  officiel **DIRM NAMO** (éd. déc. 2025) — dont 48 ajoutés. Du livret ne sont
  reprises que les **données factuelles** (hauteur, feu, portée, optique,
  dates) : sa prose est © DIRM NAMO et n'est pas reproduite ; les textes de
  présentation sont propres à l'app et les photos viennent de Commons.

  Façade **Manche Est - Mer du Nord** (Nord, Pas-de-Calais, Somme,
  Seine-Maritime, Calvados, Manche) : la couverture est désormais celle de la
  **liste officielle de la DIRM MEMN**, soit ses **21 phares** — les 7 qui
  manquaient ont été ajoutés (Ault, Berck, digue Carnot à Boulogne,
  Ouistreham, Ver-sur-Mer, fort de l'Ouest à Cherbourg, Chausey). Les rythmes
  et portées viennent des fiches techniques DIRM (licence Etalab 2.0) ou, à
  défaut, des balises seamark d'OpenStreetMap ; `tools/scan_phares_nord.py`
  les relève et `tools/sync_memn.py` les impose à ce que donne Wikipédia.

- **Me localiser** (bouton cible, optionnel) : au premier appui, un écran
  explique à quoi sert la position **avant** l'invite du système ; une fois
  l'autorisation accordée, l'app affiche votre point sur la carte, le **port**
  et le **phare les plus proches** avec les distances à vol d'oiseau, et ouvre
  la fiche marée du port. **Aucune donnée n'est envoyée** : la position est
  comparée sur l'appareil aux coordonnées embarquées, rien n'est enregistré
  (seul l'accord de principe l'est, pas de coordonnées), et l'app reste
  entièrement utilisable sans géolocalisation. Nécessite HTTPS (ou localhost) :
  en `file://` le navigateur refuse la géolocalisation, le message le dit.

## Précision (validée contre les tables officielles SHOM/maree.info)

| Grandeur | Écart typique |
|---|---|
| Horaires PM/BM | ± 5 à 10 min (± 30 min dans les estuaires : Le Havre, Saint-Nazaire) |
| Hauteurs | ± 10–20 cm |
| Coefficients | valeurs **officielles** embarquées jan→oct 2026, ensuite modèle ± 2 pts |

⚠️ **Prédictions indicatives** : ne pas utiliser pour la navigation ni pour des
activités engageant la sécurité. Les surcotes/décotes météo (vent, pression) ne
sont pas prises en compte.

## Structure

- `index.html`, `css/`, `js/` — l'application (zéro dépendance réseau)
- `confidentialite.html` — politique de confidentialité (exigée par le Play
  Store dès qu'une appli demande la position) ; retirée du fichier unique, où
  le lien n'aurait pas de cible
- `data/ports.json` — constantes harmoniques calées des 53 ports + table
  officielle des coefficients 2026
- `data/france.geojson` — fond de carte embarqué
- `data/iles.json` — contours des 15 îles ajoutées (bretonnes, anglo-normandes,
  Yeu, Chausey), régénérable par `python tools/fetch_iles.py`
- `lib/` — Leaflet 1.9.4 en local
- `dist/marees-france.html` — version tout-en-un régénérable par
  `python tools/build_single.py`
- `tools/` — chaîne de fabrication des données :
  1. `fit_ports.py` — télécharge 1 an de niveaux de la mer (API marine
     Open-Meteo) et ajuste les harmoniques par moindres carrés
  2. `calibrate.py` — recale horaires/hauteurs sur 15 ports de référence
     (`reference_maree_info.json`)
  3. `calibrate_coef2.py` — embarque les coefficients officiels
     (`coef_calendar.json`) + régression de secours

## Durée de validité

Le calage est fait pour 2026. La prédiction harmonique reste bonne en 2027
(dérive lente, quelques minutes), puis se dégrade doucement (cycle nodal de
18,6 ans non modélisé). Pour re-caler : relancer les 3 scripts de `tools/`
puis `build_single.py`.
