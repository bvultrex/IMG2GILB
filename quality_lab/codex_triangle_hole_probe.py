"""Diagnostic fill of isolated triangular boundary loops; no vertex movement."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh
from codex_splice_boundary_audit import audit

p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
sha=hashlib.sha256(a.source.read_bytes()).hexdigest()
m=trimesh.load(a.source,force='mesh',process=False)
before=audit(m); vertices=m.vertices.copy(); faces=m.faces.copy()
assert before['boundary_edges']==3*before['closed_simple_loops']
assert before['boundary_components']==before['closed_simple_loops']
trimesh.repair.fill_holes(m)
assert np.array_equal(vertices,m.vertices)
assert np.array_equal(faces,m.faces[:len(faces)])
added=m.faces[len(faces):]
duplicate_count=len(m.faces)-len(np.unique(np.sort(m.faces,axis=1),axis=0))
area=trimesh.triangles.area(m.vertices[added])
m.export(a.out/'candidate.glb')
report=dict(source_sha256=sha,before=before,after=audit(m),
            duplicate_faces_after_fill=duplicate_count,
            rejected=bool(duplicate_count),
            added_triangles=len(added),added_area_m2=float(area.sum()),
            max_added_triangle_area_m2=float(area.max()) if len(area) else 0,
            original_vertices_and_faces_unchanged=True,production_accepted=False,
            scope='Small-loop diagnostic only; nonmanifold intersections and detail fidelity remain separate gates')
assert hashlib.sha256(a.source.read_bytes()).hexdigest()==sha
(a.out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
