"""CPU-only: rebuild hybrid PBR sidecars retaining A0 metallicRoughnessTexture pixels.

Albedo/baseColor comes from an existing hybrid color GLB (or optional albedo PNG + UV mesh).
Does not overwrite baselines; writes NEW *_pbr_mr_retain.glb names.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image


def sha_rgba(img: Image.Image) -> str:
    return hashlib.sha256(img.convert("RGBA").tobytes()).hexdigest()


def load_mesh_and_albedo(color_glb: Path):
    scene = trimesh.load(str(color_glb), force="scene", process=False)
    mesh = list(scene.geometry.values())[0]
    mat = mesh.visual.material
    albedo = mat.baseColorTexture
    if albedo is None:
        raise SystemExit(f"no baseColorTexture in {color_glb}")
    return mesh, Image.fromarray(np.asarray(albedo).copy())


def load_mr(source_pbr: Path):
    scene = trimesh.load(str(source_pbr), force="scene", process=False)
    mesh = list(scene.geometry.values())[0]
    mat = mesh.visual.material
    mr = mat.metallicRoughnessTexture
    if mr is None:
        raise SystemExit(f"no metallicRoughnessTexture in {source_pbr}")
    return (
        Image.fromarray(np.asarray(mr).copy()),
        float(getattr(mat, "metallicFactor", 1.0) or 1.0),
        float(getattr(mat, "roughnessFactor", 1.0) or 1.0),
        sha_rgba(mr if isinstance(mr, Image.Image) else Image.fromarray(np.asarray(mr))),
    )


def export_pbr(mesh, albedo: Image.Image, mr: Image.Image, metal: float, rough: float, out: Path) -> dict:
    mesh = mesh.copy()
    mesh.visual.material = trimesh.visual.material.PBRMaterial(
        baseColorTexture=albedo,
        metallicRoughnessTexture=mr,
        metallicFactor=metal,
        roughnessFactor=rough,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(out)
    # verify by reload
    scene = trimesh.load(str(out), force="scene", process=False)
    m2 = list(scene.geometry.values())[0]
    mr2 = m2.visual.material.metallicRoughnessTexture
    bc2 = m2.visual.material.baseColorTexture
    return {
        "out": str(out),
        "file_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "mr_rgba_sha256": sha_rgba(mr2),
        "bc_rgba_sha256": sha_rgba(bc2),
        "n_verts": len(m2.vertices),
        "n_faces": len(m2.faces),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-pbr", required=True, type=Path, help="A0 / baseline PBR GLB (MR retained)")
    p.add_argument("--hybrid-color", action="append", required=True, type=Path, help="hybrid color GLB (repeatable)")
    p.add_argument("--out-suffix", default="_pbr_mr_retain.glb")
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()

    mr, metal, rough, a0_mr_sha = load_mr(args.source_pbr)
    records = []
    for color_glb in args.hybrid_color:
        mesh, albedo = load_mesh_and_albedo(color_glb)
        # NEW name: replace _color.glb or append
        name = color_glb.name
        if name.endswith("_color.glb"):
            out = color_glb.with_name(name[: -len("_color.glb")] + args.out_suffix.replace(".glb", "") + ".glb")
            # textured_hybrid_phase2b_color.glb -> textured_hybrid_phase2b_pbr_mr_retain.glb
            out = color_glb.with_name(name.replace("_color.glb", "_pbr_mr_retain.glb"))
        else:
            out = color_glb.with_name(color_glb.stem + args.out_suffix)
        rec = export_pbr(mesh, albedo, mr, metal, rough, out)
        rec["source_color"] = str(color_glb)
        rec["mr_matches_a0"] = rec["mr_rgba_sha256"] == a0_mr_sha
        records.append(rec)
        print(json.dumps(rec, indent=2))

    report = {
        "source_pbr": str(args.source_pbr),
        "a0_mr_rgba_sha256": a0_mr_sha,
        "records": records,
        "all_mr_match_a0": all(r["mr_matches_a0"] for r in records),
        "studio_default_flip": False,
        "baselines_preserved": True,
        "note": "NEW sidecars only; old hybrid *_pbr.glb left untouched for before/after compare.",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("REPORT", args.report)
    print("all_mr_match_a0", report["all_mr_match_a0"])
    if not report["all_mr_match_a0"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
