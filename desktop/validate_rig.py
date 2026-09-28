"""Validate the skinning contract of a local GLB; not an animation quality score."""
import argparse
import json
import struct
from pathlib import Path
import numpy as np


def load_glb(path):
    raw = Path(path).read_bytes()
    magic, version, length = struct.unpack_from('<III', raw)
    if magic != 0x46546C67 or version != 2 or length != len(raw):
        raise ValueError('Invalid GLB header')
    offset = 12
    document = None
    binary = None
    while offset < length:
        size, kind = struct.unpack_from('<II', raw, offset)
        offset += 8
        if offset + size > length:
            raise ValueError('Truncated GLB chunk')
        chunk = raw[offset:offset + size]
        if kind == 0x4E4F534A:
            document = json.loads(chunk)
        elif kind == 0x004E4942:
            binary = chunk
        offset += size
    if document is None or binary is None:
        raise ValueError('JSON and embedded binary required')
    return document, binary


def accessor(doc, binary, index):
    if not isinstance(index, int) or not 0 <= index < len(doc['accessors']):
        raise ValueError('Invalid accessor index')
    a = doc['accessors'][index]
    if 'sparse' in a:
        raise ValueError('Sparse accessors require a separate validator')
    view = doc['bufferViews'][a['bufferView']]
    if view.get('buffer', 0) != 0 or doc['buffers'][0].get('uri'):
        raise ValueError('Only embedded GLB buffers supported')
    dtype = np.dtype({5121: 'u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[a['componentType']])
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
    start = view.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = view.get('byteStride', width * dtype.itemsize)
    end = start + max(0, a['count'] - 1) * stride + width * dtype.itemsize
    if a['count'] <= 0 or stride < width * dtype.itemsize or end > min(len(binary), view.get('byteOffset', 0) + view['byteLength']):
        raise ValueError('Invalid accessor bounds')
    data = np.ndarray((a['count'], width), dtype=dtype, buffer=binary,
                      offset=start, strides=(stride, dtype.itemsize)).copy()
    if a.get('normalized'):
        if dtype.kind != 'u':
            raise ValueError('Unsupported normalized component type')
        data = data.astype(np.float64) / np.iinfo(dtype).max
    return data


def validate(doc, binary):
    nodes = doc.get('nodes', [])
    skins = doc.get('skins', [])
    if not skins:
        raise ValueError('No skeleton/skin in GLB')
    parents = {}
    for i, node in enumerate(nodes):
        for key in ('matrix', 'translation', 'rotation', 'scale'):
            if key in node and not np.isfinite(node[key]).all():
                raise ValueError('Nonfinite node transform')
        for child in node.get('children', []):
            if not 0 <= child < len(nodes) or child in parents:
                raise ValueError('Invalid or multiply parented node')
            parents[child] = i
    for i in range(len(nodes)):
        seen = set()
        while i in parents:
            if i in seen:
                raise ValueError('Cyclic skeleton hierarchy')
            seen.add(i)
            i = parents[i]
    reports = []
    for node in nodes:
        if 'skin' not in node:
            continue
        if not 0 <= node['skin'] < len(skins) or not 0 <= node.get('mesh', -1) < len(doc.get('meshes', [])):
            raise ValueError('Invalid mesh/skin binding')
        skin = skins[node['skin']]
        joints = skin['joints']
        if len(joints) < 2 or len(set(joints)) != len(joints) or any(not 0 <= j < len(nodes) for j in joints):
            raise ValueError('Invalid joint list')
        if 'inverseBindMatrices' in skin:
            matrices = accessor(doc, binary, skin['inverseBindMatrices'])
            if matrices.shape != (len(joints), 16) or not np.isfinite(matrices).all():
                raise ValueError('Invalid inverse bind matrices')
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            attrs = primitive['attributes']
            position = accessor(doc, binary, attrs['POSITION'])
            if not np.isfinite(position).all():
                raise ValueError('Nonfinite positions')
            weights = []
            for key in sorted(k for k in attrs if k.startswith('JOINTS_')):
                suffix = key.split('_')[1]
                weight_key = 'WEIGHTS_' + suffix
                joint_data = accessor(doc, binary, attrs[key])
                weight_data = accessor(doc, binary, attrs[weight_key])
                if joint_data.shape != (len(position), 4) or weight_data.shape != joint_data.shape:
                    raise ValueError('Skin attribute count mismatch')
                if joint_data.dtype.kind != 'u' or np.any(joint_data >= len(joints)):
                    raise ValueError('Joint index outside skin')
                if not np.isfinite(weight_data).all() or np.any(weight_data < 0):
                    raise ValueError('Invalid skin weights')
                weights.append(weight_data)
            if not weights:
                raise ValueError('Skinned mesh has no weights')
            totals = np.concatenate(weights, axis=1).sum(axis=1)
            max_error = float(np.max(np.abs(totals - 1)))
            if max_error > .01:
                raise ValueError('Unweighted or nonnormalized vertices')
            reports.append({'vertices': len(position), 'joints': len(joints),
                            'max_weight_sum_error': max_error})
    if not reports:
        raise ValueError('No mesh is bound to a skeleton')
    return {'status': 'passed', 'primitives': reports,
            'animations': len(doc.get('animations', [])),
            'limitations': ['Does not prove anatomical bone placement or deformation quality',
                            'Animation channels are counted, not visually validated']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('glb')
    parser.add_argument('--report')
    args = parser.parse_args()
    try:
        result = validate(*load_glb(args.glb))
    except (ValueError, KeyError, IndexError, struct.error) as exc:
        result = {'status': 'failed', 'error': str(exc)}
    result['file'] = str(Path(args.glb).resolve())
    text = json.dumps(result, indent=2)
    if args.report:
        Path(args.report).write_text(text, encoding='utf-8')
    print(text)
    raise SystemExit(0 if result['status'] == 'passed' else 1)
