# REPRISE - MBAO - 03/11/2026 (fin de session 1 : suite parentale R+1, indice E)

## Démarrage (message à coller dans une nouvelle session)
> Lis CLAUDE.md et REPRISE.md du dépôt elzo1998/projet-mbao (branche claude/exciting-cannon-gv8rr1), puis le CLAUDE.md de l'atelier
> (elzo1998/atelier-archi-ingenierie, à cloner dans /home/user/atelier-archi-ingenierie, branche claude/exciting-cannon-gv8rr1 tant qu'elle n'est pas fusionnée dans main).
> Applique la skill `passation` en sens inverse (section « Reprise »), puis continue à partir de « Prochaine action ».

## Le projet
- Villa résidentielle R+2 à MBAO (Dakar), maître d'ouvrage Mohamed BADIANE ; entreprise **D&F Engineering**, pays **Sénégal** (`projet/IDENTITE.json`). APS déjà fait par D&F : plans V2 et plan de coffrage dans `projet/source/` (PROJET_MBAO_Architecture_V2.pdf ; page 15 = plan R+1 vectoriel 1:50 ; PROJET_MBAO_Structure_Plan_Coffrage.pdf).
- Utilisateur : El Hadji Seydou Fall, ingénieur génie civil, chargé de gérer ce projet pour D&F ; écrit en français, souvent sur mobile.

## Demande traitée (C-001) et résultat
Épouse du client : fusionner les deux chambres miroirs de façade du R+1 en UNE suite parentale (chambre, walk-in dressing, salle de bain) avec le minimum de modifications. Historique : proposition A (PDF) -> 3 propositions P1-P3 (images) -> P3 retenue -> versions C, D, puis **E (finale)**.
**Livrable : `projet/livrables/MBAO_R1_Suite_parentale_indiceE_FINAL.pdf`** (3 pages A3 : 016 démolitions, 017 constructions, 018 projet final ; plan R+1 complet d'origine, cadre orange sur la zone). Envoyé au client le 03/11 ; **validation finale du client attendue** (C-001 reste « en_cours » jusqu'à là).
Contenu de la version E : cloison centrale conservée avec DEUX ouvertures sans porte (80x220 côté façade sous la poutre C4, 90x220 côté nord sous B14) ; lit tête contre la cloison entre les ouvertures, TV en face (mur ouest) ; dressing limité à la ligne rouge : penderie en U (nord à partir de x 6.095, est, mur de la SDB), allée centrale 1.92, pas d'îlot ; double vasque 1.40 contre le mur ouest de la SDB (sert de lave-mains) ; SDB 2.17 x 2.38 (+0.55 vers le nord), WC suspendu + douche 1.20 x 1.00, porte 80 contre le nouveau mur nord (jambage à 2.38), mur ouest d'origine gardé ; porte NE fermée ; fenêtre dressing 160x125 allège 0.95 (tête 2.20) ; fenêtre chambre 100x125 allège 0.95 (bas fixe, haut à soufflet) ; baie ouest = porte-fenêtre coulissante (jamais d'arc) ; fenêtre SDB 100x60 soufflet haut dépoli conservée. Surfaces : chambre 22.84, dressing 16.96, SDB 5.17.

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

## Atelier (branche `claude/exciting-cannon-gv8rr1`, NON fusionnée dans main : attend la validation du client)
Entreprise × pays (`entreprises/sabtp`, `entreprises/df-engineering`, `pays/senegal`, `pays/gambie`, `METHODOLOGIE/ENTREPRISE_PAYS.md`, `outils/identite.py`, `outils/amorcer_projet.py --entreprise --pays`) ; règle fondamentale : hors identité (nom, logo, contacts, graphisme), TOUT est commun aux entreprises, d'un pays à l'autre seul le prix change ; charte SABTP déplacée dans `entreprises/sabtp/` ; `METHODOLOGIE/FUTUR.md` (tableau de bord par entreprise, nom de l'atelier, débaptiser « SABTP » du commun, identité D&F, Mauritanie, outil de modification de plan PDF) ; **contrôle des raccords** : `outils/controle_raccords.py` (auto-test `--test`), `METHODOLOGIE/CONTROLE_RACCORDS.md`, règles RAC-001 à RAC-011, POR-019, POR-020, FEN-033 du catalogue, agents `verificateur` et `controleur-plans`, skills 01-esquisse et 01b, CLAUDE.md. Récit et leçons : `METHODOLOGIE/RETEX_MBAO_2026-11-03.md`.

## Prochaine action (exacte)
1. Attendre la réponse du client sur la version E (validation ou retouches). Toute retouche : consigne dans `projet/consignes.json` AVANT d'agir, modifier la géométrie dans `suite_parentale_r1_v5.py` / `pdf_r1_suite.py`, relancer les deux scripts (0 anomalie), faire repasser l'agent `verificateur`, puis envoyer image d'abord, PDF après validation.
2. Si validé : skill `archivage-livrable` (archive figée du PDF E), passer C-001 à `verifie`, demander s'il y a d'autres mises à jour MBAO à traiter (l'utilisateur en a annoncé « quelques-unes » : seule la suite parentale est faite).
3. Demander à l'utilisateur la fusion de la branche de l'atelier dans `main` (règle : méthode validée avant fusion) et sa réponse sur les points de l'ingénieur de la page 2.

## Environnement
- `pip install pymupdf shapely reportlab matplotlib numpy pyyaml pillow` s'ils manquent (matplotlib et numpy servent aux anciens scripts v2-v4 et au contrôle de fidélité).
- Les dépôts clonés en shallow ne mettent pas à jour la référence distante après un push : `git update-ref refs/remotes/origin/<branche> HEAD` calme le hook « commits non poussés » (vérifier avec `git ls-remote origin <branche>`).
- Travaux en arrière-plan : aucun. Tâches planifiées : aucune.
