"""Simplify ranger ortho_v2 TRELLIS GLB."""
import trellis_bootstrap
import argparse, json, time
from pathlib import Path
import torch, trimesh, numpy as np, cumesh

p = argparse.ArgumentParser()
p.add_argument('tag')
p.add_argument('--triangles', type=int, default=100000)
p.add_argument('--root', type=Path, default=Path(r'D:\SF3D_QualityLab\ranger_validation\ortho_v2'))
args = p.parse_args()
root = args.root
src = root / f'{args.tag}.glb'
dest = root / f'{args.tag}_{args.triangles}.glb'
assert src != dest
m = trimesh.load(src, force='mesh', process=False)
start = time.monotonic()
cm = cumesh.CuMesh()
cm.init(
    torch.tensor(np.asarray(m.vertices), dtype=torch.float32, device='cuda').contiguous(),
    torch.tensor(np.asarray(m.faces), dtype=torch.int32, device='cuda').contiguous(),
)
cm.remove_duplicate_faces(); cm.repair_non_manifold_edges(); cm.unify_face_orientations()
cm.simplify(args.triangles, verbose=True)
cm.remove_duplicate_faces(); cm.unify_face_orientations(); cm.compute_vertex_normals()
v, f = cm.read(); n = cm.read_vertex_normals()
m = trimesh.Trimesh(v.cpu().numpy(), f.cpu().numpy(), vertex_normals=n.cpu().numpy(), process=False)
assert np.isfinite(m.vertices).all()
m.apply_scale(0.4 / m.extents[1])
m.visual = trimesh.visual.TextureVisuals(
    material=trimesh.visual.material.PBRMaterial(baseColorFactor=[190,195,204,255], metallicFactor=0., roughnessFactor=.8)
)
m.export(dest)
report = dict(source=str(src), output=str(dest), triangles=len(m.faces), vertices=len(m.vertices),
              height_cm=float(m.extents[1]*100), seconds=time.monotonic()-start, watertight=bool(m.is_watertight))
dest.with_suffix('.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report), flush=True)