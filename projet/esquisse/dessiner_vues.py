"""YAMA HOUSE - toiture, façades et coupes de l'esquisse indice B (fond relu sur l'esquisse d'origine + éléments de la
maquette : ouvertures, grilles, mobilier en coupe, portail, cage de gaz).

python3 -I projet/esquisse/dessiner_vues.py  ->  projet/esquisse/SD-006_B ... SD-012_B (.pdf + .dxf)
"""
import re, json, os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
ATELIER = '/home/user/atelier-archi-ingenierie'
sys.path.insert(0, os.path.join(ATELIER, 'outils'))
import dessin_plan as dp, vue_relue as vr, pdf_facade as pf
from shapely.geometry import Polygon, Point, LineString, box

PDF = os.path.join(ROOT, 'projet', 'source', 'YAMA_HOUSE_Architectural_Design_realistic_v2.pdf')
MAQ = json.load(open(os.path.join(ROOT, 'projet', 'maquette', 'maquette.json')))
W, H = 13.10, 14.30
sys.path.insert(0, HERE)
from dessiner_plans import CARTO, DATE
import sys as _s, os as _o; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))), 'esquisse')); from indice import REV, REVISIONS, noter

VERRE = (0.44, 0.55, 0.61); ANTH = (0.23, 0.24, 0.26); BOIS = (0.6, 0.42, 0.26); MEUBLE = (0.91, 0.91, 0.89)
PORTES_EXT = {'D03': ('wood', BOIS), 'D10': ('metal', ANTH)}     # D03 : acier blindé finition bois ; D10 : acier


def ouvertures_facade(fac):
    out = []
    for n in ('GF', 'FF'):
        for o in MAQ['niveaux'][n]['ouvertures']:
            if o.get('facade') != fac or 'z_bas' not in o: continue
            x0, y0, x1, y1 = o['rect']
            a0, a1 = {'S': (x0, x1), 'N': (W - x1, W - x0), 'E': (y0, y1), 'W': (H - y1, H - y0)}[fac]
            out.append(dict(o, a0=a0, a1=a1, niveau=n))
    return out


def ouvertures_origine(fac):
    """Ouvertures du PDF d'origine (extraction brute) sur la façade : servent au recalage et au retrait du fond."""
    out = []
    for n in ('GF', 'FF'):
        B = json.load(open(os.path.join(ROOT, 'projet', 'maquette', 'extraction', n + '_brut.json')))
        for o in B['ouvertures']:
            if o['type'] in ('traversee', 'passage'): continue
            x0, y0, x1, y1 = o['rect']
            f = 'S' if y0 < 0.01 else 'N' if y1 > H - 0.01 else 'E' if x1 > W - 0.01 else 'W' if x0 < 0.01 else None
            if f != fac: continue
            a0, a1 = {'S': (x0, x1), 'N': (W - x1, W - x0), 'E': (y0, y1), 'W': (H - y1, H - y0)}[fac]
            out.append({'id': o.get('id', ''), 'a0': a0, 'a1': a1, 'type': o['type'], 'niveau': n})
    return out


def rect(u0, z0, u1, z1):
    return [(u0, z0), (u1, z0), (u1, z1), (u0, z1)]


def dessiner_ouverture(D, o, u0, u1, z0, z1, grille=False):
    rep = o.get('repere', '')
    if rep in PORTES_EXT:
        mat, col = PORTES_EXT[rep]
        D.poly(rect(u0, z0, u1, z1), 'A-DOOR', 0.5, (0.12, 0.12, 0.12), fond=col)
        vantaux = [(u0, u1)]
        if o.get('vantail2'):          # porte d'entrée 1.00 + 0.50 (grand vantail côté séjour = côté sud)
            L2 = math.dist(o['vantail2']['charniere'], o['vantail2']['vantail_ouvert'])
            sud_a_gauche = o.get('facade') == 'E'
            vantaux = [(u0, u1 - L2), (u1 - L2, u1)] if sud_a_gauche else [(u0, u0 + L2), (u0 + L2, u1)]
        for a, b in vantaux:
            D.poly(rect(a, z0, b, z1), 'A-DOOR', 0.5, (0.12, 0.12, 0.12), fond=col)
            if mat == 'wood':
                n = max(2, int((b - a) / 0.15))
                for i in range(1, n):
                    u = a + i * (b - a) / n; D.ligne((u, z0 + 0.02), (u, z1 - 0.02), 'A-DOOR', 0.25, (0.37, 0.25, 0.14))
            else:
                D.poly(rect(a + 0.08, z0 + 0.08, b - 0.08, z1 - 0.08), 'A-DOOR', 0.3, (0.1, 0.1, 0.1))
        a, b = vantaux[0]
        D.ligne((b - 0.12, z0 + 0.95), (b - 0.12, z0 + 1.30), 'A-DOOR', 0.9, (0.95, 0.95, 0.95))
        return
    hauteurs = o.get('empilement') or [[z0, z1]]
    for z0_, z1_ in hauteurs:
        D.poly(rect(u0, z0_, u1, z1_), 'A-GLAZ', 0.5, ANTH, fond=VERRE)
        L = u1 - u0; n = 1 if L < 0.7 else (2 if L <= 2.01 else 3)   # standard : panneaux de 1.00 maximum ; 0.60 = soufflet
        for i in range(1, n):
            u = u0 + i * L / n; D.ligne((u, z0_), (u, z1_), 'A-GLAZ', 0.7, ANTH)
        if n == 1:      # ouvrant à soufflet (basculant vers l'intérieur) : triangle pointe en bas
            D.ligne((u0, z1_), ((u0 + u1) / 2, z0_), 'A-GLAZ', 0.3, (1, 1, 1)); D.ligne((u1, z1_), ((u0 + u1) / 2, z0_), 'A-GLAZ', 0.3, (1, 1, 1))
        for i in range(n if n > 1 else 0):
            a = u0 + i * L / n
            D.ligne((a + 0.15 * L / n, z0_ + 0.25 * (z1_ - z0_)), (a + 0.45 * L / n, z0_ + 0.55 * (z1_ - z0_)), 'A-GLAZ', 0.4, (1, 1, 1))
        if grille:
            nb = int(L / 0.12)
            for i in range(1, nb):
                u = u0 + i * L / nb; D.ligne((u, z0_ + 0.03), (u, z1_ - 0.03), 'A-GLAZ', 0.35, (0.16, 0.17, 0.19))
            for zz in (z0_ + 0.10, z1_ - 0.10):
                D.ligne((u0, zz), (u1, zz), 'A-GLAZ', 0.45, (0.16, 0.17, 0.19))


BETON = (0.80, 0.80, 0.78)


def auvents_facade(D, fac, d):
    """Auvents béton (débord 0.60) : vus de face sur leur façade, de profil sur les façades d'angle."""
    for n in ('GF', 'FF'):
        for a in MAQ['niveaux'][n].get('auvents', []):
            x0, y0, x1, y1 = a['rect']
            if a['facade'] == fac:
                u0, u1 = {'S': (x0, x1), 'N': (W - x1, W - x0), 'E': (y0, y1), 'W': (H - y1, H - y0)}[fac]
                D.poly(rect(u0 + d, a['z0'], u1 + d, a['z1']), 'A-ELEV', 0.45, (0.25, 0.25, 0.25), fond=BETON)


REMPLACE = {'quiet facade, service door + vented gas cage, scullery and kitchen windows': 'quiet facade, service door, scullery and kitchen windows',
            'timber-clad master suite with louvred window, small high windows to the neighbour': 'timber-clad master suite, high windows to the neighbour',
            'SECTION A-A': 'SECTION S1-S1', 'SECTION B-B': 'SECTION S2-S2',
            'master-suite frame + balcony, roof terrace pergola, pavilion on the +0.60 base': 'master-suite frame + balcony, roof terrace pergola, pavilion deck +0.55',
            'veranda + steps, stone entrance wall, curtain wall over the stair, garden balcony frame': 'veranda + steps, stone entrance wall, stair windows, garden balcony frame'}


def textes_fond(D, F, exclure=()):
    for t in F.textes():
        t = dict(t, texte=REMPLACE.get(t['texte'], t['texte']))
        if t['texte'] in exclure or t['texte'].startswith(('Ech :',)) or t['texte'] in ('1',): continue
        if 'Elevation -' in t['texte'] or t['texte'].startswith('Section '): continue
        if t['texte'].startswith('FFL') or re.match(r'^\+\d+\.\d\d$', t['texte'].strip()): continue   # (5e passage) niveaux d'origine en double avec noms_niveaux
        z_ = t['z'] - (0.60 if t['z'] < -0.30 else 0.0)        # titres et sous-titres sous le sol hachuré (DOC-044)
        D.texte((t['u'], z_), t['texte'], t['taille'] / dp.PT_M_100, 'A-ANNO', t['gras'], False, coul=t['coul'])


def bornes(D, marge=0.6):
    xs, zs = [], []
    for pr in D.P:
        if pr[0] in ('l', 'p'):
            for x, z in pr[2]: xs.append(x); zs.append(z)
        elif pr[0] == 't':
            xs.append(pr[2][0]); zs.append(pr[2][1])
            xs.append(pr[2][0] + 0.55 * pr[4] * len(pr[3]) * (100 / 75))
    return (min(xs) - marge, min(zs) - marge, max(xs) + marge, max(zs) + marge)


AXES_Q = dp.quadrillage(dict(MAQ['niveaux'], RF=dp.niveau_toiture(MAQ)))


def couvertures(D, d, vue):
    """Couvertures polycarbonate des pergolas (maquette) : trait bleu pâle au-dessus des lames, en façade ou en coupe.
    vue : 'S', 'E' (façades) ou ('x', c) / ('y', c) pour une coupe."""
    P = [(MAQ['site']['pergola_pavillon'], 3.50), (MAQ['niveaux']['FF']['exterieurs']['pergola'], 6.90)]
    for pg, z in P:
        if not pg.get('couverture'): continue
        x0, y0, x1, y1 = pg['rect']
        if vue == 'S': u0, u1 = x0, x1
        elif vue == 'E': u0, u1 = y0, y1
        elif isinstance(vue, tuple) and vue[0] == 'x' and x0 <= vue[1] <= x1: u0, u1 = y0, y1
        elif isinstance(vue, tuple) and vue[0] == 'y' and y0 <= vue[1] <= y1: u0, u1 = x0, x1
        else: continue
        D.poly(rect(u0 + d, z, u1 + d, z + 0.04), 'A-GLAZ', 0.3, (0.25, 0.35, 0.45), fond=(0.80, 0.88, 0.94))


def habillage(D, F, sens_u, axes_cle, u_de, d, personnes=()):
    """Charte croquis des élévations et coupes : axes du quadrillage en tête (mêmes noms que les plans), noms des
    niveaux en grand du côté des repères de niveau, silhouettes à l'échelle."""
    dp.axes_elevation(D, AXES_Q[axes_cle], u_de, d, 11.7, 0.0)
    t4 = next((t for t in F.textes() if t['texte'].startswith('+4.00')), None)
    if t4:
        bb = [p['bb'] for p in F.prims]; umin = min(b[0] for b in bb); umax = max(b[2] for b in bb)
        u = (t4['u'] - 0.75) if t4['u'] < (umin + umax) / 2 else (t4['u'] + 2.6)     # juste à côté des repères de niveau
        dp.noms_niveaux(D, u, [('GF', 0.60, 4.00, 'FFL +0.60'), ('FF', 4.00, 7.40, 'FFL +4.00'), ('ROOF', 7.40, 8.40, '+7.40')])
    for u_, z_, s_ in personnes: dp.silhouette(D, u_, z_, sens=s_)


def sortir(D, numero, titre, vue, sous_titre, notes, echelle=75, symboles=None):
    carto = dict(CARTO, vue=vue, planche=numero, sous_titre=sous_titre, echelle='1:%d' % echelle)
    legende = {'titre_vue': titre, 'sous_titre_vue': f'Scale 1:%d   -   Revision {REV}' % echelle, 'numero_vue': '1', 'nord': False,
               'x': 60, 'y0': 112, 'colonnes': 215,
               'blocs': [{'titre': 'REVISIONS', 'lignes': REVISIONS}],
               'symboles': symboles or []}
    noter(numero, titre, [{'titre': 'NOTES', 'lignes': [(n, '') for n in notes]}])      # rapport séparé (indice D)
    nom = os.path.join(HERE, f'%s_{REV}_%s' % (numero.replace(' ', ''), titre.split(' - ')[-1].replace(' ', '_').replace('/', '-')))
    dp.rendre_pdf(D, nom + '.pdf', {'pt': (25, 125, 940, 800), 'm': bornes(D)}, carto, legende, echelle=echelle)
    dp.rendre_dxf(D, nom + '.dxf')
    return nom


# ----------------------------------------------------------------------------------------------- façades
FACADES = {'S': (22, 'SD - 007', 'South Elevation - Street'), 'E': (23, 'SD - 008', 'East Elevation - Garden - Main Entrance'),
           'N': (24, 'SD - 009', 'North Elevation - Rear Neighbour'), 'W': (25, 'SD - 010', 'West Elevation - Side Neighbour')}
GRILLES = {g['ouverture'] for g in MAQ['niveaux']['GF'].get('grilles', []) if not g['ouverture'].startswith('SD')}   # baies : grilles repliables escamotées


def arbres_facade(D, fac, d, proches):
    """Arbres de la maquette en façade (FAC-018), dans l'ordre de profondeur (DOC-043) : proches=False -> arbres au-delà ou
    sur les côtés (dessinés avant le bâtiment) ; True -> arbres devant. Jamais devant une façade (lisibilité) ni au-delà de
    3.50 des pignons (cadre de la planche, DOC-042)."""
    Lf = W if fac in 'NS' else H
    for a in MAQ['site'].get('arbres', []):
        cx, cy = a['centre']; r = a['diametre'] / 2
        u = {'S': cx, 'N': W - cx, 'E': cy, 'W': H - cy}[fac] + d
        prof = {'S': cy, 'N': -cy, 'E': -cx, 'W': cx}[fac]               # plus grand = plus loin de l'observateur
        devant = prof < {'S': 0, 'N': -H, 'E': -W, 'W': 0}[fac]
        if devant != proches: continue
        if d - r < u < d + Lf + r: continue                               # devant ou derrière la façade : non dessiné
        if u - r < d - 3.5 or u + r > d + Lf + 3.5: continue              # hors du cadre de la planche
        D.poly(rect(u - 0.08, 0.0, u + 0.08, 2.0), 'A-PLANT', 0.3, (0.35, 0.45, 0.30), fond=(0.55, 0.45, 0.35))
        D.cercle((u, 2.0 + r), r, 'A-PLANT', 0.4, (0.35, 0.55, 0.30), fond=(0.80, 0.88, 0.74))


def facade(fac):
    page, numero, titre = FACADES[fac]
    F = vr.Fond(PDF, page, 75)
    O = ouvertures_facade(fac)
    vit, _ = pf.vitrages(PDF, page)
    OO = ouvertures_origine(fac)
    d, m = pf.recaler(vit, [{'id': o['id'], 'a0': o['a0'], 'a1': o['a1']} for o in OO])
    # retrait : vitrages d'origine + portes d'origine + emplacements des nouvelles ouvertures
    zones = [(v['x0'] - 0.07, v['z0'] - 0.07, v['x1'] + 0.07, v['z1'] + 0.07) for v in vit]
    zones += [(o['a0'] + d - 0.07, (0.5 if o['niveau'] == 'GF' else 3.9), o['a1'] + d + 0.07, (3.2 if o['niveau'] == 'GF' else 6.8)) for o in OO if 'porte' in o['type']]
    zones += [(o['a0'] + d - 0.07, o['z_bas'] - 0.07, o['a1'] + d + 0.07, o['z_haut'] + 0.07) for o in O]
    notes = []
    if fac == 'N':   # ancienne cage de gaz (devant W08) retirée
        cx0, cx1 = W - 6.68 + d, W - 5.58 + d
        zones.append((cx0 - 0.05, -0.05, cx1 + 0.05, 2.2))
    if fac == 'W':   # ancienne cage de gaz (nord, y 14.30-14.90) vue de profil
        zones.append((H - 14.95 + d, -0.05, H - 14.25 + d, 2.2))
    if fac == 'E':   # ancienne cage de gaz vue de profil (au-delà de l'angle nord)
        zones.append((14.25 + d, -0.05, 14.95 + d, 2.2))
    if fac == 'N':   # indice C : fenêtres à allège 0.80 -> garde-corps vitrés de l'étage inutiles ; auvent bois remplacé par les auvents béton
        def vestige(p):
            f = p['fill']; b = p['bb']
            if not f or len(f) != 3: return False
            f2 = tuple(round(x, 2) for x in f)
            if f2 == (0.66, 0.75, 0.8) and 3.9 < b[1] and b[3] < 5.3 and (b[2] - b[0]) > 1.0: return True
            if f2 in ((0.69, 0.49, 0.32), (0.6, 0.42, 0.26)) and b[3] < 3.6 and (b[2] - b[0]) > 2.0: return True
            return False
        n_v = F.retirer(filtre=vestige)
        notes.append('Former glass guardrails (first floor) and timber canopy removed:')
        notes.append('   windows now have 0.80 sills and RC canopies.')
    # vestiges de l'ancien projet (relecture indice C) : lames bois devant les baies, garde-corps et lames sans balcon,
    # panneau bois au-dessus de l'ancienne porte d'entrée, objet sous W06, poteau de pergola côté chambre
    BOIS_F = ((0.69, 0.49, 0.32), (0.6, 0.42, 0.26)); VERRE_GC = (0.66, 0.75, 0.8); ANTH_F = (0.23, 0.24, 0.26)
    baies = [(o['a0'] + d, o['z_bas'], o['a1'] + d, o['z_haut']) for o in O if o['type'] == 'baie_coulissante']
    def vestige2(p):
        f = p['fill']; b = p['bb']; c = p['color']
        f2 = tuple(round(x, 2) for x in f) if f and len(f) == 3 else None
        c2 = tuple(round(x, 2) for x in c) if c and len(c) == 3 else None
        bois = f2 in BOIS_F or (p['type'] == 's' and c2 == (0.49, 0.33, 0.2))
        etroit_vertical = (b[2] - b[0]) < 0.15 and (b[3] - b[1]) > 0.6
        if bois and etroit_vertical and any(b[0] < z[2] and b[2] > z[0] and b[1] < z[3] and b[3] > z[1] for z in baies): return True
        if bois and etroit_vertical and b[1] > 3.9: return True                 # lames verticales décoratives absentes de la maquette
        if fac == 'W' and b[1] > 3.9 and (f2 == VERRE_GC or (bois and (b[3] - b[1]) < 0.15 and (b[2] - b[0]) > 1.5)): return True   # garde-corps sans balcon, poutre de l'ancien brise-soleil
        if fac == 'N' and f2 == (0.85, 0.84, 0.81) and b[3] < 0.45 and abs(b[0] - (7.62 + d)) < 0.1: return True   # anciennes marches sous D10
        if fac == 'N' and b[1] > 3.9 and (bois or f2 == VERRE_GC): return True
        if fac == 'W' and b[1] > 3.9 and b[2] < d + 4.5 and (bois or f2 == VERRE_GC): return True
        if fac == 'E':
            for o in O:
                if o.get('repere') == 'D03' and bois and b[0] < o['a1'] + d + 0.1 and b[2] > o['a0'] + d - 0.1 and b[1] < 3.40 and b[3] > 0.60: return True   # ancienne porte bois 2.70 + panneau
                if o.get('repere') == 'W06' and f2 and (max(f2) < 0.45 or (max(f2) - min(f2) < 0.06 and max(f2) < 0.85)) and (b[2] - b[0]) < 0.5 and b[1] > -0.30 and b[3] <= o['z_bas'] + 0.15 \
                        and o['a0'] + d - 0.7 < b[0] and b[2] < o['a1'] + d + 0.7: return True
        if fac == 'S' and f2 == ANTH_F and abs(b[0] - (7.13 + d)) < 0.05 and (b[2] - b[0]) < 0.3 and b[1] > 3.9: return True
        # (2e passage) cadres fins d'anciennes ouvertures (contour sans remplissage autour d'une ouverture de la maquette)
        if not f2 and p['type'] == 's' and 1.0 < (b[2] - b[0]) < 3.5 and 1.0 < (b[3] - b[1]) < 3.0 and any(
                b[0] - 0.05 <= o['a0'] + d and o['a1'] + d <= b[2] + 0.05 and b[1] - 0.05 <= o['z_bas'] and o['z_haut'] <= b[3] + 0.05 for o in O):
            return True
        # (2e passage) haies basses sans jardinière dans la maquette (façades nord et ouest) : végétation = maquette seulement
        vert = f2 and f2[1] > f2[0] + 0.08 and f2[1] > f2[2] + 0.05
        Lf = W if fac in 'NS' else H
        if fac in 'NW' and vert and b[3] < 2.2 and b[0] >= d - 0.3 and b[2] <= d + Lf + 0.3: return True
        # (5e passage) haie d'origine le long de la véranda (jardinière remplacée par la voie piétonne en V4)
        if fac == 'E' and vert and b[3] < 2.2 and b[0] >= d - 3.80 and b[2] <= d + 6.5: return True   # jardinière sud du pavillon (y < -3.75) gardée
        if fac == 'S' and vert and b[3] < 2.2 and b[0] >= d + 14.25: return True
        if fac == 'S' and not f2 and (b[2] - b[0]) < 0.10 and b[0] > d + 14.3 and (b[3] - b[1]) > 3.0 and b[1] < 0.3: return True   # trait isolé d'origine (x 16.5)
        if vert and b[3] >= 2.2: return True                     # (3e passage) arbres d'origine : redessinés depuis site.arbres
        if f2 and len(set(f2)) == 1 and 0.6 < f2[0] < 0.85 and 0.25 < (b[2] - b[0]) < 0.60 and 1.2 < (b[3] - b[1]) < 1.95 and b[1] < 0.75:
            return True                                           # (4e passage) silhouette humaine d'origine (corps gris sans tête)
        return False
    n_ret0 = F.retirer(filtre=vestige2)
    if fac == 'S':      # poutres de la pergola prolongées jusqu'au mur de la chambre (x 6.43)
        for p in F.prims:
            b = p['bb']
            if p['fill'] and tuple(round(x, 2) for x in p['fill']) == ANTH_F and abs(b[0] - (7.13 + d)) < 0.05 and (b[2] - b[0]) > 3 and b[1] > 6.0:
                p['pts'] = [((6.43 + d) if x < 7.4 + d else x, z) for x, z in p['pts']]; p['bb'] = (6.43 + d, b[1], b[2], b[3])
    n_ret = F.retirer(zones, garder=lambda p: vr.premier_plan(p) and not any(
        p['bb'][0] >= z[0] and p['bb'][2] <= z[2] and p['bb'][3] <= 2.25 and z[1] < 0 for z in zones))
    F.retirer(filtre=lambda p: p['bb'][3] <= 0.03 and p['bb'][1] < -0.10 and (p['bb'][2] - p['bb'][0]) > 5.0)   # bande de sol d'origine
    D = dp.Dessin()
    bb_ = [p['bb'] for p in F.prims]
    dp.terrain_coupe(D, min(b[0] for b in bb_) - 0.5, max(b[2] for b in bb_) + 0.5, 0.0, 0.75)
    arbres_facade(D, fac, d, proches=False)             # arbres au-delà / sur les côtés : avant le bâtiment
    F.vers_dessin(D, sauf=vr.premier_plan)
    for o in O:
        dessiner_ouverture(D, o, o['a0'] + d, o['a1'] + d, o['z_bas'], o['z_haut'], grille=o.get('repere') in GRILLES)
    auvents_facade(D, fac, d)
    T_ = MAQ['site']['toiture']
    for c in T_['citernes']:       # citernes : partie visible au-dessus de l'acrotère (+8.40)
        cx, cy = c['centre']; r = c['rayon']
        u0, u1 = {'S': (cx - r, cx + r), 'N': (W - cx - r, W - cx + r), 'E': (cy - r, cy + r), 'W': (H - cy - r, H - cy + r)}[fac]
        D.poly(rect(u0 + d, 8.40, u1 + d, 7.40 + c['hauteur']), 'A-ELEV', 0.4, (0.35, 0.35, 0.35), fond=(0.93, 0.93, 0.92))
    if fac == 'N':
        for m in MAQ['site']['marches']:
            if not m['nom'].startswith('service'): continue
            r = m['rect']; u0, u1 = W - r[2], W - r[0]
            if m['montee'] == 'palier': D.poly(rect(u0 + d, 0.0, u1 + d, m['z']), 'A-ELEV', 0.4, (0.3, 0.3, 0.3), fond=(0.85, 0.84, 0.81))
            else:
                n = m['n']
                g_ = n - 1; hh = m.get('hauteur', 0.15)
                for k in range(g_):    # n - 1 girons ; la marche haute est toujours contre le palier (SIT-013)
                    hk = hh * (k + 1) if m['montee'] == 'ouest' else hh * (g_ - k)
                    D.poly(rect(u0 + d + k * (u1 - u0) / g_, 0.0, u0 + d + (k + 1) * (u1 - u0) / g_, hk), 'A-ELEV', 0.4, (0.3, 0.3, 0.3), fond=(0.85, 0.84, 0.81))
        for q in MAQ['niveaux']['GF']['equipements']:
            if q['nom'].startswith('VENT GRILLE'):
                r = q['rect']; D.poly(rect(W - r[2] + d, 2.45, W - r[0] + d, 2.65), 'A-ELEV', 0.4, (0.2, 0.2, 0.2), fond=(0.6, 0.6, 0.6))
        # (indice D) grilles de ventilation de l'arrière-cuisine retirées jusqu'à l'étape 3 (retour client)
        pe = T_['porte_edicule']; r = pe['rect']                 # porte de l'édicule D20 (avec relevé)
        D.texte(((W - r[2] + W - r[0]) / 2 + d, pe['z'][1] + 0.25), pe['repere'], 0.20, 'A-TAGS', False, True, coul=(0.1, 0.25, 0.55))
    if fac == 'S':      # D13 (palier -> terrasse) vue au fond de la terrasse ; poteaux intermédiaires de la pergola
        o13 = next(o for o in MAQ['niveaux']['FF']['ouvertures'] if o['id'] == 'FF-D03')
        D.poly(rect(o13['rect'][0] + d, o13['z_bas'], o13['rect'][2] + d, o13['z_haut']), 'A-DOOR', 0.6, ANTH, fond=VERRE)
        D.poly(rect(o13['rect'][0] + d + 0.08, o13['z_bas'] + 0.08, o13['rect'][2] + d - 0.08, o13['z_haut'] - 0.08), 'A-DOOR', 0.3, ANTH)
        D.texte(((o13['rect'][0] + o13['rect'][2]) / 2 + d, o13['z_haut'] + 0.15), 'D13', 0.20, 'A-TAGS', False, True, coul=(0.1, 0.25, 0.55))
        for r in MAQ['niveaux']['FF']['poteaux']:
            if abs(r[0] - 9.23) < 0.01 and r[1] < 1:
                D.poly(rect(r[0] + d, 4.0, r[2] + d, 6.8), 'A-ELEV', 0.4, (0.1, 0.1, 0.1), fond=ANTH)
    for g in MAQ['site'].get('garde_corps_deck', []) if fac in 'WN' else []:   # (6e passage, FAC-024) vu au-delà, avant la végétation
        (x0, y0), (x1, y1) = g['pts']; z0, z1 = g['z'], g['z'] + g['h']
        if fac == 'W':                               # visible hors de l'emprise de la maison (y < 0), à travers la pergola
            u0, u1 = H - max(y0, y1) + d, H - min(y0, y1) + d; u0 = max(u0, H + d)
            D.ligne((u0, z1), (u1, z1), 'A-ELEV', 0.5, ANTH)
            k = 0
            while u0 + k * 0.12 <= u1 + 1e-6:
                D.ligne((u0 + k * 0.12, z0), (u0 + k * 0.12, z1), 'A-ELEV', 0.2, ANTH); k += 1
        else:                                        # nord : vu de bout
            u = W - x0 + d
            D.poly(rect(u - 0.03, z0, u + 0.03, z1), 'A-ELEV', 0.4, ANTH, fond=ANTH)
    F.vers_dessin(D, seulement=vr.premier_plan)          # garde-corps, lames bois, plantes devant les menuiseries
    for g in MAQ['site'].get('garde_corps_deck', []):    # (5e passage, FAC-024) garde-corps acier du bord de la véranda
        (x0, y0), (x1, y1) = g['pts']; z0, z1 = g['z'], g['z'] + g['h']
        if fac == 'E':
            u0, u1 = min(y0, y1) + d, max(y0, y1) + d
            D.ligne((u0, z1), (u1, z1), 'A-ELEV', 0.6, ANTH); D.ligne((u0, z0 + 0.10), (u1, z0 + 0.10), 'A-ELEV', 0.4, ANTH)
            k = 0
            while u0 + k * 0.12 <= u1 + 1e-6:
                D.ligne((u0 + k * 0.12, z0), (u0 + k * 0.12, z1), 'A-ELEV', 0.25, ANTH); k += 1
        elif fac == 'S':
            u = x0 + d
            D.poly(rect(u - 0.03, z0, u + 0.03, z1), 'A-ELEV', 0.4, ANTH, fond=ANTH)
    arbres_facade(D, fac, d, proches=True)              # arbres devant (côté observateur), dessinés en dernier
    if fac == 'W' and MAQ['site'].get('etendoir'):      # étendoir (bande ouest) : 2 poteaux + fils
        r = MAQ['site']['etendoir']['rect']
        for yy in (r[1], r[3]): D.poly(rect(H - yy + d - 0.03, 0.0, H - yy + d + 0.03, 1.80), 'A-ELEV', 0.3, (0.3, 0.3, 0.3), fond=(0.8, 0.8, 0.8))
        D.ligne((H - r[3] + d, 1.75), (H - r[1] + d, 1.75), 'A-ELEV', 0.3, (0.3, 0.3, 0.3))
    gg = MAQ['site']['toiture'].get('gargouille')
    if gg and fac == 'W':
        u = H - gg['pos'][1] + d; D.poly(rect(u - 0.06, 10.03, u + 0.06, 10.13), 'A-PLUMB', 0.4, (0.1, 0.3, 0.6), fond=(0.6, 0.7, 0.8))
        D.texte((u, 10.45), 'spout', 0.15, 'A-ANNO', coul=(0.1, 0.3, 0.6))
    for o in O:                                           # repères des ouvertures (comme sur les plans)
        porte = (o['niveau'] == 'GF' and o['z_haut'] < 3.0) or o['z_bas'] - MAQ['niveaux'][o['niveau']]['z'] < 0.30   # RDC et portes : repère au-dessus
        pos = ((o['a0'] + o['a1']) / 2 + d, o['z_haut'] + (0.35 if o['niveau'] == 'GF' and fac != 'S' else 0.25) if porte else o['z_bas'] - 0.25)
        if o.get('repere') == 'D03': pos = (o['a1'] + d + 0.35, (o['z_bas'] + o['z_haut']) / 2)     # imposte au-dessus : repère à côté
        D.texte(pos, o['repere'], 0.20, 'A-TAGS', False, True, coul=(0.1, 0.25, 0.55))
    niv = [t for t in F.textes() if t['texte'].startswith('+8.40')]
    tri = [p for p in F.prims if len(p['pts']) in (3, 4) and p['fill'] and abs(sum(p['fill']) / 3 - 0.33) < 0.03
           and abs((p['bb'][1] + p['bb'][3]) / 2 - 8.40) < 0.25 and (p['bb'][2] - p['bb'][0]) < 0.5]
    if niv and tri:
        t0 = niv[0]; tr = tri[0]; dz = 10.25 - 8.40
        D.poly([(x, z + dz) for x, z in tr['pts']], 'A-ANNO', 0, (0.33, 0.33, 0.33), fond=(0.33, 0.33, 0.33))
        u_txt = t0['u'] - 0.75 if tr['bb'][0] > t0['u'] else t0['u']       # étiquette à gauche ou à droite du triangle
        D.texte((u_txt, t0['z'] + dz), '+10.25 penthouse roof', t0['taille'] / dp.PT_M_100, 'A-ANNO', False, False, coul=t0['coul'])
    if fac == 'S':
        notes.append('Boundary wall and sliding gate: see SD-013.')
    if fac in 'SE': couvertures(D, d, fac)
    d03 = next((o for o in O if o.get('repere') == 'D03'), None)
    pers = {'S': [(10.9 + d, MAQ['site']['deck']['z'], 1)], 'E': [((d03['a0'] - 0.9 + d) if d03 else 3.0, MAQ['site']['deck']['z'], -1)]}.get(fac, [])
    habillage(D, F, 1, 'x' if fac in 'NS' else 'y', {'S': lambda p: p, 'N': lambda p: W - p, 'E': lambda p: p, 'W': lambda p: H - p}[fac], d, pers)
    textes_fond(D, F)
    notes += ['First-floor windows (sill 0.80): fixed laminated lower pane to 1.00.',
              'Openings, grilles and doors redrawn from the model',
              '   (SABTP standards: doors and sliding doors h 2.20,',
              '   windows max 2.00 wide, 2 sliding panels).',
              'RC canopies 0.60 (grey) over unprotected windows.',
              'Pergolas: timber slats + compact polycarbonate 0.006',
              '   (to be confirmed on site; UV, opal) above the slats, 3 % fall.',
              'Ground-floor windows: security grilles (inside).', 'All levels and dimensions in metres.']
    sym = [({'ep': 0.6, 'coul': ANTH}, 'aluminium sliding window, anthracite frame'),
           ({'ep': 0.35, 'coul': (0.16, 0.17, 0.19)}, 'security grille (ground-floor windows, inside)'),
           ({'ep': 0.35, 'coul': (1, 1, 1)}, 'folding grilles (sliding doors): not shown')]
    return sortir(D, numero, titre, 'Elevation', titre.split(' - ', 1)[0], notes, symboles=sym), len(m), len(O), n_ret


# ----------------------------------------------------------------------------------------------- coupes
COUPES = {'A': (26, 'SD - 011', 'Section S1-S1', 'x', 10.43), 'B': (27, 'SD - 012', 'Section S2-S2', 'y', 7.65)}


def murs_coupes(axe, c):
    out = []
    for n in ('GF', 'FF'):
        for w in MAQ['niveaux'][n]['murs']:
            x0, y0, x1, y1 = w['rect']
            if axe == 'x' and x0 <= c <= x1: out.append((y0, y1))
            if axe == 'y' and y0 <= c <= y1: out.append((x0, x1))
    return sorted(set((round(a, 3), round(b, 3)) for a, b in out))


MUR_COUPE = (0.15, 0.15, 0.15)
NIV_HAUT = {'GF': 4.00, 'FF': 7.40}


def escaliers_coupe(D, axe, c, d):
    """Escaliers de la maquette en coupe : marches coupées (poché) et volées vues au-delà (contour), garde-corps."""
    for n in ('GF', 'FF'):
        M = MAQ['niveaux'][n]
        for e in M.get('escaliers', []):
            if e['type'] == 'palier':
                r = e['rect']; u0, u1 = (r[1], r[3]) if axe == 'x' else (r[0], r[2])
                coupe_ = (r[0] <= c <= r[2]) if axe == 'x' else (r[1] <= c <= r[3])
                au_dela = (r[2] < c) if axe == 'x' else (r[1] > c)
                if coupe_: D.poly(rect(u0 + d, e['z'] - 0.20, u1 + d, e['z']), 'A-WALL', 0.3, (0, 0, 0), fond=MUR_COUPE)
                elif au_dela: D.poly(rect(u0 + d, e['z'] - 0.20, u1 + d, e['z']), 'A-STAIR', 0.3, (0.3, 0.3, 0.3), fond=(0.86, 0.86, 0.84))
                continue
            L = e['n'] * e['giron']; a, b = e['larg']
            for k in range(e['n']):
                zt = e['z0'] + (k + 1) * e['hauteur']
                if e['sens'] in 'NS':
                    s0 = e['depart'] + (k if e['sens'] == 'N' else -(k + 1)) * e['giron']; s1 = s0 + e['giron']
                    box_ = (a, s0, b, s1)
                else:
                    s0 = e['depart'] + (k if e['sens'] == 'E' else -(k + 1)) * e['giron']; s1 = s0 + e['giron']
                    box_ = (s0, a, s1, b)
                coupe_ = (box_[0] <= c <= box_[2]) if axe == 'x' else (box_[1] <= c <= box_[3])
                au_dela = (box_[2] <= c) if axe == 'x' else (box_[1] >= c)
                u0, u1 = (box_[1], box_[3]) if axe == 'x' else (box_[0], box_[2])
                if coupe_: D.poly(rect(u0 + d, zt - 0.17, u1 + d, zt), 'A-WALL', 0.3, (0, 0, 0), fond=MUR_COUPE)
                elif au_dela: D.poly(rect(u0 + d, zt - 0.17, u1 + d, zt), 'A-STAIR', 0.25, (0.35, 0.35, 0.35), fond=(0.88, 0.88, 0.86))
        for gp in M.get('garde_corps_paliers', []):            # garde-corps de palier vus au-delà
            (ax_, ay_), (bx_, by_) = gp['pts']
            if (axe == 'x' and abs(ax_ - bx_) < 1e-6 and ax_ < c) or (axe == 'y' and abs(ay_ - by_) < 1e-6 and ay_ > c):
                u0, u1 = sorted((ay_, by_)) if axe == 'x' else sorted((ax_, bx_))
                D.ligne((u0 + d, gp['z'] + 1.0), (u1 + d, gp['z'] + 1.0), 'A-GLAZ', 0.6, ANTH)
        for gc in M.get('garde_corps_escalier', []):
            vol = next(e for e in M['escaliers'] if e.get('nom') == gc['volee'])
            (ax_, ay_), (bx_, by_) = gc['pts']
            visible = (min(ax_, bx_) <= c) if axe == 'x' else (max(ay_, by_) >= c)
            if not visible: continue
            z0_ = vol['z0']; z1_ = vol['z0'] + vol['n'] * vol['hauteur']
            if axe == 'x': u0, u1 = sorted((ay_, by_))
            else: u0, u1 = sorted((ax_, bx_))
            if u1 - u0 < 0.05: continue
            sens_monte = 1 if vol['sens'] in ('N', 'E') else -1
            pa, pb = (u0, z0_ + 1.0), (u1, z1_ + 1.0)
            if sens_monte < 0: pa, pb = (u0, z1_ + 1.0), (u1, z0_ + 1.0)
            D.ligne((pa[0] + d, pa[1]), (pb[0] + d, pb[1]), 'A-GLAZ', 0.6, ANTH)


def murs_coupes_maquette(D, axe, c, d):
    """Murs coupés par le plan de coupe (maquette) avec leurs ouvertures (vitrage ou passage) et les auvents en profil."""
    for n in ('GF', 'FF'):
        M = MAQ['niveaux'][n]; z0, z1 = M['z'], NIV_HAUT[n]
        for w in M['murs']:
            x0, y0, x1, y1 = w['rect']
            if not ((axe == 'x' and x0 - 1e-6 <= c <= x1 + 1e-6) or (axe == 'y' and y0 - 1e-6 <= c <= y1 + 1e-6)): continue
            u0, u1 = (y0, y1) if axe == 'x' else (x0, x1)
            D.poly(rect(u0 + d, z0, u1 + d, z1), 'A-WALL', 0.3, (0, 0, 0), fond=MUR_COUPE)
        for o in M['ouvertures']:
            x0, y0, x1, y1 = o['rect']
            if not ((axe == 'x' and x0 <= c <= x1 and o['axe'] == 'x') or (axe == 'y' and y0 <= c <= y1 and o['axe'] == 'y')): continue
            u0, u1 = (y0, y1) if axe == 'x' else (x0, x1)
            D.poly(rect(u0 + d, z0, u1 + d, z1), 'A-WALL', 0.3, (0, 0, 0), fond=MUR_COUPE)     # allège + linteau
            for za, zb in (o.get('empilement') or [[o['z_bas'], o['z_haut']]]):
                D.poly(rect(u0 + d, za, u1 + d, zb), 'A-GLAZ', 0.0, (1, 1, 1), fond=(1, 1, 1))
                if o['type'] in ('fenetre', 'baie_coulissante'):
                    m_ = (u0 + u1) / 2 + d
                    D.poly(rect(m_ - 0.025, za, m_ + 0.025, zb), 'A-GLAZ', 0.3, (0.23, 0.24, 0.26), fond=(0.66, 0.75, 0.80))
                D.ligne((u0 + d, zb), (u1 + d, zb), 'A-GLAZ', 0.3, (0, 0, 0)); D.ligne((u0 + d, za), (u1 + d, za), 'A-GLAZ', 0.3, (0, 0, 0))
        for a in M.get('auvents', []):
            x0, y0, x1, y1 = a['rect']
            if (axe == 'x' and x0 <= c <= x1 and a['facade'] in 'NS') or (axe == 'y' and y0 <= c <= y1 and a['facade'] in 'EW'):
                u0, u1 = (y0, y1) if axe == 'x' else (x0, x1)
                D.poly(rect(u0 + d, a['z0'], u1 + d, a['z1']), 'A-WALL', 0.3, (0, 0, 0), fond=MUR_COUPE)


def mobilier_coupe(D, axe, c, d):
    """Mobilier vu en coupe : pièces traversées par le plan de coupe, objets coupés ou au-delà (sens du regard)."""
    n_obj = 0
    for n in ('GF', 'FF'):
        M = MAQ['niveaux'][n]; z = M['z']
        ligne = LineString([(c, -20), (c, 40)]) if axe == 'x' else LineString([(-20, c), (40, c)])
        pieces = [Polygon(p['contour']) for p in M['pieces'] if p.get('nom') and Polygon(p['contour']).intersects(ligne)]
        items = []
        for m in M['mobilier']:
            x0, y0, x1, y1 = m['rect']; g = box(*m['rect'])
            ext_ok = m.get('exterieur') and ((axe == 'x' and x0 <= c + 6) or (axe == 'y' and y1 >= c - 6))
            if not ext_ok and not any(p.buffer(0.05).contains(g.centroid) for p in pieces): continue
            if axe == 'x' and x0 > c: continue           # regard vers l'ouest : x < c
            if axe == 'y' and y1 < c: continue           # regard vers le nord : y > c
            if m['nom'] in ('OBJECT',) or m['nom'].startswith(('UP',)): continue
            items.append(m)
        items.sort(key=(lambda m: m['rect'][0]) if axe == 'x' else (lambda m: -m['rect'][3]))
        for m in items:
            x0, y0, x1, y1 = m['rect']
            u0, u1 = ((y0, y1) if axe == 'x' else (x0, x1))
            h = vr.hauteur(m['nom']); zm = z - 0.05 if m.get('exterieur') else z
            D.poly(rect(u0 + d, zm, u1 + d, zm + h), 'A-FURN', 0.4, (0.6, 0.6, 0.58), fond=MEUBLE)
            n_obj += 1
    return n_obj


def gardes_coupes(axe, c):
    """Garde-corps (vide, paliers, volées) traversés par le plan de coupe : (u, z du support)."""
    out = []
    def croise(a, b):
        i = 0 if axe == 'x' else 1
        if min(a[i], b[i]) < c < max(a[i], b[i]) and abs(a[1 - i] - b[1 - i]) < 1e-6: return a[1 - i]
    F_ = MAQ['niveaux']['FF']
    for i_, pl in enumerate(F_['exterieurs']['garde_corps_vitres']):     # vide (+4.00), terrasse et balcons (+3.95)
        for a, b in zip(pl, pl[1:]):
            u = croise(a, b)
            if u is not None: out.append((u, 4.00 if i_ == 3 else 3.95))
    for n in ('GF', 'FF'):
        M = MAQ['niveaux'][n]
        for gp in M.get('garde_corps_paliers', []):
            u = croise(*gp['pts'])
            if u is not None: out.append((u, gp['z']))
        for gc in M.get('garde_corps_escalier', []):
            u = croise(*gc['pts'])
            if u is None: continue
            e = next(e for e in M['escaliers'] if e.get('nom') == gc['volee'])
            k = int(abs(c - e['depart']) / e['giron'])
            out.append((u, e['z0'] + min(k + 1, e['n']) * e['hauteur']))
    return out


def dalles_coupe(D, axe, c, d, u0, u1):
    """Planchers coupés dans la zone de la cage (u0-u1) depuis la maquette : dalle de l'étage moins ses trémies,
    dalle de toiture moins la terrasse de l'étage et l'intérieur de l'édicule (règle MOD-012)."""
    ligne = LineString([(c, u0), (c, u1)]) if axe == 'x' else LineString([(u0, c), (u1, c)])
    bat = box(0, 0, W, H)
    ff = bat
    for t in MAQ['niveaux']['FF'].get('tremies', []): ff = ff.difference(box(*t['rect']))
    terr = next(s_['rect'] for s_ in MAQ['niveaux']['FF']['exterieurs']['sols'] if s_['nom'].startswith('ROOF TERRACE'))
    toit = bat.difference(box(*terr)).difference(box(*MAQ['site']['toiture']['tremie']))
    for g, za, zb in ((ff, 3.80, 4.00), (toit, 7.20, 7.40)):
        x = g.intersection(ligne)
        for seg in (getattr(x, 'geoms', None) or ([x] if not x.is_empty else [])):
            if seg.length < 0.02: continue
            cs = list(seg.coords); us = [q[1] if axe == 'x' else q[0] for q in cs]
            D.poly(rect(min(us) + d, za, max(us) + d, zb), 'A-WALL', 0.3, (0, 0, 0), fond=MUR_COUPE)


def coupe(nom):
    page, numero, titre, axe, c = COUPES[nom]
    F = vr.Fond(PDF, page, 75)
    mu = murs_coupes(axe, c)
    d, n_ok, n_m = vr.recaler_murs_coupes(F, mu)
    # mobilier d'origine et cage de gaz retirés (redessinés depuis la maquette)
    retire = lambda p: (p['fill'] and tuple(round(x, 2) for x in p['fill']) in ((0.91, 0.91, 0.89), (0.94, 0.9, 0.77))) or \
        (p['color'] and tuple(round(x, 2) for x in p['color']) == (0.54, 0.48, 0.29))
    u_bat = [m for m in mu]; ub0 = min(a for a, b in u_bat) + d; ub1 = max(b for a, b in u_bat) + d
    # sous le dallage : hérisson redessiné (retrait des éléments parasites entre le sol et la dalle)
    n_ret = F.retirer(zones=[(ub0 + 0.16, -0.01, ub1 - 0.16, 0.46)], filtre=retire,
                      garder=lambda p: p['fill'] and max(p['fill']) < 0.2)
    # indice C : murs coupés et vitrages du bâtiment retirés du fond, puis redessinés depuis la maquette
    Lb = W if axe == 'y' else H
    def mur_ou_vitre(p):
        b = p['bb']; f = p['fill']
        dedans = b[0] >= d - 0.25 and b[2] <= Lb + d + 0.25 and b[1] >= 0.50 and b[3] <= 10.30
        if not dedans or p['type'] not in ('f', 'fs') or not f: return False
        sombre = max(f) < 0.2 and (b[3] - b[1]) > 0.5 and (b[2] - b[0]) < 0.40 and b[3] <= 7.45
        verre = len(f) == 3 and f[2] > f[0] + 0.08 and min(f) > 0.3 and max(f) < 0.85     # y compris l'ancien vitrage de l'édicule
        return sombre or verre
    # escaliers d'origine retirés de la zone de la cage, redessinés depuis la maquette (définition unique)
    z_esc = (8.30 + d, 0.62, 13.0 + d, 7.38) if axe == 'y' else (5.70 + d, 0.62, 9.65 + d, 7.38)
    n_ret += F.retirer(filtre=lambda p: p['bb'][0] >= z_esc[0] and p['bb'][2] <= z_esc[2] and p['bb'][1] >= z_esc[1] and p['bb'][3] <= z_esc[3]
                       and not (p['fill'] and max(p['fill']) < 0.2 and (p['bb'][2] - p['bb'][0]) > 1.0))
    if axe == 'x':      # ancienne SD04 (imposte au-dessus de 2.20) : tout le dessin d'origine retiré dans son emprise
        n_ret += F.retirer(zones=[(1.80 + d, 3.95, 3.90 + d, 6.75)])
    n_ret += F.retirer(filtre=mur_ou_vitre)
    # planchers d'origine retirés au droit de la cage d'escalier / édicule, redessinés depuis la maquette (trémies)
    Tc = MAQ['site']['toiture']['edicule']; cu0, cu1 = ((Tc[1], Tc[3]) if axe == 'x' else (Tc[0], Tc[2]))
    def dalle_cage(p):
        b = p['bb']; f = p['fill']
        if not (b[0] >= cu0 + d - 0.30 and b[2] <= cu1 + d + 0.30): return False
        return any(za - 0.08 <= b[1] and b[3] <= zb + 0.12 for za, zb in ((3.80, 4.00), (7.20, 7.40))) and (b[2] - b[0]) > 0.12
    n_ret += F.retirer(filtre=dalle_cage)
    n_ret += F.retirer(filtre=lambda p: p['bb'][3] <= 0.05 and p['bb'][1] < -0.30 and (p['bb'][2] - p['bb'][0]) > 5.0 and p['fill'] is not None)   # aplat de sol d'origine (S2)
    D = dp.Dessin()
    bb = [p['bb'] for p in F.prims]
    g0 = min(b[0] for b in bb) - 0.3; g1 = max(b[2] for b in bb) + 0.3
    dp.terrain_coupe(D, g0, g1, 0.0, 1.20)                                                # sol hachuré (charte croquis)
    D.poly(rect(ub0, 0.0, ub1, 0.45), 'A-SITE', 0.3, (0.47, 0.47, 0.47), fond=(0.86, 0.84, 0.80))   # hérisson
    for i in range(int((ub1 - ub0) / 0.15)):
        for j in range(3):
            D.cercle((ub0 + 0.08 + i * 0.15, 0.08 + j * 0.15), 0.02, 'A-SITE', 0.1, (0.47, 0.47, 0.47), fond=(0.47, 0.47, 0.47))
    F.vers_dessin(D)
    D.ligne((g0, 0.0), (g1, 0.0), 'A-SITE', 0.8, (0.12, 0.12, 0.12))
    if axe == 'x':      # SD04 (chambre -> terrasse) vue au-delà : dessinée avant le mobilier (DOC-043)
        o = next(o for o in MAQ['niveaux']['FF']['ouvertures'] if o['repere'] == 'SD04')
        dessiner_ouverture(D, o, o['rect'][1] + d, o['rect'][3] + d, o['z_bas'], o['z_haut'])
    n_obj = mobilier_coupe(D, axe, c, d)
    escaliers_coupe(D, axe, c, d)
    murs_coupes_maquette(D, axe, c, d)
    dalles_coupe(D, axe, c, d, cu0, cu1)
    # (3e passage) poutres de transfert coupées : retombée en pointillé sous le plancher qui les porte
    murs_rf = {w['id']: w['rect'] for w in dp.niveau_toiture(MAQ)['murs']}
    murs_ff = {w['id']: w['rect'] for w in MAQ['niveaux']['FF']['murs']}
    for q in MAQ['niveaux']['FF'].get('poutres_transfert', []):
        r = murs_ff.get(q['mur']) or murs_rf.get(q['mur'])
        if not r: continue
        zb = 3.80 if q['mur'] in murs_ff else 7.40
        if (axe == 'x' and r[0] <= c <= r[2]) or (axe == 'y' and r[1] <= c <= r[3]):
            u0, u1 = (r[1], r[3]) if axe == 'x' else (r[0], r[2])
            D.poly(rect(u0 + d, zb - 0.45, u1 + d, zb), 'A-STRU', 0.5, (0.1, 0.1, 0.1), tirets=(3, 2))
            D.texte(((u0 + u1) / 2 + d, zb - 0.62), 'TB', 0.14, 'A-STRU', True, coul=(0.1, 0.1, 0.1))
    if axe == 'x':          # terrasse du pavillon (+0.55) et ses marches coupées, hachurées (masquent le fond)
        zd = MAQ['site']['deck']['z']; pv = MAQ['site']['deck']['parties']['pavillon']
        if pv[0] <= c <= pv[2]:
            D.poly(rect(pv[1] + d, 0.0, pv[3] + d, zd), 'A-WALL', 0.4, (0, 0, 0), fond=(0.62, 0.62, 0.60))
            for k in range(int((pv[3] - pv[1]) / 0.25)):
                xa = pv[1] + d + k * 0.25; D.ligne((xa, 0.0), (min(xa + 0.25, pv[3] + d), zd), 'A-WALL', 0.2, (0.2, 0.2, 0.2))
        for m in MAQ['site']['marches']:
            r = m['rect']
            if m['nom'].startswith('pavilion') and r[0] <= c <= r[2]:
                n = m.get('n', 4); h = zd / n; g = (r[3] - r[1]) / (n - 1)
                for k in range(n - 1):
                    D.poly(rect(r[1] + d + k * g, 0.0, r[1] + d + (k + 1) * g, h * (k + 1)), 'A-WALL', 0.4, (0, 0, 0), fond=(0.62, 0.62, 0.60))
    T_ = MAQ['site']['toiture']; ex0, ey0, ex1, ey1 = T_['edicule']
    for a_, b_ in (((ey0, ey0 + 0.15), (ey1 - 0.15, ey1)) if axe == 'x' else ((ex0, ex0 + 0.15), (ex1 - 0.15, ex1))):
        D.poly(rect(a_ + d, 7.40, b_ + d, 10.05), 'A-WALL', 0.3, (0, 0, 0), fond=MUR_COUPE)
    D.poly(rect((ey0 if axe == 'x' else ex0) + d, 10.05, (ey1 if axe == 'x' else ex1) + d, 10.25), 'A-WALL', 0.3, (0, 0, 0), fond=MUR_COUPE)
    if axe == 'x':         # semelles des poteaux du pavillon (vus au-delà de la coupe)
        for py in (-0.10, -3.65):
            D.poly(rect(py - 0.10 + d, -0.80, py + 0.10 + d, 0.0), 'A-STRU', 0.3, (0.3, 0.3, 0.3), fond=(0.75, 0.75, 0.75))
            D.poly(rect(py - 0.30 + d, -1.10, py + 0.30 + d, -0.80), 'A-STRU', 0.3, (0.3, 0.3, 0.3), fond=(0.85, 0.85, 0.85))
            for k in range(6):
                xa = py - 0.30 + d + k * 0.10; D.ligne((xa, -1.10), (xa + 0.10, -0.80), 'A-STRU', 0.2, (0.3, 0.3, 0.3))
    # garde-corps vitré du vide sur hall (h 1.00) : coupé aux deux bords du vide
    # (indice C, 2e passage) : chaque garde-corps de la maquette coupé par le plan, posé sur son vrai support
    for u_, zb in gardes_coupes(axe, c):
        D.poly(rect(u_ + d - 0.03, zb, u_ + d + 0.03, zb + 1.00), 'A-GLAZ', 0.3, ANTH, fond=(0.66, 0.75, 0.8))
        D.ligne((u_ + d - 0.05, zb + 1.00), (u_ + d + 0.05, zb + 1.00), 'A-GLAZ', 1.2, ANTH)
    if axe == 'x':   # hotte de l'îlot (plafond) vue en coupe
        for q in MAQ['niveaux']['GF'].get('equipements', []):
            if 'ISLAND' in q['nom']:
                r = q['rect']; D.poly(rect(r[1] + d, 2.95, r[3] + d, 3.45), 'A-FURN', 0.4, (0.5, 0.5, 0.5), fond=(0.85, 0.85, 0.83))
                D.poly(rect((r[1] + r[3]) / 2 + d - 0.12, 3.45, (r[1] + r[3]) / 2 + d + 0.12, 3.85), 'A-FURN', 0.4, (0.5, 0.5, 0.5), fond=(0.85, 0.85, 0.83))
    for t in F.textes():
        if t['texte'] == 'ROOF TERRACE': t['z'] += 0.0
    couvertures(D, d, (axe, c))
    habillage(D, F, 1, 'y' if axe == 'x' else 'x', lambda p: p, d, [((7.40 if axe == 'x' else 9.80) + d, 0.60, 1)])
    textes_fond(D, F, exclure=('ROOF TERRACE',) if axe == 'x' else ())
    t84 = next((t for t in F.textes() if t['texte'].startswith('+8.40')), None)     # repère de niveau +10.25 (édicule)
    if t84:
        dz = 10.25 - 8.40; u0 = t84['u'] + 1.47 if t84['u'] < 5 else t84['u'] - 0.85   # même dessin que les repères d'origine
        D.ligne((u0, 10.25), (u0 + 0.60, 10.25), 'A-ANNO', 0.3, (0.33, 0.33, 0.33))
        D.poly([(u0 + 0.16, 10.45), (u0 + 0.44, 10.45), (u0 + 0.30, 10.25)], 'A-ANNO', 0.3, (0.33, 0.33, 0.33), fond=(0.33, 0.33, 0.33))
        D.texte((t84['u'], t84['z'] + dz), '+10.25 penthouse', t84['taille'] / dp.PT_M_100, 'A-ANNO', t84['gras'], False, coul=t84['coul'])
    if axe == 'x': D.texte((2.26 + d, 6.30), 'ROOF TERRACE +3.95', 0.16, 'A-ANNO', True, False)
    notes = ['Cut %s = %.2f, looking %s. Void guardrail h 1.00.' % (axe, c, 'west' if axe == 'x' else 'north'),
             'Structure (stage 3, engineer) - transfer beams under',
             '   first-floor walls not carried by a ground-floor wall:'] + [
             '   %s (span %.2f): %s.' % (l, p_, o_.split(' (')[0].split(',')[0]) for l, p_, o_ in sorted({(q['ligne'], q['portee'], q['objet'])
                                                                            for q in MAQ['niveaux']['FF'].get('poutres_transfert', [])})] + [
             'TB = transfer beam (dashed, depth to be confirmed).',
             'Grid axes as on the plans; figure 1.70 for scale.',
             'Stairs: n treads + 1 riser onto each landing / floor.',
             'Furniture in section redrawn from the model',
             f'   (revision {REV} layout). Cut walls, openings and RC',
             '   canopies redrawn from the model.', 'All levels and dimensions in metres.']
    return sortir(D, numero, titre, 'Section', titre, notes), d, n_ok, n_m, n_ret, n_obj


# ----------------------------------------------------------------------------------------------- toiture
def toiture(variante=None):
    X0, Y0 = json.load(open(os.path.join(ROOT, 'projet', 'maquette', 'extraction', 'GF_brut.json')))['source']['origine_pt']
    F = vr.Fond(PDF, 21, 100, plan=(X0, Y0))
    zone = box(-0.25, -3.85, 14.65, 14.45)
    garde = lambda p: box(*p['bb']).within(zone) and not (p['fill'] and len(p['fill']) == 3 and p['fill'][1] > p['fill'][0] + 0.05 and p['fill'][1] > p['fill'][2])
    F.prims = [p for p in F.prims if garde(p)]
    # indice C (demande client) : une seule évacuation (angle nord-est, côté panneaux) ; panneaux solaires déplacés
    # dans la zone sud-ouest (ils gênaient l'arrivée de l'escalier) ; flèches de pente redessinées vers l'avaloir
    AVALOIR = (12.63, 13.85); PV_DE = (9.03, 10.6); PV_VERS = (1.00, 1.60)
    cage = box(8.3, 5.7, 13.0, 9.7)
    def a_retirer(p):
        b = p['bb']; cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        carre = p['fill'] and max(p['fill']) < 0.2 and (b[2] - b[0]) < 0.3 and (b[3] - b[1]) < 0.3 and (b[2] - b[0]) > 0.2
        if carre and cy > 0 and 0 < cx < 13.1 and math.dist((cx, cy), AVALOIR) > 0.3: return True       # avaloirs supprimés
        pente = p['type'] == 's' and p['color'] and abs(p['color'][0] - 0.47) < 0.02 and not box(*b).within(cage)
        return pente and 0 <= b[0] and b[2] <= 13.1 and 0 <= b[1] and b[3] <= 14.3
    F.prims = [p for p in F.prims if not a_retirer(p)]
    # escalier de l'édicule : dessin d'origine retiré, redessiné depuis la maquette (volées C, D, paliers, vide)
    INT_CAGE = box(*MAQ['site']['toiture']['tremie'])
    F.prims = [p for p in F.prims if not box(*p['bb']).within(INT_CAGE)]
    dx, dy = PV_VERS[0] - PV_DE[0], PV_VERS[1] - PV_DE[1]
    for p in F.prims:
        if p['fill'] and tuple(round(x, 2) for x in p['fill']) == (0.24, 0.31, 0.4):
            p['pts'] = [(x + dx, z + dy) for x, z in p['pts']]
    D = dp.Dessin()
    # (client 15/10) toiture +7.40 en trait normal ; tout ce qui est vu en contrebas (terrasse +3.95, balcons, auvents,
    # jardin, parking) en demi-teinte
    TOIT = box(0, 0, 13.1, 14.3).difference(box(6.43, -1.0, 13.2, 5.60))
    haut = lambda p: TOIT.buffer(0.05).contains(box(*p['bb']).centroid)
    tous = F.prims
    dp.site(D, MAQ['site'], MAQ['emprise'])
    F.prims = [p for p in tous if not haut(p)]; F.vers_dessin(D)
    dp.demi_teinte(D, 0)
    F.prims = [p for p in tous if haut(p)]; F.vers_dessin(D); F.prims = tous
    D.poly(rect(*MAQ['site']['toiture']['tremie']), 'A-STAIR', 0.1, (1, 1, 1), fond=(1, 1, 1))
    for w in dp.niveau_toiture(MAQ)['murs']:         # murs de l'édicule (maquette) par-dessus le fond
        D.poly(rect(*w['rect']), 'A-WALL', 0.3, (0, 0, 0), fond=(0.15, 0.15, 0.15))
    tc = MAQ['site']['toiture']['tremie']
    for t_ in MAQ['niveaux']['FF']['tremies']:      # vide sur le hall et trémie de la volée B (maquette)
        v = [max(t_['rect'][0], tc[0]), max(t_['rect'][1], tc[1]), min(t_['rect'][2], 11.88), min(t_['rect'][3], tc[3])]
        D.poly(rect(*v), 'A-STAIR', 0.3, (0.4, 0.4, 0.4), tirets=(3, 2))
        D.ligne((v[0], v[1]), (v[2], v[3]), 'A-STAIR', 0.2, (0.6, 0.6, 0.6), tirets=(3, 2))
        D.ligne((v[0], v[3]), (v[2], v[1]), 'A-STAIR', 0.2, (0.6, 0.6, 0.6), tirets=(3, 2))
    dp.escaliers(D, MAQ['niveaux']['FF'])
    D.texte((10.1, 7.65), 'void over hall', 0.09, 'A-ANNO', coul=(0.4, 0.4, 0.4))
    for t in F.textes():
        if INT_CAGE.contains(Point(t['u'], t['z'])) and not t['texte'].startswith('STAIR PENTHOUSE'): continue
        if -0.25 <= t['u'] <= 14.65 and -3.85 <= t['z'] <= 14.45:
            pos = (t['u'], t['z']); t = dict(t, texte=t['texte'].replace('+4.00', '+3.95'))
            if t['texte'].startswith('PV-ready'): pos = (t['u'] + dx, t['z'] + dy - 3.55)
            elif t['texte'].startswith('ACCESSIBLE ROOF'): pos = (2.2, 9.6)
            elif t['texte'].startswith('+7.40 — parapet'): pos = (2.45, 9.35)
            D.texte(pos, t['texte'], t['taille'] / dp.PT_M_100, 'A-ANNO', t['gras'], False, coul=t['coul'])
    GRIS = (0.47, 0.47, 0.47)
    # (indice D, retour client) 3 siphons de la maquette (angles NO, NE, SO) ; flèches de pente vers le siphon le plus proche
    T_ = MAQ['site']['toiture']; cs = [((r[0] + r[2]) / 2, (r[1] + r[3]) / 2) for r in T_['avaloirs']]
    for a in ((5.6, 12.4), (3.0, 9.6), (7.3, 12.9), (10.6, 11.2), (2.6, 6.4), (5.9, 1.4), (5.6, 4.9)):
        c = min(cs, key=lambda c_: math.dist(c_, a)); L_ = math.dist(a, c); b = (a[0] + (c[0] - a[0]) * (L_ - 0.55) / L_, a[1] + (c[1] - a[1]) * (L_ - 0.55) / L_)
        D.ligne(a, b, 'A-ANNO', 0.4, GRIS)
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for s_ in (-0.4, 0.4):
            D.ligne(b, (b[0] - 0.35 * math.cos(ang + s_), b[1] - 0.35 * math.sin(ang + s_)), 'A-ANNO', 0.4, GRIS)
    for r, (cx_, cy_) in zip(T_['avaloirs'], cs):
        D.poly(rect(*r), 'A-PLUMB', 0.3, (0.1, 0.3, 0.6), fond=(0.75, 0.85, 0.95))
        D.texte((cx_ + (0.35 if cx_ < 6 else -1.35), cy_ + (0.30 if cy_ < 7 else -0.42)), 'RWO +%.2f' % T_['niveau_avaloir'], 0.10, 'A-ANNO', False, False, coul=(0.1, 0.3, 0.6))
    for r in MAQ['niveaux']['FF']['exterieurs'].get('avaloirs', []):
        D.poly(rect(*r), 'A-PLUMB', 0.3, (0.1, 0.3, 0.6), fond=(0.75, 0.85, 0.95)); D.texte(((r[2] + 0.30) if r[0] > 13.1 else (r[0] - 0.55), r[1] + 0.05), 'RWO', 0.09, 'A-ANNO', coul=(0.1, 0.3, 0.6))
    i_bas = len(D.P)
    pr = MAQ['niveaux']['FF']['exterieurs']['pergola']['rect']       # pergola de la terrasse (poutres jusqu'au mur de la chambre)
    D.poly(rect(*pr), 'A-ANNO', 0.6, ANTH, tirets=(4, 2))
    for r in MAQ['niveaux']['FF']['poteaux']:
        if r[1] >= 0: D.poly(rect(*r), 'A-WALL', 0.2, (0.2, 0.2, 0.2), fond=ANTH)
    D.texte((pr[0] + 0.25, pr[1] + 0.25), 'pergola beams on base plates in the bedroom wall', 0.08, 'A-ANNO', False, False, coul=(0.3, 0.3, 0.3))
    balcons = [box(*s_['rect']) for s_ in MAQ['niveaux']['FF']['exterieurs']['sols'] if s_['nom'] == 'BALCONY']
    for n in ('GF', 'FF'):          # auvents béton vus de dessus (ceux du RDC cachés sous un balcon ne sont pas dessinés)
        for a in MAQ['niveaux'][n].get('auvents', []):
            if n == 'GF' and any(box(*a['rect']).intersection(b_).area > 0.5 * box(*a['rect']).area for b_ in balcons): continue
            D.poly(rect(*a['rect']), 'A-ELEV', 0.3, (0.3, 0.3, 0.3), fond=(0.82, 0.82, 0.80))
    dp.demi_teinte(D, i_bas)                         # pergola, poteaux, auvents : sous la toiture
    D.texte((11.9, -8.45), 'STREET (south)', 0.22, 'A-SITE', True)
    T_ = MAQ['site']['toiture']; pe = T_['porte_edicule']; r_ = pe['rect']
    D.texte(((r_[0] + r_[2]) / 2, r_[3] + 0.30), pe['repere'], 0.15, 'A-TAGS', False, True, coul=(0.1, 0.25, 0.55))
    gg = T_['gargouille']; gx, gy = gg['pos']
    D.ligne((gx, gy), (gx - 0.45, gy), 'A-PLUMB', 1.0, (0.1, 0.3, 0.6))
    D.texte((gx - 1.55, gy + 0.18), 'spout (penthouse roof falls 2 %)', 0.08, 'A-ANNO', coul=(0.1, 0.3, 0.6))
    AX = dp.quadrillage(dict(MAQ['niveaux'], RF=dp.niveau_toiture(MAQ)))
    bord = lambda a, k: abs(a['pos'] - 0.075) < 0.06 or abs(a['pos'] - ((W if k == 'x' else H) - 0.075)) < 0.06    # façades + édicule
    AXR = {k: [dict(a, niveaux=a['niveaux'] + ['RF']) if bord(a, k) and 'RF' not in a['niveaux'] else a for a in v] for k, v in AX.items()}
    dp.dessiner_quadrillage(D, AXR, 'RF', [0, 0, W, H], -7.55, -2.35, 14.9, 13.7)
    D.texte((13.85, 5.50), 'entrance canopy', 0.10, 'A-ANNO', rot=90, coul=(1, 1, 1))
    notes = ['Roof terrace +7.40, parapet +8.40; stair penthouse',
             '   roof +10.25 (future second floor +10.80).',
             '2 x 2000 L water tanks, AC outdoor units.',
             'PV-ready zone moved to the south-west (clear of the',
             '   stair arrival and the door to the roof terrace).',
             'Falls 1.5 % to 3 rainwater outlets (RWO) at the',
             '   NW, NE and SW corners; terrace +3.95: own RWO.',
             'Roof finish +7.40 at the high points, falls 1.5 % to',
             '   the outlets (+%.2f); parapet +8.40 = 1.00 above' % MAQ['site']['toiture']['niveau_avaloir'],
             '   the highest point everywhere.',
             '   Rainwater pipes: plumbing (stage 3).',
             'RC canopies 0.60 over the windows (grey).',
             f'Site (gate, path) as plan SD-004 rev. {REV}.', 'All dimensions in metres.']
    carto = dict(CARTO, vue='Plan View', planche='SD - 006', sous_titre='Roof plan + site', echelle='1:100')
    legende = {'titre_vue': '02 - Roof Plan', 'sous_titre_vue': f'Scale 1:100   -   Revision {REV}', 'numero_vue': '1',
               'blocs': [{'titre': 'REVISIONS', 'lignes': REVISIONS}]}
    nom = os.path.join(HERE, f'SD-006_{REV}_Roof_Plan')
    if variante:                 # (client 15/10) plan de surface et plan de circulation de la toiture-terrasse
        nom, carto, legende = toiture_variante(D, variante, carto, legende)
    else:
        noter('SD - 006', 'Roof Plan', [{'titre': 'NOTES', 'lignes': [(n, '') for n in notes]}])
    dp.rendre_pdf(D, nom + '.pdf', {'pt': (16, 40, 745, 822), 'm': (-4.3, -9.4, 21.7, 17.3)}, carto, legende)
    dp.rendre_dxf(D, nom + '.dxf')
    return nom


def toiture_variante(D, variante, carto, legende):
    """SD-006A (surfaces par fonction) et SD-006B (circulation calculée) de la toiture-terrasse +7.40."""
    import parcours as pc
    from shapely.ops import unary_union
    T = MAQ['site']['toiture']; ed = box(*T['edicule'])
    toit = box(0.15, 0.15, 12.95, 14.15).difference(box(6.28, -1.0, 13.2, 5.75))
    tech = unary_union([Point(c['centre']).buffer(c['rayon']) for c in T['citernes']] + [box(*r) for r in T['clim']]
                       + [box(*T['pv']['rect'])])
    palier = box(11.88, 8.47, 12.95, 9.60)
    if variante == 'zonage':
        ALPHA = 0.42
        zones = [('Accessible roof terrace +7.40', toit.difference(ed).difference(tech), (0.55, 0.80, 0.80)),
                 ('Technical (water tanks, AC units, PV)', tech, (0.85, 0.72, 0.50)),
                 ('Stair penthouse (circulation)', ed.buffer(-0.15), (0.70, 0.70, 0.70))]
        lignes = []
        for lib, g, c in zones:
            for part in getattr(g, 'geoms', [g]):
                D.poly(list(part.exterior.coords), 'A-CTRL', 0.0, c, fond=c, alpha=ALPHA)
            lignes.append((lib, '%.1f m²' % g.area))
        legende = {'titre_vue': 'Functional zoning - Roof terrace', 'sous_titre_vue': 'Scale 1:100   -   Revision %s' % REV, 'numero_vue': '1',
                   'blocs': [{'titre': 'ZONES (areas computed from the model)', 'lignes': lignes},
                             {'titre': 'REVISIONS', 'lignes': [REVISIONS[-1]]}],
                   'symboles': [({'ep': 6.0, 'coul': tuple(1 - ALPHA + ALPHA * x for x in c)}, lib) for lib, g, c in zones]}
        return (os.path.join(HERE, f'SD-006A_{REV}_Zoning_Roof'), dict(carto, vue='Functional zoning', planche='SD - 006A', sous_titre='Roof terrace'), legende)
    # circulation : de l'arrivée de l'escalier (palier +7.40) par D20 vers les équipements à entretenir et les siphons
    libre = unary_union([toit.difference(ed).difference(tech), palier, box(12.0, 9.50, 12.9, 9.85)])
    O = box(-6, -6, 20, 20).difference(libre)
    depart = (12.43, 9.05)
    cs = [((r[0] + r[2]) / 2, (r[1] + r[3]) / 2) for r in T['avaloirs']]
    buts = [('Water tanks', (T['citernes'][0]['centre'][0], T['citernes'][0]['centre'][1] - T['citernes'][0]['rayon'] - 0.45), (0.10, 0.40, 0.85)),
            ('AC outdoor units', (2.10, 7.75), (0.10, 0.62, 0.25)),
            ('PV zone (future panels)', (4.55, 3.30), (0.95, 0.50, 0.05)),
            ('Rainwater outlets (maintenance)', None, (0.55, 0.20, 0.75))]
    lignes = []
    sys.path.insert(0, os.path.join(ROOT, 'projet', 'controle')); import controle_parcours as _cpt
    for k, (lib, but, coul) in enumerate(buts, 1):
        etapes = [depart, (12.45, 10.30)] + ([but] if but else [(c[0] + (0.5 if c[0] < 6 else -0.5), c[1] + (0.5 if c[1] < 7 else -0.5)) for c in cs])
        r = pc.parcours_libre(libre, O, etapes)
        if not r['trajet']: lignes.append(('%d  %s: NOT FOUND' % (k, lib), '')); continue
        _cpt.fleches(D, r['trajet'], coul)
        D.cercle(r['trajet'][0], 0.24, 'A-CTRL', 0.5, coul, fond=(1, 1, 1)) if k == 1 else None
        lignes.append(('%d  %s' % (k, lib), '')); lignes.append(('     %.1f m; narrowest %.2f' % (r['longueur'], r['largeur'] or 0), ''))
    D.texte((depart[0] - 0.9, depart[1]), 'from the stair', 0.10, 'A-CTRL', False, False, coul=(0.2, 0.2, 0.2))
    legende = {'titre_vue': 'Circulation - Roof terrace', 'sous_titre_vue': 'Scale 1:100   -   Revision %s' % REV, 'numero_vue': '1',
               'blocs': [{'titre': 'ROUTES (computed on the design model)', 'lignes': lignes},
                         {'titre': 'REVISIONS', 'lignes': [REVISIONS[-1]]}], 'symboles': []}
    return (os.path.join(HERE, f'SD-006B_{REV}_Circulation_Roof'), dict(carto, vue='Circulation', planche='SD - 006B', sous_titre='Roof terrace'), legende)


def portail():
    """SD-013 : élévation sur rue du mur de clôture et du portail coulissant (1:50)."""
    D = dp.Dessin(); g = MAQ['site']['portail']; x0, x1 = g['position'][0], g['position'][2]
    murg, murd = min(11.0, x0 - g['largeur'] - 0.5), 21.09          # mur de rue dessiné jusqu'au bout du refoulement
    dp.terrain_coupe(D, murg - 0.5, murd + 0.5, 0.0, 0.50)
    for a, b in ((murg, x0), (x1, murd)):
        D.poly(rect(a, 0.0, b, 2.10), 'A-ELEV', 0.5, (0.12, 0.12, 0.12), fond=(0.96, 0.95, 0.93))
        D.poly(rect(a, 2.02, b, 2.10), 'A-ELEV', 0.3, (0.12, 0.12, 0.12), fond=ANTH)
        for i in range(int((b - a) / 0.12)):
            u = a + 0.06 + i * 0.12
            if u < b: D.poly(rect(u, 1.30, u + 0.06, 2.00), 'A-ELEV', 0.2, (0.49, 0.33, 0.2), fond=(0.69, 0.49, 0.32))
    D.poly(rect(x0, 0.02, x1, 2.10), 'A-DOOR', 0.7, (0.1, 0.1, 0.1), fond=(0.30, 0.32, 0.34))
    for i in range(1, int((x1 - x0) / 0.12)):
        u = x0 + i * (x1 - x0) / int((x1 - x0) / 0.12); D.ligne((u, 0.08), (u, 2.04), 'A-DOOR', 0.3, (0.16, 0.17, 0.19))
    w = g['portillon']['largeur']
    D.poly(rect(x0 + 0.10, 0.05, x0 + 0.10 + w, 2.00), 'A-DOOR', 1.0, (0.85, 0.45, 0.1))
    D.ligne((x0 + 0.10 + w - 0.10, 0.95), (x0 + 0.10 + w - 0.10, 1.20), 'A-DOOR', 1.5, (0.9, 0.9, 0.9))
    lg = g['largeur']
    D.ligne((x0 - lg, 2.35), (x0, 2.35), 'A-ANNO', 0.4, (0.3, 0.3, 0.3), tirets=(4, 2))
    D.texte((x0 - lg / 2, 2.55), 'gate slides west behind the wall (run-back %.2f)' % lg, 0.16, 'A-ANNO')
    dp.cote(D, x0, x1, -0.95, 'x', '%.2f' % (x1 - x0)); dp.cote(D, x0 + 0.10, x0 + 0.10 + w, 2.75, 'x', 'wicket %.2f' % w)
    dp.cote(D, 0.0, 2.10, murg - 0.45, 'y', 'wall 2.10'); dp.cote(D, 0.0, 2.00, x0 - 0.35, 'y', 'wicket 2.00')
    for u in (murg,):                 # ligne de coupure à l'ouest seulement (l'extrémité est est l'angle réel de la parcelle)
        D.ligne((u, -0.3), (u, 0.9), 'A-ANNO', 0.4, (0.2, 0.2, 0.2)); D.ligne((u, 0.9), (u - 0.12, 1.05), 'A-ANNO', 0.4, (0.2, 0.2, 0.2))
        D.ligne((u - 0.12, 1.05), (u + 0.12, 1.20), 'A-ANNO', 0.4, (0.2, 0.2, 0.2)); D.ligne((u + 0.12, 1.20), (u, 1.35), 'A-ANNO', 0.4, (0.2, 0.2, 0.2))
        D.ligne((u, 1.35), (u, 2.40), 'A-ANNO', 0.4, (0.2, 0.2, 0.2))
    D.texte(((x0 + x1) / 2, 1.05), 'GT01  SLIDING GATE', 0.2, 'A-ANNO', True, coul=(1, 1, 1))
    D.texte(((murg + x0) / 2, 0.6), 'rendered blockwork wall, timber slats, anthracite coping', 0.13, 'A-ANNO')
    notes = ['Street-side boundary wall h 2.10 (neighbours 2.00), 0.20 thick.',
             'Sliding gate %.2f x 2.10, steel, anthracite, vertical slats;' % MAQ['site']['portail']['largeur'],
             '   integrated pedestrian wicket door 0.90 x 2.00 (outlined),',
             '   at the west end, opening onto the pedestrian lane 0.90.',
             'Gate widened to 6.20: 2 x Land Cruiser 300 drive straight in.',
             'Partial view (break line at the west end); east end = plot corner.',
             'Intercom, letter box and house number on the wall: stage 3.', 'All dimensions in metres.']
    return sortir(D, 'SD - 013', 'Boundary Wall and Gate - Street Elevation', 'Elevation', 'Boundary wall + gate', notes, echelle=50)


if __name__ == '__main__':
    print(toiture()); print(toiture('zonage')); print(toiture('circulation'))
    for f in 'SENW':
        print(f, facade(f))
    for c in 'AB':
        print(c, coupe(c))
    print(portail())
