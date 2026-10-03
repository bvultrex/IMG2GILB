"""Phase-1 eval repair: unlit final-GLB renders + true crops + float Laplacian.

Does NOT regenerate paint. Does NOT mutate Zenko sources or Phase-1 bake outputs.
Reads each arm's baked albedo atlas + shared UV mesh (same content as color GLB)
and renders matched unlit front / back / oblique views for A0-A3.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
import trimesh
from PIL import Image, ImageDraw
from scipy import ndimage

JOB = Path(r"D:\SF3D_QualityLab\app_jobs\5e81ac7963f84af2a403fb659cea7513")
PHASE1 = JOB / "quality_jump_phase1"
OUT = Path(r"C:\Users\Shadow\Documents\ComfyUI\_vis_export\quality_jump_phase1_evalfix")
LAB_DOC = Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\quality_lab")
HUNYUAN = Path(r"C:\Users\Shadow\Documents\ComfyUI\Hunyuan3D-2-Lab")
sys.path.insert(0, str(HUNYUAN))
sys.path.insert(0, str(Path(r"D:\SF3D_QualityLab")))

from hy3dgen.texgen.differentiable_renderer.mesh_render import MeshRender, transform_pos  # noqa: E402

ARMS = [
    ("A0_single_pil", "A0"),
    ("A1_multi_pil", "A1"),
    ("A2_single_esrgan", "A2"),
    ("A3_multi_esrgan", "A3"),
]

# Semantic crops on 1024 unlit full-body front (matched across arms).
# Face: upper third; chest: jacket/cross region (not waist/thighs).
CROPS_1024 = {
    "face": (360, 20, 664, 300),
    "chest": (340, 260, 684, 540),
}

VIEWS = [
    ("front", 0.0, 0.0),
    ("back", 0.0, 180.0),
    ("oblique", 8.0, 35.0),
]


class ProjectionRender(MeshRender):
    def _render(self, mvp, pos, pos_idx, uv, uv_idx, tex, resolution, max_mip_level, keep_alpha, filter_mode):
        clip = transform_pos(mvp, pos)
        rast, _ = self.raster_rasterize(clip, pos_idx, resolution=resolution)
        coords, _ = self.raster_interpolate(uv[None, ...], rast, uv_idx)
        color = torch.nn.functional.grid_sample(
            tex.permute(2, 0, 1)[None, ...],
            coords * 2 - 1,
            mode="bilinear",
            padding_mode="border",
            align_corners=True,
        ).permute(0, 2, 3, 1)
        mask = rast[..., -1:].clamp(0, 1)
        return torch.cat([color * mask, mask], dim=-1)[0]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def float_laplacian_metrics(image: Image.Image, alpha_mask: np.ndarray | None = None) -> dict:
    """Signed float Laplacian via scipy.ndimage — no PIL L-mode clipping."""
    arr = np.asarray(image.convert("RGB"), dtype=np.float64)
    lum = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    if alpha_mask is None:
        mask = np.ones(lum.shape, dtype=bool)
    else:
        mask = alpha_mask.astype(bool)
        if mask.mean() < 0.02:
            mask = np.ones(lum.shape, dtype=bool)
    # Classic 4-neighbour Laplacian (signed, float)
    kernel = np.array([[0.0, 1.0, 0.0], [1.0, -4.0, 1.0], [0.0, 1.0, 0.0]], dtype=np.float64)
    lap = ndimage.convolve(lum, kernel, mode="reflect")
    # Also ndimage.laplace for cross-check
    lap2 = ndimage.laplace(lum, mode="reflect")
    smooth = ndimage.gaussian_filter(lum, sigma=1.0)
    high = lum - smooth
    vals = lap[mask]
    vals2 = lap2[mask]
    return {
        "laplacian_var_signed_conv": float(np.var(vals)),
        "laplacian_var_ndimage": float(np.var(vals2)),
        "hf_rms": float(np.sqrt(np.mean(high[mask] ** 2))),
        "mean_luminance": float(lum[mask].mean()),
        "evaluated_pixel_fraction": float(mask.mean()),
        "note": "float64 luminance; signed convolution; mask=silhouette if available",
    }


def load_uv_mesh(job: Path) -> trimesh.Trimesh:
    data = np.load(job / "controls" / "uv_mesh.npz")
    mesh = trimesh.Trimesh(
        vertices=data["vertices"],
        faces=data["faces"],
        process=False,
        visual=trimesh.visual.TextureVisuals(uv=data["uv"]),
    )
    mesh.vertex_normals = data["vertex_normals"]
    return mesh


def extract_glb_basecolor_sha(glb: Path) -> str | None:
    """Best-effort: hash PNG/JPEG bytes of first baseColor image in GLB."""
    try:
        raw = glb.read_bytes()
        if raw[:4] != b"glTF":
            return None
        import struct

        pos = 12
        doc = None
        bin_payload = None
        while pos < len(raw):
            length, ctype = struct.unpack_from("<II", raw, pos)
            pos += 8
            payload = raw[pos : pos + length]
            pos += length
            if ctype == 0x4E4F534A:
                doc = json.loads(payload.rstrip(b" \t\r\n\x00").decode("utf-8"))
            elif ctype == 0x004E4942:
                bin_payload = payload
        if not doc or bin_payload is None:
            return None
        images = doc.get("images", [])
        if not images:
            return None
        img0 = images[0]
        if "bufferView" in img0:
            bv = doc["bufferViews"][int(img0["bufferView"])]
            off = int(bv.get("byteOffset", 0))
            ln = int(bv["byteLength"])
            return hashlib.sha256(bin_payload[off : off + ln]).hexdigest()
        return None
    except Exception as e:
        return f"error:{e}"


def sheet(paths: list[Path], labels: list[str], out: Path, cols: int = 2, pad: int = 10) -> None:
    imgs = [Image.open(p).convert("RGB") for p in paths]
    w, h = imgs[0].size
    rows = (len(imgs) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + 36 + pad) + pad), (28, 28, 30))
    draw = ImageDraw.Draw(canvas)
    for i, (im, lab) in enumerate(zip(imgs, labels)):
        r, c = divmod(i, cols)
        x = pad + c * (w + pad)
        y = pad + r * (h + 36 + pad)
        canvas.paste(im, (x, y))
        draw.text((x, y + h + 6), lab, fill=(220, 220, 220))
    canvas.save(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    mesh = load_uv_mesh(JOB)
    renderer = ProjectionRender(default_resolution=2048, texture_size=2048)
    renderer.load_mesh(mesh)

    report = {
        "created": datetime.now().isoformat(timespec="seconds"),
        "job": str(JOB),
        "method": "unlit MeshRender from UV mesh + arm bake atlas (content of color GLB)",
        "bugs_addressed": [
            "crops from final bake/GLB path, not native albedo_0 pre-SR",
            "face+chest semantic boxes on 1024 unlit front",
            "float signed Laplacian (no PIL L-mode clip)",
            "explicit front/back/oblique camera azim/elev",
        ],
        "views": [{"name": n, "elev": e, "azim": a} for n, e, a in VIEWS],
        "crops_1024": CROPS_1024,
        "arms": {},
    }

    for arm_dir, short in ARMS:
        d = PHASE1 / arm_dir
        atlas = d / "albedo_atlas_2K.png"
        glb = d / f"textured_{arm_dir}_color.glb"
        assert atlas.exists(), atlas
        assert glb.exists(), glb

        arm_out = OUT / arm_dir
        arm_out.mkdir(parents=True, exist_ok=True)

        atlas_sha = sha256(atlas)
        glb_sha = sha256(glb)
        embedded_sha = extract_glb_basecolor_sha(glb)

        tex = np.asarray(Image.open(atlas).convert("RGB"), dtype=np.float32) / 255.0
        renderer.set_texture(tex)

        arm_entry = {
            "atlas": str(atlas),
            "atlas_sha256": atlas_sha,
            "color_glb": str(glb),
            "color_glb_sha256": glb_sha,
            "embedded_basecolor_sha256": embedded_sha,
            "atlas_matches_prior_phase1_summary": None,
            "renders": {},
            "crops": {},
            "metrics": {},
        }

        # Atlas metrics (post-SR bake atlas)
        arm_entry["metrics"]["atlas"] = float_laplacian_metrics(Image.open(atlas))

        for vname, elev, azim in VIEWS:
            rgba = renderer.render(elev, azim, return_type="np")
            rgb = (rgba[:, :, :3].clip(0, 1) * 255).astype(np.uint8)
            alpha = rgba[:, :, 3]
            im = Image.fromarray(rgb).resize((1024, 1024), Image.Resampling.LANCZOS)
            # resize alpha with nearest-ish via array
            alpha_img = Image.fromarray((alpha.clip(0, 1) * 255).astype(np.uint8)).resize(
                (1024, 1024), Image.Resampling.BILINEAR
            )
            alpha_np = np.asarray(alpha_img) > 16
            path = arm_out / f"unlit_{vname}.png"
            im.save(path)
            arm_entry["renders"][vname] = {
                "path": str(path),
                "sha256": sha256(path),
                "elev": elev,
                "azim": azim,
            }
            arm_entry["metrics"][f"unlit_{vname}"] = float_laplacian_metrics(im, alpha_np)

            if vname == "front":
                for cname, box in CROPS_1024.items():
                    crop = im.crop(box)
                    cpath = arm_out / f"crop_front_{cname}.png"
                    crop.save(cpath)
                    arm_entry["crops"][cname] = {
                        "path": str(cpath),
                        "sha256": sha256(cpath),
                        "box": list(box),
                    }
                    arm_entry["metrics"][f"crop_front_{cname}"] = float_laplacian_metrics(crop)

            # also save back/oblique upper crop for seam glance
            if vname in ("back", "oblique"):
                box = CROPS_1024["chest"]
                crop = im.crop(box)
                cpath = arm_out / f"crop_{vname}_chest.png"
                crop.save(cpath)
                arm_entry["crops"][f"{vname}_chest"] = {
                    "path": str(cpath),
                    "sha256": sha256(cpath),
                    "box": list(box),
                }

        # copy atlas mid window for atlas-level SR check (post-bake)
        at = Image.open(atlas).convert("RGB")
        mid = at.crop((768, 768, 1280, 1280))
        mid_path = arm_out / "atlas_mid.png"
        mid.save(mid_path)
        arm_entry["crops"]["atlas_mid"] = {"path": str(mid_path), "sha256": sha256(mid_path)}

        report["arms"][arm_dir] = arm_entry
        print(f"[ok] {arm_dir} atlas={atlas_sha[:12]} glb={glb_sha[:12]}", flush=True)

    # Contact sheets
    labels = [a[0] for a in ARMS]
    for key, fname in [
        ("crop_front_face.png", "sheet_front_face.png"),
        ("crop_front_chest.png", "sheet_front_chest.png"),
        ("unlit_front.png", "sheet_unlit_front.png"),
        ("unlit_back.png", "sheet_unlit_back.png"),
        ("unlit_oblique.png", "sheet_unlit_oblique.png"),
        ("atlas_mid.png", "sheet_atlas_mid.png"),
    ]:
        paths = [OUT / a / key.replace("crop_front_", "crop_front_").replace("crop_front_face.png", "crop_front_face.png") for a, _ in ARMS]
        # normalize key lookup
        real = []
        for a, _ in ARMS:
            p = OUT / a / key
            if not p.exists() and key.startswith("crop_front_"):
                p = OUT / a / key
            real.append(p)
        if all(p.exists() for p in real):
            sheet(real, labels, OUT / fname, cols=2)

    # Prove A0!=A2 on repaired face crops (SR must differ if bake atlas differs)
    a0_face = sha256(OUT / "A0_single_pil" / "crop_front_face.png")
    a2_face = sha256(OUT / "A2_single_esrgan" / "crop_front_face.png")
    a0_chest = sha256(OUT / "A0_single_pil" / "crop_front_chest.png")
    a2_chest = sha256(OUT / "A2_single_esrgan" / "crop_front_chest.png")
    report["sanity"] = {
        "A0_vs_A2_face_crop_identical": a0_face == a2_face,
        "A0_face_sha256": a0_face,
        "A2_face_sha256": a2_face,
        "A0_vs_A2_chest_crop_identical": a0_chest == a2_chest,
        "A0_chest_sha256": a0_chest,
        "A2_chest_sha256": a2_chest,
        "prior_bug_was_identical_pre_SR_albedo0_crops": True,
    }

    report["seconds"] = time.monotonic() - start
    (OUT / "eval_repair_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Markdown
    md_lines = [
        "# QUALITY_JUMP_PHASE1_EVAL_REPAIR",
        "",
        f"Created: {report['created']} (Europe/Warsaw local box time)",
        "",
        "## Purpose",
        "Repair Phase-1 evaluation bugs flagged by Zenko (Issue #1 comment 5958345088).",
        "No paint regeneration. Baselines A0–A3 bake/GLB preserved.",
        "",
        "## Bugs fixed",
        "1. Crops now come from **unlit renders of final bake atlases** (content of color GLBs), not native `albedo_0` pre-SR.",
        "2. Face + chest boxes retargeted on 1024 full-body front (chest = jacket region, not waist/thighs).",
        "3. Laplacian = **float64 signed convolution** / `ndimage.laplace` (no PIL L-mode clip).",
        "4. Cameras explicit: front azim=0, back azim=180, oblique elev=8 azim=35.",
        "",
        "## Staging",
        f"- Vis: `{OUT}`",
        f"- Report JSON: `{OUT / 'eval_repair_report.json'}`",
        "",
        "## Sanity (A0 vs A2 face crop)",
        f"- Identical? **{report['sanity']['A0_vs_A2_face_crop_identical']}** (must be False if SR reaches final render)",
        f"- A0 face SHA: `{a0_face}`",
        f"- A2 face SHA: `{a2_face}`",
        "",
        "## Per-arm hashes + metrics (atlas + unlit front)",
        "",
        "| Arm | Atlas SHA256 | Color GLB SHA256 | Atlas lap_var (signed) | Unlit front lap_var | Face crop SHA |",
        "|-----|--------------|------------------|------------------------|---------------------|---------------|",
    ]
    for arm_dir, _ in ARMS:
        e = report["arms"][arm_dir]
        md_lines.append(
            f"| {arm_dir} | `{e['atlas_sha256'][:16]}…` | `{e['color_glb_sha256'][:16]}…` | "
            f"{e['metrics']['atlas']['laplacian_var_signed_conv']:.2f} | "
            f"{e['metrics']['unlit_front']['laplacian_var_signed_conv']:.2f} | "
            f"`{e['crops']['face']['sha256'][:16]}…` |"
        )
    md_lines += [
        "",
        "## Sheets",
        "- `sheet_unlit_front.png` / `sheet_unlit_back.png` / `sheet_unlit_oblique.png`",
        "- `sheet_front_face.png` / `sheet_front_chest.png` / `sheet_atlas_mid.png`",
        "",
        "## Notes for Zenko",
        "- A0 remains **conservative control** for Phase 2 Hybrid — not declared quality winner.",
        "- No Studio default flip. No Meshy parity claim.",
        "- Metric script: new file `quality_lab/eval_repair_phase1_final_glb.py` (does not mutate prior make_crops_metrics.py).",
        "",
    ]
    md_path = OUT / "QUALITY_JUMP_PHASE1_EVAL_REPAIR.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    # also copy into quality_lab
    (LAB_DOC / "QUALITY_JUMP_PHASE1_EVAL_REPAIR.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(json.dumps({"out": str(OUT), "sanity": report["sanity"], "seconds": report["seconds"]}, indent=2))


if __name__ == "__main__":
    main()
