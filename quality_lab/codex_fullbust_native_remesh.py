"""Shape-only replay of upstream native-unit fill/remesh from saved 1536 latent."""
import trellis_bootstrap
from trellis_bootstrap import runtime
import gc, json, hashlib, time, traceback
from pathlib import Path
import torch, numpy as np, trimesh, cumesh
from trellis2 import models
from trellis2.modules.sparse import SparseTensor
from codex_splice_boundary_audit import audit

out=Path('../quality_runs/trellis1536_native_remesh');out.mkdir(parents=True,exist_ok=False)
latent=Path('../quality_runs/trellis_highgrid_bust/latent.pt')
report=dict(latent_sha256=hashlib.sha256(latent.read_bytes()).hexdigest(),stages=[],production_accepted=False)
started=time.monotonic()
def checkpoint(name,**kw):
    report['stages'].append(dict(stage=name,seconds=time.monotonic()-started,**kw))
    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(report['stages'][-1],flush=True)
def ply(path,v,f,scale):
    v=v.cpu().numpy()[:,[0,2,1]].copy();v[:,2]*=-1;v*=scale
    f=f.cpu().numpy().astype('<i4')
    with path.open('wb') as s:
        s.write(('ply\nformat binary_little_endian 1.0\nelement vertex %d\nproperty float x\nproperty float y\nproperty float z\nelement face %d\nproperty list uchar int vertex_indices\nend_header\n'%(len(v),len(f))).encode())
        s.write(v.astype('<f4').tobytes())
        for k in range(0,len(f),100000):
            chunk=f[k:k+100000]; packed=np.empty((len(chunk),13),np.uint8)
            packed[:,0]=3;packed[:,1:]=chunk.view(np.uint8).reshape(-1,12);s.write(packed.tobytes())
try:
    checkpoint('loading_decoder')
    cfg=json.loads((runtime/'models/trellis2/pipeline.json').read_text())['args']
    decoder=models.from_pretrained(str(runtime/'models/trellis2'/cfg['models']['shape_slat_decoder'])).eval().cuda()
    state=torch.load(latent,map_location='cpu',weights_only=True)
    decoder.set_resolution(state['resolution']);decoder.low_vram=True
    with torch.no_grad():
        meshes,_=decoder(SparseTensor(feats=state['feats'].cuda(),coords=state['coords'].cuda()),return_subs=True)
        v,f=meshes[0].vertices,meshes[0].faces
    del meshes,decoder,state;gc.collect();torch.cuda.empty_cache()
    scale=.4/float(v[:,2].max()-v[:,2].min());report['native_to_meters']=scale
    checkpoint('decoded',vertices=len(v),triangles=len(f),bounds=[v.amin(0).tolist(),v.amax(0).tolist()])
    cm=cumesh.CuMesh();cm.init(v.contiguous(),f.contiguous())
    cm.fill_holes(max_hole_perimeter=.03)
    v,f=cm.read();checkpoint('filled',vertices=len(v),triangles=len(f))
    ply(out/'filled.ply',v,f,scale)
    checkpoint('remeshing',resolution=1536,band=1,project_back=0)
    cm.init(*cumesh.remeshing.remesh_narrow_band_dc(v,f,center=torch.zeros(3,device='cuda'),scale=1539/1536,resolution=1536,band=1,project_back=0,verbose=True))
    v,f=cm.read();checkpoint('remeshed',vertices=len(v),triangles=len(f))
    ply(out/'remeshed.ply',v,f,scale)
    cm.simplify(100000,verbose=True);cm.compute_vertex_normals()
    v,f=cm.read();n=cm.read_vertex_normals()
    v=v.cpu().numpy()[:,[0,2,1]].copy();v[:,2]*=-1;v*=scale
    n=n.cpu().numpy()[:,[0,2,1]].copy();n[:,2]*=-1
    mesh=trimesh.Trimesh(v,f.cpu().numpy(),vertex_normals=n,process=False)
    mesh.export(out/'candidate.glb',include_normals=True)
    report['topology']=audit(mesh)
    report['latent_unchanged']=hashlib.sha256(latent.read_bytes()).hexdigest()==report['latent_sha256']
    assert report['latent_unchanged']
    checkpoint('complete',triangles=len(mesh.faces))
except Exception:
    report['error']=traceback.format_exc();checkpoint('failed');raise
