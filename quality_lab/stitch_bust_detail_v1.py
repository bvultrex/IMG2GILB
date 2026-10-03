"""Stitch readiness dry-run on ROI-v4 primary cut-loop. No topology mutation."""
from pathlib import Path
import json
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from collections import defaultdict

ROOT = Path(r"D:\SF3D_QualityLab\bust_validation\shape_ablation")
BASE_PATH = ROOT / "trellis1024_direct_100000.glb"
DETAIL_PATH = ROOT / "detail_registered.glb"
ROI_REPORT_PATH = ROOT / "detail_dry_splice_roiv4.json"
OUT_REPORT = ROOT / "detail_stitch_v1.json"

KEEP=0.007; DIN=0.003; RIM=0.001; NEAR=0.008; SS=0.003; SM=0.003
LOOP_MED=3.0; LOOP_P90=6.0
GATE_P90=0.003; GATE_MAX=0.005; GATE_COV=0.90

base=trimesh.load(BASE_PATH, force="mesh", process=False)
detail_src=trimesh.load(DETAIL_PATH, force="mesh", process=False)
bv=np.asarray(base.vertices,np.float64); bf=np.asarray(base.faces,np.int64)
dv=np.asarray(detail_src.vertices,np.float64).copy(); df=np.asarray(detail_src.faces,np.int64)

def patch_roi_box(v): return (np.abs(v[:,0])<0.066)&(v[:,1]>0.090)&(v[:,1]<0.183)&(v[:,2]>-0.010)
def protected_lens_roi(v): return (np.abs(v[:,0])<0.048)&(v[:,1]>0.100)&(v[:,1]<0.172)&(v[:,2]>0.0)
def boundary_edges(mesh):
    faces=np.asarray(mesh.faces,np.int64)
    edges=np.sort(np.vstack((faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]])),axis=1)
    u,c=np.unique(edges,axis=0,return_counts=True); return u[c==1]
def boundary_vertices(mesh):
    be=boundary_edges(mesh)
    if len(be)==0: return np.empty((0,3)), np.empty((0,),np.int64)
    vids=np.unique(be); return np.asarray(mesh.vertices,np.float64)[vids], vids
def new_boundary_edges(mesh, prior, tol=1e-9):
    be=boundary_edges(mesh); V=np.asarray(mesh.vertices,np.float64)
    if len(be)==0: return be
    d0,_=prior.query(V[be[:,0]]); d1,_=prior.query(V[be[:,1]])
    return be[(d0>=tol)&(d1>=tol)]
def comps(be):
    if len(be)==0: return []
    adj=defaultdict(list)
    for i,(a,b) in enumerate(be):
        adj[int(a)].append(i); adj[int(b)].append(i)
    seen=np.zeros(len(be),dtype=bool); out=[]
    for i in range(len(be)):
        if seen[i]: continue
        st=[i]; seen[i]=True; e=[]
        while st:
            x=st.pop(); e.append(x)
            for v in (int(be[x,0]),int(be[x,1])):
                for ei in adj[v]:
                    if not seen[ei]: seen[ei]=True; st.append(ei)
        out.append(np.array(e,np.int64))
    out.sort(key=len, reverse=True); return out
def stats(d):
    d=np.asarray(d,float)
    if len(d)==0: return {"n":0,"median_mm":None,"p90_mm":None,"max_mm":None,"empty":True}
    return {"n":int(len(d)),"median_mm":float(np.median(d)*1000),"p90_mm":float(np.quantile(d,0.9)*1000),"max_mm":float(np.max(d)*1000),"empty":False}

base_open,_=boundary_vertices(base); detail_open,_=boundary_vertices(detail_src)
bot=cKDTree(base_open); dot=cKDTree(detail_open); bst=cKDTree(bv)
d_to_base,_=bst.query(dv)
keep=patch_roi_box(dv)&((d_to_base<KEEP)|protected_lens_roi(dv))
face=keep[df].all(axis=1)
detail=detail_src.copy(); detail.vertices=dv
patch=detail.submesh([face], append=True, repair=False)
pv=np.asarray(patch.vertices,np.float64); prot=protected_lens_roi(pv); pv0=pv.copy()
pb,pb_vids=boundary_vertices(patch); d,_=dot.query(pb); m=d>=1e-9; pb_vids=pb_vids[m]
sid=pb_vids[~prot[pb_vids]]
_,nn=bst.query(pv[sid]); delta=bv[nn]-pv[sid]; dn=np.linalg.norm(delta,axis=1)
pv[sid]=pv[sid]+delta*(np.minimum(1.0,SS/np.maximum(dn,1e-12))[:,None]); patch.vertices=pv
pb,pb_vids=boundary_vertices(patch); d,_=dot.query(pb); m=d>=1e-9; pb_new=pb[m]; pb_vids=pb_vids[m]
cents=bv[bf].mean(axis=1)
loose=(np.abs(cents[:,0])<0.070)&(cents[:,1]>0.088)&(cents[:,1]<0.185)&(cents[:,2]>-0.012)
pt=cKDTree(pv); pbt=cKDTree(pb_new)
ds=np.full(len(cents),np.inf); db=np.full(len(cents),np.inf)
ds[loose],_=pt.query(cents[loose]); db[loose],_=pbt.query(cents[loose])
cut=loose&(ds<DIN)&(db>RIM)
base_cut=base.submesh([~cut], append=True, repair=False)
V=np.asarray(base_cut.vertices,np.float64)
be=new_boundary_edges(base_cut, bot); cps=comps(be)
pbt=cKDTree(pb_new); vids=[]
for eidx in cps:
    vv=np.unique(be[eidx]); pts=V[vv]; dd,_=pbt.query(pts)
    if float(np.median(dd)*1000)<LOOP_MED and float(np.quantile(dd,0.9)*1000)<LOOP_P90:
        vids.append(vv)
prim=V[np.unique(np.concatenate(vids))]
sid=pb_vids[~prot[pb_vids]]
_,nn=cKDTree(prim).query(pv[sid]); delta=prim[nn]-pv[sid]; dn=np.linalg.norm(delta,axis=1)
pv[sid]=pv[sid]+delta*(np.minimum(1.0,SM/np.maximum(dn,1e-12))[:,None]); patch.vertices=pv
pb,pb_vids=boundary_vertices(patch); d,_=dot.query(pb); m=d>=1e-9; pb_new=pb[m]; pb_vids=pb_vids[m]
prot_move=float(np.linalg.norm(pv[prot]-pv0[prot],axis=1).max()) if prot.any() else 0.0
prot=protected_lens_roi(pv)  # refresh only for seam exclusion after snap
d_to_patch,_=cKDTree(pb_new).query(prim)
base_seam=prim[d_to_patch<NEAR]
d_to_base,_=cKDTree(base_seam).query(pb_new)
mask=d_to_base<NEAR
ps=pb_new[mask]; ps_vids=pb_vids[mask]; br=d_to_base[mask]
nonprot=~prot[ps_vids]; bridge=br[nonprot]
p2b=stats(bridge); b2,_=cKDTree(ps[nonprot]).query(base_seam); b2p=stats(b2)
cov3=float(np.mean(bridge<=GATE_P90)) if len(bridge) else 0.0
cov5=float(np.mean(bridge<=GATE_MAX)) if len(bridge) else 0.0
reasons=[]
if p2b["empty"] or b2p["empty"]: reasons.append("empty")
if p2b["p90_mm"] is not None and p2b["p90_mm"]>GATE_P90*1000: reasons.append(f"p2b_p90={p2b['p90_mm']:.4f}>3")
if p2b["max_mm"] is not None and p2b["max_mm"]>GATE_MAX*1000: reasons.append(f"p2b_max={p2b['max_mm']:.4f}>5")
if b2p["p90_mm"] is not None and b2p["p90_mm"]>GATE_P90*1000: reasons.append(f"b2p_p90={b2p['p90_mm']:.4f}>3")
if b2p["max_mm"] is not None and b2p["max_mm"]>GATE_MAX*1000: reasons.append(f"b2p_max={b2p['max_mm']:.4f}>5")
if cov3<GATE_COV: reasons.append(f"cov3={cov3:.4f}<0.9")
if prot_move>1e-9: reasons.append(f"protected_moved={prot_move}")
accepted=len(reasons)==0
roi={}
if ROI_REPORT_PATH.exists(): roi=json.loads(ROI_REPORT_PATH.read_text(encoding="utf-8"))
report={
  "scope":"stitch readiness dry-run on ROI-v4 primary cut-loop; no topology mutation",
  "version":"stitch_bust_detail_v1_dry_run_roiv4",
  "roi_report":str(ROI_REPORT_PATH),
  "gates":{"max_bridge_accept_p90_mm":3.0,"max_bridge_accept_max_mm":5.0,"min_coverage_frac_le_p90_gate":0.9},
  "before_from_roiv4_json":{
    "patch_to_base_boundary_p90_mm":roi.get("patch_to_base_boundary_p90_mm"),
    "patch_to_base_boundary_max_mm":roi.get("patch_to_base_boundary_max_mm"),
    "base_to_patch_boundary_p90_mm":roi.get("base_to_patch_boundary_p90_mm"),
    "base_to_patch_boundary_max_mm":roi.get("base_to_patch_boundary_max_mm"),
    "patch_to_base_coverage_le_3mm":roi.get("patch_to_base_coverage_le_3mm"),
    "orphan_component_vertices_dropped":roi.get("orphan_component_vertices_dropped"),
  },
  "compared_to_roiv3_stitch":{"bridge_p90_mm":2.9851,"bridge_max_mm":7.6797,"b2p_p90_mm":6.0400,"coverage_le_3mm":0.9022},
  "measured_patch_to_base":p2b,
  "measured_base_to_patch":b2p,
  "bridge_length_p90_mm":p2b["p90_mm"],
  "bridge_length_max_mm":p2b["max_mm"],
  "coverage_frac_bridge_le_3mm":cov3,
  "coverage_frac_bridge_le_5mm":cov5,
  "patch_seam_vertices_nonprot":int(nonprot.sum()),
  "base_seam_vertices_primary":int(len(base_seam)),
  "protected_planned_move_max_m":prot_move,
  "accepted_for_topology_mutation":accepted,
  "rejection_reasons":reasons,
  "decision":"rejected_no_topology_mutation" if not accepted else "gates_passed_but_v1_still_skips_mutation",
  "topology_mutated":False,
  "output_mesh_written":False,
  "production_accepted":False,
}
OUT_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
