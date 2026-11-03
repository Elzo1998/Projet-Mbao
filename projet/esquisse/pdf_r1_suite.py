"""MBAO - R+1 : PDF de la suite parentale (version E) en trois versions (démolitions, constructions, projet final).

python3 -I projet/esquisse/pdf_r1_suite.py   ->  projet/esquisse/MBAO_R1_Suite_parentale_D.pdf (+ aperçus PNG dans apercus/pdf/)

Chaque page reprend le plan R+1 complet du PDF d'origine (page 15 de PROJET_MBAO_Architecture_V2.pdf, vectoriel, échelle 1:50, charte graphique
de D&F : murs gris 0.75 à contour noir, libellés bleu foncé, cotes en italique) ; un cadre orange marque la zone des deux chambres ; les
modifications sont dessinées dans le même style. Géométrie du projet : suite_parentale_r1_v5.py (version E, contrôles chiffrés).
"""
import math, os, sys
import pymupdf
from shapely.geometry import box, LineString
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import suite_parentale_r1_v5 as V
import suite_parentale_r1 as B

SRC = os.path.join(os.path.dirname(HERE), 'source', 'PROJET_MBAO_Architecture_V2.pdf')
OUT = os.path.join(HERE, 'MBAO_R1_Suite_parentale_E.pdf')
K = 1000 / 50 * 72 / 25.4                               # 1 m a 1:50 en points
X0, Y0 = 190.6, 898.8                                    # face intérieure ouest / face intérieure de la façade (relevés sur le PDF d'origine)
W, D = B.W, B.D
GRIS, NOIR, BLEU_T, ORANGE, ROUGE, BLEU = (0.75,) * 3, (0, 0, 0), (0, 0, 0.627), (1.0, 0.55, 0.0), (0.85, 0.1, 0.1), (0.1, 0.3, 0.8)
BLEU_C = (0.80, 0.88, 1.0)
SDB_Y, Y_TOP = V.SDB_Y, V.Y_TOP
DATE = '03/11/26'


def X(x): return X0 + K * x
def Y(y): return Y0 - K * y
def R(x, y, w, h): return pymupdf.Rect(X(x), Y(y + h), X(x + w), Y(y))
def P(x, y): return pymupdf.Point(X(x), Y(y))


class Pg:
    """Page de sortie : fond = plan d'origine, puis dessins par-dessus."""
    def __init__(self, doc, src):
        self.pg = doc.new_page(width=841.92, height=1190.52); self.pg.show_pdf_page(self.pg.rect, src, 14)

    def rect(self, r, fill=None, color=NOIR, w=0.84, dash=None):
        s = self.pg.new_shape(); s.draw_rect(r); s.finish(fill=fill, color=color, width=w, dashes=dash, closePath=True); s.commit()

    def line(self, a, b, color=NOIR, w=0.48, dash=None):
        s = self.pg.new_shape(); s.draw_line(a, b); s.finish(color=color, width=w, dashes=dash); s.commit()

    def poly(self, pts, color=NOIR, w=0.48, dash=None, fill=None, close=False):
        s = self.pg.new_shape(); s.draw_polyline(pts); s.finish(color=color, fill=fill, width=w, dashes=dash, closePath=close); s.commit()

    def oval(self, r, fill=None, color=NOIR, w=0.48):
        s = self.pg.new_shape(); s.draw_oval(r); s.finish(fill=fill, color=color, width=w); s.commit()

    def blanc(self, r): self.rect(r, fill=(1, 1, 1), color=None, w=0)

    def effacer(self, rects):
        """Supprime le TEXTE d'origine sous ces zones (pas de texte caché dans le PDF) ; le tracé vectoriel est laissé, un cache blanc le couvre."""
        for r in rects: self.pg.add_redact_annot(r, fill=False)             # texte seulement : aucun fond blanc, les murs dessous restent
        self.pg.apply_redactions(images=0, graphics=0)

    def txt(self, x, y, t, size=8, font='helv', color=NOIR, rot=0, centre=False):
        if centre: x -= pymupdf.get_text_length(t, fontname=font, fontsize=size) / 2 * (1 if rot == 0 else 0)
        self.pg.insert_text(pymupdf.Point(x, y), t, fontsize=size, fontname=font, color=color, rotate=rot)

    def hachures(self, r, color=ROUGE, pas=3.2, w=0.5):
        b = box(r.x0, r.y0, r.x1, r.y1); h = r.height
        for k in range(int((r.width + h) / pas) + 2):
            l = LineString([(r.x0 + k * pas, r.y0), (r.x0 + k * pas - h, r.y1)]).intersection(b)
            if not l.is_empty: (a, c) = list(l.coords)[0], list(l.coords)[-1]; self.line(pymupdf.Point(*a), pymupdf.Point(*c), color, w)

    def mur(self, m, mode='ex'):
        """m = (x, y, l, h) en mètres. ex = existant gris ; neuf = bleu ; demol = hachures rouges sur gris."""
        r = R(*m)
        if mode == 'ex': self.rect(r, GRIS, NOIR, 0.84)
        elif mode == 'neuf': self.rect(r, BLEU_C, BLEU, 1.1); self.hachures(r, BLEU, 3.6, 0.35)
        elif mode == 'demol': self.rect(r, GRIS, NOIR, 0.84); self.hachures(r, ROUGE, 2.6, 0.7); self.rect(r, None, ROUGE, 1.1)

    def arc(self, ch, r, a0, a1, ouvert, color=NOIR):
        pts = [P(ch[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / 24)), ch[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / 24))) for i in range(25)]
        self.poly(pts, color, 0.48)
        self.line(P(*ch), P(ch[0] + r * math.cos(math.radians(ouvert)), ch[1] + r * math.sin(math.radians(ouvert))), color, 0.84)

    def cote(self, a, b, texte, decal=0.0, vertical=False, size=9):
        """Cote dans la charte du plan : trait fin, traits obliques aux extrémités, texte italique sur fond blanc."""
        if vertical: p1, p2 = pymupdf.Point(X(a[0]) + decal, Y(a[1])), pymupdf.Point(X(b[0]) + decal, Y(b[1]))
        else: p1, p2 = pymupdf.Point(X(a[0]), Y(a[1]) + decal), pymupdf.Point(X(b[0]), Y(b[1]) + decal)
        self.line(p1, p2, NOIR, 0.48)
        for p in (p1, p2): self.line(pymupdf.Point(p.x - 3, p.y + 3), pymupdf.Point(p.x + 3, p.y - 3), NOIR, 0.7)
        c = pymupdf.Point((p1.x + p2.x) / 2, (p1.y + p2.y) / 2); tl = pymupdf.get_text_length(texte, 'heit', size)
        if vertical:
            self.blanc(pymupdf.Rect(c.x - 5, c.y - tl / 2 - 1, c.x + 5, c.y + tl / 2 + 1)); self.txt(c.x + 3.5, c.y + tl / 2, texte, size, 'heit', rot=90)
        else:
            self.blanc(pymupdf.Rect(c.x - tl / 2 - 1, c.y - 6, c.x + tl / 2 + 1, c.y + 4)); self.txt(c.x - tl / 2, c.y + 3, texte, size, 'heit')

    def etiquette(self, x, y, nom, surf=None):
        """Libellé de pièce comme sur le plan d'origine : capitales bleu foncé 8 pt, surface dessous."""
        t = nom if surf is None else nom
        self.txt(X(x) - pymupdf.get_text_length(t, 'helv', 8) / 2, Y(y), t, 8, 'helv', BLEU_T)
        if surf is not None:
            s = '%.2f m²' % surf; self.txt(X(x) - pymupdf.get_text_length(s, 'helv', 8.1) / 2, Y(y) + 10, s, 8.1, 'helv', BLEU_T)


# ---------------------------------------------------------------------------------------------------- éléments communs
CADRE = pymupdf.Rect(160, 561, 706, 1012)


def cartouche(p, titre, no):
    p.effacer([pymupdf.Rect(456, 1064, 614, 1095), pymupdf.Rect(520, 1111, 548, 1129), pymupdf.Rect(404, 1111, 458, 1129)])
    p.blanc(pymupdf.Rect(456, 1064, 614, 1095)); titre += ' - IND. E'; p.txt(535 - pymupdf.get_text_length(titre, 'hebo', 10.5) / 2, 1085, titre, 10.5, 'hebo')
    p.blanc(pymupdf.Rect(520, 1111, 548, 1129)); p.txt(523, 1124, no, 12, 'helv')
    p.blanc(pymupdf.Rect(404, 1111, 458, 1129)); p.txt(406, 1124, DATE, 11, 'hebo')


def cadre(p, legende):
    p.rect(CADRE, None, ORANGE, 2.2)
    p.rect(pymupdf.Rect(470, 551, 706, 563), ORANGE, ORANGE, 0); p.txt(476, 560.5, 'ZONE DES MODIFICATIONS - SUITE PARENTALE', 7.4, 'hebo', (1, 1, 1))


def bande(p, x, y, titre, lignes, larg):
    """Colonne de texte dans la marge de la page (légende ou notes)."""
    p.txt(x, y, titre, 8, 'hebo'); y += 11
    for l in lignes:
        for sous in wrap(l, larg, 6.4):
            p.txt(x, y, sous, 6.4); y += 7.9
        y += 3
    return y


def wrap(t, larg, size):
    mots, out, cur = t.split(), [], ''
    for m in mots:
        if pymupdf.get_text_length((cur + ' ' + m).strip(), 'helv', size) > larg: out.append(cur); cur = m
        else: cur = (cur + ' ' + m).strip()
    return out + [cur]


def vider_zone(p):
    p.effacer([pymupdf.Rect(191.0, 580.6, 659.0, 898.4), pymupdf.Rect(142, 566, 181.5, 899), pymupdf.Rect(669, 566, 704, 899), pymupdf.Rect(315, 897.5, 335, 912), pymupdf.Rect(541, 897.5, 561, 912)])
    """Efface l'intérieur de la zone (cloisons, mobilier, textes, cotes de chaîne) ; murs extérieurs, balcon et chaînes du bas restent."""
    p.blanc(pymupdf.Rect(191.0, 580.6, 659.0, 898.4))
    p.blanc(pymupdf.Rect(142, 566, 181.5, 899)); p.blanc(pymupdf.Rect(669, 566, 704, 899))
    p.blanc(pymupdf.Rect(431.4, 899.4, 522.9, 906.6))                               # symbole de la baie est : l'ouverture seulement, murs et piliers de façade intacts


def retirer_ss(p):
    """Les repères « SS » des anciens WC sont effacés comme texte par vider_zone ; rien n'est redessiné sur la façade."""
    return


def chaines(p):
    """Chaînes verticales gauche et droite refaites (le mur à 1.83 a disparu côté ouest ; salle de bain 2.38 côté est)."""
    for xl, xt, droite in ((173.5, 152.0, False), (695.0, 683.0, True)):
        ys = [(5.65 + 0.15, 5.65, '0.15'), (5.65, 0.0, None), (0.0, -0.15, '0.15')]
        seg = [('0.15', D + 0.15, D)]
        if not droite: seg += [('%.2f' % D, D, 0.0)]
        else: seg += [('%.2f' % (D - Y_TOP), D, Y_TOP), ('0.15', Y_TOP, SDB_Y), ('%.2f' % SDB_Y, SDB_Y, 0.0)]
        seg += [('0.15', 0.0, -0.15)]
        for t, a, b in seg:
            p.line(pymupdf.Point(xl, Y(a)), pymupdf.Point(xl, Y(b)), NOIR, 0.48)
            for yy in (a, b): p.line(pymupdf.Point(xl - 3, Y(yy) + 3), pymupdf.Point(xl + 3, Y(yy) - 3), NOIR, 0.7)
            mid = (Y(a) + Y(b)) / 2; tl = pymupdf.get_text_length(t, 'heit', 10.6)
            p.blanc(pymupdf.Rect(xt - 7, mid - tl / 2 - 1, xt + 6, mid + tl / 2 + 1)); p.txt(xt + 4, mid + tl / 2, t, 10.6, 'heit', rot=90)
        # prolongements des murs jusqu'à la chaîne
        for yy in sorted({a for _, a, _ in seg} | {b for _, _, b in seg}):
            xw = 182.0 if not droite else 667.9
            p.line(pymupdf.Point(xl + (0 if not droite else 0), Y(yy)), pymupdf.Point(xw - (2 if not droite else -2), Y(yy)), NOIR, 0.48)


def fenetre_est(p, final):
    """Baie est de la façade ramenée à une fenêtre 1.60 x 1.00 (allège 1.10) : même ouverture, symbole de fenêtre."""
    p.rect(R(4.245, -0.15, 1.62, 0.15), (1, 1, 1), NOIR, 0.48)
    for yy in (-0.05, -0.10): p.line(P(4.245, yy), P(5.865, yy), NOIR, 0.48)
    p.line(P(5.05, -0.05), P(5.05, -0.10), NOIR, 0.48)
    if not final: p.txt(X(4.52), Y(0.45), 'fenêtre 160x125', 6.0, 'helv', BLEU); p.txt(X(4.52), Y(0.45) + 6.5, 'allège 0.95', 6.0, 'helv', BLEU)


# ---------------------------------------------------------------------------------------------------- version 1 : démolitions
def v_demolitions(doc, src):
    p = Pg(doc, src); cartouche(p, 'R+1 - DEMOLITIONS', '016'); cadre(p, None)
    for xa, xb in ((2.405, 4.025), (4.245, 5.865)): p.blanc(pymupdf.Rect(X(xa) + 1.2, Y(0.86), X(xb) - 1.2, Y(0.035)))      # portes-fenêtres coulissantes : pas d'arc d'ouverture en plan
    for c in (B.CLOIS_EXISTANT[0], B.CLOIS_EXISTANT[1], B.CLOIS_EXISTANT[2]): p.mur(c, 'demol')               # WC ouest (2 murs), mur nord du WC est
    p.mur((5.95, 1.84, 0.14, 0.14), 'demol')                                                                  # retour du mur ouest du WC est
    p.mur((4.06, V.OUV_S[0], 0.15, V.OUV_S[1] - V.OUV_S[0]), 'demol')                                         # ouverture côté façade (cloison centrale)
    p.mur((4.06, V.OUV_N[0], 0.15, V.OUV_N[1] - V.OUV_N[0]), 'demol')                                         # ouverture côté nord
    p.mur(B.STUB_O, 'demol'); p.mur(B.STUB_E, 'demol')                                                        # petits murs de l'ancien dressing
    for r in (R(*B.PLACARD_O), R(*B.PLACARD_E)): p.rect(r, None, ROUGE, 1.0, '[3 2] 0')                      # placards coulissants
    p.txt(X(1.75), Y(5.30), 'placard à déposer', 6.8, 'helv', ROUGE); p.txt(X(4.95), Y(5.30), 'placard à déposer', 6.8, 'helv', ROUGE)
    for r in ((0.0, 0.6, 0.6, 0.85), (1.50, 0.0, 0.70, 0.55), (7.65, 0.6, 0.62, 0.85), (6.1, 0.0, 0.70, 0.55)): p.rect(R(*r), None, ROUGE, 1.0, '[3 2] 0')   # sanitaires
    p.txt(X(0.10), Y(2.35), 'appareils sanitaires', 6.2, 'helv', ROUGE); p.txt(X(0.10), Y(2.35) + 7, 'à déposer', 6.2, 'helv', ROUGE)
    for r in ((2.18, 0.98, 0.14, 0.86), (5.95, 0.98, 0.14, 0.86), (7.22, 5.65, 0.90, 0.15), (4.245, -0.15, 1.62, 0.15), (0.20, -0.15, 1.00, 0.15)): p.rect(R(*r), None, ROUGE, 1.1, '[3 2] 0')   # portes des WC, porte NE, baie est, fenêtre du WC ouest
    p.txt(X(7.20), Y(4.62), 'porte NE à déposer', 6.2, 'helv', ROUGE)
    p.txt(X(4.32), Y(0.45), 'baie est à déposer', 6.4, 'helv', ROUGE)
    p.txt(X(0.68), Y(0.32), 'allège à démolir', 5.6, 'helv', ROUGE); p.txt(X(0.68), Y(0.32) + 6.5, '(1.60 à 0.95)', 5.6, 'helv', ROUGE)
    bande(p, 14, 600, 'LÉGENDE', ['Cadre orange : zone des modifications (deux chambres miroirs du R+1).', 'Hachures rouges : cloison ou mur à démolir.', 'Pointillé rouge : élément à déposer (placard, sanitaire, porte, baie, allège).', 'Gris : existant conservé.', 'Les poteaux, les poutres et les dalles ne sont pas touchés.'], 100)
    bande(p, 722, 600, 'DÉMOLITIONS', ['1. Cloison nord du WC ouest, 2.32 m.', '2. Cloison est du WC ouest, 1.98 m.', '3. Cloison nord du WC est, 2.32 m ; petit retour du mur ouest, 0.14 m.', '4. Deux ouvertures de porte dans la cloison centrale (non porteuse, sous la poutre B14) : côté façade 0.80 m (sous la poutre C4), côté nord 0.90 m (sous la poutre B14), hauteur 2.20, linteaux à prévoir.', '5. Deux petits murs de l\'ancien dressing : 0.62 m chacun.', '6. Placards coulissants des deux chambres.', '7. Appareils sanitaires, deux portes de WC, porte NE, baie est de façade ; repères « SS » des anciens WC retirés.', '8. Allège de la fenêtre du WC ouest, de 1.60 à 0.95 (fenêtre agrandie).', 'POINT DE L\'INGÉNIEUR : sur le coffrage du plancher haut, des bandes hachurées passent au droit des cloisons des WC : nature à confirmer avant la démolition.'], 100)
    return p


# ---------------------------------------------------------------------------------------------------- version 2 : constructions
def v_constructions(doc, src):
    p = Pg(doc, src); cartouche(p, 'R+1 - CONSTRUCTIONS', '017'); vider_zone(p); retirer_ss(p); chaines(p); fenetre_est(p, False)
    for m in ((4.06, V.OUV_S[1], 0.15, V.OUV_N[0] - V.OUV_S[1]), (5.95, 0, 0.14, 0.98)): p.mur(m, 'ex')
    p.rect(R(4.06, 0.81, 0.15, 0.60), (0.5,) * 3, NOIR, 0.5)                                                 # poteau K1 15/60 conservé
    for m in ((5.95, 0.98, 0.15, 0.57), (5.95, 2.35, 0.15, Y_TOP - 2.35), (5.95, SDB_Y, W - 5.95, 0.15)): p.mur(m, 'neuf')
    p.rect(R(7.22, D, 0.90, 0.15), BLEU_C, BLEU, 1.1); p.hachures(R(7.22, D, 0.90, 0.15), BLEU, 3.6, 0.35)     # fermeture de la porte NE
    p.txt(X(7.12), Y(5.42), 'fermeture porte NE', 6.2, 'helv', BLEU)
    # ouvertures de la cloison centrale, fenêtre de la chambre, menuiseries et appareils neufs (bleu)
    for (a, b), nom in ((V.OUV_S, 'ouv. 80x220'), (V.OUV_N, 'ouv. 90x220')):
        p.rect(R(4.06, a, 0.15, b - a), None, BLEU, 0.9, '[3 2] 0'); p.txt(X(4.36), Y(a) - 2, nom, 5.8, 'helv', BLEU, rot=90)
    p.arc(*V.PORTE_SDB[:4], V.PORTE_SDB[4], BLEU); p.arc(*V.PORTE_NO[:4], V.PORTE_NO[4], (0.35,) * 3)
    p.rect(R(0.20, -0.15, 1.00, 0.15), None, BLEU, 1.1, '[3 2] 0'); p.txt(X(0.25), Y(0.30), 'fenêtre 100x125, allège 0.95', 5.8, 'helv', BLEU); p.txt(X(0.25), Y(0.30) + 7, 'bas fixe, haut à soufflet', 5.8, 'helv', BLEU)
    for m in (V.U_N, V.U_E, V.U_S):
        p.rect(R(*m[1:]), None, BLEU, 1.0)
        if m[3] >= m[4]: p.line(P(m[1] + 0.05, m[2] + m[4] / 2), P(m[1] + m[3] - 0.05, m[2] + m[4] / 2), BLEU, 0.5, '[2 2] 0')
        else: p.line(P(m[1] + m[3] / 2, m[2] + 0.05), P(m[1] + m[3] / 2, m[2] + m[4] - 0.05), BLEU, 0.5, '[2 2] 0')
    p.txt(X(6.30), Y(5.18), 'penderie en U', 6.2, 'helv', BLEU)
    for m in (V.VASQUE, V.DOUCHE, V.WC): p.rect(R(*m[1:]), None, BLEU, 1.0)
    p.txt(X(5.66), Y(0.12), 'double vasque', 6.0, 'helv', BLEU, rot=90); p.txt(X(7.45), Y(0.92), 'douche', 6.2, 'helv', BLEU); p.txt(X(7.12), Y(0.30), 'fenêtre 100x60 :', 5.6, 'helv', BLEU); p.txt(X(7.12), Y(0.30) + 6.2, 'soufflet haut dépoli', 5.6, 'helv', BLEU)
    p.etiquette(7.2, 1.30 + 0.1, 'SDB', (W - 6.10) * SDB_Y); p.etiquette(5.2, 3.95, 'DRESSING', 4.06 * (D - Y_TOP) + 1.74 * Y_TOP)
    cadre(p, None)
    bande(p, 14, 600, 'LÉGENDE', ['Cadre orange : zone des modifications (deux chambres miroirs du R+1).', 'Bleu hachuré : mur ou cloison à construire (épaisseur 0.15).', 'Contour bleu : menuiserie, appareil ou agencement neuf.', 'Gris : existant conservé.', 'Mobilier libre non figuré (voir le projet final).'], 100)
    bande(p, 722, 600, 'CONSTRUCTIONS', ['1. Cloison nord de la salle de bain, 2.32 m, à 2.38 de la façade ; mur ouest prolongé de 0.75 m (rebouchage 0.57 et mur au-dessus de la porte déplacée à 1.55-2.35).', '2. Fermeture de la porte NE (0.90 x 2.20) en maçonnerie.', '3. Deux ouvertures dans la cloison centrale, 80x220 (côté façade) et 90x220 (côté nord), avec linteaux : on entre et on sort du dressing de chaque côté ; sans porte.', '4. Fenêtre du dressing 160x125, allège 0.95 (à la hauteur de la double vasque), tête 2.20, dans l\'ouverture de la baie est (162) : maçonnerie d\'allège 1.62 x 0.95 à construire.', '5. Fenêtre de la chambre : l\'ancienne fenêtre du WC ouest devient 100x125, allège 0.95 : partie basse fixe, partie haute à soufflet.', '6. Double vasque 1.40 contre le mur ouest de la salle de bain ; penderie en U limitée à la ligne rouge, sans îlot.', '7. Salle de bain : douche 1.20 x 1.00 et WC suspendu, sans vasque ; porte 80x220, vantail ouvert contre le mur nord.', 'POINTS DE L\'INGÉNIEUR : (a) cloison nord de la salle de bain parallèle aux nervures 12+8, à 0.55 de l\'ancienne : poutrelle doublée ou calcul de charge ; (b) linteaux neufs de la porte 1.55-2.35 et des deux ouvertures (sous C4 et B14), appuis de 0.20, joints de désolidarisation sous poutre ; (c) attentes de plomberie à relever sur site (WC déplacé, double vasque) ; (d) étanchéité sous faïence toute hauteur derrière la double vasque et la douche.'], 100)
    return p


# ---------------------------------------------------------------------------------------------------- version 3 : projet final
def meuble(p, m, kind):
    r = R(*m[1:]); x, y, l, h = m[1:]
    if kind == 'lit':                                                           # tête à l'est (contre la cloison centrale)
        p.rect(r, (1, 1, 1), NOIR, 0.6); p.rect(R(x + l - 0.44, y + 0.08, 0.40, 0.62), (1, 1, 1), NOIR, 0.48); p.rect(R(x + l - 0.44, y + h - 0.70, 0.40, 0.62), (1, 1, 1), NOIR, 0.48)
        p.line(P(x + l - 0.55, y + 0.05), P(x + l - 0.55, y + h - 0.05), NOIR, 0.48)
    elif kind == 'rect': p.rect(r, (1, 1, 1), NOIR, 0.6)
    elif kind == 'faut': p.rect(r, (1, 1, 1), NOIR, 0.6); p.rect(R(x + 0.08, y + 0.08, l - 0.16, h - 0.16), None, NOIR, 0.48)
    elif kind == 'rond': p.oval(r, (1, 1, 1), NOIR, 0.6)
    elif kind == 'tv': p.rect(r, (1, 1, 1), NOIR, 0.6); p.line(P(x + 0.08, y + 0.05), P(x + 0.08, y + h - 0.05), NOIR, 0.8)
    elif kind == 'pend':
        p.rect(r, (1, 1, 1), NOIR, 0.6)
        if l >= h: p.line(P(x + 0.05, y + h / 2), P(x + l - 0.05, y + h / 2), NOIR, 0.48, '[3 2] 0')
        else: p.line(P(x + l / 2, y + 0.05), P(x + l / 2, y + h - 0.05), NOIR, 0.48, '[3 2] 0')
    elif kind == 'douche':
        p.rect(r, (1, 1, 1), NOIR, 0.6); p.line(P(x, y), P(x + l, y + h), NOIR, 0.4); p.line(P(x, y + h), P(x + l, y), NOIR, 0.4); p.oval(R(x + l / 2 - 0.05, y + h / 2 - 0.05, 0.10, 0.10), (1, 1, 1))
    elif kind == 'wc':
        p.rect(R(x + 0.30, y, 0.25, h), (1, 1, 1), NOIR, 0.6); p.oval(R(x, y + 0.02, 0.38, h - 0.04), (1, 1, 1), NOIR, 0.6)
    elif kind == 'vasque2':
        p.rect(r, (1, 1, 1), NOIR, 0.6)
        for k in (0, 1): p.oval(R(x + 0.08, y + 0.08 + k * (h / 2), l - 0.18, h / 2 - 0.16), (1, 1, 1), NOIR, 0.48)


def v_final(doc, src):
    p = Pg(doc, src); cartouche(p, 'R+1 - PROJET FINAL', '018'); vider_zone(p); retirer_ss(p); chaines(p); fenetre_est(p, True)
    p.mur((4.06, V.OUV_S[1], 0.15, V.OUV_N[0] - V.OUV_S[1]), 'ex'); p.mur((5.95, 0, 0.15, 1.55), 'ex')                 # cloison centrale ; mur ouest de la salle de bain (une seule pièce, sans joint apparent)
    L = [(5.95, 2.35), (6.10, 2.35), (6.10, SDB_Y), (W, SDB_Y), (W, Y_TOP), (5.95, Y_TOP)]                              # mur au-dessus de la porte et mur nord de la salle de bain d'un seul tenant
    p.poly([P(*q) for q in L], NOIR, 0.84, None, GRIS, True)
    p.rect(R(4.06, 0.81, 0.15, 0.60), (0.5,) * 3, NOIR, 0.5); p.rect(R(7.22, D, 0.90, 0.15), GRIS, NOIR, 0.84)       # K1, porte NE fermée
    p.line(P(7.07, 1.00), P(W, 1.00), (0.2, 0.5, 0.9), 1.2)                                                           # paroi vitrée douche / WC
    p.arc(*V.PORTE_NO[:4], V.PORTE_NO[4]); p.arc(*V.PORTE_SDB[:4], V.PORTE_SDB[4])
    for m, k in ((V.LIT, 'lit'), (V.CHEV_S, 'rect'), (V.CHEV_N, 'rect'), (V.FAUT, 'faut'), (V.GUER, 'rond'), (V.COMM, 'rect'), (V.TV, 'tv'), (V.U_N, 'pend'), (V.U_E, 'pend'), (V.U_S, 'pend'), (V.VASQUE, 'vasque2'), (V.DOUCHE, 'douche'), (V.WC, 'wc')): meuble(p, m, k)
    p.txt(X(6.55), Y(5.35), 'penderie', 6.2, 'helv', (0.35,) * 3)
    p.etiquette(2.15, 4.35, 'CHAMBRE', 4.06 * D); p.etiquette(5.2, 3.95, 'DRESSING', 4.06 * (D - Y_TOP) + 1.74 * Y_TOP); p.etiquette(7.0, 1.55, 'SDB', (W - 6.10) * SDB_Y)
    cadre(p, None)
    bande(p, 14, 600, 'LÉGENDE', ['Cadre orange : zone des modifications (deux chambres miroirs du R+1 transformées en une suite parentale).', 'Parcours : chambre, dressing, salle de bain ; on entre et on sort du dressing par deux ouvertures de porte (0.80 côté façade, 0.90 côté nord).', 'Lumière et air naturels : fenêtre 160x125 pour le dressing, fenêtre 100x125 pour la chambre (bas fixe, haut à soufflet), fenêtre 100x60 à soufflet haut dépoli pour la salle de bain, au-dessus de la douche.'], 100)
    bande(p, 722, 600, 'SURFACES NETTES (m²)', ['Avant : 2 chambres de 18.18 et 2 toilettes de 3.97.', 'Après : chambre 22.94 ; dressing 17.07 (hall et penderie en U, allée centrale 1.92) ; salle de bain 5.16, avec WC et douche seulement.', 'Double vasque 1.40 contre le mur de la salle de bain, côté dressing : elle sert de lave-mains.', 'Pas d\'îlot : un îlot de 1.00 de large ne laisse pas 0.90 de passage de chaque côté.', 'Écart au standard : fenêtre de chambre de 100 de large (standard 140 ou 160), conservée à la demande du client ; lue comme 100x125, allège 0.95 (une lecture jusqu\'au sol est possible).', 'Deux ouvertures sans porte (80x220 et 90x220) : intimité du lit et de la salle de bain à traiter si besoin. Baie ouest : porte-fenêtre coulissante, conservée.', 'Le WC n\'est pas en cabinet fermé (pièce de 2.17 x 2.38).', 'Cotes en mètres. Plan sous réserve du relevé des attentes sur site et du visa de l\'ingénieur de structure.'], 100)
    return p


def construire():
    src = pymupdf.open(SRC); doc = pymupdf.open()
    v_demolitions(doc, src); v_constructions(doc, src); v_final(doc, src)
    doc.set_metadata({'title': 'MBAO - R+1 - Suite parentale - demolitions, constructions, projet final', 'author': 'D&F ENGINEERING'})
    doc.save(OUT, deflate=True, garbage=3)
    ap = os.path.join(HERE, 'apercus', 'pdf'); os.makedirs(ap, exist_ok=True)
    for i, pg in enumerate(doc): pg.get_pixmap(dpi=100).save(os.path.join(ap, 'page%d.png' % (i + 1)))
    return OUT


if __name__ == '__main__':
    print(construire())
