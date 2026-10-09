"""Create a genuinely unlit preview without re-exporting geometry or animation."""
import json
import struct
from pathlib import Path

def build_unlit(source, destination):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError('Preview must not replace the PBR source')
    raw = source.read_bytes()
    if len(raw) < 20 or struct.unpack_from('<III', raw) != (0x46546C67, 2, len(raw)):
        raise ValueError('Invalid GLB header')
    size, kind = struct.unpack_from('<II', raw, 12)
    if kind != 0x4E4F534A or 20+size > len(raw):
        raise ValueError('Missing GLB JSON chunk')
    doc = json.loads(raw[20:20+size])
    if not doc.get('materials'):
        raise ValueError('No explicit material to preview')
    extension = 'KHR_materials_unlit'
    for material in doc['materials']:
        # Lighting extensions are irrelevant to this diagnostic material.
        material['extensions'] = {extension: {}}
    for key in ('extensionsUsed', 'extensionsRequired'):
        doc[key] = list(dict.fromkeys(doc.get(key, []) + [extension]))
    encoded = json.dumps(doc, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    tail = raw[20+size:]
    destination.write_bytes(struct.pack('<III', 0x46546C67, 2, 20+len(encoded)+len(tail))
                           + struct.pack('<II', len(encoded), kind) + encoded + tail)
    return {'mode': 'unlit', 'original_binary_chunks_preserved': True}
