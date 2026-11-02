"""MBAO - R+1 : suite parentale, 3 propositions (indice B) en IMAGES, retours client du 02/11 sur la proposition A.

python3 -I projet/esquisse/suite_parentale_r1_v2.py  ->  projet/esquisse/apercus/MBAO_R1_P1.png, _P2.png, _P3.png + contrôles chiffrés

Parcours imposé : chambre -> dressing -> salle de bain (une seule porte depuis la chambre). Le dressing et la salle de bain ont chacun
une fenêtre sur la façade (lumière et ventilation naturelles). Repère et géométrie : voir suite_parentale_r1.py.
"""
import math, os, sys
from shapely.geometry import box, Point, Polygon
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import suite_parentale_r1 as B           # géométrie de base, primitives de dessin
from suite_parentale_r1 import W, D, GRIS, NOIR, ROUGE, BLEU, rect, porte, meuble, etiquette

SX = 5.85                                                   # face intérieure ouest de la salle de bain
N_UNITS = 0.60                                              # profondeur des penderies
BANDE = 0.15


def pie(c, r, a0, a1, n=24):
    return Polygon([c] + [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)])


def variante(num):
    """Géométrie d'une proposition. num 1 : fenêtre 1.00 + coiffeuse ; 2 : porte vitrée 0.90 sur le balcon ; 3 : îlot 1.20 + fenêtre bandeau 1.40."""
    sy = 1.83 if num == 3 else 2.03                         # profondeur intérieure de la salle de bain
    y0 = sy + BANDE                                         # début du corps du dressing
    prof = D - y0                                           # profondeur du corps du dressing
    idep = 1.20 if num == 3 else 1.00                       # largeur (profondeur) de l'îlot
    ay = (prof - N_UNITS - idep) / 2                        # allées nord et sud
    v = dict(num=num, sy=sy, y0=y0, idep=idep)
    v['ilot'] = ('Îlot %.2f x 1.60' % idep, 5.11, y0 + ay, 1.60, idep)
    v['pend_n'] = ('Penderie', 4.21, D - N_UNITS, W - 4.21, N_UNITS)
    v['pend_e'] = ('Penderie', 7.67, y0, N_UNITS, D - N_UNITS - y0)
    # salle de bain : douche SE, WC suspendu au mur est, meuble vasque suspendu au mur ouest
    wcy = sy - 0.43 if num == 3 else 1.55
    v['douche'] = ('Douche 1.00 x 1.00', 7.27, 0.0, 1.00, 1.00)
    v['wc'] = ('WC susp.', 7.72, wcy - 0.18, 0.55, 0.36)
    v['vasque'] = ('Vasque susp.', SX, 0.25, 0.45, 0.80)
    # portes : (charnière, largeur, arc0, arc1, ouvert_vers)
    v['porte_sdb'] = ((6.80, y0), 0.80, 90, 180, 90)
    v['porte_nw'] = ((0.15, D), 0.90, 270, 360, 270)
    if num == 1:
        v['porte_dr'] = ((4.21, 3.80), 0.80, 270, 360, 0); v['tv'] = ('Meuble TV', 3.66, 3.95, 0.40, 1.00)
        v['coiff'] = ('Coiffeuse 1.10', 4.30, 0.0, 1.10, 0.50); v['fen_dr'] = (4.35, 5.35, 'Fenêtre 1.00 x 1.40, allège 0.90'); v['extra'] = [v['coiff']]
    if num == 2:
        v['porte_dr'] = ((4.21, 2.25), 0.80, 270, 360, 0); v['tv'] = ('Meuble TV', 3.66, 2.80, 0.40, 1.40)
        v['porte_balcon'] = ((5.41, 0.0), 0.90, 90, 180, 90); v['fen_dr'] = (4.51, 5.41, 'Porte vitrée 0.90 (1 vantail) sur balcon'); v['extra'] = []
        v['banc'] = ('Banc', 4.21, 2.30 - 0.0, 0.0, 0.0)    # pas de banc : place libre devant le vantail
    if num == 3:
        v['porte_dr'] = ((4.21, 4.95), 0.80, 270, 360, 0); v['tv'] = ('Meuble TV', 3.66, 2.55, 0.40, 1.40)
        v['bas'] = ('Meuble bas 1.45 x 0.50', 4.21, 0.0, 1.45, 0.50); v['fen_dr'] = (4.25, 5.65, 'Fenêtre 1.40 x 1.00, allège 1.10'); v['extra'] = [v['bas']]
    v['lit'] = ('Lit 1.80 x 2.00', 0.0, 2.05, 2.10, 1.80)
    v['chev'] = [('Chevet', 0.0, 1.55, 0.45, 0.45), ('Chevet', 0.0, 3.90, 0.45, 0.45)]
    v['faut'] = ('Fauteuil', 0.35, 0.25, 0.80, 0.80)
    return v


def R(m): return box(m[1], m[2], m[1] + m[3], m[2] + m[4])


def controles(v):
    L = []
    def t(rid, nom, val, mini): L.append((rid, nom, round(val, 2), mini, val >= mini - 1e-9))
    il, pn, pe = R(v['ilot']), R(v['pend_n']), R(v['pend_e'])
    t('CLIENT', 'Îlot : largeur (profondeur) >= 1.00 (idéal 1.20)', v['idep'], 1.00)
    t('CIR-013', 'Dressing : allée îlot / penderie nord', il.distance(pn), 0.90)
    t('CIR-013', 'Dressing : allée îlot / penderie est', il.distance(pe), 0.90)
    t('CIR-013', 'Dressing : allée îlot / mur ouest', il.distance(box(4.06, v['y0'], 4.21, D)), 0.90)
    t('CIR-013', 'Dressing : allée îlot / cloison de la salle de bain', il.distance(box(SX - 0.15, v['sy'], W, v['y0'])), 0.90)
    # salle de bain
    do, wc, va = R(v['douche']), R(v['wc']), R(v['vasque'])
    t('SDE-005', 'Douche >= 0.90 x 0.90 (1.00 x 1.00)', min(v['douche'][3], v['douche'][4]), 0.90)
    t('SDE-007', 'WC : axe à >= 0.40 du mur nord', v['sy'] - (v['wc'][2] + 0.18), 0.40)
    t('SDE-007', 'WC : axe à >= 0.40 de la douche', (v['wc'][2] + 0.18) - 1.00, 0.40)
    t('CIR-018', 'WC : libre devant la cuvette >= 0.60', wc.distance(va), 0.60)
    t('CIR-019', 'Meuble vasque : libre devant >= 0.70', va.distance(box(7.27, 0, 7.28, 1.0)), 0.70)
    t('CIR-020', 'Douche : approche libre >= 0.70', do.distance(va), 0.70)
    # portes : le débattement ne touche aucun meuble
    for nom, cle, obst in (('Porte SDB', 'porte_sdb', [il, pe, wc, do, va]), ('Porte chambre -> dressing', 'porte_dr', [il, pe, pn] + [R(m) for m in v['extra']]),
                           ('Porte NO', 'porte_nw', [R(v['lit'])] + [R(m) for m in v['chev']])):
        (c, r, a0, a1, _) = v[cle]; p = pie(c, r, a0, a1)
        t('CIR-030', nom + ' : débattement libre (distance au meuble le plus proche)', min(-p.intersection(o).area if p.intersection(o).area > 1e-6 else p.distance(o) for o in obst), 0.0)
    if 'porte_balcon' in v:
        (c, r, a0, a1, _) = v['porte_balcon']; p = pie(c, r, a0, a1); t('CIR-016', 'Porte vitrée : débattement libre', min(-p.intersection(o).area if p.intersection(o).area > 1e-6 else p.distance(o) for o in [il, pn]), 0.0)
    # chambre
    lit = R(v['lit']); chn = R(v['chev'][1])
    t('CIR-004', 'Chambre : côté sud du lit / fauteuil', lit.distance(R(v['faut'])), 0.60)
    t('CIR-004', 'Chambre : côté nord (chevet compris) / mur nord', lit.union(chn).distance(box(0, D, 4.06, D + 0.1)), 0.70)
    t('CIR-005', 'Chambre : pied du lit / meuble TV', lit.distance(R(v['tv'])), 0.70)
    t('NAT', 'Lumière et air naturels : fenêtre du dressing (largeur >= 0.90)', v['fen_dr'][1] - v['fen_dr'][0], 0.90)
    t('NAT', 'Lumière et air naturels : fenêtre de la salle de bain existante (1.00)', 1.00, 0.60)
    return L


def dessiner(v):
    fig, ax = plt.subplots(figsize=(11, 8.6))
    num, sy, y0 = v['num'], v['sy'], v['y0']
    # structure et enveloppe (inchangées) : murs extérieurs, poteaux, cloison centrale, balcon
    for m in B.MURS_EXT: rect(ax, m, GRIS, NOIR, 1.0, z=3)
    for n, m in B.POTEAUX.items(): rect(ax, m, NOIR, NOIR, 0.5, z=4)
    ax.add_patch(Rectangle((1.38, -1.40), 5.57, 1.25, fc='#f2f2f2', ec=NOIR, lw=0.6, zorder=1)); ax.text(4.1, -0.78, 'BALCON (inchangé)', ha='center', fontsize=7, color='#555')
    ax.add_patch(Rectangle((B.PORTE_NO[0], D), B.PORTE_NO[1] - B.PORTE_NO[0], 0.15, fc='white', ec='none', zorder=4))      # porte NO
    ax.add_patch(Rectangle((B.PORTE_NE[0], D), B.PORTE_NE[1] - B.PORTE_NE[0], 0.15, fc='#f4c0c0', ec=ROUGE, lw=0.8, zorder=4))   # porte NE fermée
    # façade : baie ouest inchangée, fenêtre SDB inchangée, ouverture du dressing modifiée
    x0, x1, txt = v['fen_dr']
    for a, b, col in ((B.BAIES[0][0], B.BAIES[0][1], BLEU), (7.07, 8.07, BLEU), (4.245, 5.865, '#cccccc')):
        ax.add_patch(Rectangle((a, -0.15), b - a, 0.15, fc='white', ec='none', zorder=4)); ax.plot([a, b], [-0.075, -0.075], color=col, lw=1.6, zorder=5)
    ax.add_patch(Rectangle((4.245, -0.15), 1.62, 0.15, fc=GRIS, ec='none', zorder=4.5)); ax.add_patch(Rectangle((x0, -0.15), x1 - x0, 0.15, fc='white', ec='none', zorder=4.6))
    ax.plot([x0, x1], [-0.075, -0.075], color=ROUGE, lw=2.2, zorder=5)
    ax.text((x0 + x1) / 2, -0.30, txt, ha='center', fontsize=6.3, color=ROUGE, zorder=8)
    # cloison centrale conservée avec son percement
    py0, py1 = v['porte_dr'][0][1] - 0.80 if num != 2 else 1.45, v['porte_dr'][0][1] if num != 2 else 2.25
    rect(ax, (4.06, 0, 0.15, py0), GRIS, NOIR, 1.0, z=3); rect(ax, (4.06, py1, 0.15, D - py1), GRIS, NOIR, 1.0, z=3)
    for c in (B.DEMOL[:3] + B.DEMOL[3:] if num != 3 else [B.DEMOL[0], B.DEMOL[1], B.DEMOL[3]]): rect(ax, c, '#f8e0e0', ROUGE, 0.8, hatch='////', z=3, ls=(0, (3, 2)))
    rect(ax, (SX - 0.15, 0, 0.15, y0), '#cfe0ff', BLEU, 1.0, z=3); rect(ax, (SX - 0.15, sy, 6.00 - SX + 0.15, BANDE), '#cfe0ff', BLEU, 1.0, z=3); rect(ax, (6.80, sy, W - 6.80, BANDE), GRIS if num == 3 else '#cfe0ff', NOIR if num == 3 else BLEU, 1.0, z=3)   # salle de bain neuve, ouverture de porte 6.00-6.80
    # mobilier
    for k in ('ilot', 'pend_n', 'pend_e', 'douche', 'wc', 'vasque', 'lit', 'faut', 'tv'): meuble(ax, v[k], fs=5.2)
    for m in v['chev'] + v['extra']: meuble(ax, m, fs=5.0)
    for k in ('porte_sdb', 'porte_dr', 'porte_nw', 'porte_balcon'):
        if k in v: porte(ax, *v[k])
    # étiquettes
    surf_dr = box(4.21, y0, W, D).area + box(4.21, 0, SX - 0.15, sy).area
    etiquette(ax, 2.55, 4.7, 'CHAMBRE', 4.06 * D, fs=9); etiquette(ax, 7.0, 3.15 + (0.0 if num != 3 else 0.0), '', None)
    etiquette(ax, 6.1, D - N_UNITS - 0.50, 'WALK-IN DRESSING', surf_dr, fs=8)
    etiquette(ax, 6.55, 1.30 if num != 3 else 1.25, 'SDB', (W - SX) * sy, fs=8)
    ax.set_aspect('equal'); ax.set_xlim(-0.6, W + 0.6); ax.set_ylim(-1.7, D + 1.4); ax.axis('off')
    titres = {1: 'PROPOSITION 1 - fenêtre 1.00 + coiffeuse dans l\'alcôve lumineuse du dressing',
              2: 'PROPOSITION 2 - porte vitrée 0.90 (1 vantail) : le dressing ouvre sur le balcon',
              3: 'PROPOSITION 3 - îlot 1.20 et fenêtre bandeau 1.40 sur meuble bas'}
    ax.text(-0.5, D + 1.30, 'MBAO - R+1 - suite parentale - ' + titres[num], fontsize=10.5, fontweight='bold', va='top')
    L = controles(v); nko = sum(1 for l in L if not l[4])
    ax.text(-0.5, D + 0.98, 'Parcours : chambre -> dressing -> salle de bain (une porte depuis la chambre) ; porte NO ouvrant contre le mur ; ancien dressing supprimé ; '
            'SDB sans baignoire (douche, WC et vasque suspendus) ; façade modifiée seulement à l\'ouverture rouge.', fontsize=6.6, va='top', color='#333')
    ax.text(-0.5, -1.62, 'Contrôles chiffrés : %d, écarts : %d. Rouge hachuré = démolition, bleu = neuf, rouge plein = fermeture. Cotes en mètres.' % (len(L), nko), fontsize=6.6, va='bottom')
    out = os.path.join(HERE, 'apercus'); os.makedirs(out, exist_ok=True)
    fig.savefig(os.path.join(out, 'MBAO_R1_P%d.png' % num), dpi=130, bbox_inches='tight'); plt.close(fig)
    return L, nko


if __name__ == '__main__':
    total = 0
    for n in (1, 2, 3):
        L, nko = dessiner(variante(n)); total += nko
        print('--- proposition', n, ':', len(L), 'contrôles,', nko, 'écart(s)')
        for l in L:
            if not l[4]: print('   ÉCART', *l)
    sys.exit(1 if total else 0)
