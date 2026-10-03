"""Ranger face_iso_v2 vis: paint | prior hybrid | face_iso_v2; front/back + angled; face/jaw crops."""
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
OUT = JOB / "quality_jump_ranger_face_iso_v2"
PRIOR = JOB / "quality_jump_second_fixture"
VIS = Path(r"C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_ranger_face_iso_v2")
VIS.mkdir(parents=True, exist_ok=True)
UV = JOB / "controls" / "uv_mesh.npz"
PAINT = JOB / "textured_color.glb"
HYB = PRIOR / "textured_hybrid_ranger_color.glb"
FISO = OUT / "textured_hybrid_ranger_face_iso_v2_color.glb"
FISO_PBR = OUT / "textured_hybrid_ranger_face_iso_v2_pbr_mr_retain.glb"

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

pre = json.loads((OUT / "pre_hashes.json").read_text(encoding="utf-8"))
post_base = {
    "paint_color": sha(PAINT),
    "paint_pbr": sha(JOB / "textured_pbr.glb"),
    "hybrid_color": sha(HYB),
    "hybrid_pbr": sha(PRIOR / "textured_hybrid_ranger_pbr_mr_retain.glb"),
}
assert all(post_base[k].lower() == pre[k].lower() for k in pre), f"baseline mutated: { {k:(post_base[k],pre[k]) for k in pre if post_base[k]!=pre[k]} }"

data = np.load(UV)
mesh = trimesh.Trimesh(vertices=data["vertices"], faces=data["faces"], process=False, visual=trimesh.visual.TextureVisuals(uv=data["uv"]))
mesh.vertex_normals = data["vertex_normals"]

def atlas_from_glb(glb: Path) -> np.ndarray:
    scene = trimesh.load(str(glb), force="scene", process=False)
    m = list(scene.geometry.values())[0]
    return np.asarray(m.visual.material.baseColorTexture.convert("RGB"), dtype=np.float32) / 255.0

def render(atlas, azims):
    r = ProjectionRender(default_resolution=2048, texture_size=2048)
    r.load_mesh(mesh)
    r.set_texture(atlas)
    out = {}
    for lab, ang in azims:
        im = r.render(0, ang, return_type="np")
        out[lab] = Image.fromarray((im.clip(0, 1) * 255).astype(np.uint8)).resize((1024, 1024))
    return out

azims = [("front", 0), ("back", 180), ("p35", 35), ("m35", -35), ("p90", 90), ("m90", -90)]
print("render paint...", flush=True)
paint = render(atlas_from_glb(PAINT), azims)
print("render prior hybrid...", flush=True)
hyb = render(atlas_from_glb(HYB), azims)
print("render face_iso_v2...", flush=True)
fiso = render(atlas_from_glb(FISO), azims)

crops = {
    "face": (400, 40, 640, 300),
    "jaw": (380, 180, 660, 380),
    "chest": (360, 280, 664, 540),
    "back_logo": (360, 200, 664, 480),
}

def sheet(ims, labels, box, path, title):
    tiles = []
    for im, lab in zip(ims, labels):
        c = im.crop(box).resize((384, 384), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (384, 416), (18, 18, 22))
        canvas.paste(c, (0, 32))
        arr = np.array(canvas)
        arr[:32] = (36, 36, 44)
        cv2.putText(arr, lab, (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (230, 230, 235), 1, cv2.LINE_AA)
        tiles.append(Image.fromarray(arr))
    w = sum(t.width for t in tiles) + 12 * (len(tiles) - 1)
    sh = Image.new("RGB", (w, tiles[0].height + 28), (10, 10, 14))
    arr = np.array(sh)
    cv2.putText(arr, title, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 210), 1, cv2.LINE_AA)
    sh = Image.fromarray(arr)
    x = 0
    for t in tiles:
        sh.paste(t, (x, 28))
        x += t.width + 12
    sh.save(path)

def lap(im, box):
    g = cv2.cvtColor(np.array(im.crop(box).convert("RGB")), cv2.COLOR_RGB2GRAY).astype(np.float32)
    return float(np.mean(np.abs(cv2.Laplacian(g, cv2.CV_32F))))

labels3 = ["paint", "hybrid", "face_iso_v2"]
for name, box in crops.items():
    src = "back" if "back" in name else "front"
    sheet([paint[src], hyb[src], fiso[src]], labels3, box, VIS / f"sbs_{name}.png", f"Ranger {name}  paint|hybrid|face_iso_v2")

for lab, _ in azims:
    sheet([paint[lab], hyb[lab], fiso[lab]], labels3, (256, 0, 768, 1024), VIS / f"sbs_angle_{lab}.png", f"Ranger angle {lab}")
    # face crop on angled for face/jaw focus
    if lab in ("front", "p35", "m35", "p90", "m90"):
        sheet([paint[lab], hyb[lab], fiso[lab]], labels3, crops["face"], VIS / f"sbs_face_angle_{lab}.png", f"Ranger FACE {lab}")
        sheet([paint[lab], hyb[lab], fiso[lab]], labels3, crops["jaw"], VIS / f"sbs_jaw_angle_{lab}.png", f"Ranger JAW {lab}")
    paint[lab].save(VIS / f"paint_{lab}.png")
    hyb[lab].save(VIS / f"hybrid_{lab}.png")
    fiso[lab].save(VIS / f"face_iso_v2_{lab}.png")

metrics = {}
for name, box in crops.items():
    src = "back" if "back" in name else "front"
    metrics[name] = {
        "paint": lap(paint[src], box),
        "hybrid": lap(hyb[src], box),
        "face_iso_v2": lap(fiso[src], box),
    }

rep = json.loads((OUT / "report.json").read_text(encoding="utf-8"))
micro = (rep["views"][0].get("align") or {}).get("micro") or {}
extract = micro.get("extract") or {}

# cyan-collar heuristic: strong cyan dominance in collar/jaw band vs hybrid
def cyan_score(im, box):
    arr = np.array(im.crop(box).convert("RGB"), dtype=np.float32)
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    cyan = ((b > r + 20) & (g > r + 10) & (b > 80)).mean()
    return float(cyan)

cyan = {
    "paint": cyan_score(paint["front"], crops["jaw"]),
    "hybrid": cyan_score(hyb["front"], crops["jaw"]),
    "face_iso_v2": cyan_score(fiso["front"], crops["jaw"]),
}

summary = {
    "fixture": "ranger_ortho_v1",
    "method": "quality_jump_ranger_face_iso_v2",
    "production_accepted": False,
    "studio_default_flip": False,
    "full_export_preview_gate": "OPEN",
    "job": str(JOB),
    "out": str(OUT),
    "vis": str(VIS),
    "sha256": {
        "paint_color_untouched": post_base["paint_color"],
        "paint_pbr_untouched": post_base["paint_pbr"],
        "prior_hybrid_color_untouched": post_base["hybrid_color"],
        "prior_hybrid_pbr_untouched": post_base["hybrid_pbr"],
        "face_iso_v2_color": sha(FISO),
        "face_iso_v2_pbr_mr_retain": sha(FISO_PBR),
        "face_iso_v2_atlas": sha(OUT / "albedo_atlas_hybrid_a3_2K.png"),
    },
    "baseline_integrity": {k + "_unchanged": True for k in pre},
    "front_micro": {
        "chosen": micro.get("chosen"),
        "accepted": micro.get("accepted"),
        "reject_reason": micro.get("reject_reason"),
        "fallback_no_micro": micro.get("fallback_no_micro"),
        "weight_map": micro.get("weight_map"),
        "project_face": micro.get("project_face"),
        "iou_before": micro.get("iou_before"),
        "iou_after": micro.get("iou_after"),
        "extract": extract,
        "landmark_quality": micro.get("landmark_quality"),
        "no_forehead_eye_delta": float(extract.get("dy", 0)) >= 0 and float(extract.get("dx", 0)) > -20,
    },
    "laplacian": metrics,
    "cyan_collar_score": cyan,
    "views": [{"name": v["name"], "iou": v.get("silhouette_iou"), "w50": v.get("atlas_pixels_weight_above_half")} for v in rep["views"]],
    "mean_confidence": rep.get("mean_confidence"),
    "mr_retain_mode": rep.get("mr_retain_mode"),
    "git_head": "203f07aa76fde6c4971ba402213ea96759dc5543",
    "notes": [
        "face_iso extract preferred center-not-raw_tx (scale~1.044 raw_tx~-40); applied candidate dx=+6.82 dy=+11.65",
        "micro REJECTED iou_regression (0.90311->0.90084); weight_map=face_iso_paint_no_micro",
        "no forehead-eye symptom expected (dy>0); Zenko visual on angled sheets required",
        "prior hybrid + paint baselines preserved; production_accepted=false; Studio defaults OFF; export/preview gate OPEN",
    ],
}
(OUT / "ranger_face_iso_v2_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
(VIS / "ranger_face_iso_v2_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps({
    "sha12": {k: v[:12] for k, v in summary["sha256"].items()},
    "micro_accepted": micro.get("accepted"),
    "reject": micro.get("reject_reason"),
    "extract_dx_dy": (extract.get("dx"), extract.get("dy")),
    "chosen": extract.get("chosen"),
    "lap": metrics,
    "cyan": cyan,
    "vis": str(VIS),
}, indent=2))
