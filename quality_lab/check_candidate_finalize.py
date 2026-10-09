"""Exercise the real Studio finalize stage in a new isolated directory; no caches."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
import numpy as np
import trimesh

p = argparse.ArgumentParser()
p.add_argument('--candidate', type=Path, required=True)
p.add_argument('--project', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
root = Path(__file__).resolve().parents[1]
config_path = root/'desktop/runtime.json'
config = json.loads(config_path.read_text(encoding='utf-8-sig'))
spec = json.loads(a.project.read_text(encoding='utf-8-sig'))
spec['settings'].update(face=False, rig=False, finalize_candidate='candidate.glb',
                        face_source='experimental_reference_ownership')
shutil.copy2(a.candidate, a.out/'candidate.glb')
(a.out/'project.json').write_text(json.dumps(spec, indent=2))
cmd = [config['python'], str(root/'desktop/stages.py'), 'finalize', str(a.out), str(config_path)]
result = subprocess.run(cmd, capture_output=True, text=True)
(a.out/'execution.log').write_text(result.stdout+'\n'+result.stderr)
assert result.returncode == 0, result.stderr
def mesh(path):
    scene = trimesh.load(path, force='scene', process=False)
    assert len(scene.geometry) == 1
    return next(iter(scene.geometry.values()))
before, after = mesh(a.candidate), mesh(a.out/'output.glb')
checks = {name: np.array_equal(getattr(before, name), getattr(after, name)) for name in ('vertices', 'faces')}
checks['uv'] = np.array_equal(before.visual.uv, after.visual.uv)
for channel in ('baseColorTexture', 'metallicRoughnessTexture'):
    checks[channel] = np.array_equal(np.asarray(getattr(before.visual.material, channel).convert('RGBA')),
                                     np.asarray(getattr(after.visual.material, channel).convert('RGBA')))
assert all(checks.values()), checks
report = dict(scope='real finalize only; NOT fresh end-to-end', checks=checks,
              source_sha256=hashlib.sha256(a.candidate.read_bytes()).hexdigest(),
              output_sha256=hashlib.sha256((a.out/'output.glb').read_bytes()).hexdigest(),
              production_accepted=False)
(a.out/'finalize_audit.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report), flush=True)
