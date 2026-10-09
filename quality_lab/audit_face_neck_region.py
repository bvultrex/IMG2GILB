"""CPU region-selection audit; no texture/model writes or learned model download.

GrabCut is a color/edge hypothesis, not semantic skin parsing. Inspect its output
before using it for projection, particularly for collars with skin-like colors.
"""
import argparse,json,hashlib
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

p=argparse.ArgumentParser()
p.add_argument('--projection',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--detection-resolution',type=int,default=2048,help='Raster resolution used by projection report; exported diagnostic images are downscaled')
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
report=json.loads((a.projection/'report.json').read_text())
front=next(v for v in report['views'] if v['name']=='front')
steps=front.get('align',{}).get('micro',{}).get('steps',[])
boxes=[s['dst_bbox'] for s in steps if s.get('mode')=='face_center_translation' and 'dst_bbox' in s]
if not boxes:
    (a.out/'report.json').write_text(json.dumps({'accepted':False,'reason':'no_confirmed_face'}))
    raise SystemExit(0)
rgba=np.array(Image.open(a.projection/'front_aligned.png').convert('RGBA'))
rgb=rgba[:,:,:3];h,w=rgb.shape[:2]
x0,y0,x1,y1=np.array(boxes[0])*np.array([w,h,w,h])/a.detection_resolution
fw=x1-x0;fh=y1-y0;cx=(x0+x1)/2
labels=np.full((h,w),cv2.GC_BGD,np.uint8)
left=max(0,int(x0-.35*fw));right=min(w,int(x1+.35*fw))
top=max(0,int(y0));bottom=min(h,int(y1+1.3*fh))
labels[top:bottom,left:right]=cv2.GC_PR_BGD
# Confirmed face plus narrow neck corridor are hypotheses, not hard foreground.
cv2.ellipse(labels,(int(cx),int((y0+y1)/2)),(int(.46*fw),int(.47*fh)),0,0,360,cv2.GC_PR_FGD,-1)
labels[int(y1-.15*fh):int(y1+.9*fh),int(cx-.22*fw):int(cx+.22*fw)]=cv2.GC_PR_FGD
# Two cheek seeds supply observed skin color without seeding hair or clothing.
for x in [cx-.24*fw,cx+.24*fw]:
    cv2.ellipse(labels,(int(x),int(y0+.65*fh)),(max(2,int(.07*fw)),max(2,int(.08*fh))),0,0,360,cv2.GC_FGD,-1)
labels[rgba[:,:,3]<128]=cv2.GC_BGD
cv2.setRNGSeed(0)
cv2.grabCut(cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR),labels,None,np.zeros((1,65)),np.zeros((1,65)),5,cv2.GC_INIT_WITH_MASK)
mask=np.isin(labels,[cv2.GC_FGD,cv2.GC_PR_FGD])
Image.fromarray((mask*255).astype('uint8')).save(a.out/'mask.png')
overlay=rgb.copy();overlay[mask]=(.6*rgb[mask]+.4*np.array([0,255,100])).astype('uint8')
Image.fromarray(overlay).crop((left,top,right,bottom)).save(a.out/'region_overlay.png')
(a.out/'report.json').write_text(json.dumps({'accepted':False,'scope':'diagnostic_only','algorithm':'deterministic_face_seeded_grabcut','selected_pixels':int(mask.sum()),'source_sha256':hashlib.sha256((a.projection/'front_aligned.png').read_bytes()).hexdigest(),'limitation':'Color segmentation may include similar-colored clothing; requires visual review'},indent=2))
