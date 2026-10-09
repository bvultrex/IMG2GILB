"""Exercise actual finalize with a legal GLB lacking explicit materials."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import trimesh

class UntexturedFinalizeTests(unittest.TestCase):
 def test_geometry_only_export_needs_no_material(self):
  desktop=Path(__file__).resolve().parent
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   trimesh.creation.box(extents=[.5,1,.2]).export(root/'shape.glb')
   (root/'project.json').write_text(json.dumps({'settings':{
       'textures':False,'face':False,'height_cm':100,'texture_size':2048}}))
   # Finalize does not load GPU models. Minimal local config avoids production runtime coupling.
   (root/'config.json').write_text(json.dumps({'lab':directory,'hunyuan':directory}))
   result=subprocess.run([sys.executable,str(desktop/'stages.py'),'finalize',directory,
                          str(root/'config.json')],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   self.assertEqual((root/'output.glb').read_bytes(),(root/'preview_color.glb').read_bytes())
   report=json.loads((root/'result.json').read_text())
   self.assertIsNone(report['texture_size'])
   self.assertEqual(report['triangles'],12)
   self.assertAlmostEqual(report['height_cm'],100)

if __name__=='__main__':unittest.main()
