"""Isolated CPU reduction with explicit triangle budget and immutable source."""
import argparse
import hashlib
import json
import time
from pathlib import Path
import pymeshlab
import trimesh
import numpy as np

def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()

p = argparse.ArgumentParser()
p.add_argument('--source', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--triangles', type=int, default=100000)
a = p.parse_args()
assert a.triangles > 0
a.out.mkdir(parents=True, exist_ok=False)
report = {'source': str(a.source.resolve()), 'source_sha256': digest(a.source),
          'target_triangles': a.triangles, 'production_accepted': False}
def checkpoint(stage):
    report['stage'] = stage
    (a.out/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(stage, flush=True)
checkpoint('loading')
start = time.monotonic()
ms = pymeshlab.MeshSet()
ms.load_new_mesh(str(a.source))
report['input_vertices'] = ms.current_mesh().vertex_number()
report['input_triangles'] = ms.current_mesh().face_number()
checkpoint('reducing')
ms.meshing_decimation_quadric_edge_collapse(targetfacenum=a.triangles,
    preservenormal=True, optimalplacement=True, autoclean=True, qualitythr=1.0)
m = ms.current_mesh()
mesh = trimesh.Trimesh(m.vertex_matrix(), m.face_matrix(), process=False)
report.update(vertices=len(mesh.vertices), triangles=len(mesh.faces),
              bounds=mesh.bounds.tolist(), watertight=bool(mesh.is_watertight))
report['duplicate_faces'] = int(len(mesh.faces) - len(np.unique(np.sort(mesh.faces, axis=1), axis=0)))
report['quality_accepted'] = False
report['requires_independent_visual_review'] = True
checkpoint('exporting')
target = a.out/'candidate.glb'
mesh.export(target, include_normals=True)
report.update(output_sha256=digest(target), seconds=time.monotonic()-start,
              source_unchanged=digest(a.source)==report['source_sha256'])
assert report['source_unchanged']
checkpoint('complete')
