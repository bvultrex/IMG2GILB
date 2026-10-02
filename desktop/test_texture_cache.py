"""CPU regression tests for texture implementation and final PBR cache validity."""
import json
import tempfile
import unittest
from pathlib import Path

from pipeline import Job, hybrid_outputs, texture_code_signature


class TextureCacheTests(unittest.TestCase):
 def test_missing_or_changed_pbr_recomputes_hybrid(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder)
   (root/'state.json').write_text('{}')
   job=Job(root,{})
   outputs=hybrid_outputs(root)
   runs=[]
   def generate():
    runs.append(1)
    for output in outputs:
     output.parent.mkdir(exist_ok=True)
     output.write_bytes(b'original')
   job.cached('hybrid_a3',outputs,generate,'version1')
   job.cached('hybrid_a3',outputs,generate,'version1')
   self.assertEqual(len(runs),1)
   outputs[-1].unlink()
   job.cached('hybrid_a3',outputs,generate,'version1')
   self.assertEqual(len(runs),2)
   outputs[-1].write_bytes(b'corrupt')
   job.cached('hybrid_a3',outputs,generate,'version1')
   self.assertEqual(len(runs),3)

 def test_active_implementation_change_invalidates_signature(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder)
   hybrid=root/'hybrid.py';multi=root/'multi.py'
   hybrid.write_text('hybrid v1');multi.write_text('multi v1')
   cfg={'lab':folder,'hybrid_a3_script':str(hybrid),'paint_multiref_script':str(multi)}
   settings={'textures':True,'hybrid_a3':True,'paint_multiref':True}
   before=texture_code_signature(cfg,settings)
   hybrid.write_text('hybrid v2')
   after=texture_code_signature(cfg,settings)
   self.assertNotEqual(before,after)
   multi.write_text('multi v2')
   self.assertNotEqual(after,texture_code_signature(cfg,settings))
   disabled={'textures':True,'hybrid_a3':False,'paint_multiref':False}
   self.assertEqual(texture_code_signature(cfg,disabled),'')

if __name__=='__main__':unittest.main()
