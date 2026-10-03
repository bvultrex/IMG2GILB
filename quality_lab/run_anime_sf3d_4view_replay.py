import json, time, uuid
from pathlib import Path
from PIL import Image
import sys

ROOT = Path(r"C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\desktop")
sys.path.insert(0, str(ROOT))
from pipeline import Job, write_json, sha

cfg = json.loads((ROOT / "runtime.json").read_text(encoding="utf-8-sig"))
jobs = Path(cfg["jobs_dir"])
src = Path(r"D:\SF3D_QualityLab\app_jobs\b66c77f5fb844cefae8ec485d8bab8af\inputs")
# Already named front/back/left/right
view_map = {n: src / f"{n}.png" for n in ["front", "back", "left", "right"]}
for n, p in view_map.items():
    assert p.is_file(), p

jid = uuid.uuid4().hex
job = jobs / jid
(job / "inputs").mkdir(parents=True)
for name, p in view_map.items():
    im = Image.open(p)
    im.load()
    im.convert("RGBA").save(job / "inputs" / f"{name}.png")

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
    "note": "anime replay of b66c77f5 inputs; identical settings to ranger 4abf740c; Grok",
    "source_job": "b66c77f5fb844cefae8ec485d8bab8af",
}
write_json(job / "project.json", spec)
write_json(
    job / "state.json",
    {
        "id": jid,
        "label": "Anime SF3D 4-view replay (b66c77f5 inputs)",
        "status": "queued",
        "created": time.time(),
        "settings": s,
        "views": list(view_map.keys()),
        "stage": None,
        "completed_stages": 0,
        "stages": [],
        "source_job": "b66c77f5fb844cefae8ec485d8bab8af",
        "fixture": str(src),
    },
)
mirror = Path(r"D:\SF3D_QualityLab\anime_validation\sf3d_4view_replay_2026-09-28")
mirror.mkdir(parents=True, exist_ok=True)
(mirror / "JOB_ID.txt").write_text(jid + "\n" + str(job) + "\n", encoding="utf-8")
(mirror / "source.json").write_text(
    json.dumps(
        {
            "source_job": "b66c77f5fb844cefae8ec485d8bab8af",
            "source_inputs": str(src),
            "matched_ranger_job": "4abf740c34c9487ba818455efe460833",
            "new_job": jid,
        },
        indent=2,
    ),
    encoding="utf-8",
)
print(json.dumps({"job_id": jid, "job_path": str(job), "mirror": str(mirror)}), flush=True)
active = Job(job, cfg)
active.run()
print(json.dumps(active.snapshot(), indent=2), flush=True)