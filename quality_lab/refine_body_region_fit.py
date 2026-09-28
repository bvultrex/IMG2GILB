"""Experimental front/back reference projection; keeps head and original PBR maps."""
import copy,hashlib,json,os,sys,time
from pathlib import Path
import numpy as np,cv2,torch,trimesh
from PIL import Image
ROOT=Path(r'D:\SF3D_QualityLab\male_anime_validation')
job=Path(r'D:\SF3D_QualityLab\app_jobs\b66c77f5fb844cefae8ec485d8bab8af')
sys.path.insert(0,r'D:\SF3D_QualityLab\face_v1')
os.environ['IMG2GILB_HUNYUAN_SOURCE']=r'C:\Users\Shadow\Documents\ComfyUI\Hunyuan3D-2-Lab'
from render_adapter import ProjectionRender
source_mesh=ROOT/'full_pipeline_rig_test/face/Face_1_0.glb'
out=ROOT/'body_multiview_v6';out.mkdir(exist_ok=True)
face_landmarks=json.loads((source_mesh.parent/'landmarks.json').read_text())[1]['faces'][0]
scene=trimesh.load(source_mesh,process=False);mesh=next(iter(scene.geometry.values()))
mat=copy.deepcopy(mesh.visual.material);base=np.asarray(mat.baseColorTexture.convert('RGB')).astype(np.float32)/255
r=ProjectionRender(default_resolution=2048,texture_size=2048);r.load_mesh(mesh.copy());r.set_texture(base)
acc=torch.zeros((2048,2048,3),device='cuda');weights=torch.zeros((2048,2048,1),device='cuda')
report={'status':'experimental','method':'four-view silhouette registration, protected head, sharper incidence weighting','source_mesh':str(source_mesh),'source_sha256':hashlib.sha256(source_mesh.read_bytes()).hexdigest(),'views':[]}
def bbox(mask):
    ys,xs=np.where(mask);return np.array([xs.min(),ys.min(),xs.max(),ys.max()],float)
for name,angle in [('front',0),('back',180),('left',-90),('right',90)]:
    target=r.render(0,angle,return_type='np');Image.fromarray((target.clip(0,1)*255).round().astype('uint8')).save(out/f'{name}_before.png')
    rgba=np.array(Image.open(job/'prepared'/f'{name}.png').convert('RGBA'))
    sb=bbox(rgba[:,:,3]>250);tb=bbox(target[:,:,3]>.99);scale=(tb[2:]-tb[:2])/(sb[2:]-sb[:2]);shift=tb[:2]-sb[:2]*scale
    affine=np.array([[scale[0],0,shift[0]],[0,scale[1],shift[1]]],np.float32)
    if name in ('left','right'):
        # Hands protrude sideways in the supplied profiles; use trunk/leg rows
        # for horizontal registration rather than stretching their whole bbox.
        vertical=cv2.warpAffine(rgba[:,:,3],np.array([[1,0,0],[0,scale[1],shift[1]]],np.float32),(2048,2048))>250
        ratios=[];pairs=[]
        for yy in range(int(tb[1]+.40*(tb[3]-tb[1])),int(tb[1]+.85*(tb[3]-tb[1])),8):
            sx=np.flatnonzero(vertical[yy]);tx=np.flatnonzero(target[yy,:,3]>.99)
            if len(sx)>10 and len(tx)>10:
                ratios.append((tx[-1]-tx[0])/(sx[-1]-sx[0]));pairs.append(((sx[0]+sx[-1])/2,(tx[0]+tx[-1])/2))
        if ratios:
            xs=float(np.median(ratios));shiftx=float(np.median([t-xs*a for a,t in pairs]));affine[0]=[xs,0,shiftx]
    warped=cv2.warpAffine(rgba,affine,(2048,2048),flags=cv2.INTER_LINEAR)
    source=warped[:,:,3]>250;visible=target[:,:,3]>.99
    iou=float((source&visible).sum()/(source|visible).sum())
    row={'view':name,'silhouette_iou':iou,'affine':affine.tolist()};report['views'].append(row)
    roi=np.ones(source.shape,np.uint8)
    if name in ('left','right'):
        roi[:int(tb[1]+.38*(tb[3]-tb[1]))]=0;roi[int(tb[1]+.9*(tb[3]-tb[1])):]=0
        roi_iou=float(((source&visible)&(roi>0)).sum()/((source|visible)&(roi>0)).sum());row['body_region_iou']=roi_iou
    else:roi_iou=iou
    if roi_iou<.75:row['skipped']='registration_overlap_low';continue
    mask=(source&visible).astype(np.uint8)*roi
    alpha=np.clip(cv2.distanceTransform(mask,cv2.DIST_L2,5)/40,0,1)
    # Exclude the head from body colour replacement, including the refined face.
    cutoff=float(face_landmarks['bbox'][3])+20
    alpha*=np.clip((np.arange(2048)[:,None]-cutoff)/25,0,1)
    rgb=warped[:,:,:3].astype(np.float32)/255
    data=np.concatenate([rgb*alpha[:,:,None],alpha[:,:,None]],axis=-1)
    tex,cos,_=r.back_project(data,0,angle);a=tex[:,:,3:4].clamp(0,1)
    incidence=((cos-.65)/.3).clamp(0,1);incidence=incidence*incidence*(3-2*incidence)
    w=a*incidence; detail_weight=w*cos.clamp(0,1)**8;acc+=tex[:,:,:3]/a.clamp_min(1e-6)*detail_weight;weights+=detail_weight
    row['strong_projection_pixels']=int((w>.8).sum())
confidence=(weights*2).clamp(0,1);mixed=torch.as_tensor(base,device='cuda')*(1-confidence)+acc/weights.clamp_min(1e-6)*confidence
atlas=(mixed.clamp(0,1).cpu().numpy()*255).round().astype('uint8')
unchanged=weights[:,:,0].cpu().numpy()<=1e-6;atlas[unchanged]=(base[unchanged]*255).round().astype('uint8')
mat.baseColorTexture=Image.fromarray(atlas);mesh.visual.material=mat;mesh.export(out/'Body_Reference_Trial.glb')
r.set_texture(atlas.astype(np.float32)/255)
for name,angle in [('front',0),('back',180),('left',90),('right',-90)]:
    im=r.render(0,angle,return_type='np');Image.fromarray((im.clip(0,1)*255).round().astype('uint8')).save(out/f'{name}_after.png')
report['changed_atlas_pixels']=int(np.any(atlas!=(base*255).round().astype('uint8'),axis=2).sum())
face_mask=np.asarray(Image.open(source_mesh.parent/'projection_mask.png'))>10
report['changed_face_pixels']=int((np.any(atlas!=(base*255).round().astype('uint8'),axis=2)&face_mask).sum())
assert report['changed_face_pixels']==0,'Body projection modified the protected face'
check=next(iter(trimesh.load(out/'Body_Reference_Trial.glb',process=False).geometry.values()))
assert np.array_equal(mesh.faces,check.faces) and np.allclose(mesh.vertices,check.vertices)
assert np.allclose(mesh.visual.uv,check.visual.uv)
assert np.array_equal(np.asarray(mat.metallicRoughnessTexture),np.asarray(check.visual.material.metallicRoughnessTexture))
report['geometry_uv_material_validation']='passed'
report['limitations']=['silhouette alignment does not prove semantic correspondence','reference shadows remain in colour','side camera mapping assumes the current Hunyuan convention; not a universal registration solution']
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
