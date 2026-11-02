"""YAMA HOUSE - planches des vues 3D schématiques (cartouche « 3D » du projet, distinct du cartouche des plans).

python3 -I projet/vues3d/planches_3d.py  ->  projet/vues3d/YAMA_3D_schematique_revC.pdf (une vue par planche)
Le cartouche reprend celui des pages 3D de l'esquisse d'origine : titre du projet, lieu, logo SABTP, bandeau gris
(année, client, auteurs, description, format), titre de la vue en bas à droite.
"""
import json, os, glob, sys
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import sys as _s, os as _o; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))), 'esquisse')); from indice import REV, REVISIONS
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/home/user/atelier-archi-ingenierie/outils'); import identite
ID = identite.depuis_projet(os.path.dirname(os.path.dirname(HERE)))   # entreprise + pays du projet (projet/IDENTITE.json)
LOGO = ID['logo']
DATE = '15/10/2026'
W, H = 1190.52, 841.92

ORDRE = ['ensemble_se', 'ensemble_no', 'axo_rdc', 'axo_etage',
         'ext_rue', 'ext_aerien', 'ext_pavillon', 'ext_entree', 'ext_jardin']   # puis vues extérieures
TITRES = {
    'ext_rue': 'Street view along the boundary wall', 'ext_aerien': 'Aerial view', 'ext_pavillon': 'Veranda and pavilion',
    'ext_entree': 'Entrance door', 'ext_jardin': 'Garden and rear',
    'ext_parking': 'Arrival - parking, veranda and south facade', 'ext_entree': 'Main entrance and veranda',
    'ext_jardin': 'East garden facade', 'ext_pavillon': 'Pavilion and garden (south)',
    'ext_arriere': 'Rear (north-west) and service side', 'ext_toit': 'Roof terrace +7.40',
    'ensemble_se': 'Overall view from the street (south-east) - boundary wall and gate',
    'ensemble_no': 'Overall view from the rear (north-west)',
    'axo_rdc': 'Ground floor - 3D cut at 1.70 above floor level',
    'axo_etage': 'First floor - 3D cut at 1.70 above floor level (+5.70)',
}
NOMS = {'KITCHEN / DINING': 'Kitchen / dining', 'SCULLERY / AFRICAN KITCHEN': 'Scullery (African kitchen)', 'EN-SUITE 1': 'En-suite 1',
        'WC': 'WC'}


def cartouche(c, titre, numero):
    c.setFillColorRGB(0, 0, 0); c.setFont('Helvetica-Bold', 26); c.drawString(28, H - 52, 'YAMA HOUSE')
    c.setFont('Helvetica', 10); c.drawString(30, H - 70, 'BRIKAMA, The Gambia')
    c.drawImage(ImageReader(LOGO), W - 210, H - 82, width=180, height=58, preserveAspectRatio=True, mask='auto')
    c.setFillColorRGB(0.85, 0.85, 0.85); c.rect(28, H - 122, W - 56, 32, stroke=0, fill=1)
    c.setFillColorRGB(0, 0, 0); c.setFont('Helvetica-Bold', 7.5)
    champs = [('PROJECT YEAR', '2026', 40, -102), ('CLIENT', 'MRS MARIAMA FATAJO JAMMEH', 40, -116), ('PRINCIPAL BY', 'E H S Fall', 470, -102),
              ('DRAFTER BY', 'A D Paye', 470, -116), ('DESCRIPTION', f'3D Schematic Design - rev. {REV}', 880, -102), ('PAPER FORMAT', 'A3', 880, -116)]
    for t, v, x, dy in champs:
        c.setFont('Helvetica-Bold', 7.5); c.drawString(x, H + dy, t); c.setFont('Helvetica', 7.5); c.drawString(x + 120, H + dy, ': ' + v)
    c.setFont('Helvetica-Bold', 11); c.drawRightString(W - 30, 30, titre)
    c.setFont('Helvetica', 7.5); c.setFillColorRGB(0.35, 0.35, 0.35)
    c.drawRightString(W - 30, 17, numero)          # (retour client 15/10) pas de note sous les images


def planche(c, png, titre, numero, etiquettes=()):
    cartouche(c, titre, numero)
    from PIL import Image as _I
    jpg = png[:-4] + '.jpg'                    # JPEG qualité 88 : PDF < 10 Mo (règle DOC-026)
    _I.open(png).convert('RGB').save(jpg, quality=88, optimize=True)
    img = ImageReader(jpg); iw, ih = img.getSize()
    x0, y0, x1, y1 = 28, 45, W - 28, H - 130
    k = min((x1 - x0) / iw, (y1 - y0) / ih); w, h = iw * k, ih * k
    ox, oy = x0 + (x1 - x0 - w) / 2, y0 + (y1 - y0 - h) / 2
    c.drawImage(img, ox, oy, width=w, height=h)
    c.setStrokeColorRGB(0.6, 0.6, 0.6); c.setLineWidth(0.4); c.rect(ox, oy, w, h)
    for e in etiquettes:
        t = NOMS.get(e['texte'], e['texte'].title().replace('Wc', 'WC'))
        px, py = ox + e['x'] * w, oy + e['y'] * h
        c.setFont('Helvetica-Bold', 8.5); tw = c.stringWidth(t, 'Helvetica-Bold', 8.5)
        c.setFillColorRGB(1, 1, 1); c.setFillAlpha(0.85); c.roundRect(px - tw / 2 - 4, py - 4, tw + 8, 14, 3, stroke=0, fill=1); c.setFillAlpha(1)
        c.setFillColorRGB(0.1, 0.1, 0.35); c.drawCentredString(px, py, t)
    c.showPage()


def main():
    R = os.path.join(HERE, 'rendus')
    vues = [v for v in ORDRE if os.path.exists(os.path.join(R, v + '.png'))]
    inter = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(R, 'int_*.png')))
    # ordre des vues intérieures : RDC puis étage, comme une visite
    ordre_int = ['entrance_hall', 'living_room', 'kitchen_dining', 'scullery_african_kitchen', 'wc_gf', 'corridor', 'bedroom_1', 'en_suite_1',
                 'bedroom_2', 'shared_bath', 'bedroom_3', 'landing', 'family_lounge', 'wc_ff', 'master_bedroom', 'walk_in_dressing',
                 'master_bath', 'roof_terrace']
    inter.sort(key=lambda n: ordre_int.index(n[4:]) if n[4:] in ordre_int else 99)
    sortie = os.path.join(HERE, f'YAMA_3D_schematique_rev{REV}.pdf')
    c = canvas.Canvas(sortie, pagesize=(W, H))
    n = 0
    for v in vues + inter:
        n += 1
        meta = json.load(open(os.path.join(R, v + '.json')))
        titre = TITRES.get(v)
        if not titre:
            nom = NOMS.get(meta['titre'], meta['titre'].title().replace('Wc', 'WC'))
            niv = 'ground floor' if '_gf' in v or meta['titre'] in ('ENTRANCE HALL', 'LIVING ROOM', 'KITCHEN / DINING', 'SCULLERY / AFRICAN KITCHEN',
                                                                      'CORRIDOR', 'BEDROOM 1', 'BEDROOM 2', 'BEDROOM 3', 'EN-SUITE 1', 'SHARED BATH') else 'first floor'
            titre = '%s (%s)' % (nom, niv)
        planche(c, os.path.join(R, v + '.png'), titre, '3D-%02d' % n, meta.get('etiquettes', []))
    c.save()
    json.dump({v: '3D-%02d' % (i + 1) for i, v in enumerate(vues + inter)}, open(os.path.join(HERE, 'index_planches.json'), 'w'), indent=1)
    print(sortie, n, 'planches')
    return sortie, n


if __name__ == '__main__':
    main()
