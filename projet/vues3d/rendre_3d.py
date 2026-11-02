"""YAMA HOUSE - vues 3D schématiques (indice C) générées depuis la maquette de données.

python3 -I projet/vues3d/rendre_3d.py VARIANTE [VUE ...]   (VARIANTE : complet | rdc | etage ; sans VUE = toutes les vues de la variante)
  -> projet/vues3d/rendus/<vue>.png + <vue>.json (étiquettes projetées : nom de pièce, position image)
Variante « rdc » : maquette coupée à 1.70 au-dessus du sol du RDC (+2.30) ; « etage » : coupée à +5.70 (FF + 1.70).
Aucune géométrie n'est dessinée à la main : tout vient de maquette.json (+ éléments d'enveloppe propres à YAMA ci-dessous,
relus sur les plans / façades / coupes de l'esquisse : dalles, escaliers, acrotères, cadres de balcons, pergolas, parements).
"""
import json, math, os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, '/home/user/atelier-archi-ingenierie/outils')
import bpy
import maquette_3d as m3
from shapely.geometry import Polygon, box, Point

MAQ = json.load(open(os.path.join(ROOT, 'projet', 'maquette', 'maquette.json')))
from empreinte import empreinte as _emp
EMPREINTE = _emp(MAQ)          # calculée au chargement (la construction 3D ajoute ensuite des objets à MAQ)
W, H = 13.10, 14.30
OUT = os.path.join(HERE, 'rendus'); os.makedirs(OUT, exist_ok=True)
G, F = MAQ['niveaux']['GF'], MAQ['niveaux']['FF']
TREMIE_FF = [t['rect'] for t in F['tremies']]          # trémies : définies dans la maquette (règle MOD-012)
VIDE = TREMIE_FF[0]
TERRASSE = [6.43, 0.0, 13.10, 5.60]
EDICULE = MAQ['site']['toiture']['edicule']


def rect_moins(r, trous):
    g = box(*r)
    for t in trous: g = g.difference(box(*t))
    return [list(p.exterior.coords)[:-1] for p in (g.geoms if hasattr(g, 'geoms') else [g])]


def enveloppe(S):
    B = S.boite
    # socle (plinthe) + dalle du RDC
    B(0, 0, 0.0, W, H, 0.585, 'socle', 'bat', poche=True)
    # dalle de l'étage (trémie du vide et de l'escalier), balcons
    g = box(0, 0, W, H)
    for t in TREMIE_FF: g = g.difference(box(*t))
    S.dalle(g.difference(box(*TERRASSE)), 3.80, 3.985, 'beton')     # trémie du vide et de l'escalier respectée
    S.dalle(box(*TERRASSE), 3.80, 3.935, 'beton')                    # terrasse : sol fini extérieur +3.95
    for s in F['exterieurs']['sols']:
        if s['nom'] == 'BALCONY':
            r = s['rect']; B(r[0], r[1], 3.80, r[2], r[3], 3.935, 'beton', 'dalles', poche=True)
            B(r[0], r[1], 3.935, r[2], r[3], 3.95, 'sol_ext', 'sols')
    B(*TERRASSE[:2], 3.935, *TERRASSE[2:], 3.95, 'sol_ext', 'sols')    # sols extérieurs finis +3.95 (seuils, maquette)    # terrasses, balcons : antidérapant extérieur
    # toiture-terrasse (+7.40) : dalle hors terrasse et hors édicule, acrotères h 1.00
    toit = box(0, 0, W, H).difference(box(*TERRASSE)).difference(box(*EDICULE))
    S.dalle(toit, 7.20, 7.40, 'beton')
    e = 0.15
    S.tag = 'env:acrotere'
    for r in ([0, 0, e, H], [0, H - e, W, H], [W - e, TERRASSE[3], W, EDICULE[1]], [W - e, EDICULE[3], W, H], [0, 0, TERRASSE[0], e],
              [TERRASSE[0] - e, 0, TERRASSE[0], TERRASSE[3]], [TERRASSE[0], TERRASSE[3] - e, EDICULE[0], TERRASSE[3]]):
        B(r[0], r[1], 7.40, r[2], r[3], 8.40, 'enduit', 'bat', poche=True)     # acrotère interrompu au droit de l'édicule (pas de mur doublé)
    # édicule d'escalier (+10.25), porte d'accès au nord (maquette : toiture.porte_edicule)
    T_ = MAQ['site']['toiture']; x0, y0, x1, y1 = T_['edicule']; pe = T_['porte_edicule']
    S.tag = 'env:edicule'
    for r in ([x0, y0, x0 + e, y1], [x1 - e, y0, x1, y1], [x0, y0, x1, y0 + e], [x0, y1 - e, pe['rect'][0], y1], [pe['rect'][2], y1 - e, x1 - e, y1]):
        B(r[0], r[1], 7.40, r[2], r[3], 10.05, 'enduit', 'bat', poche=True)
    B(pe['rect'][0], y1 - e, pe['z'][1], pe['rect'][2], y1, 10.05, 'enduit', 'bat', poche=True)
    rel = pe.get('releve', 0.0)                         # relevé d'étanchéité sous la porte de l'édicule
    if rel: B(pe['rect'][0], y1 - e, 7.40, pe['rect'][2], y1, 7.40 + rel, 'enduit', 'bat', poche=True)
    B(pe['rect'][0] + 0.02, y1 - 0.09, pe['z'][0] + rel, pe['rect'][2] - 0.02, y1 - 0.06, pe['z'][1], 'anthracite', 'menuis')
    B(x0, y0, 10.05, x1, y1, 10.25, 'anthracite', 'bat', poche=True)
    gg = T_.get('gargouille')                            # exutoire du toit de l'édicule
    if gg: B(gg['pos'][0] - 0.45, gg['pos'][1] - 0.06, 10.05, gg['pos'][0], gg['pos'][1] + 0.06, 10.11, 'inox', 'bat')
    S.tag = 'env:toiture'
    # équipements de toiture : citernes, groupes de clim, panneaux PV (zone sud-ouest)
    for c in T_['citernes']:
        S.cylindre(c['centre'][0], c['centre'][1], c['rayon'], 7.40, 7.40 + c['hauteur'], 'blanc', 'bat')
    for r in T_['clim']:
        B(r[0], r[1], 7.40, r[2], r[3], 8.10, 'inox', 'bat')
    pv = T_['pv']; px0, py0, px1, py1 = pv['rect']; ni, nj = pv['panneaux']
    for i in range(ni):
        for j in range(nj):
            x = px0 + i * (px1 - px0) / ni; y = py0 + j * (py1 - py0) / nj
            B(x + 0.02, y + 0.02, 7.70, x + (px1 - px0) / ni - 0.02, y + (py1 - py0) / nj - 0.02, 7.75, 'anthracite', 'bat')
    # escaliers : définition unique dans la maquette (volées + paliers), garde-corps des côtés ouverts
    S.tag = 'esc'
    for M in (G, F):
        for e_ in M.get('escaliers', []):
            if e_['type'] == 'volee':
                escalier_droit(S, e_['sens'], e_['larg'][0], e_['larg'][1], e_['depart'], e_['z0'], e_['n'], e_['giron'], e_['hauteur'])
            else:
                r = e_['rect']; B(r[0], r[1], e_['z'] - 0.20, r[2], r[3], e_['z'], 'beton', 'esc', poche=True)
        vol = {e_['nom']: e_ for e_ in M.get('escaliers', []) if e_['type'] == 'volee'}
        for gc in M.get('garde_corps_escalier', []):
            e_ = vol[gc['volee']]; (ax, ay), (bx, by) = gc['pts']
            for k in range(e_['n']):
                zt = e_['z0'] + (k + 1) * e_['hauteur']
                if e_['sens'] in 'NS':
                    ya = e_['depart'] + k * e_['giron']; S.boite(ax - 0.01, ya, zt, ax + 0.01, ya + e_['giron'], zt + 1.0, 'verre', 'verre')
                else:
                    xa = e_['depart'] + (k if e_['sens'] == 'E' else -(k + 1)) * e_['giron']; S.boite(xa, ay - 0.01, zt, xa + e_['giron'], ay + 0.01, zt + 1.0, 'verre', 'verre')
        for gc in M.get('garde_corps_paliers', []):         # bords libres des paliers (chute) : garde-corps h 1.00
            (ax, ay), (bx, by) = gc['pts']
            S.boite(min(ax, bx) - 0.01, min(ay, by) - 0.01, gc['z'], max(ax, bx) + 0.01, max(ay, by) + 0.01, gc['z'] + 1.0, 'verre', 'verre')
    S.tag = 'env'
    # garde-corps vitrés (vide, terrasse, balcons) h 1.00
    for i_, pl in enumerate(F['exterieurs']['garde_corps_vitres']):
        z_ = 4.0 if i_ == 3 else 3.95                      # vide intérieur +4.00 ; terrasse et balcons +3.95
        for a, b in zip(pl, pl[1:]):
            if abs(a[0] - b[0]) < 1e-6: B(a[0] - 0.01, min(a[1], b[1]), z_, a[0] + 0.01, max(a[1], b[1]), z_ + 1.0, 'verre', 'verre')
            else: B(min(a[0], b[0]), a[1] - 0.01, z_, max(a[0], b[0]), a[1] + 0.01, z_ + 1.0, 'verre', 'verre')
    # cadres anthracite des balcons (+8.40) avec lames bois en partie haute
    cadre(S, [0.43, -1.80, 6.03, 0.0], 'S')
    cadre(S, [13.10, 10.35, 14.60, 13.65], 'E')
    # auvent d'entrée, auvents béton des fenêtres
    ae = MAQ['site']['auvents'][0]; a = ae['rect']; B(a[0] + 0.03, a[1], ae['z'][0], a[2], a[3], ae['z'][1], 'anthracite', 'bat', poche=True)   # devant le parement pierre
    for n in ('GF', 'FF'):
        for c in MAQ['niveaux'][n].get('auvents', []):
            r = c['rect']; B(r[0], r[1], c['z0'], r[2], r[3], c['z1'], 'beton', 'bat', poche=True)
    # pergolas : pavillon (RDC) et terrasse (étage, poutres sur platines dans le mur de la chambre)
    pp = MAQ['site']['pergola_pavillon']
    for r in pp['poteaux']: B(r[0], r[1], 0.60, r[2], r[3], 3.40, 'anthracite', 'bat', poche=True)
    r = pp['rect']; pergola(S, r, 3.20, 3.40, pp.get('couverture'))
    for r in F['poteaux']:
        if r[1] >= 0: B(r[0], r[1], 3.95, r[2], r[3], 6.80, 'anthracite', 'bat', poche=True)
    pergola(S, F['exterieurs']['pergola']['rect'], 6.60, 6.80, F['exterieurs']['pergola'].get('couverture'))
    # parements : pierre (sud RDC chambre 1, entrée est), bois (ouest étage, suite parentale)
    for pm in MAQ['site']['parements']:                   # définis dans la maquette (même valeur que les façades)
        parement(S, pm['face'], pm['de'], pm['a'], pm['z'][0], pm['z'][1], pm['mat'])


def escalier_droit(S, sens, a, b, depart, z0, n, g=0.27, h=0.17):
    """Volée droite de n marches : sens N / E / W / S ; a, b = bornes de largeur ; depart = coordonnée du départ."""
    for k in range(n):
        z1 = z0 + (k + 1) * h
        if sens == 'N': S.boite(a, depart + k * g, z0 + k * h - 0.17, b, depart + (k + 1) * g, z1, 'beton', 'esc', poche=True)
        elif sens == 'E': S.boite(depart + k * g, a, z0 + k * h - 0.17, depart + (k + 1) * g, b, z1, 'beton', 'esc', poche=True)
        elif sens == 'W': S.boite(depart - (k + 1) * g, a, z0 + k * h - 0.17, depart - k * g, b, z1, 'beton', 'esc', poche=True)


def cadre(S, r, face):
    x0, y0, x1, y1 = r; e = 0.15; B = S.boite
    if face == 'S':
        B(x0, y0, 3.95, x0 + e, y1, 8.40, 'anthracite', 'bat', poche=True); B(x1 - e, y0, 3.95, x1, y1, 8.40, 'anthracite', 'bat', poche=True)   # posé sur le sol du balcon
        B(x0, y0, 7.90, x1, y1, 8.40, 'anthracite', 'bat', poche=True)          # bandeau 0.50 et lames 6.60-7.90 (façade SD-007)
        for k in range(10): B(x0 + e, y0, 6.60 + k * 0.13, x1 - e, y0 + 0.05, 6.60 + k * 0.13 + 0.07, 'bois', 'bat', poche=True)
    else:
        B(x0, y0, 3.95, x1, y0 + e, 8.40, 'anthracite', 'bat', poche=True); B(x0, y1 - e, 3.95, x1, y1, 8.40, 'anthracite', 'bat', poche=True)
        B(x0, y0, 7.90, x1, y1, 8.40, 'anthracite', 'bat', poche=True)
        for k in range(10): B(x1 - 0.05, y0 + e, 6.60 + k * 0.13, x1, y1 - e, 6.60 + k * 0.13 + 0.07, 'bois', 'bat', poche=True)


def pergola(S, r, z0, z1, couverture=None):
    x0, y0, x1, y1 = r; B = S.boite
    if couverture:              # couverture polycarbonate posée sur les lames (pente négligée à cette échelle)
        B(x0, y0, z1 + 0.10, x1, y1, z1 + 0.12, 'verre', 'verre')
    B(x0, y0, z0, x1, y0 + 0.20, z1, 'anthracite', 'bat', poche=True); B(x0, y1 - 0.20, z0, x1, y1, z1, 'anthracite', 'bat', poche=True)
    B(x0, y0, z0, x0 + 0.20, y1, z1, 'anthracite', 'bat', poche=True); B(x1 - 0.20, y0, z0, x1, y1, z1, 'anthracite', 'bat', poche=True)
    n = int((x1 - x0) / 0.22)
    for k in range(1, n):
        x = x0 + k * (x1 - x0) / n; B(x - 0.03, y0, z1, x + 0.03, y1, z1 + 0.10, 'bois', 'bat', poche=True)


def parement(S, face, a, b, z0, z1, mat, e=0.03):
    """Parement sur une façade, percé de TOUTES les ouvertures de cette façade (trous intérieurs compris), avec retours
    dans les tableaux côté extérieur (jambages, appui, linteau) jusqu'à la menuiserie. (Erreur YAMA : un trou entièrement
    à l'intérieur du parement était perdu et la fenêtre masquée.)"""
    trous = []
    for n in ('GF', 'FF'):
        for o in MAQ['niveaux'][n]['ouvertures']:
            if o.get('facade') != face: continue
            x0, y0, x1, y1 = o['rect']; u0, u1 = (x0, x1) if face in 'SN' else (y0, y1)
            ep = (y1 - y0) if face in 'SN' else (x1 - x0)
            for za, zb in (o.get('empilement') or [[o['z_bas'], o['z_haut']]]):
                trous.append((u0, za, u1, zb, ep))
    g = box(a, z0, b, z1)
    for t in trous: g = g.difference(box(*t[:4]))
    for n in ('GF', 'FF'):                 # les auvents béton traversent le parement : il est découpé autour
        for c in MAQ['niveaux'][n].get('auvents', []):
            if c['facade'] != face: continue
            r = c['rect']; u0, u1 = (r[0], r[2]) if face in 'SN' else (r[1], r[3])
            g = g.difference(box(u0, c['z0'], u1, c['z1']))
    S.tag = 'env:parement'
    # décomposition en rectangles (u, z) sur la grille des sommets (trous compris)
    us = sorted({round(c[0], 4) for p in (g.geoms if hasattr(g, 'geoms') else [g]) for r in [p.exterior] + list(p.interiors) for c in r.coords})
    zs = sorted({round(c[1], 4) for p in (g.geoms if hasattr(g, 'geoms') else [g]) for r in [p.exterior] + list(p.interiors) for c in r.coords})
    def plaque(u0, za, u1, zb, d0=-e, d1=0.0):
        if face == 'S': S.boite(u0, d0, za, u1, d1, zb, mat, 'bat', poche=True)
        elif face == 'N': S.boite(u0, H - d1, za, u1, H - d0, zb, mat, 'bat', poche=True)
        elif face == 'E': S.boite(W - d1, u0, za, W - d0, u1, zb, mat, 'bat', poche=True)
        else: S.boite(d0, u0, za, d1, u1, zb, mat, 'bat', poche=True)
    for za, zb in zip(zs, zs[1:]):
        run = None
        for u0, u1 in zip(us, us[1:]):
            dedans = g.contains(box(u0, za, u1, zb).centroid)
            if dedans and run is None: run = u0
            if not dedans and run is not None: plaque(run, za, u0, zb); run = None
        if run is not None: plaque(run, za, us[-1], zb)
    for u0, za, u1, zb, ep in trous:          # retours dans les tableaux (demi-épaisseur du mur, côté extérieur)
        if not (a - 1e-6 <= u0 and u1 <= b + 1e-6 and z0 - 1e-6 <= za and zb <= z1 + 1e-6): continue
        for uu in (u0, u1):
            plaque(uu - (0 if uu == u0 else e), za, uu + (e if uu == u0 else 0), zb, 0.0, ep / 2)
        plaque(u0, za, u1, za + e, 0.0, ep / 2); plaque(u0, zb - e, u1, zb, 0.0, ep / 2)
    S.tag = 'env'


def site(S):
    St = MAQ['site']; B = S.boite
    c = St['parcelle']['contour']; px0, py0 = c[0]; px1, py1 = c[2]
    B(px0 - 25, py0 - 25, -0.06, px1 + 25, py1 + 25, -0.02, 'terrain', 'site')        # terrain naturel autour
    B(px0, py0, -0.02, px1, py1, 0.0, 'pelouse', 'site')                                 # jardin
    # rue au sud
    B(px0 - 24.9, py0 - 9.0, -0.05, px1 + 24.9, py0 - 2.5, -0.015, 'socle', 'site')      # rue (bouts en retrait du terrain)
    for k in ('parking', 'allee', 'voie_pietonne', 'parvis'):
        if St.get(k): r = St[k]['rect']; B(r[0], r[1], 0.0, r[2], r[3], 0.02, 'paves', 'site')
    for v in (St['parking'].get('vehicules', []) if S.zc is None else []):     # véhicules de calcul (Land Cruiser), vues complètes
        x0, y0, x1, y1 = v
        B(x0, y0, 0.32, x1, y1, 1.10, 'anthracite', 'site'); B(x0 + 0.10, y0 + 1.10, 1.10, x1 - 0.10, y1 - 1.05, 1.90, 'verre', 'site')
        for (wx, wy) in ((x0 + 0.02, y0 + 0.85), (x1 - 0.27, y0 + 0.85), (x0 + 0.02, y1 - 0.95), (x1 - 0.27, y1 - 0.95)):
            B(wx, wy - 0.38, 0.02, wx + 0.25, wy + 0.38, 0.70, 'noir', 'site')
    r = St['chemin_jardin']['rect']; n = int((r[2] - r[0]) / 0.75)
    for k in range(n):
        x = r[0] + k * (r[2] - r[0]) / n; B(x + 0.08, r[1] + 0.1, 0.0, x + (r[2] - r[0]) / n - 0.08, r[3] - 0.1, 0.03, 'paves', 'site')
    for j in St['jardinieres']:
        pts = j.get('contour') or [(j['rect'][0], j['rect'][1]), (j['rect'][2], j['rect'][1]), (j['rect'][2], j['rect'][3]), (j['rect'][0], j['rect'][3])]
        S.prisme(pts, 0.0, 0.45, 'socle', 'site'); S.prisme(pts, 0.45, 0.50, 'plante', 'site')
    d = St['deck']['contour']; zd = St['deck']['z']; S.prisme(d, 0.0, zd - 0.015, 'socle', 'site', poche=True); S.prisme(d, zd - 0.015, zd, 'sol_ext', 'sols')   # véranda + pavillon : antidérapant
    for m in St['marches']:                 # n contremarches égales, n - 1 girons, volumes disjoints (pas de faces confondues)
        r = m['rect']; n = m.get('n', 4)
        if m['montee'] == 'palier': B(r[0], r[1], 0.0, r[2], r[3], m['z'], 'beton', 'site'); continue
        h = m.get('hauteur', 0.15); g_ = n - 1; w = (r[2] - r[0]) / g_; l = (r[3] - r[1]) / g_
        for k in range(g_):                 # k = 0 : marche basse (côté opposé au palier)
            zt = h * (k + 1)
            if m['montee'] == 'ouest': B(r[2] - (k + 1) * w, r[1], 0.0, r[2] - k * w, r[3], zt, 'beton', 'site')
            elif m['montee'] == 'est': B(r[0] + k * w, r[1], 0.0, r[0] + (k + 1) * w, r[3], zt, 'beton', 'site')
            elif m['montee'] == 'nord': B(r[0], r[1] + k * l, 0.0, r[2], r[1] + (k + 1) * l, zt, 'beton', 'site')
            else: B(r[0], r[3] - (k + 1) * l, 0.0, r[2], r[3] - k * l, zt, 'beton', 'site')
    for gc in St.get('garde_corps_deck', []):           # garde-corps acier du bord de la véranda (barreaudage)
        (ax, ay), (bx, by) = gc['pts']; z0 = gc['z']
        B(ax - 0.02, min(ay, by), z0 + gc['h'] - 0.05, ax + 0.02, max(ay, by), z0 + gc['h'], 'anthracite', 'site')
        y = min(ay, by)
        while y < max(ay, by) - 0.05:
            B(ax - 0.01, y, z0, ax + 0.01, y + 0.02, z0 + gc['h'] - 0.05, 'anthracite', 'site'); y += 0.12
    if St.get('etendoir') and S.zc is None:             # étendoir : 2 poteaux + fils
        r = St['etendoir']['rect']; cx = (r[0] + r[2]) / 2
        for yy in (r[1], r[3] - 0.05): B(cx - 0.03, yy, 0.0, cx + 0.03, yy + 0.05, 1.80, 'inox', 'site')
        for dx in (-0.25, 0.0, 0.25): B(cx + dx - 0.005, r[1], 1.74, cx + dx + 0.005, r[3], 1.75, 'inox', 'site')
    # clôture : mur enduit 0.20, chaperon anthracite, lames bois côté rue, portail coulissant + portillon
    e = St['cloture']['epaisseur']; g = St['portail']['position']
    murs = [([px0 - e, py0 - e, g[0], py0], 2.10), ([g[2], py0 - e, px1 + e, py0], 2.10), ([px0 - e, py0, px0, py1 + e], 2.00),
            ([px1, py0, px1 + e, py1 + e], 2.00), ([px0, py1, px1, py1 + e], 2.00)]
    for i_, (r, h) in enumerate(murs):
        ex = -0.02 if i_ == 4 else 0.02         # chaperon du mur nord entre les chaperons est et ouest (pas de recouvrement)
        B(r[0], r[1], 0.0, r[2], r[3], h - 0.06, 'enduit', 'site', poche=True); B(r[0] - ex, r[1] - 0.02, h - 0.06, r[2] + ex, r[3] + 0.02, h, 'anthracite', 'site', poche=True)
    for r, h in murs[:2]:
        n = int((r[2] - r[0]) / 0.12)
        for k in range(n):
            x = r[0] + 0.03 + k * 0.12; B(x, r[1] - 0.04, 1.30, x + 0.06, r[1], 1.98, 'bois', 'site')
    B(g[0], py0 - 0.12, 0.02, g[2], py0 - 0.05, 2.10, 'anthracite', 'site', poche=True)
    for r_ in ((g[0] + 0.10, g[0] + 0.14, 0.05, 2.00), (g[0] + 0.96, g[0] + 1.00, 0.05, 2.00)):
        B(r_[0], py0 - 0.13, r_[2], r_[1], py0 - 0.12, r_[3], 'orange', 'site')
    B(g[0] + 0.10, py0 - 0.13, 1.96, g[0] + 1.00, py0 - 0.12, 2.00, 'orange', 'site'); B(g[0] + 0.10, py0 - 0.13, 0.05, g[0] + 1.00, py0 - 0.12, 0.09, 'orange', 'site')
    # arbres (schématiques) ; pas dans les vues coupées (ils masqueraient les pièces)
    for a in (St['arbres'] if S.zc is None else []):
        cx, cy = a['centre']; rr = a['diametre'] / 2
        S.cylindre(cx, cy, 0.12, 0.0, 2.6, 'meuble_bois', 'site'); S.sphere(cx, cy, 2.6 + rr * 0.8, rr, 'plante', 'site')


def construire(variante):
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    zc = {'complet': None, 'rdc': 0.60 + 1.70, 'etage': 4.00 + 1.70}[variante]
    S = m3.Scene3D(MAQ, zcoupe=zc)
    S.niveaux({'GF': 3.80, 'FF': 7.20})
    S.murs('GF'); S.murs('FF')
    S.sols('GF'); S.sols('FF', tremies=TREMIE_FF)
    S.revetements('GF', 3.80); S.revetements('FF', 7.20)
    S.mobilier('GF'); S.mobilier('FF')
    enveloppe(S); site(S)
    S.construire()
    return S


def eclairage_interieur(S):
    """Une source surfacique au plafond de chaque pièce (vues intérieures)."""
    for n, M in (('GF', G), ('FF', F)):
        for p in M['pieces']:
            if not p.get('nom') or 'TERRACE' in p['nom']: continue
            P = Polygon(p['contour']); c = P.representative_point(); a = P.area
            l = bpy.data.lights.new('L_' + p['nom'], 'AREA'); l.energy = 9 * a; l.size = max(0.8, math.sqrt(a) * 0.6)
            o = bpy.data.objects.new('L_' + p['nom'], l); bpy.context.scene.collection.objects.link(o)
            o.location = (c.x, c.y, M['z'] + 3.0 if n == 'GF' else M['z'] + 3.05)


# --------------------------------------------------------------------------------------------- vues
CENTRE = (6.55, 4.5, 2.0)


def cam_axo(azimut, elev, cible, echelle, dist=60):
    a = math.radians(azimut); e = math.radians(elev)
    pos = (cible[0] + dist * math.cos(e) * math.sin(a), cible[1] - dist * math.cos(e) * math.cos(a), cible[2] + dist * math.sin(e))
    return m3.camera(pos, cible, ortho=echelle)


def vues_interieures():
    """Une vue par pièce, depuis la porte principale (comme un visiteur qui entre) vers le fond de la pièce."""
    V = {}
    for n, M in (('GF', G), ('FF', F)):
        for p in M['pieces']:
            nom = p.get('nom')
            if not nom or nom in ('LINEN',): continue
            P = Polygon(p['contour'])
            portes = []
            for o in M['ouvertures']:
                if o['type'] in ('fenetre',): continue
                g = box(*o['rect'])
                if g.buffer(0.10).intersects(P):
                    ext = o.get('facade') is not None
                    prio = (0 if (ext and 'ENTRANCE' in nom) else 1 if o['type'] == 'porte' else 2 if o['type'] in ('porte_coulissante', 'passage') else 3 if not ext else 4)
                    # porte principale = celle qui vient d'une circulation, pas d'une salle d'eau / dressing / WC (vérificateur 4)
                    autres = [q.get('nom') or '' for q in M['pieces'] if q is not p and Polygon(q['contour']).intersects(g.buffer(0.10))]
                    if any(re.search(r'BATH|EN-SUITE|^WC|DRESSING|CLOSET|SHOWER', a_) for a_ in autres): prio += 5
                    if not autres and not ext: prio += 10      # (5e passage, M3D-028) porte intérieure à la pièce (cabinet WC, placard) : jamais
                    portes.append((prio, o))
            if not portes: continue
            portes.sort(key=lambda t: t[0]); o = portes[0][1]
            x0, y0, x1, y1 = o['rect']; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            # entrer de 0.45 dans la pièce, perpendiculairement au mur de l'ouverture
            cand = [(cx, cy + 0.85), (cx, cy - 0.85)] if o['axe'] == 'x' else [(cx + 0.85, cy), (cx - 0.85, cy)]
            if not any(P.contains(Point(q)) for q in cand):
                cand = [(cx, cy + 0.45), (cx, cy - 0.45)] if o['axe'] == 'x' else [(cx + 0.45, cy), (cx - 0.45, cy)]
            pos = next((q for q in cand if P.contains(Point(q))), None)
            if pos is None: continue
            # cible : point de la pièce le plus éloigné de la caméra (fond de la pièce)
            loin = max(list(P.exterior.coords), key=lambda q: math.dist(q, pos))
            cent = P.centroid
            cib = (0.5 * loin[0] + 0.5 * cent.x, 0.5 * loin[1] + 0.5 * cent.y)
            z = M['z']
            LEGENDES = {'LANDING': 'from the west end of the landing', 'ROOF TERRACE': 'from door D13', 'KITCHEN / DINING': 'from the hall sliding door D18',
                        'LIVING ROOM': 'from the hall opening'}
            EXPLICITES = {'LANDING': ((4.75, 7.30), (12.0, 7.7)), 'ROOF TERRACE': ((6.95, 5.00), (12.5, 1.2)),
                          'KITCHEN / DINING': ((8.55, 10.05), (12.2, 13.6)), 'LIVING ROOM': ((6.2, 4.0), (12.5, 0.8))}
            depuis = 'from door %s' % o.get('repere') if o['type'] != 'passage' else 'from the opening to the next room'
            if nom in EXPLICITES: pos, cib = EXPLICITES[nom]; depuis = LEGENDES.get(nom, 'view across the room')
            foc = 14 if P.area < 8 else (16 if P.area < 20 else 18)
            zc = 1.20
            if P.area < 3.0:            # petite pièce (WC) : caméra dans l'embrasure, grand angle, visée basse (M3D-025)
                pos = (cx, cy); foc = 11; zc = 0.80
                loin = max(list(P.exterior.coords), key=lambda q: math.dist(q, pos)); cib = (0.6 * loin[0] + 0.4 * P.centroid.x, 0.6 * loin[1] + 0.4 * P.centroid.y)
            V['int_' + re.sub(r'[^a-z0-9]+', '_', nom.lower()).strip('_') + ('_' + n.lower() if nom == 'WC' else '')] = {
                'variante': 'complet', 'nom': nom, 'niveau': n, 'pos': (pos[0], pos[1], z + 1.60), 'cible': (cib[0], cib[1], z + zc), 'focale': foc, 'expo': 1.7 if 'TERRACE' in nom else 0.0,
                'porte': depuis}
    return V


VUES = {
    'ensemble_se': {'variante': 'complet', 'axo': (35, 32, (7.5, 3.5, 3.2), 40), 'titre': 'Overall view from the street (south-east), with boundary wall and gate'},
    'ensemble_no': {'variante': 'complet', 'axo': (215, 32, (7.5, 5.0, 3.2), 40), 'titre': 'Overall view from the rear (north-west)'},
    'axo_rdc': {'variante': 'rdc', 'axo': (35, 42, (6.6, 5.6, 0.6), 29.5), 'titre': 'Ground floor - 3D cut at 1.70 above floor level', 'niveau': 'GF'},
    'axo_etage': {'variante': 'etage', 'axo': (35, 42, (6.6, 6.6, 4.0), 25.5), 'titre': 'First floor - 3D cut at 1.70 above floor level', 'niveau': 'FF'},
    # (retour client 15/10, repris de la première version du projet : mêmes angles de vue, même repère)
    'ext_rue': {'variante': 'complet', 'ext': True, 'pos': (17.0, -15.5, 1.7), 'cible': (8.0, 4.0, 3.6), 'focale': 17, 'titre': 'Street view along the boundary wall'},
    'ext_aerien': {'variante': 'complet', 'ext': True, 'pos': (-6.0, -10.0, 15.0), 'cible': (11.5, 11.0, 2.5), 'focale': 24, 'titre': 'Aerial view'},
    'ext_pavillon': {'variante': 'complet', 'ext': True, 'pos': (6.0, -6.15, 1.6), 'cible': (11.0, -1.0, 1.8), 'focale': 18, 'titre': 'Veranda and pergola'},
    'ext_entree': {'variante': 'complet', 'ext': True, 'pos': (19.8, 1.8, 1.6), 'cible': (13.3, 3.2, 2.2), 'focale': 22, 'titre': 'Entrance door'},
    'ext_jardin': {'variante': 'complet', 'ext': True, 'pos': (19.9, 4.0, 1.7), 'cible': (9.0, 11.0, 3.2), 'focale': 15, 'titre': 'Garden and rear'},
}


def rendre(nom, v, S, L=2000, Hh=1180, ech=24):
    for o in [o for o in bpy.data.objects if o.type in ('CAMERA', 'LIGHT')]: bpy.data.objects.remove(o)
    if os.environ.get('APERCU'): L, Hh, ech = 640, 360, 6        # aperçu rapide de cadrage (client 15/10) : valider avant le rendu final
    m3.regler_rendu(L, Hh, ech, True, 1.1 if 'axo' in v else 1.3)
    if 'axo' in v:
        az, el, cib, ech_ = v['axo']; cam = cam_axo(az, el, cib, ech_); m3.soleil(az + 40, 55, 2.6)
    else:
        cam = m3.camera(v['pos'], v['cible'], focale=v['focale'])
        if v.get('ext'): m3.soleil(130, 50, 2.6)                          # vue extérieure : plein jour, pas d'éclairage intérieur
        else: m3.soleil(130, 50, 1.5); eclairage_interieur(S)
        bpy.context.scene.world.node_tree.nodes['Background'].inputs[1].default_value = 1.0 if v.get('ext') else 0.35
        try: bpy.context.scene.view_settings.view_transform = 'AgX'
        except Exception: pass
        bpy.context.scene.view_settings.exposure = v.get('expo', 0.0)      # vue extérieure sous pergola : +1.7 (M3D-024, luminance mesurée 116 à +1 pour une médiane de 176)
    sc = bpy.context.scene; sc.render.filepath = os.path.join(OUT, nom + '.png')
    bpy.ops.render.render(write_still=True)
    et = []
    if v.get('niveau') and 'axo' in v:
        pts = [(t, p) for t, p, n in S.etiquettes if n == v['niveau']]
        proj = m3.projeter(cam, [p for t, p in pts])
        et = [{'texte': t, 'x': q[0], 'y': q[1]} for (t, p), q in zip(pts, proj) if q]
    json.dump({'vue': nom, 'titre': v.get('titre') or v.get('nom'), 'etiquettes': et, 'porte': v.get('porte'), 'empreinte': EMPREINTE,
               'niveau': v.get('niveau'), 'pos': v.get('pos'), 'cible': v.get('cible'), 'focale': v.get('focale'), 'axo': v.get('axo')},
              open(os.path.join(OUT, nom + '.json'), 'w'), indent=1)
    print('rendu', nom, flush=True)


if __name__ == '__main__':
    variante = sys.argv[1]; demandees = sys.argv[2:]
    toutes = dict(VUES); toutes.update(vues_interieures())
    choix = {k: v for k, v in toutes.items() if v['variante'] == variante and (not demandees or k in demandees)}
    S = construire(variante)
    import verif_3d as v3
    if variante == 'complet':
        # caméras : si un meuble masque un bord de l'image (M3D-009) ou si la caméra est dans un objet, avancer de 0.30
        T, info = v3._bvh(S)
        for k, v in choix.items():
            for _ in range(4):
                if not v3.cameras(S, T, info, {k: v}): break
                p, c = v['pos'], v['cible']; d = math.dist(p[:2], c[:2]) or 1
                v['pos'] = (p[0] + 0.30 * (c[0] - p[0]) / d, p[1] + 0.30 * (c[1] - p[1]) / d, p[2])
        R = v3.verifier(S, {k: v for k, v in choix.items()})
        json.dump(R, open(os.path.join(OUT, 'verif_3d.json'), 'w'), indent=1, ensure_ascii=False)
        nb = [c for c in R if c['gravite'] == 'B']
        print('VERIF_3D', len(R), 'constat(s) dont', len(nb), 'bloquant(s)', flush=True)
        for c in R: print('  ', c['regle'], c['gravite'], c['texte'], flush=True)
    for k, v in choix.items():
        rendre(k, v, S, *( (900, 530, 8) if os.environ.get('APERCU') else (1800, 1060, 16)))
    open(os.path.join(OUT, '%s_done.txt' % variante), 'w').write('\n'.join(choix))
