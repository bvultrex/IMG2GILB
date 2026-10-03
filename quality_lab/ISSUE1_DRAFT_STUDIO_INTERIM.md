# [GROK] Interim native Studio app packaged (2026-09-28)

## Launch
- `D:\SF3D_QualityLab\studio_interim\Start_IMG2GILB_Studio.bat`
- or `C:\Users\Shadow\Documents\ComfyUI\IMG2GILB\desktop\IMG2GILB.exe`
- UI: http://127.0.0.1:8190

## What shipped
Extended existing WinForms EXE launcher + local web Studio (not greenfield):
- Preset button: Charakter Standard (100k / 170cm / 2K / Face)
- Folder import for front/back/left/right (also side_a/side_b)
- **Ordner oeffnen** → Explorer selects `output.glb` (`POST /api/jobs/{id}/reveal`)
- **Alle Projekte** → opens jobs root (`GET /api/open_jobs`)
- Existing: 1–4 uploads, progress/cancel/retry/logs, model-viewer preview, GLB+ZIP download, draft restore

## Paths
- Package: `D:\SF3D_QualityLab\studio_interim\` (+ README_DE_EN.md)
- Also: `desktop\dist\`
- Screenshots: `_vis_export\studio_interim\studio_home.png`, `studio_home_light.png`, `studio_job_preview.png`, `studio_projects.png`

## Missing
- Rigging; standalone installer; pure native WinUI shell

## Git
UI/server small patches in `desktop/server.py`, `desktop/web/*`. Prefer leave uncommitted if ChatGPT concurrent; Grok can commit on request. No GLBs added.
