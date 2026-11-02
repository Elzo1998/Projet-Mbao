"""YAMA HOUSE - planches de plans de l'esquisse (indice C) depuis la maquette.

python3 -I projet/esquisse/dessiner_plans.py   ->  projet/esquisse/SD-004_C_Ground_Floor.pdf/.dxf, SD-005_C_First_Floor.pdf/.dxf
"""
import json, math, os, sys, re
from shapely.geometry import Polygon
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
ATELIER = '/home/user/atelier-archi-ingenierie'
sys.path.insert(0, os.path.join(ATELIER, 'outils'))
import dessin_plan as dp
import symboles
import sys as _s, os as _o; _s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))), 'esquisse')); from indice import REV, REVISIONS, noter

PDF = os.path.join(ROOT, 'projet', 'source', 'YAMA_HOUSE_Architectural_Design_realistic_v2.pdf')
MAQ = json.load(open(os.path.join(ROOT, 'projet', 'maquette', 'maquette.json')))
DATE = '15/10/2026'
import identite; ID = identite.depuis_projet(ROOT)      # entreprise + pays du projet (projet/IDENTITE.json)
CARTO = {'logo': ID['logo'],
         'phase': 'SCHEMATIC DESIGN', 'projet': 'YAMA HOUSE', 'lieu': 'BRIKAMA, The Gambia', 'echelle': '1:100',
         'client': 'MRS M. F. JAMMEH', 'principal': ID['equipe']['principal'], 'dessinateur': ID['equipe']['dessinateur'], 'approbation': ID['equipe']['approbation'],
         'contacts': ID['contacts'],
         'date_indice': f'%s  (SD)  rev. {REV}' % DATE}
AXES = dp.quadrillage(dict(MAQ['niveaux'], RF=dp.niveau_toiture(MAQ)))     # RDC, étage, toiture (édicule) : noms communs
# position des chaînes (bas, gauche) et étendue des axes (haut, droite), en mètres
GRILLE = {'GF': {'bas': -7.55, 'gauche': -2.35, 'haut': 14.9, 'droite': 13.7}, 'FF': {'bas': -7.55, 'gauche': -2.35, 'haut': 14.9, 'droite': 13.7}}
CABINET_SUPPRIME = [12.53, 6.1, 12.98, 7.1]      # meuble à chaussures (R8) : ses traits d'origine ne doivent plus être repris
ZONES_ESCALIER = {'GF': [8.23, 5.95, 12.98, 9.60], 'FF': [8.37, 5.75, 12.98, 9.60]}
COUPES = {'S1': {'x': 10.43, 'regard': (-1, 0)}, 'S2': {'y': 7.65, 'regard': (0, 1)}}   # repères S1 / S2 ; regard = sens de vue (dessiner_vues : ouest, nord)
COUL_COUPE = (0.30, 0.30, 0.30)   # flèches pleines au gris des bulles (la charte grise les traits saturés)


def fleche_regard(D, centre, regard, r=0.4):
    """Repère de coupe façon Revit (client 16/10, image de référence) : triangle plein dont la base est le diamètre de la
    bulle perpendiculaire au regard et dont les côtés sont tangents au cercle ; à dessiner AVANT la bulle (fond blanc),
    seules les deux cornes et la pointe restent visibles."""
    (x, y), (dx, dy) = centre, regard; px, py = -dy, dx
    d = 1.34 * r                                         # pointe (proportion de la référence)
    w = d * math.tan(math.asin(r / d))                   # demi-base : côtés tangents au cercle
    D.poly([(x + px * w, y + py * w), (x + dx * d, y + dy * d), (x - px * w, y - py * w)], 'A-SECT', 0.2, COUL_COUPE, fond=COUL_COUPE)


ZONES_EXTERIEURES_ANCIEN = {'GF': [[8.31, -3.52, 11.95, -2.68], [9.31, -2.27, 10.95, -1.53], [8.31, -1.87, 9.10, -1.08], [11.16, -1.87, 11.95, -1.08]], 'FF': [[0.46, -1.77, 6.0, -0.02], [13.12, 10.38, 14.57, 13.62]]}
ETIQUETTES = {'GF': {'KITCHEN / DINING': (11.55, 10.9), 'WC': (6.02, 10.55), 'SCULLERY / AFRICAN KITCHEN': (6.3, 12.95)},
              'FF': {'WALK-IN DRESSING': (1.95, 7.82), 'WC': (4.78, 10.50), 'MASTER BATH': (2.52, 11.45)}}


def surface_affichee(pc):
    a, c = pc.get('surface_annoncee'), pc['surface_calculee']
    if a and abs(c - a) / a > 0.05:
        return a, True        # limite conventionnelle d'un espace ouvert (séjour / hall, palier + vide + escalier)
    return round(c, 1), False


def planche(niv, titre, sous_titre, numero, num_vue, notes):
    M = MAQ['niveaux'][niv]
    D, cadre_m = construire_dessin(niv)
    return rendre_planche(D, cadre_m, niv, M, titre, sous_titre, numero, num_vue, notes)


from shapely.geometry import box as _bx


def construire_dessin(niv):
    """Dessin du plan d'un niveau (sans légende ni cartouche) : réutilisé par les fichiers de contrôle."""
    M = MAQ['niveaux'][niv]
    D = dp.Dessin()
    emprise = MAQ['emprise']
    if niv == 'GF':
        dp.site(D, MAQ['site'], MAQ['emprise'])
    else:   # (client 15/10) ce qui est vu en contrebas de l'étage (pavillon, deck, jardin, parking) : en demi-teinte
        dp.site(D, MAQ['site'], MAQ['emprise'])
        dp.demi_teinte(D, 0, (-4.6, -9.4, 21.7, 17.3))
        couvre = [_bx(*emprise)] + [_bx(*s_['rect']) for s_ in (M.get('exterieurs') or {}).get('sols', [])]
        for g_ in couvre:             # dalle de l'étage : masque blanc (rien n'est vu dessous)
            D.poly(list(g_.exterior.coords), 'A-ANNO', 0.0, (1, 1, 1), fond=(1, 1, 1))
    dp.exterieurs_etage(D, M)
    u = dp.murs(D, M)
    dp.poteaux(D, M)
    g = GRILLE[niv]
    dp.dessiner_quadrillage(D, AXES, niv, emprise, g['bas'], g['gauche'], g['haut'], g['droite'])
    # symboles d'origine : escalier et mobilier extérieur seulement (le reste est généré depuis la maquette)
    sym = []      # (3e passage) plus aucun symbole recopié du dessin d'origine : tout le mobilier vient de la maquette
    from shapely.geometry import box as _box
    sym = [s_ for s_ in sym if not (niv == 'GF' and Polygon(s_[0] + [s_[0][0]]).buffer(0.001).within(_box(*CABINET_SUPPRIME).buffer(0.02)) if len(s_[0]) > 2
                                    else all(_box(*CABINET_SUPPRIME).buffer(0.02).contains(_box(p_[0], p_[1], p_[0] + 1e-6, p_[1] + 1e-6)) for p_ in s_[0]))]
    for pts, ep, coul, fond in sym:
        D.poly(pts, 'A-FURN', max(ep, 0.15), tuple(min(1, c * 0.9 + 0.05) for c in coul), fond=fond, ferme=False)
    symboles.dessiner(D, M, u)
    if niv == 'FF':
        dp.escaliers(D, M, dessous=[e for e in MAQ['niveaux']['GF']['escaliers'] if e.get('nom') == 'B'])
    else:
        dp.escaliers(D, M)
    for m in M['mobilier']:          # rangement sous la volée : contour pointillé par-dessus l'escalier, étiquette dans le hall
        if 'under stair' in m['nom']:
            r = m['rect']; D.poly([(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])], 'A-FURN', 0.4, (0.35, 0.35, 0.35), tirets=(2, 1.5))
            D.texte(((r[0] + r[2]) / 2, r[1] - 0.22), 'shoe cabinet under the stair (h 0.90)', 0.10, 'A-FURN', coul=(0.3, 0.3, 0.3))
    dp.ouvertures(D, M, u)
    dp.grilles(D, M)
    dp.auvents(D, M)
    for pc in M['pieces']:
        s, conv = surface_affichee(pc); pc['surface_affichee'] = s
        if pc.get('nom') in ETIQUETTES[niv]: pc['etiquette_force'] = ETIQUETTES[niv][pc['nom']]
    for t in (M.get('exterieurs') or {}).get('annotations', []):
        D.texte(t['pos'], t['texte'], t.get('h', 0.12), 'A-ANNO', t.get('gras', False), rot=t.get('rot', 0), coul=(0.25, 0.25, 0.25))
    dp.pieces(D, M)
    dp.etiquettes_ouvertures(D, M, emprise)
    # repères de coupe
    for nom, c in COUPES.items():
        if 'x' in c:
            x = c['x']; D.ligne((x, emprise[1] - (6.2 if niv == 'GF' else 1.9)), (x, emprise[3] + 2.5), 'A-ANNO', 0.5, (0.7, 0.29, 0.0), tirets=(8, 3, 2, 3))
            for y in (emprise[1] - (6.6 if niv == 'GF' else 4.2), emprise[3] + 2.92):   # pointe Revit entre le bord du cadre et la cote PLOT
                fleche_regard(D, (x, y), c['regard'])
                D.cercle((x, y), 0.4, 'A-ANNO', 0.6, (0.7, 0.29, 0.0), fond=(1, 1, 1)); D.texte((x, y), nom, 0.20, 'A-ANNO', True, coul=(0.7, 0.29, 0.0))
        else:
 
            xg = GRILLE[niv]['gauche'] - 1.35        # colonne des bulles d'axes ; pointe Revit (demi-base 0.60) dans le cadre (DOC-042)
            y = c['y']; D.ligne((xg + 0.4, y), (emprise[2] + (3.0 if niv == 'GF' else 2.6), y), 'A-ANNO', 0.5, (0.7, 0.29, 0.0), tirets=(8, 3, 2, 3))
            for x in (xg, emprise[2] + (3.4 if niv == 'GF' else 3.0)):
                fleche_regard(D, (x, y), c['regard'])
                D.cercle((x, y), 0.4, 'A-ANNO', 0.6, (0.7, 0.29, 0.0), fond=(1, 1, 1)); D.texte((x, y), nom, 0.20, 'A-ANNO', True, coul=(0.7, 0.29, 0.0))
    D.texte((6.4, 7.35 if niv == 'GF' else 6.6), 'FFL +%.2f' % M['z'], 0.15, 'A-ANNO', False, coul=(0.7, 0.29, 0.0))
    if niv == 'GF':
        D.texte((2.0, -9.15), 'STREET (south)', 0.20, 'A-SITE', True)
        cadre_m = (-4.6, -9.4, 21.7, 17.3)
    else:   # (client 15/10) même cadre que le RDC et la toiture : toute la parcelle et le mur de clôture
        cadre_m = (-4.6, -9.4, 21.7, 17.3)
    return D, cadre_m


def rendre_planche(D, cadre_m, niv, M, titre, sous_titre, numero, num_vue, notes):
    # légende : tableau des surfaces (+ totaux et extérieurs), légende graphique, révisions, notes
    lignes = []; tot = 0.0
    for pc in sorted([p for p in M['pieces'] if p.get('nom') and 'TERRACE' not in p['nom']], key=lambda p: -p['surface_calculee']):
        s_, conv = surface_affichee(pc); tot += s_
        lignes.append(('%s%s' % (pc['nom'].title().replace('Wc', 'WC').replace('En-Suite', 'En-suite'), ' (*)' if conv else ''), '%.1f m²' % s_))
    lignes.append(('*Total habitable', '%.1f m²' % tot))
    for nom_, val in EXTERIEURS_SURF[niv]:
        lignes.append((nom_, val))
    legende = {'titre_vue': titre, 'sous_titre_vue': f'Scale 1:100   -   Revision {REV}', 'numero_vue': num_vue,
               'blocs': [{'titre': 'AREAS (net, computed from the model)', 'lignes': lignes + [('(*) conventional limit of an open space', '')]},
                         {'titre': 'REVISIONS', 'lignes': REVISIONS},
                         {'titre': 'ABBREVIATIONS', 'lignes': [('EF extract fan; VG vent grille; RWO rainwater outlet', ''),
                                                               ('SxS side-by-side fridge; WM washing machine', '')]}],
               'symboles': SYMBOLES}
    carto = dict(CARTO, vue='Plan View', planche=numero, sous_titre=sous_titre)
    noter(numero, titre, [{'titre': 'FINISHES (from the model)', 'lignes': FINITIONS_LEG[niv]}, {'titre': 'NOTES', 'lignes': [(n, '') for n in notes]}])   # rapport séparé (indice D)
    sortie = os.path.join(HERE, '%s_%s_%s' % (numero.replace(' ', ''), REV, titre.split(' - ')[1].replace(' ', '_')))
    dp.rendre_pdf(D, sortie + '.pdf', {'pt': (16, 40, 745, 822), 'm': cadre_m}, carto, legende)
    dp.rendre_dxf(D, sortie + '.dxf')
    return sortie


EXTERIEURS_SURF = {'GF': [('Veranda 1.20 (+0.55)', '14.6 m²'), ('Pavilion deck (+0.55)', '18.8 m²'), ('Planted strips', '38.8 m²'), ('Plot', '518.0 m²')],
                   'FF': [('Roof terrace (pergola)', '%.1f m²' % next(p['surface_calculee'] for p in MAQ['niveaux']['FF']['pieces'] if p.get('nom') and 'TERRACE' in p['nom'])), ('Balcony south', '10.1 m²'), ('Balcony east (garden)', '4.9 m²'), ('Void over hall', '5.8 m²')]}
FINITIONS_LEG = {
    'GF': [('Kitchen, scullery, baths, WC: anti-slip R11 floor', ''), ('Baths, WC: wall tiles full height', ''),
           ('Kitchen: splashback 0.90-1.50 (to the hood', ''), ('   behind the cooker); scullery: tiles 0.90-1.50,', ''),
           ('   full height around the gas zone', ''), ('Bedrooms: wood-effect porcelain; accent wall', ''),
           ('   behind the bed head', ''), ('Living, hall: porcelain 0.60 x 0.60; paint', ''), ('Veranda, pavilion: anti-slip R11', '')],
    'FF': [('Master bath, WC: anti-slip R11, wall tiles', ''), ('   full height; shower: anti-slip R11', ''),
           ('Bedroom, dressing: wood-effect porcelain', ''), ('Landing, lounge: porcelain 0.60 x 0.60', ''),
           ('Terrace, balconies: anti-slip R11 (outdoor)', '')]}
SYMBOLES = [({'ep': 0.6, 'coul': (0.23, 0.24, 0.26), 'tirets': [1, 1]}, 'security grille (inside, ground floor)'),
            ({'ep': 0.4, 'coul': (0.7, 0.29, 0.0), 'tirets': [3, 2]}, 'overhead: RC canopy 0.60, wall units, hood'),
            ({'ep': 0.4, 'coul': (0.55, 0.30, 0.20), 'tirets': [6, 2, 1, 2]}, 'grid axis (wall / column centre line)'),
            ({'ep': 1.4, 'coul': (0.44, 0.55, 0.61)}, 'glazed guardrail h 1.00'),
            ({'ep': 0.6, 'coul': (0.1, 0.1, 0.1)}, 'sliding aluminium window / door (2 rails)')]

NOTES_GF = ['Dimensions between grid axes (wall and column centre',
            '   lines); overall dimensions to outer faces. Grid',
            '   common to both floors. Openings: joinery plan.',
            'Doors h 2.20; windows 1.60 / 2.00 x 1.40 (sill 0.80),',
            '   over worktops 1.40 / 2.00 x 1.25, wet rooms',
            '   1.00 / 2.00 x 0.60; sliding doors 3.00 x 2.20.',
            'RC canopies 0.60 over unprotected windows.',
            'Kitchen: L-shaped worktop, side-by-side fridge,',
            '   cooker + oven with hood, wall units; island and',
            '   table for 6 in one T unit against the stair wall.',
            '   Sliding door from the hall (parks on the stair wall).',
            'Scullery (African kitchen): portable gas cookers zone,',
            '   worktop + laundry sink, WM, pot shelves; no fixed',
            '   gas bench, no hood, no outdoor gas cage.',
            'Entrance door 1.50 (1.00 + 0.50): armoured steel,',
            '   wood-effect finish. Exterior doors: steel.',
            'D05 opens against the extended hall partition.',
            'Security grilles on all windows; folding grilles',
            '   at the sliding doors.',
            'Stair: 7 + 13 risers 0.17 (6 + 12 treads 0.27), w 1.10,',
            '   landing +1.79; guardrails h 1.00 on open sides;',
            '   arrival upstairs kept free (guardrail stops at it).',
            'Shower rooms: walk-in showers with fixed glass screen',
            '   (entry 0.70); shower windows W02, W05: frosted hopper.',
            'Headroom over the landing +1.79: 2.01 under the slab',
            '   edge (flat slab, no downstand beam at the opening).',
            'Parking: 2 x Land Cruiser 300 (5.15 x 2.00), nose in;',
            '   doors: 0.90 pedestrian lane (west), 0.89 between the',
            '   cars (one door at a time), 0.80 at the east wall.',
            'Sliding gate 6.20, wicket 0.90 onto the pedestrian lane',
            '   (lane 0.90 at ground, 0.78 at mirror height).',
            'Pergolas: timber slats + compact polycarbonate roof',
            '   above (0.006 thick, to be confirmed on site; UV both faces, opal; sourced in Dakar),',
            '   3 % fall, gutter + downpipe.',
            'Veranda and pavilion deck +0.55 (0.05 below the floor),',
            '   threshold channel at SD01, SD02 and D03.',
            'Scullery: low vent grille in D10, high grille, floor',
            '   drain. WC: extract fan ducted outside.',
            'Bedrooms 1 and 3: high window 2.00 x 0.60 over the',
            '   bed head (daylight + cross ventilation).']
NOTES_FF = ['Dimensions between grid axes (see ground floor).',
            'Master bath: closed WC (sliding door, hopper window),',
            '   walk-in shower 2.00 x 1.20, built-in 2-person',
            '   jacuzzi + bathtub (one unit) on a tiled deck',
            '   under the high window, double vanity 1.80.',
            'Dressing: upholstered bench, sliding-door storage.',
            'D12 against the terrace wall; D13 1.00 swing door,',
            '   steel frame + armoured glass, opens to the terrace.',
            'Terrace pergola: no posts on the bedroom side, beams',
            '   on base plates in the wall, 1 intermediate post per',
            '   beam; rainwater outlet (RWO), BBQ moved.',
            'WC D15: swing door opening to the landing.',
            'Stair to the roof: 13 + 7 risers (12 + 6 treads),',
            '   landings +6.21 (1.37 x 1.10) and +7.40 (1.13 deep,',
            '   in the stair penthouse); guardrails on all open',
            '   sides of flights and landings.',
            'Stair window W12: 1.60 x 1.40 fixed glazing.',
            'Terrace: plant pots 0.60 min. from the guardrail;',
            '   outdoor floors +3.95, threshold channel at doors.',
            'Terrace pergola: polycarbonate roof above the slats.',
            'Point loads (engineer): 4 terrace pergola posts on the',
            '   slab over the living room / hall.'] + [
            'Transfer beam (engineer): %s, span %.2f.' % (l, p_) for l, p_ in sorted({(q['ligne'], q['portee'])
            for q in MAQ['niveaux']['FF'].get('poutres_transfert', [])})] + [
            'Windows with sill 0.80: laminated lower pane to 1.00.',
            'WCs: extract fans; balconies: rainwater outlets.',
            'Sliding doors: SD03 3.00, SD04 and SD05 2.00.',
            'RC canopies 0.60 over all first-floor windows.']

if __name__ == '__main__':
    print(planche('GF', '00 - Ground Floor', 'Ground floor + site', 'SD - 004', '1', NOTES_GF))
    print(planche('FF', '01 - First Floor', 'First floor', 'SD - 005', '1', NOTES_FF))
