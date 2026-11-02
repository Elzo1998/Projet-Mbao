"""YAMA HOUSE - vérification automatique complète avant livraison (étapes PRO-001 du catalogue).

python3 -I projet/verification/verifier_tout.py  ->  projet/verification/rapport_auto.json + résumé à l'écran
  1. contrôles 2D de la maquette (controle_degagements.py : dégagements, portes, standards SABTP, adossement,
     placards hauts, auvents, appuis, crédences, symboles) sur chaque niveau ;
  2. vérifications 3D (verif_3d.py : collisions, appuis, sols, faces superposées visibles, vitrages, passages des
     portes, échappées, caméras, K-REVETEMENT) sur la maquette 3D complète et les caméras des vues intérieures ;
  3. fichiers livrés (controle_fichiers.py) : textes superposés / hors feuille, audit des DXF, taille du PDF.
Code de sortie 1 s'il reste un constat bloquant.
"""
import json, os, sys, math, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = '/home/user/atelier-archi-ingenierie/outils'
sys.path.insert(0, OUT)
import controle_degagements as cd

rapport = {'2D': {}, '3D': []}
MAQ = json.load(open(os.path.join(ROOT, 'projet', 'maquette', 'maquette.json')))
for n, M in MAQ['niveaux'].items():
    rapport['2D'][n] = cd.controler(dict(M, z=M['z']))
rapport['2D']['FF'] += cd.controle_porteurs(MAQ) + cd.controle_porteurs(MAQ, 'FF', 'RF') + cd.controle_poteaux(MAQ)   # K-PORTEUR (STR-010, STR-011)
rapport['2D']['GF'] += cd.controle_stationnement(MAQ) + cd.controle_bords_deck(MAQ)   # K-STATIONNEMENT, K-BORD (SIT-012, SIT-015)

# parcours (CIR-022) : les trajets du fichier de contrôle des circulations, recalculés sur la maquette
sys.path.insert(0, os.path.join(ROOT, 'projet', 'controle'))
import parcours as pc
from controle_parcours import ROUTES
import sys as _s, os as _o; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))), 'esquisse')); from indice import REV, REVISIONS
for niv, L in ROUTES.items():
    for num, nom, coul, etapes in L:
        r = pc.parcours(MAQ, niv, etapes)
        if r['manquants']: rapport['2D'][niv].append({'controle': 'K-PARCOURS', 'texte': 'parcours %d (%s) : %d étape(s) inaccessible(s)' % (num, nom, len(r['manquants']))})
        if r['largeur'] is not None and r['largeur'] < 0.60:
            rapport['2D'][niv].append({'controle': 'K-PARCOURS', 'texte': 'parcours %d (%s) : passage de %.2f en %s' % (num, nom, r['largeur'], [round(v, 2) for v in r['point']])})
        for a, b, lg, dr in r.get('detours', []):
            rapport['2D'][niv].append({'controle': 'K-PARCOURS', 'texte': 'parcours %d (%s) : détour %.1f m pour %.1f m à vol d\'oiseau (obstacle ?)' % (num, nom, lg, dr)})

# 3D : construction de la maquette complète (Blender) puis vérification
V3 = os.path.join(ROOT, 'projet', 'vues3d', 'rendre_3d.py')
g = {'__file__': V3, '__name__': 'verif'}
exec(compile(open(V3).read().split("if __name__")[0], V3, 'exec'), g)
import verif_3d as v3
S = g['construire']('complet')
vues = g['vues_interieures']()
T, info = v3._bvh(S)
for k, v in vues.items():                       # même correction automatique des caméras que pour le rendu
    for _ in range(4):
        if not v3.cameras(S, T, info, {k: v}): break
        p, c = v['pos'], v['cible']; d = math.dist(p[:2], c[:2]) or 1
        v['pos'] = (p[0] + 0.30 * (c[0] - p[0]) / d, p[1] + 0.30 * (c[1] - p[1]) / d, p[2])
rapport['3D'] = v3.verifier(S, vues)
# M3D-030 (client 15/10) : caméras extérieures = dans la parcelle à 0.50 au moins de la clôture, ou sur la rue publique
# (au sud du mur), ou vue aérienne (z >= 10) ; jamais chez un voisin ni dans / contre un mur ; + mêmes contrôles 3D que l'intérieur
_cl = MAQ['site']['cloture']; (_X0, _Y0), (_X1, _Y1) = _cl['nu_interieur'][0], _cl['nu_interieur'][2]; _e = _cl['epaisseur']
_ext = {k: v for k, v in g['VUES'].items() if k.startswith('ext_') and v.get('pos')}
for k, v in _ext.items():
    x, y, z = v['pos']
    dedans = _X0 + 0.5 <= x <= _X1 - 0.5 and _Y0 + 0.5 <= y <= _Y1 - 0.5
    rue = y <= _Y0 - _e - 0.5
    if not (dedans or rue or z >= 10):
        rapport['3D'].append({'regle': 'M3D-030', 'gravite': 'B', 'texte': 'caméra %s en (%.2f ; %.2f ; %.2f) : ni dans la parcelle à 0.50 '
                              'de la clôture, ni sur la rue, ni aérienne (chez un voisin ou contre un mur)' % (k, x, y, z)})
rapport['3D'] += v3.cameras(S, T, info, _ext)
# retex phase 1 (16/10) : arbres devant une porte ou une caméra (SIT-004, M3D-031)
import controle_vues as cv
rapport['3D'] += cv.arbres_genants(MAQ, _ext)
rapport['elements_3d'] = len(S.elements)

# 3. fichiers livrés (DOC-033, DOC-035) : textes qui se chevauchent ou sortent de la feuille, audit des DXF, taille du PDF
import glob, controle_fichiers as cf
ESQ = os.path.join(ROOT, 'projet', 'esquisse')
rapport['fichiers'] = []
for f in sorted(glob.glob(os.path.join(ESQ, f'SD-0*_{REV}_*.pdf'))): rapport['fichiers'] += cf.textes(f) + cf.traces_hors_cadre(f)
rapport['fichiers'] += cf.exposition(sorted(glob.glob(os.path.join(ROOT, 'projet', 'vues3d', 'rendus', 'int_*.png'))))
for f in sorted(glob.glob(os.path.join(ESQ, f'SD-0*_{REV}_*.dxf'))): rapport['fichiers'] += cf.dxf(f)
rapport['fichiers'] += cf.jeu_complet([f for f in sorted(glob.glob(os.path.join(ESQ, f'SD-0*_{REV}_*.pdf'))) if 'SD-000' not in f])   # DOC-049
for f in glob.glob(os.path.join(ESQ, f'YAMA_HOUSE_Schematic_Design_rev{REV}.pdf')): rapport['fichiers'] += cf.taille(f)
# PRG-001 : chaque exigence forte du programme se lit sur sa planche (retex 16/10 : jacuzzi + baignoire)
import pymupdf as _pm
_txt = {os.path.basename(f)[:6]: ''.join(p.get_text() for p in _pm.open(f)) for f in glob.glob(os.path.join(ESQ, f'SD-0??_{REV}_*.pdf'))}
rapport['fichiers'] += cv.exigences(MAQ, _txt)
# DOC-037 : planches, rendus 3D et PDF assemblé plus récents que la maquette (sinon périmés)
# planches et PDF : date ; rendus 3D : empreinte géométrique de la maquette inscrite au rendu (un changement de texte
# seul ne périme pas un rendu ; un changement de géométrie, si)
from empreinte import empreinte
t_maq = os.path.getmtime(os.path.join(ROOT, 'projet', 'maquette', 'maquette.json')); emp = empreinte(MAQ)
livres = sorted(glob.glob(os.path.join(ESQ, f'SD-0*_{REV}_*.pdf')) + glob.glob(os.path.join(ESQ, f'YAMA_HOUSE_Schematic_Design_rev{REV}.pdf'))
                + glob.glob(os.path.join(ROOT, 'projet', 'vues3d', f'YAMA_3D_schematique_rev{REV}.pdf')))
perimes = [os.path.basename(f) for f in livres if os.path.getmtime(f) < t_maq]
for f in glob.glob(os.path.join(ROOT, 'projet', 'vues3d', 'rendus', '*.png')):
    j = f[:-4] + '.json'
    m = json.load(open(j)) if os.path.exists(j) else {}
    if m.get('empreinte') != emp: perimes.append(os.path.basename(f))
if perimes:
    rapport['fichiers'].append({'controle': 'DOC-037', 'gravite': 'B', 'texte': '%d fichier(s) plus ancien(s) que la maquette : %s' % (len(perimes), ', '.join(perimes[:6]) + (' ...' if len(perimes) > 6 else ''))})

json.dump(rapport, open(os.path.join(HERE, 'rapport_auto.json'), 'w'), indent=1, ensure_ascii=False)
bloq = 0
for n, R in rapport['2D'].items():
    vrais = [c for c in R if not c.get('info')]
    bloq += len(vrais)
    print('2D', n, len(vrais), 'constat(s)', '+', len(R) - len(vrais), 'information(s)')
    for c in R: print('   ', c['controle'], '(info)' if c.get('info') else '', c['texte'])
cpt = collections.Counter(c['gravite'] for c in rapport['3D'])
bloq += cpt.get('B', 0)
print('3D', len(S.elements), 'éléments ;', len(rapport['3D']), 'constat(s) :', dict(cpt))
for c in rapport['3D']: print('   ', c['regle'], c['gravite'], c['texte'])
print('Fichiers :', len(rapport['fichiers']), 'constat(s)')
for c in rapport['fichiers']: print('   ', c['controle'], c['gravite'], c['texte'])
bloq += sum(1 for c in rapport['fichiers'] if c['gravite'] in 'BI')    # un texte illisible ne part pas chez le client
print('BLOQUANTS', bloq)
sys.exit(1 if bloq else 0)
