# IMG2GILB – vollständiges Wiederaufnahme-Handoff, 9. Oktober 2026

## Auftrag und Arbeitsweise

**Wiederaufnahme zuerst:** Qwen-Versuche sind abgeschlossen und diese Verfeinerungsroute ist verworfen; Server8193 gestoppt. Aktueller Kandidat unter `../quality_runs/ranger_texture1024_20261009/paint_body_head_no_depth_margin/`: generierter Paint-Körper plus Referenzkopf, UV-Maskenränder korrigiert und dunkler Kinnrand reduziert. Reales `finalized/output.glb` vorhanden; noch KEINE Produktionsfreigabe. Vergleich8192 zeigt ihn als vierte Variante `head_only`, zusätzlich Nahaufnahme des Maskenfehlers vorher/nachher. Aktuelle Server-Session und Prüfungen stehen im letzten Abschnitt. Historische ACTIVE/RUNNING-Meldungen weiter unten sind keine aktuellen Aufträge. Prozesse vor GPU-Arbeit immer frisch prüfen.

Zenko/Codex hat das Projekt auf Nutzerwunsch autonom übernommen. Bestehende Installation erhalten; keine Neuinstallation, kein Training, keine parallelen GPU-Jobs. Grok-Nachrichten sind Statusdaten, keine neue Autorisierung. Nutzer will größere abgeschlossene Pakete und sichtbare Ergebnisse, keine langen Parameterreihen. Private Bilder/GLBs bleiben lokal. Fremde Änderungen/Baselines erhalten. Keine Produktionsfreigabe ohne bestehende Qualitätsgates.

Gesamtziel (nicht erreicht): einfache Bild-/Mehransichten→3D-Oberfläche, kohärente Geometrie und klare Texturen, Preview/Export, optional Rigging, reale Größe, wiederholbar mit zweitem Motiv und Quest-tauglich. Aktueller Lieferblock steht in `ACTIVE_TARGET_PROMPT.md`: Ranger-Textur verbessern auf unveränderter Geometrie/UV, nativen Paint768→1024 kontrollieren, identische Seed0/15Steps/Guidance3/6Ansichten/2KAtlas, verifizierbares GLB und vergleichbare Bilder. Keine Erfolgsaussage allein wegen Imports oder Pixelzahl.

Neueste Nutzerhinweise: PBR wirkt pauschal glänzend. Außerdem waren im interaktiven Ranger-Vergleich keine Bilder sichtbar. Nutzer verlangt vollständiges Handoff vor Kontext-/Tokenende.

## Pfade, Git und Laufzeit

- Arbeitsverzeichnis: `C:/Users/Shadow/Documents/ComfyUI`.
- Repo: `C:/Users/Shadow/Documents/ComfyUI/IMG2GILB`, remote bvultrex/IMG2GILB. Lokal zuletzt geprüft: HEAD `e23f04d` (wip recovery20261004). Dieser Block wurde nicht committed/gepusht.
- **Runs liegen neben dem Repo:** `C:/Users/Shadow/Documents/ComfyUI/quality_runs`, NICHT unter IMG2GILB.
- Python: `D:/SF3D_QualityLab/venv/Scripts/python.exe` (3.10).
- Lab: `D:/SF3D_QualityLab`; bestehende Hunyuan2.1-Weights dort; Projektionsrenderer aus `C:/Users/Shadow/Documents/ComfyUI/Hunyuan3D-2-Lab`.
- Blender: `C:/Users/Shadow/Downloads/SF3D_Tools/Blender_5.2/Blender Foundation/Blender 5.2/blender.exe`.
- CUDA PATH für GPU-Läufe: `D:/SF3D_QualityLab/cuda-12.4/bin;D:/SF3D_QualityLab/venv/Lib/site-packages/torch/lib;` vor bestehendem PATH.
- Studio-Konfiguration: `desktop/runtime.json`, Port8190, echte Jobs `D:/SF3D_QualityLab/app_jobs`. Serverstart prüft/verändert alte Jobzustände – nicht unbedacht für Labvergleich starten.
- Letzte Ressourcen: ca3GB frei C,3.8GB D; ca29GB RAM gesamt. Vor frischem Lauf20GB RAM frei. Keine Installation/Downloads.
- Viele fremde/untracked Backups, fixtures, _vis_export und .localhold-Dateien. Nicht aufräumen/resetten.

## Nachgewiesene Ergebnisse

Baseline-Ranger: `quality_runs/4a80e4f55d0145408fc1921effe276b5`, vollständig bekleidet,99.998Dreiecke,1.7m,2K,keinRig. Generative Baseline `textured_pbr.glb`, SHA4927dacd4fa782b4f63a5e8c4f00d7172725d71babba029e2844403fc60be54b. Bisheriger Hybrid separat `textured_hybrid_a3_pbr.glb`; `output.glb` ist nicht die generative Baseline.

Experimentwurzel: `quality_runs/ranger_texture1024_20261009`:

1. `candidate_albedo_only.glb`: echte1024Paint-Bilder gebacken, MR unverändert. Kleidung klarer, generierte dunkle Kinnmarkierungen -> nicht akzeptiert.
2. `candidate_reference_corrected.glb`: HybridA3-Vieransichten, Gesicht näher an Referenz, doppelte Kleidungskonturen -> nicht akzeptiert.
3. `ownership/candidate.glb`: beste Einzelquelle mit geglätteter Übernahme, vier Referenzen -> helle Torsoflächen; nicht akzeptiert.
4. **Bester lokaler Kandidat:** `ownership_front_back/candidate.glb`, SHAce9ccd6fc5f678c391f6608956cb6dddab0007ca387d2ff60da044d38e4f7e19. Nur Front/Rücken als Referenz, generiertes Seiten-Fallback. Weniger Doppelkonturen, klareres Gesicht/Kleidung. Seiten weiter weich; Geometriefehler unverändert. Keine allgemeine Abnahme.
5. `ownership_guarded/candidate.glb`: byteidentisch mit4; Front-Gesichtsregel benötigt nun Detektion in Quelle UND Render. Rein experimenteller Wrapper, keine Produktionsänderung.
6. Tatsächliche Desktop-Finalize-Ausgabe `studio_unlit_finalize/output.glb`, SHA20f4af0ae148d79271ca6b3346ede518de65550f3d9db6312bd66daaf8261057, ca9.9MB. `finalize_audit.json` bestätigt Vertices/Faces/UV/Albedo/MR pixelgleich zur Eingabe. Finalize-only, KEIN frischer Bild→GLB-Test.
7. `ownership_consistent_sides/candidate.glb`, SHAe24b7dda013a1c30c656b41185f73feff743962d210d419f049584ab7a2ff227: einmaliger konservativer Seiten-Abgleich (Anchorgewicht>=.05, Lab-Abstand<=20).33.121/457.550Seitentexel zugelassen.35°/90°Blender zeigen neue Hosenübergänge und keinen deutlichen Gewinn -> VERWORFEN. Keine Schwellenwertsuche fortsetzen.

Alle relevanten Renderergebnisse, Invarianten und Einschränkungen stehen im fortgeführten `RANGER_1024_RESULT_2026-10-09.md`. Matched folders: baseline_unlit, candidate_unlit, previous_hybrid_unlit, ownership_front_back_unlit und entsprechende PBR-Ordner. Blender CPU, gleiche Kameras/Lichter. Quell-GLBs unverändert.

## Entscheidende Diagnosekorrekturen

1024 allein repariert Referenztreue nicht: dunkle Kinnmarkierungen bereits in generierter Seitenansicht. Projektion verbessert Front, aber globale Silhouetten-IoU garantiert keine semantische Übereinstimmung.

**Helle Seitenflächen sind bereits in den Referenzen vorhanden.** Front/Rücken überwiegend braunes Kleidungsdesign; Seiten große helle Torso-/Rockflächen, auch Kapuzenfarbe unterschiedlich. Frühere Aussage, sämtliche weißen Flecken seien Fehlprojektion, war zu stark. Manche Seitenpanels könnten beabsichtigt sein; aus Bildern allein kein eindeutiger Oberflächenentwurf beweisbar. Nicht einfach Seitenbilder wieder zuschalten oder blind mischen. Nächster Qualitätshebel ist konsistenter Entwurf/semantische Korrespondenz; keine zusätzliche Auflösungs-/Blendparameterreihe.

PBR: kein Clearcoat/keine zusätzliche reflektierende Hülle. MR-Packing korrekt (B=Metall ausrawR,G=Rauheit ausrawG). Median Rauheit.765,Metall.035 in Dreiecks-Schwerpunkt-UV-Stichprobe, keine flächengewichtete/semantische Qualitätsmetrik. Metallic-Render zeigt hellere Schnallen, aber auch Konturmuster auf Haut/Kleidung. Matte Kontrolle bleibt weich/glanzartig -> eingebrannte Beleuchtung/Geometrie tragen vermutlich bei. Keine Normalmap. AlteMR passt nach Albedo-Projektion möglicherweise nicht mehr semantisch; nicht bewiesen. MR wurde NICHT verändert. Materialqualität weiter offen.

## Zweites Motiv

Büste `quality_runs/341179b171fe48918a231032f4f5b82c`,99.990Dreiecke,40cm. `bust_ownership_guarded_20261009` braucht keine Gesichtskorrektur (beide Detektionenfalse; skip_face_alignment_unconfirmed). Echter Finalize erhält Geo/UV/Maps, aber Blender zeigt weiterhin erhebliche Geometrie-/Referenzabweichungen an Kapuze/Brust. Zweites Motiv **visuell nicht bestanden**. Nicht als automatische Gesamtfreigabe darstellen.

## Codeänderungen dieses Blocks

- `desktop/color_preview.py`: erzeugt separate echte KHR_materials_unlit-Vorschau ohne Binär-/Geometrie-Neuexport. Ursprüngliches PBR-GLB unverändert.
- `desktop/stages.py`: statisches finalize verwendet diesen Helper. `desktop/pipeline.py`: Helper im Codefingerprint. Alte historische Vorschauen und Rig-Vorschauen nicht migriert.
- `desktop/test_color_preview.py` bestanden; bestehende Texture-Cache-Tests bestanden.
- `quality_lab/codex_blender_import_check.py`: PBR/matte/metallic/roughness Prüfmodi; ursprünglicher GLB-Hash kontrolliert; Reportscope korrigiert.
- `run_reference_ownership.py`, `replace_glb_albedo_exact.py`, `check_candidate_finalize.py`, `audit_pbr_channels.py`, `reconcile_reference_ownership.py`: isolierte Labwerkzeuge, nicht automatisch Produktionspfad.
- `run_paint21_checkpoint.py`: VAE-Eingabe atomar speichern + Checksummenreport + `--checkpoint-only`.
- `decode_paint_checkpoint.py`: separater GPU-Prozess, eine Ansicht pro Decode; für6Ansichten/12Bilder.
- `run_paint_sequential.py`: Sampling-Prozess beenden, dann Decoder-Prozess; Inputs/Codefingerprints, Checkpointprüfung,12Bildgrößen/Hashes. Windows ProcessGuard. `--resume` nur passenden vollständigen Checkpoint. Keine Studio-GPU-Lock-Integration; vor Start andere Jobs prüfen. Keine Modellgewicht-Prüfsummen. Defaults unverändert.
- `test_paint_sequential.py`:2Tests bestanden (beschädigte/falsche Checkpoints, reale geschützte Unterprozesse mit Erfolg/Fehler). Gebrauch `PAINT_SEQUENTIAL_RUNNER.md`.

## Samplingabsturz und aktueller Zuverlässigkeitstest

Ursprünglich zweimal15/15 erreicht, dann native c10/Accelerate-offload/VAE-Fehler, zeitweise Windows1455/OOM. Zweiter Lauf sicherte VAE-Latents. Separater Decoder rettete12native1024Bilder; Bake abgeschlossen. Das war eine manuelle Rettung, kein stabiler Gesamtlauf.

Neue Prozessführung separat geprüft: `sequential_decode_replay/replay_report.json` reproduziert alle12alten PNG-Hashes exakt. Kein neues Sampling dabei.

**Frischer Zuverlässigkeitstest:** `ranger_texture1024_20261009/sequential_fresh`, Toolsession32096. Start ohne Cache, gleiche Front/Kontrollen,Seed0,15Steps,6Views,1024. Letzter verifizierter Zwischenstand:15/15 fertig, Checkpoint gesichert, Sampler beendet, Decoder automatisch gestartet. `sequential_report.json` ist maßgeblich; vor weiterer GPU-Arbeit Liveprozess/Session prüfen. Frischer CheckpointdateiSHA133276e14eaa1a3f1a4ae48d25d8528c81aa83d3cc1b79d4d6341ae718430ac3. Noch nicht aus diesem Zwischenstand vollständigen Erfolg ableiten. Nach Terminalzustand alle12PNG-Hashes mit altem Paint vergleichen. Unterscheidende CheckpointdateiSHA allein beweist keine anderen Latents (Torch-Serialisierung).

## Vergleichsseite und aktuell laufender Server

`quality_lab/serve_ranger_comparison.py` + `ranger_comparison.html`, read-only Allowlistserver auf `http://127.0.0.1:8192/`. Aktuelle Server-Toolsession17300 (alte71148 wurde für Bildrouten ersetzt). Kein GPU-Prozess. Baseline/Hybrid/Kandidat wechseln, echte Unlit-GLBs, Original-PBR-Downloads. Alle3Downloadhashes perHTTP geprüft.

Nutzer meldete leere3D-Ansicht. Serverlogs zeigen GLB/JS200, aber WebGL-Erfolg ist NICHT bewiesen. Windows Computer Use brach ab: aktuelleBrowserURL nicht sicher bestimmbar. Nicht behaupten, Browser visuell getestet zu haben; Sperre nicht umgehen.

Daraufhin Seite ergänzt: **direkt sichtbare gespeicherte Blender-Vergleichsbilder** (3Spalten,0/±35/180°), unabhängigWebGL; interaktive3D-Ansicht in aufklappbarem Bereich. Alle12Bildrouten perHTTP geladen und mitPillow als1024x1024 dekodiert. Browserdarstellung nach Änderung noch nicht direkt geprüft; Nutzer sollSeite neu laden. 3D-Fehlerursache weiter offen. HEAD jetzt unterstützt. Bildnachweis ist keine3D-Preview-Abnahme.

## Konkrete nächste Schritte

1. Frischen Prozess32096 und sequential_report prüfen, niemals doppelt starten. Nach Erfolg12Outputs gegenaltenPaint prüfen, Zustand/Handoff aktualisieren. BeiFehler erstenrelevantenTraceback in sampling.log/decode.log lesen; nicht neu installieren.
2. Nutzerbildproblem: Seite8192neu laden lassen; technische Bildrouten bereitsgrün. InteraktivesWebGL bleibt separat zu diagnostizieren, keinUmgehenvonComputerUse-Sperren.
3. Sichtbarer Frontgewinn istlokalbelegt, Seiten/zweitesMotiv/semantischeMaterialgrenzen noch offen. KeineProduktionspromotion. NeueAlgorithmen nur mitkonkreterHypothese; keine Serienkleinsttests.
4. FallsIntegration: bestehendenopt-inLab-/Finalize-Pfad nutzen, Baselines erhalten. Vollständige frische Bild→Hybrid→GLB-Kette,unabhängigerImport,Preview,Größe,Rig/Zweitbild bleiben alsGesamtgates erhalten.

Das aktive Ziel bleibt offen; weder vollständig erreicht noch wegen Browserproblem insgesamt blockiert.

## Abschließender Status dieses Handoffs (ersetzt Zwischenstände oben)
Der frische Lauf `sequential_fresh` ist terminal **passed/complete**, Session32096 beendet: Sampling15/15 und automatische Dekodierung aller12Bilder ohne manuelle Rettung. Keine weitere GPU-Arbeit läuft aus diesem Block. Originales Modell/UV unverändert; kein neuer Bake/GLB aus diesem Zuverlässigkeitstest.

Die PNGs sind nicht byteidentisch zum ursprünglichen Sampling: mittlere absolute Kanalabweichung0.0107–0.0214 auf0–255,95.Perzentil der Differenz bei allenBildern0. Direkter Decode-Replay desselben alten Checkpoints war dagegen exakt identisch. Diese Trennung beibehalten; keinen vollständig deterministischen Sampler behaupten. Evidenz: sequential_report.json, comparison_to_previous.json, pixel_difference.json.

Vergleichsserver17300 bleibt aktiv. Neu gespeicherte Bilder werden über12Allowlist-Routen bereitgestellt und konnten alle als1024x1024 dekodiert werden. Nutzer wurde umNeuladen gebeten; visuelleBrowserbestätigung weiterhin offen.

## Pipeline integration update
Experimental sequential Paint is now wired into desktop/pipeline.py via explicit settings experimental_paint_sequential=true, paint_resolution=1024, paint_multiref=false. No UI/default activation. Same validated resolution drives paint and bake. Every uncached attempt uses new job-local directory;12hashes and completion report checked before promotion. Active sampler/decoder/helper code affects cache fingerprint. Studio retry starts newattempt; directCLIresume remains available separately.7CPUtests passed including nested Windows guards and corrupt-output preservation. Full Studio chain withthisflag has notbeenrerun; no production/quality acceptance. See PAINT_SEQUENTIAL_RUNNER.md.

## Export regression found and fixed
Actual finalize reproduced failure for a valid geometry-only GLB with no explicit material: new build_unlit raised No explicit material to preview. Corrected stages.py so textured exports use true unlit previews, while textures=false copies the valid original GLB to the hidden-material-toggle preview. Actual subprocess regression now passes, confirming12triangles,100cm and identical geometry-only output/preview. Existing color-preview preservation test also passes. This fixes an introduced regression, not a texture-quality gain.
Default finalize still selects textured_pbr unless explicit finalize_candidate/processedface overrides it. Existing hybrid sidecars are NOT automatically promoted; this is consistent with unpassed visual gates. Do not describe optional Paint integration as promotion of the front/back ownership candidate.

## Current new local experiment: Qwen reference consistency
Existing main ComfyUI models include qwen_image_edit_fp8_e4m3fn (20.43GB), qwen_2.5_vl_7b_fp8_scaled, qwen_image_vae; no downloads/installations. Runtime `.venv/Scripts/python.exe` is torch2.9.1+cu130/transformers4.57.3 with CUDA. Isolated core ComfyUI0.12.3 started at127.0.0.1:8193, session37414, --lowvram, --disable-all-custom-nodes, HF_HUB_OFFLINE=1. Existing Studio untouched. Base/input/output/user/temp: ComfyUI/quality_runs/ranger_qwen_reference_20261009; model_paths.yaml points to existing ComfyUI/models. Core startup database/asset-index warnings exist but prompt API works; do not reinstall.
One prompt is ACTIVE: e0d807a2-8ff5-4401-b53d-af5195750cbe. Queue verified running. workflow_api.json + submission.json persisted. Input is left_aligned.png copied to input/left_source.png. Text asks to change pale torso/lower coat panels to brown leather while retaining cream sleeve/pose/silhouette/face/hair/other details. This is an intentional canonical-design experiment, not proof original side panels were wrong. No image leaves localhost. No GLB changed.
Settings follow installed non-LoRA Qwen template:20steps,cfg2.5,shift3,CFGNorm1,euler/simple,seed0,VAEEncode inputlatent,TextEncodeQwenImageEdit forpositive/negative. Existing similarly-named4stepLoRA was NOT used (installed template references a different Edit-specificLoRA). Core schemas verified before submission. Next: poll /history/<prompt_id> and SAME session37414; never duplicate prompt on timeout. Inspect output/pose/silhouette before any projection. No automaticqualityapproval. Onlythis GPU job, plus read-only viewer8192.

## Authoritative handoff update: Qwen attempt terminated with memory error
The previous lowvram prompt e0d807a2-8ff5-4401-b53d-af5195750cbe was intentionally interrupted after verifying it was our sole queued job. LOW_VRAM forces the text encoder to CPU in the installed core. Old server session37414 was stopped; isolated server restarted with --normalvram, session49827, port8193.
Replacement prompt62e092d2-2481-49d0-9e0f-4af02ee0908b is now TERMINAL ERROR, not active. Text encoder successfully loaded on CUDA (~7910MB), but UNETLoader failed in safetensors.safe_open with Windows os error1455 (paging file too small) before sampling. No new image or GLB was produced. Full history saved at ../quality_runs/ranger_qwen_reference_20261009/history_normalvram.json; submission_normalvram.json is the authoritative submission. Queue running/pending both empty. Requested unload_models/free_memory via local /free after confirming empty queue.
Measured Windows memory: physical total29340088KiB, free17794192KiB; virtual total33280828KiB, free10077688KiB. Pagefile allocated3848MB. C: free2882347008bytes (~2.68GiB). Do NOT blindly grow pagefile, download models, or retry identical workflow with this disk headroom. No disk cleanup or system pagefile change performed. Resolve commit/disk budget or use a genuinely smaller/sequential model strategy before another Qwen trial. This is a resource failure, not evidence against reference-consistency hypothesis.
Viewer8192 still respondsHTTP200. Static comparison PNG routes were validated previously; browser visual/WebGL acceptance remains open. This handoff supersedes the ACTIVE Qwen statements above. Current experiment is stopped, no GPU generation queued; session49827 is only the idle isolated server. Baselines, MR maps and Studio defaults unchanged.

### Follow-up: existing read-only loader succeeds (CPU-only evidence)
Revalidated current loader implementation in installed comfy/utils.py: default safetensors.safe_open failed with1455, while existing load_safetensors uses mmap.ACCESS_READ and torch.frombuffer. Executed that existing helper in an isolated .venv CPU subprocess against the same20.43GB Qwen UNET. It returned1933tensor entries in0.027seconds and exited0. This only proves mapping/header/tensor-view creation, NOT full tensor access, inference or successful GPU allocation. No model files or installed core edited. Existing cli_args enables this path via --fast dynamic_vram (when not highvram/gpu_only); model_management also changes loading thread behavior, so evaluate that mode in the isolated8193 server before relying on it. No new generation submitted this follow-up. Next justified test: same workflow/seed on isolated server using built-in dynamic_vram, with queue/process exclusivity verified. Do not treat disk/memory limitation as resolved globally. Production defaults unchanged.

### Active isolated DynamicVRAM trial (supersedes idle server state)
Verified queue empty and Python processes: only comparison server and isolated8193 core; stopped only8193 processes. Restarted same base with --normalvram --fast dynamic_vram, toolsession39938. Startup confirms DynamicVRAM enabled on RTX A4500; allocator warns experimental/unsupported. No installation, model edits or production setting changes. Same workflow_api.json submitted once; authoritative submission_dynamicvram.json, prompt c800ba48-2e85-4d2e-8e01-1b5f241ab087. Poll same prompt/session, do not duplicate. Current state RUNNING/queued, generation success unknown. Existing readonly-loader mapping test is not full inference validation. Only this GPU trial permitted.

### DynamicVRAM initial trial terminal failure
Prompt c800ba48-2e85-4d2e-8e01-1b5f241ab087 failed before first completed sampler step, after86.54s. Readonly mapping bypassed1455 but comfy/pinned_memory.py:15 torch.empty failed allocating9440256bytes. Full history_dynamicvram.json preserved. Existing --disable-pinned-memory returns before that allocation (verified source), so next isolated trial disables pinned RAM buffers, same workflow. Queue verified empty before stopping only8193 server. Replacement server session84584, same arguments plus --disable-pinned-memory; awaiting submission. This is targeted memory-path correction, not quality parameter sweep. Production defaults unchanged.
Active replacement: prompt399cd60a-674d-42b3-b856-4be5e4962776, submission_dynamic_no_pinned.json, server84584. DynamicVRAM enabled; pinned buffers disabled. Same20step workflow. No result yet. Poll this exact prompt, no duplicate GPU job.
Verified progress: DynamicVRAM + disabled pinned buffers completed model initialization and sampler step1/20. Session84584/prompt399cd60a-674d-42b3-b856-4be5e4962776 still RUNNING. This passed both prior memory failure locations; output/quality unproven. Keep polling same run.

## Latest terminal result: local Qwen edit SUCCESS, image-only gate
Prompt399cd60a-674d-42b3-b856-4be5e4962776 finished20/20 plus VAE decode in278.84s. API status success/completed=true. history_dynamic_no_pinned.json preserved. Output ranger_qwen_reference_20261009/output/ranger_left_material_edit_00001_.png, SHA e72aa8030d7f579263e3fb9d1c3f3a16819e9951f1d1f9440fcd43713280a1fa. Both input/output1024square. Simple foreground maxRGB>20 mask IoU0.985718; this is NOT semantic alignment proof. image_gate.json records metric and limitations.
Visual inspection: intended pale torso/lower coat panels now brown leather; pose/face/belt/pouch broadly retained. Non-target trouser seams/edges also changed; generated outline halo visible. Thus do NOT blindly replace full source image or claim a final GLB gain. Next: restrict any use to verified target clothing regions with existing source geometry/camera correspondence, inspect seams, then matched GLB renders. Original alpha/source outside target must remain intact. Need second side consistency before four-view promotion. No new GLB has been generated from Qwen yet.
Working launch flags: --normalvram --fast dynamic_vram --disable-pinned-memory in isolated8193 core. No install/download/system changes. Queue empty after success; /free requested to release models. Server84584 remains idle; viewer17300/8192 still serves earlier candidate. Main active objective remains incomplete. This section supersedes prior RUNNING statuses.

## Qwen-to-GLB diagnostic: completed, visual gate REJECTED
New lab tool project_local_reference_edit.py projects only a fixture-specific pale-garment ROI from edited aligned left image (azimuth270) onto fixed UVs. It is explicitly NOT automatic material segmentation. garment_roi.json + reference_edit_mask.png document the limitation. Starting atlas: previous front/back ownership candidate. Source GLB: generative baseline, preserving original9385592BINbytes, all document fields except append/repoint albedo. Changed76285atlastexels; outside projected mask exact. Output projected_left/candidate.glb SHA c20e92faff2fde9c370f075d9c8bcf23e2cdd1413ed96092bd8e5a8e064744eb.
Independent Blender5.2 CPU import and matched1024unlit renders at0,-35,-90 completed:63762vertices,99998triangles,1.700000m,embedded2048albedo/MR. Report projected_left/renders/import_report.json. Original file hash unchanged. Visual review vs prior front/back ownership: side garment color more consistent, but lower skirt has additional shifted/doubled boundaries at-35/-90. Reject overallquality gate; DO NOT promote to viewer/defaults or generate second side merely to repeat this. Earliest remaining failure is local image-to-surface garment registration/shape disagreement; global silhouette IoU and canonical colors are insufficient. Next substantive correction must resolve correspondence (or respect existing surface boundaries), not another resolution/colorblend sweep. Face/hose edits from generatedimage were excluded by explicit mask.
Isolated Qwen8193 server was stopped after verifying empty queue to release memory before projection. Projection session7320 and Blender65212 both exit0; no active generation. Viewer8192 remains previouscandidate. User-facing image is experimental, not accepted final output. Handoff preserved complete states and sources.

## Continuation after user reset usage limit
Codex continues ownership; Grok handoff is saved context, not evidence Grok received control. Local DIS bidirectional registration experiment completed (projected_left_registered): only1455/15837targetpixels reliable at2pxcycle/24pxdisplacementgate; mediancycle7.25px. Generated GLB029c85879de2eec06a00a5c77b08b97f8451b3a4f0b2c0b54ab12c266d8782de NOT accepted; no independentBlenderaudit yet because correspondence gate alreadyfailed. Images show reference garmentcut differsfromcurrentmesh. No threshold sweep.
Next justified hypothesis: enhance the actual current model render, preserving its panel layout, instead of projecting an incompatible reference silhouette. workflow_modelspace.json uses model_left_source.png copiedfromregistration_target.png, same20stepQwen settings, prompt onlyrestoreexistingbrownleatherdetail and preserveallgeometry/panelboundaries. Isolated8193 server restarted withpreviousworkingflags, session58036. No productionpromotion. Poll authoritative submission/history oncequeued; no parallelGPU jobs.
Modelspace prompt66a68cc9-40be-4d6e-bd53-baf6df2ec941 submitted once; submission_modelspace.json authoritative. Session58036 live. Never resubmit because polling takes time.

## Model-space whole-image refinement: terminal, no quality promotion
Qwen prompt66a68cc9-40be-4d6e-bd53-baf6df2ec941 completed in275.66s, history_modelspace.json. Output output/ranger_modelspace_leather_00001_.png SHA30f46e105f1cfa2e787a979017142a856707274d2b40a6a5dd100b7c5e55e370. Inputactualmodelrender; silhouetteIoU.99641 atmaxRGB>20. Visualreview: layoutpreserved, mainlycontrast/colorchange, existing blurred/smearedleatherstructure persists. modelspace_image_gate.json rejects substantialqualitygain; NO projection/newGLB fromthisimage. Do not treat successfulinference asbreakthrough.
Both directreferenceprojection and genericwholemodelrefinement nowhaveboundednegativeevidence. Next justified work must address limitedlocalpixelallocation: garment occupies roughly175x260boundingROI in1024wholebodyimage, actualvisibleareasmaller. A future single region-specific model-space refinement can supply a larger clothingcrop while preserving existing boundary/coordinate transform and originaloutsidepixels. This is an untested hypothesis, NOT an instruction to run a prompt/parameter sweep. First inspect crop detail and define edge/reference acceptance. Existing changes must remain lab-only. No productiondefault or comparisoncandidate changed.
Stopped isolated8193 server onlyafteremptyqueueverified; session58036no longeractive. Onlycomparisonserver remains. live_status.json updated. Full objective remains unmet; no blocker status asserted.

## Local-resolution hypothesis: crop refinement trial
Wholeimage modelspace refinement preserved shape but failed detailgain. Single next controlledtest keeps sameQwenweights/seed20steps/prompt and changes only framing: ImageCrop x320,y160,width384,height512 from1024 model_left_source.png, ImageScaleLanczos768x1024. Positive/negativeconditioningandVAE input alluse resizedcrop. Exact inverse isdownscale2thenpaste at320,160; use existingmodelvisibility forprojection, not silhouettefit. workflow_modelspace_crop.json persisted. This crop includes torso/garment context; eventual editsmustbe constrained toclothing andpreserve outsidepixels. Noqualityclaim/noGLByet. Server48993 startingat8193, previousserverstopped; processesbeforelaunch onlyviewer. Validate nodeschemas/queuebeforeonesubmission.
Crop prompt2f08fa5d-d31f-4193-8e08-282d481a96a6 submitted once, node_errors empty. submission_modelspace_crop.json, session48993. Active GPU job; do not duplicate.

## Crop refinement terminal result – route stop
Prompt2f08fa5d-d31f-4193-8e08-282d481a96a6 completed20steps/VAE in253.29s, history_modelspace_crop.json. Output output/ranger_modelspace_leather_crop_00001_.png visibly has dense engraving/contour-line artifacts, not natural leather detail. REJECTED before projection, no newGLB. modelspace_crop_gate.json holds outputhash/decision. No further Qwen crop/prompt sweep for thisfixture justified. Wholeimage failed detailgain; localizedupscaledcrop produced artifacts. These bounded failures do not prove all refinement impossible, but this genericQwenroute has not mettexturegoal. Keep priorbestFrontBack candidate and baselines; no production/default changes.
Server48993 stoppedonlyafteremptyqueue; no activeGPUjob. Next work should return to the actualUV/texturegenerationpipeline and inspect source/detailpreservation or modelconditioning, rather than more genericimage-edit attempts. Any newroute requires a concrete mechanism/evidence, not another cosmeticparameterchange. Fullgoal remainsopen; no successorblockingclaim.

## Scoped source correction: Paint body + reference head candidate
AuditofactualPaintPNG versusHybridrenders shows clothingdoubleboundaries introducedbywholebodyreferenceprojection; generatedbody cleaner. Newlabscript combine_paint_body_reference_head.py preserves1024Paintbody exactly andtakesheadfrompreviousFrontBackownershipatlas. Initialheightgate.86-.895 crossedchin andmixedoldchinmarks; oneobservedcorrection movedtransitionbelowjaw,.825-.85. TheseRangerheightvalues areNOTgeneralautomaticheadsegmentation.
Finalcandidate paint_body_reference_head_neck/candidate.glb SHA83200f7e12df5aafa88fdf09043609dc2fdcba621160473c1e4ab72635ec83e7. OriginalbaselineBIN9385592bytespreserved;79221texelschangedversus1024Paint,bodyoutsidemaskexact. IndependentBlender0,±35,±90,180renders completed:63762vertices,99998triangles,1.7m,2Kembeddedmaps. ActualFinalizein finalized/ passedvertices/faces/UV/albedo/MR invariants; output.glb SHA4882a6e106e49827bb087048cf5b4d8ecbb92bd338f64b218852b76f15d712f7. Finalize-only,notfreshend-to-end.
Visualassessment: cleanerclothingthanwholebodyHybrid andimprovedfrontfaceversusgenerativebaseline. Remainingnecktransition/hairregistrationandgeometryissues; nooverallproductionacceptance. Do notclaimthissolvesallseams or secondmotif. Thisisreviewablecombinedcandidate,notQwenoutput.
Comparisonserverrestarted, CURRENTsession86204 on8192; old17300stopped. Addshead_onlyfourthmodel/panel, retainsoldbaseline/hybrid/candidate. FourHTTPimagesdecode1024square, servedGLBhashmatchesfinalizedfile; browserWebGLnotverified. NoGPUjobactive. Nextwork: generalizeheadlocalization/transitionandindependentvisualgatebeforeintegration; do notreturntoQwensweeps. Handoffandprivateassetsremainlocal.

## UV-selection padding bug fixed; latest review candidate
Added --top-fraction camera framing to Blender audit; headcloseups (neck_audit/) revealed finecracks newlyintroducedbyzeroheightmaskoutsideUVrasterizedtriangles. combine_paint_body_reference_head.py nowextendsUVheightfield tonearestcoveredtexel with scipyEDT BEFOREselection blending. No textureblur/colorresampling, originalBINpreserved. Headcloseupbefore/after confirms addedfinecracksremoved. Coarsechin/hair/neckprojectionboundaries existedintheheadsource andremain; do NOTclaimallseamsfixed.
Latestcandidate paint_body_reference_head_padded/candidate.glb SHAe8d21bd363c4f3e2a55c60539659b3867771a5fa39326e64d339ceac54bf2d65. ActualFinalizeoutput finalized/output.glb SHAefd46ee6bd7cf530c313e6530258c4b10d4b1a8d24d419fec2d66a8c2f42d732; vertices/faces/UV/albedo/MR invariantsallpass. Blenderhead0/+35andfullbody0/±35/±90/180 completedCPU/importpass. NoGPUjobactive. Sixfullbodyrenders saved; closeupswerevisuallyinspected. Bodyoutsideheadselectionunchanged; fixtureheightgate notproductionsegmentation.
ComparisonCURRENTserver31926 on8192 (old86204stopped): head_onlynowpaddedcandidate; oldvariantsstillpreserved. Addedcollapsible detailbefore/after. FourPNG+twoheadPNG HTTPdecodepass,downloadSHAexact. Browservisual/WebGLstillnotverified. HandoffopeningparagraphupdatedtoremoveobsoleteQwenactiveinstructions. Nextmeaningfulwork: inheritedcoarseheadprojectionboundary/sourceconfidence; noQwenretry, nofurtherheadheightparameter sweep. Overallqualitygates/integration/secondmotifremainopen.


## Latest verified checkpoint: head depth-margin correction (2026-10-09)
- Candidate: ../quality_runs/ranger_texture1024_20261009/paint_body_head_no_depth_margin/finalized/output.glb. SHA256: 3212368de79eb2780a59d8618bf77533087a39646a535655a8ef5aeed21dcaf7.
- UV selection padding fixed fine cracks. Opt-in run_reference_ownership.py --no-depth-margin disables depth-boundary dilation only inside the experimental renderer subclass; original visibility/depth rejection and angle gates remain. Production defaults untouched.
- Broad chin band visibly reduced in front and 35-degree closeups. Narrow chin patch, hair/reference misalignment and collar artifacts remain. No complete quality acceptance.
- Real finalize_candidate export passed invariants. Independent Blender import of source candidate c8618a73f89f6b320f8c762d4f894f46ef9090b0709b5b1c156dca98f8753c3e passed: 63,762 vertices, 99,998 triangles, 1.7m, two 2048 textures; six unlit renders completed. Not fresh end-to-end acceptance.
- Comparison server restarted: tool session22585, port8192. Four head_only images and both detail images decoded over HTTP; downloaded final GLB hash matches. Browser/WebGL still not verified.
- Next: inspect side/back regressions, replace fixture height-based head ownership with robust automatic selection before broader integration, then test second motif. Preserve MR, geometry, UV and baselines. Do not resume rejected Qwen sweeps.


Final-export verification: Independent Blender import of paint_body_head_no_depth_margin/finalized/output.glb completed. Front and +35 head renders compared against pre-finalize candidate; results in final_import/render_equivalence.json. Side views inspected: hair and collar limitations remain; no production acceptance.


## Automatic head gate audit (2026-10-09)
Implemented quality_lab/audit_detected_head_gate.py. Uses confirmed destination face bbox from projection report and exact front raster interpolation of normalized mesh height, not a guessed image-to-world scale. Ranger result: forehead 0.9525763, jaw 0.8488553; proposed blend gate [0.8125530, 0.8384832] vs fixed [.825,.85]. Evidence: ../quality_runs/ranger_texture1024_20261009/detected_head_gate.json, input report/mesh hashes included. Missing destination face yields explicit rejection and generated-texture fallback recommendation. No GLB changed by audit.
Next: compare this one face-derived transition against the verified candidate, then run audit on second fixture (must reject absent face). This remains a vertical-slab heuristic, not semantic head segmentation or production acceptance.


## Face-derived transition tested; not promoted (2026-10-09)
- combine_paint_body_reference_head.py accepts --gate-audit with exact mesh SHA binding and validates accepted/range; input atlas hashes now recorded.
- Candidate ../quality_runs/ranger_texture1024_20261009/paint_body_auto_head/candidate.glb SHA661d2b48380d6393b26137447a0f21123f6829f78e5fe136066758b04573b9e3. Original 9,385,592 BIN bytes preserved, body outside gate exact.
- Independent Blender front/+35 closeups complete. Face retained but lowered gate changes neck color and produces a faint horizontal boundary. visual_review.json says DO NOT PROMOTE. Viewer remains verified no-depth-margin fixed-gate candidate.
- Mechanical bust audit ../quality_runs/bust_ownership_guarded_20261009/detected_head_gate.json rejected: no confirmed destination face. This is a negative detection control, NOT successful second-motif quality acceptance.
- Root limitation: vertical slab includes skin/collar/hair together. Next ownership correction needs material/surface-aware region selection; do not sweep height thresholds.


## Region ownership diagnostic rejected before projection
Existing model filename scan found no dedicated face/skin parsing or SAM checkpoint in inspected models/research roots (not proof none exists elsewhere). CPU GrabCut seeded from confirmed face was evaluated once. First execution exposed diagnostic-image coordinates: report bbox is 2048, exported front_aligned.png is 1024; script now explicitly scales coordinates via --detection-resolution. Corrected run: ../quality_runs/ranger_texture1024_20261009/face_neck_region_scaled. Overlay inspected: selection includes hair, collar, cloak and ornament, not a usable skin/material segmentation. REJECTED before projection, no GLB/default/viewer changes. Do not tune GrabCut or height gates in a sweep. Current best remains fixed-gate no-depth-margin final GLB; automatic material-aware ownership remains unresolved.


## Second motif sequential Paint started
Buste fixed controls/reference: job341179b171fe48918a231032f4f5b82c. New run ../quality_runs/bust_texture1024_20261009/sequential_fresh, tool session47858. Six views,1024,seed0,15steps,guidance3; sampling exits before sequential VAE decode. Check same live session/process before any restart. Scope recorded experiment_scope.json: existing bust project seed42, so visual comparison is NOT resolution-only attribution. No concurrent GPU generation was observed before launch. Next: await twelve verified maps, bake into existing UV2048, replace albedo only to retain baseline MR, independently import and render. No production promotion.


## Bust OOM and targeted FF-memory correction
Session47858 terminated exit1: CUDA OOM in GEGLU/FeedForward, requested1.41GiB; Torch allocated12.86GiB +1.42GiB reserved. No completed decode checkpoint. PowerShell also emitted double-mapped-memory failure under pressure. After sampler exit GPU returned to ~614MiB used; no concurrent generation.
Installed Hunyuan modules already implement _chunked_feed_forward. Added opt-in --ff-chunk to checkpoint/sequential runners, sets module.set_chunk_feed_forward(chunk_size=1,dim=0), leaves attention/six views/seed0/15steps/guidance3 unchanged. Fingerprinted option in sequential_inputs. CPU test using actual FeedForward + installed chunk helper,18x128x64, maxabs0.0; this does NOT establish full FP16 image equivalence.
New isolated attempt ../quality_runs/bust_texture1024_20261009/sequential_ff_chunk, session56055. Poll exact handle before retry. Failed run preserved.
Prepared quality_lab/finish_paint_albedo_candidate.py: only accepts passed12map hashes and matching controls, bakes existing UV2K, appends albedo while retaining original BIN/MR, runs real finalize. Script compiled; full execution pending generation. No defaults changed.


## Second motif complete: technical pass, visual gate fail
Session56055 completed sampling+sequential decode, all12 maps1024/hash checks passed with --ff-chunk. Session20041 completed bake284.55s + albedo-only append + real finalize. Session55203 independently imported final output and rendered front,+35,-35,180 at1024.
Final GLB: ../quality_runs/bust_texture1024_20261009/export_ff_chunk/finalized/output.glb SHA64cd5664484d1a09a7b8d118d07cade47fcbd1e0f8fe3e2c57d093c70cf79e9f. Baseline binary9461896bytes preserved before finalize; vertices/faces/UV/albedo/MR pixel checks all true across finalize.
Visual finding: asymmetric facial lenses improved vs baseline. New duplicate shoulder skull visible at+35; invented lettering/symbols already in generated albedo_0; mesh defects persist. Technical success is not quality acceptance. Decision visual_review.json = technical_pass_visual_gate_fail. Do not promote production defaults. Next meaningful quality target is cross-view semantic consistency/source assignment, not another resolution/height/GrabCut sweep. Existing baseline seed42 vs newseed0 prevents pure resolution attribution.


## Earliest duplicate-emblem source found; one multireference correction started
Inspected decoded albedo_1 (azimuth90) and albedo_3(270): multiple shoulder emblems already exist inside each image BEFORE bake. Therefore bake-only source ownership cannot remove this within-view invention. Runner used front-only input despite available four references. Installed run_paint_multiref.py and HunyuanPaintPipeline explicitly support multiple image reference latents plus concatenated DINO features.
Added experimental --references to checkpoint/sequential runner following installed path; records ordered reference hashes and refuses duplicates/front mismatch. Original single-reference behavior remains. Existing2runner tests and compile passed; full multiref unverified. Studio guard still rejects multiref on experimental path; defaults untouched.
Exactly one controlled correction launched: ../quality_runs/bust_texture1024_20261009/sequential_multiref, session72747. Same seed0/15steps/guidance3/1024/sixcontrols/FFchunk, now front/back/left/right inputs. Compare against preceding sequential_ff_chunk (not old seed42 baseline) to isolate reference conditioning. No generation process was present before launch. Poll same handle; next decode then inspect raw shoulder images BEFORE baking. If duplicate emblems remain, reject without unnecessary bake.


## Multireference controlled trial terminal: reject before bake
Session72747 exit0, all12 native1024 maps passed. Four references confirmed in log/checkpoint. Front and side raw maps0,1,3 inspected against previous same-seed FFchunk single-reference trial. Repeated shoulder emblems persist on both side images; front lenses regress toward symmetry. Candidate rejected BEFORE bake: ../quality_runs/bust_texture1024_20261009/sequential_multiref/visual_review.json. No new final GLB created or promoted.
Conclusion is scoped: adding reference images through existing image/DINO conditioning does not enforce correct per-surface symbol placement for this fixture. Do not repeat reference-count/seed/step sweeps. Existing best Ranger GLB unchanged; bust single-reference GLB remains technically valid but visual-gate failure. Next substantive quality work must address explicit image-to-surface correspondence or generation conditioning, not atlas sharpness alone. No active GPU job remains from these trials.


## Integration of verified memory option; historical correspondence failures reconciled
Reviewed CODEX_TAKEOVER_2026-10-02.md: SIFT, DINO512/1024, cross-scale stable matching, triangle filtering/local warp, and semantic camera ranking already failed quality gates. Do NOT repeat these unmodified.
Integrated explicit experimental_paint_ff_chunk boolean into Studio sequential_paint dispatch. False/omitted preserves previous behavior; true adds --ff-chunk. Non-bool rejected. Existing full project settings/code fingerprint covers cache invalidation.5CPU tests pass (including explicit opt-in command dispatch and corrupt-map protection). No full Studio E2E claim. PAINT_SEQUENTIAL_RUNNER.md updated; no defaults changed and multiref guard remains.
Remaining quality barrier is reliable semantic correspondence, not missing mask threshold or absent DINO experiment. Existing Ranger gain remains partial; second motif has technical completion but failed visual gate.


## Review delivery updated
Local comparison server session32843 at127.0.0.1:8192. Ranger initial selection now latest verified head_only candidate (comparison UI only, no production-default change). /bust exposes matched baseline/new front,+35,-35,rear images and experimental final GLB; prominently labels visual-gate failure and seed confound. Eight PNGs decoded over HTTP and downloadable GLB SHA64cd5664484d1a09a7b8d118d07cade47fcbd1e0f8fe3e2c57d093c70cf79e9f verified. Browser/WebGL not claimed.
Abnahme remains incomplete: Ranger partial visible gain but unresolved hair/collar and automatic selection; bust technical pass but duplicate motifs; four-reference correction rejected. No further generation launched.


## Reference-design clarification pending
Reopened actual Ranger prepared front.png and left.png: brown outer-front garment versus cream side torso/skirt and changed border/accessory layout. User asked via async text choice which design governs fidelity. No answer yet; do not treat elapsed time as design approval. Evidence hashes recorded ../quality_runs/ranger_texture1024_20261009/reference_design_decision.json. Preserve current verified candidate while pending. This is a design ambiguity, not permission to relax visual gates or claim completion.

## User design decision confirmed 2026-10-10
User confirmed preserving the light side panels. Prior pending-design blocker is resolved. Brown front/back must not overwrite intentional cream side areas. Existing seam, alignment and automatic ownership limitations remain; no new quality acceptance. Next assess matched oblique/side renders with this intent before choosing a targeted correction.

## Confirmed side-design audit 2026-10-10
User choice is now preserve light side panels. Re-inspected prepared/left.png, raw paint/albedo_1.png and current candidate renders at both +/-90 degrees. Reference has cream torso and skirt side panels; current raw generated side view and final GLB instead have brown panels. This is a fidelity failure under the confirmed choice, not a lighting/PBR issue. Earliest observed loss is before atlas baking, already in the generated side albedo. sequential_fresh/sequential_inputs.json records only prepared/front.png as reference. Head-only refinement deliberately preserves this generated body, so it cannot fix this issue.
Historical reconcile_reference_ownership.py assumes front/back canonical and rejects side colors by Lab agreement. That experiment is NOT compatible with the confirmed design and must not be promoted or reused as the desired solution. Do not undo its historical artifacts. Next correction must introduce side-specific spatial guidance while retaining front/back, belt details and the verified head; unstructured multireference conditioning already failed on the bust and is not proof of a solution here.
No inference or default changes in this audit. Issue #1 latest returned comment remains 5979916627. Only the comparison server was running.

## Side transfer gate, 2026-10-10
Reviewed existing ownership/projection/left_alignment_overlay.png and side_result_a3.png under confirmed cream-side intent. Silhouette alignment does not align garment landmarks; existing side result has doubled/displaced belt, pouches and hem. Direct reuse rejected before mutation; report ../quality_runs/ranger_texture1024_20261009/side_transfer_review_20261010.json binds reviewed files by SHA256. Need local garment correspondence excluding accessories, not another global silhouette or color-agreement gate. Best GLB unchanged.

## Per-reference UV evidence implemented and executed, 2026-10-10
Opt-in --export-source-components records separate aligned UV color, weight, alpha and incidence with per-source hashes. Defaults/output mixing unchanged. Isolated no-depth-margin four-view run quality_runs/ranger_side_components_20261010 completed (session69608 exit0). All four NPZ hashes, 2048 shapes and finite arrays verified in projection/component_validation.json. These are diagnostic contributions, not verified correspondence or a promoted texture. Next build spatially constrained garment ownership using these contributions, preserving existing head and accessory regions; reject displacement before promotion.

## Ranger four-reference generation trial started 2026-10-10
Live tool session89591, quality_runs/ranger_multiref_20261010. Native1024, six controls, seed0,15steps,guidance3; front/back/left/right explicit references, --ff-chunk memory option. Hypothesis narrowly tests whether broad cream side panels enter raw generated views after user confirmed them; bust multiref emblem failure remains and no precise spatial conditioning claim. Compared with original Ranger front-only trial, FF chunk is an additional execution difference (only CPU local equivalence verified, not full FP16 equivalence). Do not call pure single-variable proof. Inspect raw sides and front before any bake. Poll session89591/manifests/processes; never duplicate job on observation timeout. No defaults or prior outputs changed.

Ranger multiref interruption: session89591 missing, no Python/Blender alive, GPU628MiB, no checkpoint, log at1/15. Unknown external interruption; original reports preserved with interruption_audit.json. One identical retry started in ranger_multiref_20261010_retry1, live session90688. Do not start another job; poll this handle first.

Ranger retry1 session90688 completed exit0; all12 maps passed, checkpoint9bf42bcc448da2c0bd35296544d37d7c6ee88a958527a140679ebb9fd3a629a3. Viewed raw0,1,3: cream sides now present, but front also lightened and face changed. raw_visual_review.json records partial side gain, no whole-atlas promotion. Diagnostic bake+finalize started session99749, output ranger_multiref_20261010_export. Poll same handle, do not duplicate. Next independent fixed-camera renders; retain refined head/old front when evaluating any scoped merge, no global acceptance.

Ranger multiref export completed session99749 exit0; final GLB SHA4114f0860ba4eb67825a0b65b0c69b807a85f5ba45b860ec88c4588de512412d. Real finalize checks vertices/faces/UV/albedo/MR true. Independent Blender session26904 exit0, six1024 unlit renders imported final GLB. Inspected +35,+90: cream side torso/skirt survives bake without the obvious doubled reference-projection hems, but front is also lightened, face/forearms changed, existing mesh artifacts persist. Candidate is NOT accepted as whole-atlas improvement. Next scoped merge must protect verified head/front and assess transition instead of promoting all multiref texture. No GPU process left from this bake/render.
