/* Phares des côtes de France — sélection emblématique.
   rank 0 : visibles dès la vue nationale ; 1 : zoom régional ; 2 : zoom local.
   sea : true = phare en mer. h : hauteur (m), year : mise en service. */
"use strict";

const PHARES = [
  // Mer du Nord & Manche est
  { id: "risban", name: "Phare de Dunkerque (Risban)", lat: 51.0510, lon: 2.3660, dep: "Nord (59)", h: 63, year: 1843, rank: 1, txt: "Le phare le plus septentrional de France, en plein port de Dunkerque." },
  { id: "calais-ph", name: "Phare de Calais", lat: 50.9578, lon: 1.8552, dep: "Pas-de-Calais (62)", year: 1848, rank: 2, txt: "Tour blanche octogonale au cœur de la ville ; on y grimpe pour voir l'Angleterre par temps clair." },
  { id: "gris-nez", name: "Phare du cap Gris-Nez", lat: 50.8687, lon: 1.5850, dep: "Pas-de-Calais (62)", rank: 0, txt: "Au point de France le plus proche de l'Angleterre (34 km) ; veille sur le détroit le plus fréquenté du monde." },
  { id: "alprech", name: "Phare d'Alprech", lat: 50.6990, lon: 1.5673, dep: "Pas-de-Calais (62)", rank: 2, txt: "Signale l'approche sud de Boulogne-sur-Mer, premier port de pêche de France." },
  { id: "touquet", name: "Phare du Touquet", lat: 50.5240, lon: 1.5900, dep: "Pas-de-Calais (62)", rank: 2, txt: "Tour de brique reconstruite en 1951 ; domine la baie de Canche et la forêt du Touquet." },
  { id: "cayeux", name: "Phare de Cayeux-sur-Mer", lat: 50.1877, lon: 1.4948, dep: "Somme (80)", rank: 2, txt: "Rouge et blanc au-dessus des galets, il garde l'entrée sud de la baie de Somme." },
  { id: "ailly", name: "Phare d'Ailly", lat: 49.9099, lon: 0.9548, dep: "Seine-Maritime (76)", rank: 2, txt: "Troisième phare du site, au sommet des falaises de craie du pays de Caux, près de Varengeville." },
  { id: "antifer", name: "Phare d'Antifer", lat: 49.6902, lon: 0.1657, dep: "Seine-Maritime (76)", rank: 2, txt: "Reconstruit après-guerre au-dessus des falaises, entre Étretat et Le Havre." },
  { id: "la-heve", name: "Phare de la Hève", lat: 49.5077, lon: 0.0690, dep: "Seine-Maritime (76)", rank: 2, txt: "Béton et hublots d'après-guerre ; domine l'entrée du port du Havre depuis le cap." },
  // Manche ouest / Cotentin
  { id: "gatteville", name: "Phare de Gatteville", lat: 49.6947, lon: -1.2653, dep: "Manche (50)", h: 75, year: 1835, rank: 0, txt: "Deuxième plus haut phare de France en pierre ; 365 fenêtres, autant que de jours. Il garde le raz de Barfleur." },
  { id: "cap-levi", name: "Phare du cap Lévi", lat: 49.6960, lon: -1.4700, dep: "Manche (50)", rank: 2, txt: "Tour carrée de granit rose reconstruite en 1947, à l'est de Cherbourg." },
  { id: "goury", name: "Phare de Goury (la Hague)", lat: 49.7183, lon: -1.9483, sea: true, dep: "Manche (50)", rank: 1, txt: "Sur son rocher face au nez de Jobourg, il veille sur le raz Blanchard, l'un des courants les plus violents d'Europe." },
  { id: "carteret-ph", name: "Phare de Carteret", lat: 49.3715, lon: -1.8085, dep: "Manche (50)", rank: 2, txt: "Sur le cap, au départ du sentier des douaniers ; vue sur les îles Anglo-Normandes." },
  { id: "granville-ph", name: "Phare de la pointe du Roc", lat: 48.8350, lon: -1.6136, dep: "Manche (50)", year: 1828, rank: 2, txt: "À la pointe de la cité corsaire de Granville, face à Chausey." },
  // Bretagne nord
  { id: "frehel", name: "Phare du cap Fréhel", lat: 48.6852, lon: -2.3190, dep: "Côtes-d'Armor (22)", year: 1950, rank: 0, txt: "Au sommet de falaises de grès rose de 70 m, l'un des plus beaux panoramas de Bretagne nord." },
  { id: "heaux", name: "Phare des Héaux de Bréhat", lat: 48.9125, lon: -3.0886, sea: true, year: 1840, dep: "Côtes-d'Armor (22)", rank: 1, txt: "Chef-d'œuvre de Léonce Reynaud posé en pleine mer sur les récifs, au large de l'archipel de Bréhat." },
  { id: "ploumanach", name: "Phare de Mean Ruz (Ploumanac'h)", lat: 48.8305, lon: -3.4890, dep: "Côtes-d'Armor (22)", rank: 1, txt: "Tout en granit rose, reconstruit après 1944 ; gardien du chaos rocheux de Ploumanac'h." },
  { id: "sept-iles", name: "Phare des Sept-Îles", lat: 48.8788, lon: -3.4715, sea: true, dep: "Côtes-d'Armor (22)", rank: 2, txt: "Sur l'île aux Moines, au cœur de la plus grande réserve d'oiseaux marins de France (fous de Bassan, macareux)." },
  { id: "batz", name: "Phare de l'île de Batz", lat: 48.7448, lon: -4.0248, dep: "Finistère (29)", rank: 2, txt: "Domine l'île face à Roscoff ; 198 marches et une vue sur toute la côte du Léon." },
  { id: "ile-vierge", name: "Phare de l'île Vierge", lat: 48.6403, lon: -4.5670, sea: true, h: 82.5, year: 1902, dep: "Finistère (29)", rank: 0, txt: "Le plus haut phare d'Europe en pierre de taille ; son escalier est tapissé de 12 500 plaques d'opaline." },
  { id: "le-four", name: "Phare du Four", lat: 48.5230, lon: -4.8043, sea: true, dep: "Finistère (29)", rank: 1, txt: "Dans le chenal du Four ; les photos de tempête où la vague l'engloutit ont fait le tour du monde." },
  // Ouessant & Iroise
  { id: "stiff", name: "Phare du Stiff (Ouessant)", lat: 48.4885, lon: -5.0553, year: 1695, dep: "Finistère (29)", rank: 1, txt: "Construit sous Vauban : l'un des plus anciens phares de France encore en service." },
  { id: "creach", name: "Phare du Créac'h (Ouessant)", lat: 48.4633, lon: -5.1310, h: 55, year: 1863, dep: "Finistère (29)", rank: 0, txt: "L'un des phares les plus puissants du monde : il ouvre l'entrée de la Manche. Musée des Phares et Balises à son pied." },
  { id: "jument", name: "Phare de la Jument", lat: 48.4172, lon: -5.1330, sea: true, year: 1911, dep: "Finistère (29)", rank: 0, txt: "Rendu mythique par la photo de Jean Guichard (1989) : le gardien sur le seuil, la vague derrière." },
  { id: "kereon", name: "Phare de Kéréon", lat: 48.4390, lon: -5.0195, sea: true, year: 1916, dep: "Finistère (29)", rank: 1, txt: "Le « palace des phares » : boiseries et parquet marqueté. Dernier phare en mer gardienné de France (2004)." },
  { id: "saint-mathieu", name: "Phare de Saint-Mathieu", lat: 48.3302, lon: -4.7702, dep: "Finistère (29)", rank: 0, txt: "Dressé dans les ruines d'une abbaye médiévale, face à la mer d'Iroise." },
  { id: "petit-minou", name: "Phare du Petit Minou", lat: 48.3374, lon: -4.6169, dep: "Finistère (29)", rank: 1, txt: "Avec son pont de pierre, il aligne l'entrée du goulet de Brest ; l'un des plus photographiés de France." },
  { id: "ar-men", name: "Phare d'Ar-Men", lat: 48.0503, lon: -4.9990, sea: true, year: 1881, dep: "Finistère (29)", rank: 0, txt: "« L'Enfer des Enfers » : le plus exposé des phares français, au bout de la chaussée de Sein. 14 ans de chantier." },
  { id: "la-vieille", name: "Phare de la Vieille", lat: 48.0402, lon: -4.7565, sea: true, dep: "Finistère (29)", rank: 1, txt: "Face à la pointe du Raz, il tient tête aux courants du raz de Sein." },
  { id: "eckmuhl", name: "Phare d'Eckmühl", lat: 47.7979, lon: -4.3726, h: 65, year: 1897, dep: "Finistère (29)", rank: 0, txt: "Granit gris et escalier d'opaline, financé par la fille du maréchal Davout, prince d'Eckmühl." },
  // Bretagne sud & Loire
  { id: "goulphar", name: "Grand Phare de Goulphar (Belle-Île)", lat: 47.3086, lon: -3.2184, year: 1836, dep: "Morbihan (56)", rank: 1, txt: "Domine les aiguilles de Port-Coton peintes par Monet." },
  { id: "poulains", name: "Phare des Poulains (Belle-Île)", lat: 47.3874, lon: -3.2532, dep: "Morbihan (56)", rank: 2, txt: "Sur sa presqu'île qui s'isole à marée haute ; Sarah Bernhardt vécut à côté." },
  { id: "port-navalo", name: "Phare de Port-Navalo", lat: 47.5490, lon: -2.9180, dep: "Morbihan (56)", rank: 2, txt: "Marque l'entrée du golfe du Morbihan et de ses courants." },
  { id: "pilier", name: "Phare du Pilier", lat: 47.0428, lon: -2.3565, sea: true, dep: "Loire-Atlantique (44)", rank: 2, txt: "Deux tours jumelles sur l'île du Pilier, au large de Noirmoutier." },
  // Atlantique
  { id: "baleines", name: "Phare des Baleines (Ré)", lat: 46.2486, lon: -1.5614, year: 1854, dep: "Charente-Maritime (17)", rank: 0, txt: "À la pointe nord-ouest de l'île de Ré ; 257 marches et la vieille tour Vauban à ses côtés." },
  { id: "chassiron", name: "Phare de Chassiron (Oléron)", lat: 46.0472, lon: -1.4106, year: 1836, dep: "Charente-Maritime (17)", rank: 1, txt: "Zébré noir et blanc à la pointe nord d'Oléron ; jardins dessinés en rose des vents." },
  { id: "coubre", name: "Phare de la Coubre", lat: 45.6953, lon: -1.2397, h: 64, year: 1905, dep: "Charente-Maritime (17)", rank: 1, txt: "Rouge et blanc au-dessus de la Côte Sauvage ; il guide l'entrée de la Gironde." },
  { id: "cordouan", name: "Phare de Cordouan", lat: 45.5867, lon: -1.1735, sea: true, h: 67.5, year: 1611, dep: "Gironde (33)", rank: 0, txt: "Le « roi des phares » : le plus ancien de France en activité, Renaissance en pleine mer, classé UNESCO en 2021." },
  { id: "grave", name: "Phare de Grave", lat: 45.5686, lon: -1.0644, dep: "Gironde (33)", rank: 2, txt: "Face à Cordouan, à la pointe du Médoc ; il abrite un musée des phares." },
  { id: "cap-ferret", name: "Phare du Cap Ferret", lat: 44.6316, lon: -1.2489, year: 1947, dep: "Gironde (33)", rank: 0, txt: "Rouge au-dessus des pins ; vue sur le banc d'Arguin et la dune du Pilat, à l'entrée du Bassin." },
  { id: "contis", name: "Phare de Contis", lat: 44.0957, lon: -1.3190, dep: "Landes (40)", rank: 1, txt: "Seul phare des Landes, spirale noire et blanche au milieu des dunes et de la forêt." },
  { id: "biarritz", name: "Phare de Biarritz", lat: 43.4963, lon: -1.5644, dep: "Pyrénées-Atlantiques (64)", rank: 0, txt: "Pointe Saint-Martin : 248 marches, la Côte basque et les Pyrénées à l'horizon. Il marque la fin des plages landaises." },
  // Méditerranée
  { id: "cap-bear", name: "Phare du cap Béar", lat: 42.5157, lon: 3.1370, dep: "Pyrénées-Orientales (66)", rank: 1, txt: "Marbre rose des Pyrénées au-dessus de la côte Vermeille, près de Port-Vendres." },
  { id: "sete-ph", name: "Phare Saint-Louis (Sète)", lat: 43.3970, lon: 3.7010, dep: "Hérault (34)", rank: 2, txt: "Au bout du môle, il veille sur les joutes et l'entrée du port de Sète." },
  { id: "espiguette", name: "Phare de l'Espiguette", lat: 43.4870, lon: 4.1430, dep: "Gard (30)", rank: 1, txt: "Perdu dans les dunes camarguaises : depuis sa construction, le rivage s'est éloigné de plus de 700 m." },
  { id: "faraman", name: "Phare de Faraman", lat: 43.4088, lon: 4.7318, dep: "Bouches-du-Rhône (13)", rank: 2, txt: "En Camargue, l'érosion a fait l'inverse de l'Espiguette : la mer s'est rapprochée jusqu'à ses pieds." },
  { id: "planier", name: "Phare du Planier", lat: 43.1990, lon: 5.2305, sea: true, year: 1959, dep: "Bouches-du-Rhône (13)", rank: 0, txt: "Sur son île au large de Marseille ; un feu y signale l'approche du port depuis le Moyen Âge." },
  { id: "porquerolles", name: "Phare de Porquerolles", lat: 42.9822, lon: 6.2068, dep: "Var (83)", rank: 1, txt: "Au cap d'Arme, dans le parc national de Port-Cros ; balade emblématique de l'île." },
  { id: "camarat", name: "Phare du cap Camarat", lat: 43.2018, lon: 6.6810, dep: "Var (83)", rank: 2, txt: "Haut perché au-dessus de Pampelonne, l'un des feux les plus élevés de Méditerranée." },
  { id: "garoupe", name: "Phare de la Garoupe (Antibes)", lat: 43.5642, lon: 7.1320, dep: "Alpes-Maritimes (06)", rank: 2, txt: "Sur le plateau de la Garoupe ; par temps clair, la vue court de l'Estérel à l'Italie." },
  { id: "cap-ferrat-ph", name: "Phare du cap Ferrat", lat: 43.6755, lon: 7.3308, dep: "Alpes-Maritimes (06)", rank: 2, txt: "À la pointe de la presqu'île, entre Nice et Monaco." },
  // Corse
  { id: "revellata", name: "Phare de la Revellata", lat: 42.5794, lon: 8.7245, dep: "Haute-Corse (2B)", rank: 2, txt: "Sur sa presqu'île sauvage face à la citadelle de Calvi." },
  { id: "sanguinaires", name: "Phare des Sanguinaires", lat: 41.8830, lon: 8.5960, sea: true, dep: "Corse-du-Sud (2A)", rank: 1, txt: "Sur la Grande Sanguinaire, îles rouges au couchant chantées par Alphonse Daudet." },
  { id: "pertusato", name: "Phare de Pertusato", lat: 41.3700, lon: 9.1830, dep: "Corse-du-Sud (2A)", rank: 0, txt: "Au-dessus des falaises blanches de Bonifacio, le point le plus au sud de la France métropolitaine, face à la Sardaigne." },
  { id: "alistro", name: "Phare d'Alistro", lat: 42.2635, lon: 9.5433, dep: "Haute-Corse (2B)", rank: 2, txt: "Seul grand phare de la plaine orientale corse, entre mer et étangs." },
];
