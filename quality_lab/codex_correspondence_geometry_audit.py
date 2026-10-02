"""Diagnose local foldovers in candidate matches; does not approve or apply warps."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.spatial import Delaunay

def audit(pairs):
 src=np.array([p['source'] for p in pairs],float)
 dst=np.array([p['target'] for p in pairs],float)
 rows=[]
 for ids in Delaunay(src).simplices:
  a,b=src[ids],dst[ids]
  x=(a[1:]-a[0]).T;y=(b[1:]-b[0]).T
  determinant=float(np.linalg.det(x))
  if abs(determinant)<1e-8:continue
  transform=y@np.linalg.inv(x)
  sv=np.linalg.svd(transform,compute_uv=False)
  longest=float(max(np.linalg.norm(a[i]-a[j]) for i in range(3) for j in range(i)))
  rows.append({'indices':ids.tolist(),'source_longest_edge':longest,
               'orientation_preserved':bool(np.linalg.det(transform)>0),
               'min_scale':float(sv.min()),'max_scale':float(sv.max())})
 local=[r for r in rows if r['source_longest_edge']<=160]
 plausible=[r for r in local if r['orientation_preserved'] and r['min_scale']>=.5 and r['max_scale']<=2]
 return {'triangles':rows,'local_triangles':len(local),'local_foldovers':sum(not r['orientation_preserved'] for r in local),
         'locally_plausible':len(plausible),'limitations':'Geometric plausibility is necessary, not semantic or visibility proof.'}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--matches',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 data=json.loads(a.matches.read_text());results=[]
 for view in data['results']:
  r={'view':view['view'],**audit(view['pairs'])};results.append(r)
  print(json.dumps({k:v for k,v in r.items() if k!='triangles'}))
 with a.out.open('x') as f:json.dump({'results':results,'production_accepted':False,'diagnostic_limits':{'max_edge':160,'min_scale':.5,'max_scale':2}},f,indent=2)
