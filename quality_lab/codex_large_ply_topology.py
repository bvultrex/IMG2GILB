"""Count indexed edge incidence on saved large PLY stages, no geometry edits."""
import trellis_bootstrap
import gc,json,time
from pathlib import Path
import numpy as np,torch
root=Path('../quality_runs/trellis1536_native_remesh')
reports=[]
for name in ['filled.ply','remeshed.ply']:
    start=time.monotonic();src=root/name
    with src.open('rb') as stream:
        while True:
            line=stream.readline().decode().strip()
            if line.startswith('element vertex'):nv=int(line.split()[-1])
            if line.startswith('element face'):nf=int(line.split()[-1])
            if line=='end_header':break
        offset=stream.tell()
    data=np.memmap(src,mode='r',dtype=np.dtype([('n','u1'),('ids','<i4',(3,))]),offset=offset+nv*12,shape=(nf,))
    faces=torch.from_numpy(np.array(data['ids'])).cuda().long()
    edges=[]
    for a,b in [(0,1),(1,2),(2,0)]:
        lo=torch.minimum(faces[:,a],faces[:,b]);hi=torch.maximum(faces[:,a],faces[:,b])
        edges.append(lo*nv+hi)
    del faces,lo,hi
    all_edges=torch.cat(edges);del edges;gc.collect();torch.cuda.empty_cache()
    _,counts=torch.unique(all_edges,return_counts=True);del all_edges
    r=dict(stage=name,triangles=nf,vertices=nv,indexed_boundary_edges=int((counts==1).sum()),indexed_nonmanifold_edges=int((counts>2).sum()),max_incidence=int(counts.max()),seconds=time.monotonic()-start)
    reports.append(r);print(r,flush=True)
    (root/'large_stage_topology.json').write_text(json.dumps(reports,indent=2))
    del counts,_;gc.collect();torch.cuda.empty_cache()
