"""YAMA HOUSE - construction de la maquette de données (étape 1) depuis l'extraction du PDF d'origine.

python3 -I projet/maquette/construire_maquette.py
  entrées : projet/maquette/extraction/{GF,FF}_brut.json (outils/pdf_plan.py), PDF d'origine (façades)
  sorties : projet/maquette/maquette.json (référence unique) ; projet/maquette/{GF,FF}_niveau.json (format contrôle)
            projet/maquette/CORRECTIONS.md (journal de chaque modification par rapport au PDF d'origine)
Unité : le mètre. Repère : origine = angle sud-ouest du bâtiment (nu extérieur), x = est, y = nord, z = NGL ±0.00.
Toute correction est écrite ici, motivée, avec sa référence (B1..., I1..., décision client ou autonome).
"""
import json, os, sys, copy, math
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join('/home/user/atelier-archi-ingenierie', 'outils')
sys.path.insert(0, OUT)
import pdf_facade as pf
from shapely.geometry import box

PDF = os.path.join(ROOT, 'projet', 'source', 'YAMA_HOUSE_Architectural_Design_realistic_v2.pdf')
W, H = 13.10, 14.30
NIV = {'GF': {'z': 0.60, 'hsp_brut': 3.20}, 'FF': {'z': 4.00, 'hsp_brut': 3.20}}
JOURNAL = []


def note(ref, quoi, pourquoi, type_='correction'):
    JOURNAL.append((ref, type_, quoi, pourquoi))


def charger(n):
    return json.load(open(os.path.join(HERE, 'extraction', n + '_brut.json')))


# ---------------------------------------------------------------- nommage des formes (chevets, chaises, sanitaires)
def nommer(M):
    """Donne un nom et une catégorie aux formes non nommées utiles (règles simples, vérifiables)."""
    meubles = [dict(f, cat=None) for f in M['mobilier']]
    out = []
    vus = set()
    for r in M['formes']:
        k = tuple(round(v, 2) for v in r)
        if k in vus: continue
        vus.add(k); g = box(*r); w, h = r[2] - r[0], r[3] - r[1]
        if g.area > 4 or g.area < 0.02: continue
        if any(g.within(box(*m['rect']).buffer(0.01)) for m in meubles): continue
        if any(g.buffer(0.01).contains(box(*m['rect'])) for m in meubles): continue
        out.append(list(r))
    # emboîtements : garder l'enveloppe
    out = [r for r in out if not any(s is not r and box(*r).within(box(*s).buffer(0.01)) and box(*s).area > box(*r).area for s in out)]
    fus = True     # petits objets qui se chevauchent (vasque + plan) : une seule enveloppe
    while fus:
        fus = False
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                a, b = box(*out[i]), box(*out[j])
                if a.area < 0.3 and b.area < 0.3 and a.intersection(b).area > 0.2 * min(a.area, b.area):
                    out[i] = list(a.union(b).envelope.bounds); del out[j]; fus = True; break
            if fus: break
    obj = []
    # étiquette posée sur une chaise alors qu'elle désigne la table qui la contient (« GAMES TABLE »)
    for m in meubles:
        if 'TABLE' in m['nom'] and (m['rect'][2] - m['rect'][0]) < 0.5:
            grand = [r for r in out if box(*r).area > 0.8 and box(*r).intersects(box(*m['rect']).buffer(0.05))]
            if grand:
                vrai = grand[0]; out.remove(vrai); out.append(list(m['rect'])); m['rect'] = list(vrai)
                for f in M['mobilier']:
                    if f['nom'] == m['nom']: f['rect'] = list(vrai)
    for r in out:
        w, h = r[2] - r[0], r[3] - r[1]; g = box(*r)
        nom = 'OBJECT'
        lits = [m for m in meubles if 'BED' in m['nom']]
        tables = [m for m in meubles if 'DINING' in m['nom'] or 'TABLE' in m['nom']]
        if abs(w - 0.45) < 0.03 and abs(h - 0.45) < 0.03 and any(g.distance(box(*l['rect'])) < 0.08 for l in lits):
            nom = 'NIGHTSTAND'
        elif abs(w - 0.40) < 0.03 and abs(h - 0.40) < 0.03 and any(g.distance(box(*t['rect'])) < 0.30 for t in tables):
            nom = 'CHAIR'
        elif max(w, h) > 1.3 and min(w, h) <= 0.45 and any(g.distance(box(*l['rect'])) < 0.15 for l in lits):
            nom = 'FOOT BENCH'
        if nom == 'OBJECT':
            from shapely.geometry import Polygon as _P, Point as _Pt
            piece = next((pc['nom'] or '' for pc in M['pieces'] if _P(pc['contour']).contains(_Pt(g.centroid.coords[0]))), '')
            humide = any(k in piece for k in ('WC', 'BATH', 'EN-SUITE', 'SHOWER'))
            if humide:
                cit = lambda q: 0.18 <= min(q[2] - q[0], q[3] - q[1]) <= 0.22 and 0.40 <= max(q[2] - q[0], q[3] - q[1]) <= 0.46
                if 0.35 <= min(w, h) <= 0.41 and 0.45 <= max(w, h) <= 0.55 and any(cit(q) and box(*q).distance(g) < 0.02 for q in out): nom = 'WC'
                elif 0.18 <= min(w, h) <= 0.22 and 0.40 <= max(w, h) <= 0.46: nom = 'WC CISTERN'
                elif 0.30 <= min(w, h) <= 0.42 and 0.35 <= max(w, h) <= 0.52: nom = 'BASIN'
                elif min(w, h) >= 0.85 and max(w, h) >= 0.85: nom = 'SHOWER'
                elif 0.45 <= min(w, h) <= 0.55 and 0.9 <= max(w, h) <= 1.5: nom = 'VANITY'
        obj.append({'nom': nom, 'rect': [round(v, 3) for v in r]})
    return obj


def remplacer(M, nom, rect=None, nouveau_nom=None, suppr=False, idx=0):
    L = [m for m in M['mobilier'] if m['nom'] == nom]
    m = L[idx]
    if suppr:
        M['mobilier'].remove(m); return
    if rect: m['rect'] = [round(v, 3) for v in rect]
    if nouveau_nom: m['nom'] = nouveau_nom


def objets_dans(M, zone, nom=None):
    z = box(*zone)
    return [m for m in M['mobilier'] if box(*m['rect']).within(z.buffer(0.01)) and (nom is None or m['nom'] == nom)]


def deplacer(m, dx, dy):
    r = m['rect']; m['rect'] = [round(r[0] + dx, 3), round(r[1] + dy, 3), round(r[2] + dx, 3), round(r[3] + dy, 3)]


def porte_coulissante(M, oid, ref, pourquoi, cote=None):
    o = next(o for o in M['ouvertures'] if o['id'] == oid)
    o['type'] = 'porte_coulissante'; o.pop('porte', None)
    if cote: o['coulisse'] = cote
    note(ref, '%s : porte battante -> porte coulissante (%s)' % (oid, cote or 'rail en applique'), pourquoi)


# ---------------------------------------------------------------- corrections du RDC
def corriger_GF(M):
    # B1 + B2 : cuisine. Îlot réduit 1.60 x 0.80 à 1.05 du plan de travail (nord) et du cellier (ouest),
    # prolongé au sud par la table de 6 (1.80 x 0.90) en T : 3 chaises de chaque côté.
    remplacer(M, 'ISLAND + INDUCTION HOB', rect=[9.93, 11.73, 11.53, 12.53])
    note('B1', 'îlot 1.80 x 0.90 -> 1.60 x 0.80, posé à 1.05 du plan de travail et 1.05 du cellier / colonne',
         'dégagements mesurés 0.53 / 0.15 (mini 1.00)')
    remplacer(M, 'DINING 6', rect=[10.38, 9.93, 11.28, 11.73])
    for c in objets_dans(M, [11.0, 9.9, 13.0, 12.3], 'CHAIR'):
        M['mobilier'].remove(c)
    for i in range(3):
        y = 10.13 + i * 0.55
        M['mobilier'].append({'nom': 'CHAIR', 'rect': [9.93, y, 10.33, y + 0.40]})
        M['mobilier'].append({'nom': 'CHAIR', 'rect': [11.33, y, 11.73, y + 0.40]})
    # tabourets de l'ancien îlot (côté sud) : supprimés (la table en prolongement sert de coin repas)
    for c in objets_dans(M, [9.0, 11.6, 10.8, 12.1]):
        if c['nom'] in ('CHAIR', 'OBJECT'): M['mobilier'].remove(c)
    note('B2', 'table de 6 (1.80 x 0.90) placée en T dans le prolongement sud de l\'îlot, 3 chaises par côté ; '
         'tabourets supprimés', 'la table était à 0.50 du mur est (mini 0.75) et les tabourets à 0.40 des chaises ; '
         'îlot + table côte à côte impossible dans 4.43 x 4.75 (5.10 nécessaires)', 'décision autonome (B1/B2 validés)')
    M.setdefault('equipements', []).append({'nom': 'ISLAND HOOD (ceiling)', 'rect': [10.33, 11.83, 11.13, 12.43], 'z': 'plafond'})
    note('I3', 'hotte d\'îlot suspendue au plafond au-dessus de la plaque', 'plaque à induction sans hotte')

    # B3 : chambre 2. Armoire sur le mur est (1.50, hors débattement de la porte), lit queen recentré,
    # bureau contre le mur sud côté fenêtre, hors de l'axe du lit.
    remplacer(M, 'WARDROBE', rect=[3.65, 6.75, 4.25, 8.25], idx=1)
    lit = [m for m in M['mobilier'] if m['nom'] == 'QUEEN BED'][1]
    lit['rect'] = [1.10, 6.71, 2.70, 8.71]
    chev = sorted(objets_dans(M, [0.15, 8.2, 4.25, 8.71], 'NIGHTSTAND'), key=lambda m: m['rect'][0])
    chev[0]['rect'] = [0.60, 8.26, 1.05, 8.71]; chev[1]['rect'] = [2.75, 8.26, 3.20, 8.71]
    remplacer(M, 'DESK', rect=[0.15, 5.71, 1.05, 6.21], idx=1)
    note('B3', 'chambre 2 : armoire déplacée sur le mur est (3.65-4.25 x 6.75-8.25), lit queen 1.10-2.70, '
         'bureau 0.90 x 0.50 contre le mur sud à côté de la fenêtre',
         'pied du lit à 0.40 de l\'armoire et bureau devant l\'armoire (0.29) : armoire inutilisable')

    # B4 : chambre 1. Armoire décalée à l'est (jusqu'à la porte de la salle d'eau) ; lit et chevets descendus de 0.30.
    remplacer(M, 'WARDROBE', rect=[0.68, 3.37, 3.33, 3.97], idx=0)
    lit = [m for m in M['mobilier'] if m['nom'] == 'QUEEN BED'][0]
    deplacer(lit, 0, -0.30)
    for c in objets_dans(M, [0.15, 0.6, 0.7, 3.4], 'NIGHTSTAND'):
        deplacer(c, 0, -0.30)
    note('B4', 'chambre 1 : armoire décalée de 0.25 vers l\'est (0.68-3.33), lit et chevets descendus de 0.30',
         'chevet posé devant l\'armoire (0.02) et côté du lit à 0.52 de l\'armoire')


# ---------------------------------------------------------------- corrections de l'étage
def corriger_FF(M):
    # B5 : dressing - suppression de l'îlot ; pouf Ø0.45 devant le miroir, hors des façades de rangement.
    remplacer(M, 'ISLAND', suppr=True)
    M['mobilier'].append({'nom': 'POUF', 'rect': [3.28, 7.03, 3.73, 7.48]})
    note('B5', 'dressing : îlot supprimé, pouf Ø0.45 devant le miroir', 'îlot à 0.35 / 0.40 des rangements (mini 0.90) ; '
         'un îlot de 0.50 laisserait 0.53 de chaque côté : insuffisant aussi', 'décision autonome dans la proposition validée')
    porte_coulissante(M, 'FF-D03', 'B6', 'l\'arc de la porte (1.30) heurtait le poteau de la pergola', 'vitrée, 2 vantaux')
    porte_coulissante(M, 'FF-D07', 'B7', 'l\'arc de la porte du linge touchait une chaise de la table de jeux')
    porte_coulissante(M, 'FF-D05', 'B8', 'WC de 1.9 m² : marge de 0.21 seulement (amélioration validée)')
    # table de jeux décalée de 0.20 vers le sud (bureau : 0.58 -> > 0.70 devant)
    for m in objets_dans(M, [6.1, 11.4, 7.95, 13.45]):
        deplacer(m, 0, -0.20)
    note('N2', 'salon : table de jeux et ses 4 chaises décalées de 0.20 vers le sud', '0.58 seulement devant le bureau (mini 0.70)')
    # I7 : barbecue à l'angle est de la terrasse ; salon d'extérieur remonté
    remplacer(M, 'BBQ', rect=[11.98, 0.45, 12.58, 1.65])
    remplacer(M, 'LOUNGE', rect=[11.38, 1.85, 12.18, 4.65])
    note('I7', 'barbecue déplacé à l\'angle sud-est de la terrasse ; banquette remontée au nord', 'fumées contre la chambre parentale')
    # I8 : table de 8
    remplacer(M, 'OUTDOOR DINING 8', rect=[8.33, 2.35, 10.73, 3.35])
    for c in objets_dans(M, [8.3, 1.8, 10.8, 3.9], 'CHAIR'):
        M['mobilier'].remove(c)
    for i in range(4):
        x = 8.43 + i * 0.58
        M['mobilier'].append({'nom': 'CHAIR', 'rect': [x, 1.90, x + 0.40, 2.30]})
        M['mobilier'].append({'nom': 'CHAIR', 'rect': [x, 3.40, x + 0.40, 3.80]})
    note('I8', 'terrasse : table 2.40 x 1.00 et 8 chaises (4 par côté)', '« Outdoor dining 8 » avec 6 chaises dessinées')


# ---------------------------------------------------------------- hauteurs des ouvertures (façades)
def trouver(M, nom, pres):
    L = [m for m in M['mobilier'] if m['nom'] == nom]
    return min(L, key=lambda m: abs(m['rect'][0] - pres[0]) + abs(m['rect'][1] - pres[1]))


def corriger_relecture(niveaux):
    G, F = niveaux['GF'], niveaux['FF']
    # R4 hotte de l'arrière-cuisine (au-dessus du banc gaz)
    G.setdefault('equipements', []).append({'nom': 'EXTRACTOR HOOD', 'rect': [5.78, 13.63, 7.78, 14.18], 'z': 'mur'})
    note('R4', 'hotte d\'extraction au-dessus du banc gaz (arrière-cuisine)', 'relecture : hotte de l\'original et du programme absente')
    # R6 dressing : rangement bas sous la fenêtre haute W13 (allège 1.60)
    m = trouver(F, 'HANGING', (0.15, 5.9)); m['nom'] = 'LOW DRAWERS (h 0.90, under window)'
    note('R6', 'dressing : la penderie du mur ouest devient un rangement bas (h 0.90) sous la fenêtre haute (allège 1.60)',
         'relecture : penderie devant la fenêtre W13 (même erreur que la 3D v1)')
    # R7 WC : cuvette centrée (axe à 0.55 des murs), lave-mains d'angle près de la porte ; D07 ouvre vers le hall
    for M_, wc, cit, bas, nb in ((G, (5.84, 10.8), (5.81, 11.3), (6.35, 10.6), [6.40, 9.95, 6.75, 10.33]),
                                 (F, (4.69, 10.75), (4.66, 11.25), (5.135, 10.6), [5.15, 9.85, 5.50, 10.23])):
        a = trouver(M_, 'WC', wc); c = trouver(M_, 'WC CISTERN', cit)
        piece_x0 = 5.65 if M_ is G else 4.40; piece_x1 = 6.75 if M_ is G else 5.50
        dx = (piece_x0 + piece_x1) / 2 - (a['rect'][0] + a['rect'][2]) / 2
        deplacer(a, dx, 0); deplacer(c, dx, 0)
        b = trouver(M_, 'BASIN', bas); b['rect'] = nb; b['nom'] = 'HAND BASIN (corner)'
    o = next(o for o in G['ouvertures'] if o['id'] == 'GF-D07')
    o['porte'] = {'charniere': [5.75, 9.6], 'vantail_ouvert': [5.75, 8.85], 'ouverture_vers': [0.0, -0.75]}
    o['etiquette_cote_ouverture'] = True
    note('R7', 'WC RDC et étage : cuvette centrée (axe à 0.55 des murs), lave-mains d\'angle près de la porte ; '
         'porte du WC invités D07 ouvrant vers le hall', 'relecture : lave-mains à 0.25-0.32 de l\'axe (mini 0.40), porte à 0.20 de la cuvette')
    # R8 meuble à chaussures retiré du pied de l'escalier -> rangement sous l'escalier
    G['mobilier'].remove(trouver(G, 'COAT / SHOE CABINET', (12.53, 6.1)))
    note('R8', 'meuble à chaussures supprimé du pied de l\'escalier ; manteaux et chaussures dans le rangement sous l\'escalier',
         'relecture : meuble devant la première marche et dans l\'arc de la porte d\'entrée')
    # R9 table de jeux encore +0.10 vers l'est ; sens de glissement de la lingerie
    for m in objets_dans(F, [6.1, 11.2, 7.95, 13.25]):
        deplacer(m, 0.10, 0)
    next(o for o in F['ouvertures'] if o['id'] == 'FF-D07')['coulisse_vers'] = '-'
    note('R9', 'salon : table de jeux décalée de 0.10 vers l\'est (0.77 devant la lingerie) ; vantail de la lingerie glissant vers le sud',
         'relecture : 0.67 devant la lingerie ; sens de glissement non indiqué')
    # R10 armoires à portes coulissantes
    for M_ in (G, F):
        for m in M_['mobilier']:
            if m['nom'] == 'WARDROBE': m['nom'] = 'WARDROBE (sliding doors)'
    note('R10', 'armoires des chambres : portes coulissantes (0.70 libres suffisent)', 'relecture : 0.82 devant l\'armoire de la chambre 1')
    # R20 fauteuils du séjour éloignés de la baie ; R21 porte D05 ouvrant côté hall, plante déplacée
    for m in objets_dans(G, [10.4, 0.5, 12.5, 2.1]):
        deplacer(m, 0, 0.30)
    o = next(o for o in G['ouvertures'] if o['id'] == 'GF-D05')
    o['porte'] = {'charniere': [5.65, 6.95], 'vantail_ouvert': [6.55, 6.95], 'ouverture_vers': [0.9, 0.0]}
    pl = trouver(G, 'OBJECT', (5.93, 6.0)); pl['rect'] = [7.00, 6.00, 7.60, 6.60]; pl['nom'] = 'PLANT POT'
    note('R20', 'séjour : fauteuils et guéridon reculés de 0.30 de la baie SD01', 'relecture : 0.45 devant la baie (grilles repliables, passage)')
    note('R21', 'porte D05 hall -> couloir ouvrant côté hall ; pot de plante déplacé', 'relecture : la porte ouverte bloquait le couloir de 1.10')
    # R5 / R22 terrasse : barbecue hors des poteaux, banquette remontée, table de 8 décalée vers l'ouest
    trouver(F, 'BBQ', (11.98, 0.45))['rect'] = [9.00, 5.00, 10.20, 5.60]
    trouver(F, 'LOUNGE', (11.38, 1.85))['rect'] = [11.38, 2.05, 12.18, 4.72]
    t = trouver(F, 'OUTDOOR DINING 8', (8.33, 2.35)); deplacer(t, -0.40, 0)
    for c in [m for m in F['mobilier'] if m['nom'] == 'CHAIR' and 1.8 < m['rect'][1] < 3.9 and m['rect'][0] > 8.0]:
        deplacer(c, -0.40, 0)
    note('R5', 'terrasse : barbecue contre le mur nord, hors de la pergola à lames bois (0.97 à 1.20 libres autour) ; banquette remontée ; '
         'table de 8 décalée de 0.40 vers l\'ouest (1.05 entre table et banquette)', 'relecture : barbecue sur le poteau sud-est, 0.19 de la banquette, 0.78 table-banquette')


# ---------------------------------------------------------------- indice C : retour de l'ingénieur (15/10/2026)
# Standards SABTP : atelier METHODOLOGIE/STANDARDS_SABTP.md. Détail des remarques : projet/retours/2026-10-15_revB/.
LINTEAU = 2.20                    # sous linteau, au-dessus du sol fini : portes, portes-fenêtres, haut des fenêtres
FENETRES = {                      # type -> (hauteur, allège)
    'A': (1.40, 0.80),            # fenêtre courante du projet (1.60 ou 2.00 de large)
    'P': (1.25, 0.95),            # au-dessus d'un plan de travail (1.40 ou 2.00)
    'H': (0.60, 1.60),            # salle d'eau / WC / rangement (1.00 ou 2.00 ; 0.60 x 0.60 à soufflet)
}


def _rect_ouv(o, a, b):
    r = list(o['rect'])
    if o['axe'] == 'x': r[0], r[2] = a, b
    else: r[1], r[3] = a, b
    return [round(v, 3) for v in r]


def boucher(M, rect, axe, ep=None):
    M['murs'].append({'id': '%s-W%03d' % (M['niveau'] if 'niveau' in M else 'X', len(M['murs']) + 1), 'rect': [round(v, 3) for v in rect],
                      'axe': axe, 'epaisseur': round(ep or ((rect[3] - rect[1]) if axe == 'x' else (rect[2] - rect[0])), 3)})


def percer(M, rect):
    """Retire des murs le rectangle d'une ouverture (découpe le long de l'axe du mur)."""
    r = box(*rect); nouveaux = []
    for w in M['murs']:
        g = box(*w['rect'])
        if g.intersection(r).area < 1e-4: nouveaux.append(w); continue
        reste = g.difference(r)
        for p in (reste.geoms if hasattr(reste, 'geoms') else [reste]):
            if p.is_empty: continue
            b = p.bounds
            if (b[2] - b[0]) < 0.015 or (b[3] - b[1]) < 0.015: continue
            nouveaux.append(dict(w, rect=[round(v, 3) for v in b]))
    M['murs'] = nouveaux


def deplacer_ouverture(M, oid, a, b, **champs):
    """Bouche l'ancienne ouverture (mur) et perce la nouvelle position [a, b] le long du même mur."""
    o = next(o for o in M['ouvertures'] if o['id'] == oid)
    boucher(M, o['rect'], 'x' if o['axe'] == 'x' else 'y')
    o['rect'] = _rect_ouv(o, a, b); o['largeur'] = round(b - a, 2)
    percer(M, o['rect'])
    o.update(champs)
    return o


def supprimer_ouverture(M, oid):
    o = next(o for o in M['ouvertures'] if o['id'] == oid)
    boucher(M, o['rect'], o['axe']); M['ouvertures'].remove(o)


def hauteur_std(o, z, type_=None):
    """Hauteurs standard SABTP (linteau commun 2.20)."""
    if o['type'] == 'passage':          # passage ouvert : jusqu'en sous-face de dalle (pas de retombée)
        o['z_bas'], o['z_haut'] = z, round(z + 3.20, 2)
    elif o['type'] in ('porte', 'porte_coulissante', 'baie_coulissante'):
        o['z_bas'], o['z_haut'] = z, round(z + LINTEAU, 2)
    else:
        h, al = FENETRES[type_ or o.get('type_fenetre', 'A')]
        o['type_fenetre'] = type_ or o.get('type_fenetre', 'A')
        o['z_bas'], o['z_haut'] = round(z + al, 2), round(z + al + h, 2)
    o['source_hauteur'] = 'standard SABTP (linteau 2.20), indice C'


def corriger_C(niveaux):
    G, F = niveaux['GF'], niveaux['FF']
    G['niveau'], F['niveau'] = 'GF', 'FF'
    zG, zF = NIV['GF']['z'], NIV['FF']['z']
    # siphons de douche relus comme « poteaux » : retirés (ils sont dans le symbole de la douche)
    G['poteaux'] = [p for p in G['poteaux'] if (p[2] - p[0]) > 0.15]
    F['poteaux'] = [p for p in F['poteaux'] if (p[2] - p[0]) > 0.15 and p[1] >= 0]      # poteaux du pavillon : RDC seulement
    G['poteaux'] = [[7.63, -0.2, 7.83, 0.0], [12.43, -0.2, 12.63, 0.0], [7.63, -3.75, 7.83, -3.55], [12.43, -3.75, 12.63, -3.55]]

    # objets sans nom relus sur le PDF : nommés ou retirés (aucun objet fantôme sur les plans)
    for M_, pos, nom in ((G, (7.23, 1.35), 'L-SOFA (chaise part)'), (G, (11.26, 1.88), 'SIDE TABLE'), (G, (12.33, 3.85), 'PLANT POT'),
                         (G, (10.03, 8.5), None), (G, (8.55, 7.65), None),
                         (F, (5.01, 1.78), 'SIDE TABLE'), (F, (8.43, 10.95), 'L-SOFA (chaise part)'), (F, (9.73, 11.1), 'COFFEE TABLE'),
                         (F, (12.58, 0.45), None), (F, (9.88, 5.75), None), (F, (6.95, 7.05), None)):
        L = [m for m in M_['mobilier'] if m['nom'] == 'OBJECT' and abs(m['rect'][0] - pos[0]) < 0.02 and abs(m['rect'][1] - pos[1]) < 0.02]
        if not L: continue
        if nom: L[0]['nom'] = nom
        else: M_['mobilier'].remove(L[0])
    note('C26', 'objets sans nom relus sur le PDF : méridiennes des canapés d\'angle, guéridons, coffee table et pot nommés ; repères de '
         'niveau (triangles), trait d\'escalier et jardinière en double retirés', 'règle : tout ce qui est dessiné provient d\'un objet nommé de la maquette')
    # fente de 0.07 entre deux murs relue comme un « passage » de 4.10 (salle d'eau partagée / chambre 3) : rebouchée
    supprimer_ouverture(G, 'GF-O03')
    note('C28', 'faux passage O03 (fente de 0.07 x 4.10 entre deux murs, artefact de lecture du PDF) rebouché en mur',
         'détecté par le contrôle K-REVETEMENT (faïence posée « dans » ce passage)')
    # ---------- C1-C3 cuisine ouverte : réfrigérateur américain, cuisinière + four + hotte, meuble en T, placards hauts
    for nom in ('FRIDGE / OVEN TOWER', 'PANTRY', 'WORKTOP', 'ISLAND + INDUCTION HOB', 'DINING 6', 'COFFEE BAR'):
        remplacer(G, nom, suppr=True)
    for c in objets_dans(G, [9.5, 9.8, 12.0, 11.9], 'CHAIR'):
        G['mobilier'].remove(c)
    G['equipements'] = [q for q in G.get('equipements', []) if q['nom'] not in ('ISLAND HOOD (ceiling)', 'EXTRACTOR HOOD')]
    G['mobilier'] += [
        {'nom': 'FRIDGE (side by side)', 'rect': [8.28, 13.43, 9.21, 14.18]},
        {'nom': 'WORKTOP + BASE UNITS', 'rect': [9.21, 13.58, 12.98, 14.18]},
        {'nom': 'COOKER + OVEN 0.90', 'rect': [12.38, 12.40, 12.98, 13.30]},
        {'nom': 'WORKTOP RETURN', 'rect': [12.38, 13.30, 12.98, 13.58]},
        {'nom': 'WORKTOP RETURN', 'rect': [12.38, 11.85, 12.98, 12.40]},
        {'nom': 'ISLAND (prep + storage)', 'rect': [9.58, 11.58, 11.18, 12.38]},
        {'nom': 'DINING 6 (T with island)', 'rect': [9.93, 9.75, 10.83, 11.58]},
    ]
    for i in range(3):
        y = 9.95 + i * 0.55
        G['mobilier'].append({'nom': 'CHAIR', 'rect': [9.48, y, 9.88, y + 0.40]})
        G['mobilier'].append({'nom': 'CHAIR', 'rect': [10.88, y, 11.28, y + 0.40]})
    G['equipements'] += [
        {'nom': 'SINK (double bowl)', 'rect': [9.98, 13.68, 11.08, 14.10], 'z': 'plan'},
        {'nom': 'COOKER HOOD', 'rect': [12.48, 12.40, 12.98, 13.30], 'z': 'haut'},
        {'nom': 'WALL UNITS', 'rect': [11.53, 13.83, 12.98, 14.18], 'z': 'haut'},
        {'nom': 'TALL UNIT OVER FRIDGE', 'rect': [8.28, 13.58, 9.21, 14.18], 'z': 'haut'},
    ]
    supprimer_ouverture(G, 'GF-W10')
    deplacer_ouverture(G, 'GF-W09', 9.53, 11.53, type_fenetre='P')
    note('C1', 'cuisine : îlot (préparation + rangements, 1.60 x 0.80) et table de 6 (0.90 x 1.83) en un seul meuble en T '
         'adossé au mur de l\'escalier ; circulation sur les trois autres côtés (1.20 devant le plan, 1.40 à l\'ouest, 1.45 à l\'est)',
         'demande client ; plaque de l\'îlot et hotte de plafond supprimées (cuisson sur la cuisinière)', 'décision client')
    note('C2', 'cuisine : plan de travail sur toute la longueur du mur nord (4.75) ; réfrigérateur américain (0.92 x 0.75) '
         'dans l\'angle nord-ouest ; cuisinière avec four (0.90) + hotte sur le retour est (au fond) ; évier double sous la fenêtre',
         'demande client : réfrigérateur side by side indispensable, cuisinière avec four, plan jusqu\'à la fenêtre', 'décision client')
    note('C3', 'cuisine : W09 + W10 remplacées par une seule fenêtre 2.00 x 1.25 (appui 0.95) au-dessus de l\'évier ; placards hauts '
         'de part et d\'autre, colonne au-dessus du réfrigérateur', 'placards hauts demandés, jamais devant une fenêtre (contrôle K-HAUT)', 'décision client')
    # ---------- C4 garde-manger supprimé, D09 contre le mur sud de l'arrière-cuisine, ouverture inversée
    deplacer_ouverture(G, 'GF-D09', 11.70, 12.60,
                       porte={'charniere': [8.08, 11.70], 'vantail_ouvert': [7.18, 11.70], 'ouverture_vers': [-0.9, 0.0]})
    note('C4', 'garde-manger supprimé ; porte D09 déplacée contre le mur sud (y 11.70-12.60), ouvrant vers l\'arrière-cuisine '
         'et adossée au mur sud', 'demande client', 'décision client')
    # ---------- C5 arrière-cuisine (cuisine africaine)
    for nom in ('LOW GAS BENCH', 'WM', 'LAUNDRY SINK', 'POT SHELVES'):
        remplacer(G, nom, suppr=True)
    G['mobilier'] += [
        {'nom': 'WM', 'rect': [5.48, 13.58, 6.08, 14.18]},
        {'nom': 'WORKTOP + LAUNDRY SINK (pot shelves under)', 'rect': [6.08, 13.58, 8.08, 14.18]},
        {'nom': 'WORKTOP (base + wall units)', 'rect': [5.45, 11.65, 7.08, 12.25]},
        {'nom': 'GAS COOKING ZONE (portable cookers)', 'rect': [4.40, 11.65, 5.40, 12.45]},
    ]
    G['equipements'] += [{'nom': 'LAUNDRY SINK', 'rect': [6.48, 13.68, 7.18, 14.10], 'z': 'plan'},
                         {'nom': 'WALL UNITS', 'rect': [5.75, 11.65, 7.08, 12.00], 'z': 'haut'},
                         {'nom': 'VENT GRILLE high 0.20 x 0.20', 'rect': [5.48, 14.18, 5.68, 14.30], 'z': 'haut'}]
    deplacer_ouverture(G, 'GF-W08', 6.08, 7.48, type_fenetre='P')
    deplacer_ouverture(G, 'GF-D10', 4.53, 5.43, materiau='steel door',
                       porte={'charniere': [4.53, 14.18], 'vantail_ouvert': [4.53, 13.28], 'ouverture_vers': [0.0, -0.9]})
    note('C5', 'arrière-cuisine : banc gaz et hotte supprimés ; zone de réchauds à gaz portatifs (bouteille + brûleur) dans l\'angle '
         'sud-ouest face à D10 (ventilation : grille basse dans la porte métallique D10, grille haute 0.20 x 0.20 au mur nord, faïence '
         'pare-feu autour de la zone) ; plan de travail avec bac de lavage et étagères à marmites sous la fenêtre W08 (1.40 x 1.25), '
         'machine à laver sous le plan ; petit plan avec placards hauts au mur sud jusqu\'au débattement de D09 ; cage de gaz '
         'extérieure supprimée', 'demande client (pas de plan à gaz fixe ni de hotte : réchauds portatifs)', 'décision client')
    # ---------- C6 porte d'entrée 1.00 + 0.50, métallique blindée effet bois
    o = next(o for o in G['ouvertures'] if o['id'] == 'GF-D03')
    o['porte'] = {'charniere': [12.98, 4.55], 'vantail_ouvert': [11.98, 4.55], 'ouverture_vers': [-1.0, 0.0]}
    o['vantail2'] = {'charniere': [12.98, 6.05], 'vantail_ouvert': [12.48, 6.05], 'ouverture_vers': [-0.5, 0.0]}
    o['materiau'] = 'armoured steel door, wood-effect finish, leaves 1.00 + 0.50'
    note('C6', 'porte d\'entrée D03 : 2 vantaux 1.00 + 0.50, métallique blindée finition effet bois ; grand vantail adossé '
         'au mur du séjour', 'demande client', 'décision client')
    # ---------- C9-C12 hall
    deplacer_ouverture(G, 'GF-D05', 5.75, 6.65,
                       porte={'charniere': [5.65, 5.75], 'vantail_ouvert': [6.55, 5.75], 'ouverture_vers': [0.9, 0.0]})
    w = next(w for w in G['murs'] if w['rect'] == [5.65, 5.6, 6.13, 5.75]); w['rect'] = [5.65, 5.6, 6.60, 5.75]
    note('C10', 'porte D05 (hall -> couloir) : ouverture inversée, adossée au retour de cloison prolongé à 0.95 dans le hall',
         'demande client', 'décision client')
    remplacer(G, 'CONSOLE', suppr=True)
    note('C11', 'console du hall supprimée', 'demande client', 'décision client')
    o = next(o for o in G['ouvertures'] if o['id'] == 'GF-O02')
    boucher(G, o['rect'], 'x'); o['rect'] = [7.03, 9.6, 8.23, 9.75]; o['largeur'] = 1.20; percer(G, o['rect'])
    o['type'] = 'porte_coulissante'; o['coulisse_vers'] = '+'; o['cote_rail'] = '+'
    note('C12', 'hall -> cuisine : coffee bar supprimé ; porte coulissante 1.20 en applique côté cuisine, qui s\'efface vers l\'est '
         'le long du mur de l\'escalier', 'demande client', 'décision client')
    note('C9', 'meuble à chaussures au pied de l\'escalier : déjà supprimé de la maquette (R8) mais son symbole d\'origine restait '
         'dessiné ; les symboles sont désormais tous générés depuis la maquette', 'erreur de dessin signalée par le client')
    # ---------- C7-C8 menuiseries standard (RDC)
    o = next(o for o in G['ouvertures'] if o['id'] == 'GF-D07')
    boucher(G, o['rect'], 'x'); o['rect'] = [5.75, 9.6, 6.55, 9.75]; o['largeur'] = 0.80; percer(G, o['rect'])
    o['porte'] = {'charniere': [5.75, 9.6], 'vantail_ouvert': [5.75, 8.80], 'ouverture_vers': [0.0, -0.8]}
    o = next(o for o in G['ouvertures'] if o['id'] == 'GF-D08')
    boucher(G, o['rect'], 'y'); o['rect'] = [4.25, 10.65, 4.4, 11.45]; o['largeur'] = 0.80; percer(G, o['rect'])
    o['porte'] = {'charniere': [4.25, 10.65], 'vantail_ouvert': [3.45, 10.65], 'ouverture_vers': [-0.8, 0.0]}
    for oid, a, b, t in (('GF-W01', 2.43, 4.03, 'A'), ('GF-W02', 4.34, 5.34, 'H'), ('GF-W03', 6.41, 8.01, 'A'),
                         ('GF-W05', 9.10, 10.10, 'H'), ('GF-W06', 9.85, 11.85, 'A'), ('GF-W07', 2.45, 4.05, 'A'),
                         ('GF-W04', 7.35, 9.35, 'H')):
        deplacer_ouverture(G, oid, a, b, type_fenetre=t)
    deplacer_ouverture(G, 'GF-SD01', 8.63, 11.63)
    deplacer_ouverture(G, 'GF-SD02', 0.95, 3.95)
    for o in G['ouvertures']:
        hauteur_std(o, zG)
    o = next(o for o in G['ouvertures'] if o['id'] == 'GF-W04')
    o['z_bas'], o['z_haut'] = 2.50, 3.10; o['exception'] = 'fenêtre de la cage d\'escalier : bandeau 2.00 x 0.60 au-dessus de la volée (linteau 2.50 au lieu de 2.20)'
    note('C7', 'RDC : toutes les portes à 2.20 ; fenêtres aux standards SABTP (chambres 1.60 x 1.40, salles d\'eau 1.00 x 0.60, '
         'est de la cuisine 2.00 x 1.40) ; WC D07 et chambre 3 D08 : 0.80 ; D10 : porte métallique 0.90',
         'standards SABTP dictés par le client', 'décision client')
    note('C8', 'baies SD01 (séjour -> pavillon, centrée sur le pavillon) et SD02 (séjour -> véranda) : 3.00 x 2.20, 3 panneaux de 1.00',
         'standards SABTP : portes-fenêtres de 2.00 ou 3.00 seulement', 'décision client')
    note('C7b', 'fenêtre de l\'escalier W04 : bandeau 2.00 x 0.60 au-dessus de la volée, linteau à 2.50 (exception)',
         'une fenêtre 1.40 de haut serait coupée par la volée qui longe le mur est', 'décision autonome (exception)')

    # ---------- étage
    # C14 D12 contre le mur du toit-terrasse, meuble supprimé
    deplacer_ouverture(F, 'FF-D02', 5.33, 6.23,
                       porte={'charniere': [6.23, 5.6], 'vantail_ouvert': [6.23, 4.70], 'ouverture_vers': [0.0, -0.9]})
    remplacer(F, 'VANITY / DESK', suppr=True)
    note('C14', 'porte D12 (palier -> chambre parentale) contre le mur du toit-terrasse, adossée à ce mur ; coiffeuse supprimée',
         'demande client', 'décision client')
    # C17 D13 porte battante 1.00 vitrée blindée ; pergola sans poteaux côté chambre ; poteaux intermédiaires
    o = deplacer_ouverture(F, 'FF-D03', 6.48, 7.48, materiau='steel frame door, armoured glass',
                           porte={'charniere': [6.48, 5.6], 'vantail_ouvert': [6.48, 4.60], 'ouverture_vers': [0.0, -1.0]})
    o['type'] = 'porte'; o.pop('coulisse', None)
    F['poteaux'] = [p for p in F['poteaux'] if abs(p[0] - 7.13) > 0.01] + [[9.23, 0.65, 9.43, 0.85], [9.23, 4.75, 9.43, 4.95]]
    trouver(F, 'BBQ', (9.0, 5.0))['rect'] = [10.60, 5.00, 11.80, 5.60]
    note('C17', 'toit-terrasse : D13 = porte battante 1.00 à huisserie métallique et vitrage blindé, ouvrant vers la terrasse et '
         'adossée au mur de la chambre ; pergola : poteaux côté chambre supprimés, poutres ancrées dans le mur de la chambre par '
         'platines + boulons ; un poteau intermédiaire par poutre (portées entre axes environ 2.90 + 3.00) ; barbecue décalé hors du poteau',
         'demande client (poteaux devant l\'entrée ; portée 5.80 trop grande sans appui intermédiaire)', 'décision client')
    # C13 D15 WC : battante ouvrant vers le palier
    o = next(o for o in F['ouvertures'] if o['id'] == 'FF-D05')
    o['type'] = 'porte'; o.pop('coulisse', None)
    o['porte'] = {'charniere': [4.53, 9.6], 'vantail_ouvert': [4.53, 8.80], 'ouverture_vers': [0.0, -0.8]}
    note('C13', 'WC de l\'étage D15 : porte battante ouvrant vers le palier (comme au RDC)', 'demande client', 'décision client')
    # règle d'adossement : la porte du salon D16 contre le mur ouest
    deplacer_ouverture(F, 'FF-D06', 5.70, 6.60,
                       porte={'charniere': [5.70, 9.75], 'vantail_ouvert': [5.70, 10.65], 'ouverture_vers': [0.0, 0.9]})
    note('C14b', 'porte du salon D16 décalée contre le mur ouest du salon pour que le vantail ouvert s\'adosse au mur',
         'règle du client (portes adossées) appliquée à toutes les portes ; contrôle K-ADOSSEMENT ; D08 (chambre 3) adossée au mur sud', 'décision autonome')
    # C15 dressing : banc rembourré au centre, rangements à portes coulissantes (étagères 0.45)
    remplacer(F, 'POUF', suppr=True)
    trouver(F, 'SHELVES + DRAWERS', (0.75, 5.9)).update(rect=[0.75, 5.9, 3.08, 6.35], nom='SHELVES + DRAWERS (sliding doors)')
    trouver(F, 'HANGING + SHOES', (0.75, 8.05))['nom'] = 'HANGING + SHOES (sliding doors)'
    F['mobilier'].append({'nom': 'UPHOLSTERED BENCH', 'rect': [1.45, 7.05, 2.65, 7.35]})
    note('C15', 'dressing : pouf supprimé ; banc rembourré 1.20 x 0.30 au centre (0.70 libres de chaque côté) ; rangements à portes '
         'coulissantes, étagères ramenées à 0.45 de profondeur ; miroir conservé', 'demande client', 'décision client')
    # C16 salle de bains parentale (refaite)
    for nom in ('JACUZZI 1.90 x 1.90', 'WALK-IN SHOWER', 'DOUBLE VANITY'):
        remplacer(F, nom, suppr=True)
    for m in objets_dans(F, [0.15, 8.8, 4.25, 14.15]):
        if m['nom'] in ('WC', 'WC CISTERN', 'OBJECT'): F['mobilier'].remove(m)
    F['mobilier'] += [
        {'nom': 'WC (wall-hung, concealed cistern)', 'rect': [0.535, 9.71, 0.915, 10.25]},
        {'nom': 'WC CISTERN', 'rect': [0.475, 10.25, 0.975, 10.45]},
        {'nom': 'WALK-IN SHOWER 2.00 x 1.20', 'rect': [0.15, 10.55, 1.35, 12.55]},
        {'nom': 'JACUZZI + BATHTUB 1.90 x 1.10 (one 2-person unit, built-in, tiled deck)', 'rect': [0.15, 12.55, 4.25, 14.15]},
        {'nom': 'DOUBLE VANITY 1.80', 'rect': [3.70, 10.15, 4.25, 11.95]},
    ]
    F['murs'] += [{'id': 'FF-WCP1', 'rect': [1.30, 8.80, 1.40, 10.55], 'axe': 'y', 'epaisseur': 0.10},
                  {'id': 'FF-WCP2', 'rect': [0.15, 10.45, 1.30, 10.55], 'axe': 'x', 'epaisseur': 0.10}]
    F['ouvertures'].append({'id': 'FF-D08', 'rect': [1.30, 8.85, 1.40, 9.65], 'axe': 'y', 'largeur': 0.80, 'epaisseur': 0.10,
                            'type': 'porte_coulissante', 'coulisse_vers': '+', 'cote_rail': '+'})
    percer(F, [1.30, 8.85, 1.40, 9.65])
    F['ouvertures'].append({'id': 'FF-W06', 'rect': [0.0, 9.30, 0.15, 9.90], 'axe': 'y', 'largeur': 0.60, 'epaisseur': 0.15,
                            'type': 'fenetre', 'type_fenetre': 'H', 'facade': 'W', 'ouvrant': 'bottom-hung, opens inwards'})
    percer(F, [0.0, 9.30, 0.15, 9.90])
    F['equipements'] = [{'nom': 'MIRROR (lit)', 'rect': [4.15, 10.15, 4.25, 11.95], 'z': 'mur'},
                        {'nom': 'GLASS SCREEN', 'rect': [1.33, 11.15, 1.37, 12.55], 'z': 'plan'},
                        {'nom': 'GLASS SCREEN', 'rect': [0.15, 12.51, 1.37, 12.55], 'z': 'plan'}]
    note('C16', 'salle de bains parentale refaite : cabinet WC fermé (porte coulissante, fenêtre à soufflet 0.60 x 0.60), douche à '
         'l\'italienne 2.00 x 1.20 à paroi vitrée, baignoire balnéo 2 places encastrée dans une estrade carrelée (jacuzzi + baignoire en '
         'un seul appareil) sous la fenêtre haute, double vasque 1.80 et miroir éclairé ; vue depuis la porte D14 : la baignoire au fond',
         'demande client : salle de bains à repenser, un seul WC, double vasque', 'décision autonome (créativité demandée)')
    # menuiseries standard (étage)
    for oid, a, b, t in (('FF-W01', 1.85, 3.85, 'A'), ('FF-W03', 6.25, 8.25, 'H'), ('FF-W04', 1.20, 3.20, 'H')):
        deplacer_ouverture(F, oid, a, b, type_fenetre=t)
    o = next(o for o in F['ouvertures'] if o['id'] == 'FF-W05')
    deplacer_ouverture(F, 'FF-W05', 6.80, 8.80, type_fenetre='A')
    o2 = copy.deepcopy(o); o2.pop('repere', None); o2['id'] = 'FF-W07'; o2['rect'] = _rect_ouv(o, 9.80, 11.80); percer(F, o2['rect']); F['ouvertures'].append(o2)
    o = deplacer_ouverture(F, 'FF-W02', 6.95, 8.95, type_fenetre='A')
    deplacer_ouverture(F, 'FF-SD01', 1.73, 4.73)
    deplacer_ouverture(F, 'FF-SD03', 11.0, 13.0)
    for o in F['ouvertures']:
        hauteur_std(o, zF)

    note('C7c', 'étage : fenêtres aux standards (chambre 2.00 x 1.40, salon 2 x 2.00 x 1.40, dressing et salle de bains 2.00 x 0.60) ; '
         'cage d\'escalier : une fenêtre standard 2.00 x 1.40 (appui 0.80) sous la volée vers le toit, à la place du vitrage 3.50 x 3.15 '
         '(deux fenêtres superposées impossibles : la fenêtre haute arrivait dans la dalle de toiture)',
         'standards SABTP ; largeur maxi 2.00', 'décision client')
    note('C8b', 'baies de l\'étage : SD03 (chambre -> balcon) 3.00 centrée sur le balcon ; SD04 (chambre -> terrasse) 2.00 ; '
         'SD05 (salon -> balcon jardin) 2.00 centrée sur le balcon', 'standards SABTP', 'décision client')
    # C17/C18 avaloirs (eaux pluviales) de la terrasse
    F.setdefault('exterieurs', {})


FINITIONS = [   # (motif du nom de pièce, sol, murs, faïence) ; clés = matériaux de la 3D ; textes anglais = livrables
    (r'BATH|EN-SUITE|^WC$', 'antiderapant', 'faience', 'full height (floor to ceiling)'),
    (r'SCULLERY', 'antiderapant', 'faience_cuisine', 'full height on all walls (client 15/10, indice D)'),
    (r'KITCHEN', 'antiderapant', 'faience_cuisine', 'full height on all walls (client 15/10, indice D)'),
    (r'BEDROOM|DRESSING', 'sol_bois', 'peinture_greige', None),
    (r'LIVING|LOUNGE', 'sol_carrelage', 'peinture_lin', None),
    (r'TERRACE', 'sol_ext', None, None),
    (r'.', 'sol_carrelage', 'peinture_blanc', None),
]
DESCRIPTIONS = {
    'antiderapant': 'anti-slip porcelain floor tiles 0.60 x 0.60 (R11), warm grey', 'sol_bois': 'wood-effect porcelain planks 0.20 x 1.20',
    'sol_carrelage': 'porcelain floor tiles 0.60 x 0.60, light beige', 'sol_ext': 'anti-slip outdoor porcelain tiles 0.60 x 0.60 (R11)',
    'faience': 'ceramic wall tiles 0.30 x 0.60, light greige', 'faience_cuisine': 'ceramic wall tiles 0.30 x 0.30, warm white', 'peinture_blanc': 'paint, warm white', 'peinture_greige': 'paint, soft greige',
    'peinture_lin': 'paint, linen beige', 'accent': 'accent wall behind the bed head (paint, sage green / clay)'}


def finitions(niveaux):
    """Règle client 15/10 : sols antidérapants dans la cuisine, toutes les salles d'eau et toutes les terrasses ; faïence en
    cuisine (crédence) ; faïence toute hauteur dans les salles d'eau (remarque client 14/10)."""
    import re as _re
    for n, M in niveaux.items():
        for p in M['pieces']:
            if not p.get('nom'): continue
            for motif, sol, murs, faience in FINITIONS:
                if _re.search(motif, p['nom']):
                    p['finitions'] = {'sol': sol, 'murs': murs, 'faience': faience,
                                      'texte': '; '.join(x for x in (DESCRIPTIONS.get(sol), DESCRIPTIONS.get(murs) if not str(murs).startswith('faience') else None,
                                                                     ('wall tiles ' + faience) if faience else None) if x)}
                    if 'BEDROOM' in p['nom']: p['finitions']['accent'] = 'accent_terre' if 'MASTER' in p['nom'] else 'accent_sauge'
                    break
    for s_ in niveaux['FF']['exterieurs']['sols']:
        s_['finition'] = 'sol_ext'
    note('C27', 'finitions par pièce dans la maquette : sols antidérapants (cuisine, arrière-cuisine, salles d\'eau, WC, terrasses, '
         'balcons, véranda, pavillon), faïence toute hauteur des salles d\'eau, crédence de cuisine, faïence de l\'arrière-cuisine '
         '(toute hauteur autour de la zone gaz), peintures par pièce, mur d\'accent derrière la tête de lit',
         'demande client 15/10 (antidérapant, faïence de cuisine) + règles de l\'art', 'décision client')


def corriger_V1(niveaux):
    """Indice C, corrections issues de l'agent vérificateur (15/10) : escaliers définis dans la maquette (une seule
    définition pour plans, coupes et 3D), garde-corps, fenêtres sous / le long des volées, éclairement des chambres,
    ventilation, extraction, avaloirs, réfrigérateur, meuble sous escalier."""
    G, F = niveaux['GF'], niveaux['FF']
    G['escaliers'] = [
        {'nom': 'A', 'type': 'volee', 'sens': 'N', 'larg': [11.88, 12.98], 'depart': 6.88, 'n': 6, 'z0': 0.60},
        {'nom': 'PA', 'type': 'palier', 'rect': [11.88, 8.50, 12.98, 9.60], 'z': 0.60 + 7 * 0.17},
        {'nom': 'B', 'type': 'volee', 'sens': 'W', 'larg': [8.50, 9.60], 'depart': 11.88, 'n': 13, 'z0': 0.60 + 7 * 0.17}]
    F['escaliers'] = [
        {'nom': 'C', 'type': 'volee', 'sens': 'E', 'larg': [5.75, 6.85], 'depart': 8.37, 'n': 13, 'z0': 4.00},
        {'nom': 'PC', 'type': 'palier', 'rect': [11.88, 5.75, 12.98, 6.85], 'z': 4.00 + 13 * 0.17},
        {'nom': 'D', 'type': 'volee', 'sens': 'N', 'larg': [11.88, 12.98], 'depart': 6.85, 'n': 7, 'z0': 4.00 + 13 * 0.17},
        {'nom': 'PD', 'type': 'palier', 'rect': [11.88, 8.74, 12.98, 9.55], 'z': 7.40, 'arrivee': 'roof terrace +7.40 (stair penthouse)'}]
    for M in (G, F):
        for e in M['escaliers']:
            e.setdefault('giron', 0.27); e.setdefault('hauteur', 0.17)
    # garde-corps des côtés ouverts des volées (h 1.00 au-dessus des nez de marche) ; garde-corps du vide côté palier
    G['garde_corps_escalier'] = [{'volee': 'A', 'pts': [[11.88, 6.88], [11.88, 8.50]]}, {'volee': 'B', 'pts': [[8.37, 8.50], [11.88, 8.50]]}]
    F['garde_corps_escalier'] = [{'volee': 'C', 'pts': [[8.37, 6.85], [11.88, 6.85]]}, {'volee': 'D', 'pts': [[11.88, 6.85], [11.88, 8.74]]}]
    F['exterieurs']['garde_corps_vitres'][3] = [[8.37, 6.85], [8.37, 9.60]]
    note('V1-01', 'escaliers décrits dans la maquette (RDC : 6 marches + palier +1.79 + 13 marches ; étage -> toit : 13 marches + palier '
         '+6.21 + 7 marches + palier d\'arrivée +7.40 dans l\'édicule) ; départ RDC à y 6.88 (palier 1.10 x 1.10) ; garde-corps h 1.00 '
         'sur tous les côtés ouverts des volées ; garde-corps du vide côté palier sur toute la trémie',
         'agent vérificateur : marches différentes entre vues, palier d\'arrivée absent, garde-corps absents (ESC-005/007/010)', 'correction')
    # fenêtres le long des volées
    o = deplacer_ouverture(F, 'FF-W02', 7.60, 9.20, type_fenetre='A'); hauteur_std(o, NIV['FF']['z'])
    o = next(o for o in G['ouvertures'] if o['id'] == 'GF-W04'); o['z_bas'], o['z_haut'] = 2.80, 3.40
    o['exception'] = 'fenêtre de la cage d\'escalier : bandeau 2.00 x 0.60, appui 1.00 au-dessus du palier (+1.79), linteau 3.40'
    note('V1-02', 'W12 (escalier de l\'étage) : 1.60 x 1.40 à y 7.60-9.20, sous la volée vers le toit (sous-face >= 6.38) ; W04 : '
         'bandeau relevé à +2.80 / +3.40 (appui à 1.00 au-dessus du palier du RDC)', 'agent vérificateur : volée dans le tableau de W12, '
         'appui de W04 à 0.71 du palier (FEN-014, FEN-015)', 'correction')
    # éclairement et ventilation traversante des chambres 1 et 3 : fenêtre principale 2.00 + fenêtre haute au-dessus de la tête de lit
    for oid, a, b in (('GF-W01', 2.23, 4.23), ('GF-W07', 2.20, 4.20)):
        o = deplacer_ouverture(G, oid, a, b, type_fenetre='A'); hauteur_std(o, NIV['GF']['z'])
    for oid, r in (('GF-W11', [0.0, 0.80, 0.15, 2.80]), ('GF-W12', [0.0, 11.45, 0.15, 13.45])):
        o = {'id': oid, 'rect': r, 'axe': 'y', 'largeur': 2.0, 'epaisseur': 0.15, 'type': 'fenetre', 'type_fenetre': 'H', 'facade': 'W'}
        percer(G, r); hauteur_std(o, NIV['GF']['z']); G['ouvertures'].append(o)
    note('V1-03', 'chambres 1 et 3 : fenêtre principale 2.00 x 1.40 + fenêtre haute 2.00 x 0.60 (appui 1.60) au-dessus de la tête de lit, '
         'au mur ouest : éclairement >= 1/6 et ventilation traversante', 'agent vérificateur : chambre 1 à 10.9 %, chambre 3 à 15.2 % (FEN-012) ; '
         'suggestion de ventilation traversante en attente', 'décision autonome')
    # arrière-cuisine : grille basse dans D10, siphon de sol ; WC : extraction ; réfrigérateur à 0.10 du mur
    next(o for o in G['ouvertures'] if o['id'] == 'GF-D10')['grille_basse'] = 'low vent grille 0.40 x 0.20 in the steel door'
    G['equipements'] += [{'nom': 'FLOOR DRAIN', 'rect': [5.55, 12.75, 5.70, 12.90], 'z': 'sol'},
                         {'nom': 'EXTRACT FAN (ducted outside)', 'rect': [6.05, 11.20, 6.30, 11.45], 'z': 'haut'}]
    F['equipements'] += [{'nom': 'EXTRACT FAN (ducted outside)', 'rect': [4.85, 11.15, 5.10, 11.40], 'z': 'haut'},
                         {'nom': 'EXTRACT FAN (ducted outside)', 'rect': [0.55, 8.85, 0.80, 9.10], 'z': 'haut'}]
    trouver(G, 'FRIDGE (side by side)', (8.28, 13.43))['rect'] = [8.33, 13.43, 9.26, 14.18]
    trouver(G, 'WORKTOP + BASE UNITS', (9.21, 13.58))['rect'] = [9.26, 13.58, 12.98, 14.18]
    for q in G['equipements']:
        if q['nom'] == 'TALL UNIT OVER FRIDGE': q['rect'] = [8.33, 13.58, 9.26, 14.18]
    G['mobilier'].append({'nom': 'SHOE CABINET (under stair, h 0.90)', 'rect': [8.70, 8.60, 10.40, 9.55]})
    F['exterieurs']['avaloirs'] += [[5.70, -1.65, 5.85, -1.50], [14.35, 13.40, 14.50, 13.55]]
    note('V1-04', 'arrière-cuisine : grille basse dans la porte métallique D10 + grille haute + siphon de sol ; WC du RDC, de l\'étage et '
         'cabinet WC parental : extracteur raccordé à l\'extérieur ; réfrigérateur à 0.10 du mur (charnière) ; meuble à chaussures bas sous '
         'la volée ; avaloir sur chaque balcon', 'agent vérificateur (AFR-002, SDE-012, CUI-001, ESC-012, FAC-001)', 'correction')


def site_V1(S, niveaux):
    """Site et toiture (vérificateur) : marches de la porte de service D10, équipements de toiture dans la maquette."""
    S['marches'] += [{'nom': 'service landing +0.45', 'rect': [4.43, 14.30, 5.43, 15.30], 'montee': 'palier', 'n': 0, 'z': 0.45},
                     {'nom': 'service steps (3 x 0.15)', 'rect': [5.43, 14.30, 6.33, 15.30], 'montee': 'ouest', 'n': 3}]
    S['toiture'] = {
        'edicule': [8.30, 5.70, 13.10, 9.70], 'edicule_haut': 10.25,
        'porte_edicule': {'repere': 'D20', 'rect': [12.00, 9.55, 12.90, 9.70], 'z': [7.40, 9.60], 'materiau': 'steel door'},
        'citernes': [{'centre': [6.33, 12.65], 'rayon': 0.60, 'hauteur': 1.55, 'volume': '2000 L'}, {'centre': [7.73, 12.65], 'rayon': 0.60, 'hauteur': 1.55, 'volume': '2000 L'}],
        'clim': [[0.73, 6.45, 1.63, 7.05], [0.73, 7.45, 1.63, 8.05], [0.73, 8.45, 1.63, 9.05]],
        'pv': {'rect': [1.00, 1.60, 4.10, 4.95], 'panneaux': [3, 2]},
        'avaloir': [12.51, 13.73, 12.75, 13.97]}
    note('V1-05', 'porte de service D10 : palier +0.45 (1.00 x 1.00) et 3 marches de 0.15 / 0.30 dans le recul nord ; équipements de '
         'toiture (citernes, groupes de clim, panneaux, avaloir, porte de l\'édicule D20) décrits dans la maquette',
         'agent vérificateur : marches absentes de la maquette, équipements de toiture différents entre la toiture et la 3D (SIT-011, MOD-011)', 'correction')


def corriger_V2(niveaux, S):
    """Indice C, 2e passage de l'agent vérificateur (15/10) : convention des volées (n girons, n + 1 contremarches, le
    palier ou le plancher est la dernière marche), garde-corps d'arrivée et de palier, palier d'arrivée de l'édicule,
    trémies dans la maquette, poutres de transfert, exutoire de l'édicule, parois de douche, parements, seuils."""
    G, F = niveaux['GF'], niveaux['FF']; h = 0.17
    for M, nom, n in ((G, 'B', 12), (F, 'C', 12), (F, 'D', 6)):
        next(e for e in M['escaliers'] if e['nom'] == nom)['n'] = n
    pc = next(e for e in F['escaliers'] if e['nom'] == 'PC'); pc['rect'] = [11.61, 5.75, 12.98, 6.85]
    pd = next(e for e in F['escaliers'] if e['nom'] == 'PD'); pd['rect'] = [11.88, 8.47, 12.98, 9.60]
    G['garde_corps_escalier'] = [{'volee': 'A', 'pts': [[11.88, 6.88], [11.88, 8.50]]}, {'volee': 'B', 'pts': [[8.64, 8.50], [11.88, 8.50]]}]
    F['garde_corps_escalier'] = [{'volee': 'C', 'pts': [[8.37, 6.85], [11.61, 6.85]]}, {'volee': 'D', 'pts': [[11.88, 6.85], [11.88, 8.47]]}]
    # garde-corps fixes (h 1.00) : bord ouest du vide jusqu'au plancher d'arrivée de la volée B ; palier PC côté vide ;
    # palier d'arrivée PD côté trémie (chute > 3.40)
    F['exterieurs']['garde_corps_vitres'][3] = [[8.37, 6.85], [8.37, 8.50], [8.64, 8.50]]
    F['garde_corps_paliers'] = [{'palier': 'PC', 'pts': [[11.61, 6.85], [11.88, 6.85]], 'z': pc['z']},
                                {'palier': 'PD', 'pts': [[11.88, 8.47], [11.88, 9.60]], 'z': pd['z']}]
    G['tremies'] = []
    F['tremies'] = [{'nom': 'void over hall', 'rect': [8.37, 6.85, 11.88, 8.50]}, {'nom': 'stair B', 'rect': [8.64, 8.50, 12.98, 9.60]}]
    note('V2-01', 'volées : n girons et n + 1 contremarches (la dernière contremarche monte sur le palier ou le plancher) : RDC 6 + palier '
         '+1.79 + 12 girons ; étage 12 + palier +6.21 (1.37 x 1.10) + 6 girons + palier d\'arrivée +7.40 de 1.13 ; garde-corps '
         'd\'arrivée de la volée B arrêté au plancher (arrivée libre) ; garde-corps du palier PD côté trémie ; trémies dans la maquette',
         'agent vérificateur 2 : garde-corps en travers de l\'arrivée, palier PD ouvert et trop court, girons dessinés en trop '
         '(ESC-009, ESC-007, ESC-014, ESC-010)', 'correction')
    T = S['toiture']
    T['edicule'] = [8.30, 5.60, 13.10, 9.75]          # murs sud et nord au droit des murs de l'étage (y 5.60-5.75 / 9.60-9.75)
    T['porte_edicule']['rect'] = [12.00, 9.60, 12.90, 9.75]; T['porte_edicule']['releve'] = 0.15
    T['tremie'] = [8.45, 5.75, 12.95, 9.60]           # pas de dalle à +7.40 dans l'édicule (hors palier PD)
    T['gargouille'] = {'pos': [8.30, 9.20], 'sens': 'W', 'pente': 0.02, 'note': 'penthouse roof falls 2 % to a spout on the west side, onto the roof terrace'}
    for c in T['citernes']: c['rayon'] = 0.65        # 2000 L : diamètre 1.30 x 1.55 = 2.06 m3
    note('V2-02', 'édicule : murs sud et nord à y 5.60-5.75 et 9.60-9.75 (au droit des murs de l\'étage ; le mur sud débordait de 0.10 au-dessus de la volée C), porte D20 avec relevé de 0.15 ; toit de l\'édicule '
         'en pente 2 % vers une gargouille ouest (rejet sur la toiture-terrasse) ; citernes diamètre 1.30 (2000 L)',
         'agent vérificateur 2 (ESC-014, FAC-001, regard d\'architecte)', 'correction')
    from controle_degagements import murs_non_portes
    lignes = {'FF-W004': ('x 6.36, y 0.00 - 5.60', 5.60, 'master bedroom east wall (SD04 in it), roof edge, parapet, pergola base plates'),
              'FF-W005': ('x 6.36, y 0.00 - 5.60', 5.60, 'master bedroom east wall (SD04 in it), roof edge, parapet, pergola base plates'),
              'FF-W010': ('y 5.675, x 8.03 - 13.10', 5.07, 'terrace north wall = stair penthouse south wall (up to +10.25)'),
              'FF-W026': ('x 5.575, y 12.85 - 14.15', 1.30, 'WC partition: beam or lightweight partition')}
    F['poutres_transfert'] = []
    for m in murs_non_portes(G, F):
        l, port, t = lignes.get(m['mur'], ('%s' % m['rect'], m['portee'], 'wall not supported below'))
        F['poutres_transfert'].append({'mur': m['mur'], 'ligne': l, 'portee': port, 'objet': t, 'porte_par_rdc': m['porte']})
    from dessin_plan import niveau_toiture
    for m in murs_non_portes(F, niveau_toiture({'site': S})):        # murs de l'édicule sur l'étage
        F['poutres_transfert'].append({'mur': m['mur'], 'ligne': 'x 8.375, y 5.60 - 9.75' if m['mur'] == 'RF-W1' else str(m['rect']),
                                       'portee': m['portee'], 'objet': 'stair penthouse west wall (over the void / stair)', 'porte_par_rdc': m['porte']})
    note('V2-03', 'poutres de transfert notées pour l\'ingénieur (murs de l\'étage portés à moins de 50 %% par le RDC) : %s'
         % ' ; '.join(sorted({'%s (portée %.2f)' % (p['ligne'], p['portee']) for p in F['poutres_transfert']})),
         'agent vérificateur 2 (STR-001, STR-009) ; contrôle K-PORTEUR', 'à valider par l\'ingénieur')
    # douches du RDC : paroi vitrée fixe définie dans la maquette (accès libre de 0.70 / 0.65)
    for q in G['mobilier']:
        if q['nom'] == 'SHOWER': q['nom'] = 'WALK-IN SHOWER'
    G['mobilier'] += [{'nom': 'GLASS SCREEN (shower, fixed)', 'rect': [1.15, 4.79, 1.17, 5.59]},
                      {'nom': 'GLASS SCREEN (shower, fixed)', 'rect': [1.05, 8.83, 1.07, 9.73]}]
    note('V2-04', 'salle d\'eau de la chambre 1 et salle de bains commune : douches à l\'italienne avec paroi vitrée fixe côté WC '
         '(0.80 et 0.90), accès libre 0.70 et 0.65', 'agent vérificateur 2 (SDE-005, SDE-006)', 'correction')
    # jardinières de la terrasse retirées du bord (elles servaient de marchepied derrière le garde-corps de 1.00)
    F['exterieurs']['jardinieres'] = []
    F['mobilier'] = [m for m in F['mobilier'] if not (m['nom'] == 'PLANTER' and m['rect'][0] > 6.4 and m['rect'][3] < 0.5)]
    F['mobilier'] += [{'nom': 'PLANT POT', 'rect': [6.50, 0.70, 7.00, 1.20]}, {'nom': 'PLANT POT', 'rect': [11.50, 1.05, 12.00, 1.55]}]
    F['exterieurs']['niveau_fini'] = 3.95
    note('V2-05', 'terrasse : jardinières le long du garde-corps supprimées (marchepied) et remplacées par 2 grands pots à 0.60 au moins du garde-corps ; sols extérieurs de l\'étage finis à +3.95 avec caniveau de seuil devant D13, SD03, SD04, SD05',
         'agent vérificateur 2 (ESC-008, FAC-017)', 'décision autonome')
    # parements définis dans la maquette (une seule valeur pour façades et 3D)
    S['parements'] = [{'face': 'S', 'de': 0.0, 'a': 6.43, 'z': [0.60, 3.80], 'mat': 'pierre'},
                      {'face': 'E', 'de': 4.40, 'a': 9.60, 'z': [0.60, 3.80], 'mat': 'pierre'},
                      {'face': 'W', 'de': 0.0, 'a': 5.60, 'z': [4.00, 7.40], 'mat': 'bois'}]
    w12 = next(o for o in F['ouvertures'] if o.get('repere') == 'W12'); w12['fixe'] = True
    w12['exception'] = 'fixed glazing (no floor in front: stair void), cleaning from the stair with a pole / from outside'
    for o in F['ouvertures']:
        if o.get('repere') == 'D15': o['etiquette_cote_ouverture'] = True
    # porte de service : marches aussi côté ouest (vers l'étendoir) ; étendoir écarté de la façade
    S['marches'].append({'nom': 'service steps west (3 x 0.15)', 'rect': [3.53, 14.30, 4.43, 15.30], 'montee': 'est', 'n': 3})
    S['etendoir'] = {'rect': [0.50, 14.95, 3.50, 15.55]}
    note('V2-06', 'W12 en châssis fixe (aucun sol devant) ; palier de service desservi des deux côtés ; étendoir à 0.65 de la façade ; '
         'parements (pierre sud 0.00-6.43, pierre est, bois ouest) décrits dans la maquette', 'agent vérificateur 2 (FEN-022, SIT-006, REV-009)', 'correction')


def corriger_V3(niveaux, S):
    """Indice C, 3e passage de l'agent vérificateur (15/10) : mobilier extérieur dans la maquette, niveaux finis extérieurs
    (-0.05), auvent d'entrée (niveau + exutoire), réfrigérateur, entrée de douche, niveaux de la toiture, charges
    ponctuelles des poteaux de pergola, fenêtres de douche, étendoir."""
    G, F = niveaux['GF'], niveaux['FF']
    # mobilier extérieur (avant : recopié du dessin d'origine, absent de la maquette et de la 3D)
    G['mobilier'] += [{'nom': 'OUTDOOR SOFA', 'rect': [8.31, -3.52, 11.95, -2.68], 'exterieur': True},
                      {'nom': 'COFFEE TABLE', 'rect': [9.31, -2.27, 10.95, -1.53], 'exterieur': True},
                      {'nom': 'ARMCHAIR', 'rect': [8.31, -1.87, 9.10, -1.08], 'exterieur': True},
                      {'nom': 'ARMCHAIR', 'rect': [11.16, -1.87, 11.95, -1.08], 'exterieur': True}]
    F['mobilier'] += [{'nom': 'ARMCHAIR', 'rect': [0.70, -1.40, 1.35, -0.75], 'exterieur': True},
                      {'nom': 'ARMCHAIR', 'rect': [2.05, -1.40, 2.70, -0.75], 'exterieur': True},
                      {'nom': 'COFFEE TABLE', 'rect': [1.45, -1.30, 1.95, -0.85], 'exterieur': True},
                      {'nom': 'ARMCHAIR', 'rect': [13.65, 12.70, 14.30, 13.35], 'exterieur': True},
                      {'nom': 'ARMCHAIR', 'rect': [13.65, 10.65, 14.30, 11.30], 'exterieur': True},
                      {'nom': 'COFFEE TABLE', 'rect': [13.70, 11.55, 14.25, 12.10], 'exterieur': True}]
    note('V3-01', 'mobilier extérieur (pavillon, balcons sud et est) décrit dans la maquette : plans, coupes et 3D en dérivent ; '
         'avaloir du balcon sud dégagé', 'agent vérificateur 3 : mobilier recopié du dessin d\'origine (MOD-009)', 'correction')
    # niveaux finis extérieurs : 0.05 sous les sols intérieurs (seuils), caniveau de seuil devant les baies
    for a in S['annotations']:
        a['texte'] = a['texte'].replace('VERANDA 1.20  +0.60', 'VERANDA 1.20  +0.55').replace('deck +0.60', 'deck +0.55')
    S['deck']['z'] = 0.55; S['deck']['note'] = 'finished deck +0.55 (0.05 below the interior floor), threshold channel at SD01, SD02, D03'
    F['exterieurs']['niveau_fini'] = 3.95
    for a in F['exterieurs'].get('annotations', []):
        if a['texte'] == '+4.00': a['texte'] = '+3.95'
    # auvent d'entrée : niveau et exutoire
    ae = S['auvents'][0]; ae['z'] = [3.31, 3.46]; ae['exutoire'] = 'spout at the north end (falls 2 %)'
    note('V3-02', 'sols finis extérieurs 0.05 sous les sols intérieurs : véranda et pavillon +0.55, terrasse et balcons de l\'étage +3.95, '
         'caniveau de seuil devant les baies ; auvent d\'entrée à +3.31 / +3.46 (au-dessus de l\'imposte de D03) avec gargouille',
         'agent vérificateur 3 (FAC-017, FAC-021, FAC-022, FAC-016)', 'correction')
    # réfrigérateur : 0.10 de jeu au mur arrière ; douche de la salle de bains commune : entrée 0.70
    for q in G['mobilier']:
        if q['nom'] == 'FRIDGE (side by side)': q['rect'] = [8.33, 13.33, 9.26, 14.08]
        if q['nom'].startswith('GLASS SCREEN') and q['rect'][0] == 1.05: q['rect'] = [1.05, 8.83, 1.07, 9.68]
    # fenêtres dans les douches : soufflet dépoli (jamais coulissant dans le jet)
    for o in G['ouvertures']:
        if o.get('repere') in ('W02', 'W05'): o['ouvrant'] = 'hopper, frosted glass (in the shower)'
    # toiture : niveau +7.40 = point haut des pentes ; avaloir à +7.12 ; acrotère >= 1.00 au-dessus du point haut
    T = S['toiture']; T['niveau_haut'] = 7.40; T['niveau_avaloir'] = 7.12; T['pente'] = 0.015
    T['note_niveaux'] = 'roof finish +7.40 at the high points, falls 1.5 % to the outlet (+7.12) ; parapet +8.40 = 1.00 above the highest point'
    note('V3-03', 'réfrigérateur à 0.10 du mur ; entrée de douche 0.70 ; W02 / W05 à soufflet dépoli ; toiture : +7.40 au point haut, '
         'avaloir +7.12 (pente 1.5 %, chemin 18.8), acrotère à 1.00 au-dessus du point haut partout',
         'agent vérificateur 3 (CUI-013, CIR-020, SDE-018, SEC-006)', 'correction')
    # charges ponctuelles : poteaux de la pergola de la terrasse posés sur la dalle au-dessus du séjour / hall
    from controle_degagements import poteaux_non_portes
    F['charges_ponctuelles'] = [{'poteau': p, 'objet': 'terrace pergola post on the slab over the living room / hall'} for p in poteaux_non_portes(G, F)]
    # étendoir : bande ouest, sous les fenêtres hautes (hors de la vue des fenêtres principales)
    S['etendoir'] = {'rect': [-1.45, 10.40, -0.65, 13.60]}
    note('V3-04', '%d poteaux de pergola de l\'étage sans appui dessous : charges ponctuelles notées pour l\'ingénieur ; étendoir déplacé '
         'dans la bande ouest (sous les fenêtres hautes)' % len(F['charges_ponctuelles']), 'agent vérificateur 3 (STR-001, STR-011, SIT-014)', 'à valider par l\'ingénieur')


VEHICULE = {'nom': 'Toyota Land Cruiser 300 (design vehicle)', 'longueur': 5.15, 'largeur': 2.00, 'largeur_retros': 2.25,
            'degagement_portiere': 0.80}


def corriger_V4(niveaux, S):
    """Retour client 15/10 : stationnement de 2 Land Cruiser avec ouverture des portières, portail élargi avec portillon
    côté voie piétonne, voie piétonne séparée des voitures ; pergolas couvertes (lames + polycarbonate)."""
    V = VEHICULE
    # voie piétonne 0.90 le long de la véranda, du portillon jusqu'au parvis de l'entrée (elle sert aussi de
    # dégagement de portière côté conducteur de la voiture ouest) ; parvis entre la voie et l'allée
    S['voie_pietonne'] = {'rect': [14.30, -6.95, 15.20, -1.15], 'nom': 'pedestrian lane 0.90 (gate wicket -> entrance)'}
    S['parvis'] = {'rect': [14.30, -1.15, 15.50, 4.00], 'nom': 'entrance forecourt'}
    S['jardinieres'] = [j for j in S['jardinieres'] if j.get('rect') != [14.3, -4.95, 15.5, 4.0]]
    S['chemin_jardin']['rect'] = [8.33, -5.75, 14.30, -4.95]
    # parking : 2 places côte à côte, voitures en marche avant, portières : 0.89 entre les voitures, 0.80 côté clôture
    S['parking'] = {'rect': [15.20, -6.95, 20.89, -1.15], 'places': 2, 'revetement': 'concrete pavers',
                    'vehicules': [[15.20, -6.55, 17.20, -1.40], [18.09, -6.55, 20.09, -1.40]],
                    'note': 'designed for 2 x Land Cruiser 300 (5.15 x 2.00, 2.25 with mirrors) ; doors: lane 0.90 west (0.78 at mirror height, 5e passage), 0.89 between the cars (one door at a time), 0.80 at the east wall'}
    # portail coulissant élargi : de la voie piétonne à la travée est (6.20), portillon 0.90 au droit de la voie piétonne
    g = S['portail']; g['position'] = [14.30, -6.95, 20.50, -6.95]; g['largeur'] = 6.20
    g['coulisse_vers'] = 'ouest, derrière le mur de rue (6.20 de mur libre, x 8.10 - 14.30)'
    g['portillon']['position_dans_vantail'] = 'extrémité ouest, au droit de la voie piétonne'
    note('V4-01', 'stationnement : 2 places pour Land Cruiser 300 (5.15 x 2.00) en marche avant, voie piétonne 0.90 du portillon à '
         'l\'entrée (dégagement de portière côté conducteur), 0.89 entre les voitures (une portière à la fois), 0.80 côté clôture ; '
         'portail coulissant porté de 4.50 à 6.20 (x 14.30 - 20.50) avec portillon 0.90 au droit de la voie piétonne ; jardinière '
         'le long de la véranda remplacée par la voie et le parvis', 'demande client 15/10 (contrôle des Land Cruiser)', 'décision client')
    # pergolas : lames bois conservées + couverture polycarbonate compact anti-UV au-dessus (pente 3 %, chéneau)
    couv = {'materiau': 'compact (solid) polycarbonate 0.006 thick (to be confirmed on site), UV-protected both faces, opal tint, laid on the timber slats - '
                        'sourced in Dakar (C3s Senegal, Profiserv), delivered to The Gambia', 'pente': 0.03,
            'au_dessus_des_lames': True, 'evacuation': 'gutter + downpipe in a post'}
    S['pergola_pavillon']['couverture'] = dict(couv, evacuation='gutter on the south side -> downpipe in a post -> planter')
    niveaux['FF']['exterieurs']['pergola']['couverture'] = dict(couv, evacuation='gutter -> terrace rainwater outlet (RWO)')
    note('V4-02', 'pergolas du pavillon et de la terrasse : lames bois conservées + couverture transparente anti-UV posée au-dessus '
         'des lames (polycarbonate compact 6 mm anti-UV opale posé sur les lames, '
         'acheté à Dakar - C3s Sénégal, Profiserv - et livré en Gambie par le client ; épaisseur à confirmer sur chantier), pente 3 %, chéneau et descente dans un poteau : SD01, SD04 et D13 '
         'abrités de la pluie', 'demande client 15/10 (option préférée : lames verticales + couverture transparente)', 'décision client')


def corriger_V5(niveaux, S):
    """4e passage de l'agent vérificateur (15/10) : garde-corps du bord est de la véranda (régression V4-01), marches
    extérieures recalculées (n contremarches égales jusqu'au niveau d'arrivée), entrée de la douche parentale, étiquette du
    balcon est, sources et non-prouvés (devise)."""
    G, F = niveaux['GF'], niveaux['FF']
    # véranda : bord est (x 14.30, y -3.75 à 4.00) à 0.55 au-dessus de la voie piétonne et du parvis -> garde-corps h 1.00
    S['garde_corps_deck'] = [{'pts': [[14.30, -3.75], [14.30, 4.00]], 'h': 1.00, 'z': S['deck']['z'],
                              'type': 'anthracite steel railing, vertical bars (as the gate)'}]
    note('V5-01', 'garde-corps acier anthracite h 1.00 sur le bord est de la véranda (x 14.30, y -3.75 à 4.00, chute 0.55 sur la voie '
         'piétonne) ; ouvert au droit des marches d\'entrée', 'agent vérificateur 4 : régression de V4-01 (jardinière supprimée) (ESC-007, SIT-015)', 'correction')
    # marches extérieures : n contremarches égales = niveau d'arrivée / n ; n - 1 girons sur l'emprise
    for m in S['marches']:
        if m['montee'] == 'palier': continue
        arr = 0.45 if m['nom'].startswith('service') else S['deck']['z']
        n = m.get('n') or 4
        m['n'] = n; m['arrivee'] = arr; m['hauteur'] = round(arr / n, 4)
        m['nom'] = m['nom'].split(' (')[0] + ' (%d risers to +%.2f)' % (n, arr)
    note('V5-02', 'marches extérieures : contremarches égales jusqu\'au niveau d\'arrivée (entrée et pavillon 4 x 0.1375 vers le deck '
         '+0.55 ; service 3 x 0.15 vers le palier +0.45), n - 1 girons ; 3D en escalier (plus de bloc plein)',
         'agent vérificateur 4 (SIT-011, SIT-016, M3D-004)', 'correction')
    # douche de la salle de bains parentale : entrée 0.70
    for q in F['equipements']:
        if q['nom'] == 'GLASS SCREEN' and q['rect'] == [1.33, 11.15, 1.37, 12.55]: q['rect'] = [1.33, 11.25, 1.37, 12.55]
    # balcon est : mobilier regroupé au sud, étiquette au nord
    for s_ in F['exterieurs']['sols']:
        if s_['nom'] == 'BALCONY' and s_['rect'][0] > 13: s_['etiquette_xy'] = [13.85, 13.20]
    for m in F['mobilier']:
        if m.get('exterieur') and m['rect'][0] > 13.5:
            r = m['rect']
            if m['nom'] == 'COFFEE TABLE': m['rect'] = [13.72, 11.40, 14.22, 11.85]
            elif r[1] > 12: m['rect'] = [13.65, 11.95, 14.30, 12.60]
            else: m['rect'] = [13.65, 10.65, 14.30, 11.30]
    # devise : sources et points non prouvés, inscrits dans la maquette
    S['parking']['source_vehicule'] = 'Toyota spec sheets: L 4.950-5.130, W 1.980-2.010 (Toyota Brunei, Rwanda, Zimbabwe, NZ) ; design envelope 5.15 x 2.00'
    S['portail']['type_coulissant'] = 'sliding gate on a ground rail with top guide rollers (not cantilever: no counter-tail needed)'
    for pg in (S['pergola_pavillon'], F['exterieurs']['pergola']):
        pg['couverture']['non_prouve'] = 'no manufacturer datasheet yet: span on slats, thermal expansion fixings, wind uplift - stage 3'
    note('V5-03', 'entrée de la douche parentale 0.70 ; balcon est réorganisé ; portail sur rail au sol (non autoportant) ; sources '
         'du véhicule de calcul et points non prouvés (polycarbonate : fiche fabricant à l\'étape 3) notés dans la maquette',
         'agent vérificateur 4 (CIR-020, DOC-013, PRO-008)', 'correction')


def corriger_D_avant(niveaux, S):
    """Indice D, avant le calcul des auvents : fenêtre W07 centrée sur la chambre 3 (intérieur x 0.15 - 4.25)."""
    o = deplacer_ouverture(niveaux['GF'], 'GF-W07', 1.20, 3.20, type_fenetre='A'); hauteur_std(o, NIV['GF']['z'])


def corriger_D(niveaux, S):
    """Retour client sur l'indice C (15/10 soir) -> indice D."""
    G = niveaux['GF']
    G['mobilier'] = [m for m in G['mobilier'] if not (m['nom'] == 'PLANT POT' and m['rect'][0] == 7.00 and m['rect'][1] == 6.00)]
    G['mobilier'] = [m for m in G['mobilier'] if m['nom'] != 'LINEN']
    G['equipements'] = [q for q in G.get('equipements', []) if not q['nom'].startswith('VENT GRILLE')]
    next(o for o in G['ouvertures'] if o['id'] == 'GF-D10').pop('grille_basse', None)
    # auvent commun D10 + W08 (même pièce : arrière-cuisine) ; W07 (chambre 3, recentrée) garde son auvent (retour client 15/10)
    a7 = next(a for a in G['auvents'] if a['repere'] == 'CN07')
    a7['rect'] = [4.43, 14.30, 7.58, 14.90]; a7['fenetre'] = 'D10 + W08'
    # toiture : 3 siphons (angles NO, NE, SO, schéma client), formes de pente 1.5 % vers le plus proche
    T = S['toiture']; T['avaloirs'] = [[0.35, 13.73, 0.59, 13.97], [12.51, 13.73, 12.75, 13.97], [0.35, 0.33, 0.59, 0.57]]
    from shapely.geometry import box as _b, Point as _P
    toit = _b(0.15, 0.15, 12.95, 14.15).difference(_b(6.43, 0, 13.1, 5.60)).difference(_b(*T['edicule']))
    cs = [((r[0] + r[2]) / 2, (r[1] + r[3]) / 2) for r in T['avaloirs']]; dmax = 0.0
    x0, y0, x1, y1 = toit.bounds; x = x0
    while x <= x1:
        y = y0
        while y <= y1:
            if toit.contains(_P(x, y)): dmax = max(dmax, min(((x - c[0]) ** 2 + (y - c[1]) ** 2) ** 0.5 for c in cs))
            y += 0.25
        x += 0.25
    T['niveau_avaloir'] = round(T['niveau_haut'] - T['pente'] * dmax, 2); T['distance_max'] = round(dmax, 2)
    T['note_niveaux'] = ('roof finish +7.40 at the high points, falls 1.5 %% to 3 outlets (NW, NE, SW corners, +%.2f) ; parapet +8.40 = '
                         '1.00 above the highest point' % T['niveau_avaloir'])
    note('D-01', 'toiture : 3 siphons (angles nord-ouest, nord-est, sud-ouest), formes de pente 1.5 %% vers le plus proche ; siphons à '
         '+%.2f (distance maximale %.2f)' % (T['niveau_avaloir'], dmax), 'retour client 15/10 (schéma des siphons)', 'décision client')
    note('D-02', 'pot de fleurs du hall retiré (dans l\'axe de D05, aire de manœuvre) ; placard à linge du couloir retiré (devant D08, '
         '0.55 de passage) ; contrôle K-MANOEUVRE', 'retour client 15/10 + nouveau contrôle', 'correction')
    note('D-03', 'fenêtre W07 centrée sur la chambre 3 (1.20 - 3.20) ; auvent commun D10 + W08 (même pièce, 4.43 - 7.58), W07 avec '
         'son propre auvent ; grille de ventilation haute de l\'arrière-cuisine retirée (lue comme un '
         'poteau ; ventilation reprise à l\'étape 3)', 'retour client 15/10', 'décision client')
    note('D-04', 'faïence toute hauteur sur tous les murs de la cuisine et de l\'arrière-cuisine', 'retour client 15/10', 'décision client')
    note('D-05', 'salle de bains parentale : étiquette « JACUZZI + BATHTUB » (un seul appareil 2 places, baignoire et jacuzzi en un), '
         'pour que la demande de la cliente se lise directement ; appareil et disposition inchangés', 'retour client 16/10', 'décision client')


def corriger_V6(niveaux, S):
    """Simulation de parcours (demande client 15/10, outil atelier parcours.py) : défauts de circulation trouvés par le
    calcul du plus court chemin et de la largeur libre."""
    G = niveaux['GF']
    for m in G['mobilier']:
        if m['nom'] == 'LINEN' and m['rect'] == [4.4, 11.1, 5.5, 11.5]: m['rect'] = [4.95, 11.10, 5.50, 11.50]
    S['garde_corps_deck'][0]['pts'] = [[14.27, -3.75], [14.27, 4.00]]
    # pavillon : le canapé (3.64 de long) barrait les marches vers le jardin -> salon contre le côté ouest, passage libre
    # de la baie SD01 aux marches (x 10.60 - 12.43, 1.80 de large)
    nouv = {'OUTDOOR SOFA': [[7.90, -3.30, 8.75, -0.80]], 'COFFEE TABLE': [[9.05, -2.55, 9.75, -1.55]],
            'ARMCHAIR': [[9.95, -2.95, 10.60, -2.30], [9.95, -1.80, 10.60, -1.15]]}
    k = {}
    for m in G['mobilier']:
        if m.get('exterieur') and m['rect'][1] < 0 and m['nom'] in nouv:
            i = k.get(m['nom'], 0); m['rect'] = nouv[m['nom']][i]; k[m['nom']] = i + 1
    note('V6-01', 'placard à linge du couloir réduit à 0.55 (x 4.95 - 5.50) : il occupait la moitié de l\'accès à la porte D08 de la '
         'chambre 3 (0.45 de passage pour une porte de 0.80) ; garde-corps de la véranda posé sur le deck (x 14.27) : voie '
         'piétonne libre de 0.90 ; salon du pavillon réorganisé contre le côté ouest (le canapé barrait les marches du jardin) : '
         'passage de 1.80 de la baie SD01 aux marches', 'simulation de parcours (outil parcours.py) : chambre 3 inaccessible, '
         'jardin atteint seulement par la véranda', 'correction')


REGISTRE = [
    # (id, lot, élément, spécification (anglais = livrables), unité de métré, quantité depuis la maquette, origine de la décision, statut)
    ('M01', 'Finishes', 'Floors: kitchen, scullery, all wet rooms', 'anti-slip porcelain tiles 0.60 x 0.60, R11, warm grey', 'm2', 'pieces[].finitions.sol = antiderapant', 'client 15/10 (C) - antidérapant cuisine, salles d\'eau, terrasses', 'validated'),
    ('M02', 'Finishes', 'Floors: terraces, balconies, veranda, pavilion', 'anti-slip outdoor porcelain tiles 0.60 x 0.60, R11', 'm2', 'FF.exterieurs.sols + site.deck', 'client 15/10 (C)', 'validated'),
    ('M03', 'Finishes', 'Floors: bedrooms, dressing', 'wood-effect porcelain planks 0.20 x 1.20', 'm2', 'pieces[].finitions.sol = sol_bois', 'atelier 15/10 (C), shown in 3D', 'to validate (mood board, stage 4)'),
    ('M04', 'Finishes', 'Floors: living, lounge, hall, landing, corridors', 'porcelain tiles 0.60 x 0.60, light beige', 'm2', 'pieces[].finitions.sol = sol_carrelage', 'atelier 15/10 (C)', 'to validate (stage 4)'),
    ('M05', 'Finishes', 'Wall tiles: bathrooms, en-suites, WCs', 'ceramic wall tiles 0.30 x 0.60, light greige, full height, cut around openings with returns', 'm2', 'pieces[].finitions.faience (3D: plaques de faïence)', 'client 14/10 (full height) and 15/10 (cut around openings)', 'validated'),
    ('M06', 'Finishes', 'Kitchen wall tiles', 'ceramic wall tiles 0.30 x 0.30, full height on all walls, cut around openings with returns (client 15/10)', 'm2', 'crédence (3D)', 'client 15/10', 'validated'),
    ('M07', 'Finishes', 'Scullery wall tiles', 'ceramic wall tiles 0.30 x 0.30, full height on all walls (client 15/10)', 'm2', 'crédence arrière-cuisine (3D)', 'client 15/10 (C5)', 'validated'),
    ('M08', 'Finishes', 'Paint', 'warm white (default), linen beige (living, lounge), soft greige (bedrooms, dressing) ; accent walls behind bed heads (sage / clay)', 'm2', 'pieces[].finitions.murs', 'atelier 15/10 (C)', 'to validate (stage 4)'),
    ('M09', 'Joinery', 'Windows', 'aluminium, anthracite frame, 2 sliding panels (max 2.00 wide) ; wet rooms: hopper, frosted (shower windows W02, W05) ; W12 fixed', 'u + m2', 'ouvertures type fenetre', 'client 15/10 (C6-C8) + vérificateur', 'validated'),
    ('M10', 'Joinery', 'Sliding doors SD01-SD05', 'aluminium, anthracite, 2.00 or 3.00 x 2.20 ; folding steel security grilles on ground-floor sliding doors and SD04', 'u', 'ouvertures baie_coulissante + grilles', 'client 15/10', 'validated'),
    ('M11', 'Joinery', 'Entrance door D03', '1.00 + 0.50, armoured steel, wood-effect finish', 'u', 'GF-D03', 'client 15/10 (C6)', 'validated'),
    ('M12', 'Joinery', 'Exterior doors (ground floor), roof door D20', 'steel doors ; D10 with low vent grille ; D20 with 0.15 upstand', 'u', 'portes extérieures + toiture.porte_edicule', 'client 15/10', 'validated'),
    ('M13', 'Joinery', 'Terrace door D13', '1.00 swing door, steel frame, armoured glass', 'u', 'FF-D03 (D13)', 'client 15/10 (C17)', 'validated'),
    ('M14', 'Joinery', 'Interior doors', 'swing doors h 2.20 ; sliding doors where noted (kitchen D18, WC D19)', 'u', 'ouvertures porte', 'client 15/10 (C6)', 'validated'),
    ('M15', 'Metalwork', 'Security grilles', 'steel grilles inside all ground-floor windows', 'm2', 'GF.grilles', 'client 14/10 (porte A)', 'validated'),
    ('M16', 'Metalwork', 'Glazed guardrails', 'laminated glass guardrails h 1.00 (void, stairs, landings, terrace, balconies)', 'm', 'garde_corps_* + garde_corps_vitres', 'standard + vérificateur', 'validated'),
    ('M17', 'Structure', 'RC canopies', 'reinforced concrete canopies 0.60 deep, window + 0.10 each side, 0.10 thick, cast with the lintel', 'u + m3', 'niveaux[].auvents', 'client 15/10 (SABTP standard)', 'validated'),
    ('M18', 'Pergolas', 'Pergola structure', 'anthracite steel frame on base plates, timber slats ; intermediate post when span > 6.40', 'm + u', 'site.pergola_pavillon + FF.exterieurs.pergola', 'client 15/10', 'validated'),
    ('M19', 'Pergolas', 'Pergola roof sheet', 'compact polycarbonate 0.006 thick (to be confirmed on site), UV-protected both faces, opal, laid on the slats, 3 % fall, gutter + downpipe in a post ; sourced in Dakar (C3s Senegal, Profiserv)', 'm2', 'pergolas[].couverture', 'client 15/10 (thickness to confirm on site)', 'validated'),
    ('M20', 'Facades', 'Render', 'smooth render, warm white #f4f2ed', 'm2', 'façades', 'esquisse d\'origine', 'validated'),
    ('M21', 'Facades', 'Stone cladding', 'natural stone cladding #d8cdbb (south ground floor 0.00-6.43, east entrance wall)', 'm2', 'site.parements (pierre)', 'esquisse d\'origine + vérificateur', 'validated'),
    ('M22', 'Facades', 'Timber cladding', 'timber cladding #b07d52 (west first floor, master suite) ; timber slats of the balcony frames', 'm2', 'site.parements (bois) + cadres', 'esquisse d\'origine', 'validated'),
    ('M23', 'Facades', 'Anthracite frames and coping', 'anthracite #3a3e43 balcony frames (+8.40), parapet coping', 'm', 'cadres + acrotères', 'esquisse d\'origine', 'validated'),
    ('M24', 'External works', 'Boundary wall and gate', 'rendered blockwork wall 0.20, h 2.10 street / 2.00 neighbours, anthracite coping, timber slats street side ; sliding steel gate 6.20 x 2.10 with 0.90 wicket', 'm + u', 'site.cloture + site.portail', 'client 14/10 + 15/10 (gate 6.20)', 'validated'),
    ('M25', 'External works', 'Paving', 'concrete pavers: parking (2 x Land Cruiser), pedestrian lane 0.90, forecourt, paved path ; stepping stones', 'm2', 'site.parking, voie_pietonne, parvis, allee, chemin_jardin', 'client 15/10', 'validated'),
    ('M26', 'Roof', 'Roof terrace', 'waterproofing + screed to falls 1.5 % to one outlet (+7.12 at the outlet, +7.40 high points), parapet +8.40', 'm2', 'toiture', 'client 15/10 (single outlet) + vérificateur', 'validated'),
    ('M27', 'Plumbing', 'Water tanks, PV, AC', '2 x 2000 L tanks (dia. 1.30), PV-ready zone 3 x 2 panels, 3 AC outdoor units', 'u', 'site.toiture', 'atelier 15/10', 'to validate (stage 3)'),
    ('M28', 'Kitchen', 'Kitchen equipment', 'side-by-side fridge, cooker + oven with hood, L worktop, wall units (never over a window), island + table for 6 (T unit)', 'u + m', 'GF.mobilier / equipements (cuisine)', 'client 15/10 (C1-C5)', 'validated'),
    ('M29', 'Sanitary', 'Master bath', 'built-in 2-person jacuzzi + bathtub (one unit: whirlpool bathtub) on a tiled deck, walk-in shower 2.00 x 1.20, double vanity 1.80, closed WC', 'u', 'FF.mobilier (master bath)', 'client 15/10 (C16)', 'validated'),
    ('M30', 'Sanitary', 'Shower screens', 'fixed glass screens, entry 0.70 (ground-floor shower rooms, master bath)', 'u', 'GLASS SCREEN (mobilier / equipements)', 'vérificateur 15/10', 'validated'),
    ('M31', 'Metalwork', 'Veranda railing', 'anthracite steel railing h 1.00, vertical bars, east edge of the veranda (x 14.27, y -3.75 to 4.00)', 'm', 'site.garde_corps_deck', 'vérificateur 15/10 (V5-01)', 'validated'),
    ('M32', 'External works', 'External steps', 'concrete steps, equal risers to the arrival level (entrance / pavilion 4 x 0.1375, service 3 x 0.15)', 'u', 'site.marches', 'vérificateur 15/10 (V5-02)', 'validated'),
]


def registre_materiaux():
    """Registre des matériaux et finitions décidés (demande client 15/10) : une ligne par décision, avec l'unité de
    métré et l'endroit de la maquette d'où le métré tirera la quantité. Repris par le métré de fin de projet."""
    cles = ('id', 'lot', 'element', 'specification', 'unite', 'quantite_depuis', 'decision', 'statut')
    return [dict(zip(cles, r)) for r in REGISTRE]


def ecrire_registre(reg):
    with open(os.path.join(os.path.dirname(HERE), 'REGISTRE_MATERIAUX.md'), 'w') as f:
        f.write('# Registre des matériaux et finitions - YAMA HOUSE\n\nGénéré par `maquette/construire_maquette.py` (aussi dans '
                '`maquette.json`, clé `registre_materiaux`). Chaque décision prise sur un matériau, une finition ou un équipement '
                'y est inscrite ; le **métré de fin de projet** reprend ce registre (colonne « quantité depuis la maquette »). '
                'Spécifications en anglais (livrables).\n\n')
        f.write('| Réf. | Lot | Élément | Spécification | Unité | Quantité depuis la maquette | Décision | Statut |\n|---|---|---|---|---|---|---|---|\n')
        for r in reg:
            f.write('| %s |\n' % ' | '.join(str(r[k]) for k in ('id', 'lot', 'element', 'specification', 'unite', 'quantite_depuis', 'decision', 'statut')))


def auvents(niveaux, site_):
    """Standard SABTP : auvent béton armé (débord 0.60, fenêtre + 0.10 de chaque côté, épaisseur 0.10) au linteau de toute
    fenêtre extérieure qui n'est pas sous un balcon, un cadre ou un auvent existant."""
    couverts = [a['rect'] for a in site_['auvents']] + [s['rect'] for s in niveaux['FF']['exterieurs']['sols'] if s['nom'] == 'BALCONY']
    n = 0
    for niv, M in niveaux.items():
        M['auvents'] = []
        for o in M['ouvertures']:
            if o['type'] != 'fenetre' or not o.get('facade'): continue
            x0, y0, x1, y1 = o['rect']; f = o['facade']
            d = 0.60
            r = {'S': [x0 - 0.10, y0 - d, x1 + 0.10, y0], 'N': [x0 - 0.10, y1, x1 + 0.10, y1 + d],
                 'W': [x0 - d, y0 - 0.10, x0, y1 + 0.10], 'E': [x1, y0 - 0.10, x1 + d, y1 + 0.10]}[f]
            if any(box(*r).intersection(box(*c)).area > 0.8 * box(*r).area for c in couverts):
                o['protegee_par'] = 'balcony / canopy above'; continue
            n += 1
            M['auvents'].append({'repere': 'CN%02d' % n, 'fenetre': o.get('repere', o['id']), 'rect': [round(v, 3) for v in r],
                                 'z0': o['z_haut'], 'z1': round(o['z_haut'] + 0.10, 2), 'facade': f})
    note('C24', '%d auvents en béton armé au-dessus des fenêtres non protégées (débord 0.60, fenêtre + 0.10 de chaque côté, '
         'épaisseur 0.10, encastrés au linteau)' % n, 'standard SABTP dicté par le client', 'décision client')


def hauteurs(niveaux):
    ext = []
    for n, M in niveaux.items():
        for o in M['ouvertures']:
            if o['type'] in ('traversee', 'passage'): continue
            x0, y0, x1, y1 = o['rect']
            if y0 < 0.01: ext.append(('S', o, x0, x1))
            elif y1 > H - 0.01: ext.append(('N', o, W - x1, W - x0))
            elif x1 > W - 0.01: ext.append(('E', o, y0, y1))
            elif x0 < 0.01: ext.append(('W', o, H - y1, H - y0))
    rapport = {}
    for fac, page in (('S', 22), ('E', 23), ('N', 24), ('W', 25)):
        vit, info = pf.vitrages(PDF, page)
        oo = [{'id': o['id'], 'a0': a, 'a1': b} for f, o, a, b in ext if f == fac]
        d, m = pf.recaler(vit, oo)
        rapport[fac] = {'apparies': len(m), 'ouvertures': len(oo), 'residu_niveaux': info['residu_niveaux_m']}
        for oid, v in m:
            o = next(o for f, o, a, b in ext if o['id'] == oid)
            o['z_bas'], o['z_haut'] = round(v['z0'], 2), round(v['z1'], 2)
            o['source_hauteur'] = 'façade ' + fac
            o['facade'] = fac
        for f, o, a, b in ext:
            if f == fac: o['facade'] = fac
    return rapport


def completer_hauteurs(M, n):
    z = NIV[n]['z']
    for o in M['ouvertures']:
        if o['type'] in ('traversee',): continue
        if 'z_bas' in o: continue
        if o['type'] in ('porte', 'porte_coulissante'):
            ht = 2.40 if not o.get('facade') else 2.50
            o['z_bas'], o['z_haut'] = z, round(z + ht, 2)
            o['source_hauteur'] = 'règle : portes intérieures 2.40 (amélioration 4 validée)' if not o.get('facade') else 'règle : porte extérieure 2.50 (alignée sur les linteaux des baies)'
        elif o['type'] == 'baie_coulissante':
            ht = 2.60 if n == 'FF' else 2.50
            o['z_bas'], o['z_haut'] = z, round(z + ht, 2); o['source_hauteur'] = 'règle : baie intérieure, même hauteur que les baies de façade du niveau'
        elif o['type'] == 'passage':
            o['z_bas'], o['z_haut'] = z, round(z + 2.50, 2); o['source_hauteur'] = 'règle : passage 2.50'
        else:
            o['a_verifier'] = True


# ---------------------------------------------------------------- repères uniques (anglais, livrables)
def reperes(niveaux):
    cpt = {'D': 0, 'SD': 0, 'W': 0, 'O': 0}
    pre = {'porte': 'D', 'porte_coulissante': 'D', 'baie_coulissante': 'SD', 'fenetre': 'W', 'passage': 'O'}
    for n in ('GF', 'FF'):
        for o in sorted(niveaux[n]['ouvertures'], key=lambda o: (o['rect'][1], o['rect'][0])):
            if o['type'] == 'traversee': continue
            p = pre[o['type']]; cpt[p] += 1
            o['repere'] = '%s%02d' % (p, cpt[p])


def reperes_complement(niveaux):
    """Indice C : les ouvertures existantes gardent leur repère ; les nouvelles (ou celles qui changent de famille) prennent
    le numéro libre suivant. Les numéros supprimés ne sont pas réutilisés."""
    pre = {'porte': 'D', 'porte_coulissante': 'D', 'baie_coulissante': 'SD', 'fenetre': 'W', 'passage': 'O'}
    pris = {}
    for n in ('GF', 'FF'):
        for o in niveaux[n]['ouvertures']:
            r = o.get('repere', '')
            p = r.rstrip('0123456789')
            if r and pre[o['type']] == p: pris[p] = max(pris.get(p, 0), int(r[len(p):]))
    for n in ('GF', 'FF'):
        for o in sorted(niveaux[n]['ouvertures'], key=lambda o: (o['rect'][1], o['rect'][0])):
            p = pre[o['type']]
            if o.get('repere', '').rstrip('0123456789') != p:
                ancien = o.get('repere'); pris[p] = pris.get(p, 0) + 1; o['repere'] = '%s%02d' % (p, pris[p])
                note('C-REP', 'nouveau repère %s (%s%s)' % (o['repere'], o['id'], ', ancien ' + ancien if ancien else ''), 'numérotation stable de l\'indice B')


def grilles(M):
    """Décision client : grilles de sécurité sur toutes les fenêtres du RDC ; baies : grille repliable intérieure."""
    G = []
    for o in M['ouvertures']:
        if o['type'] == 'fenetre':
            G.append({'repere': 'GR' + o['repere'][1:], 'ouverture': o['repere'], 'type': 'fixed decorative grille, anthracite, inside'})
        elif o['type'] == 'baie_coulissante':
            G.append({'repere': 'GR' + o['repere'][2:] + 'S', 'ouverture': o['repere'], 'type': 'folding security grille, inside'})
    M['grilles'] = G
    note('Q4', '%d grilles de sécurité au RDC (fenêtres : grilles fixes décoratives ; baies : grilles repliables intérieures)' % len(G),
         'décision client : grilles sur toutes les fenêtres du RDC', 'décision client')


# ---------------------------------------------------------------- site
def site():
    note('I1', 'clôture (mur 0.20 enduit, h 2.10 sur rue, 2.00 sur limites), portail coulissant 4.50 avec portillon '
         'piéton intégré, devant le parking', 'portail et clôture absents des plans ; décision client : portillon dans le vantail',
         'décision client + autonome (hauteurs)')
    note('I2', 'allée pavée 1.20 du portail aux marches de la véranda', 'pas de cheminement dessiné')
    note('R3', 'cage de gaz déplacée contre le pignon ouest aveugle de la chambre 3 (à plus de 1.00 de toute ouverture)',
         'relecture : la cage chevauchait la fenêtre W08 au-dessus du banc gaz', 'décision autonome (sécurité)')
    note('R1', 'clôture ouverte sur 4.50 au droit du portail ; vantail, portillon 0.90 et zone de refoulement dessinés',
         'relecture : portail dessiné sans ouverture dans la clôture')
    note('R2', 'allée pavée existante (1.93) nommée, alignée sur le portillon ; chemin en pas japonais du pavillon à l\'allée',
         'relecture : allée illisible ; marches du pavillon sans chemin')
    note('R22', 'barbecue sorti de la pergola en bois (contre le mur nord de la terrasse) ; parking élargi à 5.16',
         'relecture inter-planches : barbecue sous les lames bois à 0.12 d\'un poteau ; parking 4.90 (mini 5.00)')
    note('I11', 'étendoir à linge dans la bande nord (1.51), près de la porte de service', 'aucun espace de séchage')
    return {
        'source': 'contours relus sur le plan vectoriel SD-004 (aplats et traits hors murs), 15/10',
        'parcelle': {'contour': [[-1.87, -6.95], [20.89, -6.95], [20.89, 15.81], [-1.87, 15.81]], 'surface': 518.0},
        'cloture': {'epaisseur': 0.20, 'hauteur_rue': 2.10, 'hauteur_limites': 2.00,
                    'materiau': 'rendered blockwork wall, anthracite coping ; street side : timber slat screen in the upper part',
                    'nu_interieur': [[-1.87, -6.95], [20.89, -6.95], [20.89, 15.81], [-1.87, 15.81]]},
        'portail': {'repere': 'GT01', 'type': 'sliding gate with integrated pedestrian wicket door', 'largeur': 4.50, 'hauteur': 2.10,
                    'position': [15.93, -6.95, 20.43, -6.95], 'coulisse_vers': 'ouest, derrière le mur de rue (4.50 de mur libre)',
                    'portillon': {'largeur': 0.90, 'hauteur': 2.00, 'position_dans_vantail': 'extrémité ouest (côté allée)'}},
        'parking': {'rect': [15.73, -6.65, 20.89, -1.15], 'places': 2, 'revetement': 'concrete pavers', 'note': 'largeur 5.16 (mini 5.00)'},
        'allee': {'rect': [15.50, -1.15, 17.43, 6.60], 'revetement': 'concrete pavers'},
        'deck': {'contour': [[13.1, 6.95], [14.3, 6.95], [14.3, -3.75], [7.63, -3.75], [7.63, 0.0], [13.1, 0.0]], 'z': 0.60,
                 'parties': {'veranda': [13.10, 0.0, 14.30, 6.95], 'pavillon': [7.63, -3.75, 12.63, 0.0]}},
        'pergola_pavillon': {'rect': [7.63, -3.75, 12.63, 0.0], 'poteaux': [[7.63, -0.2, 7.83, 0.0], [12.43, -0.2, 12.63, 0.0], [7.63, -3.75, 7.83, -3.55], [12.43, -3.75, 12.63, -3.55]]},
        'marches': [{'nom': 'entrance steps (4 x 0.15)', 'rect': [14.30, 4.00, 15.50, 6.60], 'montee': 'ouest'},
                    {'nom': 'pavilion steps (4 x 0.15)', 'rect': [8.33, -4.95, 11.93, -3.75], 'montee': 'nord'}],
        'jardinieres': [{'contour': [[13.1, 6.95], [14.3, 6.95], [14.3, 6.6], [15.5, 6.6], [15.5, 8.15], [14.3, 8.15], [14.3, 14.3], [13.1, 14.3]]},
                        {'contour': [[6.43, -4.95], [8.33, -4.95], [8.33, -3.75], [7.63, -3.75], [7.63, 0.0], [6.43, 0.0]]},
                        {'rect': [11.93, -4.95, 14.30, -3.75]}, {'rect': [14.30, -4.95, 15.50, 4.00]}, {'rect': [0.0, -1.20, 6.43, 0.0]}],
        'auvents': [{'nom': 'entrance canopy', 'rect': [13.10, 4.15, 14.60, 6.85]},
                    {'nom': 'first-floor garden balcony above', 'rect': [13.10, 10.35, 14.60, 13.65]},
                    {'nom': 'first-floor balcony above', 'rect': [0.43, -1.80, 6.03, 0.0]}],
        'cage_gaz': {'rect': [-1.00, 12.90, -0.10, 14.00], 'note': 'vent grilles low + high ; > 1.00 from any opening ; gas pipe along the north wall to the scullery'},
        'chemin_jardin': {'rect': [8.33, -5.75, 15.50, -4.95], 'nom': 'garden path (stepping stones)'},
        'reculs': {'ouest': 1.87, 'sud': 6.95, 'nord': 1.51, 'est': 7.79},
        'annotations': [
            {'texte': 'VERANDA 1.20  +0.60', 'pos': [13.70, 1.30], 'rot': 90, 'gras': True, 'h': 0.13},
            {'texte': 'PAVILION (pergola) - deck +0.60', 'pos': [10.13, -0.78], 'gras': True, 'h': 0.13},
            {'texte': 'ENTRANCE', 'pos': [16.20, 5.30], 'gras': True, 'h': 0.18},
            {'texte': '±0.00 (natural ground)', 'pos': [18.90, 1.00], 'h': 0.13, 'coul': [0.7, 0.29, 0.0]},
            {'texte': 'GARDEN', 'pos': [18.90, 7.60], 'gras': True, 'h': 0.20, 'coul': [0.35, 0.5, 0.3]},
            {'texte': 'store under stair (coats + shoes)', 'pos': [10.60, 8.20], 'h': 0.10},
            {'texte': 'Boundary wall 0.20: h 2.10 street side, h 2.00 neighbours', 'pos': [3.2, -6.65], 'h': 0.12},
        ],
        'etendoir': {'rect': [0.50, 14.55, 3.50, 15.30]},
        'arbres': [{'centre': [4.33, -3.55], 'diametre': 2.0}, {'centre': [1.73, -4.35], 'diametre': 2.8},
                   {'centre': [17.73, 11.65], 'diametre': 3.2}, {'centre': [16.73, 14.05], 'diametre': 2.0}],
    }


def main():
    niveaux = {n: charger(n) for n in ('GF', 'FF')}
    for n, M in niveaux.items():
        M['ouvertures'] = [o for o in M['ouvertures'] if o['type'] != 'traversee']
        M['mobilier'] = [m for m in M['mobilier'] if not m['nom'].startswith(('+', 'open to', 'pergola'))] + nommer(M)
        M['formes'] = []      # tout ce qui compte est désormais nommé
        for m in M['mobilier']:
            m['rect_origine'] = list(m['rect'])   # pour reprendre le symbole du dessin d'origine s'il n'a pas changé de taille
    for n, M in niveaux.items():      # noms de pièces : « VOID + LANDING » -> LANDING (le vide est un élément, pas une pièce)
        for pc in M['pieces']:
            if pc.get('nom') and 'VOID' in pc['nom']:
                pc['nom'] = ' + '.join(x for x in pc['nom'].split(' + ') if x != 'VOID')
    rap = hauteurs(niveaux)
    corriger_GF(niveaux['GF']); corriger_FF(niveaux['FF']); corriger_relecture(niveaux)
    for n, M in niveaux.items():
        completer_hauteurs(M, n)
    # extérieurs de l'étage (relus sur SD-005) et symboles d'escalier
    niveaux['FF']['exterieurs'] = {
        'sols': [{'nom': 'ROOF TERRACE (pergola)', 'rect': [6.43, 0.0, 13.10, 5.60]},
                 {'nom': 'BALCONY', 'rect': [0.43, -1.80, 6.03, 0.0], 'surface': 10.1},
                 {'nom': 'BALCONY', 'rect': [13.10, 10.35, 14.60, 13.65], 'surface': 4.9}],
        'garde_corps_vitres': [[[6.43, 0.03], [13.07, 0.03], [13.07, 5.60]],
                               [[0.46, 0.0], [0.46, -1.77], [6.0, -1.77], [6.0, 0.0]],
                               [[13.1, 10.38], [14.57, 10.38], [14.57, 13.62], [13.1, 13.62]],
                               [[8.37, 6.85], [8.37, 8.50], [11.88, 8.50], [11.88, 6.85]]],
        'pergola': {'rect': [6.43, 0.65, 12.43, 4.95], 'note': 'anthracite frame + timber slats ; beams fixed to the bedroom wall (base plates + anchor bolts)'},
        'avaloirs': [[11.85, 0.55, 12.05, 0.75]],
        'jardinieres': [[6.73, 0.05, 12.78, 0.45], [12.58, 0.45, 12.98, 5.45]],
        'vide': [8.37, 6.85, 11.88, 8.50],
        'dessous': [{'nom': 'pavilion pergola below', 'rect': [7.63, -3.75, 12.63, 0.0]}],
        'annotations': [{'texte': 'pergola above (anthracite frame + timber slats)', 'pos': [9.78, 0.56], 'h': 0.10},
                        {'texte': '+4.00', 'pos': [7.75, 1.40], 'h': 0.13, 'gras': True},
                        {'texte': 'stair up to roof terrace +7.40', 'pos': [10.10, 6.30], 'h': 0.10},
                        {'texte': 'glazed guardrail h 1.00', 'pos': [3.23, -2.05], 'h': 0.10},
                        {'texte': 'lockable sliding door + blackout curtain', 'pos': [5.55, 2.85], 'h': 0.09, 'rot': 90},
                        {'texte': 'RWO (falls to outlet)', 'pos': [11.30, 0.95], 'h': 0.08}],
    }
    niveaux['GF']['annotations'] = []
    niveaux['GF']['escalier'] = {'depart': [12.43, 6.95], 'texte': 'UP', 'marches': '20 x 0.17 / 0.27, w 1.10, landing +1.62'}
    niveaux['FF']['escalier'] = {'depart': [8.92, 6.02], 'texte': 'UP', 'marches': '20 x 0.17 / 0.27 to roof +7.40'}
    reperes(niveaux)                 # repères de l'indice B conservés (le client s'y réfère)
    corriger_C(niveaux)
    corriger_V1(niveaux)
    reperes_complement(niveaux)
    for o in niveaux['FF']['ouvertures']:      # étiquette SD05 posée côté salon (elle chevauchait « BALCONY »)
        if o.get('repere') == 'SD05': o['etiquette_xy'] = [12.62, 10.75]
    grilles(niveaux['GF'])
    sd04 = next(o for o in niveaux['FF']['ouvertures'] if o['id'] == 'FF-SD02')
    niveaux['FF']['grilles'] = [{'repere': 'GR' + sd04['repere'][2:] + 'S', 'ouverture': sd04['repere'], 'type': 'folding security grille, inside'}]
    note('C25', 'grilles accordéon métalliques sur toutes les portes-fenêtres du RDC et sur SD04 (chambre -> terrasse commune)',
         'décision client', 'décision client')
    S = site()
    S.pop('cage_gaz', None)
    S['annotations'] = [a for a in S['annotations'] if 'store under stair' not in a['texte']]
    site_V1(S, niveaux)
    corriger_V2(niveaux, S)
    corriger_V3(niveaux, S)
    corriger_V4(niveaux, S)
    corriger_V5(niveaux, S)
    corriger_V6(niveaux, S)
    corriger_D_avant(niveaux, S)
    auvents(niveaux, S)
    corriger_D(niveaux, S)
    finitions(niveaux)
    for n, M in niveaux.items():
        M['z'] = NIV[n]['z']
        json.dump(M, open(os.path.join(HERE, n + '_niveau.json'), 'w'), indent=1, ensure_ascii=False)
    # exigences fortes du programme / de la cliente, à lire telles quelles sur les planches (contrôle PRG-001, retex 16/10)
    EXIGENCES = [
        {'id': 'E1', 'texte': 'jacuzzi + baignoire (un seul appareil 2 places) dans la salle de bains parentale', 'planche': 'SD-005', 'libelle': 'JACUZZI + BATHTUB'},
        {'id': 'E2', 'texte': 'double vasque, suite parentale', 'planche': 'SD-005', 'libelle': 'DOUBLE VANITY'},
        {'id': 'E3', 'texte': 'douche à l italienne séparée', 'planche': 'SD-005', 'libelle': 'WALK-IN SHOWER'},
        {'id': 'E4', 'texte': 'réfrigérateur américain en cuisine', 'planche': 'SD-004', 'libelle': 'FRIDGE SxS'},
        {'id': 'E5', 'texte': 'portail coulissant 6.20 avec portillon intégré 0.90', 'planche': 'SD-004', 'libelle': 'SLIDING GATE 6.20 x 2.10, INTEGRATED WICKET DOOR 0.90'},
        {'id': 'E6', 'texte': 'deux Land Cruiser 300 stationnés', 'planche': 'SD-004', 'libelle': 'LAND CRUISER'},
        {'id': 'E7', 'texte': 'grilles de sécurité sur toutes les fenêtres du RDC', 'planche': 'SD-004', 'libelle': 'security grille'},
        {'id': 'E8', 'texte': 'évacuation des eaux pluviales de la toiture', 'planche': 'SD-006', 'libelle': 'RWO'},
    ]
    maquette = {'projet': 'YAMA HOUSE', 'unite': 'm', 'repere': 'origine angle SO du bâtiment, x est, y nord, z NGL',
                'niveaux_cotes': {'NGL': 0.0, 'GF': 0.60, 'FF': 4.00, 'roof': 7.40, 'parapet': 8.40, 'stair_penthouse_roof': 10.25, 'future_2nd_floor': 10.80},
                'emprise': [0, 0, W, H], 'site': S, 'niveaux': niveaux, 'recalage_facades': rap,
                'registre_materiaux': registre_materiaux(), 'exigences': EXIGENCES}
    ecrire_registre(maquette['registre_materiaux'])
    json.dump(maquette, open(os.path.join(HERE, 'maquette.json'), 'w'), indent=1, ensure_ascii=False)
    with open(os.path.join(HERE, 'CORRECTIONS.md'), 'w') as f:
        f.write('# Journal des corrections (maquette v1 / PDF d\'origine)\n\nGénéré par `construire_maquette.py`. Unité : le mètre.\n\n')
        f.write('| Réf. | Nature | Modification | Motif |\n|---|---|---|---|\n')
        for r, t, q, p in JOURNAL:
            f.write('| %s | %s | %s | %s |\n' % (r, t, q, p))
    print('recalage façades', rap)
    print(len(JOURNAL), 'corrections journalisées')
    for n, M in niveaux.items():
        av = [o['id'] for o in M['ouvertures'] if o.get('a_verifier')]
        print(n, 'ouvertures', len(M['ouvertures']), 'sans hauteur :', av)


if __name__ == '__main__':
    main()
