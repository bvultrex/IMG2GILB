"""Append a procedural in-place walk clip to a separate GLB preview."""
import json,struct,math,argparse
from pathlib import Path
import numpy as np
from validate_rig import load_glb

def multiply(a,b):
 x,y,z,w=a;X,Y,Z,W=b
 return np.array([w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z])
def rotation(q):
 x,y,z,w=q
 return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def build(source,destination):
 if Path(source).resolve()==Path(destination).resolve():raise ValueError('Preview must use a separate output')
 d,b=load_glb(source);nodes=d['nodes'];skin=d['skins'][0];joints=set(skin['joints']);parents={c:i for i,n in enumerate(nodes) for c in n.get('children',[])}
 cache={}
 def world(i):
  if i in cache:return cache[i]
  n=nodes[i];m=np.eye(4)
  if 'matrix' in n:m=np.array(n['matrix']).reshape(4,4).T
  else:m[:3,:3]=rotation(n.get('rotation',[0,0,0,1]))@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0])
  if i in parents:m=world(parents[i])@m
  cache[i]=m;return m
 children=lambda i:[c for c in nodes[i].get('children',[]) if c in joints]
 roots=[i for i in joints if parents.get(i) not in joints]
 if len(roots)!=1:raise ValueError('Preview requires a single humanoid root')
 hip=roots[0];h=world(hip)[:3,3]
 legs=sorted([i for i in children(hip) if world(i)[1,3]<h[1]],key=lambda i:world(i)[0,3])
 shoulders=[i for i in joints if len(children(i))>=3 and world(i)[1,3]>h[1]]
 if len(legs)!=2 or not shoulders:raise ValueError('Humanoid limbs not confidently identified')
 chest=max(shoulders,key=lambda i:world(i)[1,3]);branches=sorted(children(chest),key=lambda i:world(i)[0,3]);arms=[children(i)[0] for i in [branches[0],branches[-1]] if len(children(i))==1]
 if len(arms)!=2 or any(len(children(i))!=1 for i in legs):raise ValueError('Ambiguous humanoid limb chain')
 if any(len(children(children(i)[0]))!=1 for i in legs):raise ValueError('Preview needs an ankle on each leg')
 if 'matrix' in nodes[hip]:raise ValueError('Matrix animated root unsupported')
 duration=1.25;times=np.linspace(0,duration,81,dtype='<f4');binary=bytearray(b);samplers=[];channels=[]
 def add(a,kind):
  while len(binary)%4:binary.append(0)
  start=len(binary);raw=np.asarray(a,dtype='<f4').tobytes();binary.extend(raw)
  vi=len(d.setdefault('bufferViews',[]));d['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(raw)})
  ai=len(d['accessors']);entry={'bufferView':vi,'componentType':5126,'count':len(a),'type':kind}
  if kind=='SCALAR':entry.update(min=[float(min(a))],max=[float(max(a))])
  d['accessors'].append(entry);return ai
 ti=add(times,'SCALAR')
 def track(i,angles,axis,rest_angle=0):
  if 'matrix' in nodes[i]:raise ValueError('Matrix animated joints unsupported')
  # Express a world-space diagnostic rotation in this joint's rest frame.
  local=world(i)[:3,:3].T@np.array(axis);local/=np.linalg.norm(local)
  base=np.array(nodes[i].get('rotation',[0,0,0,1]));values=[]
  for angle in angles:
   half=(angle+rest_angle)/2;q=np.r_[local*math.sin(half),math.cos(half)];out=multiply(base,q);values.append(out/np.linalg.norm(out))
  ai=add(values,'VEC4');channels.append({'sampler':len(samplers),'target':{'node':i,'path':'rotation'}});samplers.append({'input':ti,'output':ai,'interpolation':'LINEAR'})
 phase=times/duration*2*np.pi
 # Solve the sagittal two-bone chain from a foot trajectory. Stance occupies
 # 60% of a step; the swing foot clears the floor instead of kicking backwards.
 leg_length=sum(np.linalg.norm(world(c)[:3,3]-world(p)[:3,3]) for p,c in
                [(legs[0],children(legs[0])[0]),(children(legs[0])[0],children(children(legs[0])[0])[0])])
 bob=-.030*leg_length-.018*leg_length*np.cos(2*phase)
 translation=np.tile(nodes[hip].get('translation',[0,0,0]),(len(times),1)).astype(float)
 parent_world=world(parents[hip])[:3,:3] if hip in parents else np.eye(3)
 translation+=bob[:,None]*np.linalg.solve(parent_world,np.array([0.,1.,0.]))[None,:]
 ai=add(translation,'VEC3');channels.append({'sampler':len(samplers),'target':{'node':hip,'path':'translation'}});samplers.append({'input':ti,'output':ai,'interpolation':'LINEAR'})
 reach_errors=[]
 for side,(leg,arm) in enumerate(zip(legs,arms)):
  knee=children(leg)[0]
  if len(children(knee))!=1:raise ValueError('Preview needs an ankle on each leg')
  ankle=children(knee)[0];upper=world(knee)[:3,3]-world(leg)[:3,3];lower=world(ankle)[:3,3]-world(knee)[:3,3]
  l1=np.linalg.norm(upper[1:]);l2=np.linalg.norm(lower[1:]);cycle=(times/duration+side*.5)%1
  half=.19*(l1+l2);z=np.empty(len(times));lift=np.zeros(len(times));stance=cycle<.6
  z[stance]=half*(1-2*cycle[stance]/.6)
  u=(cycle[~stance]-.6)/.4
  # Hermite swing matches the stance velocity at both contacts.
  slope=-2*half*.4/.6
  z[~stance]=(2*u**3-3*u**2+1)*(-half)+(u**3-2*u**2+u)*slope+(-2*u**3+3*u**2)*half+(u**3-u**2)*slope
  lift[~stance]=.09*(l1+l2)*np.sin(np.pi*u)**2
  y=upper[1]+lower[1]+lift-bob;dz=upper[2]+lower[2]+z
  distance=np.sqrt(y*y+dz*dz);reach_errors.append(float(np.maximum(distance-(l1+l2),0).max()))
  distance=np.clip(distance,abs(l1-l2)+1e-6,l1+l2-1e-6)
  theta=np.arctan2(-dz,-y)-np.arccos(np.clip((l1*l1+distance*distance-l2*l2)/(2*l1*distance),-1,1))
  beta=np.pi-np.arccos(np.clip((l1*l1+l2*l2-distance*distance)/(2*l1*l2),-1,1))
  rest_upper=np.arctan2(-upper[2],-upper[1]);rest_lower=np.arctan2(-lower[2],-lower[1])
  thigh_angle=theta-rest_upper;knee_angle=beta-(rest_lower-rest_upper)
  track(leg,thigh_angle,[1,0,0]);track(knee,knee_angle,[1,0,0]);track(ankle,-thigh_angle-knee_angle,[1,0,0])
  wave=np.cos(phase+side*np.pi);track(arm,np.radians(16)*wave,[1,0,0])
  # Lower arms from T-pose using a constant rest-offset channel combined with swing.
  channel=channels[-1];a=d['accessors'][samplers[channel['sampler']]['output']];v=d['bufferViews'][a['bufferView']]
  values=np.frombuffer(binary,dtype='<f4',count=a['count']*4,offset=v['byteOffset']).reshape(-1,4).copy()
  axis=world(arm)[:3,:3].T@np.array([0,0,1]);axis/=np.linalg.norm(axis);angle=np.radians(75)*(1 if side==0 else -1);offset=np.r_[axis*np.sin(angle/2),np.cos(angle/2)]
  values=np.array([multiply(q,offset) for q in values],dtype='<f4');binary[v['byteOffset']:v['byteOffset']+v['byteLength']]=values.tobytes()
  if len(children(arm))==1:track(children(arm)[0],np.radians(12+5*wave),[0,0,1 if side==0 else -1])
 track(chest,np.radians(2)*np.sin(phase),[0,1,0])
 d.setdefault('animations',[]).append({'name':'Walk v2: stance and swing','samplers':samplers,'channels':channels})
 d['buffers'][0]['byteLength']=len(binary);raw=json.dumps(d,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4);binary.extend(b'\0'*((-len(binary))%4));total=12+8+len(raw)+8+len(binary)
 Path(destination).write_bytes(struct.pack('<III',0x46546c67,2,total)+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(binary),0x004e4942)+binary)
 return {'clip':'Walk v2: stance and swing','duration':duration,'legs':legs,'arms':arms,'channels':len(channels),'unreachable_distance_m':max(reach_errors),'limitation':'Sagittal two-bone foot trajectory; no terrain, toe articulation or motion-capture retargeting'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('output');a=p.parse_args();print(json.dumps(build(a.source,a.output)))
