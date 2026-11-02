"""Assemble le dossier client d'esquisse (indice courant) : couverture, vues 3D d'abord, puis les plans (retour client 15/10 :
ni résumé ni notes de modification ; ceux-ci sont dans le rapport séparé rapport_esquisse.py)."""
import os, sys, pymupdf
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, '/home/user/atelier-archi-ingenierie/outils'); sys.path.insert(0, HERE)
import dessin_plan as dp
from dessiner_plans import CARTO, DATE, ID
from reportlab.pdfgen import canvas
import sys as _s, os as _o; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))), 'esquisse')); from indice import REV, REVISIONS

SRC = os.path.join(ROOT, 'projet', 'source', 'YAMA_HOUSE_Architectural_Design_realistic_v2.pdf')
src = pymupdf.open(SRC)
out = pymupdf.open()
out.insert_pdf(src, from_page=0, to_page=0)                       # couverture
cv = out[0]
# (4e passage) image de couverture = vue 3D de l'indice courant (l'image d'origine montrait l'aménagement abandonné, DOC-041)
IMG3D = os.path.join(ROOT, 'projet', 'vues3d', 'rendus', 'ensemble_se.png')
if os.path.exists(IMG3D):
    from PIL import Image as _I
    zone = pymupdf.Rect(21.0, 108.0, 1170.0, 531.0); im = _I.open(IMG3D).convert('RGB'); w_, h_ = im.size
    k_ = zone.width / zone.height; hh = int(w_ / k_)
    if hh <= h_: im = im.crop((0, (h_ - hh) // 2, w_, (h_ - hh) // 2 + hh))
    else: ww = int(h_ * k_); im = im.crop(((w_ - ww) // 2, 0, (w_ - ww) // 2 + ww, h_))
    tmp = os.path.join(HERE, '_couv.jpg'); im.save(tmp, quality=88)
    cv.insert_image(zone, filename=tmp); os.remove(tmp)
if os.path.exists(IMG3D):         # titre du projet (il était écrit sur l'image d'origine)
    cv.draw_rect(pymupdf.Rect(21, 108, 470, 215), color=None, fill=(1, 1, 1), fill_opacity=0.82)
    cv.insert_text((36, 150), 'YAMA HOUSE', fontsize=34, fontname='hebo', color=(0.1, 0.1, 0.1))
    cv.insert_text((38, 175), f'Schematic Design  -  Revision {REV}  -  %s' % DATE, fontsize=13, fontname='helv', color=(0.2, 0.2, 0.2))
    cv.insert_text((38, 197), 'BRIKAMA, The Gambia', fontsize=12, fontname='helv', color=(0.3, 0.3, 0.3))
else:
    cv.insert_text((45, 325), 'Schematic design - REVISION C - %s' % DATE, fontsize=11, color=(1, 1, 1), fontname='helv')
# coquille du gabarit « DEDIGN » corrigée (texte dessiné en police intégrée : masqué puis réécrit)
cv.draw_rect(pymupdf.Rect(770, 600, 841, 620), color=None, fill=(1, 1, 1))
cv.insert_text((841.0 - pymupdf.get_text_length('DESIGN', 'helv', 13.6) - 6, 615.0), 'DESIGN', fontsize=13.6, fontname='helv', color=(0, 0, 0))
cv.draw_line((842.5, 602.0), (842.5, 619.5), color=(0, 0, 0), width=0.7)          # séparateur masqué avec la coquille
# (retour client 15/10) vues 3D d'abord (façades 3D, plans coupés, vues extérieures, vues intérieures : ordre de
# planches_3d.py), puis le jeu 2D complet validé au contrôle 2D (dossier_controle_2d.jeu_2d)
P3D = os.path.join(ROOT, 'projet', 'vues3d', f'YAMA_3D_schematique_rev{REV}.pdf')
out.insert_pdf(src, from_page=1, to_page=1)
out.insert_pdf(pymupdf.open(P3D))
out.insert_pdf(src, from_page=14, to_page=14)                     # intercalaire 2D schematic design
import dossier_controle_2d as c2d
out.insert_pdf(c2d.jeu_2d())
out.set_metadata({'title': f'YAMA HOUSE - Schematic Design - revision {REV}', 'author': ID['signature']})
out.save(os.path.join(HERE, f'YAMA_HOUSE_Schematic_Design_rev{REV}.pdf'), garbage=4, deflate=True)
print(len(out), 'pages')
