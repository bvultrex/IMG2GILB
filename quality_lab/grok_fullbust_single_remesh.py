"""Single-geometry full-bust remesh. Not a splice. Does not weld, does not touch failed patch outputs."""
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
import trimesh
import cumesh

source = Path(r"D:\SF3D_QualityLab\bust_validation\shape_ablation\trellis1024_direct.glb")
out = Path(r"C:\Users\Shadow\Documents\ComfyUI\quality_runs\fullbust_direct_remesh512")
out.mkdir(parents=True, exist_ok=False)
forbidden = {
    "ec9fb88b34be40a95d3f7b554ce92f7c4e9014dd55f424e5857567f98b66a7dc",
    "e191f9b8e3f0b874c2a92ba92f7ca1b68bd4d4ef393c7a7a165e64829cfd3783",
}
sha = hashlib.sha256(source.read_bytes()).hexdigest()
assert sha not in forbidden, sha
assert "headprobe" not in source.name
mesh = trimesh.load(source, force="mesh", process=False)
assert isinstance(mesh, trimesh.Trimesh)
v = torch.tensor(np.asarray(mesh.vertices), dtype=torch.float32, device="cuda").contiguous()
f = torch.tensor(np.asarray(mesh.faces), dtype=torch.int32, device="cuda").contiguous()
raw_faces = int(len(f))
del mesh
cm = cumesh.CuMesh()
cm.init(v, f)
del v, f
cm.remove_duplicate_faces()
cm.repair_non_manifold_edges()
cm.unify_face_orientations()
v, f = cm.read()
lo, hi = v.amin(0), v.amax(0)
v, f = cumesh.remeshing.remesh_narrow_band_dc(
    v, f,
    center=(lo + hi) / 2,
    scale=float((hi - lo).max()) * 515 / 512,
    resolution=512,
    band=1,
    project_back=0,
    verbose=True,
)
cm.init(v, f)
del v, f
cm.simplify(100000, verbose=True)
cm.remove_duplicate_faces()
cm.unify_face_orientations()
cm.compute_vertex_normals()
v, f = cm.read()
n = cm.read_vertex_normals()
candidate = trimesh.Trimesh(
    v.cpu().numpy(), f.cpu().numpy(), vertex_normals=n.cpu().numpy(), process=False
)
assert np.isfinite(candidate.vertices).all()
candidate.apply_scale(0.4 / candidate.extents[1])
parts = candidate.split(only_watertight=False)
dest = out / "fullbust_direct_remesh512.glb"
candidate.export(dest)
out_sha = hashlib.sha256(dest.read_bytes()).hexdigest()
src_after = hashlib.sha256(source.read_bytes()).hexdigest()
report = {
    "method": "existing TRELLIS.2 whole-object direct-1024 decode plus CuMesh remesh512/100k",
    "splice": False,
    "weld": False,
    "texture": False,
    "production_accepted": False,
    "studio_defaults": "off",
    "source": str(source),
    "source_sha256": sha,
    "source_unchanged": src_after == sha,
    "raw_triangles": raw_faces,
    "output": str(dest),
    "output_sha256": out_sha,
    "triangles": int(len(candidate.faces)),
    "vertices": int(len(candidate.vertices)),
    "components": int(len(parts)),
    "watertight": bool(candidate.is_watertight),
    "height_m": float(candidate.extents[1]),
    "not_reused": [
        "headprobe_coherent_patch_hal",
        "headprobe_tighter_seam",
        "ec9fb88b native no-remesh",
    ],
}
assert report["source_unchanged"]
(out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report), flush=True)
