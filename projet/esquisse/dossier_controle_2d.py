"""YAMA HOUSE - jeu 2D complet et dossier de contrôle 2D (porte « 2D validée avant rendu 3D », demande client 15/10).

Le contrôle 2D reprend TOUJOURS le jeu complet, même si un seul niveau change, dans cet ordre (client 15/10) :
état des lieux, démolition, nouveaux travaux ; surfaces RDC, étage ; circulation RDC, étage ; surfaces puis circulation
de la terrasse ; plans d'architecture RDC, étage, toiture ; façades ; coupes ; clôture.
python3 -I projet/esquisse/dossier_controle_2d.py  ->  projet/esquisse/YAMA_Controle_2D_rev<REV>.pdf
Le même jeu (jeu_2d) forme la partie « plans techniques » du dossier client, après la 3D.
"""
import glob, json, os, sys, pymupdf
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from indice import REV, MODIFIEES

SRC = os.path.join(ROOT, 'projet', 'source', 'YAMA_HOUSE_Architectural_Design_realistic_v2.pdf')
ORIGINE = {'SD-001': 15, 'SD-002': 16, 'SD-003': 17}          # pages du dossier d'origine (état des lieux, démolition, travaux)
ORDRE_2D = ['SD-001', 'SD-002', 'SD-003', 'SD-004A', 'SD-005A', 'SD-004B', 'SD-005B', 'SD-006A', 'SD-006B',
            'SD-004', 'SD-005', 'SD-006', 'SD-007', 'SD-008', 'SD-009', 'SD-010', 'SD-011', 'SD-012', 'SD-013']
REP = {'Ech : 1 : 100': 'Scale 1:100', '1 : 100': '1:100', 'Existing wall (120 mm hollow block)': 'Existing wall (0.12 hollow block)',
       'NEW wall (150 mm block)': 'NEW wall (0.15 block)', 'Existing wall kept (120 mm)': 'Existing wall kept (0.12)'}


def page_origine(src, i):
    """Planche d'origine, aplatie seule, en anglais et en mètres ; AUCUN filigrane ni tampon (règle DOC-056)."""
    t_ = pymupdf.open(); t_.insert_pdf(src, from_page=i, to_page=i); pg = t_[0]; pg.clean_contents()
    poses = []
    for b in pg.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            for sp in l['spans']:
                tt = ' '.join(sp['text'].split())
                if tt.startswith('Ech :'): tt = 'Ech : 1 : 100'
                if tt in REP:
                    r = pymupdf.Rect(sp['bbox']); pg.add_redact_annot(r, fill=(1, 1, 1)); poses.append((r, REP[tt], sp['size']))
    pg.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
    for r, t, sz in poses:
        pg.insert_text((r.x0, r.y1 - 1.5), t, fontsize=sz, fontname='helv', color=(0.3, 0.3, 0.3) if 'Scale' in t else (0, 0, 0))
    return t_


def jeu_2d():
    src = pymupdf.open(SRC); out = pymupdf.open()
    for m in ORDRE_2D:
        if m in ORIGINE: out.insert_pdf(page_origine(src, ORIGINE[m])); continue
        f = sorted(glob.glob(os.path.join(HERE, '%s_%s_*.pdf' % (m, REV))))
        if not f: sys.exit('planche absente : %s' % m)
        out.insert_pdf(pymupdf.open(f[0]))
    return out


if __name__ == '__main__':
    import rapport_esquisse as ra
    T = json.load(open(os.path.join(ROOT, 'projet', 'maquette', 'maquette.json')))['site']['toiture']
    lignes = [(a, b % T['niveau_avaloir'] if '%' in b and 'outlets at' in b else b) for a, b in ra.CHANGES_D]
    lignes += [('', ''), ('TO VALIDATE', 'Complete 2D set attached (%d sheets; changed in this revision: %s).' % (len(ORDRE_2D), ', '.join(MODIFIEES))),
               ('', 'Once validated, the 3D views are rendered and the client set is assembled.')]
    p1 = os.path.join(HERE, '_c2d.pdf'); ra.page_changements(p1, lignes, 'CHANGES TO CHECK BEFORE 3D', registre=False)
    out = pymupdf.open(); out.insert_pdf(pymupdf.open(p1)); os.remove(p1)
    out.insert_pdf(jeu_2d())
    sortie = os.path.join(HERE, 'YAMA_Controle_2D_rev%s.pdf' % REV); out.save(sortie, garbage=4, deflate=True)
    print(sortie, len(out), 'pages')
