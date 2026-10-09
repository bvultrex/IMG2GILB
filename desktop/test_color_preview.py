import json
import struct
import tempfile
import unittest
from pathlib import Path
from color_preview import build_unlit

class ColorPreviewTests(unittest.TestCase):
    def test_keeps_skin_animation_texture_and_binary(self):
        doc = {'asset': {'version':'2.0'}, 'materials':[{'pbrMetallicRoughness':{
            'baseColorTexture':{'index':0}, 'metallicFactor':.8}}],
            'nodes':[{'skin':0}], 'skins':[{'joints':[1]}],
            'animations':[{'name':'walk'}], 'textures':[{'source':0}]}
        encoded=json.dumps(doc).encode(); encoded+=b' '*(-len(encoded)%4)
        tail=struct.pack('<II',4,0x004E4942)+b'1234'
        raw=struct.pack('<III',0x46546C67,2,20+len(encoded)+len(tail))+struct.pack('<II',len(encoded),0x4E4F534A)+encoded+tail
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.glb'; target=Path(folder)/'preview.glb'
            source.write_bytes(raw); build_unlit(source,target)
            result=target.read_bytes(); size=struct.unpack_from('<I',result,12)[0]
            changed=json.loads(result[20:20+size])
            self.assertEqual(result[20+size:],tail)
            self.assertEqual(source.read_bytes(),raw)
            for key in ('nodes','skins','animations','textures'):
                self.assertEqual(changed[key],doc[key])
            self.assertEqual(changed['materials'][0]['pbrMetallicRoughness'],doc['materials'][0]['pbrMetallicRoughness'])
            self.assertEqual(changed['materials'][0]['extensions']['KHR_materials_unlit'],{})
            self.assertIn('KHR_materials_unlit',changed['extensionsRequired'])
            with self.assertRaises(ValueError): build_unlit(source,source)

if __name__=='__main__': unittest.main()
