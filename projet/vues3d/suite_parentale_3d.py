"""MBAO - suite parentale R+1, indice F : 4 vues 3D schématiques (+ vue de dessus) pour le passage IA du client.

python3 -I projet/vues3d/suite_parentale_3d.py [V1 V2 ...] [--apercu]      (Blender 'bpy', processeur seul, aucun téléchargement)
La scène est construite DIRECTEMENT depuis la géométrie du plan indice F (suite_parentale_r1_v5.py) : aucune dérive possible avec le 2D.
Repère = celui du plan : x vers l'est, y vers le nord, z vers le haut, mètres ; origine = angle intérieur sud-ouest de la zone.
Caméras : flèches dessinées par le client sur le plan (03/11) ; hauteur d'oeil 1.60.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'esquisse'))
import bpy, mathutils
import suite_parentale_r1_v5 as V

W, D, H = V.W, V.D, 3.00                                # hauteur sous plafond choisie 3.00 (à confirmer : poutres C4 2.80 / B14 2.75 au plan de coffrage)
XC0, XC1 = 4.06, 4.21                                   # cloison centrale
LINT = V.LINTEAU                                        # 2.20
APERCU = '--apercu' in sys.argv

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---------------------------------------------------------------- matières
def mat(nom, couleur=(0.8, 0.8, 0.8), rug=0.5, metal=0.0, emis=None, alpha=None, nodes=None):
    m = bpy.data.materials.new(nom); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*couleur, 1); b.inputs['Roughness'].default_value = rug; b.inputs['Metallic'].default_value = metal
    if emis: b.inputs['Emission Color'].default_value = (*emis[0], 1); b.inputs['Emission Strength'].default_value = emis[1]
    if alpha is not None: b.inputs['Alpha'].default_value = alpha
    if nodes: nodes(nt, b)
    return m

def tex_bois(nt, b):                                    # noyer foncé veiné (marron foncé des références du client)
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 14, 1)
    no = nt.nodes.new('ShaderNodeTexNoise'); no.inputs['Scale'].default_value = 6; no.inputs['Detail'].default_value = 8
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.10, 0.045, 0.02, 1); cr.color_ramp.elements[1].color = (0.24, 0.12, 0.055, 1)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], no.inputs['Vector'])
    nt.links.new(no.outputs['Fac'], cr.inputs['Fac']); nt.links.new(cr.outputs['Color'], b.inputs['Base Color'])

def tex_carreau(nt, b):                                 # grand carreau clair 0.80 x 0.80, joint fin
    tc = nt.nodes.new('ShaderNodeTexCoord'); br = nt.nodes.new('ShaderNodeTexBrick'); br.offset = 0.0; br.inputs['Scale'].default_value = 1.0
    br.inputs['Color1'].default_value = (0.86, 0.85, 0.82, 1); br.inputs['Color2'].default_value = (0.82, 0.81, 0.78, 1); br.inputs['Mortar'].default_value = (0.5, 0.5, 0.48, 1)
    br.inputs['Mortar Size'].default_value = 0.004; br.inputs['Brick Width'].default_value = 0.8; br.inputs['Row Height'].default_value = 0.8
    nt.links.new(tc.outputs['Object'], br.inputs['Vector']); nt.links.new(br.outputs['Color'], b.inputs['Base Color'])

M = dict(
    mur=mat('mur_blanc', (0.82, 0.82, 0.80), 0.9), plafond=mat('plafond', (0.95, 0.95, 0.95), 0.9),
    sol=mat('carreau', rug=0.18, nodes=tex_carreau), bois=mat('noyer', (0.17, 0.08, 0.04), 0.35, nodes=tex_bois),
    noir=mat('alu_noir', (0.015, 0.015, 0.015), 0.35, 0.8), noirbrillant=mat('verre_noir', (0.01, 0.01, 0.012), 0.05),
    verre=mat('verre', (0.5, 0.55, 0.55), 0.03, alpha=0.14), verre_fume=mat('verre_fume', (0.04, 0.04, 0.045), 0.03, alpha=0.35),
    led=mat('led', (1, 0.75, 0.4), 0.5, emis=((1.0, 0.72, 0.38), 3)), spot=mat('spot', (1, 1, 1), 0.5, emis=((1, 0.95, 0.85), 8)),
    blanc=mat('blanc', (0.9, 0.9, 0.9), 0.5), tissu=mat('tissu', (0.78, 0.76, 0.72), 0.95), tissu_gris=mat('tissu_gris', (0.35, 0.36, 0.38), 0.95),
    ceram=mat('ceramique', (0.95, 0.95, 0.95), 0.1), chrome=mat('chrome', (0.8, 0.8, 0.8), 0.15, 1.0), exterieur=mat('ext', (0.55, 0.62, 0.55), 0.9),
    ecran=mat('ecran', (0.005, 0.005, 0.008), 0.08), faience=mat('faience', (0.78, 0.8, 0.8), 0.15),
)

def box(x0, y0, z0, x1, y1, z1, m, nom='b'):
    bpy.ops.mesh.primitive_cube_add(location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)); o = bpy.context.active_object
    o.scale = (abs(x1 - x0) / 2, abs(y1 - y0) / 2, abs(z1 - z0) / 2); o.name = nom; o.data.materials.append(M[m]); return o

def cyl(x, y, z0, z1, r, m, nom='c'):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=z1 - z0, location=(x, y, (z0 + z1) / 2)); o = bpy.context.active_object; o.name = nom; o.data.materials.append(M[m]); return o

def mur_x(y0, y1, ouv, x0=-0.15, x1=None, m='mur'):     # mur le long de x avec ouvertures (xa, xb, za, zb)
    x1 = W + 0.15 if x1 is None else x1; xs = x0
    for xa, xb, za, zb in sorted(ouv):
        box(xs, y0, 0, xa, y1, H, m, 'mur') if xa > xs else None
        if za > 0: box(xa, y0, 0, xb, y1, za, m, 'allege')
        if zb < H: box(xa, y0, zb, xb, y1, H, m, 'linteau')
        xs = xb
    box(xs, y0, 0, x1, y1, H, m, 'mur')

def mur_y(x0, x1, ouv, y0=0, y1=None, m='mur'):         # mur le long de y avec ouvertures (ya, yb, za, zb)
    y1 = D if y1 is None else y1; ys = y0
    for ya, yb, za, zb in sorted(ouv):
        box(x0, ys, 0, x1, ya, H, m, 'mur') if ya > ys else None
        if za > 0: box(x0, ya, 0, x1, yb, za, m, 'allege')
        if zb < H: box(x0, ya, zb, x1, yb, H, m, 'linteau')
        ys = yb
    box(x0, ys, 0, x1, y1, H, m, 'mur')

# ---------------------------------------------------------------- enveloppe
box(-0.15, -0.15, -0.2, W + 0.15, D + 0.15, 0, 'sol', 'sol')
box(0, 0, H, W, D, H + 0.2, 'plafond', 'plafond')
FEN = [(*V.FEN_CH[:2], V.FEN_CH[2], V.FEN_CH[2] + V.FEN_CH[3]), (2.405, 4.025, 0, LINT), (4.245, 5.865, V.FEN_DR[2], V.FEN_DR[2] + V.FEN_DR[3]), (*V.FEN_SDB[:2], V.FEN_SDB[2], V.FEN_SDB[2] + V.FEN_SDB[3])]
mur_x(-0.15, 0, FEN)                                                                                 # façade sud
mur_x(D, D + 0.15, [(0.175, 0.962, 0, LINT)])                                                       # mur nord, porte d'entrée de la suite (porte NE fermée)
box(-0.15, -0.15, 0, 0, D + 0.15, H, 'mur', 'mur ouest'); box(W, -0.15, 0, W + 0.15, D + 0.15, H, 'mur', 'mur est')
mur_y(XC0, XC1, [(*V.OUV_S, 0, LINT), (*V.OUV_N, 0, LINT)])                                          # cloison centrale + deux ouvertures de 2.20
box(V.XM, 0, 0, V.XE_M, 1.58, H, 'mur', 'mur SDB'); box(V.XM, 1.58, LINT, V.XE_M, V.SDB_Y, H, 'mur', 'linteau porte SDB')
box(V.XM, V.SDB_Y, 0, W, V.SDB_Y + 0.15, H, 'mur', 'cloison nord SDB')
# vitrages et menuiseries de façade
for xa, xb, za, zb in FEN:
    box(xa, -0.10, za, xb, -0.08, zb, 'verre', 'vitrage')
    for (a, b_, c, d_) in ((xa, xb, za, za + 0.05), (xa, xb, zb - 0.05, zb), (xa, xa + 0.05, za, zb), (xb - 0.05, xb, za, zb)): box(a, -0.12, c, b_, -0.06, d_, 'noir', 'cadre')
box(3.215 - 0.025, -0.12, 0, 3.215 + 0.025, -0.06, LINT, 'noir', 'montant coulissant')           # porte-fenêtre coulissante 2 vantaux
box(5.055 - 0.025, -0.12, V.FEN_DR[2], 5.055 + 0.025, -0.06, LINT, 'noir', 'montant dressing')
box(-0.15, -1.60, -0.2, W + 0.15, -0.15, 0, 'exterieur', 'terrasse')                                  # balcon / extérieur (vu par les baies)
# porte d'entrée (vantail ouvert contre le mur ouest) et porte de la SDB (vantail à plat contre le mur nord)
box(0.0, 4.92, 0, 0.04, 5.626, LINT, 'bois', 'vantail entrée')
box(V.XE_M, V.SDB_Y - 0.052, 0, V.XE_M + 0.80, V.SDB_Y - 0.018, LINT, 'blanc', 'vantail SDB')

# ---------------------------------------------------------------- chambre
for i in range(48):                                                                                   # lambris vertical noyer sur tout le mur ouest (mur de la TV)
    y = 0.02 + i * (D - 0.04) / 48; box(0, y, 0, 0.025, y + (D - 0.04) / 48 - 0.012, H, 'bois', 'lambris')
x, y, l, h = V.LIT[1:]
box(x, y, 0.0, x + l, y + h, 0.30, 'bois', 'base lit'); box(x, y, 0.30, x + l - 0.10, y + h, 0.50, 'blanc', 'matelas')
box(x + 0.35, y + 0.02, 0.50, x + l - 0.10, y + h - 0.02, 0.58, 'tissu', 'couette'); box(x + 0.80, y + 0.02, 0.50, x + l - 0.10, y + h - 0.02, 0.60, 'tissu', 'couette2')
for yy in (y + 0.12, y + h - 0.12 - 0.62): box(x + l - 0.55, yy, 0.50, x + l - 0.15, yy + 0.62, 0.68, 'blanc', 'oreiller')
# tête de lit capitonnée contre la cloison, côté chambre
box(XC0 - 0.06, y - 0.10, 0.35, XC0, y + h + 0.10, 1.35, 'tissu_gris', 'tete de lit')
for m_ in (V.CHEV_S, V.CHEV_N):
    box(m_[1], m_[2], 0.05, m_[1] + m_[3], m_[2] + m_[4], 0.50, 'bois', 'chevet'); box(m_[1] + 0.1, m_[2] + 0.1, 0.50, m_[1] + 0.2, m_[2] + 0.2, 0.52, 'spot', 'lampe')
x, y, l, h = V.TV[1:]
box(0.025, y, 0.35, 0.45, y + 1.40, 0.70, 'bois', 'meuble TV'); box(0.025, y + 0.05, 0.05, 0.25, y + 1.35, 0.35, 'noir', 'ombre')
box(0.035, y + 0.20, 0.95, 0.07, y + 1.20, 1.60, 'ecran', 'TV')
x, y, l, h = V.FAUT[1:]
box(x, y, 0.0, x + l, y + h, 0.40, 'tissu_gris', 'fauteuil assise'); box(x, y, 0.40, x + 0.18, y + h, 0.90, 'tissu_gris', 'dossier')
cyl(V.GUER[1] + 0.225, V.GUER[2] + 0.225, 0.0, 0.50, 0.225, 'bois', 'gueridon')
x, y, l, h = V.COMM[1:]
box(x, y, 0.0, x + l, y + h, 0.85, 'bois', 'commode'); box(x + 0.15, y + h - 0.10, 0.85, x + 0.45, y + h, 1.25, 'blanc', 'objet')

# ---------------------------------------------------------------- penderies en U (références du client : portes vitrées à cadre noir, intérieur noyer, LED) et îlot
HP = 2.40
def penderie(m_, face):                                  # face = côté ouvert : 'S' (U nord), 'W' (U est), 'N' (U sud)
    x, y, l, h = m_[1:]; ep = 0.02
    if face == 'S':   a0, a1 = x, x + l; fy = y
    elif face == 'W': a0, a1 = y, y + h; fx = x
    else:             a0, a1 = x, x + l; fy = y + h
    box(x, y, 0, x + l, y + h, 0.08, 'noir', 'socle'); box(x, y, HP - 0.02, x + l, y + h, HP, 'bois', 'dessus')
    # fond + côtés en noyer
    if face == 'S': box(x, y + h - ep, 0, x + l, y + h, HP, 'bois', 'fond')
    elif face == 'W': box(x + l - ep, y, 0, x + l, y + h, HP, 'bois', 'fond')
    else: box(x, y, 0, x + l, y + ep, HP, 'bois', 'fond')
    n = max(2, round((a1 - a0) / 0.55)); pas = (a1 - a0) / n
    for i in range(n + 1):
        a = a0 + i * pas
        if face == 'S': box(a - 0.01, fy, 0.08, a + 0.01, fy + 0.02, HP - 0.30, 'noir', 'montant'); box(a - 0.003, fy + 0.01, 0.08, a + 0.003, fy + 0.50, HP - 0.30, 'led', 'LED')
        elif face == 'W': box(fx, a - 0.01, 0.08, fx + 0.02, a + 0.01, HP - 0.30, 'noir', 'montant'); box(fx + 0.01, a - 0.003, 0.08, fx + 0.50, a + 0.003, HP - 0.30, 'led', 'LED')
        else: box(a - 0.01, fy - 0.02, 0.08, a + 0.01, fy, HP - 0.30, 'noir', 'montant'); box(a - 0.003, fy - 0.50, 0.08, a + 0.003, fy - 0.01, HP - 0.30, 'led', 'LED')
    for i in range(n):                                   # panneaux de verre fumé + traverses
        a = a0 + i * pas + 0.012; b_ = a0 + (i + 1) * pas - 0.012
        if face == 'S': box(a, fy - 0.005, 0.08, b_, fy + 0.005, HP - 0.30, 'verre', 'verre')
        elif face == 'W': box(fx - 0.005, a, 0.08, fx + 0.005, b_, HP - 0.30, 'verre', 'verre')
        else: box(a, fy - 0.005, 0.08, b_, fy + 0.005, HP - 0.30, 'verre', 'verre')
    # étagères et tringles (visibles à travers le verre)
    for z in (0.60, 1.15):
        if face == 'S': box(x, y + 0.02, z, x + l, y + h - 0.02, z + 0.025, 'bois', 'etagere')
        elif face == 'W': box(x + 0.02, y, z, x + l - 0.02, y + h, z + 0.025, 'bois', 'etagere')
        else: box(x, y + 0.02, z, x + l, y + h - 0.02, z + 0.025, 'bois', 'etagere')
    # bandeau haut fermé (noir mat) au-dessus des portes
    if face == 'S': box(x, fy - 0.01, HP - 0.30, x + l, fy + 0.03, HP - 0.02, 'noir', 'bandeau')
    elif face == 'W': box(fx - 0.01, y, HP - 0.30, fx + 0.03, y + h, HP - 0.02, 'noir', 'bandeau')
    else: box(x, fy - 0.03, HP - 0.30, x + l, fy + 0.01, HP - 0.02, 'noir', 'bandeau')
penderie(V.U_N, 'S'); penderie(V.U_E, 'W'); penderie(V.U_S, 'N')
# îlot bijoux et montres 0.60 x 1.20, h 1.05 : corps noyer à tiroirs, dessus verre noir, compartiments vitrés éclairés
x, y, l, h = V.ILOT[1:]
box(x, y, 0.0, x + l, y + h, 0.08, 'noir', 'socle ilot'); box(x, y, 0.08, x + l, y + h, 0.88, 'bois', 'corps ilot')
for k in range(4):                                       # 4 tiroirs en façade est (côté hall), poignées noires fines
    z0 = 0.12 + k * 0.19; box(x + l - 0.01, y + 0.05, z0, x + l + 0.015, y + h - 0.05, z0 + 0.17, 'bois', 'tiroir'); box(x + l + 0.015, y + 0.15, z0 + 0.15, x + l + 0.03, y + h - 0.15, z0 + 0.165, 'noir', 'poignee')
box(x - 0.005, y - 0.005, 0.88, x + l + 0.005, y + h + 0.005, 0.90, 'noir', 'cadre dessus')
box(x + 0.02, y + 0.02, 0.90, x + l - 0.02, y + h - 0.02, 1.05, 'verre', 'vitrine')
for k in range(1, 4): box(x + 0.01, y + k * h / 4 - 0.008, 0.90, x + l - 0.01, y + k * h / 4 + 0.008, 1.05, 'noir', 'cloison vitrine')
box(x + 0.03, y + 0.03, 0.905, x + l - 0.03, y + h - 0.03, 0.915, 'led', 'LED vitrine')
box(x - 0.005, y - 0.005, 1.05, x + l + 0.005, y + h + 0.005, 1.065, 'noir', 'couvercle')
# ---------------------------------------------------------------- salle de bain
x, y, l, h = V.VASQUE[1:]
box(x, y, 0.30, x + l, y + h, 0.85, 'bois', 'meuble vasque'); box(x - 0.005, y - 0.005, 0.85, x + l + 0.005, y + h + 0.005, 0.90, 'blanc', 'plan vasque')
for k in (0, 1): cyl(x + l / 2, y + h / 4 + k * h / 2, 0.88, 0.93, 0.19, 'ceram', 'vasque'); cyl(x + 0.08, y + h / 4 + k * h / 2, 0.90, 1.12, 0.012, 'chrome', 'robinet')
x, y, l, h = V.DOUCHE[1:]
box(x, y, 0.0, x + l, y + h, 0.02, 'blanc', 'receveur'); box(x, y + h - 0.01, 0, x + l - 0.0, y + h + 0.01, 2.0, 'verre', 'paroi vitree'); box(x, y + h - 0.03, 2.0, x + l, y + h + 0.03, 2.03, 'noir', 'profil')
cyl(x + l - 0.2, y + 0.12, 2.0, 2.2, 0.012, 'chrome', 'bras'); cyl(x + l - 0.2, y + 0.12, 2.18, 2.2, 0.10, 'chrome', 'pomme')
x, y, l, h = V.WC[1:]
box(x + 0.30, y, 0.0, x + 0.55, y + h, 0.95, 'ceram', 'bati WC'); box(x, y + 0.02, 0.35, x + 0.40, y + h - 0.02, 0.45, 'ceram', 'cuvette')

# ---------------------------------------------------------------- lumière : spots encastrés + éclairage doux (aperçu fidèle à une soirée-lumière du jour)
for (sx, sy) in [(1.0, 1.2), (1.0, 4.2), (2.6, 2.8), (3.3, 1.2), (3.3, 4.4), (5.0, 1.3), (5.0, 2.8), (5.0, 4.4), (6.9, 3.8), (7.0, 1.2), (6.3, 4.5)]:
    cyl(sx, sy, H - 0.005, H, 0.05, 'spot', 'spot')
def lumiere(nom, pos, taille, w):
    bpy.ops.object.light_add(type='AREA', location=pos); o = bpy.context.active_object; o.name = nom; o.data.energy = w; o.data.size = taille; o.rotation_euler = (math.pi, 0, 0)
lumiere('L1', (2.0, 2.8, H - 0.05), 3.5, 90); lumiere('L2', (5.2, 2.8, H - 0.05), 3.0, 80); lumiere('L3', (7.0, 3.8, H - 0.05), 2.0, 50); lumiere('L4', (3.0, 5.0, H - 0.05), 2.5, 35)
w = bpy.data.worlds.new('ciel'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.75, 0.85, 1.0, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.8

# ---------------------------------------------------------------- caméras : flèches du client lues sur l'image (px -> m : x = (px-105)/98.6 ; y = (613-py)/98.0)
CAMS = {
    'V1': ((0.55, 5.00), (0.70, -0.72), 'Entrée de la chambre vers le lit et la cloison centrale'),
    'V2': ((4.95, 5.08), (1.00, -0.57), 'Dressing, du côté de l\'ouverture nord vers la penderie est'),
    'V3': ((5.25, 3.00), (-0.25, -0.97), 'Dressing vers la façade : fenêtre, double vasque, ouverture sud'),
    'V4': ((0.30, 0.39), (1.00, 0.43), 'Chambre, du coin façade vers le lit et la cloison'),
    'V6': ((3.40, 2.60), (-1.00, 0.0), 'Bonus : chambre vers le mur de la TV (lambris), le fauteuil et la commode'),
    'V5': ((6.00, 2.90), (-0.80, 0.55), 'Bonus : dressing vers l\'îlot, l\'ouverture nord et la penderie'),
}
def camera(nom, pos, d, f=22.0):
    bpy.ops.object.camera_add(); c = bpy.context.active_object; c.name = nom; c.data.lens = f; c.data.clip_start = 0.05
    c.location = (pos[0], pos[1], 1.60); v = mathutils.Vector((d[0], d[1], -0.05)).normalized()
    c.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler(); return c

sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 24 if APERCU else 48; sc.cycles.use_denoising = True; sc.cycles.max_bounces = 6
sc.cycles.use_adaptive_sampling = True; sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = -0.3
sc.render.resolution_x, sc.render.resolution_y = (500, 700) if APERCU else (900, 1260); sc.render.image_settings.file_format = 'PNG'

if __name__ == '__main__':
    vues = [a for a in sys.argv[1:] if a in CAMS or a == 'PLAN'] or list(CAMS)
    out = os.path.join(HERE, 'rendus' + ('_apercu' if APERCU else '')); os.makedirs(out, exist_ok=True)
    for nom in vues:
        if nom == 'PLAN':                                # vue de dessus orthographique (confrontation avec le plan 2D)
            plafond = bpy.data.objects['plafond']; plafond.hide_render = True
            bpy.ops.object.camera_add(location=(W / 2, D / 2, 12)); c = bpy.context.active_object; c.data.type = 'ORTHO'; c.data.ortho_scale = 9.0
            sc.render.resolution_x, sc.render.resolution_y = 900, 700
            for o in bpy.data.objects:
                if o.name.startswith(('spot', 'poutre')): o.hide_render = True
        else:
            (p, d, _) = CAMS[nom]; c = camera(nom, p, d)
        sc.camera = c; sc.render.filepath = os.path.join(out, 'MBAO_suite_%s.png' % nom); bpy.ops.render.render(write_still=True); print('OK', nom)
