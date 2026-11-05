# Septum closure (Perfume-Doser-Feasibility.md, §3; Septum-Leak-Analysis.md): each bottle keeps its own screw
# cap; the cap top gets two Ø 2 mm holes 5 mm apart, its liner is replaced by a PTFE/silicone septum (PTFE face
# down), and two 1/16" FEP tubes are pushed through 0.9 mm needle punctures. The silicone seals, the PTFE face is
# a vapour shield; a saddle clipped to the cap clamps both tubes. Half-section through the tube plane on three
# bottles + a x4 detail.
# Real scale, metres. Rebuilds the "Septum Cap" scene on every run and leaves all other scenes alone.
import math

import bmesh
import bpy
from mathutils import Vector

SCENE = "Septum Cap"
MM = 0.001
CUT = (0.0, math.pi)          # keep the back half: the section plane y = 0 contains both tubes
TUBE_R = 0.79 * MM            # 1/16" FEP
TUBE_OFF = 2.5 * MM           # tubes 5 mm apart
PTFE_T, SEPT_T = 0.25 * MM, 2.5 * MM
CAP_TOP_T = 2.5 * MM
CAP_HOLE_R = 1.0 * MM         # two Ø 2 mm holes: guide the tubes, leave almost no silicone open to the air

# (label, x, body r, body h, neck outer r, neck inner r, neck h, glass, cap colour, liquid colour, fill)
BOTTLES = [("15 mL dropper (DIN 18)\n17.5 mm septum", -0.085, 12.5, 45, 8.8, 3.75, 12, "amber", (0.08, 0.08, 0.09),
            (0.95, 0.80, 0.35), 0.6),
           ("100 mL Boston round (24/410)\n22 mm septum", 0.0, 24.0, 85, 12.0, 7.0, 14, "amber", (0.08, 0.08, 0.09),
            (0.75, 0.90, 0.55), 0.55),
           ("100 mL GL 45 lab bottle\nGL 45 septum cap", 0.105, 28.0, 62, 22.5, 17.0, 20, "clear", (0.15, 0.35, 0.75),
            (0.80, 0.60, 0.85), 0.5)]
DETAIL = Vector((0.215, 0.0, 0.085))   # where the x4 detail of the Boston-round closure is drawn
DETAIL_SCALE = 4.0


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
ptfe = mat("ptfe_face", (0.97, 0.97, 0.95), rough=0.4)
silicone = mat("septum_silicone", (0.70, 0.12, 0.12), rough=0.7)
fep = mat("fep", (0.92, 0.95, 0.95), rough=0.15, alpha=0.8)
fep_air = mat("fep_air", (0.45, 0.68, 0.95), rough=0.2, alpha=0.9)
clip_mat = mat("petg_clip", (0.55, 0.57, 0.60), rough=0.5)


def closure(tag, o, nr, ni, nh, lip, cap_color, s=1.0, liquid=None, bottom=None):
    """Neck thread, cap, septum, drawn PTFE face, tubes and saddle at origin o (lip height `lip` above o), scale s."""
    S = lambda v: v * s
    # two thread ridges on the neck, matching grooves are implied by the cap's inner wall
    for k in range(2):
        z0 = lip - nh * (0.35 + 0.3 * k)
        revolve("Thread %s %d" % (tag, k), [(S(nr), S(z0)), (S(nr + 0.8 * MM), S(z0 + 0.8 * MM)), (S(nr), S(z0 + 1.6 * MM))],
                o, glass["amber" if cap_color[2] < 0.5 else "clear"], a0=CUT[0], a1=CUT[1], segments=48)
    r_o, r_i = nr + 1.8 * MM, nr + 0.9 * MM
    z_top = lip + SEPT_T + CAP_TOP_T
    cap = [(r_i, lip - nh + 1 * MM), (r_o, lip - nh + 1 * MM), (r_o, z_top), (0, z_top), (0, z_top - CAP_TOP_T),
           (r_i, z_top - CAP_TOP_T)]
    cap_ob = revolve("Cap " + tag, [(S(r), S(z)) for r, z in cap], o, mat("cap_%s" % tag[:2], cap_color, rough=0.45),
                     a0=CUT[0], a1=CUT[1], segments=64)
    for sx in (1, -1):   # the two Ø 2 mm holes, cut by hidden cylinders
        cutter = cyl("Cap hole cutter %s %d" % (tag, sx), S(CAP_HOLE_R), S(CAP_TOP_T + 2 * MM),
                     o + Vector((S(sx * TUBE_OFF), 0, S(z_top - CAP_TOP_T - 1 * MM))), None, segments=32)
        cutter.hide_render = cutter.hide_viewport = True
        mod = cap_ob.modifiers.new("hole %d" % sx, "BOOLEAN")
        mod.operation, mod.object, mod.solver = "DIFFERENCE", cutter, "EXACT"
    # septum: PTFE face on the rim, silicone above, pressed by the cap top
    revolve("Septum PTFE face " + tag, [(0, S(lip)), (S(r_i), S(lip)), (S(r_i), S(lip + PTFE_T)), (0, S(lip + PTFE_T))],
            o, ptfe, a0=CUT[0], a1=CUT[1], segments=64)
    revolve("Septum silicone " + tag, [(0, S(lip + PTFE_T)), (S(r_i), S(lip + PTFE_T)), (S(r_i), S(lip + SEPT_T)),
                                        (0, S(lip + SEPT_T))], o, silicone, a0=CUT[0], a1=CUT[1], segments=64)
    tops = {}
    for name, sx, mat_t, low in (("liquid", 1, fep, bottom), ("air", -1, fep_air, lip - 6 * MM)):
        c = o + Vector((S(sx * TUBE_OFF), 0, 0))
        z_low = low if low is not None else lip - 10 * MM
        z_high = z_top + (25 * MM if s == 1.0 else 6 * MM)
        revolve("FEP %s tube %s" % (name, tag), [(0, S(z_low)), (S(TUBE_R), S(z_low + 0.6 * MM)), (S(TUBE_R), S(z_high)),
                                                  (0, S(z_high))], c, mat_t, a0=0, a1=2 * math.pi, segments=24, caps=False)
        # PTFE face drawn down (and torn) around the tube: a vapour shield, not the seal; the silicone seals
        revolve("PTFE face drawn %s %s" % (name, tag), [(S(TUBE_R), S(lip - 0.5 * MM)), (S(TUBE_R + 0.2 * MM), S(lip)),
                                                         (S(TUBE_R + 0.4 * MM), S(lip)), (S(TUBE_R), S(lip - 0.7 * MM))],
                c, ptfe, a0=CUT[0], a1=CUT[1], segments=32)
        tops[name] = c + Vector((0, 0, S(z_high)))
    # strain-relief saddle clipped onto the cap: a bar clamping both tubes, two legs gripping the cap skirt,
    # so a pull on the lines goes into the cap and never slides a tube in the septum (behind the section plane)
    bar_w, depth = 2 * (r_o + 1.2 * MM), 5 * MM
    box("Saddle bar " + tag, (S(bar_w), S(depth), S(3 * MM)), o + Vector((0, S(depth / 2), S(z_top + 3.5 * MM))),
        clip_mat)
    leg_h = z_top + 5 * MM - (lip - nh * 0.4)
    for sx in (1, -1):
        box("Saddle leg %s %d" % (tag, sx), (S(1.2 * MM), S(depth), S(leg_h)),
            o + Vector((S(sx * (r_o + 0.6 * MM)), S(depth / 2), S(z_top + 5 * MM - leg_h / 2))), clip_mat)
    return tops


# ------------------------------------------------------------------ three bottles, half-sectioned

for k, (name, x, br, bh, nr, ni, nh, gkey, cap_color, liq, fill) in enumerate(BOTTLES):
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
    tops = closure("B%d" % (k + 1), base, nr, ni, nh, lip, cap_color, bottom=wall + 2 * MM)
    for nm, mt, dx in (("liquid", fep, 8 * MM), ("air", fep_air, -8 * MM)):
        t = tops[nm]
        tube("%s line %d" % (nm, k + 1), [t, t + Vector((dx * 0.3, 0.004, 0.012)), t + Vector((dx, 0.012, 0.03))],
             TUBE_R, mt, 12)
    label(name, Vector((x, -0.02, -0.012)), 0.0042)

# ------------------------------------------------------------------ x4 detail of the Boston-round closure

nr, ni, nh = 12.0 * MM, 7.0 * MM, 14.0 * MM
lip_d = 12 * MM
neck = [(ni, 0), (nr, 0), (nr, lip_d - 1 * MM), (nr - 0.6 * MM, lip_d), (ni + 0.6 * MM, lip_d), (ni, lip_d - 1 * MM)]
revolve("Detail neck", [(r * DETAIL_SCALE, z * DETAIL_SCALE) for r, z in neck], DETAIL, glass["amber"], segments=72)
closure("D", DETAIL, nr, ni, nh, lip_d, (0.08, 0.08, 0.09), s=DETAIL_SCALE, bottom=-4 * MM)

# ------------------------------------------------------------------ labels

label("Septum in the bottle's own cap: two Ø 2 mm holes, liner replaced by a PTFE/silicone septum",
      Vector((0.05, -0.01, 0.205)), 0.0052)
label("Detail ×4 (100 mL Boston round)", DETAIL + Vector((0, -0.02, 0.135)), 0.0048)
label("PTFE face on the rim\n= rim seal + vapour shield", DETAIL + Vector((0.085, -0.02, 0.045)), 0.0040)
label("Silicone = the seal around each tube\n(grips at ~0.4-1.2 MPa, need 0.02)", DETAIL + Vector((0.085, -0.02, 0.075)),
      0.0040, mat("label_red", (0.65, 0.10, 0.08), rough=0.9))
label("PTFE face drawn down and torn around each tube:\nvapour shield only (0.9 mm needle puncture)",
      DETAIL + Vector((0.0, -0.02, -0.025)), 0.0040)
label("Two Ø 2 mm cap holes, 5 mm apart:\nalmost no silicone open to the air", DETAIL + Vector((-0.085, -0.02, 0.105)),
      0.0040)
label("Saddle clipped to the cap clamps both tubes:\npulls go into the cap, not the septum",
      DETAIL + Vector((0.07, -0.02, 0.122)), 0.0040)

# ------------------------------------------------------------------ camera, lights, world

cam_data = bpy.data.cameras.new("Render camera")
cam_data.lens = 42
cam_data.clip_start = 0.002
cam = bpy.data.objects.new("Render camera", cam_data)
cam.location = (0.07, -0.68, 0.20)
root.objects.link(cam)
look = bpy.data.objects.new("Camera target", None)
look.location = (0.07, 0.0, 0.10)
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
               mat("label_card", (0.97, 0.97, 0.95), rough=0.9, emission=0.15))
    card.parent = ob
    t = ob.constraints.new("TRACK_TO")
    t.target, t.track_axis, t.up_axis = cam, "TRACK_Z", "UP_Y"

for name, energy, size, loc in (("Key", 8, 0.4, (0.35, -0.45, 0.45)), ("Fill", 3, 0.6, (-0.45, -0.3, 0.3)),
                                ("Rim", 4, 0.4, (-0.1, 0.5, 0.4))):
    light = bpy.data.lights.new(name, "AREA")
    light.energy, light.size = energy, size
    lob = bpy.data.objects.new(name + " light", light)
    lob.location = loc
    root.objects.link(lob)
    lt = lob.constraints.new("TRACK_TO")
    lt.target, lt.track_axis, lt.up_axis = look, "TRACK_NEGATIVE_Z", "UP_Y"

world = bpy.data.worlds.new("Septum world")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.72, 0.74, 0.78, 1.0)
bg.inputs["Strength"].default_value = 0.25
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

result = "built %d objects in '%s'" % (len(scene.objects), SCENE)
