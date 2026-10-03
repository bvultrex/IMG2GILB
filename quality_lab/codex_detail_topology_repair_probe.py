"""Isolated post-remesh repair probe; preserves inputs and reports geometry loss."""
import trellis_bootstrap
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
import trimesh
import cumesh
from scipy.spatial import cKDTree
from codex_splice_boundary_audit import audit

p = argparse.ArgumentParser()
p.add_argument('--source', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
sha = hashlib.sha256(a.source.read_bytes()).hexdigest()
m = trimesh.load(a.source, force='mesh', process=False)
before = audit(m)
cm = cumesh.CuMesh()
cm.init(torch.tensor(np.asarray(m.vertices), dtype=torch.float32, device='cuda').contiguous(),
        torch.tensor(np.asarray(m.faces), dtype=torch.int32, device='cuda').contiguous())
cm.remove_duplicate_faces()
cm.repair_non_manifold_edges()
cm.unify_face_orientations()
v, f = cm.read()
candidate = trimesh.Trimesh(v.cpu().numpy(), f.cpu().numpy(), process=False)
candidate.export(a.out/'candidate.glb')
dist, _ = cKDTree(m.vertices).query(candidate.vertices)
report = dict(source=str(a.source.resolve()), source_sha256=sha, before=before,
              after=audit(candidate), triangles_removed=len(m.faces)-len(candidate.faces),
              max_candidate_vertex_distance_to_source=float(dist.max()),
              production_accepted=False,
              scope='Topology repair only; no remesh, no simplification, no shape or seam acceptance')
assert hashlib.sha256(a.source.read_bytes()).hexdigest() == sha
(a.out/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
