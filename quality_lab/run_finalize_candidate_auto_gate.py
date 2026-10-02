"""Run two consecutive Studio-path jobs with finalize_candidate opt-in (default OFF when unset).

Clones Ranger + Bust fixtures, sets hybrid_a3 + finalize_candidate=textured_hybrid_a3_pbr.glb,
rebinds stage cache fingerprints so only finalize (and missing stages) re-run, then Job.run().
Does NOT flip Studio UI defaults or production_accepted.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB")
DESKTOP = ROOT / "desktop"
sys.path.insert(0, str(DESKTOP))
from pipeline import Job, sha, write_json, sum_face_code  # noqa: E402

CFG = json.loads((DESKTOP / "runtime.json").read_text(encoding="utf-8-sig"))
LAB = Path(CFG["lab"])
JOBS = Path(CFG["jobs_dir"])
PY = Path(CFG["python"])
VIS = Path(r"C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_finalize_auto_gate")
VIS.mkdir(parents=True, exist_ok=True)

CANDIDATE_REL = "textured_hybrid_a3_pbr.glb"
FACE_SOURCE_LABEL = "hybrid_a3_pbr"

SOURCES = [
    {
        "label": "ranger",
        "src": JOBS / "4abf740c34c9487ba818455efe460833",
        "height_cm": 170.0,
        "face": True,
        "note": "auto_finalize_gate: Ranger clothed; hybrid_a3 + finalize_candidate=textured_hybrid_a3_pbr.glb",
    },
    {
        "label": "bust",
        "src": JOBS / "9c9d771bfdf844bc8e15b60509ef308d",
        "height_cm": 40.0,
        "face": False,
        "note": "auto_finalize_gate: Mechanical bust; hybrid_a3 + finalize_candidate=textured_hybrid_a3_pbr.glb",
    },
]

COPY_TREE = [
    "inputs",
    "prepared",
    "controls",
    "paint",
    "hybrid_a3",
    "face",
]
COPY_FILES = [
    "shape.glb",
    "shape_raw.glb",
    "shape_report.json",
    "textured_color.glb",
    "textured_pbr.glb",
    "textured_hybrid_a3_color.glb",
    "textured_hybrid_a3_pbr.glb",
    "face_project.json",
]


def fingerprint_for(spec: dict) -> str:
    s = spec["settings"]
    parts = (
        json.dumps(spec, sort_keys=True)
        + sha(DESKTOP / "stages.py")
        + sha(DESKTOP / "pipeline.py")
        + sha(LAB / "run_paint21.py")
        + sha(LAB / "bake_paint21.py")
        + sha(DESKTOP / "runtime.json")
        + sha(DESKTOP / "rig_stage.py")
        + sha(DESKTOP / "validate_rig.py")
        + sha(DESKTOP / "walk_preview.py")
    )
    if s.get("face"):
        fr = Path(CFG["face_runtime"])
        parts += sha(fr) + sum_face_code(fr.parent) + sha(fr.parent / "runtime.json")
    return hashlib.sha256(parts.encode()).hexdigest()


def clone_job(src: Path, settings: dict, note: str) -> Path:
    jid = uuid.uuid4().hex
    dst = JOBS / jid
    dst.mkdir(parents=True)
    for name in COPY_TREE:
        sp = src / name
        if sp.is_dir():
            shutil.copytree(sp, dst / name)
    for name in COPY_FILES:
        sp = src / name
        if sp.is_file():
            shutil.copy2(sp, dst / name)
    # Prefer source project views/hashes; override settings.
    base = json.loads((src / "project.json").read_text(encoding="utf-8-sig"))
    spec = {
        "schema": 1,
        "views": list(base.get("views", ["front"])),
        "settings": settings,
        "input_hashes": dict(base.get("input_hashes", {})),
        "note": note,
        "cloned_from": src.name,
    }
    write_json(dst / "project.json", spec)
    write_json(
        dst / "state.json",
        {
            "id": jid,
            "status": "queued",
            "created": time.time(),
            "settings": settings,
            "views": spec["views"],
            "stage": None,
            "completed_stages": 0,
            "stages": [],
        },
    )
    # Seed cache for reusable stages under the NEW fingerprint; drop finalize.
    fp = fingerprint_for(spec)
    keep = []
    for stage, outs in [
        ("prepare", [dst / "prepared" / f"{v}.png" for v in spec["views"]]),
        ("shape", [dst / "shape.glb", dst / "shape_report.json"]),
        (
            "uv",
            [dst / "controls" / "uv_mesh.npz"]
            + [dst / "controls" / f"render_{k}_multiview_{n}.png" for k in ("normal", "position") for n in range(6)],
        ),
        (
            "paint",
            [dst / "paint" / f"{kind}_{n}.png" for kind in ("albedo", "mr") for n in range(6)],
        ),
        ("bake", [dst / "textured_pbr.glb", dst / "textured_color.glb"]),
        ("hybrid_a3", [dst / "hybrid_a3" / "report.json", dst / "textured_hybrid_a3_color.glb"]),
    ]:
        if all(p.is_file() for p in outs):
            keep.append(
                (
                    stage,
                    {
                        "fingerprint": fp,
                        "files": {str(p.relative_to(dst)): sha(p) for p in outs},
                    },
                )
            )
    if settings.get("face") and (dst / "face" / "report.json").is_file() and (dst / "face" / "Face_1_0.glb").is_file():
        outs = [dst / "face" / "report.json", dst / "face" / "Face_1_0.glb"]
        keep.append(
            (
                "face",
                {
                    "fingerprint": fp,
                    "files": {str(p.relative_to(dst)): sha(p) for p in outs},
                },
            )
        )
    write_json(dst / "cache.json", {name: entry for name, entry in keep})
    # Ensure candidate exists
    cand = dst / CANDIDATE_REL
    if not cand.is_file():
        raise FileNotFoundError(f"missing candidate after clone: {cand}")
    return dst


def content_lineage(candidate: Path, output: Path) -> dict:
    import numpy as np
    import trimesh
    from PIL import Image

    def load_mesh(p: Path):
        scene = trimesh.load(p, process=False)
        return next(iter(scene.geometry.values()))

    def atlas_rgba(mesh, slot: str):
        tex = getattr(mesh.visual.material, slot, None)
        if tex is None:
            return None
        if hasattr(tex, "convert"):
            im = tex.convert("RGBA")
        else:
            im = Image.fromarray(np.asarray(tex)).convert("RGBA")
        return hashlib.sha256(im.tobytes()).hexdigest(), im.size

    a, b = load_mesh(candidate), load_mesh(output)
    geom_a = hashlib.sha256(
        a.vertices.astype("float64").tobytes()
        + a.faces.astype("int64").tobytes()
        + (a.visual.uv.astype("float64").tobytes() if getattr(a.visual, "uv", None) is not None else b"")
    ).hexdigest()
    geom_b = hashlib.sha256(
        b.vertices.astype("float64").tobytes()
        + b.faces.astype("int64").tobytes()
        + (b.visual.uv.astype("float64").tobytes() if getattr(b.visual, "uv", None) is not None else b"")
    ).hexdigest()
    alb_a, alb_b = atlas_rgba(a, "baseColorTexture"), atlas_rgba(b, "baseColorTexture")
    mr_a, mr_b = atlas_rgba(a, "metallicRoughnessTexture"), atlas_rgba(b, "metallicRoughnessTexture")
    return {
        "geom_sha_match": geom_a == geom_b,
        "geom_sha": geom_a,
        "albedo_rgba_match": bool(alb_a and alb_b and alb_a[0] == alb_b[0]),
        "albedo_sha": alb_a[0] if alb_a else None,
        "mr_rgba_match": bool(mr_a and mr_b and mr_a[0] == mr_b[0]),
        "mr_sha": mr_a[0] if mr_a else None,
        "candidate_sha256": sha(candidate),
        "output_sha256": sha(output),
        "candidate_bytes": candidate.stat().st_size,
        "output_bytes": output.stat().st_size,
    }


def run_one(entry: dict) -> dict:
    src = entry["src"]
    settings = {
        "quality": "standard",
        "triangles": 100000,
        "height_cm": float(entry["height_cm"]),
        "texture_size": 2048,
        "textures": True,
        "face": bool(entry["face"]),
        "rig": False,
        "seed": 42,
        "hybrid_a3": True,
        "paint_multiref": True,
        "texture_sr": "pil",
        "finalize_candidate": CANDIDATE_REL,
        "face_source": FACE_SOURCE_LABEL,
    }
    job = clone_job(src, settings, entry["note"])
    log_path = job / "finalize_auto_gate_run.log"
    t0 = time.time()
    # Drive through Studio pipeline Job (not manual stages.py-only).
    j = Job(job, CFG)
    j.run()
    state = json.loads((job / "state.json").read_text(encoding="utf-8-sig"))
    elapsed = time.time() - t0
    result = {}
    if (job / "result.json").is_file():
        result = json.loads((job / "result.json").read_text(encoding="utf-8-sig"))
    cand = job / CANDIDATE_REL
    out = job / "output.glb"
    lineage = content_lineage(cand, out) if out.is_file() and cand.is_file() else {"error": "missing glb"}
    ok = (
        state.get("status") == "complete"
        and result.get("finalize_candidate") == CANDIDATE_REL
        and result.get("face_source") == FACE_SOURCE_LABEL
        and result.get("production_accepted") is False
        and lineage.get("geom_sha_match")
        and lineage.get("albedo_rgba_match")
        and lineage.get("mr_rgba_match")
    )
    summary = {
        "label": entry["label"],
        "job": str(job),
        "job_id": job.name,
        "cloned_from": src.name,
        "status": state.get("status"),
        "error": state.get("error"),
        "seconds": elapsed,
        "settings": settings,
        "result": result,
        "lineage": lineage,
        "preview_color_exists": (job / "preview_color.glb").is_file(),
        "hybrid_report_exists": (job / "hybrid_a3" / "report.json").is_file(),
        "ok": bool(ok),
        "log": str(log_path),
    }
    write_json(job / "finalize_auto_gate_proof.json", summary)
    write_json(VIS / f"{entry['label']}_proof.json", summary)
    log_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"label": entry["label"], "job": job.name, "ok": ok, "status": state.get("status")}, indent=2), flush=True)
    return summary


def main():
    results = []
    for entry in SOURCES:
        print(f"=== AUTO FINALIZE GATE: {entry['label']} ===", flush=True)
        results.append(run_one(entry))
    gate = {
        "created": time.strftime("%Y-%m-%d %H:%M:%S Europe/Warsaw"),
        "candidate_rel": CANDIDATE_REL,
        "face_source": FACE_SOURCE_LABEL,
        "production_accepted": False,
        "defaults_flipped": False,
        "jobs": results,
        "two_consecutive_ok": all(r.get("ok") for r in results) and len(results) == 2,
    }
    write_json(VIS / "summary.json", gate)
    write_json(JOBS / "_gate_finalize_candidate_auto_summary.json", gate)
    print(json.dumps({"two_consecutive_ok": gate["two_consecutive_ok"], "jobs": [r["job_id"] for r in results]}, indent=2), flush=True)
    if not gate["two_consecutive_ok"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
