"""Isolated rigging stage. Keep the unrigged export until all checks pass."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
from PIL import Image
from validate_rig import load_glb, accessor, validate


def content_contract(path):
    doc, binary = load_glb(path)
    positions = []
    triangles = 0
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            if primitive.get('mode', 4) != 4:
                raise ValueError('Only triangle meshes supported')
            pos = accessor(doc, binary, primitive['attributes']['POSITION'])
            positions.append(pos)
            count = doc['accessors'][primitive['indices']]['count'] if 'indices' in primitive else len(pos)
            triangles += count // 3
    pixels = []
    for image in doc.get('images', []):
        view = doc['bufferViews'][image['bufferView']]
        start = view.get('byteOffset', 0)
        rgba = Image.open(io.BytesIO(binary[start:start + view['byteLength']])).convert('RGBA')
        pixels.append(hashlib.sha256(rgba.tobytes()).hexdigest())
    pos = np.concatenate(positions)
    def texture(info):
        if not info:
            return None
        entry = doc['textures'][info['index']]
        return {'pixels': pixels[entry['source']], 'texCoord': info.get('texCoord', 0)}
    materials = []
    for material in doc.get('materials', []):
        pbr = material.get('pbrMetallicRoughness', {})
        materials.append({'baseColor': texture(pbr.get('baseColorTexture')),
                          'metallicRoughness': texture(pbr.get('metallicRoughnessTexture')),
                          'baseColorFactor': pbr.get('baseColorFactor', [1, 1, 1, 1]),
                          'metallicFactor': pbr.get('metallicFactor', 1),
                          'roughnessFactor': pbr.get('roughnessFactor', 1),
                          'alphaMode': material.get('alphaMode', 'OPAQUE'),
                          'doubleSided': material.get('doubleSided', False)})
    return {'triangles': triangles, 'vertices': len(pos), 'bounds': [pos.min(0).tolist(), pos.max(0).tolist()],
            'image_pixels': sorted(pixels), 'materials': materials}


def verify_transfer(source, output):
    rig = validate(*load_glb(output))
    before, after = content_contract(source), content_contract(output)
    if before['triangles'] != after['triangles']:
        raise ValueError('Rigging changed triangle count')
    if before['image_pixels'] != after['image_pixels']:
        raise ValueError('Rigging changed texture pixels')
    if before['materials'] != after['materials']:
        raise ValueError('Rigging changed PBR material assignments or factors')
    if not np.allclose(before['bounds'], after['bounds'], atol=1e-5, rtol=1e-5):
        raise ValueError('Rigging changed mesh-coordinate bounds')
    return {'status': 'passed', 'rig': rig, 'before': before, 'after': after,
            'limitations': ['Bounds check is in mesh coordinates; world-space height needs Blender validation',
                            'Structural checks do not prove deformation quality']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('job')
    parser.add_argument('config')
    parser.add_argument('--verify-existing', type=Path)
    args = parser.parse_args()
    job = Path(args.job).resolve()
    config = json.loads(Path(args.config).read_text(encoding='utf-8-sig'))
    source = job / 'output.glb'
    folder = job / 'rig'
    folder.mkdir(exist_ok=True)
    candidate = args.verify_existing or folder / 'candidate.glb'
    if not args.verify_existing:
        env = os.environ.copy()
        env.update(HF_HUB_OFFLINE='1', IMG2GILB_ATTENTION_BACKEND='sdpa', PYTHONUNBUFFERED='1')
        subprocess.run([config['rig_python'], str(Path(config['rig_source']) / 'demo.py'),
                        '--input', str(source), '--output', str(candidate), '--use_transfer'],
                       cwd=config['rig_source'], env=env, check=True)
    report = verify_transfer(source, candidate)
    (folder / 'verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    # Distinct output avoids invalidating the finalized unrigged stage cache.
    destination = job / 'output_rigged.glb'
    temporary = destination.with_suffix('.tmp')
    temporary.write_bytes(candidate.read_bytes())
    temporary.replace(destination)
    result = json.loads((job / 'result.json').read_text(encoding='utf-8'))
    result.update(rigged=True, joints=max(p['joints'] for p in report['rig']['primitives']),
                  vertices=report['after']['vertices'], bytes=destination.stat().st_size)
    from walk_preview import build
    try:
        preview_report = build(destination, job / 'preview_color.glb')
        result['preview_animation'] = True
    except ValueError as exc:
        preview_report = {'status': 'unsupported', 'reason': str(exc)}
        result['preview_animation'] = False
        (job / 'preview_color.glb').write_bytes(destination.read_bytes())
    (folder / 'preview.json').write_text(json.dumps(preview_report, indent=2), encoding='utf-8')
    (job / 'result_rigged.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
