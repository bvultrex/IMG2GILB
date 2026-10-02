"""Read-only SIFT correspondence feasibility; never applies a geometric warp."""
import argparse,json
from pathlib import Path
import cv2
import numpy as np

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);reports=[]
 for view in ('left','right'):
  src=cv2.imread(str(a.run/(view+'_aligned.png')))
  dst=cv2.imread(str(a.run/(view+'_baseline.png')))
  if src is None or dst is None:raise ValueError('Missing diagnostic view '+view)
  sift=cv2.SIFT_create(nfeatures=4000)
  def features(im):
   mask=(im.max(axis=2)>15).astype(np.uint8)*255
   return sift.detectAndCompute(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY),mask)
  sk,sd=features(src);dk,dd=features(dst)
  matches=[]
  if sd is not None and dd is not None and min(len(sd),len(dd))>=2:
   bf=cv2.BFMatcher()
   def ratio(x,y):
    return {m.queryIdx:m for pair in bf.knnMatch(x,y,k=2) if len(pair)==2 for m,n in [pair] if m.distance<.75*n.distance}
   forward,reverse=ratio(sd,dd),ratio(dd,sd)
   matches=[m for i,m in forward.items() if m.trainIdx in reverse and reverse[m.trainIdx].trainIdx==i]
  pairs=[{'source':list(sk[m.queryIdx].pt),'target':list(dk[m.trainIdx].pt),'distance':float(m.distance)} for m in matches]
  shifts=[float(np.linalg.norm(np.array(x['source'])-x['target'])) for x in pairs]
  bands=[sum(int(x['source'][1]/src.shape[0]*4)==i for x in pairs) for i in range(4)]
  reports.append({'view':view,'source_keypoints':len(sk),'target_keypoints':len(dk),'mutual_ratio_matches':len(matches),
                  'source_vertical_quarter_counts':bands,'median_displacement_px':float(np.median(shifts)) if shifts else None,'pairs':pairs})
  drawn=cv2.drawMatches(src,sk,dst,dk,matches,None,flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
  cv2.imwrite(str(a.out/(view+'_matches.png')),drawn)
 (a.out/'report.json').write_text(json.dumps({'results':reports,'production_accepted':False,'limitations':'Descriptor matches are hypotheses; no semantic correctness, warp or camera acceptance established.'},indent=2))
 print(json.dumps([{k:v for k,v in r.items() if k!='pairs'} for r in reports],indent=2))
if __name__=='__main__':main()
