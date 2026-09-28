"""CPU-only image alignment. No model loading, filesystem writes or GPU side effects."""
import cv2
import numpy as np
from scipy.spatial import Delaunay, QhullError

class Rejected(ValueError):
    pass

GROUPS = [list(range(11,17)), list(range(17,23)), list(range(24,28))]

def coloured_fringe(image,centers,landmarks,skin):
    distance=np.linalg.norm(centers[1]-centers[0]);middle=centers[:2,0].mean()
    brow_y=landmarks[5:11,1].min()
    x0=max(0,int(middle-.7*distance));x1=min(image.shape[1],int(middle+.7*distance))
    y0=max(0,int(brow_y-1.2*distance));y1=min(image.shape[0],int(brow_y-.4*distance))
    patch=image[y0:y1,x0:x1]
    if patch.size==0:return np.zeros(image.shape[:2],bool)
    pixels=patch[:,:,:3][patch[:,:,3]>250]
    if len(pixels)<20:return np.zeros(image.shape[:2],bool)
    hair=np.median(pixels,axis=0)
    # Activate only when a separate, bright hair colour was actually observed;
    # otherwise dark generated brow shadows must not masquerade as a fringe.
    if hair.max()<110 or np.ptp(hair)<55 or np.linalg.norm(hair-skin)<82:
        return np.zeros(image.shape[:2],bool)
    return np.linalg.norm(image[:,:,:3].astype(float)-hair,axis=2)<70

def checked_face(faces, shape):
    if len(faces) != 1:
        raise Rejected('exactly_one_face_required')
    f=faces[0]; p=np.asarray(f['keypoints'],dtype=np.float64); b=np.asarray(f['bbox'],dtype=np.float64)
    if p.shape != (28,3) or b.shape != (5,) or not np.isfinite(p).all() or not np.isfinite(b).all():
        raise Rejected('invalid_landmarks')
    if b[4]<.95 or min(p[g,2].mean() for g in GROUPS)<.7:
        raise Rejected('low_detection_confidence')
    h,w=shape[:2]
    if (p[:,:2]<0).any() or (p[:,0]>=w).any() or (p[:,1]>=h).any():
        raise Rejected('clipped_face')
    centers=np.array([p[g,:2].mean(axis=0) for g in GROUPS])
    eyes=centers[1]-centers[0]; distance=np.linalg.norm(eyes)
    if distance<24 or eyes[0]<=0 or abs(eyes[1])/distance>.45:
        raise Rejected('too_small_or_tilted')
    mouth=centers[2]-(centers[0]+centers[1])/2
    if not .25< mouth[1]/distance <1.15 or abs(mouth[0])/distance>.35:
        raise Rejected('unsupported_pose_or_proportions')
    # Scores are heatmap values, not calibrated probabilities.
    return p,centers

def warp_face(source, target, source_faces, target_faces):
    sp,sc=checked_face(source_faces,source.shape);tp,tc=checked_face(target_faces,target.shape)
    sv=sc[1]-sc[0]; tv=tc[1]-tc[0]; scale=np.linalg.norm(tv)/np.linalg.norm(sv)
    if not .2<scale<5:raise Rejected('extreme_scale')
    angle=np.arctan2(tv[1],tv[0])-np.arctan2(sv[1],sv[0])
    rot=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])*scale
    mapped=(sp[:,:2]-sc[0])@rot.T+tc[0]
    delta=tc[2]-((sc[2]-sc[0])@rot.T+tc[0])
    if np.linalg.norm(delta)>.3*np.linalg.norm(tv):raise Rejected('mouth_disagreement')
    # Include the entire brow, not just its endpoints: the old hull cut through
    # the eyebrow and left the generated upper brow visible as a dark double edge.
    outer=list(range(11))
    forehead=sp[[5,6,7,8,9,10],:2].copy()
    forehead[:,1]-=np.linalg.norm(sv)*.22
    mapped_forehead=(forehead-sc[0])@rot.T+tc[0]
    src=np.vstack([sc,sp[outer,:2],forehead]);dst=np.vstack([tc,mapped[outer],mapped_forehead])
    try:tri=Delaunay(dst)
    except QhullError as e:raise Rejected('degenerate_warp') from e
    for t in tri.simplices:
        sa=np.linalg.det(np.stack([src[t[1]]-src[t[0]],src[t[2]]-src[t[0]]]))
        da=np.linalg.det(np.stack([dst[t[1]]-dst[t[0]],dst[t[2]]-dst[t[0]]]))
        if sa*da<=0:raise Rejected('folded_warp')
    h,w=target.shape[:2]
    # Only map the detected face ROI; avoid allocating full-frame triangle matrices.
    low=np.maximum(np.floor(dst.min(axis=0)).astype(int)-2,0)
    high=np.minimum(np.ceil(dst.max(axis=0)).astype(int)+3,[w,h])
    x0,y0=low;x1,y1=high
    yy,xx=np.mgrid[y0:y1,x0:x1];pts=np.c_[xx.ravel(),yy.ravel()];ids=tri.find_simplex(pts);valid=ids>=0
    coords=np.full((len(pts),2),-1,np.float32);tr=tri.transform[ids[valid]]
    bc=np.einsum('nij,nj->ni',tr[:,:2],pts[valid]-tr[:,2]);bc=np.c_[bc,1-bc.sum(axis=1)]
    coords[valid]=np.einsum('ni,nij->nj',bc,src[tri.simplices[ids[valid]]]);coords=coords.reshape(y1-y0,x1-x0,2)
    warped=np.zeros((h,w,4),np.uint8)
    warped[y0:y1,x0:x1]=cv2.remap(source,coords[:,:,0],coords[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    mask=np.zeros((h,w),np.uint8);mask[y0:y1,x0:x1]=valid.reshape(y1-y0,x1-x0).astype(np.uint8)
    mask*=((warped[:,:,3]>250)&(target[:,:,3]>250)).astype(np.uint8)
    # The extra forehead support must not paint over an occluding fringe.
    # Limit only the newly added strip, using local cheek colours in each image;
    # eyes/brows inside the original support are never classified as skin.
    base_support=np.zeros((h,w),np.uint8)
    cv2.fillConvexPoly(base_support,cv2.convexHull(np.rint(mapped[outer]).astype(np.int32)),1)
    def cheek_colour(image,centers):
        samples=[]
        for eye in centers[:2]:
            x,y=np.rint(eye*.45+centers[2]*.55).astype(int)
            patch=image[max(0,y-2):min(image.shape[0],y+3),max(0,x-2):min(image.shape[1],x+3),:3]
            if patch.size:samples.append(patch.reshape(-1,3))
        return np.median(np.concatenate(samples),axis=0)
    src_skin=cheek_colour(source,sc);dst_skin=cheek_colour(target,tc)
    compatible=(np.linalg.norm(warped[:,:,:3].astype(float)-src_skin,axis=2)<82)&(np.linalg.norm(target[:,:,:3].astype(float)-dst_skin,axis=2)<82)
    mask*=((base_support>0)|compatible).astype(np.uint8)
    # Bright coloured fringe strands can also cross the brow hull itself.
    # Keep them occluding the face; dark brow strokes remain eligible.
    above_eyes=np.arange(h)[:,None]<(tc[:2,1].min()-np.linalg.norm(tv)*.12)
    source_hair=coloured_fringe(source,sc,sp,src_skin).astype(np.uint8)
    # Reuse the exact face warp coordinates to map the source occlusion mask.
    source_fringe=np.zeros((h,w),bool)
    source_fringe[y0:y1,x0:x1]=cv2.remap(source_hair,coords[:,:,0],coords[:,:,1],cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT)>0
    target_fringe=coloured_fringe(target,tc,tp,dst_skin)
    eye_support=np.zeros((h,w),np.uint8)
    for indices in [list(range(11,17)),list(range(17,23))]:
        cv2.fillConvexPoly(eye_support,cv2.convexHull(np.rint(mapped[indices]).astype(np.int32)),1)
    eye_support=cv2.dilate(eye_support,np.ones((5,5),np.uint8))
    mask[above_eyes&(source_fringe|target_fringe)&(eye_support==0)]=0
    if mask.sum()<400:raise Rejected('insufficient_face_coverage')
    feather=max(5,np.linalg.norm(tv)*.12)
    alpha=np.clip(cv2.distanceTransform(mask,cv2.DIST_L2,5)/feather,0,1)
    feature_polygons=[np.vstack([mapped[5:8],mapped[11:17]]).tolist(),np.vstack([mapped[8:11],mapped[17:23]]).tolist()]
    return warped,mask,alpha,{'source_centers':sc.tolist(),'target_centers':tc.tolist(),'eye_scale':float(scale),'mouth_delta':delta.tolist(),'feature_polygons':feature_polygons,'roi':[int(x0),int(y0),int(x1),int(y1)]}

def feature_mask(shape,polygons):
    protect=np.zeros(shape[:2],np.uint8)
    for polygon in polygons or []:
        cv2.fillConvexPoly(protect,cv2.convexHull(np.rint(polygon).astype(np.int32)),1)
    protect=cv2.dilate(protect,np.ones((5,5),np.uint8))
    return np.maximum(cv2.GaussianBlur(protect.astype(np.float32),(0,0),2),protect.astype(np.float32))

def blend_face(warped,target,mask,alpha,method='multiband',feature_polygons=None):
    if method=='feather':return warped[:,:,:3].astype(np.float32)/255
    if method=='multiband':
        # Fill outside support with baseline before constructing image pyramids.
        src=warped[:,:,:3].astype(np.float32)/255
        dst=target[:,:,:3].astype(np.float32)/255
        src=np.where(mask[:,:,None]>0,src,dst)
        gs=[src];gd=[dst];gm=[alpha.astype(np.float32)]
        for _ in range(5):
            gs.append(cv2.pyrDown(gs[-1]));gd.append(cv2.pyrDown(gd[-1]));gm.append(cv2.pyrDown(gm[-1]))
        ls=[];ld=[]
        for i in range(5):
            size=(gs[i].shape[1],gs[i].shape[0])
            ls.append(gs[i]-cv2.pyrUp(gs[i+1],dstsize=size));ld.append(gd[i]-cv2.pyrUp(gd[i+1],dstsize=size))
        merged=gs[-1]*gm[-1][:,:,None]+gd[-1]*(1-gm[-1][:,:,None])
        for i in reversed(range(5)):
            merged=cv2.pyrUp(merged,dstsize=(gs[i].shape[1],gs[i].shape[0]))+ls[i]*gm[i][:,:,None]+ld[i]*(1-gm[i][:,:,None])
        # Return unpremultiplied colour for downstream alpha projection.
        result=np.clip((merged-dst*(1-alpha[:,:,None]))/np.maximum(alpha[:,:,None],1e-5),0,1)
        # Keep reference eye whites and brow linework; multiband's coarse levels
        # otherwise mix the dark generated eye colour back into these regions.
        if feature_polygons:
            weight=feature_mask(mask.shape,feature_polygons)*mask
            result=result*(1-weight[:,:,None])+src*weight[:,:,None]
        return result
    # Solve colour transitions in image space, never across unrelated UV islands.
    ys,xs=np.where(mask)
    if len(xs)==0:raise Rejected('empty_mask')
    x0,x1=int(xs.min()),int(xs.max())+1;y0,y1=int(ys.min()),int(ys.max())+1
    center=((x0+x1)//2,(y0+y1)//2)
    cloned=cv2.seamlessClone(warped[:,:,:3],target[:,:,:3],mask*255,center,cv2.NORMAL_CLONE)
    return cloned.astype(np.float32)/255
