"""Append an albedo image; preserve every original binary byte and scene property."""
import argparse
import copy
import hashlib
import json
import struct
from pathlib import Path


def replace(source, texture, output):
    raw = source.read_bytes()
    magic, version, length = struct.unpack_from('<III', raw)
    assert (magic, version, length) == (0x46546C67, 2, len(raw))
    chunks = []
    cursor = 12
    while cursor < len(raw):
        size, kind = struct.unpack_from('<II', raw, cursor)
        chunks.append((kind, raw[cursor + 8:cursor + 8 + size]))
        cursor += 8 + size
    assert [kind for kind, _ in chunks] == [0x4E4F534A, 0x004E4942]
    doc = json.loads(chunks[0][1])
    old = copy.deepcopy(doc)
    assert len(doc['buffers']) == 1 and 'uri' not in doc['buffers'][0]
    # A single material is intentional: ambiguous multi-material assets must fail.
    assert len(doc['materials']) == 1
    pbr = doc['materials'][0]['pbrMetallicRoughness']
    texture_index = pbr['baseColorTexture']['index']
    new_texture = copy.deepcopy(doc['textures'][texture_index])
    assert 'extensions' not in new_texture
    png = texture.read_bytes()
    assert png.startswith(b'\x89PNG\r\n\x1a\n')
    binary = chunks[1][1]
    offset = len(binary)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(png)})
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png'})
    new_texture['source'] = len(doc['images']) - 1
    doc['textures'].append(new_texture)
    pbr['baseColorTexture']['index'] = len(doc['textures']) - 1
    binary += png
    doc['buffers'][0]['byteLength'] = len(binary)
    binary += b'\x00' * (-len(binary) % 4)
    # Check all document fields except the explicit append/repoint operation.
    restored = copy.deepcopy(doc)
    for field in ('buffers', 'bufferViews', 'images', 'textures'):
        restored[field] = old[field]
    restored['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index'] = texture_index
    assert restored == old
    assert binary[:offset] == chunks[1][1]
    encoded = json.dumps(doc, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    result = struct.pack('<III', magic, version, 28 + len(encoded) + len(binary))
    result += struct.pack('<II', len(encoded), 0x4E4F534A) + encoded
    result += struct.pack('<II', len(binary), 0x004E4942) + binary
    with output.open('xb') as handle:
        handle.write(result)
    return {'source_sha256': hashlib.sha256(raw).hexdigest(),
            'output_sha256': hashlib.sha256(result).hexdigest(),
            'preserved_binary_bytes': offset, 'only_albedo_repointed': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('texture', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(replace(args.source, args.texture, args.output), indent=2))
