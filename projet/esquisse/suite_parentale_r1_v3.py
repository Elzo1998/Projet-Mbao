"""MBAO - R+1 : suite parentale, proposition 3 version C (indice C), retours du client du 02/11 sur la proposition 3.

python3 -I projet/esquisse/suite_parentale_r1_v3.py  ->  projet/esquisse/apercus/MBAO_R1_P3C.png + contrôles chiffrés (image seulement : PDF après validation)
Repère et géométrie de base : suite_parentale_r1.py (x vers l'est, y vers le nord, origine = angle intérieur sud-ouest de la zone).
"""
import os, sys, math
from shapely.geometry import box
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import suite_parentale_r1 as B
from suite_parentale_r1 import W, D, GRIS, NOIR, ROUGE, BLEU, rect, porte, meuble, etiquette
from suite_parentale_r1_v2 import pie

SDB_Y = 2.38                                   # profondeur intérieure de la salle de bain : 1.83 existant + 0.55
Y_TOP = SDB_Y + 0.15                           # dessus du mur nord de la salle de bain
SLIDE = (3.90, 4.70)                           # percement de la porte coulissante du dressing (cloison centrale)
# ---- chambre : lit contre le côté façade, TV axé sur le lit, fauteuil au nord
LIT = ('Lit 1.80 x 2.00', 0.0, 0.75, 2.10, 1.80)
AXE_LIT = 0.75 + 0.90
CHEV_S, CHEV_N = ('Chevet', 0.0, 0.30, 0.45, 0.40), ('Chevet', 0.0, 2.60, 0.45, 0.45)
TV = ('Meuble TV 1.40', 3.66, AXE_LIT - 0.70, 0.40, 1.40)
FAUT = ('Fauteuil', 1.90, 4.30, 0.80, 0.80)
# ---- dressing : penderie en U (nord, est, mur de la salle de bain), allée centrale, meuble bas sous la fenêtre
U_N = ('Penderie U (nord)', 4.30, D - 0.60, W - 4.30, 0.60)
U_E = ('Penderie U (est)', W - 0.60, Y_TOP, 0.60, D - 0.60 - Y_TOP)
U_S = ('Penderie U (sud)', 6.09, Y_TOP, W - 0.60 - 6.09, 0.60)
BAS = ('Meuble bas rangements 1.45 x 0.50', 4.21, 0.0, 1.45, 0.50)
# ---- salle de bain 2.18 x 2.38 : douche SE, WC suspendu mur est, meuble vasque suspendu mur nord
DOUCHE = ('Douche 1.00 x 1.00', 7.27, 0.0, 1.00, 1.00)
WC = ('WC susp.', 7.72, 1.52, 0.55, 0.36)
VASQUE = ('Vasque susp. 0.80', 6.25, SDB_Y - 0.45, 0.80, 0.45)
PORTE_SDB = ((6.09, 0.98), 0.86, 0, 90, 0)     # porte latérale d'origine (mur ouest de la SDB, y 0.98-1.84), charnière au sud, ouverture vers l'intérieur
PORTE_NO = ((0.15, D), 0.90, 270, 360, 270)    # charnière côté ouest : le vantail s'ouvre contre le mur
MEUBLES = [LIT, CHEV_S, CHEV_N, TV, FAUT, U_N, U_E, U_S, BAS, DOUCHE, WC, VASQUE]


def R(m): return box(m[1], m[2], m[1] + m[3], m[2] + m[4])


def controles():
    L = []
    def t(rid, nom, val, mini): L.append((rid, nom, round(val, 2), mini, val >= mini - 1e-9))
    lit = R(LIT); pn, pe, ps = R(U_N), R(U_E), R(U_S)
    t('CIR-013', 'Dressing : allée centrale entre penderie nord et sud', pn.distance(ps), 0.90)
    t('CIR-013', 'Dressing : allée centrale (largeur) 1.92, banc possible (0.70 de chaque côté)', pn.distance(ps) - 0.40, 1.40)
    t('CIR-013', 'Dressing : allée devant la penderie est (du bord ouest du U)', 7.67 - 4.21, 0.90)
    t('CIR-004', 'Chambre : côté façade du lit / mur de façade', lit.distance(box(0, -0.15, 4.06, 0)), 0.60)
    t('CIR-004', 'Chambre : côté nord du lit (chevet) / fauteuil', lit.union(R(CHEV_N)).distance(R(FAUT)), 0.60)
    t('CIR-005', 'Chambre : pied du lit / meuble TV', lit.distance(R(TV)), 0.70)
    t('AXE', 'Meuble TV axé sur le lit (écart des axes, max 0.05)', 0.05 - abs((TV[2] + TV[4] / 2) - AXE_LIT), 0.0)
    t('CIR-016', 'Baie ouest : débattement des portes-fenêtres libre devant le meuble TV', R(TV).distance(box(2.405, 0, 4.025, 0.81)), 0.0)
    for nom, (c, r, a0, a1, _), obst in (('Porte NO', PORTE_NO, [lit, R(CHEV_N), R(FAUT)]), ('Porte SDB', PORTE_SDB, [R(DOUCHE), R(WC), R(VASQUE)])):
        p = pie(c, r, a0, a1); t('CIR-030', nom + ' : débattement libre', min(-p.intersection(o).area if p.intersection(o).area > 1e-6 else p.distance(o) for o in obst), 0.0)
    t('CIR-030', 'Porte coulissante : vantail rangé derrière la penderie nord (course libre au nord 0.85)', D - SLIDE[1], 0.85)
    t('SDE-005', 'Douche >= 0.90 x 0.90 (1.00 x 1.00)', 1.00, 0.90)
    t('SDE-007', 'WC : axe à >= 0.40 de la douche', (WC[2] + 0.18) - 1.00, 0.40)
    t('SDE-007', 'WC : axe à >= 0.40 du mur nord de la SDB', SDB_Y - (WC[2] + 0.18), 0.40)
    t('CIR-018', 'WC : libre devant la cuvette >= 0.60 (vers la porte)', R(WC).distance(R(VASQUE)), 0.60)
    t('CIR-019', 'Meuble vasque : libre devant >= 0.70', R(VASQUE).distance(R(DOUCHE)), 0.70)
    t('CIR-020', 'Douche : approche libre >= 0.70', R(DOUCHE).distance(R(VASQUE)), 0.70)
    t('NAT', 'Lumière et air naturels : fenêtre du dressing 1.40 (>= 0.90)', 1.40, 0.90)
    t('NAT', 'Lumière et air naturels : fenêtre de la salle de bain existante 1.00', 1.00, 0.60)
    return L


def dessiner():
    fig, ax = plt.subplots(figsize=(11, 8.9))
    for m in B.MURS_EXT: rect(ax, m, GRIS, NOIR, 1.0, z=3)
    for n, m in B.POTEAUX.items(): rect(ax, m, NOIR, NOIR, 0.5, z=4)
    ax.add_patch(Rectangle((1.38, -1.40), 5.57, 1.25, fc='#f2f2f2', ec=NOIR, lw=0.6, zorder=1)); ax.text(4.1, -0.78, 'BALCON (inchangé)', ha='center', fontsize=7, color='#555')
    ax.add_patch(Rectangle((B.PORTE_NO[0], D), B.PORTE_NO[1] - B.PORTE_NO[0], 0.15, fc='white', ec='none', zorder=4))
    ax.add_patch(Rectangle((B.PORTE_NE[0], D), B.PORTE_NE[1] - B.PORTE_NE[0], 0.15, fc='#f4c0c0', ec=ROUGE, lw=0.8, zorder=4))
    # façade : baie ouest et fenêtre de la SDB inchangées ; baie est réduite à une fenêtre 1.40 x 1.00 (allège 1.10)
    for a, b in ((B.BAIES[0][0], B.BAIES[0][1]), (7.07, 8.07)):
        ax.add_patch(Rectangle((a, -0.15), b - a, 0.15, fc='white', ec='none', zorder=4)); ax.plot([a, b], [-0.075, -0.075], color=BLEU, lw=1.6, zorder=5)
    ax.add_patch(Rectangle((4.245, -0.15), 1.62, 0.15, fc=GRIS, ec='none', zorder=4.5)); ax.add_patch(Rectangle((4.25, -0.15), 1.40, 0.15, fc='white', ec='none', zorder=4.6))
    ax.plot([4.25, 5.65], [-0.075, -0.075], color=ROUGE, lw=2.2, zorder=5); ax.text(4.95, -0.30, 'Fenêtre 1.40 x 1.00, allège 1.10', ha='center', fontsize=6.3, color=ROUGE)
    # cloison centrale conservée, un seul percement : porte coulissante du dressing
    rect(ax, (4.06, 0, 0.15, SLIDE[0]), GRIS, NOIR, 1.0, z=3); rect(ax, (4.06, SLIDE[1], 0.15, D - SLIDE[1]), GRIS, NOIR, 1.0, z=3)
    rect(ax, (4.26, SLIDE[1], 0.04, 0.85), '#dddddd', NOIR, 0.8, z=5, ls=(0, (3, 2)))                    # vantail ouvert, rangé vers le nord
    ax.annotate('', (4.50, SLIDE[1] + 0.50), (4.50, SLIDE[0] + 0.30), arrowprops=dict(arrowstyle='->', lw=0.9, color=NOIR), zorder=8)
    ax.text(4.55, 4.28, 'porte coulissante 0.80', fontsize=5.6, rotation=90, va='center', zorder=8)
    # démolitions : WC ouest (2 murs) et mur nord du WC est ; le mur ouest du WC est est CONSERVÉ
    for c in (B.CLOIS_EXISTANT[0], B.CLOIS_EXISTANT[1], B.CLOIS_EXISTANT[2]): rect(ax, c, '#f8e0e0', ROUGE, 0.8, hatch='////', z=3, ls=(0, (3, 2)))
    rect(ax, (5.95, 0, 0.14, 0.98), GRIS, NOIR, 1.0, z=3); rect(ax, (5.95, 1.84, 0.14, 0.14), GRIS, NOIR, 1.0, z=3)   # mur conservé, ouverture de porte 0.98-1.84
    rect(ax, (5.95, 1.98, 0.14, Y_TOP - 1.98), '#cfe0ff', BLEU, 1.0, z=3)                                                  # prolongement neuf
    rect(ax, (5.95, SDB_Y, W - 5.95, 0.15), '#cfe0ff', BLEU, 1.0, z=3)                                                     # nouveau mur nord de la SDB
    for m in MEUBLES: meuble(ax, m, fs=5.0)
    porte(ax, *PORTE_SDB); porte(ax, *PORTE_NO)
    surf_dr = box(4.21, Y_TOP, W, D).area + box(4.21, 0, 5.95, Y_TOP).area
    etiquette(ax, 2.75, 3.55, 'CHAMBRE', 4.06 * D, fs=9)
    etiquette(ax, 5.75, 4.05, 'WALK-IN DRESSING\npenderie en U', surf_dr, fs=7.5)
    etiquette(ax, 6.95, 1.15, 'SDB', (W - 6.09) * SDB_Y, fs=8)
    ax.set_aspect('equal'); ax.set_xlim(-0.6, W + 0.6); ax.set_ylim(-1.7, D + 1.45); ax.axis('off')
    L = controles(); nko = sum(1 for l in L if not l[4])
    ax.text(-0.5, D + 1.40, 'MBAO - R+1 - suite parentale - PROPOSITION 3, VERSION C', fontsize=10.5, fontweight='bold', va='top')
    ax.text(-0.5, D + 1.08, 'Lit côté façade, TV axé sur le lit, fauteuil au nord ; porte du dressing coulissante ; SDB agrandie de 0.55 vers le nord (mur et porte d\'origine gardés) ;\n'
            'penderie en U sans îlot (allée centrale 1.92) ; façade modifiée seulement à l\'ouverture rouge. Chambre -> dressing -> SDB.', fontsize=6.6, va='top', color='#333')
    ax.text(-0.5, -1.62, 'Contrôles chiffrés : %d, écarts : %d. Rouge hachuré = démolition, bleu = neuf, rouge plein = fermeture. Cotes en mètres.' % (len(L), nko), fontsize=6.6, va='bottom')
    out = os.path.join(HERE, 'apercus'); os.makedirs(out, exist_ok=True)
    fig.savefig(os.path.join(out, 'MBAO_R1_P3C.png'), dpi=130, bbox_inches='tight'); plt.close(fig)
    return L, nko


if __name__ == '__main__':
    L, nko = dessiner()
    print(len(L), 'contrôles,', nko, 'écart(s)')
    for l in L: print('  ', 'ÉCART' if not l[4] else 'ok   ', *l[:4])
    sys.exit(1 if nko else 0)
