"""Replay upstream no-remesh geometry sequence in native decoder coordinates."""
import trellis_bootstrap
from trellis_bootstrap import runtime
import gc,json,hashlib
from pathlib import Path
import torch,numpy as np,trimesh,cumesh
from trellis2 import models
from trellis2.modules.sparse import SparseTensor
from codex_splice_boundary_audit import audit
out=Path('../quality_runs/headprobe_native_standard_eval');out.mkdir(parents=True,exist_ok=False)
latent=Path('D:/SF3D_QualityLab/bust_validation/shape_ablation/trellis1024_direct_headprobe_latent.pt')
cfg=json.loads((runtime/'models/trellis2/pipeline.json').read_text())['args']
print('Loading existing shape decoder and latent',flush=True)
decoder=models.from_pretrained(str(runtime/'models/trellis2'/cfg['models']['shape_slat_decoder'])).eval().cuda()
state=torch.load(latent,map_location='cpu',weights_only=True)
decoder.set_resolution(state['resolution']);decoder.low_vram=True
with torch.no_grad():
    slat=SparseTensor(feats=state['feats'].cuda(),coords=state['coords'].cuda())
    meshes,_=decoder(slat,return_subs=True)
    v,f=meshes[0].vertices,meshes[0].faces
del meshes,slat,decoder;gc.collect();torch.cuda.empty_cache()
report=dict(latent_sha256=hashlib.sha256(latent.read_bytes()).hexdigest(),native_bounds=[v.amin(0).tolist(),v.amax(0).tolist()],stages=[],production_accepted=False)
cm=cumesh.CuMesh();cm.init(v.contiguous(),f.contiguous())
def checkpoint(name):
    x,y=cm.read();report['stages'].append(dict(stage=name,vertices=len(x),triangles=len(y)))
    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report['stages'][-1],flush=True)
cm.fill_holes(max_hole_perimeter=.03);checkpoint('initial_fill')
for target in [300000,100000]:
    cm.simplify(target,verbose=False)
    cm.remove_duplicate_faces();cm.repair_non_manifold_edges()
    cm.remove_small_connected_components(1e-5);cm.fill_holes(max_hole_perimeter=.03)
    checkpoint(f'clean_{target}')
cm.unify_face_orientations();cm.compute_vertex_normals()
v,f=cm.read();n=cm.read_vertex_normals()
vertices=v.cpu().numpy()[:,[0,2,1]];vertices[:,2]*=-1
normals=n.cpu().numpy()[:,[0,2,1]];normals[:,2]*=-1
m=trimesh.Trimesh(vertices,f.cpu().numpy(),vertex_normals=normals,process=False)
scale=.4/m.extents[1];m.apply_scale(scale)
m.export(out/'candidate.glb',include_normals=True)
report.update(native_to_glb_scale=float(scale),topology=audit(m),scope='Upstream no-remesh geometry sequence only; not texture export or visual acceptance')
(out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)
