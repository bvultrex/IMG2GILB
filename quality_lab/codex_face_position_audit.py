"""Measure actual saved feature positions, without fitting away placement error."""
import argparse,json
from pathlib import Path
import cv2
import numpy as np
import project_hybrid_a3 as hybrid
from face_transform_math import face_feature_indices

p=argparse.ArgumentParser()
for name in ('before','after','target','out'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args()
points={}
for name in ('before','after','target'):
    image=cv2.imread(str(getattr(a,name)))
    assert image is not None
    keypoints,_=hybrid._try_anime_face_keypoints(image)
    assert keypoints is not None
    points[name]=keypoints
n=min(map(len,points.values()));ids=face_feature_indices(n)
result={'scope':'Direct detector correspondence distances in saved image pixels; no refitted transform; not human ground truth',
        'indices':ids,'metrics':{}}
for name in ('before','after'):
    distances=np.linalg.norm(points[name][ids]-points['target'][ids],axis=1)
    result['metrics'][name]={'median_px':float(np.median(distances)),'p90_px':float(np.percentile(distances,90)),'per_point_px':distances.tolist()}
a.out.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
