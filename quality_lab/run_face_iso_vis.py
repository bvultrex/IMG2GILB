"""Build face-iso SBS vs P2 (face + chest + back emblem) and verify baselines."""
from __future__ import annotations
import hashlib, json, shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
import torch
import trimesh
import sys
sys.path.insert(0, r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\quality_lab")
from project_hybrid_a3 import ProjectionRender

JOB = Path(r"D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513")
VIS = Path(r"C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_face_iso")
VIS.mkdir(parents=True, exist_ok=True)
OUT = JOB / "quality_jump_face_iso"

P2_COLOR = JOB / "quality_jump_phase2" / "textured_hybrid_phase2_vs_A0_color.glb"
FACE_COLOR = OUT / "textured_hybrid_face_iso_color.glb"
A0_ATLAS = JOB / "quality_jump_phase1" / "A0_single_pil" / "albedo_atlas_2K.png"
P2B_COLOR = JOB / "quality_jump_phase2b" / "textured_hybrid_phase2b_color.glb"
UV = JOB / "controls" / "uv_mesh.npz"

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

pre = json.loads((OUT / "pre_hashes.json").read_text(encoding="utf-8"))
post = {
    "p2": sha(P2_COLOR),
    "a0a": sha(A0_ATLAS),
    "p2b": sha(P2B_COLOR),
    "face_iso_color": sha(FACE_COLOR),
    "face_iso_pbr": sha(OUT / "textured_hybrid_face_iso_pbr_mr_retain.glb"),
    "face_iso_atlas": sha(OUT / "hybrid_work" / "albedo_atlas_hybrid_a3_2K.png"),
}
assert post["p2"].lower() == pre["p2"].lower(), "P2 baseline mutated!"
assert post["a0a"].lower() == pre["a0a"].lower(), "A0 atlas mutated!"
assert post["p2b"].lower() == pre["p2b"].lower(), "P2B mutated!"

# Load mesh once
data = np.load(UV)
mesh = trimesh.Trimesh(vertices=data["vertices"], faces=data["faces"], process=False, visual=trimesh.visual.TextureVisuals(uv=data["uv"]))
mesh.vertex_normals = data["vertex_normals"]

def atlas_from_glb(glb: Path) -> np.ndarray:
    scene = trimesh.load(str(glb), force="scene", process=False)
    m = list(scene.geometry.values())[0]
    tex = m.visual.material.baseColorTexture
    return np.asarray(tex.convert("RGB"), dtype=np.float32) / 255.0

def render_flat(atlas: np.ndarray, azims):
    r = ProjectionRender(default_resolution=2048, texture_size=2048)
    r.load_mesh(mesh)
    r.set_texture(atlas)
    out = {}
    for label, ang in azims:
        im = r.render(0, ang, return_type="np")
        out[label] = Image.fromarray((im.clip(0, 1) * 255).astype(np.uint8)).resize((1024, 1024))
    return out

azims = [("front", 0), ("back", 180), ("p35", 35), ("m35", -35)]
print("render P2...", flush=True)
p2 = render_flat(atlas_from_glb(P2_COLOR), azims)
print("render face_iso...", flush=True)
fi = render_flat(atlas_from_glb(FACE_COLOR), azims)
# A0 from atlas
a0 = render_flat(np.asarray(Image.open(A0_ATLAS).convert("RGB"), dtype=np.float32) / 255.0, azims)

crops = {
    "face": (400, 50, 624, 300),
    "chest_cross": (370, 300, 654, 520),
    "back_emblem": (360, 220, 664, 480),
    "collar_necklace": (360, 240, 664, 430),
}

def lap(im: Image.Image, box):
    g = cv2.cvtColor(np.array(im.crop(box).convert("RGB")), cv2.COLOR_RGB2GRAY).astype(np.float32)
    return float(np.mean(np.abs(cv2.Laplacian(g, cv2.CV_32F))))

def sheet(ims, labels, box, path, title):
    tiles = []
    for im, lab in zip(ims, labels):
        c = im.crop(box).resize((384, 384), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (384, 416), (18, 18, 22))
        canvas.paste(c, (0, 32))
        arr = np.array(canvas)
        arr[:32] = (36, 36, 44)
        cv2.putText(arr, lab, (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (230, 230, 235), 1, cv2.LINE_AA)
        tiles.append(Image.fromarray(arr))
    w = sum(t.width for t in tiles) + 12 * (len(tiles) - 1)
    sheet = Image.new("RGB", (w, tiles[0].height + 28), (10, 10, 14))
    arr = np.array(sheet)
    cv2.putText(arr, title, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 210), 1, cv2.LINE_AA)
    sheet = Image.fromarray(arr)
    x = 0
    for t in tiles:
        sheet.paste(t, (x, 28))
        x += t.width + 12
    sheet.save(path)

metrics = {}
for name, box in crops.items():
    src = "back" if name == "back_emblem" else "front"
    sheet([a0[src], p2[src], fi[src]], ["A0", "P2", "face_iso"], box, VIS / f"sbs_{name}.png", f"face_iso vs P2 — {name}")
    metrics[name] = {"A0": lap(a0[src], box), "P2": lap(p2[src], box), "face_iso": lap(fi[src], box)}
    a0[src].crop(box).save(VIS / f"crop_A0_{name}.png")
    p2[src].crop(box).save(VIS / f"crop_P2_{name}.png")
    fi[src].crop(box).save(VIS / f"crop_face_iso_{name}.png")

for label in ("front", "back", "p35", "m35"):
    sheet([a0[label], p2[label], fi[label]], ["A0", "P2", "face_iso"], (256, 0, 768, 1024), VIS / f"sbs_angle_{label}_A0_P2_face_iso.png", f"angle {label}")
    fi[label].save(VIS / f"face_iso_{label}.png")
    p2[label].save(VIS / f"P2_{label}.png")

report = json.loads((OUT / "hybrid_work" / "report.json").read_text(encoding="utf-8"))
summary = {
    "method": "quality_jump_face_iso",
    "production_accepted": False,
    "studio_default_flip": False,
    "sha256": post,
    "baseline_integrity": {
        "P2_unchanged": post["p2"].lower() == pre["p2"].lower(),
        "A0_unchanged": post["a0a"].lower() == pre["a0a"].lower(),
        "P2B_unchanged": post["p2b"].lower() == pre["p2b"].lower(),
    },
    "front_micro": report["views"][0]["align"].get("micro"),
    "mean_confidence": report["mean_confidence"],
    "laplacian": metrics,
    "vis_dir": str(VIS),
    "artifacts": {
        "color_glb": str(FACE_COLOR),
        "pbr_glb": str(OUT / "textured_hybrid_face_iso_pbr_mr_retain.glb"),
        "atlas": str(OUT / "hybrid_work" / "albedo_atlas_hybrid_a3_2K.png"),
    },
    "notes": [
        "P2 incidence retained (not Phase2b steeper falloff)",
        "Coherent face source via landmark gate (project-all or paint-all; no mid-face mix)",
        "Torso/back projection unchanged vs P2 settings",
    ],
}
(OUT / "face_iso_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
(VIS / "face_iso_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps({"sha12": {k: v[:12] for k,v in post.items()}, "lap": metrics, "project_face": summary["front_micro"].get("project_face"), "weight_map": summary["front_micro"].get("weight_map")}, indent=2))
