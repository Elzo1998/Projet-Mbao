#!/bin/sh
# rendu de toutes les vues 3D schématiques (arrière-plan) ; fin = rendus/tout_done.txt ; échec = rendus/echec.txt
# (leçon 15/10 : un plantage Python ne doit jamais être suivi d'un « terminé »)
cd "$(dirname "$0")"
rm -f rendus/*_done.txt rendus/echec.txt
for v in rdc etage complet; do
  python3 -I rendre_3d.py $v > rendus/log_$v.txt 2>&1 || echo "$v : code $? (voir rendus/log_$v.txt)" >> rendus/echec.txt
done
if [ -f rendus/echec.txt ]; then date >> rendus/echec.txt; else date > rendus/tout_done.txt; fi
