"""Fast contract tests for desktop cancellation and stage-cache integrity."""
import json,subprocess,tempfile,time,unittest
from pathlib import Path
from pipeline import Job,write_json
from process_guard import ProcessGuard,identity
class Contracts(unittest.TestCase):
 def test_status_write_survives_transient_windows_sharing_error(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as d:
   target=Path(d)/'state.json';write_json(target,{'status':'running'})
   real=Path.replace;attempts=[]
   def transient(source,destination):
    attempts.append(1)
    if len(attempts)<3:raise PermissionError('Windows sharing conflict')
    return real(source,destination)
   with patch.object(Path,'replace',transient):write_json(target,{'status':'complete'})
   self.assertEqual(json.loads(target.read_text())['status'],'complete')
   self.assertEqual(len(attempts),3);self.assertEqual(list(Path(d).glob('*.tmp')),[])
 def test_cache_detects_changed_artifact(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);write_json(root/'state.json',{'id':'test','status':'queued'})
   job=Job(root,{});dest=root/'value';calls=[]
   def action():calls.append(1);dest.write_text('valid')
   job.cached('test',[dest],action,'v1');job.cached('test',[dest],action,'v1');self.assertEqual(len(calls),1)
   dest.write_text('corrupt');job.cached('test',[dest],action,'v1');self.assertEqual(len(calls),2);self.assertEqual(dest.read_text(),'valid')
   job.cached('test',[dest],action,'v2');self.assertEqual(len(calls),3)
 def test_guard_kills_child_tree(self):
  import sys
  child=subprocess.Popen([sys.executable,'-c','import os,time;print(os.getpid(),flush=True);time.sleep(30)'],stdout=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW|4)
  guard=ProcessGuard(child);leaf=int(child.stdout.readline());self.assertIsNotNone(identity(leaf));guard.close();child.wait(timeout=5)
  for _ in range(20):
   if identity(leaf) is None:break
   time.sleep(.05)
  self.assertIsNone(identity(leaf))
  child.stdout.close()
 def test_worker_failure_updates_state(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);write_json(root/'state.json',{'id':'test','status':'queued'});job=Job(root,{})
   job.run();self.assertEqual(job.state['status'],'failed');self.assertTrue(job.state['error'])
if __name__=='__main__':unittest.main(verbosity=2)
