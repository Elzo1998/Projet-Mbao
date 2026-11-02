# Métré du projet (pôle métré de l'atelier)

Méthode : skill `metre-dqe-btp` de l'atelier (`/home/user/atelier-archi-ingenierie/.claude/skills/metre-dqe-btp/`), agents
`metre-*` (`.claude/agents/LISEZMOI.md` de l'atelier). Sources des quantités : `projet/maquette/maquette.json` et
`projet/REGISTRE_MATERIAUX.md` (règle DOC-040) ; le dossier `projet/structure/` prime pour le gros œuvre s'il existe.

Bases de prix propres au projet (modifiables sans toucher à l'atelier), à créer à la première utilisation :

    S=/home/user/atelier-archi-ingenierie/.claude/skills/metre-dqe-btp
    export PYTHONDONTWRITEBYTECODE=1   # pas de __pycache__ dans l'atelier
    mkdir -p projet/metre/data && cp -n $S/data/* projet/metre/data/
    python3 $S/scripts/build_classeur.py projet/metre/projet.json projet/metre/DQE_OFFRE_1.xlsx --base projet/metre/data/base_prix.json
    python3 $S/scripts/recalc.py projet/metre/DQE_OFFRE_1.xlsx && python3 $S/scripts/verif.py projet/metre/DQE_OFFRE_1.xlsx

Gambie : `python3 $S/scripts/build_boq.py projet/metre/projet_boq.json projet/metre/BOQ.xlsx` puis `recalc.py` ; les coûts de
revient de chaque article sont repris (champ `cout_revient`) de `projet/metre/data/prix_gambie.json`, le script ne lit pas cette base. Un prix durable validé par le gérant remonte à la base
de l'atelier (proposition, puis mise à jour et `metre-verificateur-final`).
