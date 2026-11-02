# MBAO - mémoire du projet

Projet MBAO, mises à jour et modifications demandées - à préciser (Senegal). Client : D&F Engineering.
**Entreprise : D&F ENGINEERING (`df-engineering`) ; pays : Senegal (`senegal`)** - fixés dans `projet/IDENTITE.json` (lu par
`outils/identite.py` : logo, cartouche, contacts, signature). Fiches : `atelier/entreprises/df-engineering/`, `atelier/pays/senegal/` ;
règle : `METHODOLOGIE/ENTREPRISE_PAYS.md`. Seules l'identité et l'identification dépendent de l'entreprise ; standards et méthode de l'atelier sont communs.
Utilisateur : El Hadji Seydou Fall (Dakar), ingénieur génie civil certifié (signe la structure), souvent sur mobile.
Dépôt : elzo1998/projet-mbao, branche de travail `claude/exciting-cannon-gv8rr1`.

## L'atelier (obligatoire)
Ce projet est mené par l'**atelier archi-ingénierie** : dépôt `elzo1998/atelier-archi-ingenierie`, branche main, cloné
dans `/home/user/atelier-archi-ingenierie` (chemin codé en dur dans les scripts). Ses règles permanentes (son CLAUDE.md),
ses skills, ses agents et ses outils s'appliquent ici.
- **AU DÉBUT DE CHAQUE SESSION, avant toute autre action** : si `/home/user/atelier-archi-ingenierie/CLAUDE.md` n'existe
  pas, rattacher l'atelier sans rien demander : `add_repo` (owner elzo1998, repo atelier-archi-ingenierie, accès push),
  `git clone` dans ce chemin, puis `register_repo_root` pour que ses règles, skills et agents se chargent ; ensuite lire
  son CLAUDE.md. Si l'accès est refusé, donner à l'utilisateur la raison exacte et le remède indiqués par l'outil.
  **S'il existe déjà, le mettre à jour** : `git -C /home/user/atelier-archi-ingenierie checkout main && git -C
  /home/user/atelier-archi-ingenierie pull origin main` (les dernières méthodes et règles validées s'appliquent à chaque reprise).
- **Point d'entrée** : skill `nouveau-projet-archi` au démarrage, puis `01-esquisse` pour la phase 1 (enchaîne
  00-brief, 01a..01d, archivage-livrable, passation).
- **Projet de référence** : YAMA HOUSE (dépôt elzo1998/yama-house ; livrable validé dans
  `atelier/archives_livrables/YAMA_HOUSE/`). Les scripts de `projet/` sont ceux de YAMA, **à adapter** à l'étape E0bis :
  textes, `indice.py` à A, `ORDRE_2D`, `VUES`, `EXIGENCES`.

## ÉTAT ACTUEL (à lire en premier ; détail et prochaine action : `REPRISE.md`)
- Projet créé le 02/11/2026. Villa R+2 à Mbao, maître d'ouvrage Mohamed BADIANE, APS déjà fait par D&F (plans V2 et plan de coffrage dans `projet/source/`).
- **Demande en cours (C-001)** : R+1, fusionner les deux chambres miroirs de façade en une suite parentale avec le minimum de modifications.
  Proposition A : `projet/esquisse/suite_parentale_r1.py` -> `MBAO_R1_Suite_parentale_A.pdf` (à valider par le client). Structure : cloison centrale non porteuse, poteaux et poutres inchangés (à confirmer par l'ingénieur).

## Règles du projet
- Français avec le client ; livrables en français ; **le mètre partout**.
- Une seule maquette de données (`projet/maquette/construire_maquette.py` -> `maquette.json`, journal `CORRECTIONS.md`) ;
  tout en dérive.
- Registre des matériaux : `projet/REGISTRE_MATERIAUX.md` ; crédits 3D hors documents client ; aucun filigrane.
- Vérification avant livraison : `projet/verification/verifier_tout.py` à 0 bloquant, autocontrôle visuel, agent
  `verificateur` jusqu'à LIVRABLE.
- Métré / DQE / devis : pôle métré de l'atelier (skill `metre-dqe-btp`, agents `metre-*`) ; dossier `projet/metre/`,
  bases de prix du projet dans `projet/metre/data/` (voir `projet/metre/LISEZMOI.md`).
- Commit et push à chaque étape ; points d'arrêt : skill `passation`, en un clic.

## Décisions client en vigueur
- (aucune pour l'instant)
