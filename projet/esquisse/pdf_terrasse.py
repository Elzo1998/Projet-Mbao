"""MBAO - plan TERRASSE (C-013) : cuisine fermée, nouvelle toilette, bac lessive / vaisselle. Page 1 = plan, page 2 = tableaux.

python3 -I projet/esquisse/pdf_terrasse.py   ->  projet/livrables/MBAO_Terrasse_indiceC_FINAL.pdf (+ aperçus PNG dans apercus/terrasse/)

Fond = page 17 (index 16) de PROJET_MBAO_Architecture_V2.pdf (vectoriel, 1:50, charte D&F : murs gris 0.75, faces noires 2.52, cotes 0.72).
Tout est RELEVÉ sur le vectoriel (RAC-007) : échelle 51.5 pt/m (cuisine 271.92 pt = 5.28 m ; murs extérieurs 441.6 pt = 8.57 m), mur 7.68 pt.
Les coordonnées client (REPRISE.md, mètres depuis l'angle extérieur NO) sont converties avec ce repère.
Sort en erreur (code 1) s'il reste une anomalie de raccord.
"""
import math, os, sys
import pymupdf
from shapely.geometry import Polygon, box
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), 'source', 'PROJET_MBAO_Architecture_V2.pdf')
OUT = os.path.join(os.path.dirname(HERE), 'livrables', 'MBAO_Terrasse_indiceC_FINAL.pdf')
PG = 16
sys.path.insert(0, '/home/user/atelier-archi-ingenierie/outils'); import controle_raccords as CR

# ------------------------------------------------------------------ relevé sur le vectoriel (points) et conversion
K = 51.5                                    # pt par m (relevé : 271.92 pt = 5.28 m)
OX, OY = 211.56, 132.60                     # angle extérieur nord-ouest
EP = 7.68                                   # épaisseur des murs (0.15)
XW_I, XE_I = 219.24, 645.48                 # faces intérieures des murs ouest et est
XC0, XC1 = 491.16, 498.84                   # mur est de la cuisine (existant jusqu'à y 324.12) ; face est de l'escalier
YN_I = 140.28                               # face intérieure du mur nord
YH0, YH1 = 316.44, 324.12                   # mur horizontal existant (nord de la toilette)
YE0, YE1 = 389.28, 397.08                   # mur nord de l'escalier (sud de la cuisine)
YS0, YS1 = 510.48, 518.16                   # mur sud de l'escalier
YB_I = 868.08                               # face intérieure du mur sud de la terrasse
GRIS, NOIR, BLANC = (0.75,) * 3, (0, 0, 0), (1, 1, 1)
W_FACE, W_COTE, W_DET = 2.52, 0.72, 0.6     # traits de la source : faces des murs, cotes, détails (portes)


def M(x, y): return ((x - OX) / K, (y - OY) / K)


# ------------------------------------------------------------------ données du projet (mètres client -> points)
FEN_C = (OY + 0.75 * K, OY + 2.75 * K)                      # fenêtre cuisine 2.00 x 1.25 dans le mur est (y 0.75 à 2.75)
PW = 48.72                                                   # largeur d'ouverture de la porte existante de l'escalier (relevé : 228.36 à 277.08 = 0.95)
POR_C = (OX + 0.30 * K, OX + 0.30 * K + PW)                      # porte cuisine 0.90 x 2.20 dans le mur sud (x 0.30 à 1.20)
FEN_T = (XC1 + 1.62 * K, XC1 + 2.62 * K)                    # fenêtre toilette 1.00 x 0.60 dans le mur nord (1.62 de l'angle ouest)
POR_T = (XC1, XC1 + PW)                               # porte toilette 0.90 x 2.20 dans le mur sud, côté ouest (réponse client 05/11)
WT = 0.60 * K                                                # profondeur du plan de travail
Y_FR = YE0 - 0.70 * K                                        # haut du frigo 0.70 x 0.70 (angle sud-est)
HOB_X0 = XW_I + 2.00 * K                                     # plaque 0.60 : axe à 2.30 de la face ouest
BAC = (XE_I - 1.87 * K, YE1, XE_I, YE1 + 1.10 * K)          # bac 1.87 x 1.10, contre le mur sud de la toilette, collé au mur est ; h 0.40


# ------------------------------------------------------------------ surfaces et périmètres
def pieces():
    cu = (5.28, 4.83); to = (2.85, 1.26); esc = (5.28, 2.20)
    terr = Polygon([(XW_I, YS1), (XC1, YS1), (XC1, YE1), (XE_I, YE1), (XE_I, YB_I), (XW_I, YB_I)])
    # terrasse = surface libre de murs, bac compris ; polygone en mètres
    tm = Polygon([M(*p) for p in terr.exterior.coords])
    bac_s = 1.87 * 1.10
    return [
        ('CUISINE', '%.2f x %.2f' % cu, cu[0] * cu[1], 2 * (cu[0] + cu[1])),
        ('TOILETTE', '%.2f x %.2f' % to, to[0] * to[1], 2 * (to[0] + to[1])),
        ('ESC', '%.2f x %.2f' % esc, 11.61, 2 * (esc[0] + esc[1])),
        ('TERRASSE', 'forme en L (voir plan)', tm.area, tm.length),
    ], bac_s, 2 * (1.87 + 1.10)


S_TERRASSE = pieces()[0][3][2]
def fmt(v): return '%.2f' % v


# ------------------------------------------------------------------ murs (x0, y0, x1, y1) en points : source, conservés, neufs
def m_pt_to_m(r): return ((r[0] - OX) / K, (r[1] - OY) / K, (r[2] - r[0]) / K, (r[3] - r[1]) / K)


NEUF_W1 = (XC0, YH1, XC1, YE0)                              # mur ouest de la toilette = fermeture est de la cuisine
NEUF_W2 = (POR_T[1], YE0, XE_I, YE1)                        # mur sud de la toilette, de la porte au mur est
# conservés : tronçons des murs existants entre les ouvertures (fenêtres, porte cuisine)
CONSERVES = [(XC0, YN_I, XC1, FEN_C[0]), (XC0, FEN_C[1], XC1, YH0),                       # mur est de la cuisine de part et d'autre de la fenêtre
             (XC1, YH0, FEN_T[0], YH1), (FEN_T[1], YH0, XE_I, YH1),                       # mur nord de la toilette de part et d'autre de la fenêtre
             (OX, YE0, POR_C[0], YE1), (POR_C[1], YE0, XC0, YE1)]                          # mur sud de la cuisine de part et d'autre de la porte
LIBRES = [(XC0 + EP / 2, FEN_C[0]), (XC0 + EP / 2, FEN_C[1]), (FEN_T[0], YH0 + EP / 2), (FEN_T[1], YH0 + EP / 2),
          (POR_C[0], YE0 + EP / 2), (POR_C[1], YE0 + EP / 2), (POR_T[1], YE0 + EP / 2)]   # jambages d'ouverture : extrémités libres voulues


def murs_source():
    """Murs et poteaux de la source (page 17), en points (x0, y0, x1, y1) ; gris 0.75 et poteaux 0.5."""
    out = []
    with pymupdf.open(SRC) as s:
        for dr in s[PG].get_drawings():
            f = dr.get('fill')
            if not f or not (abs(f[0] - 0.75) < 0.01 or abs(f[0] - 0.5) < 0.01): continue
            for it in dr['items']:
                if it[0] == 're' and it[1].width > 1 and it[1].height > 1 and it[1].y0 > 100 and it[1].y1 < 960: out.append((it[1].x0, it[1].y0, it[1].x1, it[1].y1))
    return out


def en_xywh(L): return [(a[0], a[1], a[2] - a[0], a[3] - a[1]) for a in L]


# zones où le dessin a le droit de différer de la source (points) / texte effacé
ZONES_ERASE = [(563.0, 449.0, 582.0, 462.5), (517.0, 346.5, 531.0, 366.5), (407.5, 646.5, 447.0, 660.5), (464.0, 1023.5, 584.0, 1041.5), (514.0, 1065.0, 533.5, 1079.5)]
ZONES_OK = [(486, 133, 503, 397), (436, 132, 470, 397), (212, 138, 496, 200), (455, 169, 492, 392), (424, 180, 442, 266), (503, 200, 516, 246), (255, 226, 320, 252),                                  # fenêtre cuisine + cote + mur de fermeture
            (212, 330, 290, 430), (226, 332, 280, 396),                                  # porte cuisine, arc, cote
            (214, 330, 300, 340),                                                        # libellé CUISINE
            (440, 195, 466, 252),                                                        # repère de fenêtre
            (490, 278, 655, 400), (578, 312, 638, 330),                                  # toilette, fenêtre, cote nord
            (489, 394, 655, 512),                                                        # porte, arc, bac, cotes, repères
            (405, 646, 448, 662),                                                        # surface de la terrasse
            (404, 1020, 600, 1130)]                                                      # cartouche (titre, n°, dessinateur, date)
BANDES_MURS = [(490, 440, 500, 480), (644, 440, 654, 480)]


def base_preparee():
    """Copie du plan source dont le TEXTE périmé (cote 2.85 sous la toilette, surface 92.53, cartouche) et les petits tracés périmés (cote 2.85 et ses ticks) sont SUPPRIMÉS."""
    import tempfile
    doc = pymupdf.open(SRC); pg = doc[PG]
    for r in ZONES_ERASE: pg.add_redact_annot(pymupdf.Rect(*r), fill=False)
    pg.apply_redactions(images=0, graphics=0)                                                    # texte seulement
    pg.add_redact_annot(pymupdf.Rect(516.0, 316.9, 543.6, 396.9), fill=False)                    # ancienne cote 1.26 (elle traversait l'aménagement)
    pg.add_redact_annot(pymupdf.Rect(491.0, 447.0, 652.5, 470.5), fill=False)                    # cote 2.85 : chemins entièrement contenus seulement
    pg.apply_redactions(images=0, graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED)
    ch = os.path.join(tempfile.gettempdir(), 'mbao_terrasse_base.pdf'); doc.save(ch); doc.close()
    return pymupdf.open(ch)


# ------------------------------------------------------------------ outils de dessin
class Pg:
    def __init__(self, doc, base):
        self.pg = doc.new_page(width=841.92, height=1190.52); self.pg.show_pdf_page(self.pg.rect, base, PG)

    def line(self, a, b, color=NOIR, w=W_DET, dash=None):
        s = self.pg.new_shape(); s.draw_line(pymupdf.Point(*a), pymupdf.Point(*b)); s.finish(color=color, width=w, dashes=dash); s.commit()

    def rect(self, r, fill=None, color=NOIR, w=W_DET):
        s = self.pg.new_shape(); s.draw_rect(pymupdf.Rect(*r)); s.finish(fill=fill, color=color, width=w, closePath=True); s.commit()

    def poly(self, pts, color=NOIR, w=W_DET):
        s = self.pg.new_shape(); s.draw_polyline([pymupdf.Point(*p) for p in pts]); s.finish(color=color, width=w, closePath=False); s.commit()

    def oval(self, r, fill=None, color=NOIR, w=W_DET):
        s = self.pg.new_shape(); s.draw_oval(pymupdf.Rect(*r)); s.finish(fill=fill, color=color, width=w); s.commit()

    def txt(self, x, y, t, size=9.0, font='helv', rot=0, color=NOIR):
        self.pg.insert_text(pymupdf.Point(x, y), t, fontsize=size, fontname=font, rotate=rot, color=color)

    def txtc(self, xc, y, t, size=9.0, font='helv', color=NOIR):
        self.txt(xc - pymupdf.get_text_length(t, font, size) / 2, y, t, size, font, 0, color)

    def blanc(self, r): self.rect(r, BLANC, None, 0)

    # --- cotes dans la charte du plan : trait 0.72, ticks obliques 0.72, traits d'attache, texte 9.7 sur fond blanc
    def tick(self, x, y, horiz):
        d = 3.24
        a, b = ((x - d, y + d), (x + d, y - d)) if horiz else ((x - d, y - d), (x + d, y + d))          # horizontale : « / » ; verticale : « \ » (comme la source)
        self.line(a, b, NOIR, W_COTE)

    def hcote(self, x0, x1, y, segs, vers=-1, att=12.96, hors=6.36):
        """Chaîne horizontale : segs = [(x_debut, x_fin, texte, place)] ; place = 'h' (au-dessus), 'b' (en dessous). vers = -1 : objet au-dessus de la ligne."""
        self.line((x0 - 6.48, y), (x1 + 6.48, y), NOIR, W_COTE)
        xs = sorted({s[0] for s in segs} | {s[1] for s in segs})
        for x in xs:
            self.line((x, y + vers * att), (x, y - vers * hors), NOIR, W_COTE); self.tick(x, y, True)
        for sg in segs:
            a, b, t, pl = sg[:4]; dx = sg[4] if len(sg) > 4 else 0.0
            tl = pymupdf.get_text_length(t, 'helv', 9.7); xc = (a + b) / 2 + dx
            by = y - 3.4 if pl == 'h' else y + 10.6
            self.blanc((xc - tl / 2 - 0.8, by - 8.0, xc + tl / 2 + 0.8, by + 1.6)); self.txt(xc - tl / 2, by, t, 9.7)

    def vcote(self, y0, y1, x, segs, vers=1, att=12.96, hors=6.36):
        """Chaîne verticale : segs = [(y_debut, y_fin, texte, place)] ; place = 'g' (à gauche), 'd' (à droite). vers = 1 : objet à droite de la ligne."""
        self.line((x, y0 - 6.48), (x, y1 + 6.48), NOIR, W_COTE)
        ys = sorted({s[0] for s in segs} | {s[1] for s in segs})
        for y in ys:
            self.line((x - vers * att, y), (x + vers * hors, y), NOIR, W_COTE); self.tick(x, y, False)
        for a, b, t, pl in segs:
            tl = pymupdf.get_text_length(t, 'helv', 9.7); yc = (a + b) / 2
            bx = x - 3.4 if pl == 'g' else x + 10.6
            self.blanc((bx - 8.0, yc - tl / 2 - 0.8, bx + 1.6, yc + tl / 2 + 0.8)); self.txt(bx, yc + tl / 2, t, 9.7, rot=90)

    def arc_porte(self, charniere, r, a0, a1, vantail=True):
        """Arc d'ouverture (angles en degrés, repère page : y vers le bas) et vantail ouvert à a1."""
        pts = [(charniere[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / 40)), charniere[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / 40))) for i in range(41)]
        self.poly(pts, NOIR, W_DET)
        if vantail: self.line(charniere, pts[-1], NOIR, W_DET)


def murs_neufs(p):
    # mur ouest de la toilette (W1) : corps gris, faces noires ; le trait de la face sud de l'ancien mur horizontal, resté dans l'épaisseur, est recouvert
    p.rect((XC0, YH1, XC1, YE0), GRIS, None, 0)
    p.rect((XC0 + W_FACE / 2, YH1 - W_FACE / 2 - 0.1, XC1, YH1 + W_FACE / 2 + 0.1), GRIS, None, 0)
    p.line((XC0, YH1), (XC0, YE0), NOIR, W_FACE)
    p.line((XC1, YH1 - W_FACE / 2), (XC1, YE0), NOIR, W_FACE)
    # mur sud de la toilette (W2), du jambage de la porte au mur est
    x0, x1 = NEUF_W2[0], NEUF_W2[2]
    p.rect((x0, YE0, x1, YE1), GRIS, None, 0)
    p.line((x0, YE0), (x1, YE0), NOIR, W_FACE); p.line((x0, YE1), (x1, YE1), NOIR, W_FACE); p.line((x0, YE0), (x0, YE1), NOIR, W_FACE)


def ouverture_horiz_mur(p, xa, xb, y0, y1):
    """Fenêtre dans un mur horizontal (épaisseur y0..y1) : le mur est ouvert, jambages à 2.52, symbole de vitrage en quatre traits."""
    p.blanc((xa, y0 - W_FACE / 2 - 0.2, xb, y1 + W_FACE / 2 + 0.2))
    for x in (xa, xb): p.line((x, y0), (x, y1), NOIR, W_FACE)
    for k in range(4): p.line((xa, y0 + k * (y1 - y0) / 3), (xb, y0 + k * (y1 - y0) / 3), NOIR, W_DET if k in (0, 3) else 0.48)


def ouverture_vert_mur(p, ya, yb, x0, x1):
    p.blanc((x0 - W_FACE / 2 - 0.2, ya, x1 + W_FACE / 2 + 0.2, yb))
    for y in (ya, yb): p.line((x0, y), (x1, y), NOIR, W_FACE)
    for k in range(4): p.line((x0 + k * (x1 - x0) / 3, ya), (x0 + k * (x1 - x0) / 3, yb), NOIR, W_DET if k in (0, 3) else 0.48)


def source_porte():
    """Traits noirs fins du dessin de la porte existante de l'escalier (mur sud de l'escalier, ouverture 228.36 à 277.08, battant vers la terrasse), relevés sur le vectoriel."""
    out = []
    with pymupdf.open(SRC) as s_:
        for dr in s_[PG].get_drawings():
            w, c, r = dr.get('width') or 0, dr.get('color'), dr['rect']
            if c is None or tuple(round(v, 2) for v in c) != (0, 0, 0) or w >= 1.0 or dr.get('fill') is not None: continue
            if not (r.x0 >= 226.5 and r.x1 <= 278.0 and r.y0 >= 509.5 and r.y1 <= 556.0): continue
            for it in dr['items']:
                if it[0] == 'l': out.append((it[1].x, it[1].y, it[2].x, it[2].y, w))
    return out


def porte_source(p, xl, caps):
    """Même porte que celle de l'escalier : dessin de la source translaté au jambage ouest xl et retourné (battant vers le nord) dans un mur sud de la toilette ou de la cuisine."""
    dx, yc = xl - 228.36, (YE0 + YE1) / 2
    if caps:
        for x in (xl, xl + PW): p.line((x, YE0), (x, YE1), NOIR, W_FACE)
    for x0, y0, x1, y1, w in source_porte():
        p.line((x0 + dx, yc - (y0 - 514.32)), (x1 + dx, yc - (y1 - 514.32)), NOIR, w)


def dessiner_plan(p):
    murs_neufs(p)
    # --- cuisine : fenêtre 2.00 x 1.25 (mur est), porte 0.90 x 2.20 (mur sud, battant vers la cuisine)
    ouverture_vert_mur(p, FEN_C[0], FEN_C[1], XC0, XC1)
    p.blanc((POR_C[0], YE0 - W_FACE / 2 - 0.2, POR_C[1], YE1 + W_FACE / 2 + 0.2))
    porte_source(p, POR_C[0], caps=True)                                  # même porte que celle de l'escalier (copie du dessin de la source), battant vers la cuisine
    # --- toilette : fenêtre 1.00 x 0.60 (mur nord), porte 0.90 x 2.20 (mur sud côté ouest, battant vers la terrasse, charnière à l'est)
    ouverture_horiz_mur(p, FEN_T[0], FEN_T[1], YH0, YH1)
    porte_source(p, POR_T[0], caps=False)                                 # même porte que celle de l'escalier, battant vers l'INTÉRIEUR, charnière à l'ouest, contre le mur ouest
    # lave-mains 0.40 x 0.30 contre le mur nord, à 0.30 de la face ouest
    lx = XC1 + 0.30 * K; p.rect((lx, YH1 + 1.4, lx + 0.40 * K, YH1 + 1.4 + 0.30 * K), BLANC, NOIR, W_DET)
    p.oval((lx + 3.0, YH1 + 4.2, lx + 0.40 * K - 3.0, YH1 + 1.4 + 0.30 * K - 2.8), None, NOIR, 0.48); p.oval((lx + 0.20 * K - 1.2, YH1 + 2.0, lx + 0.20 * K + 1.2, YH1 + 4.4), BLANC, NOIR, 0.48)
    p.txt(526, 346.0, 'LAVE-MAINS', 5.0, 'helv')
    # WC contre le mur nord, axe à 1.40 de la face ouest : réservoir 0.40 x 0.18, cuvette 0.36 x 0.50
    cx = XC1 + 1.40 * K
    p.rect((cx - 0.20 * K, YH1 + 1.4, cx + 0.20 * K, YH1 + 1.4 + 0.18 * K), BLANC, NOIR, W_DET)
    p.oval((cx - 0.18 * K, YH1 + 1.4 + 0.18 * K, cx + 0.18 * K, YH1 + 1.4 + 0.18 * K + 0.50 * K), BLANC, NOIR, W_DET)
    # douche : simple pente carrelée vers un siphon au bout (côté mur est), sans receveur ni paroi
    sx0 = XE_I - 0.90 * K; gris = (0.4, 0.4, 0.4)
    for a_, b_ in (((sx0, YH1 + 1.3), (XE_I - 1.3, YH1 + 1.3)), ((sx0, YE0 - 1.3), (XE_I - 1.3, YE0 - 1.3)), ((sx0, YH1 + 1.3), (sx0, YE0 - 1.3))): p.line(a_, b_, gris, 0.5, '[3 2] 0')
    xs, ys = XE_I - 0.12 * K, YH1 + 0.63 * K
    for yy in (YH1 + 0.40 * K, ys + 3.0, YE0 - 0.22 * K):
        xe = xs - 7.0; p.line((sx0 + 5.0, yy), (xe, yy), gris, 0.5); p.line((xe - 3.0, yy - 1.8), (xe, yy), gris, 0.5); p.line((xe - 3.0, yy + 1.8), (xe, yy), gris, 0.5)
    p.oval((xs - 2.6, ys - 2.6, xs + 2.6, ys + 2.6), BLANC, NOIR, 0.5); p.line((xs - 2.6, ys), (xs + 2.6, ys), NOIR, 0.4); p.line((xs, ys - 2.6), (xs, ys + 2.6), NOIR, 0.4)
    p.txt(sx0 + 4.0, YH1 + 8.5, 'DOUCHE', 5.4, 'hebo'); p.txt(sx0 + 4.0, YH1 + 14.0, 'pente carrelée', 4.6, 'helv'); p.txt(xs - 15.0, ys + 7.5, 'siphon', 4.8, 'helv')
    # --- bac lessive / vaisselle : 1.87 x 1.10, h 0.40, contre le mur sud de la toilette, robinets côté mur
    bx0, by0, bx1, by1 = BAC; rim = 0.10 * K
    p.rect((bx0, by0 + W_FACE / 2, bx1 - W_FACE / 2, by1), BLANC, NOIR, 0.84)
    p.rect((bx0 + rim, by0 + rim, bx1 - rim, by1 - rim), None, NOIR, 0.48)
    for xr in (bx0 + 0.45 * K, bx0 + 1.30 * K):
        p.oval((xr - 2.0, by0 + 2.6, xr + 2.0, by0 + 6.6), BLANC, NOIR, 0.5)
        p.line((xr, by0 + 6.6), (xr, by0 + rim + 3.0), NOIR, 0.5)
    xd, yd = bx0 + 0.90 * K, by0 + 0.62 * K
    p.oval((xd - 2.4, yd - 2.4, xd + 2.4, yd + 2.4), None, NOIR, 0.48); p.line((xd - 2.4, yd), (xd + 2.4, yd), NOIR, 0.4); p.line((xd, yd - 2.4), (xd, yd + 2.4), NOIR, 0.4)
    # --- cuisine : plan de travail en L (prof. 0.60) suivant les murs nord et est, vasque axée sur la fenêtre, plaque + four, frigo
    ins = 1.3
    p.poly([(XW_I + ins, YN_I + ins), (XC0 - ins, YN_I + ins), (XC0 - ins, Y_FR), (XC0 - WT, Y_FR), (XC0 - WT, YN_I + WT), (XW_I + ins, YN_I + WT), (XW_I + ins, YN_I + ins)], NOIR, W_DET)
    yc = (FEN_C[0] + FEN_C[1]) / 2                                                       # axe de la fenêtre = axe de la vasque (1.75 de l'angle nord)
    sx0c, sx1c = XC0 - WT + 2.2, XC0 - WT + 2.2 + 0.45 * K
    p.rect((sx0c, yc - 0.60 * K, sx1c, yc + 0.60 * K), BLANC, NOIR, W_DET)
    for dy in (-0.60 * K + 2.2, 2.0):
        p.rect((sx0c + 2.0, yc + dy, sx1c - 2.0, yc + dy + 0.60 * K - 4.2), None, NOIR, 0.48)
    p.oval((XC0 - 4.0, yc - 1.5, XC0 - 1.3, yc + 1.5), BLANC, NOIR, 0.5)
    p.line((XC0 - 1.3 - 52.0, yc), (XC0 - 1.3, yc), (0, 0.5, 1.0), W_COTE, '[6 3 1 3] 0')   # axe fenêtre / vasque (bleu comme les axes du plan)
    p.txt(433.5, yc + 40.0, 'VASQUE 2 BACS 1.20 x 0.45, axée sur la fenêtre', 5.2, 'helv', rot=90)
    h0, h1 = HOB_X0, HOB_X0 + 0.60 * K
    p.rect((h0, YN_I + 2.8, h1, YN_I + 2.8 + 0.52 * K), BLANC, NOIR, W_DET)
    for fx in (0.27, 0.73):
        for fy in (0.27, 0.73): p.oval((h0 + fx * (h1 - h0) - 3.6, YN_I + 2.8 + fy * 0.52 * K - 3.6, h0 + fx * (h1 - h0) + 3.6, YN_I + 2.8 + fy * 0.52 * K + 3.6), None, NOIR, 0.48)
    p.txtc((h0 + h1) / 2, 196.5, 'PLAQUE 4 FEUX + FOUR dessous', 5.4, 'helv')
    p.rect((XC0 - 0.70 * K, Y_FR, XC0 - 1.3, YE0 - 1.3), BLANC, NOIR, W_DET)
    p.txtc(XC0 - 0.35 * K, 370.0, 'FRIGO', 6.0, 'hebo'); p.txtc(XC0 - 0.35 * K, 377.5, '0.70 x 0.70', 5.2, 'helv')
    # --- libellés
    p.txtc(288, 237, 'CUISINE', 9.0); p.txtc(288, 248, '%s m²' % fmt(pieces()[0][0][2]), 9.1)
    p.txtc(571, 372, 'TOILETTE', 9.0); p.txtc(571, 382, '%s m²' % fmt(pieces()[0][1][2]), 9.1)
    p.txt(408.2, 657.25, '%s m²' % fmt(S_TERRASSE), 9.1)
    p.txt(231, 334, 'P 0.95 x 2.20', 6.4); p.txt(511.5, FEN_C[0] + 70.0, 'F 2.00 x 1.25', 6.4, rot=90)
    p.txtc((FEN_T[0] + FEN_T[1]) / 2, 281.5, 'F 1.00 x 0.60, allège 1.60', 6.4)
    p.txt(503, 492, 'P 0.95 x 2.20', 6.4)
    p.txt(548, 490, 'BAC LESSIVE / VAISSELLE', 6.0, 'hebo'); p.txt(548, 498, 'h 0.40 (2 rangs de briques)', 6.0); p.txt(548, 506, 'robinets côté mur de la toilette', 6.0)
    # --- cotes
    # cuisine : chaîne verticale à 8 pt devant le plan de travail est (0.60 | 2.00 | 1.53 | 0.70 = 4.83), traits d'attache jusqu'au mur
    xv = XC0 - WT - 8.0
    yw = YN_I + WT
    p.vcote(YN_I, YE0, xv, [(YN_I, yw, '0.60', 'g'), (yw, FEN_C[1], '2.00', 'g'), (FEN_C[1], Y_FR, '%.2f' % ((Y_FR - FEN_C[1]) / K), 'g'), (Y_FR, YE0, '0.70', 'g')], vers=-1, att=XC0 - 1.3 - xv)
    # cuisine : plan de travail nord, de gauche à droite : 2.00 | plaque 0.60 | 2.08 | angle 0.60 = 5.28
    p.hcote(XW_I, XC0, 184.0, [(XW_I, HOB_X0, '2.00', 'h'), (HOB_X0, HOB_X0 + 0.60 * K, '0.60', 'h'), (HOB_X0 + 0.60 * K, XC0 - WT, '%.2f' % ((XC0 - WT - HOB_X0 - 0.60 * K) / K), 'h'), (XC0 - WT, XC0, '0.60', 'h')], vers=-1)
    # cuisine : position de la porte, sous le mur sud (côté escalier) : 0.15 | 0.90
    p.hcote(XW_I, POR_C[1], 412.0, [(XW_I, POR_C[0], '0.15', 'b', 6.5), (POR_C[0], POR_C[1], '%.2f' % (PW / K), 'h')], vers=-1)
    # toilette : position de la fenêtre, au nord du mur (dans le vide) : 1.62 | 1.00 | 0.23 = 2.85
    p.hcote(XC1, XE_I, 301.0, [(XC1, FEN_T[0], '%.2f' % ((FEN_T[0] - XC1) / K), 'h'), (FEN_T[0], FEN_T[1], '1.00', 'h'), (FEN_T[1], XE_I, '%.2f' % ((XE_I - FEN_T[1]) / K), 'h', -8.0)], vers=1, att=12.0)
    # terrasse : porte | jeu | bac = 0.90 | 0.08 | 1.87 = 2.85
    p.hcote(XC1, XE_I, 471.0, [(POR_T[0], POR_T[1], '%.2f' % (PW / K), 'h'), (POR_T[1], BAC[0], '%.2f' % ((BAC[0] - POR_T[1]) / K), 'b'), (BAC[0], BAC[2], '1.87', 'h')], vers=-1, att=17.0)
    # toilette : profondeur 1.26 (ancienne cote déplacée : elle traversait l'aménagement)
    # bac : profondeur 1.10, dans le bac, côté est
    p.vcote(BAC[1], BAC[3], BAC[2] - 9.5, [(BAC[1], BAC[3], '1.10', 'g')], vers=1, att=0.01, hors=0.01)
    return p


def cartouche(p):
    """Titre, n° de plan, dessinateur et date (le cartouche d'origine reste celui de D&F)."""
    p.blanc((464.2, 1023.0, 584.5, 1042.0)); p.txtc(523.5, 1037.0, 'TERRASSE COTÉ - IND. C', 9.2, 'hebo')
    p.blanc((514.5, 1064.5, 534.0, 1080.0)); p.txt(515.6, 1076.4, '019', 9.7, 'helv')
    p.txt(437.5, 1109.0, 'E.H.S.F', 8.6, 'helv'); p.txt(563.0, 1116.2, '05/11/26', 6.4, 'helv')


# ------------------------------------------------------------------ page 2 : tableaux
def page_tableaux(doc, base):
    p = Pg(doc, base); pg = p.pg
    p.blanc((48, 64, 794, 996))
    p.txt(70, 100, 'TERRASSE - TABLEAU DES PIÈCES ET DES MENUISERIES', 13, 'hebo')
    p.txt(70, 116, 'Maître d\'ouvrage : Mohamed BADIANE - Projet de construction d\'une villa résidentielle à Mbao - D&F ENGINEERING - Indice B du 05/11/2026', 7.6, 'helv', color=(0.3, 0.3, 0.3))
    lignes, bac_s, bac_p = pieces()
    # --- tableau 1 : pièces
    y = 150; cols = [70, 150, 290, 390, 490]
    p.rect((70, y - 14, 520, y + 4), (0.88, 0.88, 0.88), NOIR, 0.6)
    for x, t in zip(cols, ('PIÈCE', 'DIMENSIONS (m)', 'SURFACE (m²)', 'PÉRIMÈTRE (m)')): p.txt(x + 4, y - 1.5, t, 8.4, 'hebo')
    for nom, dim, s, per in lignes:
        y += 19; p.rect((70, y - 14, 520, y + 5), None, NOIR, 0.4)
        p.txt(cols[0] + 4, y - 1, nom, 9, 'hebo'); p.txt(cols[1] + 4, y - 1, dim, 9); p.txt(cols[2] + 4, y - 1, fmt(s), 9, 'hebo'); p.txt(cols[3] + 4, y - 1, fmt(per), 9)
    y += 19; p.rect((70, y - 14, 520, y + 5), (0.95, 0.95, 0.95), NOIR, 0.4)
    p.txt(cols[0] + 4, y - 1, 'BAC (ouvrage)', 9, 'hebo'); p.txt(cols[1] + 4, y - 1, '1.87 x 1.10, h 0.40', 9); p.txt(cols[2] + 4, y - 1, fmt(bac_s), 9); p.txt(cols[3] + 4, y - 1, fmt(bac_p), 9)
    notes = ['Surface = surface nette, mesurée à l\'intérieur des murs (faces des murs) ; périmètre = contour des faces intérieures, ouvertures non déduites.',
             'CUISINE et TOILETTE : cotes du plan (5.28 x 4.83 ; 2.85 x 1.26). ESC : surface 11.61 du plan d\'origine, inchangée (5.28 x 2.20 = 11.62).',
             'TERRASSE : polygone relevé sur le vectoriel (échelle 51.5 pt/m) ; le bac (%s) est compris dans la surface, surface libre = %s.' % (fmt(bac_s), fmt(S_TERRASSE - bac_s)),
             'Le seuil de la porte de la toilette ferme le polygone de la terrasse au droit de l\'ouverture (pas de surface d\'ouverture comptée).']
    y += 30
    for n in notes: p.txt(70, y, '- ' + n, 7.0); y += 10.5
    # --- tableau 2 : menuiseries
    y += 26; p.txt(70, y, 'MENUISERIES', 10.5, 'hebo'); y += 26
    cols2 = [70, 112, 200, 360, 440, 520, 640]
    p.rect((70, y - 12, 720, y + 4), (0.88, 0.88, 0.88), NOIR, 0.6)
    for x, t in zip(cols2, ('REP.', 'LOCAL', 'MUR / POSITION', 'L x H (m)', 'ALLÈGE', 'OUVRANT')): p.txt(x + 3, y - 1.5, t, 8, 'hebo')
    men = [('F1', 'CUISINE', 'mur est, x 0.60 de l\'angle nord', '2.00 x 1.25', 'à confirmer', 'à définir'),
           ('P1', 'CUISINE', 'mur sud (vers ESC), 0.15 de l\'angle ouest', '0.90 x 2.20', '-', 'vers la cuisine'),
           ('F2', 'TOILETTE', 'mur nord, 1.62 de l\'angle ouest', '1.00 x 0.60', '1.60 (tête 2.20)', 'à définir'),
           ('P2', 'TOILETTE', 'mur sud, côté ouest', '0.90 x 2.20', '-', 'vers l\'intérieur, contre le mur ouest')]
    for r in men:
        y += 16; p.rect((70, y - 12, 720, y + 4), None, NOIR, 0.4)
        for x, t in zip(cols2, r): p.txt(x + 3, y - 1.5, t, 8)
    p.txt(70, y + 16, '- Dimensions L x H en mètres. Allège de F1 non donnée : 0.95 proposée (tête 2.20, comme P1/P2) ; allège de F2 : 1.60 (tête 2.20), à confirmer.', 7.0)
    # --- aménagements (indice B)
    y += 34; p.txt(70, y, 'AMÉNAGEMENTS (indice B)', 10.5, 'hebo'); y += 14
    for t in ['CUISINE : plan de travail en L, prof. 0.60, suivant les murs nord (5.28) et est (3.53 de la face nord du plan au frigo) ; développé 8.81 ; hauteur 0.90 (hypothèse).',
              'CUISINE : vasque 2 bacs 1.20 x 0.45 sur la branche est, axée sur la fenêtre F1 (axe à 1.75 de l\'angle extérieur nord, 1.60 de la face intérieure nord).',
              'CUISINE : plaque 4 feux 0.60 x 0.52 sur la branche nord, axe à 2.30 de la face ouest, avec four dessous (cuisinière : à confirmer par le client) ; frigo 0.70 x 0.70 dans l\'angle sud-est, contre le plan de travail.',
              'TOILETTE : porte P2 vers l\'INTÉRIEUR, charnière à l\'ouest, vantail ouvert contre le mur ouest (plus vers le bac).',
              'TOILETTE : lave-mains 0.40 x 0.30 contre le mur nord (de 0.30 à 0.70 de la face ouest) ; WC contre le mur nord, axe à 1.40 de la face ouest.',
              'TOILETTE : douche = receveur maçonné carrelé 0.90 x 1.26 (de 1.95 à 2.85 de la face ouest, contre le mur est, sous la fenêtre F2), siphon de sol au centre',
              '   (0.45 du mur est, 0.63 du mur nord ; profondeur de la toilette 1.26) ; paroi vitrée fixe 0.70 le long du receveur, passage 0.56 côté sud.',
              'Lecture retenue de « la sèche de la douche » : receveur et paroi (zone mouillée) ; à confirmer par le client.']:
        p.txt(70, y, '- ' + t, 7.0); y += 10.5
    y += 14; p.txt(70, y, 'POINTS À SIGNALER', 10.5, 'hebo'); y += 12
    for t in ['Murs neufs en maçonnerie de 0.15 (comme les murs existants), faces dans le prolongement exact des murs voisins (contrôle des raccords).',
              'Bac lessive / vaisselle : maçonnerie de briques, 2 rangs soit h 0.40 ; robinets contre le mur de la toilette (alimentation par ce mur) ; décalé à 0.08 du jambage est de la porte de la toilette (passage libre devant la porte).',
              'POINTS DE L\'INGÉNIEUR : (a) fermeture de la cuisine : murs neufs 0.15 à ancrer au mur existant ; (b) baie 2.00 dans le mur est existant : linteau, appuis 0.20, sous la poutre ;',
              '(c) fenêtre 1.00 x 0.60 de la toilette et portes 0.90 x 2.20 : linteaux ; (d) évacuations (WC, bac, cuisine) et étanchéité de la terrasse sous le bac et le long des murs neufs.',
              'Plan sous réserve du relevé sur site et du visa de l\'ingénieur de structure. Cotes en mètres, échelle 1:50 pour le plan (page 1).']:
        p.txt(70, y, '- ' + t, 7.0); y += 10.5
    return p


# ------------------------------------------------------------------ contrôles
def controler(chemin):
    err = []
    src = en_xywh(murs_source())
    to_m = lambda L: [m_pt_to_m(a) for a in L]
    conserv = [((a[0] - OX) / K, (a[1] - OY) / K, (a[2] - a[0]) / K, (a[3] - a[1]) / K) for a in CONSERVES]
    neufs = [((a[0] - OX) / K, (a[1] - OY) / K, (a[2] - a[0]) / K, (a[3] - a[1]) / K) for a in (NEUF_W1, NEUF_W2)]
    libres = [((x - OX) / K, (y - OY) / K) for x, y in LIBRES]
    appuis = [((a[0] - OX) / K, (a[1] - OY) / K, (a[2] - a[0]) / K, (a[3] - a[1]) / K) for a in murs_source()]
    srcm = appuis
    for e in CR.raccords_murs(conserv, neufs, appuis=appuis, libres=libres, source=srcm): err.append('MURS : ' + e)
    for b in CR._fidelite(SRC, PG, chemin, 0, ZONES_OK, 200, 40, 1.0): err.append('PAGE 1 : différence avec la source hors zone modifiée, boîte (pt) %s' % (b,))
    for w in CR.texte_perime(SRC, PG, chemin, 0, ZONES_ERASE): err.append('PAGE 1 : texte d\'origine périmé encore extractible %s' % (w,))
    faces = [('face est du mur de la cuisine', (XC1, YN_I), (XC1, YH0), [(FEN_C[0], FEN_C[1])]), ('face ouest du mur de la cuisine / toilette', (XC0, YN_I), (XC0, YE0), [(FEN_C[0], FEN_C[1])]),
             ('face nord du mur de la toilette', (XC1, YH0), (XE_I, YH0), [(FEN_T[0], FEN_T[1])]), ('face sud de la toilette', (NEUF_W2[0], YE1), (XE_I, YE1), []),
             ('face nord de la toilette (intérieur)', (NEUF_W2[0], YE0), (XE_I, YE0), []), ('face est de la toilette', (XE_I, YH1), (XE_I, YE1), [])]
    for c in CR.continuite_traits(chemin, 0, faces): err.append('PAGE 1 : trait de face coupé (%s) de %.1f à %.1f pt' % c)
    for c in CR.traits_parasites(chemin, 0, BANDES_MURS): err.append('PAGE 1 : tick de cote orphelin en %s' % (c,))
    for c in CR.cotes_perimees(chemin, 0, BANDES_MURS, (500, 440, 644, 480)): err.append('PAGE 1 : ancienne cote encore visible dans un mur, boîte (pt) %s' % (tuple(round(v, 1) for v in c),))
    return err


ERR = []


def construire():
    base = base_preparee(); doc = pymupdf.open()
    p = Pg(doc, base); dessiner_plan(p); cartouche(p)
    doc.set_metadata({'title': 'MBAO - Terrasse - plan et tableau des pieces (indice A)', 'author': 'D&F ENGINEERING'})
    os.makedirs(os.path.dirname(OUT), exist_ok=True); doc.save(OUT, deflate=True, garbage=3)
    global ERR
    err = ERR = controler(OUT)
    for e in err: print('RACCORD :', e)
    print('contrôle des raccords :', 'CONFORME' if not err else '%d anomalie(s)' % len(err))
    ap = os.path.join(HERE, 'apercus', 'terrasse'); os.makedirs(ap, exist_ok=True)
    for i, pg in enumerate(doc): pg.get_pixmap(dpi=110).save(os.path.join(ap, 'page%d.png' % (i + 1)))
    return OUT


if __name__ == '__main__':
    lg, bs, bp = pieces()
    for l in lg: print('%-9s %-24s surface %6.2f  périmètre %6.2f' % l)
    print('bac %.2f  %.2f' % (bs, bp))
    construire()
    sys.exit(1 if ERR else 0)
