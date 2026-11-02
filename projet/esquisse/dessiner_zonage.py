"""YAMA HOUSE - plans de zonage par fonction (demande client 15/10) : une trame de couleur par type de pièce, surfaces
par zone calculées depuis la maquette. Placés dans le dossier client avant les plans d'architecture.

python3 -I projet/esquisse/dessiner_zonage.py  ->  SD-004A_C_Zoning_Ground_Floor.pdf, SD-005A_C_Zoning_First_Floor.pdf
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, '/home/user/atelier-archi-ingenierie/outils')
import dessiner_plans as dpl
import dessin_plan as dp
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
import sys as _s, os as _o; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))), 'esquisse')); from indice import REV, REVISIONS
MAQ = dpl.MAQ

# fonction -> (motif des noms de pièces, couleur de trame, libellé anglais)
# (retour client 15/10, indice D) couleurs seules, sans hachures (lisibilité du contenu des pièces) ; trame None
ZONES = [('night', r'BEDROOM', (0.98, 0.62, 0.25), 'Bedrooms (night)', None),
         ('dressing', r'DRESSING|LINEN', (0.72, 0.55, 0.85), 'Dressing, linen (storage)', None),
         ('wet', r'BATH|EN-SUITE|^WC$', (0.30, 0.60, 0.95), 'Bathrooms, shower rooms, WCs', None),
         ('day', r'LIVING|LOUNGE', (0.35, 0.75, 0.40), 'Living spaces (day)', None),
         ('kitchen', r'KITCHEN|SCULLERY', (0.98, 0.85, 0.25), 'Kitchen, scullery (service)', None),
         ('circulation', r'HALL|CORRIDOR|LANDING', (0.70, 0.70, 0.70), 'Circulation (hall, corridor, landing)', None),
         ('outdoor', r'TERRACE', (0.55, 0.80, 0.80), 'Outdoor (terraces, veranda)', None)]
ALPHA = 0.42


def zone_de(nom):
    for k, motif, c, lib, _t in ZONES:
        if re.search(motif, nom): return k
    return None


def planche(niv, titre, numero, sortie):
    M = MAQ['niveaux'][niv]
    D, cadre_m = dpl.construire_dessin(niv)
    surf = {k: 0.0 for k, *_ in ZONES}
    coul = {k: c for k, m, c, l, t in ZONES}; trm = {k: t for k, m, c, l, t in ZONES}
    fonce = lambda c: tuple(0.55 * x for x in c)
    reserves = [dp.reserve_etiquette(q, M) for q in M['pieces'] if q.get('nom')]   # étiquettes non barrées (vérificateur 6)
    for p in M['pieces']:
        nom = p.get('nom')
        if not nom: continue
        k = zone_de(nom)
        if not k: continue
        D.poly(p['contour'], 'A-CTRL', 0.0, coul[k], fond=coul[k], alpha=ALPHA)
        dp.trame(D, p['contour'], trm[k], fonce(coul[k]), trous=reserves)
        surf[k] += p.get('surface_affichee') or p['surface_calculee']
    # extérieurs : balcons (étage), véranda et pavillon (RDC)
    ext = []
    if niv == 'FF':
        ext = [box(*s_['rect']) for s_ in M['exterieurs']['sols'] if s_['nom'] == 'BALCONY']
    else:
        ext = [Polygon(MAQ['site']['deck']['contour'])]
    for g in ext:
        D.poly(list(g.exterior.coords), 'A-CTRL', 0.0, coul['outdoor'], fond=coul['outdoor'], alpha=ALPHA)
        dp.trame(D, list(g.exterior.coords), trm['outdoor'], fonce(coul['outdoor']), trous=reserves)
        surf['outdoor'] += g.area
    lignes = []
    for k, motif, c, lib, _t in ZONES:
        if surf[k] > 0: lignes.append(('%s' % lib.split(' - ')[0], '%.1f m²' % surf[k]))
    hab = sum(v for k, v in surf.items() if k != 'outdoor')
    lignes.append(('*Total indoor (net)', '%.1f m²' % hab))
    legende = {'titre_vue': titre, 'sous_titre_vue': f'Scale 1:100   -   Revision {REV}   -   functional zoning', 'numero_vue': '1',
               'blocs': [{'titre': 'ZONES (areas computed from the model)', 'lignes': lignes},
                         {'titre': 'REVISIONS', 'lignes': [('C  15/10/2026  first issue', ''), REVISIONS[-1]]}],
               'symboles': [({'ep': 6.0, 'coul': tuple(1 - ALPHA + ALPHA * x for x in c), 'trame': t or 'aucune', 'coul_trame': tuple(0.55 * x for x in c)}, lib) for k, m, c, lib, t in ZONES if surf[k] > 0]}   # pastille = teinte réelle de l'aplat
    carto = dict(dpl.CARTO, vue='Functional zoning', planche=numero, sous_titre=titre.split(' - ')[-1])
    dp.rendre_pdf(D, sortie, {'pt': (16, 40, 745, 822), 'm': cadre_m}, carto, legende)
    dp.rendre_dxf(D, sortie[:-4] + '.dxf')                    # DOC-049 : chaque planche a son DXF
    return sortie, surf


if __name__ == '__main__':
    for niv, titre, num, nom in (('GF', 'Functional zoning - Ground floor', 'SD - 004A', f'SD-004A_{REV}_Zoning_Ground_Floor'),
                                 ('FF', 'Functional zoning - First floor', 'SD - 005A', f'SD-005A_{REV}_Zoning_First_Floor')):
        f, s = planche(niv, titre, num, os.path.join(HERE, nom + '.pdf'))
        print(f, {k: round(v, 1) for k, v in s.items() if v})
