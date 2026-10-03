"""Experimental corner connectivity repair. Never moves triangle coordinates."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import trimesh
from codex_splice_boundary_audit import audit

p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
sha=hashlib.sha256(a.source.read_bytes()).hexdigest()
m=trimesh.load(a.source,force='mesh',process=False)
f=np.asarray(m.faces); normals=m.vertex_normals.copy()
parent=np.arange(f.size)
def root(i):
    while parent[i]!=i:
        parent[i]=parent[parent[i]];i=parent[i]
    return i
def join(i,j):
    parent[root(i)]=root(j)
edges=np.sort(m.edges,axis=1)
_,inv,counts=np.unique(edges,axis=0,return_inverse=True,return_counts=True)
order=np.argsort(inv,kind='stable'); offsets=np.r_[0,np.cumsum(counts)]
choices=[]
for ei,count in enumerate(counts):
    entries=order[offsets[ei]:offsets[ei+1]]
    if count==2: pairs=[(entries[0],entries[1])]
    elif count==4:
        options=[]
        for pattern in [((0,1),(2,3)),((0,2),(1,3)),((0,3),(1,2))]:
            pairs=[(entries[x],entries[y]) for x,y in pattern]
            if not all(np.array_equal(m.edges[x],m.edges[y][::-1]) for x,y in pairs):continue
            score=sum(float(m.face_normals[m.edges_face[x]]@m.face_normals[m.edges_face[y]]) for x,y in pairs)
            options.append((score,pairs))
        if not options:raise ValueError('No orientation-consistent pairing')
        score,pairs=max(options,key=lambda x:x[0]);choices.append(dict(edge=ei,score=score))
    else:raise ValueError(f'Unsupported edge valence {count}')
    for x,y in pairs:
        fx,fy=m.edges_face[x],m.edges_face[y]
        for vertex in m.edges[x]:
            join(int(fx*3+np.flatnonzero(f[fx]==vertex)[0]),int(fy*3+np.flatnonzero(f[fy]==vertex)[0]))
roots=np.array([root(i) for i in range(f.size)])
_,first,new=np.unique(roots,return_index=True,return_inverse=True)
src=f.ravel()[first]
candidate=trimesh.Trimesh(vertices=m.vertices[src],faces=new.reshape(-1,3),vertex_normals=normals[src],process=False)
assert np.array_equal(candidate.triangles,m.triangles)
candidate.export(a.out/'candidate.glb',include_normals=True)
report=dict(source_sha256=sha,before=audit(m),after=audit(candidate),pairings=choices,
            triangle_positions_exact=True,production_accepted=False,
            scope='Index connectivity only; coincident surface contacts remain, no intersection-free claim')
assert hashlib.sha256(a.source.read_bytes()).hexdigest()==sha
(a.out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
