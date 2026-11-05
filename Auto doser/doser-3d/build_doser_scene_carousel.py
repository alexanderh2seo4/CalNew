# Builds the carousel + docking perfume doser (Perfume-Doser-Feasibility.md) as a Blender scene.
# Real scale, metres. Rebuilds the "Perfume Doser" scene from scratch on every run and
# leaves all other scenes alone. Run inside Blender (via the Claude Blender Bridge MCP).
import math

import bmesh
import bpy
from mathutils import Vector

SCENE = "Perfume Doser"
N_BOTTLES = 48
TOP = 0.02                        # base plate top
C = Vector((0.0, 0.10, 0.0))      # carousel axis
DOCK_ANGLE = -math.pi / 2         # dock faces the front (-y)
DISC_R, DISC_Z = 0.29, 0.10       # turntable radius, underside height
BOTTLE_R, BOTTLE_RING = 0.017, 0.255
BODY_H = 0.075
BOTTLE_Z = DISC_Z + 0.01          # bottles stand on the disc
MAX_LIQUID = BOTTLE_Z + BODY_H    # bottle shoulder = highest possible liquid level
CAP_Z = BOTTLE_Z + BODY_H + 0.013
CAP_TOP = CAP_Z + 0.014
TIP_RING, TIP_Z = 0.335, 0.205    # gooseneck tips: outside the rim, above MAX_LIQUID
PALETTE = [(0.95, 0.80, 0.35), (0.75, 0.90, 0.55), (0.98, 0.65, 0.30), (0.85, 0.85, 0.80),
           (0.95, 0.55, 0.45), (0.70, 0.80, 0.95), (0.90, 0.75, 0.55), (0.80, 0.60, 0.85)]

assert TIP_Z > MAX_LIQUID + 0.01, "nozzle tips must sit above the max liquid level (siphon)"


def polar(radius, angle, z):
    return Vector((C.x + radius * math.cos(angle), C.y + radius * math.sin(angle), z))


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
    m = bpy.data.materials.new("doser_" + name)
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


def ring(name, r_in, r_out, z, h, a0, a1, material, segments=96, trough=False):
    """Annular sector around C from angle a0 to a1; trough=True leaves the top open (U profile)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rows = []
    for i in range(segments + 1):
        a = a0 + (a1 - a0) * i / segments
        rows.append([bm.verts.new(polar(r, a, zz)) for r, zz in
                     ((r_in, z), (r_out, z), (r_out, z + h), (r_in, z + h))])
    for i in range(segments):
        a, b = rows[i], rows[i + 1]
        bm.faces.new((a[0], b[0], b[1], a[1]))          # bottom
        bm.faces.new((a[1], b[1], b[2], a[2]))          # outer wall
        bm.faces.new((a[3], b[3], b[0], a[0]))          # inner wall
        if not trough:
            bm.faces.new((a[2], b[2], b[3], a[3]))      # top
    if abs(a1 - a0) < 2 * math.pi - 1e-6:
        bm.faces.new(rows[0][::-1])
        bm.faces.new(rows[-1])
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    link(ob, material)
    if trough:
        mod = ob.modifiers.new("wall", "SOLIDIFY")
        mod.thickness = 0.0015
    return ob


def tube(name, points, radius, material, resolution=12, cyclic=False):
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
    sp.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(name, cu)
    return link(ob, material)


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


# ------------------------------------------------------------------ materials

alu = mat("aluminium", (0.62, 0.64, 0.67), metallic=1.0, rough=0.35)
anod = mat("anodised", (0.10, 0.10, 0.12), metallic=0.6, rough=0.4)
steel = mat("steel", (0.8, 0.8, 0.82), metallic=1.0, rough=0.2)
amber = mat("amber_glass", (0.55, 0.25, 0.05), rough=0.05, alpha=0.55)
glass = mat("clear_glass", (0.92, 0.96, 1.0), rough=0.02, alpha=0.18)
ptfe = mat("ptfe", (0.96, 0.96, 0.94), rough=0.45)
fep = mat("fep", (0.92, 0.95, 0.95), rough=0.15, alpha=0.6)
pp_cap = mat("pp_cap", (0.93, 0.93, 0.93), rough=0.6)
hdpe = mat("turntable", (0.90, 0.90, 0.88), rough=0.55)
pu_blue = mat("pu_air", (0.10, 0.35, 0.85), rough=0.4)
coil_black = mat("coil", (0.03, 0.03, 0.03), rough=0.5)
valve_body = mat("valve_body", (0.75, 0.72, 0.68), metallic=0.7, rough=0.3)
fkm = mat("fkm_seal", (0.95, 0.45, 0.08), rough=0.5)
pcb = mat("pcb", (0.05, 0.35, 0.15), rough=0.5)
nfc = mat("nfc", (0.20, 0.45, 0.95), rough=0.4)
plastic_dark = mat("plastic_dark", (0.12, 0.12, 0.13), rough=0.5)
plastic_white = mat("plastic_white", (0.88, 0.88, 0.86), rough=0.4)
brass = mat("brass", (0.80, 0.62, 0.25), metallic=1.0, rough=0.3)
gutter_mat = mat("gutter", (0.55, 0.58, 0.62), rough=0.4)
lcd = mat("lcd", (0.3, 0.9, 0.5), emission=2.0)
magnet = mat("magnet", (0.85, 0.10, 0.10), rough=0.4)

# ------------------------------------------------------------------ base, pedestal, turntable, drive

box("Base plate", (0.82, 0.84, 0.02), (0, 0.02, 0.01), anod)
cyl("Pedestal", 0.11, DISC_Z - 0.012 - TOP, (C.x, C.y, TOP), alu)
ring("Lazy-susan bearing", 0.12, 0.15, DISC_Z - 0.012, 0.012, 0, 2 * math.pi, steel, segments=64)
cyl("Turntable", DISC_R, 0.01, (C.x, C.y, DISC_Z), hdpe, segments=128)
ring("Belt pulley ring", 0.105, 0.112, DISC_Z - 0.03, 0.018, 0, 2 * math.pi, coil_black, segments=64)
motor_at = polar(0.20, math.radians(55), TOP)
box("NEMA17 stepper", (0.042, 0.042, 0.04), motor_at + Vector((0, 0, 0.02)), coil_black)
cyl("Motor pulley", 0.008, 0.016, motor_at + Vector((0, 0, 0.04)), alu)
tube("GT2 belt", [motor_at + Vector((0.0, 0.010, DISC_Z - 0.021 - TOP)),
                  polar(0.11, math.radians(130), DISC_Z - 0.021),
                  polar(0.11, math.radians(240), DISC_Z - 0.021),
                  polar(0.11, math.radians(340), DISC_Z - 0.021),
                  motor_at + Vector((0.006, -0.008, DISC_Z - 0.021 - TOP))], 0.0025, coil_black, cyclic=True)
box("Hall sensor", (0.012, 0.008, 0.006), polar(DISC_R - 0.02, math.radians(200), DISC_Z - 0.018), pcb)
cyl("Homing magnet", 0.004, 0.003, polar(DISC_R - 0.02, math.radians(200), DISC_Z - 0.003), magnet)

# ------------------------------------------------------------------ bottles with dispensing caps

for i in range(N_BOTTLES):
    a = DOCK_ANGLE + 2 * math.pi * i / N_BOTTLES
    rot_z = a + math.pi / 2
    p = polar(BOTTLE_RING, a, BOTTLE_Z)
    color = PALETTE[i % len(PALETTE)]
    fill = 0.02 + 0.05 * (math.sin(i * 12.9898) * 43758.5453 % 1.0)

    cyl("Bottle %02d" % (i + 1), BOTTLE_R, BODY_H, p, amber, segments=32)
    cyl("Shoulder %02d" % (i + 1), BOTTLE_R, 0.009, p + Vector((0, 0, BODY_H)), amber, r2=0.0095,
        caps=False, segments=32)
    cyl("Neck %02d" % (i + 1), 0.0095, 0.004, p + Vector((0, 0, BODY_H + 0.009)), amber, segments=24)
    cyl("Liquid %02d" % (i + 1), BOTTLE_R - 0.002, fill, p + Vector((0, 0, 0.002)),
        mat("liquid_%d" % (i % len(PALETTE)), color, rough=0.1, alpha=0.8), segments=32)
    cyl("Dispensing cap %02d" % (i + 1), 0.0115, CAP_TOP - CAP_Z, Vector((p.x, p.y, CAP_Z)), pp_cap, segments=32)
    cyl("Air inlet seat %02d" % (i + 1), 0.0045, 0.004, Vector((p.x, p.y, CAP_TOP)), ptfe, r2=0.003, segments=24)
    cyl("NFC tag %02d" % (i + 1), 0.0095, 0.0006, Vector((p.x, p.y, CAP_TOP)), nfc, segments=32)
    dip = polar(BOTTLE_RING + 0.005, a, BOTTLE_Z + 0.003)
    cyl("Dip tube %02d" % (i + 1), 0.0013, CAP_TOP - dip.z, dip, fep, segments=12)
    tube("Gooseneck %02d" % (i + 1),
         [polar(BOTTLE_RING + 0.006, a, CAP_TOP),
          polar(BOTTLE_RING + 0.012, a, CAP_TOP + 0.009),
          polar(TIP_RING - 0.025, a, CAP_TOP + 0.010),
          polar(TIP_RING - 0.004, a, TIP_Z + 0.008),
          polar(TIP_RING, a, TIP_Z)], 0.0012,
         mat("gooseneck_%d" % (i % len(PALETTE)), color, rough=0.2, alpha=0.9), 8)

# ------------------------------------------------------------------ drip gutter (gap at the dock)

gap = math.radians(7)
gutter = ring("Drip gutter", TIP_RING - 0.018, TIP_RING + 0.014, TIP_Z - 0.022, 0.012,
              DOCK_ANGLE + gap, DOCK_ANGLE + 2 * math.pi - gap, gutter_mat, segments=144, trough=True)
for k in range(6):
    a = DOCK_ANGLE + math.radians(40 + k * 56)
    cyl("Gutter post %d" % k, 0.004, TIP_Z - 0.022 - TOP, polar(TIP_RING, a, TOP), alu, segments=12)

# ------------------------------------------------------------------ balance, draft shield, vial

dock_tip = polar(TIP_RING, DOCK_ANGLE, TIP_Z)
box("Balance housing", (0.15, 0.19, 0.06), (dock_tip.x, dock_tip.y - 0.025, TOP + 0.03), plastic_white)
box("Balance display", (0.07, 0.002, 0.018), (dock_tip.x, dock_tip.y - 0.121, TOP + 0.035), lcd)
cyl("Weighing pan", 0.045, 0.004, (dock_tip.x, dock_tip.y, TOP + 0.06), steel)
shell("Draft shield", 0.058, 0.09, (dock_tip.x, dock_tip.y, TOP + 0.064), glass, 0.0015)
shell("Target vial", 0.014, 0.09, (dock_tip.x, dock_tip.y, TOP + 0.064), glass, 0.0012)
cyl("Vial bottom", 0.014, 0.0015, (dock_tip.x, dock_tip.y, TOP + 0.064), glass)
cyl("Formula in vial", 0.0125, 0.02, (dock_tip.x, dock_tip.y, TOP + 0.0656),
    mat("formula", (0.95, 0.78, 0.40), rough=0.1, alpha=0.85))
cyl("Falling drop", 0.0016, 0.0032, (dock_tip.x, dock_tip.y, TIP_Z - 0.012), mat("liquid_0", PALETTE[0]),
    r2=0.0008, segments=16)

# ------------------------------------------------------------------ dock post, valve, docking head

dock_cap = polar(BOTTLE_RING, DOCK_ANGLE, CAP_TOP)
post = Vector((0.20, -0.26, 0))
box("Dock post", (0.02, 0.02, 0.32), (post.x, post.y, TOP + 0.16), alu)
arm_z = 0.33
arm_mid = (post + Vector((dock_cap.x, dock_cap.y, 0))) / 2
arm_vec = Vector((dock_cap.x - post.x, dock_cap.y - post.y, 0))
box("Dock arm", (arm_vec.length + 0.02, 0.016, 0.016), (arm_mid.x, arm_mid.y, arm_z), alu,
    rot=(0, 0, math.atan2(arm_vec.y, arm_vec.x)))
box("Linear actuator", (0.028, 0.028, 0.06), (dock_cap.x, dock_cap.y, arm_z - 0.035), coil_black)
cyl("Actuator rod", 0.003, 0.05, (dock_cap.x, dock_cap.y, CAP_TOP + 0.03), steel, segments=16)
cyl("Docking head", 0.009, 0.026, (dock_cap.x, dock_cap.y, CAP_TOP + 0.006), alu, segments=32)
cyl("FKM seal", 0.0062, 0.002, (dock_cap.x, dock_cap.y, CAP_TOP + 0.004), fkm, segments=32)
cyl("NFC reader ring", 0.017, 0.003, (dock_cap.x, dock_cap.y, CAP_TOP + 0.012), pcb, segments=48)

valve_at = Vector((post.x, post.y - 0.022, 0.25))
box("3/2 valve body", (0.018, 0.022, 0.016), valve_at, valve_body)
cyl("Valve coil", 0.009, 0.024, valve_at + Vector((0, 0, 0.008)), coil_black)
box("Pressure sensor", (0.018, 0.004, 0.012), valve_at + Vector((0, -0.002, -0.03)), pcb)
tube("Air: valve to docking head", [valve_at + Vector((-0.01, 0, 0)), Vector((0.10, -0.25, 0.30)),
                                    Vector((dock_cap.x + 0.012, dock_cap.y - 0.01, CAP_TOP + 0.045)),
                                    Vector((dock_cap.x + 0.009, dock_cap.y, CAP_TOP + 0.025))], 0.002, pu_blue)

# ------------------------------------------------------------------ air supply (left front)

pump_at = Vector((-0.31, -0.30, TOP))
box("Diaphragm pump", (0.06, 0.045, 0.04), pump_at + Vector((0, 0, 0.02)), plastic_dark)
cyl("Pump motor", 0.016, 0.035, pump_at + Vector((0, -0.0225, 0.02)), steel, rot=(math.pi / 2, 0, 0))
res_at = Vector((-0.31, -0.20, TOP))
cyl("Air reservoir", 0.03, 0.10, res_at, alu)
cyl("Relief valve", 0.006, 0.018, res_at + Vector((0.008, 0, 0.10)), brass)
tube("Air: pump to reservoir", [pump_at + Vector((0, 0.022, 0.03)), res_at + Vector((0, -0.05, 0.07)),
                                res_at + Vector((0, -0.02, 0.10))], 0.002, pu_blue)
tube("Air: reservoir to valve", [res_at + Vector((-0.008, 0, 0.10)), Vector((-0.20, -0.36, 0.12)),
                                 Vector((0.05, -0.38, 0.10)), Vector((post.x, post.y - 0.03, 0.18)),
                                 valve_at + Vector((0, -0.006, -0.008))], 0.002, pu_blue)

# ------------------------------------------------------------------ electronics (right)

ctrl = Vector((0.31, -0.25, TOP))
box("Controller enclosure", (0.10, 0.075, 0.025), ctrl + Vector((0, 0, 0.0125)), plastic_dark)
box("ESP32 + TMC2209 + MAX3232", (0.085, 0.06, 0.003), ctrl + Vector((0, 0, 0.0265)), pcb)
box("12 V PSU", (0.09, 0.06, 0.035), (0.31, 0.32, TOP + 0.0175), alu)
cable = mat("cable", (0.12, 0.12, 0.13), rough=0.6)
tube("Balance RS232", [Vector((dock_tip.x + 0.075, dock_tip.y - 0.04, TOP + 0.02)),
                       Vector((0.18, -0.30, TOP + 0.01)), ctrl + Vector((-0.05, 0, 0.012))], 0.0018, cable)
tube("Dock cable (valve, actuator, NFC)", [ctrl + Vector((-0.02, 0.035, 0.02)), Vector((0.24, -0.20, 0.12)),
                                           Vector((post.x + 0.012, post.y, 0.28))], 0.0022, cable)
tube("Motor + hall cable", [ctrl + Vector((0.03, 0.035, 0.02)), Vector((0.36, 0.0, TOP + 0.01)),
                            motor_at + Vector((0.02, 0, 0.02))], 0.0022, cable)

# ------------------------------------------------------------------ labels

label("Carousel: 48 x 30 mL bottles\nturntable on lazy-susan bearing", (-0.12, 0.42, 0.25), 0.014)
label("Dispensing cap per bottle:\nair inlet, dip tube, gooseneck nozzle,\n0.2 mm bleed hole, NFC tag",
      (-0.50, -0.02, 0.24))
label("Docking head: FKM seal on air inlet\n+ NFC reader (bottle ID)", (-0.02, -0.17, 0.47))
label("The only valve:\n3/2 + pressure sensor", (0.36, -0.31, 0.31))
label("Pump -> reservoir + relief valve", (-0.33, -0.38, 0.09))
label("Balance 0.01 g, RS232 -> ESP32\nclosed-loop gravimetric dosing", (dock_tip.x, -0.40, 0.07))
label("Vial in draft shield", (-0.11, -0.26, 0.19))
label("Drip gutter ring\n(gap only at the dock)", (0.38, 0.38, 0.32))
label("Nozzle tips above max liquid level\n-> no siphon", (0.48, -0.02, 0.17), 0.012,
      mat("label_red", (0.75, 0.08, 0.05), rough=0.9))
label("NEMA17 belt drive + hall homing", (0.36, 0.20, 0.07))
label("ESP32 + stepper driver + MAX3232", (0.34, -0.33, 0.04))
label("12 V PSU", (0.40, 0.32, 0.05))

# ------------------------------------------------------------------ camera, lights, world

cam_data = bpy.data.cameras.new("Render camera")
cam_data.lens = 39
cam_data.clip_start = 0.005
cam = bpy.data.objects.new("Render camera", cam_data)
cam.location = (0.95, -1.15, 0.95)
root.objects.link(cam)
look = bpy.data.objects.new("Camera target", None)
look.location = (0.0, -0.05, 0.13)
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

for name, energy, size, loc in (("Key", 30, 0.8, (0.5, -0.6, 0.9)), ("Fill", 10, 1.0, (-0.8, -0.3, 0.6)),
                                ("Rim", 15, 0.8, (-0.2, 0.9, 0.8))):
    light = bpy.data.lights.new(name, "AREA")
    light.energy, light.size = energy, size
    lob = bpy.data.objects.new(name + " light", light)
    lob.location = loc
    root.objects.link(lob)
    lt = lob.constraints.new("TRACK_TO")
    lt.target, lt.track_axis, lt.up_axis = look, "TRACK_NEGATIVE_Z", "UP_Y"

world = bpy.data.worlds.new("Doser world")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.72, 0.74, 0.78, 1.0)
bg.inputs["Strength"].default_value = 0.35
scene.world = world

box("Floor", (6, 6, 0.001), (0, 0, -0.0006), mat("floor", (0.80, 0.80, 0.82), rough=0.8))

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
