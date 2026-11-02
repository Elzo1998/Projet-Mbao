"""YAMA HOUSE - rapport d'esquisse séparé (retour client 15/10, indice D) : résumé des changements par indice, registre
des planches, notes et finitions de chaque planche (retirées des planches du dossier client), points ouverts.

python3 -I projet/esquisse/rapport_esquisse.py  ->  projet/esquisse/YAMA_HOUSE_Design_Report_rev<REV>.pdf
"""
import os, sys, json, pymupdf
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, '/home/user/atelier-archi-ingenierie/outils'); sys.path.insert(0, HERE)
import dessin_plan as dp
from dessiner_plans import CARTO, DATE, ID
from reportlab.pdfgen import canvas
import sys as _s, os as _o; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))), 'esquisse')); from indice import REV, REVISIONS

SRC = os.path.join(ROOT, 'projet', 'source', 'YAMA_HOUSE_Architectural_Design_realistic_v2.pdf')
import glob, json

CHANGES_D = [
    ('REVISION D', 'Client review of revision C (15/10/2026).'),
    ('ROOF', 'Three rainwater outlets (north-west, north-east and south-west corners of the main roof); falls 1.5 % to the'),
    ('', 'nearest outlet; outlets at +%.2f, high points +7.40, parapet +8.40.'),
    ('HALL', 'Plant pot removed (it stood in line with door D05); new check: 1.50 manoeuvre area clear in front of every door.'),
    ('CORRIDOR', 'Linen cupboard removed (it narrowed the access to bedroom 3, door D08, to 0.55).'),
    ('TILING', 'Kitchen and scullery: wall tiles full height on all walls.'),
    ('BEDROOM 3', 'Main window W07 centred on the room (1.20 to 3.20); its own RC canopy.'),
    ('CANOPY', 'One RC canopy over D10 and W08 (same room: scullery), 4.43 to 7.58.'),
    ('LABELS', 'Room names and areas centred in each room.'),
    ('SCULLERY', 'High vent grille and D10 low grille removed from the drawings until stage 3 (ventilation design).'),
    ('DRAWINGS', 'Client set: 3D views first, then the drawings; no notes on the sheets (this report); zoning in plain colours.'),
    ('', 'Plans: what is seen below the cut level (lower floor, garden, low terrace) is drawn in half-tone.'),
    ('', 'Order: existing, demolition, new works; zoning and circulation (ground floor, first floor, roof terrace); plans;'),
    ('', 'elevations; sections. SD-002 / SD-003 are the rev. A sheets (openings not yet updated): redrawn from the model at'),
    ('', 'stage 3. New sheets SD-006A / SD-006B: zoning and circulation of the roof terrace.'),
]
CHANGES = [
    ('REVISION C', 'Engineer review of revision B (15/10/2026). Revision B changes are kept (see revision B, summary sheet).'),
    ('STANDARDS', 'All doors h 2.20. Windows max 2.00 wide, 2 sliding panels: 1.60 / 2.00 x 1.40 (sill 0.80); over worktops'),
    ('', '1.40 / 2.00 x 1.25 (sill 0.95); bathrooms and WCs 1.00 / 2.00 x 0.60 (sill 1.60). Sliding doors 2.00 or 3.00 x 2.20 only.'),
    ('', 'RC canopies (0.60 deep, window + 0.10 each side, 0.10 thick) over every unprotected window.'),
    ('DIMENSIONS', 'Plans dimensioned on a grid of axes following every wall and column, common to both floors (same name on'),
    ('', 'both floors), chains outside the plan (bottom and left). Opening dimensions will be on the joinery plan.'),
    ('KITCHEN', 'L-shaped worktop along the whole north wall, side-by-side fridge, cooker + oven with hood at the far end,'),
    ('', 'wall units (never in front of a window: one 2.00 window over the sink); island and table for 6 as one T unit'),
    ('', 'against the stair wall; sliding door from the hall (coffee bar and pantry removed).'),
    ('SCULLERY', 'African kitchen: zone for portable gas cookers, worktop with laundry sink, pot shelves, washing machine, small'),
    ('', 'worktop with wall units; no fixed gas bench, no hood, no outdoor gas cage. Door D09 moved to the corner.'),
    ('DOORS', 'Entrance door 1.50 = 1.00 + 0.50, armoured steel, wood-effect finish. Exterior doors: steel. Every swing door'),
    ('', 'opens against a wall (D05 against an extended partition, D09, D12, D16 moved). First-floor WC: swing door outwards.'),
    ('', 'Landing -> roof terrace D13: 1.00 swing door, steel frame, armoured glass.'),
    ('MASTER BATH', 'Redesigned: closed WC (sliding door, small hopper window), walk-in shower 2.00 x 1.20, built-in 2-person'),
    ('', 'jacuzzi + bathtub (one unit) on a tiled deck under the high window, double vanity 1.80 with lit mirror.'),
    ('DRESSING', 'Upholstered bench in the centre (0.70 clear each side), sliding-door storage. Hall: console removed.'),
    ('TERRACE', 'Pergola: no posts on the bedroom side (beams on base plates in the wall), one intermediate post per beam.'),
    ('', 'Planters along the guardrail removed (climbable); 2 plant pots 0.60 off the guardrail. Outdoor floors +3.95.'),
    ('STAIRS', '7 + 13 risers to the first floor, 13 + 7 to the roof (landings +1.79, +6.21, +7.40 in the stair penthouse);'),
    ('', 'guardrails h 1.00 on every open side of flights and landings; arrival upstairs kept free. W12: fixed glazing.'),
    ('ROOF', 'Single rainwater outlet at the north-east corner; PV zone moved to the south-west; penthouse roof falls to a'),
    ('', 'spout; penthouse walls aligned on the first-floor walls; door D20 with 0.15 upstand; 2 x 2000 L tanks dia. 1.30.'),
    ('STRUCTURE', 'For the engineer: transfer beams where an upper wall is not carried by a wall below (checked on the model):'),
    ('', 'master bedroom east wall (span 5.60), terrace / penthouse south wall (5.07), penthouse west wall (4.15),'),
    ('', 'first-floor WC partition (1.30: beam or lightweight partition). Shown in the notes of SD-005, S1 and S2.'),
    ('', 'Point loads: the 4 terrace pergola posts stand on the slab over the living room / hall.'),
    ('BATHROOMS', 'Ground-floor shower rooms: walk-in showers with a fixed glass screen (entry 0.70); shower windows: frosted hopper.'),
    ('PARKING', '2 x Land Cruiser 300 nose in (doors: one at a time between the cars); sliding gate widened to 6.20; wicket'),
    ('', 'door onto a pedestrian lane 0.90 at ground (0.78 at mirror height) from the gate to the entrance.'),
    ('PERGOLAS', 'Timber slats kept + compact polycarbonate roof above (0.006 thick, to be confirmed on site, UV-protected, opal, sourced in Dakar),'),
    ('', '3 % fall to a gutter: SD01, SD04 and D13 sheltered from rain.'),
    ('LEVELS', 'Outdoor floors 0.05 below indoor floors (veranda / pavilion +0.55, terrace / balconies +3.95), threshold channels.'),
    ('', 'Roof +7.40 at the high points, falls 1.5 % to the outlet (+7.12): parapet 1.00 above the highest point.'),
    ('ZONING', 'New sheets before the architectural plans: functional zoning (one colour per type of room, areas computed'),
    ('', 'from the model) SD-004A / SD-005A, then circulation SD-004B / SD-005B (routes from the gate to every room,'),
    ('', 'computed as shortest paths around walls and furniture, with their length and narrowest clear width).'),
    ('DRAWINGS', 'Sketch-style graphics (light colours, prints well in black and white); grid axes also on elevations and sections.'),
    ('3D VIEWS', 'New schematic 3D views generated from the same model: overall views, 3D cuts of each floor, one view per main room.'),
    ('NOT YET DONE', 'SD-002 / SD-003 (demolition, new works) superseded: reissued at stage 3 with the technical design (joinery'),
    ('', 'sheets, structure incl. transfer beams, ceilings, electrical, plumbing incl. rainwater, AC).'),
]


def page_changements(chemin, sections, titre_page='SUMMARY OF CHANGES', registre=True):
    """SD-000 : résumé des changements, sur autant de pages que nécessaire (saut de page avant le bas du cadre,
    contrôle DOC-042), puis registre des planches."""
    W, H = 1190.52, 841.92
    c = canvas.Canvas(chemin, pagesize=(W, H)); nb = [1]

    def entete(suite=False):
        c.setFillColorRGB(0, 0, 0.5); c.setFont('Helvetica-Bold', 20)
        c.drawString(60, H - 90, titre_page + (' (continued)' if suite else ''))
        c.setFillColorRGB(0.3, 0.3, 0.3); c.setFont('Helvetica', 11)
        c.drawString(60, H - 112, 'YAMA HOUSE - schematic design - revision %s - %s' % (REV, DATE))
        return H - 150

    def fin_page():
        dp.legende_et_cartouche(c, dict(CARTO, vue=f'Revision {REV}', planche='REPORT - %s (%d)' % (titre_page.split()[0], nb[0]), sous_titre=titre_page.capitalize(), echelle='-'),
                                {'nord': False, 'titre_vue': '', 'numero_vue': ''}, W, H)
        c.showPage(); nb[0] += 1

    BAS = 70                                   # au-dessous : nouvelle page (cadre intérieur à y 40)
    y = entete()
    groupes = []
    for t, txt in sections:
        if t or not groupes: groupes.append([])
        groupes[-1].append((t, txt))
    for g in groupes:
        if y - 6 - 15 * len(g) < BAS:
            fin_page(); y = entete(True)
        for t, txt in g:
            if t:
                y -= 6; c.setFillColorRGB(0.7, 0.29, 0.0); c.setFont('Helvetica-Bold', 10); c.drawString(60, y, t)
            c.setFillColorRGB(0, 0, 0); c.setFont('Helvetica', 10); c.drawString(200, y, txt); y -= 15
    if not registre:
        fin_page(); c.save(); return
    reg = [('3D-01..%02d' % len(json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'vues3d', 'index_planches.json')))), 'Schematic 3D views (overall, floor cuts, rooms) - first in the set', REV),
           ('SD-001', 'Existing ground floor (survey)', 'A'),
           ('SD-004A', 'Functional zoning - ground floor', REV), ('SD-005A', 'Functional zoning - first floor', REV),
           ('SD-004B', 'Circulation - ground floor + site', REV), ('SD-005B', 'Circulation - first floor', REV),
           ('SD-004', 'Ground floor plan + site', REV), ('SD-005', 'First floor plan', REV), ('SD-006', 'Roof plan + site', REV),
           ('SD-007', 'South elevation - street', REV), ('SD-008', 'East elevation - garden / entrance', REV),
           ('SD-009', 'North elevation', REV), ('SD-010', 'West elevation', REV), ('SD-011', 'Section S1-S1', REV),
           ('SD-012', 'Section S2-S2', REV), ('SD-013', 'Boundary wall + gate, street elevation', REV),
           ('SD-002/003', 'Demolition / new works (superseded, reissued at stage 3)', 'A')]
    lignes = (len(reg) + 1) // 2
    if y - 30 - 13 * lignes < BAS:
        fin_page(); y = entete(True)
    y -= 14; c.setFillColorRGB(0, 0, 0.5); c.setFont('Helvetica-Bold', 11); c.drawString(60, y, 'DRAWING REGISTER'); y -= 16
    c.setFont('Helvetica', 9.5); c.setFillColorRGB(0, 0, 0)
    for i, (n, t, r) in enumerate(reg):
        x = 60 + (i // lignes) * 420; yy = y - (i % lignes) * 13
        c.drawString(x, yy, n); c.drawString(x + 55, yy, t); c.drawString(x + 330, yy, 'rev. ' + r)
    fin_page(); c.save()




OUVERTS = [
    ('OPEN POINTS', 'For the client: roof overflow (emergency outlets through the parapet), kitchen work triangle, stiffeners,'),
    ('', 'canopy over SD02, door D06 swing, TV - sofa distance, chair in front of D17.'),
    ('SUGGESTIONS', 'Cross ventilation of bedrooms 1 and 3 (one window each); guard house / service WC.'),
    ('NOT PROVEN', 'Polycarbonate 0.006 (to be confirmed on site; suppliers in Dakar, no written quotation); sliding gate rail'),
    ('', 'not designed; DXF of elevations / sections checked automatically, not by eye.'),
    ('3D', 'Schematic views: short focal length in the WCs; laundry room of the first floor without a view.'),
]


if __name__ == '__main__':
    T = json.load(open(os.path.join(ROOT, 'projet', 'maquette', 'maquette.json')))['site']['toiture']
    d_ = [(a, b % T['niveau_avaloir'] if '%' in b and 'outlets at' in b else b) for a, b in CHANGES_D]
    parties = []
    f1 = os.path.join(HERE, '_r1.pdf'); page_changements(f1, d_ + [('', '')] + CHANGES, 'SUMMARY OF CHANGES'); parties.append(f1)
    notes = []
    for f in sorted(glob.glob(os.path.join(HERE, 'notes', '*.json'))):
        n = json.load(open(f))
        for k, b in enumerate(n['blocs']):
            lignes = [l[0] for l in b['lignes'] if l[0].strip()]
            if not lignes: continue
            notes.append((n['planche'].replace(' ', '') if k == 0 else '', '%s - %s' % (b['titre'].split(' (')[0], lignes[0].strip())))
            notes += [('', l) for l in lignes[1:]]
    f2 = os.path.join(HERE, '_r2.pdf'); page_changements(f2, notes, 'SHEET NOTES AND FINISHES', registre=False); parties.append(f2)
    f3 = os.path.join(HERE, '_r3.pdf'); page_changements(f3, OUVERTS, 'OPEN POINTS', registre=False); parties.append(f3)
    out = pymupdf.open()
    for f in parties: out.insert_pdf(pymupdf.open(f)); os.remove(f)
    out.set_metadata({'title': 'YAMA HOUSE - Design report - revision %s' % REV, 'author': ID['signature']})
    sortie = os.path.join(HERE, 'YAMA_HOUSE_Design_Report_rev%s.pdf' % REV); out.save(sortie, garbage=4, deflate=True)
    print(sortie, len(out), 'pages')
