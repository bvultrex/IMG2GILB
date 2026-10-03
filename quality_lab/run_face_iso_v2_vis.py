"""Build face_iso_v2 SBS vs P2 (face + collar + chest + back emblem)."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
import cv2
import trimesh

sys.path.insert(0, r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\quality_lab")
from project_hybrid_a3 import ProjectionRender

JOB = Path(r"D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513")
VIS = Path(r"C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_face_iso_v2")
VIS.mkdir(parents=True, exist_ok=True)
OUT = JOB / "quality_jump_face_iso_v2"
V1 = JOB / "quality_jump_face_iso"

P2_COLOR = JOB / "quality_jump_phase2" / "textured_hybrid_phase2_vs_A0_color.glb"
V2_COLOR = OUT / "textured_hybrid_face_iso_v2_color.glb"
V1_COLOR = V1 / "textured_hybrid_face_iso_color.glb"
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
    "face_iso_v1_color": sha(V1_COLOR),
    "face_iso_v1_pbr": sha(V1 / "textured_hybrid_face_iso_pbr_mr_retain.glb"),
    "face_iso_v2_color": sha(V2_COLOR),
    "face_iso_v2_pbr": sha(OUT / "textured_hybrid_face_iso_v2_pbr_mr_retain.glb"),
    "face_iso_v2_atlas": sha(OUT / "hybrid_work" / "albedo_atlas_hybrid_a3_2K.png"),
}
assert post["p2"].lower() == pre["p2"].lower(), "P2 mutated"
assert post["a0a"].lower() == pre["a0a"].lower(), "A0 mutated"
assert post["p2b"].lower() == pre["p2b"].lower(), "P2B mutated"
assert post["face_iso_v1_color"].lower() == pre["face_iso_v1_color"].lower(), "v1 color mutated"
assert post["face_iso_v1_pbr"].lower() == pre["face_iso_v1_pbr"].lower(), "v1 pbr mutated"

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
print("render face_iso_v2...", flush=True)
v2 = render_flat(atlas_from_glb(V2_COLOR), azims)
print("render face_iso_v1...", flush=True)
v1 = render_flat(atlas_from_glb(V1_COLOR), azims)
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
    sheet_im = Image.new("RGB", (w, tiles[0].height + 28), (10, 10, 14))
    arr = np.array(sheet_im)
    cv2.putText(arr, title, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 210), 1, cv2.LINE_AA)
    sheet_im = Image.fromarray(arr)
    x = 0
    for t in tiles:
        sheet_im.paste(t, (x, 28))
        x += t.width + 12
    sheet_im.save(path)

# Primary SBS: A0 | P2 | face_iso_v1 (failed) | face_iso_v2
sheet([a0["front"], p2["front"], v1["front"], v2["front"]], ["A0", "P2", "face_iso_v1 FAIL", "face_iso_v2"], crops["face"], VIS / "sbs_face.png", "FACE  A0 | P2 | v1(bad tx) | v2(center)")
sheet([a0["front"], p2["front"], v1["front"], v2["front"]], ["A0", "P2", "v1", "v2"], crops["collar_necklace"], VIS / "sbs_collar_necklace.png", "COLLAR  A0 | P2 | v1 | v2")
sheet([a0["front"], p2["front"], v2["front"]], ["A0", "P2", "face_iso_v2"], crops["chest_cross"], VIS / "sbs_chest_cross.png", "CHEST  A0 | P2 | face_iso_v2")
sheet([a0["back"], p2["back"], v2["back"]], ["A0", "P2", "face_iso_v2"], crops["back_emblem"], VIS / "sbs_back_emblem.png", "BACK EMBLEM  A0 | P2 | face_iso_v2")

for label, _ in azims:
    sheet([a0[label], p2[label], v2[label]], ["A0", "P2", "v2"], (0, 0, 1024, 1024), VIS / f"sbs_angle_{label}_A0_P2_face_iso_v2.png", f"ANGLE {label}")

laps = {k: {"A0": lap(a0["front" if k != "back_emblem" else "back"], box),
            "P2": lap(p2["front" if k != "back_emblem" else "back"], box),
            "face_iso_v1": lap(v1["front" if k != "back_emblem" else "back"], box),
            "face_iso_v2": lap(v2["front" if k != "back_emblem" else "back"], box)}
        for k, box in crops.items()}

# emblem must not regress vs P2
emblem_ok = abs(laps["back_emblem"]["face_iso_v2"] - laps["back_emblem"]["P2"]) < 0.05

summary = {
    "method": "quality_jump_face_iso_v2",
    "production_accepted": False,
    "studio_default_flip": False,
    "sha256": post,
    "baseline_integrity": {
        "P2_unchanged": True,
        "A0_unchanged": True,
        "P2B_unchanged": True,
        "face_iso_v1_unchanged": True,
    },
    "front_micro": json.loads((OUT / "hybrid_work" / "report.json").read_text(encoding="utf-8"))["views"][0]["align"]["micro"],
    "laplacian": laps,
    "emblem_matches_p2": emblem_ok,
    "vis": str(VIS),
    "controls_verdict": json.loads((OUT / "controls" / "control_results.json").read_text(encoding="utf-8"))["verdict"],
}
(OUT / "face_iso_v2_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
(VIS / "face_iso_v2_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps({"emblem_ok": emblem_ok, "laplacian": laps, "vis": str(VIS), "sha_v2_color": post["face_iso_v2_color"]}, indent=2))
