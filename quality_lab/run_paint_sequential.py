"""Opt-in six-view Paint runner: sample, exit, then decode in a fresh process.

Existing Studio defaults are not changed. Resume requires matching input/code
fingerprints and a checksummed sampler checkpoint, never just existing PNGs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'desktop'))
from process_guard import ProcessGuard

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_json(path, value):
    temp = path.with_suffix('.pending')
    temp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temp.replace(path)

def valid_checkpoint(output, resolution):
    report = json.loads((output/'generation_checkpoint_report.json').read_text())
    if (report.get('status') != 'sampling_complete_decode_pending'
            or report.get('views') != 6 or report.get('resolution') != resolution
            or report.get('checkpoint_sha256') != sha(output/'vae_decode_input.pt')):
        raise ValueError('Checkpoint metadata or checksum mismatch; refusing resume')
    return report

def run_child(command, log):
    flags = subprocess.CREATE_NO_WINDOW | 4 if os.name == 'nt' else 0
    with log.open('w', encoding='utf-8') as stream:
        child = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT, creationflags=flags)
        guard = ProcessGuard(child)
        try:
            rc = child.wait()
            if rc:
                raise RuntimeError(f'Child exit {rc}; see {log}')
        finally:
            guard.close()

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--controls', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--resolution', type=int, choices=[512, 768, 1024], default=1024)
    p.add_argument('--resume', action='store_true')
    p.add_argument('--ff-chunk', action='store_true', help='Opt-in batch-wise FF memory reduction; sampling parameters unchanged')
    p.add_argument('--references', nargs='+', type=Path, help='Explicit ordered references; lab-only, not Studio default')
    a = p.parse_args()
    a.input, a.controls, a.output = a.input.resolve(), a.controls.resolve(), a.output.resolve()
    files = [a.input, HERE/'run_paint21_checkpoint.py', HERE/'decode_paint_checkpoint.py', Path(__file__)]
    if a.references:
        a.references = [f.resolve() for f in a.references]
        if len(set(a.references)) != len(a.references) or a.references[0] != a.input:
            raise ValueError('References must be unique and start with --input')
        files += a.references
    files += [a.controls/f'render_{kind}_multiview_{i}.png' for kind in ('normal','position') for i in range(6)]
    spec = {'files': {str(f): sha(f) for f in files}, 'views': 6,
            'resolution': a.resolution, 'seed': 0, 'steps': 15, 'guidance': 3.0,
            'scope': 'Paint only; supplied fixed mesh/control views; model weights not fingerprinted'}
    if a.ff_chunk:
        spec['ff_chunk'] = {'size': 1, 'dim': 0}
    if a.references:
        spec['ordered_references'] = [str(f) for f in a.references]
    if a.resume:
        if json.loads((a.output/'sequential_inputs.json').read_text()) != spec:
            raise ValueError('Input/code fingerprint changed; use a new output directory')
    else:
        a.output.mkdir(parents=True, exist_ok=False)
        write_json(a.output/'sequential_inputs.json', spec)
    state = {'status': 'running', 'stage': 'sampling', 'resumed': a.resume}
    try:
        write_json(a.output/'sequential_report.json', state)
        if not a.resume:
            run_child([sys.executable, str(HERE/'run_paint21_checkpoint.py'), '--input', str(a.input),
                       '--controls', str(a.controls), '--output', str(a.output), '--views', '6',
                       '--resolution', str(a.resolution), '--checkpoint-only'] + (['--ff-chunk'] if a.ff_chunk else []) + (['--references', *map(str, a.references)] if a.references else []), a.output/'sampling.log')
        checkpoint = valid_checkpoint(a.output, a.resolution)
        state.update(stage='decode', checkpoint_sha256=checkpoint['checkpoint_sha256'])
        write_json(a.output/'sequential_report.json', state)
        run_child([sys.executable, str(HERE/'decode_paint_checkpoint.py'), str(a.output)], a.output/'decode.log')
        from PIL import Image
        outputs = {}
        for kind in ('albedo','mr'):
            for i in range(6):
                path = a.output/f'{kind}_{i}.png'
                with Image.open(path) as image:
                    image.load()
                    if image.size != (a.resolution, a.resolution):
                        raise ValueError(f'Unexpected decoded size for {path}')
                outputs[path.name] = sha(path)
        state.update(status='passed', stage='complete', outputs=outputs)
        write_json(a.output/'sequential_report.json', state)
    except BaseException as exc:
        state.update(status='failed', error=str(exc))
        write_json(a.output/'sequential_report.json', state)
        raise
    print(json.dumps(state), flush=True)

if __name__ == '__main__':
    main()
