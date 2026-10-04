"""Remove duplicate/zero-area triangles without inventing missing surfaces."""
import argparse,hashlib,json,struct
from pathlib import Path
import numpy as np,trimesh
from codex_splice_boundary_audit import audit
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(exist_ok=False,parents=True)
sha=hashlib.sha256(a.source.read_bytes()).hexdigest()
m=trimesh.load(a.source,force='mesh',process=False)
assert m.visual.kind != 'texture', 'Geometry-only diagnostic; do not drop textures'
v=m.vertices.copy();faces=m.faces.copy();normals=m.vertex_normals.copy()
_,first=np.unique(np.sort(faces,axis=1),axis=0,return_index=True)
keep=np.zeros(len(faces),bool);keep[first]=True
duplicates=int((~keep).sum());zero=m.area_faces==0
keep &= ~zero
r=dict(source_sha256=sha,before=audit(m),duplicates=duplicates,exact_zero_area=int(zero.sum()),removed=int((~keep).sum()),production_accepted=False)
m.update_faces(keep);m.vertex_normals=normals
assert np.array_equal(m.vertices,v) and np.array_equal(m.faces,faces[keep])
target=a.out/'candidate.glb'
raw=a.source.read_bytes();jsize,jtype=struct.unpack_from('<II',raw,12)
doc=json.loads(raw[20:20+jsize]);bstart=20+jsize
bsize,btype=struct.unpack_from('<II',raw,bstart);binary=bytearray(raw[bstart+8:bstart+8+bsize])
assert len(doc['meshes'])==1 and len(doc['meshes'][0]['primitives'])==1
primitive=doc['meshes'][0]['primitives'][0];acc=doc['accessors'][primitive['indices']]
view=doc['bufferViews'][acc['bufferView']]
dtype={5123:'<u2',5125:'<u4'}[acc['componentType']]
offset=view.get('byteOffset',0)+acc.get('byteOffset',0)
original=np.frombuffer(binary,dtype=dtype,count=acc['count'],offset=offset).reshape(-1,3)
assert np.array_equal(original,faces)
packed=np.asarray(faces[keep],dtype=dtype).tobytes();binary[offset:offset+len(packed)]=packed
acc['count']=int(keep.sum()*3)
if 'min' in acc:acc['min']=[int(faces[keep].min())]
if 'max' in acc:acc['max']=[int(faces[keep].max())]
j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
target.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(binary))+struct.pack('<II',len(j),jtype)+j+struct.pack('<II',len(binary),btype)+binary)
check=trimesh.load(target,force='mesh',process=False)
assert np.array_equal(check.faces,m.faces)
assert np.array_equal(check.vertices,m.vertices)
r['non_index_binary_bytes_preserved']=binary[:offset]==raw[bstart+8:bstart+8+offset] and binary[offset+len(packed):]==raw[bstart+8+offset+len(packed):bstart+8+bsize]
assert r['non_index_binary_bytes_preserved']
r.update(after=audit(check),output_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),retained_geometry_exact=True)
assert hashlib.sha256(a.source.read_bytes()).hexdigest()==sha
(a.out/'report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r),flush=True)
