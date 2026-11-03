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
XM, XE_M = V.XM, V.XE_M                                  # faces du mur ouest de la salle de bain (existant, relevé sur le plan source)
XC = 4.059                                               # face ouest de la cloison centrale (relevé)
NE0, NE1 = B.PORTE_NE                                    # montants de la porte NE dans la bande du mur nord (relevé)
S_CH = (XC * D); S_DR = (W - 4.209) * (D - Y_TOP) + (XM - 4.209) * Y_TOP; S_SDB = (W - XE_M) * SDB_Y
sys.path.insert(0, '/home/user/atelier-archi-ingenierie/outils'); import controle_raccords as CR
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

    def effacer(self, rects, traits=False):
        """Supprime le TEXTE d'origine sous ces zones (pas de texte caché dans le PDF), sans fond blanc : les murs dessous restent.
        traits=True supprime aussi les petits tracés vectoriels ENTIÈREMENT contenus dans la zone (tick de cote, symbole de porte) ; un tracé qui dépasse
        (trait de mur, grand chemin de murs) n'est jamais touché."""
        for r in rects: self.pg.add_redact_annot(r, fill=False)
        self.pg.apply_redactions(images=0, graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED if traits else 0)

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

    def arc(self, ch, r, a0, a1, ouvert, color=NOIR, ymin=None):
        """Arc et vantail d'une porte ; ymin (pt) : le tracé reste sous cette ordonnée (la partie dans l'épaisseur du mur est celle de la source)."""
        pts = [P(ch[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / 48)), ch[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / 48))) for i in range(49)]
        if ymin is not None: pts = [q for q in pts if q.y >= ymin]
        self.poly(pts, color, 0.6 if ymin is not None else 0.48)
        d0 = P(*ch); d1 = P(ch[0] + r * math.cos(math.radians(ouvert)), ch[1] + r * math.sin(math.radians(ouvert)))
        if ymin is not None: d0 = pymupdf.Point(d0.x, max(d0.y, ymin))
        self.line(d0, d1, color, 0.6 if ymin is not None else 0.84)       # porte de la source : vantail et arc à 0.6

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
CADRE = pymupdf.Rect(143, 561, 706, 1012)


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
        l = l.replace('{CH}', '%.2f' % S_CH).replace('{DR}', '%.2f' % S_DR).replace('{SDB}', '%.2f' % S_SDB)
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
    """Efface l'intérieur de la zone (cloisons, mobilier, textes, cotes de chaîne) ; murs extérieurs, balcon et chaînes du bas restent. Textes et petits tracés
    périmés ont déjà été SUPPRIMÉS dans le fond (base_preparee) ; les caches blancs ne couvrent plus que le reste du dessin d'origine."""
    p.blanc(pymupdf.Rect(191.0, 580.25, 659.0, 898.4))
    p.blanc(pymupdf.Rect(142, 586, 181.5, 892.5)); p.blanc(pymupdf.Rect(669, 586, 704, 892.5))
    p.line(pymupdf.Point(313.92, 898.8), pymupdf.Point(322.44, 898.8), NOIR, 0.84)                               # trait de la face intérieure de la façade, coupé par l'ancienne cloison du WC ouest
    p.blanc(pymupdf.Rect(431.4, 899.4, 522.9, 906.6))                               # symbole de la baie est : l'ouverture seulement, murs et piliers de façade intacts




def base_preparee():
    """Copie du plan source (page 15) dont les textes périmés de la zone et les petits tracés périmés (ticks de cotes orphelins, symbole de la porte NE) sont SUPPRIMÉS
    du vectoriel : ils ne sont pas seulement cachés. Sert de fond aux pages 2 et 3."""
    doc = pymupdf.open(SRC); pg = doc[14]
    for r in ZONES_ERASE: pg.add_redact_annot(r, fill=False)
    pg.apply_redactions(images=0, graphics=0)                                               # texte seulement
    for r in rects_orphelins() + [pymupdf.Rect(598, 570.5, 656, 581.0)]:                    # une zone à la fois : des zones qui se recouvrent se gênent (vérifié)
        pg.add_redact_annot(r, fill=False); pg.apply_redactions(images=0, graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED)   # tracés entièrement contenus dans la zone seulement
    import tempfile
    chemin = os.path.join(tempfile.gettempdir(), 'mbao_base_preparee.pdf'); doc.save(chemin); doc.close()
    return pymupdf.open(chemin)                                                               # nom de fichier distinct : PyMuPDF ne réutilise pas le fond de la page 1 pour les pages 2 et 3


def rects_orphelins():
    """Boîtes des chemins vectoriels de la source qui portent un tick de cote orphelin dans les bandes des murs ouest et est (cotes périmées : 1.24, 4.06, 2.18...).
    Le chemin entier est supprimé, sinon la moitié du tick restée dans le mur subsiste (RAC-010)."""
    out = []
    with pymupdf.open(SRC) as s:
        for dr in s[14].get_drawings():
            r = dr['rect']
            if r.width > 320 or r.height > 320: continue                                  # jamais un grand chemin (murs, cadre)
            for it in dr['items']:
                if it[0] != 'l' or (dr.get('width') or 0) < 0.7: continue
                a, b = it[1], it[2]; dx, dy = abs(a.x - b.x), abs(a.y - b.y)
                if dx < 0.5 or dy < 0.5 or (dx * dx + dy * dy) ** 0.5 > 6.0: continue
                c = ((a.x + b.x) / 2, (a.y + b.y) / 2)
                if any(z[0] <= c[0] <= z[2] and z[1] <= c[1] <= z[3] for z in BANDES_MURS):
                    out.append(pymupdf.Rect(r.x0 - 1.0, r.y0 - 1.0, r.x1 + 1.0, r.y1 + 1.0)); break      # marge >= demi-trait : PyMuPDF compare la boîte avec l'épaisseur du trait
    return out + CR.cotes_perimees(SRC, 14, BANDES_TOUS, (193, 583, 657, 897))


def traits_face(p):
    """Traits de face des murs extérieurs rendus CONTINUS là où une ancienne cloison les interrompait dans la source (RAC-010)."""
    for a, b in (((190.6, 786.0), (190.6, 796.0)), ((659.4, 786.0), (659.4, 796.0))): p.line(pymupdf.Point(*a), pymupdf.Point(*b), NOIR, 0.84)      # murs ouest et est
    for x0, x1 in ((313.4, 322.9), (420.2, 429.7)): p.line(pymupdf.Point(x0, 898.8), pymupdf.Point(x1, 898.8), NOIR, 0.84)                          # façade
    for x0, x1 in ((260.1, 266.8), (420.2, 429.7), (583.4, 590.0)): p.line(pymupdf.Point(x0, 579.8), pymupdf.Point(x1, 579.8), NOIR, 0.84)          # mur nord


def retirer_ss(p):
    """Les repères « SS » des anciens WC sont effacés comme texte par vider_zone ; rien n'est redessiné sur la façade."""
    return


def chaines(p):
    """Chaînes verticales gauche et droite : même ligne que la source (x 158.28 et 688.44, trait 0.84). Seuls les segments du milieu sont refaits ;
    les segments de l'épaisseur du mur nord et de la façade et leurs traits obliques restent ceux de la source."""
    for xl, xt, droite in ((158.28, 150.5, False), (688.44, 680.5, True)):
        seg = [('%.2f' % D, D, 0.0)] if not droite else [('%.2f' % (D - Y_TOP), D, Y_TOP), ('0.15', Y_TOP, SDB_Y), ('%.2f' % SDB_Y, SDB_Y, 0.0)]
        xw = 182.0 if not droite else 667.9
        for t_, a, b in seg:
            p.line(pymupdf.Point(xl, Y(a)), pymupdf.Point(xl, Y(b)), NOIR, 0.84)
            for yy in (a, b):
                if abs(yy - D) < 1e-9 or abs(yy) < 1e-9: continue                  # traits aux extrémités : ceux de la source
                p.line(pymupdf.Point(xl - 3, Y(yy) + 3), pymupdf.Point(xl + 3, Y(yy) - 3), NOIR, 0.7)
                p.line(pymupdf.Point(xl, Y(yy)), pymupdf.Point(xw - (2 if not droite else -2), Y(yy)), NOIR, 0.48)
            mid = (Y(a) + Y(b)) / 2; tl = pymupdf.get_text_length(t_, 'heit', 10.6)
            p.blanc(pymupdf.Rect(xt - 7, mid - tl / 2 - 1, xt + 6, mid + tl / 2 + 1)); p.txt(xt + 4, mid + tl / 2, t_, 10.6, 'heit', rot=90)


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
    p.mur((XM, 1.84, 0.15, 1.975 - 1.84), 'demol')                                                                  # retour du mur ouest du WC est
    p.mur((XC, V.OUV_S[0], 0.15, V.OUV_S[1] - V.OUV_S[0]), 'demol')                                         # ouverture côté façade (cloison centrale)
    p.mur((XC, V.OUV_N[0], 0.15, V.OUV_N[1] - V.OUV_N[0]), 'demol')                                         # ouverture côté nord
    p.mur(B.STUB_O, 'demol'); p.mur(B.STUB_E, 'demol')                                                        # petits murs de l'ancien dressing
    for r in (R(*B.PLACARD_O), R(*B.PLACARD_E)): p.rect(r, None, ROUGE, 1.0, '[3 2] 0')                      # placards coulissants
    p.txt(X(1.75), Y(5.30), 'placard à déposer', 6.8, 'helv', ROUGE); p.txt(X(4.95), Y(5.30), 'placard à déposer', 6.8, 'helv', ROUGE)
    for r in ((0.0, 0.6, 0.6, 0.85), (1.50, 0.0, 0.70, 0.55), (7.65, 0.6, 0.62, 0.85), (6.1, 0.0, 0.70, 0.55)): p.rect(R(*r), None, ROUGE, 1.0, '[3 2] 0')   # sanitaires
    p.txt(X(0.10), Y(2.35), 'appareils sanitaires', 6.2, 'helv', ROUGE); p.txt(X(0.10), Y(2.35) + 7, 'à déposer', 6.2, 'helv', ROUGE)
    for r in ((2.175, 0.98, 0.151, 0.86), (XM, 0.98, 0.15, 0.86), (NE0, D, NE1 - NE0, 0.15), (4.245, -0.15, 1.62, 0.15), (0.20, -0.15, 1.00, 0.15)): p.rect(R(*r), None, ROUGE, 1.1, '[3 2] 0')   # portes des WC, porte NE, baie est, fenêtre du WC ouest
    p.txt(X(7.20), Y(4.62), 'porte NE à déposer', 6.2, 'helv', ROUGE)
    p.txt(X(4.32), Y(0.45), 'baie est à déposer', 6.4, 'helv', ROUGE)
    p.txt(X(0.68), Y(0.32), 'allège à démolir', 5.6, 'helv', ROUGE); p.txt(X(0.68), Y(0.32) + 6.5, '(1.60 à 0.95)', 5.6, 'helv', ROUGE)
    bande(p, 14, 600, 'LÉGENDE', ['Cadre orange : zone des modifications (deux chambres miroirs du R+1).', 'Hachures rouges : cloison ou mur à démolir.', 'Pointillé rouge : élément à déposer (placard, sanitaire, porte, baie, allège).', 'Gris : existant conservé.', 'Les poteaux, les poutres et les dalles ne sont pas touchés.'], 100)
    bande(p, 722, 600, 'DÉMOLITIONS', ['1. Cloison nord du WC ouest, 2.32 m.', '2. Cloison est du WC ouest, 1.98 m.', '3. Cloison nord du WC est, 2.32 m ; petit retour du mur ouest, 0.14 m.', '4. Deux ouvertures de porte dans la cloison centrale (non porteuse, sous la poutre B14) : côté façade 0.80 m (sous la poutre C4), côté nord 0.90 m (sous la poutre B14), hauteur 2.20, linteaux à prévoir.', '5. Deux petits murs de l\'ancien dressing : 0.62 m chacun.', '6. Placards coulissants des deux chambres.', '7. Appareils sanitaires, deux portes de WC, porte NE, baie est de façade ; repères « SS » des anciens WC supprimés au projet (pages 2 et 3).', '8. Allège de la fenêtre du WC ouest, de 1.60 à 0.95 (fenêtre agrandie).', 'POINT DE L\'INGÉNIEUR : sur le coffrage du plancher haut, des bandes hachurées passent au droit des cloisons des WC : nature à confirmer avant la démolition.'], 100)
    return p


# ---------------------------------------------------------------------------------------------------- version 2 : constructions
def v_constructions(doc, src):
    p = Pg(doc, src); cartouche(p, 'R+1 - CONSTRUCTIONS', '017'); vider_zone(p); traits_face(p); retirer_ss(p); chaines(p); fenetre_est(p, False)
    for m in CONSERVES: p.mur(m, 'ex')
    p.rect(R(XC, 1.027, 0.15, 0.15), (0.5,) * 3, NOIR, 0.5)                                                  # poteau K1 : même marque que sur le plan source
    for m in NEUFS: p.mur(m, 'neuf')                                                                         # tous les murs neufs, y compris la fermeture de la porte NE alignée sur le mur nord
    p.txt(X(NE0) - 6, 570.2, 'fermeture porte NE', 6.0, 'helv', BLEU)
    # ouvertures de la cloison centrale, fenêtre de la chambre, menuiseries et appareils neufs (bleu)
    for (a, b), nom in ((V.OUV_S, 'ouv. 80x220'), (V.OUV_N, 'ouv. 90x220')):
        p.rect(clip_int(R(XC, a, 0.15, b - a)), None, BLEU, 0.6, '[3 2] 0'); p.txt(X(4.36), Y(a) - 2, nom, 5.8, 'helv', BLEU, rot=90)
    p.arc(*V.PORTE_SDB[:4], V.PORTE_SDB[4], BLEU); p.arc(*V.PORTE_NO[:4], V.PORTE_NO[4], ymin=580.0)
    p.rect(R(XE_M, SDB_Y - 0.052, 0.80, 0.034), None, BLEU, 0.48)
    p.rect(R(0.20, -0.15, 1.00, 0.15), None, BLEU, 1.1, '[3 2] 0'); p.txt(X(0.25), Y(0.30), 'fenêtre 100x125, allège 0.95', 5.8, 'helv', BLEU); p.txt(X(0.25), Y(0.30) + 7, 'bas fixe, haut à soufflet', 5.8, 'helv', BLEU)
    for m in (V.U_N, V.U_E, V.U_S):
        p.rect(clip_int(R(*m[1:])), None, BLEU, 0.6)
        if m[3] >= m[4]: p.line(P(m[1] + 0.05, m[2] + m[4] / 2), P(m[1] + m[3] - 0.05, m[2] + m[4] / 2), BLEU, 0.5, '[2 2] 0')
        else: p.line(P(m[1] + m[3] / 2, m[2] + 0.05), P(m[1] + m[3] / 2, m[2] + m[4] - 0.05), BLEU, 0.5, '[2 2] 0')
    p.txt(X(6.30), Y(5.18), 'penderie en U', 6.2, 'helv', BLEU)
    for m in (V.VASQUE, V.DOUCHE, V.WC): p.rect(clip_int(R(*m[1:])), None, BLEU, 0.6)
    p.txt(X(5.66), Y(0.12), 'double vasque', 6.0, 'helv', BLEU, rot=90); p.txt(X(7.50), Y(0.74), 'douche', 6.2, 'helv', BLEU); p.txt(X(7.12), Y(0.30), 'fenêtre 100x60 :', 5.6, 'helv', BLEU); p.txt(X(7.12), Y(0.30) + 6.2, 'soufflet haut dépoli', 5.6, 'helv', BLEU)
    p.etiquette(7.2, 1.30 + 0.1, 'SDB', S_SDB); p.etiquette(5.2, 3.95, 'DRESSING', S_DR)
    cadre(p, None)
    bande(p, 14, 600, 'LÉGENDE', ['Cadre orange : zone des modifications (deux chambres miroirs du R+1).', 'Bleu hachuré : MUR ou cloison neuf (épaisseur 0.15).', 'Contour bleu : menuiserie, appareil ou agencement neuf (pas un mur).', 'Gris : existant conservé.', 'Mobilier libre non figuré (voir le projet final).'], 100)
    bande(p, 722, 600, 'CONSTRUCTIONS', ['1. Cloison nord de la salle de bain, 2.32 m, à 2.38 de la façade ; mur ouest prolongé de 0.60 m (rebouchage de 0.60 ; porte déplacée à 1.58-2.38, jambage dans le prolongement du mur nord).', '2. Fermeture de la porte NE (0.90 x 2.20) en maçonnerie.', '3. Deux ouvertures dans la cloison centrale, 80x220 (côté façade) et 90x220 (côté nord), avec linteaux : on entre et on sort du dressing de chaque côté ; sans porte.', '4. Fenêtre du dressing 160x125, allège 0.95 (à la hauteur de la double vasque), tête 2.20, dans l\'ouverture de la baie est (162) : maçonnerie d\'allège 1.62 x 0.95 à construire.', '5. Fenêtre de la chambre : l\'ancienne fenêtre du WC ouest devient 100x125, allège 0.95 : partie basse fixe, partie haute à soufflet.', '6. Double vasque 1.40 contre le mur ouest de la salle de bain ; penderie en U limitée à la ligne rouge, sans îlot.', '7. Salle de bain : douche 1.20 x 1.00 et WC suspendu, sans vasque ; porte 80x220, vantail ouvert contre le mur nord.', 'POINTS DE L\'INGÉNIEUR : (a) cloison nord de la salle de bain parallèle aux nervures 12+8, à 0.55 de l\'ancienne : poutrelle doublée ou calcul de charge ; (b) linteaux neufs de la porte 1.55-2.35 et des deux ouvertures (sous C4 et B14), appuis de 0.20, joints de désolidarisation sous poutre ; (c) attentes de plomberie à relever sur site (WC déplacé, double vasque) ; (d) étanchéité sous faïence toute hauteur derrière la double vasque et la douche.'], 100)
    return p


# ---------------------------------------------------------------------------------------------------- version 3 : projet final
def clip_int(r):
    """Un élément ne recouvre jamais le trait d'un mur : bords rentrés à l'intérieur de la pièce."""
    return pymupdf.Rect(max(r.x0, 191.3), max(r.y0, 580.5), min(r.x1, 658.7), min(r.y1, 898.1))


def meuble(p, m, kind):
    r = R(*m[1:]); x, y, l, h = m[1:]
    r = clip_int(r)
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
    p = Pg(doc, src); cartouche(p, 'R+1 - PROJET FINAL', '018'); vider_zone(p); traits_face(p); retirer_ss(p); chaines(p); fenetre_est(p, True)
    p.mur((XC, V.OUV_S[1], 0.15, V.OUV_N[0] - V.OUV_S[1]), 'ex'); p.mur((XM, 0, 0.15, 1.58), 'ex')                      # cloison centrale ; mur ouest de la salle de bain (une seule pièce, sans joint apparent)
    p.mur((XM, SDB_Y, W - XM, 0.15), 'ex')                                                                                # mur nord de la salle de bain d'un seul tenant
    p.rect(R(XC, 1.027, 0.15, 0.15), (0.5,) * 3, NOIR, 0.5); fermer_porte_ne(p)                                      # K1 (marque du plan source), porte NE fermée dans le prolongement exact du mur nord
    for dy in (0.0, 1.0): p.line(pymupdf.Point(X(7.07), Y(1.00) + dy), pymupdf.Point(X(W) - 0.7, Y(1.00) + dy), NOIR, 0.5)   # paroi vitrée douche / WC : double trait fin, en noir comme le reste de la page
    p.arc(*V.PORTE_NO[:4], V.PORTE_NO[4], ymin=580.0); p.arc(*V.PORTE_SDB[:4], V.PORTE_SDB[4])
    p.rect(R(XE_M, SDB_Y - 0.052, 0.80, 0.034), (1, 1, 1), NOIR, 0.48)                                             # vantail de la salle de bain ouvert à plat contre le mur nord (épaisseur 0.034)
    for m, k in ((V.LIT, 'lit'), (V.CHEV_S, 'rect'), (V.CHEV_N, 'rect'), (V.FAUT, 'faut'), (V.GUER, 'rond'), (V.COMM, 'rect'), (V.TV, 'tv'), (V.U_N, 'pend'), (V.U_E, 'pend'), (V.U_S, 'pend'), (V.VASQUE, 'vasque2'), (V.DOUCHE, 'douche'), (V.WC, 'wc')): meuble(p, m, k)
    p.txt(X(6.55), Y(5.46), 'penderie', 6.2, 'helv', (0.35,) * 3)
    p.etiquette(2.15, 4.35, 'CHAMBRE', S_CH); p.etiquette(5.2, 3.95, 'DRESSING', S_DR); p.etiquette(7.0, 1.55, 'SDB', S_SDB)
    cadre(p, None)
    bande(p, 14, 600, 'LÉGENDE', ['Cadre orange : zone des modifications (deux chambres miroirs du R+1 transformées en une suite parentale).', 'Parcours : chambre, dressing, salle de bain ; on entre et on sort du dressing par deux ouvertures de porte (0.80 côté façade, 0.90 côté nord).', 'Lumière et air naturels : fenêtre 160x125 pour le dressing, fenêtre 100x125 pour la chambre (bas fixe, haut à soufflet), fenêtre 100x60 à soufflet haut dépoli pour la salle de bain, au-dessus de la douche.'], 100)
    bande(p, 722, 600, 'SURFACES NETTES (m²)', ['Avant : 2 chambres de 18.18 et 2 toilettes de 3.97.', 'Après : chambre {CH} ; dressing {DR} (hall et penderie en U, allée centrale 1.92) ; salle de bain {SDB}, avec WC et douche seulement.', 'Double vasque 1.40 contre le mur de la salle de bain, côté dressing : elle sert de lave-mains.', 'Pas d\'îlot : un îlot de 1.00 de large ne laisse pas 0.90 de passage de chaque côté.', 'Écart au standard : fenêtre de chambre de 100 de large (standard 140 ou 160), conservée à la demande du client ; lue comme 100x125, allège 0.95 (une lecture jusqu\'au sol est possible).', 'Deux ouvertures sans porte (80x220 et 90x220) : intimité du lit et de la salle de bain à traiter si besoin. Baie ouest : porte-fenêtre coulissante, conservée.', 'Le WC n\'est pas en cabinet fermé (pièce de 2.17 x 2.38).', 'Cotes en mètres. Plan sous réserve du relevé des attentes sur site et du visa de l\'ingénieur de structure.'], 100)
    return p


# ---------------------------------------------------------------------------------------------------- murs et contrôles des raccords
CONSERVES = [(XC, V.OUV_S[1], 0.15, V.OUV_N[0] - V.OUV_S[1]), (XM, 0.0, 0.15, 0.98)]                         # cloison centrale entre les ouvertures ; pied du mur ouest de la salle de bain
NEUFS = [(XM, 0.98, 0.15, 0.60), (XM, SDB_Y, W - XM, 0.15), (NE0, D, NE1 - NE0, 0.15)]   # rebouchage, mur nord de la SDB, fermeture NE
LIBRES = [(XC + 0.075, V.OUV_S[1]), (XC + 0.075, V.OUV_N[0]), (XM + 0.075, 1.58), (XM, SDB_Y + 0.075)]       # jambages d'ouverture : extrémités libres voulues


def fermer_porte_ne(p):
    """Fermeture de la porte NE dans le prolongement EXACT du mur nord (mêmes faces, même épaisseur, mêmes traits de bord que la source)."""
    r = R(NE0, D, NE1 - NE0, 0.15); e = 1.5
    p.rect(pymupdf.Rect(r.x0 - e, r.y0, r.x1 + e, r.y1), GRIS, None, 0)
    for yy in (r.y0, r.y1): p.line(pymupdf.Point(r.x0 - e - 0.5, yy), pymupdf.Point(r.x1 + e + 0.5, yy), NOIR, 0.84)


def murs_source():
    """Murs et poteaux EXTÉRIEURS de la source (appuis des raccords), relevés dans le vectoriel de la page 15, en mètres (x, y, l, h)."""
    out = []; Z = pymupdf.Rect(150, 560, 700, 1010)
    with pymupdf.open(SRC) as s:
        for dr in s[14].get_drawings():
            f = dr.get('fill')
            for it in dr['items']:
                r = it[1] if it[0] == 're' else (it[1].rect if it[0] == 'qu' else None)
                if r is None or not Z.intersects(r) or not f or r.width < 1 or r.height < 1 or not (abs(f[0] - 0.75) < 0.01 or abs(f[0] - 0.5) < 0.01): continue
                m = ((r.x0 - X0) / K, (Y0 - r.y1) / K, r.width / K, r.height / K)
                if m[1] + m[3] <= 0.001 or m[1] >= D - 0.01 or m[0] + m[2] <= 0.001 or m[0] >= W - 0.001: out.append(m)   # façade, mur nord, murs ouest et est
    return out


def murs_source_tous():
    with pymupdf.open(SRC) as s:
        out = []
        for dr in s[14].get_drawings():
            f = dr.get('fill')
            for it in dr['items']:
                r = it[1] if it[0] == 're' else (it[1].rect if it[0] == 'qu' else None)
                if r is not None and pymupdf.Rect(150, 560, 700, 1010).intersects(r) and f and abs(f[0] - 0.75) < 0.01 and r.width > 1 and r.height > 1: out.append(((r.x0 - X0) / K, (Y0 - r.y1) / K, r.width / K, r.height / K))
    return out


# zones où le dessin a le DROIT de différer de la source (points) : intérieur de la zone, chaînes refaites, ouvertures modifiées, cadre orange, légendes, cartouche
ZONES_ERASE = [(191.0, 580.25, 659.0, 898.4), (142, 586, 181.5, 892.5), (669, 586, 704, 892.5), (315, 897.5, 335, 912), (541, 897.5, 561, 912)]
BANDES_MURS = [(182, 585, 193, 893), (657, 585, 668, 893)]
BANDES_TOUS = BANDES_MURS + [(190, 568, 668, 583), (190, 897, 660, 909)]                    # + bande du mur nord et bande de façade                                  # bandes des murs ouest et est : plus aucun tick de cote orphelin
ZONES_OK = ZONES_ERASE + [(r.x0, r.y0, r.x1, r.y1) for r in rects_orphelins()] + [(186, 784, 196, 798), (653, 784, 665, 798), (418, 896.5, 432, 901), (258, 577.5, 268, 582), (418, 577.5, 432, 582), (581, 577.5, 592, 582), (596, 569, 658, 583),
                          (X(0.20) - 2, 897, X(1.20) + 2, 909), (141, 575, 183, 900), (668, 575, 705, 900),
                          (431.4, 899.4, 522.9, 906.6), (R(NE0, D, NE1 - NE0, 0.15).x0 - 2, 569.5, R(NE0, D, NE1 - NE0, 0.15).x1 + 2, 581.5),
                          (141, 549, 708, 570), (141, 1008, 708, 1016), (141, 549, 147, 1016), (702, 549, 708, 1016), (10, 590, 132, 1010), (715, 590, 836, 1010), (404, 1064, 614, 1129)]


def controler_raccords(chemin):
    """Raccords des murs neufs, fidélité hors zones modifiées et texte d'origine périmé : toute anomalie est renvoyée (liste vide = conforme)."""
    err = ['MURS : ' + e for e in CR.raccords_murs(CONSERVES, NEUFS, appuis=murs_source(), libres=LIBRES, source=murs_source_tous())]
    for page in (1, 2):
        for b in CR._fidelite(SRC, 14, chemin, page, ZONES_OK, 200, 40, 1.0): err.append('PAGE %d : différence avec la source hors zone modifiée, boîte (pt) %s' % (page + 1, b))
        for w in CR.texte_perime(SRC, 14, chemin, page, ZONES_ERASE): err.append('PAGE %d : texte d\'origine périmé encore extractible %s' % (page + 1, w))
    faces = [('mur ouest', (X0, Y(D)), (X0, Y0), []), ('mur est', (X(W), Y(D)), (X(W), Y0), []), ('façade', (X0, Y0), (X(W), Y0), []),
             ('mur nord', (X0, Y(D)), (X(W), Y(D)), [(X(0.095), X(1.041))])]                                           # seule coupure voulue : la porte d'entrée NO
    for page in (1, 2):
        for c in CR.continuite_traits(chemin, page, faces): err.append('PAGE %d : trait de face coupé (%s) de %.1f à %.1f pt' % ((page + 1,) + c))
        for c in CR.traits_parasites(chemin, page, BANDES_MURS): err.append('PAGE %d : tick de cote orphelin en %s' % (page + 1, c))
        for c in CR.cotes_perimees(chemin, page, BANDES_TOUS, (193, 583, 657, 897)): err.append('PAGE %d : ancienne cote encore visible dans un mur, boîte (pt) %s' % (page + 1, tuple(round(v, 1) for v in c)))
    return err


def construire():
    src = pymupdf.open(SRC); base = base_preparee(); doc = pymupdf.open()
    v_demolitions(doc, src); v_constructions(doc, base); v_final(doc, base)
    doc.set_metadata({'title': 'MBAO - R+1 - Suite parentale - demolitions, constructions, projet final', 'author': 'D&F ENGINEERING'})
    doc.save(OUT, deflate=True, garbage=3)
    global ERR
    err = ERR = controler_raccords(OUT)
    for e in err: print('RACCORD :', e)
    print('contrôle des raccords :', 'CONFORME' if not err else '%d anomalie(s)' % len(err))
    ap = os.path.join(HERE, 'apercus', 'pdf'); os.makedirs(ap, exist_ok=True)
    for i, pg in enumerate(doc): pg.get_pixmap(dpi=100).save(os.path.join(ap, 'page%d.png' % (i + 1)))
    return OUT


ERR = []

if __name__ == '__main__':
    construire()
    sys.exit(1 if ERR else 0)
