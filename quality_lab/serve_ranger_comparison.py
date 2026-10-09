"""Local, read-only GLB comparison. No pipeline jobs or production state changes."""
import argparse
import hashlib
import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'desktop'))
from color_preview import build_unlit

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runs', type=Path, default=REPO.parent / 'quality_runs')
    parser.add_argument('--port', type=int, default=8192)
    args = parser.parse_args()
    root = args.runs / 'ranger_texture1024_20261009'
    baseline = args.runs / '4a80e4f55d0145408fc1921effe276b5'
    out = root / 'interactive_comparison'
    out.mkdir(exist_ok=True)
    models = {
        'baseline': baseline / 'textured_pbr.glb',
        'hybrid': baseline / 'textured_hybrid_a3_pbr.glb',
        'candidate': root / 'studio_unlit_finalize/output.glb',
        'head_only': root / 'paint_body_head_no_depth_margin/finalized/output.glb',
    }
    routes = {'/': REPO / 'quality_lab/ranger_comparison.html',
              '/bust': REPO / 'quality_lab/bust_comparison.html',
              '/model-viewer.min.js': REPO / 'desktop/web/model-viewer.min.js',
              '/detail/before': root / 'neck_audit/combined/front_unlit.png',
              '/detail/after': root / 'neck_audit/no_depth_margin/front_unlit.png'}
    bust = args.runs / 'bust_texture1024_20261009'
    routes['/model/bust_candidate'] = bust / 'export_ff_chunk/finalized/output.glb'
    for key, folder in {'baseline':'baseline_renders', 'candidate':'candidate_renders'}.items():
        for angle, filename in {'0':'front_unlit.png', '35':'angle_35_0_unlit.png', '-35':'angle_-35_0_unlit.png', '180':'angle_180_0_unlit.png'}.items():
            routes[f'/bust/render/{key}/{angle}'] = bust / folder / filename
    for key, folder in {'baseline':'baseline_unlit', 'hybrid':'previous_hybrid_unlit',
                        'candidate':'ownership_front_back_unlit',
                        'head_only':'paint_body_head_no_depth_margin/renders'}.items():
        for angle, filename in {'0':'front_unlit.png', '35':'angle_35_0_unlit.png',
                                '-35':'angle_-35_0_unlit.png', '180':'angle_180_0_unlit.png'}.items():
            path = root/folder/filename
            if not path.is_file():
                raise FileNotFoundError(path)
            routes[f'/render/{key}/{angle}'] = path
    manifest = {'scope': 'Controlled fixed-geometry comparison; not production acceptance', 'models': {}}
    for key, source in models.items():
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        preview = out / (key + '_' + digest[:12] + '_unlit.glb')
        if not preview.exists():
            build_unlit(source, preview)
        routes['/model/' + key] = source
        routes['/color/' + key] = preview
        manifest['models'][key] = {'source': str(source), 'sha256': digest,
                                    'bytes': source.stat().st_size, 'color_preview': str(preview)}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    routes['/manifest.json'] = out / 'manifest.json'

    class Handler(BaseHTTPRequestHandler):
        def do_HEAD(self):
            self.do_GET(head=True)

        def do_GET(self, head=False):
            if self.headers.get('Host') not in (f'127.0.0.1:{args.port}', f'localhost:{args.port}'):
                self.send_error(403)
                return
            path = routes.get(self.path.split('?')[0])
            if path is None:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', 'model/gltf-binary' if path.suffix == '.glb' else
                             mimetypes.guess_type(str(path))[0] or 'application/octet-stream')
            self.send_header('Content-Length', str(path.stat().st_size))
            self.send_header('Cache-Control', 'no-cache')
            if self.path.startswith('/model/'):
                self.send_header('Content-Disposition', f'inline; filename="ranger_{self.path.split("?")[0].rsplit("/",1)[-1]}.glb"')
            self.end_headers()
            if head:
                return
            try:
                with path.open('rb') as stream:
                    while chunk := stream.read(1024 * 1024):
                        self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass

    print(f'Comparison ready at http://127.0.0.1:{args.port}/', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()

if __name__ == '__main__':
    main()
