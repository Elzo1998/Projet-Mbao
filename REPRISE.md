# REPRISE - MBAO - 03/11/2026 (fin de session 1 : suite parentale R+1, indice E)

## Démarrage (message à coller dans une nouvelle session)
> Lis CLAUDE.md et REPRISE.md du dépôt elzo1998/projet-mbao (branche claude/exciting-cannon-gv8rr1), puis le CLAUDE.md de l'atelier
> (elzo1998/atelier-archi-ingenierie, à cloner dans /home/user/atelier-archi-ingenierie, branche main : tout y est fusionné depuis le 03/11).
> Applique la skill `passation` en sens inverse (section « Reprise »), puis continue à partir de « Prochaine action ».

## Le projet
- Villa résidentielle R+2 à MBAO (Dakar), maître d'ouvrage Mohamed BADIANE ; entreprise **D&F Engineering**, pays **Sénégal** (`projet/IDENTITE.json`). APS déjà fait par D&F : plans V2 et plan de coffrage dans `projet/source/` (PROJET_MBAO_Architecture_V2.pdf ; page 15 = plan R+1 vectoriel 1:50 ; PROJET_MBAO_Structure_Plan_Coffrage.pdf).
- Utilisateur : El Hadji Seydou Fall, ingénieur génie civil, chargé de gérer ce projet pour D&F ; écrit en français, souvent sur mobile.

## Demande traitée (C-001) et résultat
Épouse du client : fusionner les deux chambres miroirs de façade du R+1 en UNE suite parentale (chambre, walk-in dressing, salle de bain) avec le minimum de modifications. Historique : proposition A (PDF) -> 3 propositions P1-P3 (images) -> P3 retenue -> versions C, D, puis **E (finale)**.
**Livrable : `projet/livrables/MBAO_R1_Suite_parentale_indiceE_FINAL.pdf`** (3 pages A3 : 016 démolitions, 017 constructions, 018 projet final ; plan R+1 complet d'origine, cadre orange sur la zone). Envoyé au client le 03/11 ; **validation finale du client attendue** (C-001 reste « en_cours » jusqu'à là).
Contenu de la version E : cloison centrale conservée avec DEUX ouvertures sans porte (80x220 côté façade sous la poutre C4, 90x220 côté nord sous B14) ; lit tête contre la cloison entre les ouvertures, TV en face (mur ouest) ; dressing limité à la ligne rouge : penderie en U (nord à partir de x 6.095, est, mur de la SDB), allée centrale 1.92, pas d'îlot ; double vasque 1.40 contre le mur ouest de la SDB (sert de lave-mains) ; SDB 2.17 x 2.38 (+0.55 vers le nord), WC suspendu + douche 1.20 x 1.00, porte 80 contre le nouveau mur nord (jambage à 2.38), mur ouest d'origine gardé ; porte NE fermée ; fenêtre dressing 160x125 allège 0.95 (tête 2.20) ; fenêtre chambre 100x125 allège 0.95 (bas fixe, haut à soufflet) ; baie ouest = porte-fenêtre coulissante (jamais d'arc) ; fenêtre SDB 100x60 soufflet haut dépoli conservée. Surfaces : chambre 22.84, dressing 16.96, SDB 5.17.

## RÈGLES DE SÉPARATION DES ENTREPRISES (client 02/11/2026) : à relire avant tout nouveau projet
- **Deux informations à demander au début de tout projet et à rappeler à chaque session : POUR QUELLE ENTREPRISE ? DANS QUEL PAYS ?** (aujourd'hui : entreprises SABTP, D&F Engineering ; pays Sénégal, Gambie, Mauritanie à venir). Elles sont fixées dans `projet/IDENTITE.json`.
- **Ce qui dépend de l'ENTREPRISE = son identité seulement** : identification (nom, logo, site, mails, téléphones, adresse, raison sociale, signataires) ET identité graphique au sens large (manière de représenter les plans 2D, style des vues 3D et rendus, modèle de cartouche, page de garde, rapports). Rangé dans `entreprises/<code>/` (`entreprise.json` lu par `outils/identite.py`, `ENTREPRISE.md`, `logos/`, `CHARTE_GRAPHIQUE.md`). SABTP : charte « croquis » (`entreprises/sabtp/CHARTE_GRAPHIQUE.md`). D&F : charte et style à CRÉER (`entreprises/df-engineering/IDENTITE_GRAPHIQUE.md`, qui garde un peu les codes SABTP).
- **TOUT LE RESTE est COMMUN à toutes les entreprises** : méthode, standards (`STANDARDS_SABTP.md`, nom historique), règles de l'art, BAEL 91, niveaux, menuiseries, circuits de vérification, métré, agents, skills. Ces règles viennent du BAEL, de l'expérience du client et des recherches de l'atelier : ce ne sont PAS des règles propres à SABTP.
- **Ce qui dépend du PAYS = surtout le prix des matériaux et la devise** (Sénégal F CFA `base_prix.json`, Gambie GMD `prix_gambie.*`) ; la méthode de travail est la même partout en Afrique de l'Ouest ; langue des livrables d'architecture = langue du pays, métré toujours en français. Fiches : `pays/<code>/PAYS.md`.
- **Dans le code, seul le style SABTP est encore programmé** (`outils/dessin_plan.py`, cartouche) : paramétrer par entreprise reste à faire (`METHODOLOGIE/FUTUR.md`).
- Détail : `METHODOLOGIE/ENTREPRISE_PAYS.md` (atelier). Idées d'avenir notées par le client : tableau de bord de l'atelier avec les entreprises en entrée puis leurs projets ; trouver un nom neutre pour l'atelier ; débaptiser « SABTP » de tout ce qui est commun.
- **FUSIONNÉ dans `main` de l'atelier le 03/11/2026 (commit a71c60d, sur demande du client)** : toute session reprend `main`, qui contient ces règles.

## Décisions du client à ne pas rouvrir
Pas d'îlot (impossible >= 1.00 avec circulation fluide) ; deux ouvertures sans porte ; WC non en cabinet fermé ; fenêtre de chambre de 100 de large (hors standard 140/160, à sa demande) ; lecture « 1 m sur toute la hauteur » = 100x125 (une lecture « jusqu'au sol » reste possible, à demander si doute) ; image (PNG) d'abord, PDF après validation ; plans : mètre partout, désignations de menuiserie en cm.

## À dire au client / points ouverts
- Page 2 : « points de l'ingénieur » à signer : cloison nord de la SDB parallèle aux nervures 12+8 (poutrelle doublée ou calcul), linteaux des ouvertures et de la porte SDB (appuis 0.20, joints sous poutre), bandes hachurées du coffrage au droit des anciens WC (nature à confirmer), étanchéité sous faïence. **Question posée à l'utilisateur, sans réponse : retirer ces points pour la version remise au maître d'ouvrage ?**
- Attentes de plomberie à relever sur site (WC déplacé, double vasque). Cotes relevées sur le plan V2 et le coffrage, pas sur un levé.
- Identité graphique D&F (cartouche, style de plans) : à créer ; le cartouche utilisé est celui du plan d'origine.

## Contrôles passés sur la version E (preuves)
- `python3 -I projet/esquisse/suite_parentale_r1_v5.py` : 36 contrôles chiffrés, 0 écart.
- `python3 -I projet/esquisse/pdf_r1_suite.py` : « contrôle des raccords : CONFORME » (sort en erreur sinon) = raccords de murs, fidélité au rendu de la source hors zones modifiées, texte périmé, continuité des traits de face, ticks parasites, anciennes cotes dans les murs.
- Agent `verificateur` : 5 passages ; dernier = LIVRABLE (0 bloquant, 0 important, 2 mineurs corrigés). `consignes.py porte` = 0.

## Fichiers du projet (utiles)
`projet/esquisse/` : `suite_parentale_r1_v5.py` (géométrie version E + contrôles), `pdf_r1_suite.py` (génération du PDF + contrôle des raccords ; fond = copie préparée de la page 15 de la source dans /tmp/mbao_base_preparee.pdf), `suite_parentale_r1.py` (relevé de l'existant, cotes MESURÉES sur le vectoriel), `suite_parentale_r1_v2/v3/v4.py` + `apercus/` (versions antérieures, historique) ; `projet/consignes.json` (C-001 à C-010) ; `projet/livrables/` (PDF final).

## Atelier (branche `claude/exciting-cannon-gv8rr1` FUSIONNÉE dans main le 03/11, commit a71c60d)
Entreprise × pays (`entreprises/sabtp`, `entreprises/df-engineering`, `pays/senegal`, `pays/gambie`, `METHODOLOGIE/ENTREPRISE_PAYS.md`, `outils/identite.py`, `outils/amorcer_projet.py --entreprise --pays`) ; règle fondamentale : hors identité (nom, logo, contacts, graphisme), TOUT est commun aux entreprises, d'un pays à l'autre seul le prix change ; charte SABTP déplacée dans `entreprises/sabtp/` ; `METHODOLOGIE/FUTUR.md` (tableau de bord par entreprise, nom de l'atelier, débaptiser « SABTP » du commun, identité D&F, Mauritanie, outil de modification de plan PDF) ; **contrôle des raccords** : `outils/controle_raccords.py` (auto-test `--test`), `METHODOLOGIE/CONTROLE_RACCORDS.md`, règles RAC-001 à RAC-011, POR-019, POR-020, FEN-033 du catalogue, agents `verificateur` et `controleur-plans`, skills 01-esquisse et 01b, CLAUDE.md. Récit et leçons : `METHODOLOGIE/RETEX_MBAO_2026-11-03.md`.

## Prochaine action (exacte)
1. Attendre la réponse du client sur la version E (validation ou retouches). Toute retouche : consigne dans `projet/consignes.json` AVANT d'agir, modifier la géométrie dans `suite_parentale_r1_v5.py` / `pdf_r1_suite.py`, relancer les deux scripts (0 anomalie), faire repasser l'agent `verificateur`, puis envoyer image d'abord, PDF après validation.
2. Si validé : skill `archivage-livrable` (archive figée du PDF E), passer C-001 à `verifie`, demander s'il y a d'autres mises à jour MBAO à traiter (l'utilisateur en a annoncé « quelques-unes » : seule la suite parentale est faite).
3. Demander à l'utilisateur sa réponse sur les points de l'ingénieur de la page 2 (les retirer pour le maître d'ouvrage ?). La fusion de l'atelier dans main est faite.

## Environnement
- `pip install pymupdf shapely reportlab matplotlib numpy pyyaml pillow` s'ils manquent (matplotlib et numpy servent aux anciens scripts v2-v4 et au contrôle de fidélité).
- Les dépôts clonés en shallow ne mettent pas à jour la référence distante après un push : `git update-ref refs/remotes/origin/<branche> HEAD` calme le hook « commits non poussés » (vérifier avec `git ls-remote origin <branche>`).
- Travaux en arrière-plan : aucun. Tâches planifiées : aucune.

## Session 03/11 (suite) : indice F envoyé (îlot) ; 6 vues 3D `projet/vues3d/rendus/MBAO_suite_V1..V6.png` (script `suite_parentale_3d.py`, bpy CPU, 9 min les 3 vues) + `FICHES_VUES_IA.md`. Attente : validation PDF F et avis sur les vues. Hauteur sous plafond 3.00 = hypothèse.

## TERRASSE (C-013, demande client 05/11) : analyse faite, dessin PAS commencé
Source : `projet/source/PROJET_MBAO_Architecture_V2.pdf`, page index 16 (plan TERRASSE, cartouche D&F, IND. APS, échelle réelle à mesurer : les murs extérieurs mesurent 441.6 pt pour 8.57 m = 51.5 pt/m, PAS 56.693 comme le R+1 ; relever repère et épaisseurs sur le vectoriel, murs = polygones gris 0.75 contour noir).
Lecture de l'esquisse du client (mètres depuis l'angle extérieur NO ; murs 0.15) :
- CUISINE existante 5.28 x 4.83 (x 0.15-5.43, y 0.15-4.98) ; son mur est (x 5.43-5.58) s'arrête à y 3.72 : mur NEUF x 5.43-5.58 de y 3.72 à 4.98 pour la fermer ; fenêtre 2.00 x 1.25 dans le mur est, centrée y ~1.75 (0.75-2.75) ; porte 0.90 x 2.20 dans le mur sud (côté ESC), x ~0.30-1.20, ouvrant vers l'intérieur.
- TOILETTE neuve = 2.85 x 1.26 (x 5.58-8.42, y 3.72-4.98) = 3.59 m2 ; mur sud NEUF y 4.98-5.13 de x 5.58 à 8.42 (prolonge le mur nord de l'ESC) ; fenêtre 1.00 x 0.60 (allège 1.60) dans le mur nord, x ~7.20-8.20 ; porte 0.90 x 2.20 dans le mur sud, côté ouest, hypothèse (le client l'a dessinée près du coin SO) ; WC sous la fenêtre.
- BAC lessive / vaisselle (encadré bleu) : contre le mur sud de la toilette, côté terrasse, esquisse ~2.10 x 1.10 (x 6.32-8.42), h 0.40 (2 rangs de briques), robinets côté mur de la toilette ; conflit avec la porte (x 5.58-6.48) : décaler le bac à partir de x 6.55 (à confirmer par le client).
- À refaire : cote « 2.85 » existante (y ~5.9) qui traversera le bac ; surface TERRASSE (92.53) à recalculer sans la toilette ; livrer plan + tableau nom / surface / PÉRIMÈTRE des pièces (cuisine, toilette, ESC, terrasse), cotations exactes, même style (page source).
- Procédure : RAC-001..011 + `outils/controle_raccords.py` (murs neufs dans le prolongement exact, rendu identique à la source hors zones modifiées), vérificateur avant envoi ; image d'abord si doute.
Autres points ouverts : avis du client sur les 6 vues 3D ; correction éventuelle des noirs parasites du modèle 3D (10 min) ; prompts : artefact https://claude.ai/artifact/TkqYGLEVn3g3ufqdkwG1fn ; validation du PDF indice F.
