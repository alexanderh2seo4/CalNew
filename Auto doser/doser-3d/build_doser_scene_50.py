# Builds the 50-ingredient version of the per-line perfume doser (Perfume-Doser-Feasibility.md, §7):
# 7 modules x 8 slots arranged as an octagon around the balance, front side left open for access.
# Each module: 8 valves on its own manifold, 8 mixed bottles closed by their own caps with septa, one braided
# sleeve carrying its 8 FEP lines to the central nozzle head. Real scale, metres.
# Rebuilds the "Perfume Doser 50" scene on every run and leaves all other scenes alone.
import math

import bmesh
import bpy
from mathutils import Vector

SCENE = "Perfume Doser 50"
N_MODULES, SLOTS = 7, 8
N_INGREDIENTS = 50
PITCH = 0.052
SIDE = SLOTS * PITCH + 0.024                       # octagon side = module length
APOTHEM = SIDE / (2 * math.tan(math.pi / 8))       # centre -> bottle row
BASE_Z, MODULE_TOP = 0.02, 0.03                    # base plate top, module plate top
MANIFOLD_LY, MANIFOLD_Z = 0.10, 0.19
COMB_LY, COMB_Z = -0.05, 0.27
TIP_Z = 0.195
# (kind, body radius, body height, neck outer radius, neck height, vessel)
CATALOG = [("30 mL dropper", 0.016, 0.065, 0.009, 0.012, "amber"),
           ("50 mL Boston round", 0.0195, 0.075, 0.0105, 0.012, "amber"),
           ("100 mL Boston round", 0.024, 0.095, 0.012, 0.013, "amber"),
           ("15 mL dropper", 0.0125, 0.05, 0.009, 0.011, "amber"),
           ("100 mL alu flask", 0.022, 0.095, 0.011, 0.012, "alu"),
           ("50 mL clear flask", 0.02, 0.07, 0.0105, 0.012, "clear"),
           ("30 mL Boston round", 0.0165, 0.068, 0.0095, 0.012, "amber"),
           ("50 mL GL25 lab bottle", 0.021, 0.06, 0.0145, 0.014, "clear")]
PALETTE = [(0.95, 0.80, 0.35), (0.75, 0.90, 0.55), (0.98, 0.65, 0.30), (0.85, 0.85, 0.80),
           (0.95, 0.55, 0.45), (0.70, 0.80, 0.95), (0.90, 0.75, 0.55), (0.80, 0.60, 0.85)]
MAX_LIQUID = MODULE_TOP + max(b[2] for b in CATALOG)
assert TIP_Z > MAX_LIQUID + 0.03, "nozzle tips must sit above the tallest bottle's liquid level (siphon)"


def module_angle(m):
    return -math.pi / 2 + math.pi / 4 * (m + 1)     # octagon sides 1..7; side 0 (front) stays open


def W(m, lx, ly, z):
    """Module-local (lx along the module, ly outward from the centre) -> world."""
    a = module_angle(m)
    t = Vector((-math.sin(a), math.cos(a), 0))
    n = Vector((math.cos(a), math.sin(a), 0))
    return n * APOTHEM + t * lx + n * ly + Vector((0, 0, z))


def polar(radius, angle, z):
    return Vector((radius * math.cos(angle), radius * math.sin(angle), z))


def rand(i, salt=0.0):
    return (math.sin(i * 12.9898 + salt * 78.233) * 43758.5453) % 1.0


# ------------------------------------------------------------------ scene + helpers

if SCENE in bpy.data.scenes:
    old = bpy.data.scenes[SCENE]
    for ob in list(old.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.scenes.remove(old)
for block in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.lights,
              bpy.data.cameras, bpy.data.worlds):
    for item in list(block):
        if item.users == 0:
            block.remove(item)

scene = bpy.data.scenes.new(SCENE)
for window in bpy.context.window_manager.windows:
    window.scene = scene
root = scene.collection

_mats = {}


def mat(name, color, metallic=0.0, rough=0.5, alpha=1.0, emission=0.0):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new("doser50_" + name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    values = {"Base Color": (*color, 1.0), "Metallic": metallic, "Roughness": rough, "Alpha": alpha}
    if emission:
        values.update({"Emission Color": (*color, 1.0), "Emission Strength": emission})
    for key, value in values.items():
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = value
    m.diffuse_color = (*color, alpha)
    if alpha < 1.0 and hasattr(m, "surface_render_method"):
        m.surface_render_method = "BLENDED"
    _mats[name] = m
    return m


def link(ob, material):
    if material is not None:
        ob.data.materials.append(material)
    root.objects.link(ob)
    return ob


def _smooth_sides(me):
    for poly in me.polygons:
        poly.use_smooth = len(poly.vertices) == 4


def box(name, size, loc, material, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location, ob.rotation_euler = loc, rot
    return link(ob, material)


def cyl(name, r, h, loc, material, rot=(0, 0, 0), caps=True, segments=32, r2=None):
    """Cylinder whose base sits at loc (grows along local +Z)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=segments,
                          radius1=r, radius2=r if r2 is None else r2, depth=h)
    bmesh.ops.translate(bm, vec=Vector((0, 0, h / 2)), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    _smooth_sides(me)
    ob = bpy.data.objects.new(name, me)
    ob.location, ob.rotation_euler = loc, rot
    return link(ob, material)


def shell(name, r, h, loc, material, thickness=0.0015):
    ob = cyl(name, r, h, loc, material, caps=False, segments=64)
    mod = ob.modifiers.new("wall", "SOLIDIFY")
    mod.thickness = thickness
    return ob


def tube(name, points, radius, material, resolution=10):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    cu.resolution_u = resolution
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    ob = bpy.data.objects.new(name, cu)
    return link(ob, material)


def helix(center, radius, height, turns, steps_per_turn=10):
    n = turns * steps_per_turn
    return [Vector((center.x + radius * math.cos(2 * math.pi * i / steps_per_turn),
                    center.y + radius * math.sin(2 * math.pi * i / steps_per_turn),
                    center.z + height * i / n)) for i in range(n + 1)]


# Bottle closure (feasibility note §3): each bottle's own screw cap, two Ø 2 mm holes 5 mm apart, liner
# replaced by a PTFE/silicone septum (PTFE face down). Both FEP tubes are pushed through the septum;
# the cap's own thread holds the seal, so there is no hold-down hardware.
BORE_OFF = 0.0025            # tubes 5 mm apart so the two punctures cannot tear into one
CAP_STYLES = {"amber": (0.08, 0.08, 0.09), "clear": (0.92, 0.92, 0.90), "alu": (0.78, 0.66, 0.32)}


def septum_cap(tag, center, lip_z, neck_r, neck_h, along, vessel, segments=32):
    """Put the bottle's own cap (with septum) on a neck. Returns (top_z, air_port, liq_port)."""
    cap_r = neck_r + 0.0018
    cap_h = min(neck_h, 0.014) + 0.003
    top_z = lip_z + 0.003
    cyl("Cap " + tag, cap_r, cap_h, Vector((center.x, center.y, top_z - cap_h)),
        mat("cap_" + vessel, CAP_STYLES[vessel], rough=0.45), segments=segments)
    air = Vector((center.x, center.y, top_z)) - along * BORE_OFF
    liq = Vector((center.x, center.y, top_z)) + along * BORE_OFF
    for port, side in ((air, "air"), (liq, "liquid")):   # silicone visible only in the two Ø 2 mm cap holes
        cyl("Septum %s %s" % (side, tag), 0.001, 0.0002, port,
            mat("septum_silicone", (0.85, 0.25, 0.25), rough=0.7), segments=16)
    return top_z, air, liq


labels = []


def label(text, loc, size=0.022, material=None):
    cu = bpy.data.curves.new("lbl", "FONT")
    cu.body = text
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.extrude = 0.0003
    ob = bpy.data.objects.new("Label: " + text.split("\n")[0][:40], cu)
    ob.location = loc
    link(ob, material or mat("label", (0.05, 0.05, 0.07), rough=0.9))
    labels.append(ob)
    return ob


# ------------------------------------------------------------------ materials

alu = mat("aluminium", (0.62, 0.64, 0.67), metallic=1.0, rough=0.35)
anod = mat("anodised", (0.10, 0.10, 0.12), metallic=0.6, rough=0.4)
steel = mat("steel", (0.8, 0.8, 0.82), metallic=1.0, rough=0.2)
vessels = {"amber": mat("amber_glass", (0.55, 0.25, 0.05), rough=0.05, alpha=0.55),
           "clear": mat("clear_glass", (0.92, 0.96, 1.0), rough=0.02, alpha=0.25),
           "alu": mat("alu_bottle", (0.70, 0.72, 0.74), metallic=1.0, rough=0.3, alpha=0.5)}
glass = mat("shield_glass", (0.92, 0.96, 1.0), rough=0.02, alpha=0.18)
ptfe = mat("ptfe", (0.96, 0.96, 0.94), rough=0.45)
fep = mat("fep", (0.92, 0.95, 0.95), rough=0.15, alpha=0.6)
pu_blue = mat("pu_air", (0.10, 0.35, 0.85), rough=0.4)
coil_black = mat("coil", (0.03, 0.03, 0.03), rough=0.5)
valve_body = mat("valve_body", (0.75, 0.72, 0.68), metallic=0.7, rough=0.3)
check_orange = mat("check_valve", (0.95, 0.45, 0.08), rough=0.4)
pcb = mat("pcb", (0.05, 0.35, 0.15), rough=0.5)
plastic_dark = mat("plastic_dark", (0.12, 0.12, 0.13), rough=0.5)
plastic_white = mat("plastic_white", (0.88, 0.88, 0.86), rough=0.4)
brass = mat("brass", (0.80, 0.62, 0.25), metallic=1.0, rough=0.3)
sleeve = mat("braided_sleeve", (0.18, 0.19, 0.22), metallic=0.3, rough=0.45)
bus = mat("bus_cable", (0.12, 0.12, 0.13), rough=0.6)
lcd = mat("lcd", (0.3, 0.9, 0.5), emission=2.0)
module_plate = mat("module_plate", (0.80, 0.81, 0.83), rough=0.5)

# ------------------------------------------------------------------ base

base = cyl("Base (octagon)", APOTHEM / math.cos(math.pi / 8) + 0.20, BASE_Z, (0, 0, 0), anod,
           rot=(0, 0, math.pi / 8), segments=8)
for poly in base.data.polygons:
    poly.use_smooth = False

# ------------------------------------------------------------------ modules

slot = 0
for m in range(N_MODULES):
    a = module_angle(m)
    rot = (0, 0, a + math.pi / 2)
    box("M%d plate" % (m + 1), (SIDE - 0.01, 0.24, MODULE_TOP - BASE_Z),
        W(m, 0, 0.04, (BASE_Z + MODULE_TOP) / 2), module_plate, rot)
    box("M%d manifold" % (m + 1), (SIDE - 0.03, 0.02, 0.018), W(m, 0, MANIFOLD_LY, MANIFOLD_Z), alu, rot)
    for lx in (-SIDE / 2 + 0.03, SIDE / 2 - 0.03):
        box("M%d manifold post" % (m + 1), (0.012, 0.012, MANIFOLD_Z - MODULE_TOP),
            W(m, lx, MANIFOLD_LY + 0.016, (MANIFOLD_Z + MODULE_TOP) / 2), alu, rot)
    box("M%d line comb" % (m + 1), (0.06, 0.016, 0.016), W(m, 0, COMB_LY, COMB_Z), ptfe, rot)
    box("M%d comb post" % (m + 1), (0.008, 0.008, COMB_Z - MODULE_TOP),
        W(m, 0, COMB_LY, (COMB_Z + MODULE_TOP) / 2), alu, rot)
    box("M%d driver board" % (m + 1), (0.10, 0.03, 0.004), W(m, 0, 0.145, MODULE_TOP + 0.002), pcb, rot)

    for j in range(SLOTS):
        lx = (j - (SLOTS - 1) / 2) * PITCH
        tag = "M%d-%d" % (m + 1, j + 1)
        # valve chain on the manifold: check valve -> 3/2 solenoid
        cyl("Check valve " + tag, 0.0045, 0.008, W(m, lx, MANIFOLD_LY, MANIFOLD_Z + 0.009), check_orange)
        box("3/2 valve " + tag, (0.014, 0.018, 0.013), W(m, lx, MANIFOLD_LY, MANIFOLD_Z + 0.023), valve_body, rot)
        cyl("Valve coil " + tag, 0.007, 0.02, W(m, lx, MANIFOLD_LY, MANIFOLD_Z + 0.029), coil_black)

        post = W(m, lx, 0.045, MODULE_TOP)
        if slot >= N_INGREDIENTS:                      # spare slot: hold-down post only
            cyl("Free slot " + tag, 0.02, 0.001, W(m, lx, 0, MODULE_TOP), mat("free_slot", (0.55, 0.57, 0.62), rough=0.6),
                segments=24)
            slot += 1
            continue

        kind, br, bh, nr, nh, vessel = CATALOG[int(rand(slot) * len(CATALOG))]
        color = PALETTE[slot % len(PALETTE)]
        p = W(m, lx, 0, MODULE_TOP)
        shoulder_h = (br - nr) * 0.5
        lip_z = MODULE_TOP + bh + shoulder_h + nh
        cyl("Bottle %s (%s)" % (tag, kind), br, bh, p, vessels[vessel], segments=28)
        cyl("Shoulder " + tag, br, shoulder_h, p + Vector((0, 0, bh)), vessels[vessel], r2=nr, caps=False,
            segments=28)
        cyl("Neck " + tag, nr, nh, p + Vector((0, 0, bh + shoulder_h)), vessels[vessel], segments=20)
        cyl("Liquid " + tag, br - 0.0025, bh * (0.25 + 0.65 * rand(slot, 1.0)), p + Vector((0, 0, 0.002)),
            mat("liquid_%d" % (slot % len(PALETTE)), color, rough=0.1, alpha=0.8), segments=28)

        along = W(m, 1, 0, 0) - W(m, 0, 0, 0)
        top_z, air_port, liq_port = septum_cap(tag, p, lip_z, nr, nh, along, vessel, segments=24)
        cyl("Dip tube " + tag, 0.0008, top_z - (MODULE_TOP + 0.004),
            Vector((liq_port.x, liq_port.y, MODULE_TOP + 0.004)), fep, segments=10)

        # air: valve -> adapter (PE/FEP near the bottle)
        tube("Air line " + tag, [W(m, lx - 0.003, MANIFOLD_LY - 0.01, MANIFOLD_Z + 0.022),
                                 W(m, lx - 0.006, 0.04, MANIFOLD_Z - 0.01),
                                 air_port + Vector((0, 0, 0.004)), air_port], 0.0009,
             mat("fep_air", (0.45, 0.68, 0.95), rough=0.2, alpha=0.9), 8)
        # liquid: adapter -> module comb (continues inside the module's braided sleeve)
        tube("FEP line " + tag, [liq_port,
                                 W(m, lx + 0.0012, -0.01, top_z + 0.05),
                                 W(m, lx * 0.35, COMB_LY + 0.005, COMB_Z),
                                 W(m, lx * 0.08, COMB_LY, COMB_Z)], 0.0009,
             mat("fep_line_%d" % (slot % len(PALETTE)), color, rough=0.2, alpha=0.9), 8)
        slot += 1

    # braided sleeve: comb -> nozzle head
    tube("M%d braided sleeve (8 FEP lines)" % (m + 1),
         [W(m, 0, COMB_LY - 0.01, COMB_Z),
          polar(APOTHEM - 0.16, a, COMB_Z + 0.05),
          polar(0.12, a, 0.31),
          polar(0.03, a, 0.27),
          polar(0.014, a, 0.252)], 0.0065, sleeve, 16)

# ------------------------------------------------------------------ air bus + module bus (daisy chain)

for m in range(N_MODULES - 1):
    a_mid = (module_angle(m) + module_angle(m + 1)) / 2
    tube("Air bus M%d-M%d" % (m + 1, m + 2),
         [W(m, SIDE / 2 - 0.015, MANIFOLD_LY, MANIFOLD_Z),
          polar(APOTHEM / math.cos(math.pi / 8) + 0.08, a_mid, MANIFOLD_Z),
          W(m + 1, -SIDE / 2 + 0.015, MANIFOLD_LY, MANIFOLD_Z)], 0.002, pu_blue)
    tube("Module bus M%d-M%d (I2C + 12 V)" % (m + 1, m + 2),
         [W(m, SIDE / 2 - 0.05, 0.15, MODULE_TOP + 0.004),
          polar(APOTHEM / math.cos(math.pi / 8) + 0.12, a_mid, MODULE_TOP + 0.003),
          W(m + 1, -SIDE / 2 + 0.05, 0.15, MODULE_TOP + 0.004)], 0.0022, bus)

# ------------------------------------------------------------------ air supply + electronics (front gap)

res_at = Vector((-0.14, -0.50, BASE_Z))
cyl("Air reservoir", 0.03, 0.10, res_at, alu)
cyl("Relief valve", 0.006, 0.018, res_at + Vector((0.008, 0, 0.10)), brass)
box("Pressure sensor", (0.018, 0.012, 0.004), res_at + Vector((-0.01, 0, 0.102)), pcb)
pump_at = Vector((-0.14, -0.62, BASE_Z))
box("Diaphragm pump", (0.06, 0.045, 0.04), pump_at + Vector((0, 0, 0.02)), plastic_dark)
cyl("Pump motor", 0.016, 0.035, pump_at + Vector((0.03, 0, 0.02)), steel, rot=(0, math.pi / 2, 0))
tube("Air: pump to reservoir", [pump_at + Vector((0, 0.022, 0.03)), res_at + Vector((0, -0.05, 0.07)),
                                res_at + Vector((0, -0.02, 0.10))], 0.002, pu_blue)
tube("Air: reservoir to M7", [res_at + Vector((-0.008, 0, 0.10)), Vector((-0.20, -0.45, 0.17)),
                              W(N_MODULES - 1, SIDE / 2 - 0.015, MANIFOLD_LY, MANIFOLD_Z)], 0.002, pu_blue)

ctrl = Vector((0.14, -0.52, BASE_Z))
box("Controller enclosure", (0.10, 0.075, 0.025), ctrl + Vector((0, 0, 0.0125)), plastic_dark)
box("ESP32 + MAX3232", (0.085, 0.06, 0.003), ctrl + Vector((0, 0, 0.0265)), pcb)
box("12 V PSU", (0.09, 0.06, 0.035), (0.14, -0.64, BASE_Z + 0.0175), alu)
tube("Module bus to M1", [ctrl + Vector((0.05, 0.02, 0.015)), Vector((0.26, -0.42, MODULE_TOP)),
                          W(0, -SIDE / 2 + 0.05, 0.15, MODULE_TOP + 0.004)], 0.0022, bus)

# ------------------------------------------------------------------ balance, vial, nozzle head

box("Balance housing", (0.17, 0.20, 0.06), (0, -0.02, BASE_Z + 0.03), plastic_white)
box("Balance display", (0.07, 0.002, 0.018), (0, -0.121, BASE_Z + 0.035), lcd)
cyl("Weighing pan", 0.05, 0.004, (0, 0, BASE_Z + 0.06), steel, segments=48)
shell("Draft shield", 0.07, 0.10, (0, 0, BASE_Z + 0.064), glass)
shell("Target vial", 0.016, 0.085, (0, 0, BASE_Z + 0.064), glass, 0.0012)
cyl("Formula in vial", 0.0145, 0.025, (0, 0, BASE_Z + 0.0656), mat("formula", (0.95, 0.78, 0.40), rough=0.1,
                                                                     alpha=0.85))
tube("Balance RS232", [Vector((0.06, -0.10, BASE_Z + 0.02)), Vector((0.10, -0.35, BASE_Z + 0.01)),
                       ctrl + Vector((-0.05, 0.02, 0.015))], 0.0018, bus)

cyl("Nozzle head (56-hole plate)", 0.024, 0.042, (0, 0, TIP_Z + 0.015), ptfe, segments=48)
hexes = []
for q in range(-4, 5):
    for r in range(-4, 5):
        x = 0.0024 * (q + r / 2)
        y = 0.0024 * (r * math.sqrt(3) / 2)
        if math.hypot(x, y) < 0.0195:
            hexes.append((math.hypot(x, y), x, y))
hexes.sort()
for k, (_, x, y) in enumerate(hexes[:N_MODULES * SLOTS]):
    if k < N_INGREDIENTS:
        cyl("Nozzle tip %02d" % (k + 1), 0.0007, 0.015, (x, y, TIP_Z), steel, segments=8)
post_a = math.radians(67.5)
post_at = polar(0.24, post_a, BASE_Z)
box("Head post", (0.016, 0.016, 0.36), (post_at.x, post_at.y, BASE_Z + 0.18), alu)
arm_mid = post_at / 2
box("Head arm", (0.24, 0.014, 0.014), (arm_mid.x, arm_mid.y, 0.385), alu, (0, 0, post_a))
cyl("Head hanger", 0.005, 0.385 - (TIP_Z + 0.057), (0, 0, TIP_Z + 0.057), alu, segments=16)
box("Shutter servo", (0.023, 0.012, 0.022), polar(0.05, math.radians(-20), TIP_Z - 0.01), mat(
    "servo", (0.1, 0.25, 0.75), rough=0.5))
cyl("Drip shutter (open)", 0.026, 0.0015, polar(0.04, math.radians(-40), TIP_Z - 0.006), ptfe, segments=32)

# ------------------------------------------------------------------ labels

for m in range(N_MODULES):
    label("M%d" % (m + 1), W(m, 0, 0.20, MODULE_TOP + 0.02), 0.03)
label("50 ingredients = 7 modules x 8 slots\n(6 spare slots in M7)", polar(0.95, math.radians(100), 0.45), 0.03)
label("Module: own manifold + 8 valves,\n8 septum caps, 1 braided sleeve", W(2, 0, 0.25, 0.32), 0.022)
label("Braided sleeves: 8 FEP lines each\n-> nozzle head (no tube mess)", polar(0.42, math.radians(150), 0.46),
      0.022)
label("Nozzle head: 56-hole plate,\ntips in ~22 mm circle,\nabove the tallest liquid level", polar(0.35, math.radians(-160), 0.33),
      0.02)
label("Balance 0.01 g + draft shield\nopen front for access", Vector((0.0, -0.30, 0.20)), 0.022)
label("Air bus + module bus (I2C, 12 V)\ndaisy-chained around the outside",
      polar(APOTHEM + 0.30, math.radians(-10), 0.10), 0.022)
label("Pump -> reservoir\n+ pressure sensor", Vector((-0.32, -0.66, 0.10)), 0.02)
label("ESP32 + MAX3232 + 12 V PSU", Vector((0.32, -0.70, 0.08)), 0.02)
label("Mixed bottles, each with its own cap\n+ PTFE/silicone septum (no hold-down)",
      polar(APOTHEM + 0.22, math.radians(-60), 0.20), 0.02)

# ------------------------------------------------------------------ camera, lights, world

cam_data = bpy.data.cameras.new("Render camera")
cam_data.lens = 37
cam_data.clip_start = 0.01
cam = bpy.data.objects.new("Render camera", cam_data)
cam.location = (1.35, -1.75, 1.45)
root.objects.link(cam)
look = bpy.data.objects.new("Camera target", None)
look.location = (0.0, 0.0, 0.10)
root.objects.link(look)
c = cam.constraints.new("TRACK_TO")
c.target, c.track_axis, c.up_axis = look, "TRACK_NEGATIVE_Z", "UP_Y"
scene.camera = cam

for ob in labels:
    to_cam = cam.location - ob.location
    dist = to_cam.length
    pull = 0.30
    ob.location = ob.location + to_cam.normalized() * pull
    ob.data.size *= (dist - pull) / dist
    lines = ob.data.body.split("\n")
    size = ob.data.size
    card = box("Label card", (max(len(l) for l in lines) * size * 0.52 + size,
                              len(lines) * size * 1.2 + size * 0.5, 0.0005), (0, 0, -0.0012),
               mat("label_card", (0.97, 0.97, 0.95), rough=0.9, emission=0.35))
    card.parent = ob
    t = ob.constraints.new("TRACK_TO")
    t.target, t.track_axis, t.up_axis = cam, "TRACK_Z", "UP_Y"

for name, energy, size, loc in (("Key", 120, 1.5, (1.2, -1.2, 1.8)), ("Fill", 40, 2.0, (-1.6, -0.6, 1.2)),
                                ("Rim", 50, 1.5, (-0.4, 1.8, 1.4))):
    light = bpy.data.lights.new(name, "AREA")
    light.energy, light.size = energy, size
    lob = bpy.data.objects.new(name + " light", light)
    lob.location = loc
    root.objects.link(lob)
    lt = lob.constraints.new("TRACK_TO")
    lt.target, lt.track_axis, lt.up_axis = look, "TRACK_NEGATIVE_Z", "UP_Y"

world = bpy.data.worlds.new("Doser 50 world")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.72, 0.74, 0.78, 1.0)
bg.inputs["Strength"].default_value = 0.35
scene.world = world

box("Floor", (10, 10, 0.001), (0, 0, -0.0006), mat("floor", (0.80, 0.80, 0.82), rough=0.8))

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
if hasattr(scene.eevee, "use_raytracing"):
    scene.eevee.use_raytracing = False
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"

for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type == "VIEW_3D":
            space = area.spaces.active
            space.clip_start = 0.001
            space.shading.type = "MATERIAL"
            space.region_3d.view_perspective = "CAMERA"

result = "built %d objects in '%s': %d ingredients, apothem %.3f m, max liquid %.3f m, tips %.3f m" % (
    len(scene.objects), SCENE, N_INGREDIENTS, APOTHEM, MAX_LIQUID, TIP_Z)
