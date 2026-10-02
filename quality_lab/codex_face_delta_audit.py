"""Compare applied translation with fitted similarity on saved alignment landmarks."""
import argparse,json
from pathlib import Path
import cv2
import numpy as np
import project_hybrid_a3 as hybrid

p=argparse.ArgumentParser()
p.add_argument('--run',type=Path,required=True)
a=p.parse_args()
report=json.loads((a.run/'report.json').read_text())
front=next(v for v in report['views'] if v['name']=='front')
micro=front['align']['micro']
src=cv2.imread(str(a.run/'front_aligned.png'))
dst=cv2.imread(str(a.run/'front_baseline.png'))
sk,_=hybrid._try_anime_face_keypoints(src)
dk,_=hybrid._try_anime_face_keypoints(dst)
assert sk is not None and dk is not None
n=min(len(sk),len(dk));sk=sk[:n];dk=dk[:n]
M,inliers=cv2.estimateAffinePartial2D(sk,dk,method=cv2.RANSAC,ransacReprojThreshold=2.5)
assert M is not None
delta=np.array([micro['extract']['dx'],micro['extract']['dy']])*src.shape[0]/2048
pred=(M@np.column_stack([sk,np.ones(n)]).T).T
metrics={}
for name,points in [('unchanged',sk),('applied_center_translation',sk+delta),('fitted_similarity',pred)]:
    error=np.linalg.norm(points-dk,axis=1)
    metrics[name]={'median_px':float(np.median(error)),'p90_px':float(np.percentile(error,90))}
result={'scope':'Saved 1024px diagnostic images; all detected correspondences, not independent ground truth',
        'landmarks':n,'delta_1024':delta.tolist(),'similarity_1024':M.tolist(),'metrics':metrics,
        'limitation':'Detector correspondence may be wrong; visual and final-GLB checks remain required.'}
(a.run/'applied_delta_audit.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
