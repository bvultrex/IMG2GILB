"""Explicit conversion between ECC sampling and forward image transforms."""
import cv2
import numpy as np

def gate_post_warp(result, quality, weight_map_factory):
    """Fail closed on missing/failed post-warp evidence; keep body alignment."""
    image, matrix, iou, metadata, weights = result
    metadata = dict(metadata)
    metadata['post_warp_landmark_quality'] = {k:v for k,v in quality.items() if k != 'affine'}
    if metadata.get('project_face') and quality.get('ok') is not True:
        metadata['project_face'] = False
        metadata['face_reject_reason'] = 'post_warp_landmark_quality'
        metadata['weight_map'] = 'face_iso_paint_post_warp_reject'
        roi = metadata.get('weight_roi', metadata.get('roi'))
        if roi is None:
            raise ValueError('Cannot safely mask rejected face without ROI')
        weights = weight_map_factory(image[:,:,3] > 127, tuple(roi), project_face=False, body_scale=1.00)
    return image, matrix, iou, metadata, weights

def blend_valid_face_interior(image, candidate):
    """Preserve coverage while accepting near-opaque interpolation (251..255)."""
    valid=((image[:,:,3]>250)&(candidate[:,:,3]>250)).astype(np.uint8)
    weight=np.clip(cv2.distanceTransform(valid,cv2.DIST_L2,5)/12.,0,1)[:,:,None]
    result=image.copy()
    result[:,:,:3]=np.clip(image[:,:,:3]*(1-weight)+candidate[:,:,:3]*weight,0,255).astype(np.uint8)
    return result

def face_feature_indices(count):
    # hysts/anime-face-detector assets/landmarks.jpg: 0..4 contour,
    # 5..10 brows, 11..22 eyes, 23 nose, 24..27 mouth.
    return list(range(11,28)) if count == 28 else list(range(count))

def ecc_to_forward(sampling_warp):
    """ECC returns template->input sampling coordinates; warpAffine defaults forward."""
    return cv2.invertAffineTransform(sampling_warp)
