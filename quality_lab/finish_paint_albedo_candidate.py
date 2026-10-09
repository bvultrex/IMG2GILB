"""Finish a verified sequential Paint run without replacing baseline MR/geometry.

Run only after sampler/decoder coordinator exits. Existing outputs are never
overwritten; this is an explicit lab operation, not a production preset.
"""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
from PIL import Image
from replace_glb_albedo_exact import replace

p=argparse.ArgumentParser()
p.add_argument('--job',type=Path,required=True)
p.add_argument('--paint',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
a.job,a.paint,a.out=[x.resolve() for x in (a.job,a.paint,a.out)]
report=json.loads((a.paint/'sequential_report.json').read_text())
inputs=json.loads((a.paint/'sequential_inputs.json').read_text())
assert report['status']=='passed' and report['stage']=='complete', 'Generation is not complete'
expected={f'{kind}_{i}.png' for kind in ('albedo','mr') for i in range(6)}
assert set(report['outputs'])==expected
for name,digest in report['outputs'].items():
    path=a.paint/name
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest, name
    with Image.open(path) as im:
        im.load();assert im.size==(inputs['resolution'],inputs['resolution'])
for name,digest in inputs['files'].items():
    if Path(name).name.startswith('render_'):
        assert hashlib.sha256((a.job/'controls'/Path(name).name).read_bytes()).hexdigest()==digest, 'Controls do not match'
assert not (a.paint/'albedo_atlas_2K.png').exists(), 'Preserve existing bake'
a.out.mkdir(parents=True,exist_ok=False)
lab=Path('D:/SF3D_QualityLab')
here=Path(__file__).resolve().parent
env=os.environ.copy()
env['PATH']=str(lab/'cuda-12.4/bin')+';'+str(lab/'venv/Lib/site-packages/torch/lib')+';'+env['PATH']
def run(cmd,log):
    with (a.out/log).open('w',encoding='utf-8') as f:
        subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,check=True)
run([sys.executable,str(lab/'bake_paint21.py'),'--input',str(a.paint),'--uv-cache',str(a.job/'controls/uv_mesh.npz'),'--output-prefix',str(a.out/'diagnostic'),'--views','6','--resolution',str(inputs['resolution']),'--upscaler','pil'],'bake.log')
checks=replace(a.job/'textured_pbr.glb',a.paint/'albedo_atlas_2K.png',a.out/'candidate.glb')
(a.out/'albedo_invariants.json').write_text(json.dumps(checks,indent=2))
run([sys.executable,str(here/'check_candidate_finalize.py'),'--candidate',str(a.out/'candidate.glb'),'--project',str(a.job/'project.json'),'--out',str(a.out/'finalized')],'finalize.log')
print(json.dumps({'status':'exported','output':str(a.out/'finalized/output.glb'),'production_accepted':False,'next':'Independent import and matched visual review required'}),flush=True)
