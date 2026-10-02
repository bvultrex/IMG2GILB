"""Export diagnostic texture arms from one frozen rasterization; never production."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
import trimesh

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--components',type=Path,required=True)
    parser.add_argument('--source-pbr',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    data=np.load(args.components,allow_pickle=False)
    base,selected,averaged,confidence=(data[k] for k in ('base','selected','averaged','confidence'))
    strong=data['strongest_weight']>.5
    # Only remove Paint where an individual reference has substantial weight.
    normal=base*(1-confidence)+selected*confidence
    arms={'average':base*(1-confidence)+averaged*confidence,
          'best_source':normal,
          'best_source_no_paint_strong':np.where(strong,selected,normal)}
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    before=sha(args.source_pbr)
    manifest={'source_sha256':before,'components_sha256':sha(args.components),
              'strong_texels':int(strong.sum()),'strong_threshold':.5,
              'production_accepted':False,'scope':'Fixed geometry/camera/rasterization; diagnostic color mixing only','outputs':{}}
    for name,colors in arms.items():
        assert np.isfinite(colors).all()
        scene=trimesh.load(args.source_pbr,process=False)
        assert len(scene.geometry)==1,'Expected exactly one mesh'
        mesh=next(iter(scene.geometry.values()))
        mesh.visual.material.baseColorTexture=Image.fromarray((np.clip(colors,0,1)*255).round().astype(np.uint8))
        path=args.out/(name+'.glb');scene.export(path)
        manifest['outputs'][name]=sha(path)
    assert sha(args.source_pbr)==before
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
