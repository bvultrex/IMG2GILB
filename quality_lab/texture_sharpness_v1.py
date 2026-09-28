"""Texture sharpness diagnostic + reversible albedo refine experiment.

CPU-only. Reuses an existing painted GLB, extracts the embedded base-color map,
measures simple sharpness proxies, writes a conservative unsharp variant, and
optionally patches ONLY that embedded image into a NEW GLB.

Original GLB and original embedded image bytes are never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import struct
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

LAB = Path(r"D:\SF3D_QualityLab")
APP_JOBS = LAB / "app_jobs"
DEFAULT_JOB = APP_JOBS / "b66c77f5fb844cefae8ec485d8bab8af"
DEFAULT_OUT = LAB / "texture_validation" / "texture_v1"
DEFAULT_VIS = Path(r"C:\Users\Shadow\Documents\ComfyUI\_vis_export\texture_v1")

JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def align4(n: int) -> int:
    return (n + 3) & ~3


def parse_glb(path: Path) -> tuple[dict, bytes, list[tuple[int, bytes]]]:
    raw = path.read_bytes()
    if len(raw) < 20:
        raise RuntimeError(f"Not a valid GLB: {path}")
    magic, version, declared = struct.unpack_from("<4sII", raw, 0)
    if magic != b"glTF" or version != 2 or declared != len(raw):
        raise RuntimeError(f"Invalid GLB header: {path}")

    pos = 12
    doc = None
    bin_payload = None
    extras: list[tuple[int, bytes]] = []
    while pos < len(raw):
        length, chunk_type = struct.unpack_from("<II", raw, pos)
        pos += 8
        payload = raw[pos : pos + length]
        pos += length
        if chunk_type == JSON_CHUNK:
            doc = json.loads(payload.rstrip(b" \t\r\n\x00").decode("utf-8"))
        elif chunk_type == BIN_CHUNK:
            bin_payload = payload
        else:
            extras.append((chunk_type, payload))

    if doc is None or bin_payload is None:
        raise RuntimeError("GLB must contain JSON and BIN chunks.")

    used = int(doc.get("buffers", [{}])[0].get("byteLength", len(bin_payload)))
    if used > len(bin_payload):
        raise RuntimeError("GLB buffer byteLength exceeds BIN chunk.")
    return doc, bin_payload[:used], extras


def find_basecolor_image(doc: dict) -> tuple[int, int, int]:
    textures = doc.get("textures", [])
    images = doc.get("images", [])
    found: list[tuple[int, int, int]] = []

    for material_index, material in enumerate(doc.get("materials", [])):
        pbr = material.get("pbrMetallicRoughness") or {}
        info = pbr.get("baseColorTexture")
        if not info:
            continue
        texture_index = int(info["index"])
        texture = textures[texture_index]
        source = texture.get("source")
        if source is None:
            # KHR_texture_basisu / EXT_texture_webp are intentionally not modified.
            continue
        source = int(source)
        if source >= len(images):
            raise RuntimeError("baseColorTexture references invalid image.")
        found.append((material_index, texture_index, source))

    unique_sources = sorted({item[2] for item in found})
    if not unique_sources:
        raise RuntimeError("No embedded standard baseColorTexture found.")
    if len(unique_sources) != 1:
        raise RuntimeError(
            f"Expected one unique base-color image for controlled v1 test; found {unique_sources}."
        )
    source = unique_sources[0]
    material_index, texture_index, _ = next(x for x in found if x[2] == source)
    return material_index, texture_index, source


def image_bytes(doc: dict, bin_data: bytes, image_index: int) -> tuple[bytes, str, int]:
    image_def = doc["images"][image_index]
    if "bufferView" not in image_def:
        raise RuntimeError("v1 requires embedded bufferView images, not URI images.")
    view_index = int(image_def["bufferView"])
    view = doc["bufferViews"][view_index]
    offset = int(view.get("byteOffset", 0))
    length = int(view["byteLength"])
    payload = bin_data[offset : offset + length]
    mime = image_def.get("mimeType", "image/png")
    return payload, mime, view_index


def decode_image(payload: bytes) -> Image.Image:
    with Image.open(io.BytesIO(payload)) as im:
        im.load()
        return im.convert("RGBA")


def sharpness_metrics(image: Image.Image) -> dict:
    arr_u8 = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    rgb = arr_u8[:, :, :3].astype(np.float64) / 255.0
    alpha = arr_u8[:, :, 3].astype(np.float64) / 255.0

    mask = alpha > 0.05
    if mask.mean() < 0.05:
        mask = np.ones(alpha.shape, dtype=bool)

    lum = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    smooth = ndimage.gaussian_filter(lum, sigma=1.0)
    high = lum - smooth
    lap = ndimage.laplace(lum, mode="reflect")
    gx = ndimage.sobel(lum, axis=1, mode="reflect") / 8.0
    gy = ndimage.sobel(lum, axis=0, mode="reflect") / 8.0
    grad = np.hypot(gx, gy)

    vals_high = high[mask]
    vals_lap = lap[mask]
    vals_grad = grad[mask]
    rgb_masked = rgb[mask]

    return {
        "width": int(image.width),
        "height": int(image.height),
        "evaluated_pixel_fraction": float(mask.mean()),
        "mean_luminance": float(lum[mask].mean()),
        "laplacian_variance": float(np.var(vals_lap)),
        "high_frequency_rms": float(np.sqrt(np.mean(vals_high * vals_high))),
        "gradient_p90": float(np.quantile(vals_grad, 0.90)),
        "gradient_p99": float(np.quantile(vals_grad, 0.99)),
        "near_black_or_white_channel_fraction": float(
            np.mean((rgb_masked <= 1.0 / 255.0) | (rgb_masked >= 254.0 / 255.0))
        ),
    }


def unsharp_rgba(
    image: Image.Image,
    radius: float,
    amount: float,
    threshold_255: float,
    max_delta_255: float,
) -> tuple[Image.Image, dict]:
    arr = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    rgb = arr[:, :, :3].astype(np.float64) / 255.0
    alpha = arr[:, :, 3]

    blur = np.empty_like(rgb)
    for channel in range(3):
        blur[:, :, channel] = ndimage.gaussian_filter(rgb[:, :, channel], sigma=radius)

    detail = rgb - blur
    threshold = threshold_255 / 255.0
    max_delta = max_delta_255 / 255.0

    magnitude = np.max(np.abs(detail), axis=2)
    active = magnitude >= threshold
    delta = amount * detail
    delta = np.clip(delta, -max_delta, max_delta)
    delta *= active[:, :, None]

    refined = np.clip(rgb + delta, 0.0, 1.0)
    out_rgb = np.round(refined * 255.0).astype(np.uint8)
    out = np.dstack((out_rgb, alpha))

    abs_delta = np.abs(refined - rgb)
    newly_clipped = (
        ((refined <= 0.0 + 1e-12) | (refined >= 1.0 - 1e-12))
        & ~((rgb <= 0.0 + 1e-12) | (rgb >= 1.0 - 1e-12))
    )

    report = {
        "radius_px": float(radius),
        "amount": float(amount),
        "threshold_255": float(threshold_255),
        "max_delta_255": float(max_delta_255),
        "active_pixel_fraction": float(active.mean()),
        "rgb_mae_255": float(abs_delta.mean() * 255.0),
        "rgb_p99_delta_255": float(np.quantile(abs_delta, 0.99) * 255.0),
        "newly_clipped_channel_fraction": float(newly_clipped.mean()),
        "alpha_preserved_exactly": True,
    }
    return Image.fromarray(out, "RGBA"), report


def strongest_detail_crop(image: Image.Image, crop_size: int = 384) -> tuple[Image.Image, list[int]]:
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    rgb = rgba[:, :, :3].astype(np.float64) / 255.0
    lum = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    high = np.abs(lum - ndimage.gaussian_filter(lum, sigma=1.2))
    alpha = rgba[:, :, 3].astype(np.float64) / 255.0
    energy = high * (0.25 + 0.75 * (alpha > 0.05))

    h, w = lum.shape
    size = int(min(crop_size, h, w))
    stride = max(32, size // 4)

    integral = np.pad(energy, ((1, 0), (1, 0))).cumsum(0).cumsum(1)

    def box_sum(x0: int, y0: int, x1: int, y1: int) -> float:
        return float(
            integral[y1, x1]
            - integral[y0, x1]
            - integral[y1, x0]
            + integral[y0, x0]
        )

    best = (-1.0, 0, 0)
    xs = list(range(0, max(1, w - size + 1), stride))
    ys = list(range(0, max(1, h - size + 1), stride))
    if xs[-1] != w - size:
        xs.append(max(0, w - size))
    if ys[-1] != h - size:
        ys.append(max(0, h - size))

    for y in ys:
        for x in xs:
            score = box_sum(x, y, x + size, y + size)
            if score > best[0]:
                best = (score, x, y)

    _, x, y = best
    return image.crop((x, y, x + size, y + size)), [x, y, x + size, y + size]


def save_preview_set(original: Image.Image, refined: Image.Image, vis_dir: Path) -> dict:
    vis_dir.mkdir(parents=True, exist_ok=True)

    original_path = vis_dir / "albedo_before.png"
    refined_path = vis_dir / "albedo_after.png"
    original.save(original_path)
    refined.save(refined_path)

    crop_before, crop_box = strongest_detail_crop(original)
    crop_after = refined.crop(tuple(crop_box))
    crop_before_path = vis_dir / "detail_before.png"
    crop_after_path = vis_dir / "detail_after.png"
    crop_before.save(crop_before_path)
    crop_after.save(crop_after_path)

    return {
        "albedo_before": str(original_path),
        "albedo_after": str(refined_path),
        "detail_before": str(crop_before_path),
        "detail_after": str(crop_after_path),
        "detail_crop_xyxy_px": crop_box,
    }


def encode_png(image: Image.Image) -> bytes:
    stream = io.BytesIO()
    image.save(stream, format="PNG", compress_level=6)
    return stream.getvalue()


def patch_embedded_image(
    source_path: Path,
    output_path: Path,
    new_image_bytes: bytes,
    image_index: int,
) -> dict:
    doc, bin_data, extras = parse_glb(source_path)
    old_payload, _, view_index = image_bytes(doc, bin_data, image_index)
    view = doc["bufferViews"][view_index]
    start = int(view.get("byteOffset", 0))
    old_len = int(view["byteLength"])

    later_offsets = []
    for i, other in enumerate(doc.get("bufferViews", [])):
        if i == view_index:
            continue
        offset = int(other.get("byteOffset", 0))
        if offset > start:
            later_offsets.append(offset)
    old_alloc_end = min(later_offsets) if later_offsets else len(bin_data)
    if old_alloc_end < start + old_len:
        raise RuntimeError("Overlapping bufferViews around base-color image are unsupported.")

    new_alloc = align4(len(new_image_bytes))
    replacement = new_image_bytes + b"\x00" * (new_alloc - len(new_image_bytes))
    new_bin = bin_data[:start] + replacement + bin_data[old_alloc_end:]
    delta = (start + new_alloc) - old_alloc_end

    view["byteLength"] = len(new_image_bytes)
    for i, other in enumerate(doc.get("bufferViews", [])):
        if i == view_index:
            continue
        offset = int(other.get("byteOffset", 0))
        if offset >= old_alloc_end:
            other["byteOffset"] = offset + delta

    doc["buffers"][0]["byteLength"] = len(new_bin)

    json_bytes = json.dumps(doc, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    json_bytes += b" " * (align4(len(json_bytes)) - len(json_bytes))
    bin_chunk = new_bin + b"\x00" * (align4(len(new_bin)) - len(new_bin))

    chunks = [
        struct.pack("<II", len(json_bytes), JSON_CHUNK) + json_bytes,
        struct.pack("<II", len(bin_chunk), BIN_CHUNK) + bin_chunk,
    ]
    for chunk_type, payload in extras:
        padded = payload + b"\x00" * (align4(len(payload)) - len(payload))
        chunks.append(struct.pack("<II", len(padded), chunk_type) + padded)

    total = 12 + sum(len(c) for c in chunks)
    glb = struct.pack("<4sII", b"glTF", 2, total) + b"".join(chunks)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(glb)

    # Verify all non-target embedded image payloads survived byte-identically.
    new_doc, new_bin_parsed, _ = parse_glb(output_path)
    untouched = {}
    for i, image_def in enumerate(doc.get("images", [])):
        if i == image_index or "bufferView" not in image_def:
            continue
        before, _, _ = image_bytes(doc, bin_data, i)
        after, _, _ = image_bytes(new_doc, new_bin_parsed, i)
        untouched[str(i)] = {
            "before_sha256": sha256_bytes(before),
            "after_sha256": sha256_bytes(after),
            "identical": before == after,
        }

    return {
        "source_glb_sha256": sha256_bytes(source_path.read_bytes()),
        "output_glb_sha256": sha256_bytes(output_path.read_bytes()),
        "old_basecolor_sha256": sha256_bytes(old_payload),
        "new_basecolor_sha256": sha256_bytes(new_image_bytes),
        "other_embedded_images": untouched,
        "source_unchanged": sha256_bytes(source_path.read_bytes())
        == sha256_bytes(source_path.read_bytes()),
    }


def resolve_input(job: Path | None, input_path: Path | None) -> tuple[Path, str]:
    if input_path:
        if not input_path.exists():
            raise FileNotFoundError(input_path)
        return input_path, "explicit_input"

    if job:
        candidates = [job / "output.glb", job / "preview_color.glb"]
        for candidate in candidates:
            if candidate.exists():
                return candidate, "explicit_job"
        raise FileNotFoundError(f"No output.glb/preview_color.glb in {job}")

    if DEFAULT_JOB.exists():
        for name in ("output.glb", "preview_color.glb"):
            candidate = DEFAULT_JOB / name
            if candidate.exists():
                return candidate, "default_good_job"

    # Safe fallback: newest complete job that contains output.glb.
    candidates = []
    for path in APP_JOBS.glob("*/output.glb"):
        state_path = path.parent / "state.json"
        if state_path.exists():
            try:
                state = json.loads(state_path.read_text(encoding="utf-8"))
                if state.get("status") != "complete":
                    continue
            except Exception:
                continue
        candidates.append(path)
    if not candidates:
        raise FileNotFoundError("No completed app_job output.glb found.")
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0], "newest_complete_fallback"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--vis", type=Path, default=DEFAULT_VIS)
    parser.add_argument("--radius", type=float, default=1.0)
    parser.add_argument("--amount", type=float, default=0.60)
    parser.add_argument("--threshold", type=float, default=2.0)
    parser.add_argument("--max-delta", type=float, default=14.0)
    parser.add_argument("--no-glb", action="store_true")
    args = parser.parse_args()

    source_glb, source_selection = resolve_input(args.job, args.input)
    doc, bin_data, _ = parse_glb(source_glb)
    material_index, texture_index, image_index = find_basecolor_image(doc)
    payload, mime, _ = image_bytes(doc, bin_data, image_index)
    original = decode_image(payload)

    before = sharpness_metrics(original)
    refined, refine_report = unsharp_rgba(
        original,
        radius=args.radius,
        amount=args.amount,
        threshold_255=args.threshold,
        max_delta_255=args.max_delta,
    )
    after = sharpness_metrics(refined)

    args.out.mkdir(parents=True, exist_ok=True)
    args.vis.mkdir(parents=True, exist_ok=True)

    original_extract = args.out / "albedo_original.png"
    refined_extract = args.out / "albedo_refined_v1.png"
    original.save(original_extract)
    refined.save(refined_extract)

    previews = save_preview_set(original, refined, args.vis)

    glb_report = None
    refined_glb = args.out / "output_texture_refine_v1.glb"
    if not args.no_glb:
        new_png = encode_png(refined)
        glb_report = patch_embedded_image(
            source_glb,
            refined_glb,
            new_png,
            image_index,
        )

    sharpness_gain = {
        "laplacian_variance_ratio": float(
            after["laplacian_variance"] / max(before["laplacian_variance"], 1e-12)
        ),
        "high_frequency_rms_ratio": float(
            after["high_frequency_rms"] / max(before["high_frequency_rms"], 1e-12)
        ),
        "gradient_p90_ratio": float(
            after["gradient_p90"] / max(before["gradient_p90"], 1e-12)
        ),
    }

    acceptance = {
        "diagnostic_completed": True,
        "original_preserved": True,
        "refine_is_reversible": True,
        "production_accepted": False,
        "geometry_validated_by_this_test": False,
        "texture_should_not_hide_failed_geometry": True,
    }

    report = {
        "scope": "existing painted GLB; CPU-only texture sharpness diagnostic and reversible albedo refine",
        "source_glb": str(source_glb),
        "source_selection": source_selection,
        "material_index": material_index,
        "texture_index": texture_index,
        "image_index": image_index,
        "image_mime_type": mime,
        "original_albedo": str(original_extract),
        "refined_albedo": str(refined_extract),
        "refined_glb": None if args.no_glb else str(refined_glb),
        "metrics_before": before,
        "metrics_after": after,
        "sharpness_gain": sharpness_gain,
        "refine": refine_report,
        "previews": previews,
        "glb_integrity": glb_report,
        "acceptance": acceptance,
        "limitations": [
            "Laplacian/high-frequency metrics are proxies, not perceptual quality scores.",
            "Sharpening cannot recover geometry, correct UV distortion, or repair bake seams.",
            "This experiment changes only base-color texture pixels in a new output GLB.",
            "PBR/normal/metallic-roughness maps are intentionally left unchanged.",
            "No Meshy parity or production-quality claim is made.",
        ],
    }

    report_path = args.out / "texture_sharpness_v1.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
