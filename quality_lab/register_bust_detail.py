"""Fixture-only local registration experiment. Never modifies either input mesh."""
from pathlib import Path
import json
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from scipy.optimize import least_squares

ROOT = Path(r'D:\SF3D_QualityLab\bust_validation\shape_ablation')
base = trimesh.load(ROOT/'trellis1024_direct_100000.glb', force='mesh', process=False)
detail = trimesh.load(ROOT/'trellis1024_direct_headprobe_100000_remesh512.glb', force='mesh', process=False)
# Crop coordinates from the diagnostic normalized front image. glTF is Y-up, +Z front.
crop = np.array([.32, .015, .675, .36])
height = base.extents[1]
initial_scale = (crop[3]-crop[1])*height/detail.extents[1]
center = np.array([(crop[0]+crop[2])/2-.5, .5-(crop[1]+crop[3])/2, 0.])*height
src = (detail.vertices-detail.bounds.mean(0))*initial_scale+center
dst = base.vertices
# Register the hood's upper/lateral support region; hold out the lens area.
def support(v):
    return (v[:,1]>.10)&(v[:,2]>0)&((np.abs(v[:,0])>.044)|(v[:,1]>.169))&(np.abs(v[:,0])<.087)
target = dst[support(dst)]
source_ids = np.flatnonzero(support(src))
assert len(target)>100 and len(source_ids)>100
tree = cKDTree(target)
train_ids, validation_ids = source_ids[::2], source_ids[1::2]
translation = np.zeros(3)
for _ in range(40):
    points = src[train_ids]+translation
    dist, ids = tree.query(points)
    keep = dist <= np.quantile(dist,.75)
    step = np.median(target[ids[keep]]-points[keep],axis=0)
    translation += step
    if np.linalg.norm(step)<1e-6: break
def transform(parameters):
    return (src-center)*parameters[:3]+center+parameters[3:]
def objective(parameters):
    points=transform(parameters)[train_ids]
    _,ids=tree.query(points)
    return np.concatenate([(points-target[ids]).ravel(), .01*(parameters[:3]-1)])
fit=least_squares(objective,np.r_[np.ones(3),translation],bounds=(np.r_[np.full(3,.75),np.full(3,-.025)],np.r_[np.full(3,1.25),np.full(3,.025)]),loss='soft_l1',f_scale=.002,max_nfev=100)
registered = transform(fit.x)
residual, _ = tree.query(registered[validation_ids])
# Strict screening only; no claim that this proves semantic registration.
accepted = bool(np.quantile(residual,.9)<.003 and np.linalg.norm(translation)<.025)
detail.vertices = registered
detail.export(ROOT/'detail_registered.glb')
report = dict(scope='fixed bust fixture; translation-only hood ICP; no automatic ROI detection',
    source=str(ROOT/'trellis1024_direct_headprobe_100000_remesh512.glb'),
    target=str(ROOT/'trellis1024_direct_100000.glb'),
    scale=float(initial_scale), axis_scale_correction=fit.x[:3].tolist(), translation_m=fit.x[3:].tolist(),
    heldout_median_mm=float(np.median(residual)*1000),heldout_p90_mm=float(np.quantile(residual,.9)*1000),
    geometric_gate_passed=accepted,production_accepted=False,
    note='Nearest-surface distance does not verify lens placement, depth correspondence or seam topology. No fusion performed.')
(ROOT/'detail_registration.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
