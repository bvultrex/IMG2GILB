"""Explicit conversion between ECC sampling and forward image transforms."""
import cv2

def ecc_to_forward(sampling_warp):
    """ECC returns template->input sampling coordinates; warpAffine defaults forward."""
    return cv2.invertAffineTransform(sampling_warp)
