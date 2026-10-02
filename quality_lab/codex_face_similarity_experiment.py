"""Isolated full-similarity candidate; retains production IoU/quality gates."""
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
import project_hybrid_a3 as hybrid

p=argparse.ArgumentParser();p.add_argument('--job',type=Path,required=True);a=p.parse_args()
job=a.job.resolve();out=job/'codex_face_similarity';out.mkdir(exist_ok=False)
original=hybrid.face_iso_extract_micro_delta
def similarity(matrix,**kwargs):
    fallback,meta=original(matrix,**kwargs)
    q=kwargs.get('landmark_meta') or {}
    scale=float(np.hypot(matrix[0,0],matrix[0,1]))
    angle=math.degrees(math.atan2(matrix[1,0],matrix[0,0]))
    dx=q.get('center_dx');dy=q.get('center_dy')
    if dx is not None and dy is not None and max(abs(dx),abs(dy))<=24 and .98<=scale<=1.02 and abs(angle)<=2:
        return matrix.copy(),{**meta,'chosen':'experimental_full_similarity','scale':scale,'rotation_degrees':angle,'raw_translation_preserved_with_linear_part':True}
    return fallback,meta
hybrid.face_iso_extract_micro_delta=similarity
baseline=job/'output.glb';before=hashlib.sha256(baseline.read_bytes()).hexdigest()
hybrid.run(job,out,None,None,color_glb=out/'candidate_color.glb',pbr_glb=out/'candidate_pbr.glb',source_pbr=job/'textured_pbr.glb',face_iso=True)
unchanged=before==hashlib.sha256(baseline.read_bytes()).hexdigest()
(out/'experiment.json').write_text(json.dumps({'baseline_sha256':before,'baseline_unchanged':unchanged,'iou_gate_unchanged':True,'production_accepted':False},indent=2))
assert unchanged
