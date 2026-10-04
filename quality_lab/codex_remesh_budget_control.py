import trellis_bootstrap
import json,time
from pathlib import Path
import numpy as np,torch,cumesh,trimesh
root=Path('../quality_runs/trellis1536_native_remesh')
out=root/'budget500k';out.mkdir(exist_ok=False)
src=root/'remeshed.ply'; started=time.monotonic()
with src.open('rb') as f:
    nv=nf=0
    while True:
        line=f.readline().decode().strip()
        if line.startswith('element vertex'):nv=int(line.split()[-1])
        if line.startswith('element face'):nf=int(line.split()[-1])
        if line=='end_header':break
    offset=f.tell()
v=np.memmap(src,mode='r',dtype='<f4',offset=offset,shape=(nv,3))
f=np.memmap(src,mode='r',dtype=np.dtype([('n','u1'),('ids','<i4',(3,))]),offset=offset+nv*12,shape=(nf,))
assert np.all(f['n']==3)
scale=json.loads((root/'report.json').read_text())['native_to_meters']
native=np.array(v[:,[0,2,1]],copy=True);native[:,1]*=-1;native/=scale
cm=cumesh.CuMesh();cm.init(torch.from_numpy(native).cuda().contiguous(),torch.from_numpy(np.array(f['ids'])).cuda().contiguous())
print('simplifying500k',flush=True)
cm.simplify(500000,verbose=True);cm.compute_vertex_normals()
x,y=cm.read();n=cm.read_vertex_normals()
x=x.cpu().numpy()[:,[0,2,1]].copy();x[:,2]*=-1;x*=scale
n=n.cpu().numpy()[:,[0,2,1]].copy();n[:,2]*=-1
m=trimesh.Trimesh(x,y.cpu().numpy(),vertex_normals=n,process=False)
m.export(out/'candidate.glb',include_normals=True)
(out/'report.json').write_text(json.dumps(dict(triangles=len(m.faces),vertices=len(x),seconds=time.monotonic()-started,production_accepted=False),indent=2))
print('complete',len(m.faces),flush=True)
