"""Isolated full-similarity candidate; retains production IoU/quality gates."""
import argparse,hashlib,json,math,sys,time
from pathlib import Path
import numpy as np
import cv2
import project_hybrid_a3 as hybrid
from face_transform_math import blend_valid_face_interior, gate_post_warp, no_detected_face

p=argparse.ArgumentParser();p.add_argument('--job',type=Path,required=True);p.add_argument('--interior',action='store_true');p.add_argument('--out',type=Path);p.add_argument('--exclusive-face',action='store_true');p.add_argument('--search-oblique',action='store_true');p.add_argument('--best-source',action='store_true');p.add_argument('--front-back-only',action='store_true');a=p.parse_args()
job=a.job.resolve();out=a.out.resolve() if a.out else job/('codex_face_similarity_interior' if a.interior else 'codex_face_similarity');out.mkdir(parents=True,exist_ok=False)
def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
provenance={
    'started_unix':time.time(),'argv':sys.argv[1:],
    'settings':{'interior':a.interior,'exclusive_face':a.exclusive_face,'face_iso':True,'search_oblique':a.search_oblique,'best_source':a.best_source,'front_back_only':a.front_back_only},
    'implementation_sha256':{Path(p).name:digest(p) for p in (
        __file__,hybrid.__file__,Path(__file__).with_name('face_transform_math.py'))},
    'input_sha256':{str(p.relative_to(job)):digest(p) for p in
        [job/'textured_pbr.glb',job/'output.glb',*sorted((job/'prepared').glob('*.png'))]},
    'production_accepted':False,'status':'running',
}
(out/'execution.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
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
        result=blend_valid_face_interior(image,candidate)
        assert np.array_equal(result[:,:,3],image[:,:,3])
        return result
    hybrid.apply_face_local_warp=interior_warp
    original_micro=hybrid.micro_align_front
    def audited_micro(image,rendered,*args,**kwargs):
        before_quality=hybrid.face_landmark_quality(image[:,:,:3].astype(np.float32)/255.,rendered[:,:,:3])
        if no_detected_face(before_quality):
            iou=hybrid.silhouette_iou(image[:,:,3]>127,rendered[:,:,3]>.5)
            return image,args[0],float(iou),{
                'accepted':False,'project_face':False,'skipped':'no_detected_face',
                'landmark_quality':before_quality,'interior_alpha_preserved':True,
                'weight_map':'none_keep_object_projection'},None
        result=original_micro(image,rendered,*args,**kwargs)
        after=result[0]
        metadata=result[3]
        metadata['interior_alpha_preserved']=bool(np.array_equal(image[:,:,3],after[:,:,3]))
        q=hybrid.face_landmark_quality(after[:,:,:3].astype(np.float32)/255.,rendered[:,:,:3])
        return gate_post_warp(result, q, hybrid.face_iso_weight_map)
    hybrid.micro_align_front=audited_micro
baseline=job/'output.glb';before=hashlib.sha256(baseline.read_bytes()).hexdigest()
hybrid.run(job,out,None,None,color_glb=out/'candidate_color.glb',pbr_glb=out/'candidate_pbr.glb',source_pbr=job/'textured_pbr.glb',face_iso=True,exclusive_face=a.exclusive_face,search_oblique=a.search_oblique,best_source=a.best_source,front_back_only=a.front_back_only)
unchanged=before==hashlib.sha256(baseline.read_bytes()).hexdigest()
(out/'experiment.json').write_text(json.dumps({'baseline_sha256':before,'baseline_unchanged':unchanged,'iou_gate_unchanged':True,'production_accepted':False},indent=2))
assert unchanged
provenance.update(status='complete',finished_unix=time.time(),baseline_unchanged=unchanged,
                  output_sha256={p.name:digest(p) for p in out.glob('candidate_*.glb')})
(out/'execution.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
