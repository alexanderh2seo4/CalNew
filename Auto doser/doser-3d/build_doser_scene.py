# Builds the perfume auto-doser concept (Perfume-Doser-Feasibility.md) as a Blender scene.
# Real scale, metres. Rebuilds the "Perfume Doser" scene from scratch on every run and
# leaves all other scenes alone. Run inside Blender (via the Claude Blender Bridge MCP).
import math

import bmesh
import bpy
from mathutils import Vector

SCENE = "Perfume Doser"
N_LINES = 8
PITCH = 0.06
BOTTLE_Y = 0.08
TOP = 0.02                      # base plate top
# Mixed bottles, each closed by its own cap with a septum:
# (kind, body radius, body height, neck outer radius, neck height, glass material key, old size class)
BOTTLES = [("30 mL dropper DIN 18", 0.016, 0.065, 0.009, 0.012, "amber", "S"),
           ("50 mL Boston round", 0.0195, 0.075, 0.0105, 0.012, "amber", "M"),
           ("100 mL Boston round", 0.024, 0.095, 0.012, 0.013, "amber", "M"),
           ("50 mL clear flask", 0.02, 0.07, 0.0105, 0.012, "clear", "M"),
           ("15 mL dropper", 0.0125, 0.05, 0.009, 0.011, "amber", "S"),
           ("100 mL supplier alu bottle", 0.022, 0.10, 0.011, 0.012, "alu", "M"),
           ("GL45 lab bottle 100 mL", 0.028, 0.072, 0.0225, 0.016, "clear", "XL"),
           ("30 mL Boston round", 0.0165, 0.068, 0.0095, 0.012, "amber", "S")]
MAX_LIQUID = TOP + max(b[2] for b in BOTTLES)   # tallest shoulder = highest possible liquid level
TIP_Z = 0.175                   # nozzle tips, must stay above MAX_LIQUID (no siphon)
CLUSTER = Vector((0.0, -0.07, 0.205))
MANIFOLD_Y, MANIFOLD_Z = 0.17, 0.26
LIQUID_COLORS = [(0.95, 0.80, 0.35), (0.75, 0.90, 0.55), (0.98, 0.65, 0.30), (0.85, 0.85, 0.80),
                 (0.95, 0.55, 0.45), (0.70, 0.80, 0.95), (0.90, 0.75, 0.55), (0.80, 0.60, 0.85)]
LIQUID_FILL = [0.085, 0.06, 0.075, 0.04, 0.07, 0.05, 0.08, 0.065]


# ------------------------------------------------------------------ scene + helpers

if SCENE in bpy.data.scenes:
    old = bpy.data.scenes[SCENE]
    for ob in list(old.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.scenes.remove(old)
for block in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
    for item in list(block):
        if item.users == 0:
            block.remove(item)

scene = bpy.data.scenes.new(SCENE)
for window in bpy.context.window_manager.windows:
    window.scene = scene
root = scene.collection

_mats = {}


def mat(name, color, metallic=0.0, rough=0.5, transmission=0.0, alpha=1.0, ior=1.45, emission=0.0):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new("doser_" + name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    values = {"Base Color": (*color, 1.0), "Metallic": metallic, "Roughness": rough,
              "Alpha": alpha, "IOR": ior}
    if emission:
        values.update({"Emission Color": (*color, 1.0), "Emission Strength": emission})
    for key, value in values.items():
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = value
    m.diffuse_color = (*color, alpha)
    if alpha < 1.0 or transmission > 0:
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = "BLENDED" if alpha < 1.0 else "DITHERED"
        if hasattr(m, "use_screen_refraction"):
            m.use_screen_refraction = False
    _mats[name] = m
    return m


def link(ob, material, parent=None):
    if material is not None:
        ob.data.materials.append(material)
    root.objects.link(ob)
    if parent is not None:
        ob.parent = parent
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


def cyl(name, r, h, loc, material, rot=(0, 0, 0), caps=True, segments=40, r2=None):
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


def tube(name, points, radius, material, resolution=12):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 4
    cu.use_fill_caps = True
    cu.resolution_u = resolution
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    ob = bpy.data.objects.new(name, cu)
    return link(ob, material)


def helix(center, radius, height, turns, steps_per_turn=12):
    pts = []
    n = turns * steps_per_turn
    for i in range(n + 1):
        a = 2 * math.pi * i / steps_per_turn
        pts.append(Vector((center.x + radius * math.cos(a), center.y + radius * math.sin(a),
                           center.z + height * i / n)))
    return pts


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


def label(text, loc, size=0.013, material=None):
    cu = bpy.data.curves.new("lbl", "FONT")
    cu.body = text
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.extrude = 0.0002
    ob = bpy.data.objects.new("Label: " + text.split("\n")[0][:40], cu)
    ob.location = loc
    link(ob, material or mat("label", (0.05, 0.05, 0.07), rough=0.9))
    labels.append(ob)
    return ob


def leader(a, b):
    tube("leader", [Vector(a), Vector(b)], 0.0003, mat("leader", (0.15, 0.15, 0.18), rough=0.9), 2)


# ------------------------------------------------------------------ materials

alu = mat("aluminium", (0.62, 0.64, 0.67), metallic=1.0, rough=0.35)
anod = mat("anodised", (0.10, 0.10, 0.12), metallic=0.6, rough=0.4)
steel = mat("steel", (0.8, 0.8, 0.82), metallic=1.0, rough=0.2)
amber = mat("amber_glass", (0.55, 0.25, 0.05), rough=0.05, transmission=1.0, alpha=0.55, ior=1.5)
glass = mat("clear_glass", (0.92, 0.96, 1.0), rough=0.02, transmission=1.0, alpha=0.18, ior=1.5)
ptfe = mat("ptfe", (0.96, 0.96, 0.94), rough=0.45)
fep = mat("fep", (0.92, 0.95, 0.95), rough=0.15, transmission=0.6, alpha=0.6)
pp_cap = mat("pp_cap", (0.93, 0.93, 0.93), rough=0.6)
pu_blue = mat("pu_air", (0.10, 0.35, 0.85), rough=0.4)
coil_black = mat("coil", (0.03, 0.03, 0.03), rough=0.5)
valve_body = mat("valve_body", (0.75, 0.72, 0.68), metallic=0.7, rough=0.3)
check_orange = mat("check_valve", (0.95, 0.45, 0.08), rough=0.4)
pcb = mat("pcb", (0.05, 0.35, 0.15), rough=0.5)
plastic_dark = mat("plastic_dark", (0.12, 0.12, 0.13), rough=0.5)
plastic_white = mat("plastic_white", (0.88, 0.88, 0.86), rough=0.4)
brass = mat("brass", (0.80, 0.62, 0.25), metallic=1.0, rough=0.3)
danger = mat("siphon_plane", (0.95, 0.15, 0.10), rough=0.8, alpha=0.18)
lcd = mat("lcd", (0.3, 0.9, 0.5), emission=2.0)
ghost = mat("ghost", (0.45, 0.55, 0.75), rough=0.6, alpha=0.22)

# ------------------------------------------------------------------ base + frame

box("Base plate", (0.70, 0.42, 0.02), (0, 0, 0.01), anod)
for x in (-0.30, 0.30):
    box("Frame upright", (0.02, 0.02, 0.30), (x, MANIFOLD_Y + 0.02, TOP + 0.15), alu)
box("Frame crossbar", (0.62, 0.02, 0.02), (0, MANIFOLD_Y + 0.02, 0.31), alu)

# ------------------------------------------------------------------ air supply (left)

pump = box("Diaphragm pump", (0.06, 0.045, 0.04), (-0.29, -0.11, TOP + 0.02), plastic_dark)
cyl("Pump motor", 0.016, 0.035, (-0.29, -0.11 - 0.0225, TOP + 0.02), steel, rot=(math.pi / 2, 0, 0))
cyl("Air reservoir", 0.03, 0.11, (-0.29, 0.0, TOP), alu)
cyl("Relief valve", 0.006, 0.018, (-0.282, 0.0, TOP + 0.11), brass)
box("Pressure sensor", (0.018, 0.012, 0.004), (-0.298, 0.0, TOP + 0.113), pcb)
tube("Air: pump to reservoir", [Vector((-0.29, -0.09, TOP + 0.04)), Vector((-0.29, -0.05, TOP + 0.07)),
                                Vector((-0.29, -0.02, TOP + 0.11))], 0.002, pu_blue)
tube("Air: reservoir to manifold", [Vector((-0.29, 0.0, TOP + 0.125)), Vector((-0.29, 0.06, 0.22)),
                                    Vector((-0.27, MANIFOLD_Y, MANIFOLD_Z))], 0.002, pu_blue)

# ------------------------------------------------------------------ manifold + valves

box("Pressure manifold", (0.52, 0.022, 0.018), (0, MANIFOLD_Y, MANIFOLD_Z), alu)
box("Manifold hanger L", (0.01, 0.01, 0.04), (-0.24, MANIFOLD_Y + 0.012, 0.29), alu)
box("Manifold hanger R", (0.01, 0.01, 0.04), (0.24, MANIFOLD_Y + 0.012, 0.29), alu)

bottle_xs = [(i - (N_LINES - 1) / 2) * PITCH for i in range(N_LINES)]
tip_targets = []
for i, x in enumerate(bottle_xs):
    # check valve -> 3/2 solenoid on top of the manifold
    cyl("Check valve %d" % (i + 1), 0.005, 0.008, (x, MANIFOLD_Y, MANIFOLD_Z + 0.009), check_orange)
    box("3/2 valve body %d" % (i + 1), (0.016, 0.02, 0.014), (x, MANIFOLD_Y, MANIFOLD_Z + 0.024), valve_body)
    cyl("Valve coil %d" % (i + 1), 0.008, 0.022, (x, MANIFOLD_Y, MANIFOLD_Z + 0.031), coil_black)
    box("Valve plug %d" % (i + 1), (0.012, 0.01, 0.008), (x, MANIFOLD_Y + 0.006, MANIFOLD_Z + 0.057), plastic_dark)
    # exhaust diffusion coil behind the valve
    tube("Exhaust diffusion coil %d" % (i + 1),
         helix(Vector((x, MANIFOLD_Y - 0.004, MANIFOLD_Z + 0.03)), 0.0045, 0.035, 4), 0.0009,
         mat("exhaust", (0.55, 0.55, 0.58), rough=0.5), 6)

    # bottle (any kind) with the universal cone adapter in its neck
    kind, br, bh, nr, nh, glass_key, size = BOTTLES[i]
    vessel = {"amber": amber, "clear": glass, "alu": mat("alu_bottle", (0.70, 0.72, 0.74), metallic=1.0,
                                                          rough=0.3, alpha=0.45)}[glass_key]
    base = Vector((x, BOTTLE_Y, TOP))
    shoulder_h = (br - nr) * 0.5
    lip_z = TOP + bh + shoulder_h + nh
    cyl("Bottle %d (%s)" % (i + 1, kind), br, bh, base, vessel, segments=48)
    cyl("Bottle shoulder %d" % (i + 1), br, shoulder_h, base + Vector((0, 0, bh)), vessel, r2=nr, caps=False)
    cyl("Bottle neck %d" % (i + 1), nr, nh, base + Vector((0, 0, bh + shoulder_h)), vessel)
    cyl("Liquid %d" % (i + 1), br - 0.0025, LIQUID_FILL[i] * bh / 0.10, base + Vector((0, 0, 0.003)),
        mat("liquid_%d" % i, LIQUID_COLORS[i], rough=0.1, transmission=0.5, alpha=0.8))

    top_z, air_port, liq_port = septum_cap(str(i + 1), Vector((x, BOTTLE_Y, 0)), lip_z, nr, nh,
                                           Vector((1, 0, 0)), glass_key)
    cyl("Dip tube %d" % (i + 1), 0.0008, top_z - (TOP + 0.004), Vector((liq_port.x, BOTTLE_Y, TOP + 0.004)),
        fep, segments=12)

    # air line: valve outlet -> adapter air port
    tube("Air line %d" % (i + 1), [Vector((x - 0.004, MANIFOLD_Y - 0.011, MANIFOLD_Z + 0.024)),
                                   Vector((x - 0.006, (MANIFOLD_Y + BOTTLE_Y) / 2, 0.215)),
                                   air_port + Vector((0, 0, 0.004)), air_port], 0.0009,
         mat("fep_air", (0.45, 0.68, 0.95), rough=0.2, alpha=0.9))

    # FEP liquid line: adapter -> nozzle cluster (rises above everything, then drops in)
    ang = 2 * math.pi * i / N_LINES
    entry = CLUSTER + Vector((0.010 * math.cos(ang), 0.010 * math.sin(ang), 0.0125))
    tube("FEP liquid line %d" % (i + 1),
         [liq_port,
          liq_port + Vector((0, -0.01, 0.07)),
          Vector((x * 0.45, 0.0, 0.25)),
          entry + Vector((0, 0, 0.02)),
          entry], 0.0011, mat("fep_line_%d" % i, LIQUID_COLORS[i], rough=0.2, transmission=0.4, alpha=0.85))
    tip_targets.append((ang, i))

# ------------------------------------------------------------------ nozzle cluster, shutter, arm

cyl("Nozzle cluster (PTFE)", 0.017, 0.025, CLUSTER - Vector((0, 0, 0.0125)), ptfe)
for ang, i in tip_targets:
    p = CLUSTER + Vector((0.008 * math.cos(ang), 0.008 * math.sin(ang), -0.0125))
    cyl("Nozzle tip %d" % (i + 1), 0.0007, p.z - TIP_Z, Vector((p.x, p.y, TIP_Z)), steel, segments=12)
box("Arm post", (0.012, 0.012, 0.22), (0.11, CLUSTER.y, TOP + 0.11), alu)
box("Arm", (0.09, 0.01, 0.008), (0.065, CLUSTER.y, CLUSTER.z), alu)
box("Shutter servo", (0.023, 0.012, 0.022), (0.094, CLUSTER.y - 0.012, TIP_Z - 0.003), mat("servo", (0.1, 0.25, 0.75), rough=0.5))
shutter = cyl("Drip shutter (open)", 0.02, 0.0015, (0.045, CLUSTER.y - 0.012, TIP_Z - 0.006), ptfe)

# ------------------------------------------------------------------ balance, draft shield, vial

box("Balance housing", (0.17, 0.20, 0.06), (0, CLUSTER.y - 0.005, TOP + 0.03), plastic_white)
box("Balance display", (0.07, 0.002, 0.018), (0, CLUSTER.y - 0.106, TOP + 0.035), lcd)
cyl("Weighing pan", 0.05, 0.004, (0, CLUSTER.y, TOP + 0.06), steel)
shell("Draft shield", 0.07, 0.075, (0, CLUSTER.y, TOP + 0.064), glass, 0.0015)
shell("Target vial", 0.013, 0.055, (0, CLUSTER.y, TOP + 0.064), glass, 0.0012)
cyl("Vial bottom", 0.013, 0.0015, (0, CLUSTER.y, TOP + 0.064), glass)
cyl("Formula in vial", 0.0115, 0.012, (0, CLUSTER.y, TOP + 0.0656),
    mat("formula", (0.95, 0.78, 0.40), rough=0.1, transmission=0.5, alpha=0.85))

# ------------------------------------------------------------------ electronics (right front)

box("12 V PSU", (0.09, 0.06, 0.035), (0.27, 0.0, TOP + 0.0175), alu)
box("Controller enclosure", (0.10, 0.075, 0.025), (0.26, -0.13, TOP + 0.0125), plastic_dark)
box("ESP32 + 8-ch valve driver", (0.085, 0.06, 0.003), (0.26, -0.13, TOP + 0.0265), pcb)
for k in range(8):
    box("MOSFET %d" % k, (0.005, 0.004, 0.003), (0.228 + k * 0.009, -0.112, TOP + 0.0295), plastic_dark)
tube("Valve bus (I2C + 12 V)", [Vector((0.26, -0.10, TOP + 0.03)), Vector((0.29, 0.05, 0.12)),
                                Vector((0.27, MANIFOLD_Y, MANIFOLD_Z + 0.04)),
                                Vector((0.22, MANIFOLD_Y + 0.006, MANIFOLD_Z + 0.06))], 0.0025, plastic_dark)
tube("Balance RS232", [Vector((0.085, CLUSTER.y, TOP + 0.02)), Vector((0.16, -0.12, TOP + 0.01)),
                       Vector((0.21, -0.13, TOP + 0.02))], 0.0018, plastic_dark)

# ------------------------------------------------------------------ "no siphon" level

plane = box("Max liquid level (siphon limit)", (0.52, 0.07, 0.0004), (0, BOTTLE_Y, MAX_LIQUID), danger)

# ------------------------------------------------------------------ module 2 (ghost)

box("Module 2 base (ghost)", (0.50, 0.42, 0.02), (0.61, 0, 0.01), ghost)
for i in range(N_LINES):
    x = 0.40 + i * PITCH * 0.6
    cyl("Module 2 bottle %d" % (i + 1), 0.016, 0.10, (x, BOTTLE_Y, TOP), ghost, segments=24)
box("Module 2 manifold (ghost)", (0.30, 0.02, 0.018), (0.61, MANIFOLD_Y, MANIFOLD_Z), ghost)
tube("Air bus to module 2", [Vector((0.26, MANIFOLD_Y, MANIFOLD_Z)), Vector((0.46, MANIFOLD_Y, MANIFOLD_Z))],
     0.002, pu_blue)

# ------------------------------------------------------------------ labels

label("Each bottle's own cap + PTFE/silicone septum:\n2 FEP tubes pushed through,\nno hold-down hardware",
      (0.44, 0.0, 0.24))
label("Tallest bottle's max liquid level\n< nozzle tips  ->  no siphon", (0.38, BOTTLE_Y, MAX_LIQUID - 0.025), 0.011,
      mat("label_red", (0.75, 0.08, 0.05), rough=0.9))
label("Pressure manifold + check valve + 3/2 solenoid per line\n(only air touches valves)",
      (0, MANIFOLD_Y, MANIFOLD_Z + 0.085))
label("Exhaust diffusion coils", (-0.40, MANIFOLD_Y, 0.30), 0.011)
label("FEP liquid lines (no valve in liquid path)", (-0.12, 0.0, 0.285), 0.011)
label("Nozzle cluster", (-0.075, CLUSTER.y - 0.02, CLUSTER.z + 0.01), 0.011)
label("Drip shutter (servo)", (0.13, CLUSTER.y - 0.05, TIP_Z + 0.02), 0.011)
label("Balance 0.01 g, RS232 -> ESP32 + draft shield\nclosed-loop gravimetric dosing (no camera)",
      (0, CLUSTER.y - 0.13, TOP + 0.07), 0.012)
label("Pump -> reservoir\n+ pressure sensor + relief valve", (-0.33, -0.17, TOP + 0.06), 0.011)
label("ESP32 + MAX3232 + 8-ch valve driver", (0.27, -0.20, TOP + 0.012), 0.011)
label("12 V PSU", (0.40, -0.05, TOP + 0.02), 0.011)
label("Module 2: +8 lines\n(plugs into air bus + I2C)", (0.61, 0.0, 0.16), 0.014)

# ------------------------------------------------------------------ camera, lights, world

cam_data = bpy.data.cameras.new("Render camera")
cam_data.lens = 44
cam_data.clip_start = 0.005
cam = bpy.data.objects.new("Render camera", cam_data)
cam.location = (0.95, -1.20, 0.78)
root.objects.link(cam)
look = bpy.data.objects.new("Camera target", None)
look.location = (0.21, 0.0, 0.12)
root.objects.link(look)
c = cam.constraints.new("TRACK_TO")
c.target, c.track_axis, c.up_axis = look, "TRACK_NEGATIVE_Z", "UP_Y"
scene.camera = cam

# pull labels toward the camera so geometry never hides them; rescale to keep apparent size
for ob in labels:
    to_cam = cam.location - ob.location
    dist = to_cam.length
    pull = 0.18
    ob.location = ob.location + to_cam.normalized() * pull
    ob.data.size *= (dist - pull) / dist
    lines = ob.data.body.split("\n")
    size = ob.data.size
    card = box("Label card", (max(len(l) for l in lines) * size * 0.52 + size,
                              len(lines) * size * 1.2 + size * 0.5, 0.0003), (0, 0, -0.0008),
               mat("label_card", (0.97, 0.97, 0.95), rough=0.9, emission=0.35))
    card.parent = ob
    t = ob.constraints.new("TRACK_TO")
    t.target, t.track_axis, t.up_axis = cam, "TRACK_Z", "UP_Y"

key = bpy.data.lights.new("Key", "AREA")
key.energy, key.size = 30, 0.8
key_ob = bpy.data.objects.new("Key light", key)
key_ob.location = (0.5, -0.6, 0.9)
root.objects.link(key_ob)
kt = key_ob.constraints.new("TRACK_TO")
kt.target, kt.track_axis, kt.up_axis = look, "TRACK_NEGATIVE_Z", "UP_Y"
fill = bpy.data.lights.new("Fill", "AREA")
fill.energy, fill.size = 10, 1.0
fill_ob = bpy.data.objects.new("Fill light", fill)
fill_ob.location = (-0.8, -0.3, 0.6)
root.objects.link(fill_ob)
ft = fill_ob.constraints.new("TRACK_TO")
ft.target, ft.track_axis, ft.up_axis = look, "TRACK_NEGATIVE_Z", "UP_Y"

world = bpy.data.worlds.new("Doser world")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.72, 0.74, 0.78, 1.0)
bg.inputs["Strength"].default_value = 0.35
scene.world = world

floor = box("Floor", (6, 6, 0.001), (0, 0, -0.0006), mat("floor", (0.80, 0.80, 0.82), rough=0.8))

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
if hasattr(scene.eevee, "use_raytracing"):
    scene.eevee.use_raytracing = False
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"

# viewport: look through the render camera in material preview
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type == "VIEW_3D":
            space = area.spaces.active
            space.clip_start = 0.001
            space.shading.type = "MATERIAL"
            space.region_3d.view_perspective = "CAMERA"

result = "built %d objects in scene '%s'; tips at %.3f m, max liquid %.3f m" % (
    len(scene.objects), SCENE, TIP_Z, MAX_LIQUID)
