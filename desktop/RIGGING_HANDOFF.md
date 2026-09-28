# Lokales Rigging - Integrationsstand

SkinTokens-Quellcode: D:/SF3D_QualityLab/research/SkinTokens, Commit 273b691d35989d71cd17ff2895fdc735097b92d1.
Modellrevision und Downloadgroessen: rig-model-inventory.json. Noch keine Gewichte heruntergeladen.
Isolierte Laufzeit: C:/Users/Shadow/Documents/ComfyUI/IMG2GILB-rig-runtime/venv (Python 3.11.16). UV 0.12.19 liegt separat unter bootstrap. Keine Aenderung am bestehenden ComfyUI-Python oder Hunyuan-Python.

## Noch erforderlich
1. PyTorch 2.7.0/cu128, torchvision 0.22.0 und torchaudio 2.7.0 installieren (Download begonnen; Ergebnis erneut pruefen).
2. Weitere Abhaengigkeiten versionsgebunden aufloesen. Windows-kompatibles bpy bestimmen. Kein globales pip verwenden.
3. Windows-Attention-Pfad pruefen: TokenRig und SkinVAE importieren flash-attn zwingend, waehrend andere Module bereits PyTorch-SDPA als Ersatz besitzen. Ein konsistenter SDPA-Pfad muss numerisch und mit realer Inferenz getestet werden, bevor er als kompatibel gilt.
4. Gepinnte Gewichte laden, inference --use_transfer mit dem gelben Charakter ausfuehren. VRAM und Laufzeit messen.
5. validate_rig.py muss bestehen, dazu Blender-Import, erhaltene Texturen/Groesse und eine sichtbare Deformationsprobe. Der Validator allein beweist keine Rigging-Qualitaet.
6. Erst danach Pipeline-Stufe, Abbruchbehandlung und Rig-Schalter aktivieren.

## Aktueller Validator
validate_rig.py prueft GLB-Skins, Gelenkverweise, Hierarchiezyklen, endliche Werte und normalisierte Gewichte pro Vertex. Sparse/extern gespeicherte Accessors sind nicht unterstuetzt und werden abgelehnt. Animationen werden nur gezaehlt.
Sechs Tests pruefen gueltige Gewichte sowie fehlendes Rig, leere Gewichte, NaN, falsche Gelenknummern und Zyklen.
Meshy_AI_Midnight_Defiance_Running.glb besteht: 105082 exportierte Vertices, 28 Gelenke, zwei Animationen. Das aktuelle eigene GLB ist ungeriggt.

## Update: Laufzeit und Downloads abgeschlossen
Python 3.11.16, Torch 2.7.0+cu128 und Anforderungen installiert. Transformers 4.57.6, Diffusers 0.35.2, bpy 4.3.0, NumPy 1.26.4. Beide Checkpoints und Qwen-Konfiguration revisionsgebunden geladen. src/attention_compat.py ergaenzt; zwei harte FlashAttention-Imports auf Adapter umgestellt und TokenRig verwendet dessen Backend. GPU-FP32-Vergleich mit expliziter Attention bestanden (max 1.38e-6); bfloat16 und volle Inferenz noch offen. demo.py --help wird gerade erstmals importiert; Prozessstatus vor weiteren Schritten pruefen.


## 2026-09-28 - Erster eigener Rigging-Lauf erfolgreich
SkinTokens-Inferenz mit Windows-SDPA erfolgreich. Session 34582 beendet, Exitcode 0; Hilfsserver/Worker danach nicht mehr vorhanden. Kernverarbeitung nach Modellladen ca. 31 Sekunden; Kaltstart deutlich laenger.
Ergebnis: D:/SF3D_QualityLab/male_anime_validation/rig_trial/character_rig.glb. Rig-Validator bestanden: 22 Gelenke, 64803 exportierte Vertices (zusätzliche Export-Splits), Gewichtsfehler maximal 1.79e-7. Keine Animation enthalten.
Blender-Import: 1 gebundenes Mesh, 1 Armature, 99996 Dreiecke, 170.000005 cm. Blender erzeugt zusätzlich ein nicht exportiertes Bone-Anzeigemesh; dieses darf bei Modellgroesse/Triangles nicht mitgezaehlt werden. Beide 2048px-Texturkarten nach RGBA-Dekodierung pixelidentisch zum Eingang; Materialfaktoren unveraendert ueber glTF-Standardwerte.
Deformationsprobe: bone_7 lokal Z um -40 Grad, 8337 Vertices bewegt, max. 0.3485 m, Unterkoerperbewegung 0.0 m. rest.png und arm_pose.png visuell geprueft. Kein abgetrennter Arm oder sichtbares Mitziehen der Beine. Dies ist eine einzelne Pose, kein vollstaendiger Animations-/Anatomietest.
Noch offen: mehrere Gelenke und zweiter Charakter; Pipeline-Anbindung nach Finalisierung, damit trimesh das Rig nicht wieder entfernt; GLB-Vorschau/Animationsprobe; Abbruchtest; UI-Schalter erst danach aktivieren. Rigging nicht als vollstaendig abgeschlossen markieren.


## 2026-09-28 07:xx - Rig-Stufe und echter Dienststart
rig_stage.py implementiert: separater Prozess, eigener output_rigged.glb/result_rigged.json, strukturelle Rig-Pruefung sowie unveraenderte Dreieckszahl, Mesh-Bounds, Bildpixel und PBR-Zuordnung/Faktoren. Ungeriggt bleibt als separater unveraenderter Export erhalten. Pipeline-Stufe nach finalize vorbereitet; Server-Download/Projekt-ZIP waehlen geriggten Export anhand Ergebnisstatus. Laufzeit rig_enabled=false bis End-to-End-Abnahme.
Frueherer Acceptance-Lauf 82856 war nach Sitzungsunterbrechung nicht mehr vorhanden und hatte keinen Abschlussbericht. Kontrolliert neu gestartet als 88207; aktuell Modellladen, keine Fehlermeldung. Vor weiterem Start Status pruefen.
Blender-Knieprobe mit erstem Rig bestanden: bone_15, 45 Grad lokal X, 10498 bewegte Vertices. Bild knee_pose.png geprueft; zusammenhaengende Verformung. Keine universelle Rig-Freigabe.
Studio/ComfyUI waren extern beendet (keine Listener 8190/8188). EXE daraufhin gestartet, /health erfolgreich. Kein Stop-/Kill-Umweg benutzt. Vorbereitete Serverreparaturen sind dadurch nun geladen. API-Konfig rigging=false und Rig-Anforderung liefert kontrolliert HTTP400. Zehn Desktop-/Rig-Tests bestanden. GUI-Startdarstellung sowie voller Upload->Rig->Export noch offen.


## 2026-09-28 - Rig-Acceptance abgeschlossen, voller Workflow gestartet
Rig-Stufentest 88207 beendet, Exitcode0. acceptance.json bestaetigt unveraendertes ungeriggtes Original, output_rigged.glb mit 22 Gelenken. PBR-Zuordnung/Faktoren nochmals mit aktuellem Validator geprueft. Hilfsserver 59876 beendet.
Studio-Projekt 15dba43f8f424bc3a096c9c1a007ba12 als abgeleitetes Ergebnis registriert. Browser zeigt Rig:22 Gelenke, Vorschau visuell geprueft. API-Modell und output.glb im Projekt-ZIP haben SHA256 e6561453d0d6659fb4e7c3b26f74729f1d1caed6b7e9346e7272cd1926497dbd. ZIP-result.json rigged=true. Screenshot rig_stage_acceptance/studio-rigged.png.
Vollstaendiger neuer Pipeline-Test gestartet: D:/SF3D_QualityLab/male_anime_validation/test_full_pipeline_rig.py, Jobordner full_pipeline_rig_test, Session32540. Vier Referenzen,100000Zieltris,170cm,2K,Face+Rig. Aktuell prepare, ComfyUI wurde automatisch gestartet. Laeuft ausserhalb Studio-API als Integrationstest und ist daher nicht ueber deren Abbruchknopf steuerbar. Vor weiteren GPU-Laeufen Session32540 pruefen. UI-Rig-Schalter weiterhin gesperrt, bis voller Pfad einschliesslich Abbruch/Export abgenommen ist.

## 2026-09-28 — Rig walk preview
Added desktop/walk_preview.py: procedural 1.2-second in-place gait (six joint rotation tracks), generated into preview_color.glb as a separate viewer asset. rig_stage creates it automatically for supported humanoid topology; unsupported rigs retain their valid export with preview_animation=false and rig/preview.json reason. Studio offers Laufprobe starten/stoppen. Browser verified moving limbs and toggle. Original rigged GLB remains the downloadable rest-pose asset. This is a deformation diagnostic, not production locomotion (no foot IK). Acceptance rig_stage --verify-existing passed, 22 joints, 99,996 triangles, 2K materials. Full pipeline job full_pipeline_rig_test is still running, currently paint; no completion claim.

# Quality package — 2026-09-28

Walk v2 uses a 1.25-second cycle, 60% stance, a Hermite swing trajectory, sagittal two-bone IK, ankle counter-rotation, slight pelvis bob/chest turn and relaxed arms/elbows. It is an in-place diagnostic walk, not mocap or terrain-aware locomotion. Rest-pose downloads remain unchanged.

Blender imported the actual exported preview and evaluated 81 samples. Ankle height variation during stance was below 0.001 mm; endpoint ankle error was zero. This measures the joints, not shoe-ground collision. Rendered four poses also checked. Report: walk_v2_report.json. Ten existing desktop/rig tests pass.

The complete 4-view -> shape -> UV -> paint -> bake -> face -> finalize -> rig run finished successfully in ~17m27s: 99,996 triangles, 64,803 exported vertices, 170cm, 2K,22 joints. General rigging UI remains gated pending another-character and complete UI acceptance tests.

Texture experiments: stronger view-incidence weighting preserves front/back reference details (notably jacket logo) without changing geometry, UV or PBR maps. Protected face pixels changed: zero. Side profiles fail global silhouette registration: 0.593/0.449 IoU. Registering trunk/legs instead of the protruding hands improves this to 0.702/0.679. Restricted body-region IoU reaches only 0.745/0.741, still below the 0.75 acceptance threshold. Therefore both sides are skipped, not silently forced. Camera angle search 50–130 degrees did not improve the global fit beyond90degrees.

The texture variant is EXPERIMENTAL, not the production default. Residual mismatched outlines, baked lighting and seams remain. Next task: semantic part alignment / consistent projections and geometry evaluation, not blind sharpening. Do not claim Meshy parity.

Studio experiment:8532227aa14949dc97de45503b6ce6da. Its quality-verification.json records the matching original-texture control job. replace_albedo.py replaces only the base-colour texture reference, keeping original mesh/skin/accessor/binary data intact; it refuses overwrite of its input. Procedural preview is separately generated.

The scripts in this folder are reproducible LOCAL FIXTURE experiments with explicit D:/SF3D_QualityLab paths, not portable production pipeline stages. No extra dependency installations.

Cache repair: for rigged jobs, the rig stage owns preview_color.glb and rig/preview.json; finalize no longer fingerprints this shared preview output. This avoids reusing an unanimated finalize preview after retry. Unsupported topology falls back to the rigged rest pose with animation disabled. Pipeline code is loaded on server start; running Studio must restart before this cache correction applies to newly submitted jobs.

