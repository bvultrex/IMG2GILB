# QUALITY_JUMP_AUTO_HYBRID_A3_GATE_RESULT

Created: 2026-10-02 ~21:12 (Europe/Warsaw)

## Scope
Two consecutive Studio-path jobs with **job-local** hybrid_a3=true producing the contract artifacts:
hybrid_a3/report.json + 	extured_hybrid_a3_color.glb (+ PBR with MR retain).

Studio **defaults unchanged**. production_accepted=false.

## Jobs
1. Ranger 4abf740c34c9487ba818455efe460833
2. Mechanical bust 9c9d771bfdf844bc8e15b60509ef308d (also satisfies object fixture texture path)

## SHAs (color hybrid)
| Job | textured_hybrid_a3_color.glb |
|-----|------------------------------|
| Ranger | 1caea40225096805ef67dc62bfe7792bcf143b3da0fd58d28b775eca41593f5d |
| Bust | 0113bc227063d9a021423f48c074be842e966d007289dc6cde2e2b86bf3ef31 |

Paint baselines unchanged (Ranger paint still 6a809f5e…).

## Pipeline note
desktop/pipeline.py hybrid_a3 stage now appends --source-pbr <job>/textured_pbr.glb when present (MR invariant). hybrid_a3 remains opt-in default false.

## Vis
- C:\\Users\\Shadow\\Documents\\ComfyUI\\_vis_export\\quality_jump_ranger_hybrid_a3_studio\\
- C:\\Users\\Shadow\\Documents\\ComfyUI\\_vis_export\\quality_jump_bust_hybrid\\

## Still open
- Zenko visual: face_iso + Ranger (+ bust)
- External GLB import/preview
- Studio default flip (forbidden until gate complete)
