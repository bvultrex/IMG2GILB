"""Run a preserved face-ISO comparison only after the fresh sequence succeeds."""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--job',type=Path,required=True)
p.add_argument('--after-job',type=Path,required=True)
a=p.parse_args()
root=Path(__file__).resolve().parents[1]
deadline=time.monotonic()+1800
while True:
    state=json.loads((a.after_job/'state.json').read_text())
    if state['status']=='complete':break
    if state['status'] not in ('queued','running'):
        raise RuntimeError('Preceding job did not succeed: '+state['status'])
    if time.monotonic()>deadline:raise TimeoutError('Preceding job still pending; no experiment started')
    time.sleep(5)
job=a.job.resolve()
out=job/'codex_face_iso'
out.mkdir(exist_ok=False)
baseline=job/'output.glb'
digest=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
before=digest(baseline)
script=root/'quality_lab/project_hybrid_a3.py'
cmd=[sys.executable,str(script),'--job',str(job),'--out',str(out),
     '--face-iso','--source-pbr',str(job/'textured_pbr.glb'),
     '--color-glb',str(out/'candidate_color.glb'),
     '--pbr-glb',str(out/'candidate_pbr.glb')]
manifest={'command':cmd,'script_sha256':digest(script),'baseline_sha256':before,
          'status':'running','production_accepted':False}
(out/'execution.json').write_text(json.dumps(manifest,indent=2))
with (out/'execution.log').open('w',encoding='utf-8') as log:
    result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,cwd=root)
manifest['returncode']=result.returncode
manifest['baseline_unchanged']=before==digest(baseline)
manifest['status']='complete' if result.returncode==0 and manifest['baseline_unchanged'] else 'failed'
(out/'execution.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest),flush=True)
assert manifest['status']=='complete'
