"""Read-only CPU comparison of exported texture variants; no rendering."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh


def signature(path):
    scene = trimesh.load(path, force='scene', process=False)
    meshes = []
    for mesh in scene.geometry.values():
        item = {}
        for name, value in [('vertices', mesh.vertices), ('faces', mesh.faces),
                            ('uv', getattr(mesh.visual, 'uv', None))]:
            if value is None:
                item[name] = None
            else:
                value = np.ascontiguousarray(value)
                item[name] = {'shape': list(value.shape), 'sha256': hashlib.sha256(value.tobytes()).hexdigest()}
        material = mesh.visual.material
        for name in ('baseColorTexture', 'metallicRoughnessTexture'):
            image = getattr(material, name, None)
            item[name] = None if image is None else {
                'size': list(image.size),
                'sha256': hashlib.sha256(image.convert('RGBA').tobytes()).hexdigest()}
        meshes.append(item)
    return {'file': path.name, 'file_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'meshes': meshes}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='+', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    records = [signature(p) for p in args.files]
    baseline = records[0]['meshes']
    for record in records:
        record['matches_baseline'] = {
            k: [m[k] for m in record['meshes']] == [m[k] for m in baseline]
            for k in ('vertices', 'faces', 'uv', 'metallicRoughnessTexture')}
    report = {'records': records, 'limitations': 'Mesh-array and texture comparison only; does not verify scene transforms, skeleton, visual alignment or rendered seams.'}
    with args.out.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps([{'file': r['file'], 'matches': r['matches_baseline']} for r in records], indent=2))

