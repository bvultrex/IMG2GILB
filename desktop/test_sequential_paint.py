"""CPU-only integration checks for opt-in Paint dispatch and output promotion."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from pipeline import Job, paint_resolution, texture_code_signature

class SequentialPaintTests(unittest.TestCase):
 def test_defaults_and_unsupported_multiref(self):
  self.assertEqual(paint_resolution({'quality':'fast'}),'512')
  self.assertEqual(paint_resolution({'quality':'standard','paint_resolution':1024}),'768')
  settings={'quality':'standard','experimental_paint_sequential':True,'paint_resolution':1024,'paint_multiref':False}
  self.assertEqual(paint_resolution(settings),'1024')
  for value in (True,None):
   with self.assertRaises(ValueError):paint_resolution(dict(settings,paint_multiref=value))
  with self.assertRaises(ValueError):paint_resolution(dict(settings,paint_resolution=4096))
  with self.assertRaises(ValueError):paint_resolution(dict(settings,experimental_paint_ff_chunk='false'))

 def test_ff_chunk_dispatch_is_explicit_opt_in(self):
  class StopBeforeGPU(Exception):pass
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);(root/'state.json').write_text('{}')
   job=Job(root,{'lab':directory,'python':sys.executable})
   calls=[]
   def capture(cmd):
    calls.append(cmd);raise StopBeforeGPU()
   job.run_process=capture
   settings={'quality':'standard','experimental_paint_sequential':True,'paint_multiref':False,'paint_resolution':1024}
   for enabled in (False,True):
    with self.assertRaises(StopBeforeGPU):
     job.sequential_paint(dict(settings,experimental_paint_ff_chunk=enabled))
    self.assertEqual('--ff-chunk' in calls[-1],enabled)
    self.assertEqual(calls[-1][calls[-1].index('--resolution')+1],'1024')

 def test_corrupt_attempt_cannot_replace_existing_paint(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);(root/'state.json').write_text('{}');(root/'paint').mkdir()
   prior=root/'paint/albedo_0.png';prior.write_bytes(b'prior')
   job=Job(root,{'lab':directory,'python':sys.executable})
   def fake_child(cmd):
    attempt=Path(cmd[cmd.index('--output')+1]);attempt.mkdir(parents=True)
    outputs={}
    for kind in ('albedo','mr'):
     for i in range(6):
      name=f'{kind}_{i}.png';(attempt/name).write_bytes(b'new')
      outputs[name]=hashlib.sha256(b'new').hexdigest()
    (attempt/'mr_5.png').write_bytes(b'corrupt')
    (attempt/'sequential_report.json').write_text(json.dumps({'status':'passed','stage':'complete','outputs':outputs}))
   job.run_process=fake_child
   with self.assertRaises(RuntimeError):job.sequential_paint({'quality':'standard','experimental_paint_sequential':True,'paint_multiref':False,'paint_resolution':1024})
   self.assertEqual(prior.read_bytes(),b'prior')

 def test_decode_code_changes_fingerprint(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   for name in ('run_paint_sequential.py','run_paint21_checkpoint.py','decode_paint_checkpoint.py'):(root/name).write_text('v1')
   cfg={'lab':directory,'paint_sequential_script':str(root/'run_paint_sequential.py')}
   settings={'textures':True,'experimental_paint_sequential':True,'paint_multiref':False}
   old=texture_code_signature(cfg,settings)
   (root/'decode_paint_checkpoint.py').write_text('v2')
   self.assertNotEqual(old,texture_code_signature(cfg,settings))

 def test_nested_windows_process_guards(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);(root/'state.json').write_text('{}')
   job=Job(root,{})
   lab=Path(__file__).resolve().parents[1]/'quality_lab'
   code=f"import sys;from pathlib import Path;sys.path.insert(0,{str(lab)!r});from run_paint_sequential import run_child;run_child([sys.executable,'-c',\"print('nested child completed')\"],Path({str(root/'nested.log')!r}))"
   job.run_process([sys.executable,'-c',code])
   self.assertIn('nested child completed',(root/'nested.log').read_text())
   self.assertIsNone(job.snapshot()['worker'])

if __name__=='__main__':unittest.main()
