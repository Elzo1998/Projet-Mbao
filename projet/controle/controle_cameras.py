"""YAMA HOUSE - FICHIER DE CONTRÔLE (pour l'ingénieur) : position et direction de chaque caméra des vues 3D.

python3 -I projet/controle/controle_cameras.py  ->  projet/controle/YAMA_Controle_Cameras_revC.pdf (RDC + site, étage)

Données : la caméra réellement utilisée par chaque rendu (position, cible, focale, après recalage automatique), écrite
par rendre_3d.py dans rendus/<vue>.json ; numéros = ceux des planches 3D (vues3d/index_planches.json).
Usage : l'ingénieur annote ce PDF (caméras à ajouter, déplacer, supprimer) et le renvoie.
"""
import json, math, os, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'projet', 'esquisse')); sys.path.insert(0, '/home/user/atelier-archi-ingenierie/outils')
import dessiner_plans as dpl
import dessin_plan as dp
import sys as _s, os as _o; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))), 'esquisse')); from indice import REV, REVISIONS
R = os.path.join(ROOT, 'projet', 'vues3d', 'rendus')
IDX = json.load(open(os.path.join(ROOT, 'projet', 'vues3d', 'index_planches.json')))
COUL_INT, COUL_EXT = (0.85, 0.15, 0.10), (0.10, 0.35, 0.80)


def cameras():
    out = []
    for f in sorted(glob.glob(os.path.join(R, '*.json'))):
        m = json.load(open(f))
        if not isinstance(m, dict) or 'vue' not in m: continue
        out.append(m)
    return out


def niveau_de(m):
    if m.get('niveau'): return m['niveau']
    if m['vue'].startswith('ext_'): return 'GF'                  # vues extérieures : toutes sur le plan du RDC + site
    if m.get('pos'): return 'FF' if m['pos'][2] > 3.5 and not m.get('axo') else 'GF'
    return 'GF'


def dessiner_interieure(D, m, num, cadre=None):
    (x, y, z), (tx, ty, tz) = m['pos'], m['cible']
    COUL_INT = COUL_EXT if m['vue'].startswith('ext_') else globals()['COUL_INT']
    if cadre and not (cadre[0] + 0.6 < x < cadre[2] - 0.6 and cadre[1] + 0.6 < y < cadre[3] - 3.0):
        # caméra hors du cadre (ex. rue : trottoir d'en face) : ramenée au bord le plus proche, vraies coordonnées écrites
        reel = (x, y)
        x = min(max(x, cadre[0] + 0.7), cadre[2] - 0.7); y = min(max(y, cadre[1] + 0.7), cadre[3] - 3.1)
        D.texte((x + 2.4 if x < (cadre[0] + cadre[2]) / 2 else x - 2.4, y + (0.6 if y < (cadre[1] + cadre[3]) / 2 else -0.6)), 'cam. %.2f, %.2f (out of frame)' % reel, 0.16, 'A-CTRL', False, coul=COUL_INT)
    f = m.get('focale') or 18; hfov = 2 * math.atan(18.0 / f); a = math.atan2(ty - y, tx - x); L = 2.6
    p1 = (x + L * math.cos(a - hfov / 2), y + L * math.sin(a - hfov / 2)); p2 = (x + L * math.cos(a + hfov / 2), y + L * math.sin(a + hfov / 2))
    D.poly([(x, y), p1, p2], 'A-CTRL', 0.4, COUL_INT, fond=COUL_INT, alpha=0.18)
    D.ligne((x, y), (x + 1.2 * math.cos(a), y + 1.2 * math.sin(a)), 'A-CTRL', 0.8, COUL_INT)
    D.cercle((x, y), 0.12, 'A-CTRL', 0.5, (0, 0, 0), fond=COUL_INT)
    lx, ly = x - 0.45 * math.cos(a), y - 0.45 * math.sin(a)
    D.texte((lx, ly), num.replace('3D-', ''), 0.20, 'A-CTRL', True, coul=COUL_INT)


def dessiner_axo(D, m, num, emprise, cadre=None):
    az, el, cib, ech = m['axo']; a = math.radians(az)
    dx, dy = math.sin(a), -math.cos(a)                        # direction caméra -> cible inversée (cam_axo)
    cx, cy = (emprise[0] + emprise[2]) / 2, (emprise[1] + emprise[3]) / 2
    r = 12.5 if 'ensemble' in m['vue'] else 10.5
    px, py = cx + r * dx, cy + r * dy
    if cadre:                                   # repère gardé dans le cadre, sous la bande du titre de vue (DOC-042)
        px = min(max(px, cadre[0] + 1.2), cadre[2] - 1.2); py = min(max(py, cadre[1] + 1.2), cadre[3] - 3.0)
    D.ligne((px, py), (px - 2.6 * dx, py - 2.6 * dy), 'A-CTRL', 1.6, COUL_EXT)
    for s_ in (-0.45, 0.45):
        ang = math.atan2(-dy, -dx) + s_
        D.ligne((px - 2.6 * dx, py - 2.6 * dy), (px - 2.6 * dx - 0.5 * math.cos(ang), py - 2.6 * dy - 0.5 * math.sin(ang)), 'A-CTRL', 1.6, COUL_EXT)
    D.cercle((px, py), 0.40, 'A-CTRL', 0.8, COUL_EXT, fond=(1, 1, 1)); D.texte((px, py), num.replace('3D-', ''), 0.22, 'A-CTRL', True, coul=COUL_EXT)


def planche(niv, titre, numero):
    D, cadre_m = dpl.construire_dessin(niv)
    lignes = []
    for m in sorted(cameras(), key=lambda m: IDX.get(m['vue'], 'zz')):
        num = IDX.get(m['vue'])
        if not num: continue
        if m.get('axo'):
            if (m['vue'].startswith('ensemble') and niv == 'GF') or (m['vue'] == 'axo_rdc' and niv == 'GF') or (m['vue'] == 'axo_etage' and niv == 'FF'):
                dessiner_axo(D, m, num, dpl.MAQ['emprise'], cadre_m)
                lignes.append(('%s  %s (axonometric, %s)' % (num, (m.get('titre') or m['vue']), 'azimuth %d' % m['axo'][0]), ''))
        elif m.get('pos') and niveau_de(m) == niv:
            dessiner_interieure(D, m, num, cadre_m)
            lignes.append(('%s  %s - %s' % (num, (m.get('titre') or '').title().replace('Wc', 'WC'), m.get('porte') or ''), ''))
    legende = {'titre_vue': titre, 'sous_titre_vue': 'CONTROL FILE - 3D camera positions - not for issue', 'numero_vue': numero,
               'blocs': [{'titre': 'CAMERAS (number = 3D sheet number)', 'lignes': lignes},
                         {'titre': 'HOW TO USE', 'lignes': [(t, '') for t in (
                             'Red: interior view (eye height 1.60), cone = field', '   of view ; blue: exterior / overall / axonometric view.',
                             'Mark on this sheet: cameras to add (point + arrow),', '   to move, or to delete ; send it back.')]}],
               'symboles': []}
    carto = dict(dpl.CARTO, vue='CONTROL', planche='CTRL - C%s' % numero, sous_titre='3D camera positions', phase='CONTROL FILE')
    sortie = os.path.join(HERE, '_cam_%s.pdf' % niv)
    dp.rendre_pdf(D, sortie, {'pt': (16, 40, 745, 822), 'm': cadre_m}, carto, legende)
    return sortie


REG = os.path.join(ROOT, 'projet', 'vues3d', 'cameras')


def euler_blender(pos, cible):
    """Rotation XYZ (degrés) d'une caméra Blender placée en pos et visant cible (la caméra regarde son -Z local)."""
    dx, dy, dz = (c - p for c, p in zip(cible, pos))
    return (round(90 + math.degrees(math.atan2(dz, math.hypot(dx, dy))), 2), 0.0, round(math.degrees(math.atan2(-dx, dy)), 2))


assert euler_blender((0, 0, 0), (0, 1, 0)) == (90.0, 0.0, 0.0) and euler_blender((0, 0, 0), (1, 0, 0))[2] == -90.0


def registre(pdf):
    """Registre interne des caméras (jamais remis au client) : cameras.json + CAMERAS.md + plans PNG, pour retrouver
    les cadrages validés d'une session à l'autre et les poser directement dans Blender."""
    import pymupdf
    os.makedirs(REG, exist_ok=True)
    cams = []
    for m in cameras():
        c = {k: m.get(k) for k in ('vue', 'titre', 'pos', 'cible', 'focale', 'axo')}
        c['niveau'] = 'EXT' if m['vue'].startswith('ext_') else niveau_de(m); c['planche'] = IDX.get(m['vue'])
        if m.get('axo'):  # même calcul que rendre_3d.cam_axo : caméra orthographique à 60 m de la cible
            az, el, cib, ech = m['axo']; a, e = math.radians(az), math.radians(el)
            pos = [round(cib[0] + 60 * math.cos(e) * math.sin(a), 3), round(cib[1] - 60 * math.cos(e) * math.cos(a), 3), round(cib[2] + 60 * math.sin(e), 3)]
            c['blender'] = {'type': 'ORTHO', 'location': pos, 'rotation_euler_deg': euler_blender(pos, cib), 'ortho_scale': ech}
        if m.get('pos'): c['blender'] = {'location': m['pos'], 'rotation_euler_deg': euler_blender(m['pos'], m['cible']),
                                         'lens_mm': m['focale'], 'sensor_width_mm': 36, 'sensor_fit': 'AUTO'}
        cams.append(c)
    json.dump({'source': 'vues3d/rendus/<vue>.json (caméra réellement rendue)', 'repere': 'coordonnées de la maquette '
               '(m) = monde Blender ; z = 0 au sol fini du RDC', 'cameras': cams}, open(os.path.join(REG, 'cameras.json'), 'w'), indent=1)
    doc = pymupdf.open(pdf)
    for i, niv in enumerate(('GF', 'FF')): doc[i].get_pixmap(dpi=110).save(os.path.join(REG, 'plan_cameras_%s.png' % niv))
    L = ['# Registre des caméras 3D - YAMA HOUSE (fichier interne, jamais dans le PDF client)', '',
         'Généré par `controle/controle_cameras.py` à partir des caméras réellement rendues. Plans : `plan_cameras_GF.png`, '
         '`plan_cameras_FF.png`. Données complètes et réglages Blender : `cameras.json`.', '',
         'Repère : coordonnées de la maquette en mètres = monde Blender (z = 0 au sol fini du RDC). Caméra Blender : '
         'location = pos, rotation XYZ ci-dessous, objectif = focale (capteur 36, ajustement AUTO).',
         'Modifier un cadrage : `vues3d/rendre_3d.py` (dictionnaire des vues ext ; vues intérieures calculées par '
         '`vues_interieures()`), tester avec `APERCU=1`, rendre, puis relancer ce script.', '',
         '| Vue | Niveau | Position x, y, z | Cible x, y, z | Focale | Rotation Blender X, Y, Z | Titre |', '|---|---|---|---|---|---|---|']
    f = lambda v: ', '.join('%.2f' % a for a in v)
    for c in cams:
        if c.get('pos'): L.append('| %s | %s | %s | %s | %s | %s | %s |' % (c['vue'], c['niveau'], f(c['pos']), f(c['cible']), c['focale'],
                                                                              f(c['blender']['rotation_euler_deg']), c['titre']))
        else: L.append('| %s | %s | %s (ortho) | %s | échelle ortho %s | %s | %s |' % (c['vue'], c['niveau'], f(c['blender']['location']), f(c['axo'][2]),
                                                                                 c['axo'][3], f(c['blender']['rotation_euler_deg']), c['titre']))
    open(os.path.join(REG, 'CAMERAS.md'), 'w').write('\n'.join(L) + '\n')
    return len(cams)


if __name__ == '__main__':
    import pymupdf
    out = pymupdf.open()
    for niv, titre, num in (('GF', '3D cameras - Ground floor + site', '1'), ('FF', '3D cameras - First floor', '2')):
        f = planche(niv, titre, num); out.insert_pdf(pymupdf.open(f)); os.remove(f)
    out.save(os.path.join(HERE, f'YAMA_Controle_Cameras_rev{REV}.pdf'), garbage=4, deflate=True)
    print('ok', len(out), 'pages ; registre :', registre(os.path.join(HERE, f'YAMA_Controle_Cameras_rev{REV}.pdf')), 'caméras')
