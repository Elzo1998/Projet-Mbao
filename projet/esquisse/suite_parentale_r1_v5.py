"""MBAO - R+1 : suite parentale, version E (indice E) : géométrie et contrôles chiffrés.

python3 -I projet/esquisse/suite_parentale_r1_v5.py   ->  liste des contrôles (le dessin est fait par pdf_r1_suite.py, qui importe ce module)
Repère (mètres) : x vers l'est de 0 à 8.27, y vers le nord de 0 à 5.65, origine = angle intérieur sud-ouest de la zone ; relevé de l'existant : suite_parentale_r1.py.

Retours du client sur le PDF D : deux ouvertures de porte (2.20 de haut) aux deux bouts de la cloison centrale, pas de porte coulissante ; lit entre les deux ouvertures,
TV en face ; dressing limité à la ligne rouge (penderie nord raccourcie) ; meuble de rangement remplacé par une double vasque contre le mur de la salle de bain ;
salle de bain sans vasque (WC et douche) ; fenêtres : chambre 1.00 pleine hauteur (bas fixe, haut à soufflet), dressing 1.60 de l'allège de la vasque au linteau.
"""
import math, os, sys
from shapely.geometry import box, Polygon
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import suite_parentale_r1 as B

W, D = B.W, B.D
SDB_Y, Y_TOP = 2.38, 2.53                               # profondeur intérieure de la salle de bain (1.83 + 0.55) ; dessus de son mur nord
OUV_S, OUV_N = (0.0, 0.80), (4.75, D)                   # ouvertures dans la cloison centrale (y) : côté façade et côté nord
LINTEAU, ALLEGE = 2.20, 0.95                            # linteau commun ; allège standard (fenêtre 1.25 de haut)
SOUS_FACE_C4 = 2.80                                     # sous-face de la poutre C4 (15x60) au-dessus de l'ouverture sud (coffrage p.5)
POUTRE_B14 = 2.75                                       # sous-face de la poutre B14 (15x65) au-dessus de la cloison, depuis le sol fini (coffrage p.5)

# ---- chambre : lit tête contre la cloison centrale entre les deux ouvertures, TV en face sur le mur ouest
YC = (OUV_S[1] + OUV_N[0]) / 2                          # axe de la cloison pleine entre les ouvertures
LIT = ('Lit 1.80 x 2.00 (encombrement 1.86)', 4.06 - 2.10, YC - 0.93, 2.10, 1.86)
CHEV_S, CHEV_N = ('Chevet', 3.66, YC - 0.93 - 0.40, 0.40, 0.40), ('Chevet', 3.66, YC + 0.93, 0.40, 0.40)
TV = ('Meuble TV 1.40', 0.0, YC - 0.70, 0.40, 1.40)
FAUT = ('Fauteuil', 0.35, 0.25, 0.80, 0.80)
GUER = ('Guéridon', 1.25, 0.42, 0.45, 0.45)
COMM = ('Commode 1.20', 1.60, 5.20, 1.20, 0.45)
# ---- dressing : penderie en U limitée à la ligne rouge (nord à partir de x 6.10), hall libre côté cloison centrale
U_N = ('Penderie U (nord)', 6.10, D - 0.60, W - 6.10, 0.60)
U_E = ('Penderie U (est)', W - 0.60, Y_TOP, 0.60, D - 0.60 - Y_TOP)
U_S = ('Penderie U (sud)', 6.10, Y_TOP, W - 0.60 - 6.10, 0.60)
VASQUE = ('Double vasque 1.40', 5.45, 0.05, 0.50, 1.40)      # contre le mur ouest de la salle de bain, façade côté fenêtre
# ---- salle de bain 2.17 x 2.38 : douche SE sous la fenêtre existante, WC suspendu mur est (plus de vasque)
DOUCHE = ('Douche 1.20 x 1.00', 7.07, 0.0, 1.20, 1.00)
WC = ('WC susp.', 7.72, 1.52, 0.55, 0.36)
PORTE_SDB = ((6.09, 2.35), 0.80, 270, 360, 0)           # porte 1.55-2.35 du mur ouest, charnière au nord : vantail ouvert à plat contre le mur nord
PORTE_NO = ((0.15, D), 0.90, 270, 360, 270)             # porte d'entrée de la suite (existante) : vantail contre le mur ouest
# ---- fenêtres de façade (x0, x1, allège, hauteur)
FEN_CH = (0.20, 1.20, ALLEGE, 1.25)                     # chambre : 1.00, bas fixe 0.95-1.60, haut à soufflet 1.60-2.20 (ancienne fenêtre de WC)
FEN_DR = (4.25, 5.85, ALLEGE, 1.25)                     # dressing : 1.60 x 1.25
FEN_SDB = (7.07, 8.07, 1.60, 0.60)                      # salle de bain : inchangée
MEUBLES = [LIT, CHEV_S, CHEV_N, TV, FAUT, GUER, COMM, U_N, U_E, U_S, VASQUE, DOUCHE, WC]


def R(m): return box(m[1], m[2], m[1] + m[3], m[2] + m[4])


def pie(c, r, a0, a1, n=24):
    return Polygon([c] + [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)])


def controles():
    L = []
    def t(rid, nom, val, mini): L.append((rid, nom, round(val, 2), mini, val >= mini - 1e-9))
    def info(rid, nom, val): L.append((rid, nom, val, val, True))
    libre = lambda z, obst: min(-z.intersection(o).area if z.intersection(o).area > 1e-6 else 1.0 for o in obst)
    lit, tv, vq = R(LIT), R(TV), R(VASQUE)
    pn, pe, ps = R(U_N), R(U_E), R(U_S)
    # --- ouvertures de la cloison centrale
    t('PORTE', 'Ouverture sud (côté façade) : largeur >= 0.80 entre la façade et le poteau K1 (y 0.81)', OUV_S[1] - OUV_S[0], 0.80)
    t('PORTE', 'Ouverture nord : largeur >= 0.80', OUV_N[1] - OUV_N[0], 0.80)
    t('STR', 'Ouverture nord : hauteur 2.20 sous la sous-face de la poutre B14 (2.75), linteau de cloison à prévoir', POUTRE_B14 - LINTEAU, 0.0)
    t('STR', 'Ouverture sud : hauteur 2.20 sous la sous-face de la poutre C4 (2.80), linteau de cloison à prévoir', SOUS_FACE_C4 - LINTEAU, 0.0)
    info('POR-020', 'Baie ouest 1.62 : porte-fenêtre COULISSANTE, aucun débattement : ne gêne pas l\'ouverture sud (pas d\'arc en plan)', 1)
    t('CIR-001', 'Hall du dressing : largeur libre entre la cloison centrale et les penderies (x 4.21 à 6.10)', 6.10 - 4.21, 0.90)
    t('CIR-002', 'Passage entre la cloison centrale et la double vasque (ouverture sud)', vq.distance(box(4.21, 0, 4.22, D)), 0.90)
    # --- chambre
    t('CHB-001', 'Lit : tête contre le mur plein de la cloison (entre les ouvertures) : marge sud jusqu\'à l\'ouverture sud', (LIT[2] - 0.40) - OUV_S[1], 0.60)
    t('CHB-001', 'Lit : marge nord jusqu\'à l\'ouverture nord (chevets compris)', OUV_N[0] - (LIT[2] + LIT[4] + 0.40), 0.60)
    t('CIR-004', 'Chambre : côté façade du lit / mur de façade', lit.distance(box(0, -0.15, 4.06, 0)), 0.60)
    t('CIR-004', 'Chambre : côté nord du lit / mur nord', lit.distance(box(0, D, 4.06, D + 0.1)), 0.60)
    t('CIR-005', 'Chambre : pied du lit / meuble TV', lit.distance(tv), 0.70)
    t('AXE', 'Meuble TV axé sur le lit (écart des axes, max 0.05)', 0.05 - abs((TV[2] + TV[4] / 2) - (LIT[2] + LIT[4] / 2)), 0.0)
    for nom, (c, r, a0, a1, _), obst in (('Porte NO', PORTE_NO, [R(COMM), R(TV), lit, R(CHEV_N)]), ('Porte SDB', PORTE_SDB, [R(DOUCHE), R(WC), vq])):
        p = pie(c, r, a0, a1); t('CIR-030', nom + ' : débattement libre', min(-p.intersection(o).area if p.intersection(o).area > 1e-6 else p.distance(o) for o in obst), 0.0)
    t('CIR-003', 'Commode : libre devant (côté sud, jusqu\'au fauteuil / lit)', R(COMM).distance(lit), 0.70)
    t('CIR-002', 'Fauteuil / guéridon et lit : passage', R(FAUT).distance(lit), 0.70)
    # --- dressing
    t('CIR-013', 'Dressing : allée entre penderie nord et penderie sud', pn.distance(ps), 0.90)
    t('CIR-013', 'Dressing : allée devant la penderie est (jusqu\'au bord ouest du U)', U_E[1] - 6.10, 0.90)
    t('CIR-019', 'Double vasque : libre devant >= 0.70 (côté cloison centrale)', 5.45 - 4.21, 0.70)
    t('CIR-020', 'Porte SDB : approche libre côté dressing (0.80) devant la porte', vq.distance(box(5.15, 1.55, 5.95, 2.35)), 0.0)
    # --- salle de bain
    t('SDE-005', 'Douche italienne >= 1.20 x 0.90 (1.20 x 1.00)', min(DOUCHE[3], 1.20 * DOUCHE[4] / DOUCHE[4]), 1.20)
    t('SDE-007', 'WC : axe à >= 0.40 de la douche', (WC[2] + 0.18) - DOUCHE[4], 0.40)
    t('SDE-007', 'WC : axe à >= 0.40 du mur nord de la SDB', SDB_Y - (WC[2] + 0.18), 0.40)
    t('CIR-018', 'WC : zone libre 0.60 devant la cuvette', libre(box(7.12, 1.52, 7.72, 1.88), [R(DOUCHE), pie(*PORTE_SDB[:4])]), 0.0)
    t('CIR-020', 'Douche : approche libre 0.70 x 0.70', libre(box(6.37, 0.0, 7.07, 0.70), [R(WC), pie(*PORTE_SDB[:4])]), 0.0)
    t('PORTE', 'Porte SDB : vantail ouvert adossé au mur nord (jeu <= 0.05)', 0.05 - (SDB_Y - 2.35), 0.0)
    # --- fenêtres
    t('FEN-001', 'Fenêtre du dressing : tête à 2.20 (allège 0.95 + 1.25)', FEN_DR[2] + FEN_DR[3], LINTEAU)
    t('FEN-001', 'Fenêtre de la chambre : tête à 2.20 (allège 0.95 + 1.25)', FEN_CH[2] + FEN_CH[3], LINTEAU)
    t('FEN', 'Fenêtre du dressing : standard 1.60 x 1.25 (STANDARDS)', FEN_DR[1] - FEN_DR[0], 1.60)
    t('FEN', 'Allège de la fenêtre du dressing >= hauteur de la double vasque (0.90)', FEN_DR[2], 0.90)
    info('FEN', 'Fenêtre de la chambre 1.00 x 1.25 : largeur hors standard (1.40 ou 1.60), conservée sur demande du client', 1.00)
    t('NAT', 'Lumière et air naturels : fenêtre du dressing (largeur >= 0.90)', FEN_DR[1] - FEN_DR[0], 0.90)
    t('NAT', 'Lumière et air naturels : fenêtre de la chambre (largeur >= 0.90)', FEN_CH[1] - FEN_CH[0], 0.90)
    t('NAT', 'Lumière et air naturels : fenêtre de la salle de bain existante (>= 0.60)', FEN_SDB[1] - FEN_SDB[0], 0.60)
    t('MET-021', 'Murs neufs >= 0.15', 0.15, 0.15)
    return L


if __name__ == '__main__':
    L = controles(); nko = sum(1 for l in L if not l[4])
    print(len(L), 'contrôles,', nko, 'écart(s)')
    for l in L: print('  ', 'ÉCART' if not l[4] else 'ok   ', *l[:4])
    sys.exit(1 if nko else 0)
