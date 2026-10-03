import json, shutil, time, uuid
from pathlib import Path
from PIL import Image

ROOT = Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\desktop")
import sys
sys.path.insert(0, str(ROOT))
from pipeline import Job, write_json, sha

cfg = json.loads((ROOT / "runtime.json").read_text(encoding="utf-8-sig"))
jobs = Path(cfg["jobs_dir"])
fix = Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\fixtures\ranger_ortho_v1")

# side_a ~ left (right half brighter, matching ref_left asymmetry); side_b ~ right
view_map = {
    "front": fix / "front.png",
    "back": fix / "back.png",
    "left": fix / "side_a.png",
    "right": fix / "side_b.png",
}

jid = uuid.uuid4().hex
job = jobs / jid
(job / "inputs").mkdir(parents=True)
decoded = {}
for name, src in view_map.items():
    im = Image.open(src)
    im.load()
    im = im.convert("RGBA")
    im.save(job / "inputs" / f"{name}.png")
    decoded[name] = True

s = {
    "quality": "standard",
    "triangles": 100000,
    "height_cm": 170.0,
    "texture_size": 2048,
    "textures": True,
    "face": True,
    "rig": False,
    "seed": 42,
}
spec = {
    "schema": 1,
    "views": list(view_map.keys()),
    "settings": s,
    "input_hashes": {name: sha(job / "inputs" / f"{name}.png") for name in view_map},
    "note": "ranger_ortho_v1; side_a->left, side_b->right; Grok Studio 4-view",
}
write_json(job / "project.json", spec)
write_json(
    job / "state.json",
    {
        "id": jid,
        "label": "Ranger ortho_v1 SF3D 4-view",
        "status": "queued",
        "created": time.time(),
        "settings": s,
        "views": list(view_map.keys()),
        "stage": None,
        "completed_stages": 0,
        "stages": [],
        "view_mapping": {"left": "side_a.png", "right": "side_b.png"},
        "fixture": str(fix),
    },
)
# Mirror folder pointer for validation tree
mirror = Path(r"D:\SF3D_QualityLab\ranger_validation\ortho_sf3d_4view")
mirror.mkdir(parents=True, exist_ok=True)
(mirror / "JOB_ID.txt").write_text(jid + "\n" + str(job) + "\n", encoding="utf-8")
(mirror / "view_mapping.json").write_text(
    json.dumps({"left": "side_a.png", "right": "side_b.png", "job": jid}, indent=2),
    encoding="utf-8",
)
print(json.dumps({"job_id": jid, "job_path": str(job), "mirror": str(mirror)}))
# Run orchestrator (blocking)
active = Job(job, cfg)
active.run()
print(json.dumps(active.snapshot(), indent=2))