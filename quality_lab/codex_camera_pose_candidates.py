"""Render fixed-mesh camera hypotheses for semantic ranking; no texture changes."""
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image
import trimesh
from project_hybrid_a3 import ProjectionRender,load_rgba,bbox_matrix,warp_rgba,silhouette_iou
p=argparse.ArgumentParser();p.add_argument('--job',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=False);size=1024
data=np.load(a.job/'controls/uv_mesh.npz')
mesh=trimesh.Trimesh(vertices=data['vertices'],faces=data['faces'],process=False,visual=trimesh.visual.TextureVisuals(uv=data['uv']))
mesh.vertex_normals=data['vertex_normals']
renderer=ProjectionRender(default_resolution=size,texture_size=2048);renderer.load_mesh(mesh)
renderer.set_texture(np.asarray(Image.open(a.job/'paint/albedo_atlas_2K.png').convert('RGB'),np.float32)/255.)
rows=[]
for view,angles in [('right',[30,45,60,75,90]),('left',[270,285,300,315,330])]:
 rgba=load_rgba(a.job/'prepared'/f'{view}.png',size)
 for angle in angles:
  rendered=renderer.render(0.,float(angle),return_type='np');target=rendered[:,:,3]>.5
  matrix=bbox_matrix(rgba[:,:,3]>127,target);aligned=warp_rgba(rgba,matrix,size)
  key=f'{view}_{angle}';folder=a.out/key;folder.mkdir()
  Image.fromarray(aligned).save(folder/'source.png')
  Image.fromarray((rendered.clip(0,1)*255).astype(np.uint8)).save(folder/'target.png')
  rows.append({'key':key,'view':view,'azim':angle,'bbox_iou':silhouette_iou(aligned[:,:,3]>127,target),'matrix':matrix.tolist()})
  print(key,flush=True)
(a.out/'manifest.json').write_text(json.dumps({'candidates':rows,'production_accepted':False,'scope':'Fixed geometry, bbox alignment only, camera ranking input'},indent=2))
