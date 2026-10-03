"""Ranger hybrid vis: paint baseline vs hybrid SBS + summary."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
import cv2
import trimesh
sys.path.insert(0, r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\quality_lab")
from project_hybrid_a3 import ProjectionRender

JOB = Path(r"D:\SF3D_QualityLab\app_jobs\4abf740c34c9487ba818455efe460833")
OUT = JOB / "quality_jump_second_fixture"
VIS = Path(r"C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_ranger_hybrid")
VIS.mkdir(parents=True, exist_ok=True)
UV = JOB / "controls" / "uv_mesh.npz"
PAINT = JOB / "textured_color.glb"
HYB = OUT / "textured_hybrid_ranger_color.glb"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
pre = json.loads((OUT/"pre_hashes.json").read_text(encoding="utf-8"))
assert sha(PAINT).lower() == pre["textured_color"].lower()
assert sha(JOB/"textured_pbr.glb").lower() == pre["textured_pbr"].lower()

data = np.load(UV)
mesh = trimesh.Trimesh(vertices=data["vertices"], faces=data["faces"], process=False, visual=trimesh.visual.TextureVisuals(uv=data["uv"]))
mesh.vertex_normals = data["vertex_normals"]

def atlas_from_glb(glb):
    scene = trimesh.load(str(glb), force="scene", process=False)
    m = list(scene.geometry.values())[0]
    return np.asarray(m.visual.material.baseColorTexture.convert("RGB"), dtype=np.float32)/255.0

def render(atlas, azims):
    r = ProjectionRender(default_resolution=2048, texture_size=2048)
    r.load_mesh(mesh); r.set_texture(atlas)
    return {lab: Image.fromarray((r.render(0,ang,return_type="np").clip(0,1)*255).astype(np.uint8)).resize((1024,1024)) for lab,ang in azims}

azims=[("front",0),("back",180),("p35",35),("m35",-35),("p90",90),("m90",-90)]
print("render paint...", flush=True)
paint=render(atlas_from_glb(PAINT), azims)
print("render hybrid...", flush=True)
hyb=render(atlas_from_glb(HYB), azims)

crops={"face":(400,40,640,300),"chest":(360,280,664,540),"back_logo":(360,200,664,480)}

def sheet(ims, labels, box, path, title):
    tiles=[]
    for im,lab in zip(ims,labels):
        c=im.crop(box).resize((384,384), Image.Resampling.LANCZOS)
        canvas=Image.new("RGB",(384,416),(18,18,22)); canvas.paste(c,(0,32))
        arr=np.array(canvas); arr[:32]=(36,36,44)
        cv2.putText(arr,lab,(10,22),cv2.FONT_HERSHEY_SIMPLEX,0.55,(230,230,235),1,cv2.LINE_AA)
        tiles.append(Image.fromarray(arr))
    w=sum(t.width for t in tiles)+12*(len(tiles)-1)
    sh=Image.new("RGB",(w,tiles[0].height+28),(10,10,14)); arr=np.array(sh)
    cv2.putText(arr,title,(10,20),cv2.FONT_HERSHEY_SIMPLEX,0.55,(200,200,210),1,cv2.LINE_AA)
    sh=Image.fromarray(arr); x=0
    for t in tiles:
        sh.paste(t,(x,28)); x+=t.width+12
    sh.save(path)

def lap(im,box):
    g=cv2.cvtColor(np.array(im.crop(box).convert("RGB")),cv2.COLOR_RGB2GRAY).astype(np.float32)
    return float(np.mean(np.abs(cv2.Laplacian(g,cv2.CV_32F))))

metrics={}
for name,box in crops.items():
    src="back" if "back" in name else "front"
    sheet([paint[src], hyb[src]], ["paint","hybrid"], box, VIS/f"sbs_{name}.png", f"Ranger {name}")
    metrics[name]={"paint":lap(paint[src],box),"hybrid":lap(hyb[src],box)}
for lab in ("front","back","p35","m35","p90","m90"):
    sheet([paint[lab], hyb[lab]], ["paint","hybrid"], (256,0,768,1024), VIS/f"sbs_angle_{lab}.png", f"Ranger {lab}")
    paint[lab].save(VIS/f"paint_{lab}.png"); hyb[lab].save(VIS/f"hybrid_{lab}.png")

rep=json.loads((OUT/"hybrid_work"/"report.json").read_text(encoding="utf-8"))
summary={
  "fixture":"ranger_ortho_v1",
  "job":str(JOB),
  "method":"hybrid_a3_paint_fill_plus_ortho_projection",
  "texture_path":"NEW hybrid (not legacy front-only paint finalize)",
  "production_accepted":False,
  "studio_default_flip":False,
  "sha256":{
    "hybrid_color":sha(HYB),
    "hybrid_pbr_mr_retain":sha(OUT/"textured_hybrid_ranger_pbr_mr_retain.glb"),
    "paint_color_untouched":sha(PAINT),
    "paint_pbr_untouched":sha(JOB/"textured_pbr.glb"),
  },
  "baseline_integrity":{
    "textured_color_unchanged": sha(PAINT).lower()==pre["textured_color"].lower(),
    "textured_pbr_unchanged": sha(JOB/"textured_pbr.glb").lower()==pre["textured_pbr"].lower(),
  },
  "mean_confidence":rep["mean_confidence"],
  "views":[{"name":v["name"],"iou":v.get("silhouette_iou"),"skipped":v.get("skipped_projection",False),"w50":v.get("atlas_pixels_weight_above_half")} for v in rep["views"]],
  "laplacian":metrics,
  "vis_dir":str(VIS),
  "mr_retain_mode":rep.get("mr_retain_mode"),
}
(OUT/"ranger_hybrid_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
(VIS/"ranger_hybrid_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps({"sha12":{k:v[:12] for k,v in summary["sha256"].items()},"lap":metrics,"views":summary["views"],"mean_conf":summary["mean_confidence"]},indent=2))
