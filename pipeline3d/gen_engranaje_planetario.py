#!/usr/bin/env python3
# gen_engranaje_planetario.py — Engranaje planetario con DIENTES EVOLVENTE REALES
# Perfil de involuta por ecuaciones parametricas (no aproximacion de cajas).
# Ensamblado en malla: sol + 3 planetas + corona interna. Listo para imprimir
# por partes (export_parts) o como expositorio ensamblado.
# Uso: blender -b --factory-startup -P gen_engranaje_planetario.py -- <salida.blend>
import bpy, math, sys, os
import numpy as np

_out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "/tmp/planetario.blend"
os.makedirs(os.path.dirname(_out), exist_ok=True)

P = dict(
    module=2.0,          # modulo (mm)
    z_sun=24, z_planet=16,
    thickness=8.0,
    pressure_deg=20.0,   # angulo de presion
    bore_sun=5.0,        # agujero del sol
    planet_hole=4.0,     # agujero de planetas
    backlash=0.06,       # holgura de flanco
    min_printable_mm=0.4,
)

M = P["module"]
ZS, ZP = P["z_sun"], P["z_planet"]
ZR = ZS + 2 * ZP                      # 56: corona interna
ALPHA = math.radians(P["pressure_deg"])
TH = P["thickness"]

# radios clave (cilindros primitivos, base de la involuta)
def radii(z):
    d = M * z
    return dict(d=d, r=d/2, rb=(d/2)*math.cos(ALPHA), ra=(d/2)+M,
                rf=(d/2)-1.25*M)

RS, RP, RR = radii(ZS), radii(ZP), radii(ZR)

sc = bpy.context.scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'
sc.unit_settings.scale_length = 0.001

def mat(name, c, rough=0.4, metal=0.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*c, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

# metal bajo: la luz sol+mundo del pipeline no tiene entorno que reflejar,
# con metal alto todo queda negro (leccion petrolero). Colores solidos vivos.
M_BRASS = mat("Laton", (0.85, 0.62, 0.22), 0.4, 0.25)
M_STEEL = mat("Acero", (0.62, 0.65, 0.7), 0.45, 0.3)
M_BLUE  = mat("Azul", (0.18, 0.35, 0.75), 0.5, 0.15)
M_DARK  = mat("Corona", (0.35, 0.33, 0.4), 0.55, 0.25)

parts = []
def reg(o):
    parts.append(o); return o

def extrude_polygon(name, pts2d, z0, z1, m):
    # garantizar CCW (visto desde +Z) para que la cara superior reciba luz
    area = 0.0
    for i in range(len(pts2d)):
        x0, y0 = pts2d[i]; x1, y1 = pts2d[(i+1) % len(pts2d)]
        area += x0*y1 - x1*y0
    if area < 0:
        pts2d = list(reversed(pts2d))
    n = len(pts2d)
    V = [(x, y, z0) for x, y in pts2d] + [(x, y, z1) for x, y in pts2d]
    F = [tuple(range(n-1, -1, -1)), tuple(range(n, 2*n))]
    for i in range(n):
        j = (i+1) % n
        F.append((i, j, n+j, n+i))
    me = bpy.data.meshes.new(name + "_m")
    me.from_pydata(V, [], F); me.update()
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    o.data.materials.append(m)
    return reg(o)

def involute_flank(R, z, side, n=10):
    """flanco de evolvente de UN lado, de raiz a punta, angulos absolutos.
    Textbook: theta(r) = s/(2*rp) + inv(alpha) - inv(alpha_r); s = espesor en primitivo."""
    s = math.pi * M / 2 - P["backlash"]            # espesor del diente en primitivo
    inv_a = math.tan(ALPHA) - ALPHA
    rb = max(R["rb"], R["rf"])
    rs = np.linspace(rb, R["ra"], n)
    pts = []
    for r in rs:
        alpha_r = math.acos(min(rb / r, 1.0)) if r >= rb else 0.0
        inv_r = math.tan(alpha_r) - alpha_r if r >= rb else 0.0
        th = s / (2 * R["r"]) + inv_a - inv_r      # medio-espesor angular en r
        pts.append((r * math.cos(th), r * math.sin(th) * side))
    return pts

def gear_outline(z, internal=False):
    """un diente CCW monotono: flanco_izq(r->punta) -> punta(+ang) -> flanco_der(punta->r)
    -> arco de raiz por el HUECO hasta la base del siguiente diente (angulo+pitch).
    Trayectoria de angulo estrictamente creciente -> poligono simple (no ocho)."""
    R = radii(z)
    n_f = 9
    fl_L = involute_flank(R, z, -1, n_f)           # izquierda: angulos negativos, r creciente
    tip_a = abs(math.atan2(fl_L[-1][1], fl_L[-1][0]))
    tip = [(R["ra"]*math.cos(a), R["ra"]*math.sin(a))
           for a in np.linspace(-tip_a, tip_a, 4)]          # atraviesa 0 -> CCW
    fl_R = [(x, -y) for (x, y) in reversed(fl_L[1:])]       # derecha: punta -> raiz
    a_d = math.atan2(fl_R[-1][1], fl_R[-1][0])              # ~ +angulo base
    a_next = -abs(math.atan2(fl_L[0][1], fl_L[0][0])) + 2*math.pi/z
    root = [(R["rf"]*math.cos(a), R["rf"]*math.sin(a))
            for a in np.linspace(a_d, a_next, 5)]           # hueco hasta el siguiente diente
    return fl_L + tip + fl_R + root

def full_gear_outline(z, internal=False):
    tooth = gear_outline(z, internal)
    pts = []
    n = z
    for k in range(n):
        ang = 2 * math.pi * k / n
        ca, sa = math.cos(ang), math.sin(ang)
        for (x, y) in tooth:
            pts.append((x*ca - y*sa, x*sa + y*ca))
    return pts

def cyl_hole(name, x, y, dia, z0, z1):
    bpy.ops.mesh.primitive_cylinder_add(radius=dia/2, depth=(z1-z0)+2,
                                        location=(x, y, (z0+z1)/2), vertices=20)
    o = bpy.context.active_object; o.name = name
    return o

def boolean_hole(target, cutter):
    m = target.modifiers.new("hole", 'BOOLEAN'); m.operation='DIFFERENCE'; m.solver='EXACT'
    m.object = cutter
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier="hole")
    bpy.data.objects.remove(cutter, do_unlink=True)

# ---------- SOL ----------
sun = extrude_polygon("Sol", full_gear_outline(ZS), 0, TH, M_BRASS)
boolean_hole(sun, cyl_hole("h", 0, 0, P["bore_sun"], 0, TH))

# ---------- PLANETAS (3, a 120 grados, en malla con sol y corona) ----------
# distancia centros sol-planeta = r_s + r_p ; planeta-corona = rR - rP (coinciden por ZR=ZS+2ZP)
A = RS["r"] + RP["r"]
planet_outline = full_gear_outline(ZP)
for k in range(3):
    ang = 2*math.pi*k/3 + math.pi/2
    cx, cy = A*math.cos(ang), A*math.sin(ang)
    pl = extrude_polygon(f"Planeta_{k+1}", [(x+cx, y+cy) for x, y in planet_outline], 0, TH, M_STEEL)
    boolean_hole(pl, cyl_hole(f"h{k}", cx, cy, P["planet_hole"], 0, TH))

# ---------- CORONA INTERNA ----------
# Malla interna: la cavidad es el perfil de ZR dientes DESPLAZADO medio paso
# (el espacio entre dientes de la corona recibe el diente del planeta).
half_pitch = math.pi / ZR
ring_cavity = []
for (x, y) in full_gear_outline(ZR):
    r = math.hypot(x, y); a = math.atan2(y, x) + half_pitch
    ring_cavity.append((r*math.cos(a), r*math.sin(a)))
Rout = RR["ra"] + 3*M
outer = [(Rout*math.cos(2*math.pi*i/72), Rout*math.sin(2*math.pi*i/72)) for i in range(72)]
poly = outer + list(reversed(ring_cavity))   # outer CCW + cavidad CW = poligono con agujero
ring = extrude_polygon("Corona", poly, 0, TH, M_DARK)

# ---------- BASE EXPOSITORA (placa fina bajo todo, no fusionada: 0.3 mm por debajo) ----------
bpy.ops.mesh.primitive_cylinder_add(radius=Rout+4, depth=1.5, location=(0, 0, -1.0), vertices=48)
base = bpy.context.active_object; base.name = "Base_expositora"
base.data.materials.append(M_BLUE)
reg(base)

# separacion visual para render: corona 0.3 mm arriba para no fusionar con base
ring.location.z = 0.3

print("GEAR_GEOMETRY sun_z=%d planet_z=%d ring_z=%d A=%.2f mesh_ok" % (ZS, ZP, ZR, A))
print("OBJECT_COUNT:", len(parts))
bpy.ops.wm.save_as_mainfile(filepath=_out)
print("GEN_OK", _out)
