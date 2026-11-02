"""YAMA HOUSE - plans de circulation (dossier client, SD-004B / SD-005B, avant les plans d'architecture ; demande client 15/10).

python3 -I projet/controle/controle_parcours.py  ->  projet/esquisse/SD-004B_C_Circulation_Ground_Floor.pdf, SD-005B_C_Circulation_First_Floor.pdf

Les trajets ne sont pas dessinés à la main : ils sont calculés sur la maquette (outil atelier parcours.py : espace libre =
murs, fenêtres, mobilier, escaliers, garde-corps, voitures retirés ; plus court chemin A* pour une personne de 0.50 ;
largeur libre mesurée perpendiculairement au trajet). Chaque trajet donne sa longueur et son point le plus étroit.
Les volées d'escalier sont tracées le long de leur ligne de foulée (maquette).
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'projet', 'esquisse')); sys.path.insert(0, '/home/user/atelier-archi-ingenierie/outils')
import dessiner_plans as dpl
import dessin_plan as dp
import parcours as pc
from shapely.geometry import LineString, box
import sys as _s, os as _o; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))), 'esquisse')); from indice import REV, REVISIONS
MAQ = dpl.MAQ

BRUN = (0.55, 0.33, 0.12)   # escalier (le rouge est réservé au point trop étroit)
BLEU, ORANGE, VERT, VIOLET, ROUGE, CYAN = (0.10, 0.40, 0.85), (0.95, 0.50, 0.05), (0.10, 0.62, 0.25), (0.55, 0.20, 0.75), (0.85, 0.10, 0.15), (0.0, 0.62, 0.70)
ROUTES = {
    'GF': [(1, 'Arrival: wicket door - pedestrian lane - steps - D03 - hall', BLEU, [(14.75, -6.75), (14.75, -1.0), 'ENTRANCE HALL']),
           (2, 'Kitchen: hall - kitchen - scullery - service door D10', ORANGE, ['ENTRANCE HALL', 'KITCHEN / DINING', 'SCULLERY / AFRICAN KITCHEN', (4.93, 14.85)]),
           (3, 'Living: hall - living room - SD01 - pavilion - garden steps', VERT, ['ENTRANCE HALL', 'LIVING ROOM', (11.2, -0.6), (11.2, -4.6)]),
           (4, 'Night zone: hall - corridor - bedrooms, en-suite, bath, WC', VIOLET, ['ENTRANCE HALL', 'CORRIDOR', 'BEDROOM 1', 'EN-SUITE 1', 'BEDROOM 2', 'SHARED BATH', 'BEDROOM 3', 'WC']),
           (5, 'Stair: hall - stair up to the first floor', BRUN, ['ENTRANCE HALL', (12.43, 6.60)])],
    'FF': [(5, 'Stair (cont.): arrival - landing - stair up to the roof terrace', BRUN, [(8.40, 9.05), 'LANDING', (8.10, 6.30)]),
           (6, 'Family lounge - east balcony', VERT, ['LANDING', 'FAMILY LOUNGE', (13.85, 12.70)]),
           (7, 'Master suite: bedroom - dressing - bath; south balcony', VIOLET, ['LANDING', 'MASTER BEDROOM', 'WALK-IN DRESSING', 'MASTER BATH']),
           (8, 'Master bedroom - south balcony', CYAN, ['MASTER BEDROOM', (3.2, -0.6)]),
           (9, 'Roof terrace (+3.95)', ORANGE, ['LANDING', 'ROOF TERRACE']),
           (10, 'First-floor WC', BLEU, ['LANDING', 'WC'])],
}
# volées (ligne de foulée, maquette) : RDC A + palier + B ; étage C + palier + D jusqu'à la porte de l'édicule
ESC = {'GF': [(5, BRUN, [(12.43, 6.60), (12.43, 9.05), (8.40, 9.05)])],
       'FF': [(5, BRUN, [(8.10, 6.30), (12.43, 6.30), (12.43, 9.05), (12.45, 9.70)])]}


EVITER = []      # (boîtes de texte, pastilles) remplies par planche()


def fleches(D, pts, coul, pas=1.1):
    """Bande translucide + pointes de flèche le long du trajet."""
    li = LineString(pts)
    if li.length < 0.05: return
    g = li.buffer(0.13, cap_style=2, join_style=2)
    for part in getattr(g, 'geoms', [g]):
        D.poly(list(part.exterior.coords), 'A-CTRL', 0.0, coul, fond=coul, alpha=0.30)
    d = 0.55
    while d < li.length - 0.2:
        p = li.interpolate(d); q = li.interpolate(min(li.length, d + 0.05)); r = li.interpolate(max(0.0, d - 0.05))
        if any(g_.distance(p) < 0.30 for g_ in EVITER): d += 0.20; continue
        tx, ty = q.x - r.x, q.y - r.y; n = math.hypot(tx, ty) or 1; tx, ty = tx / n, ty / n
        D.poly([(p.x + 0.24 * tx, p.y + 0.24 * ty), (p.x - 0.16 * tx - 0.18 * ty, p.y - 0.16 * ty + 0.18 * tx),
                (p.x - 0.16 * tx + 0.18 * ty, p.y - 0.16 * ty - 0.18 * tx)], 'A-CTRL', 0.0, coul, fond=coul, alpha=0.80)
        d += pas


def nature(M, p):
    """Le point étroit est-il une porte (seuil = largeur de la porte - 0.10), une circulation (hall, couloir, palier :
    0.90) ou un passage entre meubles dans une pièce (0.70, usage courant Neufert) ?"""
    for o in M['ouvertures']:
        if o['type'] != 'fenetre' and box(*o['rect']).buffer(0.30).contains(box(p[0], p[1], p[0] + 1e-6, p[1] + 1e-6)):
            w = (o['rect'][2] - o['rect'][0]) if o['axe'] == 'x' else (o['rect'][3] - o['rect'][1])
            return 'door %s' % o.get('repere', ''), w - 0.10
    from shapely.geometry import Point, Polygon
    for pi in M['pieces']:
        if pi.get('nom') and Polygon(pi['contour']).buffer(0.05).contains(Point(p)):
            if any(k in pi['nom'] for k in ('HALL', 'CORRIDOR', 'LANDING')): return 'circulation', 0.90
            return 'between furniture', 0.70
    return 'passage', 0.90


def planche(niv, titre, numero, client=False, sortie=None):
    M = MAQ['niveaux'][niv]
    D, cadre_m = dpl.construire_dessin(niv)
    lignes = []; res = []; pastilles = []; a_dessiner = []; trajets = []
    # zones à éviter par les pastilles : tous les textes déjà dessinés (noms, surfaces, libellés, FFL), boîte approchée
    textes0 = [q for q in D.P if q[0] == 't']
    boites = [box(q[2][0] - 0.065 * len(q[3]) * q[4] / 0.20 - 0.05, q[2][1] - q[4] * 0.6, q[2][0] + 0.065 * len(q[3]) * q[4] / 0.20 + 0.05, q[2][1] + q[4] * 0.9)
              for q in textes0 if q[6]]
    for num, nom, coul, etapes in ROUTES[niv]:
        r = pc.parcours(MAQ, niv, etapes)
        res.append((num, nom, r))
        if not r['trajet']: lignes.append(('%d  %s: NOT FOUND' % (num, nom), '')); continue
        trajets.append((r['trajet'], coul))
        # pastille du numéro : au départ, ou plus loin sur le trajet si une autre pastille y est déjà (trajets partant du hall)
        li = LineString(r['trajet']); d = 0.0
        while d < li.length and (any(math.dist((li.interpolate(d).x, li.interpolate(d).y), q) < 0.75 for q in pastilles) or any(b_.distance(li.interpolate(d)) < 0.26 for b_ in boites)): d += 0.20
        a = (li.interpolate(d).x, li.interpolate(d).y); pastilles.append(a)
        a_dessiner.append((a, num, coul))
        nat, seuil = nature(M, r['point']); w = r['largeur']
        etat = 'OK' if w >= seuil - 0.05 else ('check' if w >= 0.60 else 'TOO NARROW')
        D.cercle(r['point'], 0.18, 'A-CTRL', 0.8, (0.85, 0.1, 0.1) if etat != 'OK' else coul)
        lignes.append(('%d  %s' % (num, nom), ''))
        lignes.append(('     %.1f m; narrowest %.2f (%s): %s' % (r['longueur'], w, nat, etat), ''))
        if r['manquants']: lignes.append(('     unreachable leg(s): %d' % len(r['manquants']), ''))
    from shapely.geometry import Point as _Pt
    EVITER[:] = boites + [_Pt(a).buffer(0.24) for a in pastilles]      # flèches : ni sur un texte ni sur une pastille (vérificateur 7)
    for t_, coul in trajets: fleches(D, t_, coul)
    for num, coul, pts in ESC[niv]:
        fleches(D, pts, coul)
    for a, num, coul in a_dessiner:                  # pastilles au-dessus des flèches (vérificateur 7)
        D.cercle(a, 0.24, 'A-CTRL', 0.5, coul, fond=(1, 1, 1)); D.texte(a, str(num), 0.20, 'A-CTRL', True, coul=coul)
    D.P = [q for q in D.P if q[0] != 't' or q not in textes0] + textes0     # étiquettes du plan au-dessus des bandes (vérificateur 6)
    legende = {'titre_vue': titre, 'sous_titre_vue': (f'Scale 1:100   -   Revision {REV}   -   how to move around the house' if client else
                                                      'CONTROL FILE - circulation simulation - not for issue'), 'numero_vue': '1' if client else numero,
               'blocs': ([{'titre': 'ROUTES (computed on the design model)', 'lignes': lignes}]
                         + ([{'titre': 'REVISIONS', 'lignes': [('C  15/10/2026  first issue', ''), REVISIONS[-1]]}] if client else [])),
               'symboles': []}
    carto = (dict(dpl.CARTO, vue='Circulation', planche=numero, sous_titre=titre.split(' - ')[-1]) if client else
             dict(dpl.CARTO, vue='CONTROL', planche='CTRL - %s' % numero, sous_titre='Circulation simulation', phase='CONTROL FILE'))
    sortie = sortie or os.path.join(HERE, '_parcours_%s.pdf' % niv)
    dp.rendre_pdf(D, sortie, {'pt': (16, 40, 745, 822), 'm': cadre_m}, carto, legende)
    if client: dp.rendre_dxf(D, sortie[:-4] + '.dxf')         # DOC-049 : chaque planche du dossier a son DXF
    return sortie, res


if __name__ == '__main__':
    # (demande client 15/10) : les plans de circulation font partie du dossier client, avant les plans d'architecture
    ESQ = os.path.join(ROOT, 'projet', 'esquisse'); bilan = {}
    for niv, titre, num, nom in (('GF', 'Circulation - Ground floor + site', 'SD - 004B', f'SD-004B_{REV}_Circulation_Ground_Floor'),
                                 ('FF', 'Circulation - First floor', 'SD - 005B', f'SD-005B_{REV}_Circulation_First_Floor')):
        f, res = planche(niv, titre, num, client=True, sortie=os.path.join(ESQ, nom + '.pdf'))
        bilan[niv] = [{'route': n, 'nom': nom, 'longueur': round(r['longueur'], 2), 'largeur_mini': r['largeur'] and round(r['largeur'], 2),
                       'point': r['point'], 'manquants': len(r['manquants'])} for n, nom, r in res]
    json.dump(bilan, open(os.path.join(HERE, 'parcours_bilan.json'), 'w'), indent=1, ensure_ascii=False)
    for niv, L in bilan.items():
        for b in L: print(niv, b['route'], b['nom'][:40], b['longueur'], b['largeur_mini'], b['manquants'])
