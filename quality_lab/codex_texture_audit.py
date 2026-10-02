"""CPU-only, read-only texture lineage audit. Requires Pillow and numpy.

Usage: python codex_texture_audit.py JOB_DIRECTORY --out report.json
No model loading, resampling, asset export, or source mutation.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct

import numpy as np
from PIL import Image


def digest(data):
    return hashlib.sha256(data).hexdigest()


def image_record(data):
    with Image.open(io.BytesIO(data)) as image:
        pixels = image.convert("RGBA")
        return {"size": list(image.size), "mode": image.mode,
                "encoded_sha256": digest(data),
                "rgba_sha256": digest(struct.pack('<II', *image.size) + pixels.tobytes())}


def glb_images(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from('<4sII', data)
    if magic != b'glTF' or version != 2 or length != len(data):
        raise ValueError(f'Invalid GLB header: {path.name}')
    offset, document, binary = 12, None, None
    while offset < len(data):
        size, kind = struct.unpack_from('<II', data, offset)
        offset += 8
        payload = data[offset:offset + size]
        if len(payload) != size:
            raise ValueError('Truncated GLB chunk')
        if kind == 0x4E4F534A:
            document = json.loads(payload)
        elif kind == 0x004E4942:
            binary = payload
        offset += size
    records = []
    for index, item in enumerate(document.get('images', [])):
        if 'bufferView' not in item:
            records.append({'index': index, 'unsupported_external_image': True})
            continue
        view = document['bufferViews'][item['bufferView']]
        if view.get('buffer', 0) != 0 or binary is None:
            raise ValueError('Image buffer unavailable')
        start = view.get('byteOffset', 0)
        record = image_record(binary[start:start + view['byteLength']])
        record['index'] = index
        records.append(record)
    return {'sha256': digest(data), 'images': records,
            'materials': document.get('materials', []),
            'textures': document.get('textures', []),
            'samplers': document.get('samplers', [])}


def audit(job):
    files = sorted(set(job.glob('prepared/*.png')) | set(job.glob('paint/*.png')))
    images = {str(p.relative_to(job)): image_record(p.read_bytes()) for p in files}
    assets = {p.name: glb_images(p) for p in sorted(job.glob('*.glb'))}
    for asset in assets.values():
        for item in asset['images']:
            item['pixel_identical_to'] = [name for name, record in images.items()
                if item.get('rgba_sha256') == record['rgba_sha256']]
    result = {'job_id': job.name, 'images': images, 'glbs': assets,
              'limitations': ['Image identity does not test UV mapping, view consistency or viewer filtering.',
                'UV area sum is not rasterized occupancy and can include overlap.',
                'No sharpness metric is interpreted as reference fidelity.']}
    for name in ('report.json', 'bake_report.json'):
        path = job / 'paint' / name
        if path.exists():
            report = json.loads(path.read_text(encoding='utf-8-sig'))
            result[name] = {k: v for k, v in report.items()
                if k in ('resolution', 'reference_count', 'views', 'native_resolution', 'atlas', 'upscaler')}
    cache = job / 'controls' / 'uv_mesh.npz'
    if cache.exists():
        with np.load(cache, allow_pickle=False) as data:
            uv, faces, vertices = data['uv'], data['faces'], data['vertices']
            triangles = uv[faces]
            a, b = triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
            area = np.abs(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]) / 2
            world = vertices[faces]
            surface = np.linalg.norm(np.cross(world[:, 1]-world[:, 0], world[:, 2]-world[:, 0]), axis=1)/2
            valid = surface > 1e-12
            density = np.sqrt(area[valid]/surface[valid])
            result['uv'] = {'triangles': len(faces), 'area_sum': float(area.sum()),
                'degenerate_uv_triangles': int((area < 1e-12).sum()),
                'linear_density_percentiles_5_50_95': np.percentile(density, [5, 50, 95]).tolist(),
                'cache_sha256': digest(cache.read_bytes())}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('job', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Output exists; choose a new report filename to preserve audit history.')
    result = audit(args.job)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'job_id': result['job_id'], 'image_count': len(result['images']),
        'glb_count': len(result['glbs']), 'uv': result.get('uv'), 'out': str(args.out)}, indent=2))

