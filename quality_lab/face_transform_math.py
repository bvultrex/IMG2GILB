"""Explicit conversion between ECC sampling and forward image transforms."""
import cv2

def face_feature_indices(count):
    # hysts/anime-face-detector assets/landmarks.jpg: 0..4 contour,
    # 5..10 brows, 11..22 eyes, 23 nose, 24..27 mouth.
    return list(range(11,28)) if count == 28 else list(range(count))

def ecc_to_forward(sampling_warp):
    """ECC returns template->input sampling coordinates; warpAffine defaults forward."""
    return cv2.invertAffineTransform(sampling_warp)
