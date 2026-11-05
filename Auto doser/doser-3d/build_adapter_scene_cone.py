# Universal bottle adapter v2 (Perfume-Doser-Feasibility.md, §3): one 60° PTFE cone with an ePTFE
# skin seals on the inner rim of any neck from ~7.5 to 40 mm. Shown as cutaways on three very
# different bottles. Real scale, metres. Rebuilds the "Universal Adapter" scene on every run.
import math

import bmesh
import bpy
from mathutils import Vector

SCENE = "Cone Adapter (option A)"
MM = 0.001
HALF = math.radians(30)                     # 60° included cone
TIP_R, BASE_R = 3.0 * MM, 21.0 * MM         # cone radius at tip / base
CONE_H = (BASE_R - TIP_R) / math.tan(HALF)  # ≈ 31.2 mm
SKIN = 0.6 * MM                             # ePTFE skin thickness
FLANGE_R, FLANGE_H = 24.0 * MM, 8.0 * MM
BORE_OFF = 1.2 * MM                         # bores at ±1.2 mm from the axis
CUT = (math.radians(-45), math.radians(225))  # revolve range: front quarter cut away

# (label, x, body r, body h, neck outer r, neck inner r, neck h, glass, liquid colour, fill fraction)
BOTTLES = [("15 mL dropper (DIN 18)\nneck ID 7.5 mm", -0.085, 12.5, 45, 8.8, 3.75, 12, "amber", (0.95, 0.80, 0.35), 0.6),
           ("100 mL Boston round (24/410)\nneck ID 14 mm", 0.0, 24.0, 85, 12.0, 7.0, 14, "amber", (0.75, 0.90, 0.55), 0.55),
           ("100 mL GL 45 lab bottle\nneck ID 34 mm", 0.105, 28.0, 62, 22.5, 17.0, 20, "clear", (0.80, 0.60, 0.85), 0.5)]


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
    m = bpy.data.materials.new("adapter_" + name)
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


def revolve(name, profile, origin, material, a0=CUT[0], a1=CUT[1], segments=72, caps=True):
    """Revolve a closed (r, z) polygon around the vertical axis through origin, from a0 to a1."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for i in range(segments + 1):
        a = a0 + (a1 - a0) * i / segments
        c, s = math.cos(a), math.sin(a)
        rings.append([bm.verts.new((origin.x + r * c, origin.y + r * s, origin.z + z)) for r, z in profile])
    n = len(profile)
    for i in range(segments):
        for k in range(n):
            a, b = rings[i], rings[i + 1]
            quad = (a[k], a[(k + 1) % n], b[(k + 1) % n], b[k])
            try:
                bm.faces.new(quad)
            except ValueError:
                pass
    if caps:
        for ring, flip in ((rings[0], True), (rings[-1], False)):
            try:
                bm.faces.new(ring[::-1] if flip else ring)
            except ValueError:
                pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = len(poly.vertices) == 4
    ob = bpy.data.objects.new(name, me)
    return link(ob, material)


def cyl(name, r, h, loc, material, segments=24):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=r, radius2=r, depth=h)
    bmesh.ops.translate(bm, vec=Vector((0, 0, h / 2)), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = len(poly.vertices) == 4
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    return link(ob, material)


def box(name, size, loc, material):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    return link(ob, material)


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


labels = []


def label(text, loc, size=0.0045, material=None):
    cu = bpy.data.curves.new("lbl", "FONT")
    cu.body = text
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.extrude = 0.00005
    ob = bpy.data.objects.new("Label: " + text.split("\n")[0][:40], cu)
    ob.location = loc
    link(ob, material or mat("label", (0.05, 0.05, 0.07), rough=0.9))
    labels.append(ob)
    return ob


# ------------------------------------------------------------------ materials

glass = {"amber": mat("amber_glass", (0.55, 0.25, 0.05), rough=0.05, alpha=0.45),
         "clear": mat("clear_glass", (0.85, 0.92, 1.0), rough=0.05, alpha=0.3)}
ptfe = mat("ptfe", (0.95, 0.95, 0.93), rough=0.45)
eptfe = mat("eptfe_skin", (0.62, 0.80, 0.98), rough=0.8)
fep = mat("fep", (0.92, 0.95, 0.95), rough=0.15, alpha=0.7)
steel = mat("steel", (0.8, 0.8, 0.82), metallic=1.0, rough=0.25)
pu = mat("pu_air", (0.10, 0.35, 0.85), rough=0.4)
pom = mat("pom_pad", (0.12, 0.12, 0.13), rough=0.5)
alu = mat("aluminium", (0.62, 0.64, 0.67), metallic=1.0, rough=0.35)

# ------------------------------------------------------------------ one adapter per bottle

r_skin = lambda t: TIP_R + SKIN + t * math.tan(HALF)       # outer skin radius at height t above the tip
for k, (name, x, br, bh, nr, ni, nh, gkey, liq, fill) in enumerate(BOTTLES):
    br, bh, nr, ni, nh = br * MM, bh * MM, nr * MM, ni * MM, nh * MM
    base = Vector((x, 0.0, 0.0))
    wall = 1.8 * MM
    shoulder = (br - nr) * 0.8
    lip = bh + shoulder + nh
    outer = [(0, 0), (br - 2 * MM, 0), (br, 2 * MM), (br, bh), (nr, bh + shoulder), (nr, lip - 1 * MM),
             (nr - 0.6 * MM, lip), (ni + 0.6 * MM, lip), (ni, lip - 1 * MM), (ni, bh + shoulder - wall),
             (br - wall, bh - wall * 0.5), (br - wall, 2.5 * MM), (br - 3 * MM, wall), (0, wall)]
    revolve("Bottle %d" % (k + 1), outer, base, glass[gkey], segments=72)
    level = wall + (bh - 2 * wall) * fill
    revolve("Liquid %d" % (k + 1), [(0, wall), (br - wall - 0.3 * MM, wall), (br - wall - 0.3 * MM, level), (0, level)],
            base, mat("liquid_%d" % k, liq, rough=0.1, alpha=0.75), segments=72)

    # seat: the skin touches the rim where its radius equals the neck's inner radius
    t_seat = max((ni - TIP_R - SKIN) / math.tan(HALF), 0.0)
    tip_z = lip - t_seat
    o = Vector((x, 0.0, tip_z))
    cone = [(0, 0), (TIP_R, 0), (BASE_R, CONE_H), (FLANGE_R, CONE_H), (FLANGE_R, CONE_H + FLANGE_H),
            (0, CONE_H + FLANGE_H)]
    revolve("PTFE cone %d" % (k + 1), cone, o, ptfe, segments=72)
    skin_top = CONE_H * 0.92
    skin = [(TIP_R, 0), (TIP_R + SKIN, 0), (r_skin(skin_top), skin_top), (r_skin(skin_top) - SKIN, skin_top)]
    revolve("ePTFE skin %d" % (k + 1), skin, o, eptfe, segments=72)

    top = tip_z + CONE_H + FLANGE_H
    # liquid line: one FEP tube from the bottle bottom up through the cone (bore at +x)
    lx = x + BORE_OFF
    tube("FEP liquid line %d" % (k + 1), [Vector((lx, 0, wall + 2 * MM)), Vector((lx, 0, top)),
                                          Vector((lx, 0, top + 25 * MM)), Vector((lx + 6 * MM, 0.01, top + 45 * MM))],
         0.795 * MM, mat("fep_line_%d" % k, liq, rough=0.2, alpha=0.9), 16)
    # air: stainless stub pressed into the top of the second bore (at -x), PU line on top
    ax = x - BORE_OFF
    cyl("Air stub %d" % (k + 1), 1.5 * MM, 22 * MM, Vector((ax, 0, top - 10 * MM)), steel, 16)
    tube("Air line %d" % (k + 1), [Vector((ax, 0, top + 11 * MM)), Vector((ax - 2 * MM, 0, top + 30 * MM)),
                                   Vector((ax - 10 * MM, 0.012, top + 45 * MM))], 2.0 * MM, pu, 12)
    # coaxial spring hold-down around both tubes
    revolve("POM pad %d" % (k + 1), [(5.2 * MM, 0), (11 * MM, 0), (11 * MM, 3 * MM), (5.2 * MM, 3 * MM)],
            Vector((x, 0, top)), pom, segments=48)
    n_turns, steps = 7, 14
    spring_h = 22 * MM
    pts = [Vector((x + 5.4 * MM * math.cos(2 * math.pi * i / steps), 5.4 * MM * math.sin(2 * math.pi * i / steps),
                   top + 3 * MM + spring_h * i / (n_turns * steps))) for i in range(n_turns * steps + 1)]
    tube("Hold-down spring %d" % (k + 1), pts, 0.6 * MM, steel, 4)
    arm_z = top + 3 * MM + spring_h
    for side in (-1, 1):
        box("Hold-down fork %d%s" % (k + 1, "ab"[side > 0]), (4 * MM, 30 * MM, 4 * MM),
            Vector((x + side * 7 * MM, 0.012, arm_z + 2 * MM)), alu)
    box("Hold-down arm %d" % (k + 1), (18 * MM, 6 * MM, 4 * MM), Vector((x, 0.024, arm_z + 2 * MM)), alu)
    label(name, Vector((x, -0.02, -0.012)), 0.0042)

# ------------------------------------------------------------------ labels

label("ONE adapter for every bottle: PTFE cone 60°, Ø 6 → 42 mm\nfits neck ID ~7.5-40 mm, self-centring",
      Vector((0.01, -0.01, 0.205)), 0.0055)
label("ePTFE skin\nseals on the inner rim\n(line contact)", Vector((0.185, -0.02, 0.105)), 0.0042,
      mat("label_blue", (0.05, 0.25, 0.65), rough=0.9))
label("2 bores near the axis:\nFEP liquid line (slides = dip-tube length)\n+ stainless air stub", Vector((-0.17, -0.02, 0.15)), 0.0042)
label("Coaxial spring + POM pad\n~30 N hold-down", Vector((0.19, -0.02, 0.165)), 0.0042)

# ------------------------------------------------------------------ camera, lights, world

cam_data = bpy.data.cameras.new("Render camera")
cam_data.lens = 50
cam_data.clip_start = 0.002
cam = bpy.data.objects.new("Render camera", cam_data)
cam.location = (0.06, -0.62, 0.26)
root.objects.link(cam)
look = bpy.data.objects.new("Camera target", None)
look.location = (0.01, 0.0, 0.095)
root.objects.link(look)
c = cam.constraints.new("TRACK_TO")
c.target, c.track_axis, c.up_axis = look, "TRACK_NEGATIVE_Z", "UP_Y"
scene.camera = cam

for ob in labels:
    to_cam = cam.location - ob.location
    dist = to_cam.length
    pull = 0.08
    ob.location = ob.location + to_cam.normalized() * pull
    ob.data.size *= (dist - pull) / dist
    lines = ob.data.body.split("\n")
    size = ob.data.size
    card = box("Label card", (max(len(l) for l in lines) * size * 0.52 + size,
                              len(lines) * size * 1.2 + size * 0.5, 0.0001), Vector((0, 0, -0.0002)),
               mat("label_card", (0.97, 0.97, 0.95), rough=0.9, emission=0.35))
    card.parent = ob
    t = ob.constraints.new("TRACK_TO")
    t.target, t.track_axis, t.up_axis = cam, "TRACK_Z", "UP_Y"

for name, energy, size, loc in (("Key", 18, 0.4, (0.35, -0.45, 0.45)), ("Fill", 7, 0.6, (-0.45, -0.3, 0.3)),
                                ("Rim", 8, 0.4, (-0.1, 0.5, 0.4))):
    light = bpy.data.lights.new(name, "AREA")
    light.energy, light.size = energy, size
    lob = bpy.data.objects.new(name + " light", light)
    lob.location = loc
    root.objects.link(lob)
    lt = lob.constraints.new("TRACK_TO")
    lt.target, lt.track_axis, lt.up_axis = look, "TRACK_NEGATIVE_Z", "UP_Y"

world = bpy.data.worlds.new("Adapter world")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.72, 0.74, 0.78, 1.0)
bg.inputs["Strength"].default_value = 0.35
scene.world = world
box("Floor", (3, 3, 0.001), Vector((0, 0, -0.0006)), mat("floor", (0.78, 0.78, 0.80), rough=0.8))

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
            space.clip_start = 0.0005
            space.shading.type = "MATERIAL"
            space.region_3d.view_perspective = "CAMERA"

result = "built %d objects; cone height %.1f mm; seat heights: %s" % (
    len(scene.objects), CONE_H * 1000,
    ", ".join("%.1f mm" % (max((b[5] * MM - TIP_R - SKIN) / math.tan(HALF), 0) * 1000) for b in BOTTLES))
