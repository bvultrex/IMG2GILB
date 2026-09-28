import trellis_bootstrap
import argparse,json,time
from pathlib import Path
import torch,trimesh,numpy as np,cumesh
p=argparse.ArgumentParser();p.add_argument('tag');p.add_argument('--triangles',type=int,default=100000);p.add_argument('--remesh',type=int,choices=[512,1024]);args=p.parse_args()
root=Path(r'D:\SF3D_QualityLab\bust_validation\shape_ablation');src=root/f'{args.tag}.glb';dest=root/f'{args.tag}_{args.triangles}{"_remesh"+str(args.remesh) if args.remesh else ""}.glb';assert src!=dest
m=trimesh.load(src,force='mesh',process=False);start=time.monotonic();cm=cumesh.CuMesh();cm.init(torch.tensor(np.asarray(m.vertices),dtype=torch.float32,device='cuda').contiguous(),torch.tensor(np.asarray(m.faces),dtype=torch.int32,device='cuda').contiguous())
cm.remove_duplicate_faces();cm.repair_non_manifold_edges();cm.unify_face_orientations()
if args.remesh:
 v,f=cm.read();lo=v.amin(0);hi=v.amax(0)
 cm.init(*cumesh.remeshing.remesh_narrow_band_dc(v,f,center=(lo+hi)/2,scale=float((hi-lo).max())*(args.remesh+3)/args.remesh,resolution=args.remesh,band=1,project_back=0,verbose=True))
cm.simplify(args.triangles,verbose=True);cm.remove_duplicate_faces();cm.unify_face_orientations();cm.compute_vertex_normals();v,f=cm.read();n=cm.read_vertex_normals()
m=trimesh.Trimesh(v.cpu().numpy(),f.cpu().numpy(),vertex_normals=n.cpu().numpy(),process=False);assert np.isfinite(m.vertices).all();m.apply_scale(.4/m.extents[1]);m.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=[190,195,204,255],metallicFactor=0.,roughnessFactor=.8));m.export(dest)
report=dict(source=str(src),output=str(dest),remesh_resolution=args.remesh,triangles=len(m.faces),vertices=len(m.vertices),height_cm=float(m.extents[1]*100),seconds=time.monotonic()-start,watertight=bool(m.is_watertight));dest.with_suffix('.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
