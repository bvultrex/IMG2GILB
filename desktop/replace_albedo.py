"""Replace one embedded base-colour image without re-exporting mesh or skin data."""
import argparse
import io
import json
import struct
from pathlib import Path
from PIL import Image
from validate_rig import load_glb


def replace(source, texture_source, destination):
    if Path(source).resolve() == Path(destination).resolve():
        raise ValueError('Use a separate output to preserve the original')
    doc, binary = load_glb(source)
    texdoc, texbinary = load_glb(texture_source)
    if len(doc.get('materials', [])) != 1 or len(texdoc.get('materials', [])) != 1:
        raise ValueError('Single-material assets required')
    def image_index(d):
        slot = d['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']
        return d['textures'][slot]['source']
    incoming = texdoc['images'][image_index(texdoc)]
    view = texdoc['bufferViews'][incoming['bufferView']]
    offset = view.get('byteOffset', 0)
    image = Image.open(io.BytesIO(texbinary[offset:offset + view['byteLength']])).convert('RGBA')
    encoded = io.BytesIO()
    image.save(encoded, format='PNG')
    body = bytearray(binary)
    body.extend(b'\0' * (-len(body) % 4))
    start = len(body)
    body.extend(encoded.getvalue())
    vi = len(doc['bufferViews'])
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': start, 'byteLength': len(encoded.getvalue())})
    # A fresh image and texture leave any shared non-colour texture references intact.
    ii = len(doc['images'])
    doc['images'].append({'bufferView': vi, 'mimeType': 'image/png'})
    slot = doc['materials'][0]['pbrMetallicRoughness']['baseColorTexture']
    texture = dict(doc['textures'][slot['index']])
    texture['source'] = ii
    slot['index'] = len(doc['textures'])
    doc['textures'].append(texture)
    doc['buffers'][0]['byteLength'] = len(body)
    raw = json.dumps(doc, separators=(',', ':')).encode()
    raw += b' ' * (-len(raw) % 4)
    body.extend(b'\0' * (-len(body) % 4))
    Path(destination).write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(raw) + len(body))
        + struct.pack('<II', len(raw), 0x4e4f534a) + raw
        + struct.pack('<II', len(body), 0x004e4942) + body)
    outdoc, outbin = load_glb(destination)
    original, _ = load_glb(source)
    for key in ('meshes', 'nodes', 'skins', 'accessors', 'animations'):
        assert outdoc.get(key) == original.get(key), key
    assert outbin[:len(binary)] == binary
    return {'status': 'passed', 'size': list(image.size), 'geometry_skin_original_binary_unchanged': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    parser.add_argument('texture_source')
    parser.add_argument('destination')
    args = parser.parse_args()
    print(json.dumps(replace(args.source, args.texture_source, args.destination)))
