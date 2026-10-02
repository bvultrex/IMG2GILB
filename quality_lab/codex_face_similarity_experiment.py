"""Isolated full-similarity candidate; retains production IoU/quality gates."""
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
import cv2
import project_hybrid_a3 as hybrid

p=argparse.ArgumentParser();p.add_argument('--job',type=Path,required=True);p.add_argument('--interior',action='store_true');p.add_argument('--out',type=Path);p.add_argument('--exclusive-face',action='store_true');a=p.parse_args()
job=a.job.resolve();out=a.out.resolve() if a.out else job/('codex_face_similarity_interior' if a.interior else 'codex_face_similarity');out.mkdir(parents=True,exist_ok=False)
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
if a.interior:
    original_warp=hybrid.apply_face_local_warp
    def interior_warp(image,*args,**kwargs):
        candidate=original_warp(image,*args,**kwargs)
        valid=((image[:,:,3]>=254)&(candidate[:,:,3]>=254)).astype(np.uint8)
        weight=np.clip(cv2.distanceTransform(valid,cv2.DIST_L2,5)/12.,0,1)[:,:,None]
        result=image.copy()
        result[:,:,:3]=np.clip(image[:,:,:3]*(1-weight)+candidate[:,:,:3]*weight,0,255).astype(np.uint8)
        assert np.array_equal(result[:,:,3],image[:,:,3])
        return result
    hybrid.apply_face_local_warp=interior_warp
    original_micro=hybrid.micro_align_front
    def audited_micro(image,rendered,*args,**kwargs):
        result=original_micro(image,rendered,*args,**kwargs)
        after=result[0]
        metadata=result[3]
        metadata['interior_alpha_preserved']=bool(np.array_equal(image[:,:,3],after[:,:,3]))
        q=hybrid.face_landmark_quality(after[:,:,:3].astype(np.float32)/255.,rendered[:,:,:3])
        metadata['post_warp_landmark_quality']={k:v for k,v in q.items() if k!='affine'}
        return result
    hybrid.micro_align_front=audited_micro
baseline=job/'output.glb';before=hashlib.sha256(baseline.read_bytes()).hexdigest()
hybrid.run(job,out,None,None,color_glb=out/'candidate_color.glb',pbr_glb=out/'candidate_pbr.glb',source_pbr=job/'textured_pbr.glb',face_iso=True,exclusive_face=a.exclusive_face)
unchanged=before==hashlib.sha256(baseline.read_bytes()).hexdigest()
(out/'experiment.json').write_text(json.dumps({'baseline_sha256':before,'baseline_unchanged':unchanged,'iou_gate_unchanged':True,'production_accepted':False},indent=2))
assert unchanged
