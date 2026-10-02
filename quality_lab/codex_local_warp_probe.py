"""Diagnostic only: apply geometrically plausible local matches to saved previews."""
import argparse,json
from pathlib import Path
import cv2
import numpy as np
from codex_correspondence_geometry_audit import audit

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--matches',type=Path,required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=False);report=[]
for view in json.loads(a.matches.read_text())['results']:
 name=view['view'];pairs=view['pairs'];src=np.array([x['source'] for x in pairs],np.float32);dst=np.array([x['target'] for x in pairs],np.float32)
 image=cv2.imread(str(a.run/(name+'_aligned.png')));h,w=image.shape[:2]
 total=np.zeros_like(image,dtype=np.float32);coverage=np.zeros((h,w),np.float32);count=0
 for tri in audit(pairs)['triangles']:
  if not(tri['source_longest_edge']<=160 and tri['orientation_preserved'] and tri['min_scale']>=.5 and tri['max_scale']<=2):continue
  ids=tri['indices'];mask=np.zeros((h,w),np.uint8);cv2.fillConvexPoly(mask,np.round(dst[ids]).astype(np.int32),1)
  warped=cv2.warpAffine(image,cv2.getAffineTransform(src[ids],dst[ids]),(w,h))
  total+=warped*mask[:,:,None];coverage+=mask;count+=1
 # Multiple destination triangles can overlap despite individually positive Jacobians.
 valid=(coverage==1).astype(np.uint8)
 feather=np.clip(cv2.distanceTransform(valid,cv2.DIST_L2,5)/8.,0,1)
 result=np.clip(image*(1-feather[:,:,None])+total/np.maximum(coverage[:,:,None],1)*feather[:,:,None],0,255).astype(np.uint8)
 cv2.imwrite(str(a.out/(name+'_local_probe.png')),result)
 cv2.imwrite(str(a.out/(name+'_coverage.png')),valid*255)
 report.append({'view':name,'triangles':count,'single_coverage_pixels':int(valid.sum()),'overlap_pixels_rejected':int((coverage>1).sum())})
(a.out/'report.json').write_text(json.dumps({'results':report,'production_accepted':False,'scope':'2D saved-preview probe only; no GLB or source mutation; semantic correctness unproven'},indent=2))
print(json.dumps(report))
