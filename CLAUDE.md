<!-- MODELE-PROJET-ARCHI-AMORCE : ce fichier est remplacé par le CLAUDE.md du projet lors de l'amorçage -->
# Nouveau projet de l'atelier archi-ingénierie (SABTP) - démarrage automatique

**À faire AU DÉBUT DE LA SESSION, avant de répondre à quoi que ce soit, sans rien demander à l'utilisateur :**

1. Rattacher l'atelier, si `/home/user/atelier-archi-ingenierie/CLAUDE.md` n'existe pas :
   - outil `add_repo` (owner `elzo1998`, repo `atelier-archi-ingenierie`, accès `push`) ;
   - `git clone` du dépôt indiqué par l'outil dans `/home/user/atelier-archi-ingenierie` (branche main) ;
   - outil `register_repo_root` (owner `elzo1998`, repo `atelier-archi-ingenierie`, directory
     `/home/user/atelier-archi-ingenierie`), pour que ses règles, skills et agents se chargent.
   Si `add_repo` refuse l'accès, donner à l'utilisateur la raison exacte et le remède indiqués par l'outil, puis
   s'arrêter.
2. Lire `/home/user/atelier-archi-ingenierie/CLAUDE.md` : ses règles permanentes s'appliquent à ce projet.
3. Appliquer la skill **`nouveau-projet-archi`** de l'atelier (fichier
   `/home/user/atelier-archi-ingenierie/.claude/skills/nouveau-projet-archi/SKILL.md`, à lire directement si la skill
   n'apparaît pas encore dans la liste) : elle copie le gabarit, remplace ce fichier par la mémoire du projet, inscrit
   le projet au registre, demande les informations du projet, puis lance l'étape 0 et la phase 1.

L'utilisateur (El Hadji Seydou Fall, ingénieur génie civil, Dakar) écrit en français, souvent depuis son téléphone :
réponses courtes.
