# render_ref_cam.py — render con camara estimada de la fotografia de referencia.
# Uso: blender -b <blend> -P render_ref_cam.py -- <out.png> <stl|NONE> [az] [cam_h] [dist] [lens] [resx] [resy]
import bpy, sys, math, os
argv = sys.argv[sys.argv.index("--")+1:]
out_png = argv[0]; out_stl = argv[1] if len(argv)>1 else ""
az   = math.radians(float(argv[2])) if len(argv)>2 else math.radians(28)
camh = float(argv[3]) if len(argv)>3 else 45.0
dist = float(argv[4]) if len(argv)>4 else 460.0
lens = float(argv[5]) if len(argv)>5 else 55.0
rx   = int(argv[6]) if len(argv)>6 else 512
ry   = int(argv[7]) if len(argv)>7 else 896
sc = bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.samples=32; sc.cycles.use_denoising=False; sc.cycles.device='CPU'
sc.render.resolution_x=rx; sc.render.resolution_y=ry; sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
if sc.world is None: sc.world = bpy.data.worlds.new("W")
sc.world.use_nodes=True
sc.world.node_tree.nodes["Background"].inputs[0].default_value=(0.35,0.35,0.35,1)
for o in list(bpy.data.objects):
    if o.type=='LIGHT': bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.light_add(type='SUN', location=(0,0,10))
sun=bpy.context.active_object; sun.data.energy=3.0
sun.rotation_euler=(math.radians(50),math.radians(-15),math.radians(30))
import mathutils
meshes=[o for o in bpy.data.objects if o.type=='MESH']
mins=mathutils.Vector((1e9,)*3); maxs=mathutils.Vector((-1e9,)*3)
for o in meshes:
    for c in o.bound_box:
        w=o.matrix_world @ mathutils.Vector(c)
        mins=mathutils.Vector(map(min,mins,w)); maxs=mathutils.Vector(map(max,maxs,w))
center=(mins+maxs)/2
for o in list(bpy.data.objects):
    if o.type=='CAMERA': bpy.data.objects.remove(o, do_unlink=True)
loc=(center.x+dist*math.cos(az), center.y+dist*math.sin(az), camh)
bpy.ops.object.camera_add(location=loc)
cam=bpy.context.active_object
d=center-mathutils.Vector((0,0,10))-cam.location
d=center-cam.location; d.z=center.z-10-cam.location.z+10
d=(center-cam.location)
cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
cam.data.lens=lens; sc.camera=cam
sc.render.filepath=out_png
bpy.ops.render.render(write_still=True)
print("PIPELINE_RENDER_OK", out_png)
if out_stl and out_stl!="NONE":
    for o in list(bpy.data.objects): o.select_set(o.type=='MESH')
    bpy.ops.wm.stl_export(filepath=out_stl, export_selected_objects=True)
    print("PIPELINE_STL_OK", out_stl, os.path.getsize(out_stl))