"""Sequential fresh-input integration test. Never copies or seeds stage caches."""
import json
import shutil
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'desktop'))
from pipeline import Job, sha, write_json


def main():
    cfg = json.loads((ROOT / 'desktop/runtime.json').read_text(encoding='utf-8-sig'))
    sources = Path(cfg['jobs_dir'])
    destination = ROOT.parent / 'quality_runs'
    destination.mkdir(exist_ok=True)
    cfg['jobs_dir'] = str(destination)
    manifest_path = destination / ('fresh_gate_' + time.strftime('%Y%m%d_%H%M%S') + '.json')
    manifest = {'test': 'fresh inputs, no seeded cache', 'runs': [], 'production_accepted': False}
    for label, source_id, height in [('ranger', '4abf740c34c9487ba818455efe460833', 170.),
                                     ('bust', '9c9d771bfdf844bc8e15b60509ef308d', 40.)]:
        if shutil.disk_usage(destination).free < 8 * 1024**3:
            raise RuntimeError('Less than 8 GiB free; preserve assets and stop.')
        source = sources / source_id
        old = json.loads((source / 'project.json').read_text(encoding='utf-8-sig'))
        path = destination / uuid.uuid4().hex
        (path / 'inputs').mkdir(parents=True)
        hashes = {}
        for view in old['views']:
            target = path / 'inputs' / (view + '.png')
            shutil.copy2(source / 'inputs' / target.name, target)
            hashes[view] = sha(target)
        settings = {'quality': 'standard', 'triangles': 100000, 'height_cm': height,
                    'texture_size': 2048, 'textures': True, 'face': False, 'rig': False,
                    'seed': 42, 'hybrid_a3': True, 'paint_multiref': False,
                    'texture_sr': 'pil', 'finalize_candidate': 'textured_hybrid_a3_pbr.glb',
                    'face_source': 'hybrid_a3_pbr'}
        write_json(path / 'project.json', {'schema': 1, 'views': old['views'],
                   'settings': settings, 'input_hashes': hashes})
        write_json(path / 'state.json', {'id': path.name, 'status': 'queued', 'created': time.time()})
        assert not (path / 'cache.json').exists()
        manifest['runs'].append({'fixture': label, 'path': str(path), 'source': source_id,
                                'inputs_only': True, 'status': 'running'})
        write_json(manifest_path, manifest)
        print('START ' + str(path), flush=True)
        job = Job(path, cfg)
        job.run()
        manifest['runs'][-1]['status'] = job.state['status']
        manifest['runs'][-1]['error'] = job.state.get('error')
        write_json(manifest_path, manifest)
        print(json.dumps(manifest['runs'][-1]), flush=True)
        if job.state['status'] != 'complete':
            raise RuntimeError('Stop sequential test at first failure; inspect job.log')


if __name__ == '__main__':
    main()
