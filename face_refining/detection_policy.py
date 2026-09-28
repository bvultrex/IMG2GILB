"""Conservative second pass for a single small, well-localized frontal face."""
import numpy as np

GROUPS = [list(range(11, 17)), list(range(17, 23)), list(range(24, 28))]

def points(face):
    box = np.asarray(face['bbox'], dtype=float)
    p = np.asarray(face['keypoints'], dtype=float)
    if box.shape != (5,) or p.shape != (28, 3) or not np.isfinite(box).all() or not np.isfinite(p).all():
        raise ValueError('Invalid detection')
    return box, p, np.asarray([p[g, :2].mean(axis=0) for g in GROUPS])

def retry_crop(faces, shape):
    if len(faces) != 1:
        return None
    try: box, p, centers = points(faces[0])
    except ValueError: return None
    if not .01 <= box[4] < .95 or min(p[g, 2].mean() for g in GROUPS) < .8:
        return None
    size = max(box[2:4] - box[:2])
    eye_distance = np.linalg.norm(centers[1] - centers[0])
    if size < 32 or eye_distance < 24 or size > min(shape[:2]) * .35:
        return None
    center = (box[:2] + box[2:4]) / 2
    low = np.maximum(np.floor(center-size).astype(int), 0)
    high = np.minimum(np.ceil(center+size).astype(int), [shape[1], shape[0]])
    return [int(low[0]), int(low[1]), int(high[0]), int(high[1])]

def consistent_retry(original, candidates):
    if len(candidates) != 1:
        return False
    try:
        old, _, old_centers = points(original)
        box, p, centers = points(candidates[0])
    except ValueError: return False
    if box[4] < .95 or min(p[g, 2].mean() for g in GROUPS) < .8:
        return False
    distance = np.linalg.norm(old_centers[1]-old_centers[0])
    new_distance = np.linalg.norm(centers[1]-centers[0])
    if distance < 24 or not .8 <= new_distance/distance <= 1.25:
        return False
    if np.max(np.linalg.norm(centers-old_centers, axis=1)) > distance*.08:
        return False
    intersection = np.maximum(np.minimum(old[2:4],box[2:4])-np.maximum(old[:2],box[:2]),0).prod()
    union = (old[2:4]-old[:2]).prod()+(box[2:4]-box[:2]).prod()-intersection
    return bool(union > 0 and intersection/union >= .6)
