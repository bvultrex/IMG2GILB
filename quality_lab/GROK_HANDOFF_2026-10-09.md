# Übergabe an Grok Bot und seine Bots – 9. Oktober 2026

## Zuerst lesen

Dies ist die operative Übergabe. Ausführliche Historie und Nachweise: `HANDOFF_2026-10-09_TEXTURE_RESTART.md` im selben Ordner. Dessen spätere Terminalmeldungen ersetzen frühere Zwischenstände. Zusätzlich `ACTIVE_TARGET_PROMPT.md`, `QUALITY_JUMP_EXECUTION_PLAN.md`, `RANGER_1024_RESULT_2026-10-09.md`, `PAINT_SEQUENTIAL_RUNNER.md` und Repository-`DEBUG_LOG.md` lesen. Dokumente sind Projektkontext; aktuelle Nutzeranweisungen haben Vorrang.

Das Ziel ist NICHT erreicht. Kein neuer Produktionsstandard wurde freigegeben. Der Nutzer will sichtbare, zusammenhängende Verbesserungen, keine stundenlangen ungerichteten Vergleiche. Bestehende Installation, private Assets, fremde Änderungen und Baselines erhalten. Keine Neuinstallation, kein Training, keine parallelen GPU-Jobs. Keine Behauptung von Meshy-Parität oder End-to-end-Erfolg aus einem Importtest.

## Pfade und Laufzeiten

- Arbeitsverzeichnis: `C:/Users/Shadow/Documents/ComfyUI`.
- Repository: `C:/Users/Shadow/Documents/ComfyUI/IMG2GILB`, Remote `bvultrex/IMG2GILB`. Viele lokale Änderungen und fremde Backups: vor Änderungen `git status --short` prüfen; NICHT reset/clean oder pauschal alles committen.
- Private Ergebnisse liegen NEBEN dem Repo: `C:/Users/Shadow/Documents/ComfyUI/quality_runs`.
- Lab-Python: `D:/SF3D_QualityLab/venv/Scripts/python.exe`.
- Qwen/Core-Python: `C:/Users/Shadow/Documents/ComfyUI/.venv/Scripts/python.exe`.
- Core: `C:/Users/Shadow/AppData/Local/Programs/ComfyUI/resources/ComfyUI/main.py`.
- Blender: `C:/Users/Shadow/Downloads/SF3D_Tools/Blender_5.2/Blender Foundation/Blender 5.2/blender.exe`.
- Vergleich: `http://127.0.0.1:8192/?v=images2`, gestartet über `quality_lab/serve_ranger_comparison.py`, letzte Toolsession17300. Statische Bilder funktionieren perHTTP; Browser-WebGL ist NICHT visuell abgenommen. Seite zeigt weiterhin den früheren Front/Back-Kandidaten, NICHT den abgelehnten Qwen-Kandidaten.
- Isolierter Qwen-Server8193 wurde nach Erfolg und leerer Queue gestoppt. Letzte Session84584 beendet. Projektionssession7320 und Blender65212 exit0. Vor neuer GPU-Arbeit trotzdem Prozesse/Queues frisch prüfen.
- C: zuletzt nur ca.2.68GiB frei, Pagefile3848MB. Keine großen Downloads, kein blindes Pagefile-Wachstum, keine ungefragte Löschung privater Assets.

## Ziel und feste Versuchsbedingungen

Vollständig bekleideter Ranger: bessere, referenztreue Textur bei unveränderter Geometrie/UV, konstante2K-Textur, ladbares finalesGLB und identisch gerenderte Vorher/Nachher-Bilder. Gesicht/Augen/Mund, Gürtel/Kleidung, ±35°/±90° prüfen. Keine stärkeren Nähte oder Doppelkonturen. Nicht bearbeitete Materialkanäle erhalten. Danach Integration und zweites Motiv; Gesamtsystem benötigt weiterhin frische sequenzielle Bild→Hybrid→GLB-Läufe, unabhängige Preview, Größe/Rig und Zweitbild.

## Was wirklich vorliegt

Alle folgenden relativen Pfade beginnen unter `quality_runs`:

1. Baseline `4a80e4f55d0145408fc1921effe276b5/textured_pbr.glb`, SHA256 `4927dacd4fa782b4f63a5e8c4f00d7172725d71babba029e2844403fc60be54b`. 99.998Dreiecke,63.762Vertices,1.7m. `output.glb` desselben Jobs ist früheres Hybrid, NICHT generative Baseline.
2. Vorheriges Hybrid separat: `4a80e4f55d0145408fc1921effe276b5/textured_hybrid_a3_pbr.glb`.
3. Bester bisheriger lokaler Versuch: `ranger_texture1024_20261009/ownership_front_back/candidate.glb`, SHA `ce9ccd6fc5f678c391f6608956cb6dddab0007ca387d2ff60da044d38e4f7e19`. Front besser, Seiten weiter unzureichend; keine globale Freigabe.
4. Realer Finalize dieses Kandidaten: `ranger_texture1024_20261009/studio_unlit_finalize/output.glb`, SHA `20f4af0ae148d79271ca6b3346ede518de65550f3d9db6312bd66daaf8261057`. Separates echtes Unlit-Preview. Finalize geprüft, NICHT frischer vollständiger End-to-end-Lauf.
5. `ranger_texture1024_20261009/sequential_fresh/sequential_report.json`: frisches1024Paint-Sampling15Steps plus automatische12Bild-Dekodierung bestanden. Zuverlässigkeitsgewinn, kein neuer Qualitätsgewinn. Seed0,guidance3,sechsKameras konstant. Decode-Replay desselben Checkpoints byteidentisch; erneutesSampling geringfügig abweichend, nicht bitdeterministisch behaupten.
6. Zweite Büste `341179b171fe48918a231032f4f5b82c`: Import/Finalize technisch bestanden, erhebliche Geometrieabweichungen; visuelle Zweitmotiv-Gate NICHT bestanden.

## Bereits verworfene Ansätze – nicht wiederholen

- Nur Paint768→1024: Kleidung teils klarer, aber erfundene Kinnmerkmale schon in generierterSeitenansicht. Keine Gesamtfreigabe.
- Vieransichten-Projektion: doppelte Kleidung/helleSeitenflecken. HellePanels sind teilweise bereits in Seitenreferenzen enthalten! Nicht alles als Projektionsbug bezeichnen.
- Farbähnlichkeits-Gate für Seiten: `ownership_consistent_sides` erzeugte zusätzliche Grenzen, verworfen. Keine weitere Threshold-Suche ohne neue Ursache.
- Qwen-Farbkorrektur behebt Referenzfarbe, aber allein keine lokale geometrische Zuordnung. Details unten.

## Qwen: erstmals lokal erfolgreich, aber nach Projektion verworfen

Ordner `ranger_qwen_reference_20261009` enthält alleInputs/Workflow/Histories. BestehendeModelle, keineDownloads: qwen_image_edit_fp8_e4m3fn (~20.43GB),qwen_2.5_vl_7b_fp8_scaled,qwen_image_vae. KEINE vorhandene4StepLoRA verwenden: ihr Name entspricht nicht der Edit-spezifischen TemplateLoRA.

Fehlerkette:
- lowvram zwingt Textencoder aufCPU, absichtlich abgebrochen.
- normalvram: Windows1455 in safetensors.safe_open.
- vorhandener schreibgeschützter mmap-Loader konnte Datei öffnen. `--fast dynamic_vram` umgeht erstenFehler, aber zusätzlicher pinnedRAM-Puffer lief inCPU-OOM.
- **Funktionierende isolierte Flags:** `--normalvram --fast dynamic_vram --disable-pinned-memory --disable-all-custom-nodes --listen 127.0.0.1 --port 8193`, HF_HUB_OFFLINE=1. Basisverzeichnis obigerQwenOrdner, `--extra-model-paths-config` dessen`model_paths.yaml`, `--user-directory` dessen`user`. DynamicVRAM meldet experimentellenAllocator; nicht alsProduktionsstandard aktivieren.
- Erfolgreicher Prompt `399cd60a-674d-42b3-b856-4be5e4962776`, `submission_dynamic_no_pinned.json`, `history_dynamic_no_pinned.json`,20Steps+VAE in278.84s.
- `workflow_api.json`: seed0,euler/simple,20Steps,cfg2.5,shift3,CFGNorm1,VAEEncodeOriginal,TextEncodeQwenImageEdit. Nicht einfach erneut starten; Ergebnis ist vorhanden.
- Bild `output/ranger_left_material_edit_00001_.png`, SHA `e72aa8030d7f579263e3fb9d1c3f3a16819e9951f1d1f9440fcd43713280a1fa`,1024². Ziel: helle Seitenweste/untereKleidungsflächen inbraunesLeder; Rest beibehalten. GrobeSilhouettenIoU.985718 ist KEIN semantischerBeweis. Hosenkanten wurden unerwünscht mitgeändert.

`quality_lab/project_local_reference_edit.py` projizierte nur hellesKleidungsROI. `garment_roi.json` ist ausdrücklich FIXTURE-SPEZIFISCH, keine fertigeAutomatik! Masken undProvenienz in`projected_left`. Ausgangsatlas warFront/Back-Kandidat. 76.285Texel geändert; außerhalbMaske exakt erhalten. OriginalGLB-BIN9385592Bytes erhalten, nurAlbedo angehängt/referenziert.

`projected_left/candidate.glb`, SHA `c20e92faff2fde9c370f075d9c8bcf23e2cdd1413ed96092bd8e5a8e064744eb`: unabhängigerBlenderImport bestanden,2KMaps,Geometrie/Größe erhalten. Renders0,-35,-90 unter`projected_left/renders`, Report`import_report.json`. **VisualGateABGELEHNT** (`visual_gate.json`): seitlicherLederfarbton besser, aber versetzte/doppelte untereKleidungsränder. Keine Promotion. Keine zweiteSeite generieren, bevor dieseKorrespondenzursache behoben ist.

## PBR nicht mit Texturqualität verwechseln

Keine zusätzlicheGlanzhülle/keinClearcoat gefunden. MR-Packung korrekt(B=Metall,G=Rauheit), MedianRauheit~.765/Metall~.035 in begrenzterUV-Stichprobe. KeineNormalmap. MatteKontrolle bleibtweich: eingebrannteBeleuchtung/Geometrie vermutlichmitverantwortlich. AlteMR kann nachAlbedoänderung semantischabweichen; noch nicht bewiesen. MR unverändert lassen, Farbabnahme inUnlit, PBR separat abnehmen.

## Nächster Arbeitsblock – konkrete Aufgaben

Grok übernimmt Koordination. Bots bekommen abgegrenzte Dateien; nur EIN GPU-Besitzer. Erst Status lesen, dann Arbeit verteilen. Bei Widersprüchen zählt tatsächlicherCode/Artefakt, nichtIssueBehauptung.

**Bot A: Korrespondenzdiagnose, zunächstCPU.** VorhandeneFront/Seitenreferenz, alignedPNG, aktuelleRenders undUV kontrollieren. UntereKleidungsränder/Gürtel lokal gegenüberstellen. GlobalIoU ist zu schwach. Feststellen, ob Kantenverschiebung ausSilhouettenfit, perspektivischerAbweichung, anderemKleidungsdesign oder fehlenderGeometrie entsteht. KonkreteKoordinaten/Overlay und eine überprüfbareHypothese liefern. Keine neueGeometrie in diesemBlock.

**Bot B: unabhängigeAbnahme.** Baseline/vorherigesHybrid/FrontBackKandidat/QwenDiagnose mit exakt gleichenKameras undUnlit vergleichen. Prüfen, welcheNaht neu versusvorhanden ist. KritischeGesichts-,Gürtel-,Saumregionen dokumentieren. Kein Erfolg allein ausImport/Hash. BestehendeDateien nicht überschreiben.

**Grok/Hauptbot: genau eine begründeteKorrektur.** Erst A/B-Ergebnis nutzen. Bevorzugt lokale materialgrenzenbewussteZuordnung oderErhaltung vorhandenerOberflächengrenzen; nicht blind Seitenreferenz darüberblenden. WennShapeWiderspruch bei fixierterGeometrie unlösbar, Grenze explizit belegen stattParameterreihe. Keine manuelleRangerMaske als fertigesAutomatikfeature verkaufen. Hypothese, erwarteterGewinn undStopkriterium vorLauf insLog.

**Bot C optional: Pipelineprüfung ohneGPU.** Opt-inSequentialPaint undExportregression prüfen, keineÜberarbeitung parallelzuHauptbot. Nutzer will schließlichAutomatik; Qualitätsexperiment undIntegrationsarbeit getrenntnachweisen.

Nach einer Korrektur: eigenesVerzeichnis; originalGeo/UV/MR prüfen; `replace_glb_albedo_exact.py` nutzen; BlenderImport/2KEmbeddedMaps; gleiche0,±35,±90,180Renders; Gesicht/Mund/Gürtel/Saum prüfen. BeiMehrnähten verwerfen. Bei sichtbaremGesamtgewinn echtenFinalize undfrischeSequenz mit zweitemMotiv prüfen. Erst danach überDefaultpromotion entscheiden, bestehendeExecutionPlanGates verbindlich.

## Bestehende Codeänderungen und Prüfgrenzen

- `desktop/color_preview.py`: echteKHR_materials_unlitPreview, OriginalBIN erhalten. `stages.py` kopiert bei textures=false geometry-onlyGLB unverändert; vorherigerNoMaterialFehler repariert.
- `desktop/pipeline.py`: opt-in `experimental_paint_sequential=true`, `paint_resolution=1024`, explizit`paint_multiref=false`. Default bleibt512/768. NeueAttemptverzeichnisse,12PNGHashes vorPromotion, relevanteCodefingerprints. VollständigeStudioKette damit noch nichtabgenommen.
- `quality_lab/run_paint_sequential.py`,SamplerCheckpoint,Decoder trennenSampling/DecodeProzesse. Checkpoints/12Outputsprüfen, CLIresume nurpassend. KeinmanuellgesetzterCache alsfrischerLauf ausgeben.
- CPU-Tests fürSequentialPaint/Cache/Unlit sowieechterGeometry-onlyFinalize bestanden. DetailsimlangenHandoff. Nicht unnötigTests wiederholen ohneÄnderung/Unsicherheit.

## Beispiel für unabhängige Abnahme

PowerShell, cwdComfyUI:

```powershell
& 'C:/Users/Shadow/Downloads/SF3D_Tools/Blender_5.2/Blender Foundation/Blender 5.2/blender.exe' --background --python 'IMG2GILB/quality_lab/codex_blender_import_check.py' -- --model '<absoluter Kandidat.glb-Pfad>' --out '<neuer Renderordner>' --angles 0 35 -35 90 -90 180 --resolution 1024
```

Dies rendertCPU/Unlit undändertSourceGLBnicht. PBR-Prüfung separatmit`--pbr`. KeineBrowserabnahme darausableiten. WindowsComputerUse war wegenunsichererBrowserURLgestoppt; dieseSperre nichtübergehen.

## Übergabe-/Kommunikationsregeln

PrivateBilder/GLBs lokalhalten, nicht insRepohochladen. ReviewbareCode/Markdownänderungen gezieltcommitten, fremdeDateien erhalten. DiesenHandoff hatCodex lokalgeschrieben; NICHT behaupten, Grok habeihngelesen oderGitHubseiaktualisiert. FallsimIssue#1 koordiniertwird, SendimmerperReadbackverifizieren. ProArbeitsblockkurzeNachrichtmitBild, tatsächlichemGewinn/Fehler undnächstemSchritt. Bei unverändertemStand keinStatusspam. AlleKandidaten undAblehnungsgründe erhalten.

## Continuation after user reset usage limit
Codex continues ownership; Grok handoff is saved context, not evidence Grok received control. Local DIS bidirectional registration experiment completed (projected_left_registered): only1455/15837targetpixels reliable at2pxcycle/24pxdisplacementgate; mediancycle7.25px. Generated GLB029c85879de2eec06a00a5c77b08b97f8451b3a4f0b2c0b54ab12c266d8782de NOT accepted; no independentBlenderaudit yet because correspondence gate alreadyfailed. Images show reference garmentcut differsfromcurrentmesh. No threshold sweep.
Next justified hypothesis: enhance the actual current model render, preserving its panel layout, instead of projecting an incompatible reference silhouette. workflow_modelspace.json uses model_left_source.png copiedfromregistration_target.png, same20stepQwen settings, prompt onlyrestoreexistingbrownleatherdetail and preserveallgeometry/panelboundaries. Isolated8193 server restarted withpreviousworkingflags, session58036. No productionpromotion. Poll authoritative submission/history oncequeued; no parallelGPU jobs.

## Model-space whole-image refinement: terminal, no quality promotion
Qwen prompt66a68cc9-40be-4d6e-bd53-baf6df2ec941 completed in275.66s, history_modelspace.json. Output output/ranger_modelspace_leather_00001_.png SHA30f46e105f1cfa2e787a979017142a856707274d2b40a6a5dd100b7c5e55e370. Inputactualmodelrender; silhouetteIoU.99641 atmaxRGB>20. Visualreview: layoutpreserved, mainlycontrast/colorchange, existing blurred/smearedleatherstructure persists. modelspace_image_gate.json rejects substantialqualitygain; NO projection/newGLB fromthisimage. Do not treat successfulinference asbreakthrough.
Both directreferenceprojection and genericwholemodelrefinement nowhaveboundednegativeevidence. Next justified work must address limitedlocalpixelallocation: garment occupies roughly175x260boundingROI in1024wholebodyimage, actualvisibleareasmaller. A future single region-specific model-space refinement can supply a larger clothingcrop while preserving existing boundary/coordinate transform and originaloutsidepixels. This is an untested hypothesis, NOT an instruction to run a prompt/parameter sweep. First inspect crop detail and define edge/reference acceptance. Existing changes must remain lab-only. No productiondefault or comparisoncandidate changed.
Stopped isolated8193 server onlyafteremptyqueueverified; session58036no longeractive. Onlycomparisonserver remains. live_status.json updated. Full objective remains unmet; no blocker status asserted.

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


## Face-derived transition tested; not promoted (2026-10-09)
- combine_paint_body_reference_head.py accepts --gate-audit with exact mesh SHA binding and validates accepted/range; input atlas hashes now recorded.
- Candidate ../quality_runs/ranger_texture1024_20261009/paint_body_auto_head/candidate.glb SHA661d2b48380d6393b26137447a0f21123f6829f78e5fe136066758b04573b9e3. Original 9,385,592 BIN bytes preserved, body outside gate exact.
- Independent Blender front/+35 closeups complete. Face retained but lowered gate changes neck color and produces a faint horizontal boundary. visual_review.json says DO NOT PROMOTE. Viewer remains verified no-depth-margin fixed-gate candidate.
- Mechanical bust audit ../quality_runs/bust_ownership_guarded_20261009/detected_head_gate.json rejected: no confirmed destination face. This is a negative detection control, NOT successful second-motif quality acceptance.
- Root limitation: vertical slab includes skin/collar/hair together. Next ownership correction needs material/surface-aware region selection; do not sweep height thresholds.


## Second motif complete: technical pass, visual gate fail
Session56055 completed sampling+sequential decode, all12 maps1024/hash checks passed with --ff-chunk. Session20041 completed bake284.55s + albedo-only append + real finalize. Session55203 independently imported final output and rendered front,+35,-35,180 at1024.
Final GLB: ../quality_runs/bust_texture1024_20261009/export_ff_chunk/finalized/output.glb SHA64cd5664484d1a09a7b8d118d07cade47fcbd1e0f8fe3e2c57d093c70cf79e9f. Baseline binary9461896bytes preserved before finalize; vertices/faces/UV/albedo/MR pixel checks all true across finalize.
Visual finding: asymmetric facial lenses improved vs baseline. New duplicate shoulder skull visible at+35; invented lettering/symbols already in generated albedo_0; mesh defects persist. Technical success is not quality acceptance. Decision visual_review.json = technical_pass_visual_gate_fail. Do not promote production defaults. Next meaningful quality target is cross-view semantic consistency/source assignment, not another resolution/height/GrabCut sweep. Existing baseline seed42 vs newseed0 prevents pure resolution attribution.


## Multireference controlled trial terminal: reject before bake
Session72747 exit0, all12 native1024 maps passed. Four references confirmed in log/checkpoint. Front and side raw maps0,1,3 inspected against previous same-seed FFchunk single-reference trial. Repeated shoulder emblems persist on both side images; front lenses regress toward symmetry. Candidate rejected BEFORE bake: ../quality_runs/bust_texture1024_20261009/sequential_multiref/visual_review.json. No new final GLB created or promoted.
Conclusion is scoped: adding reference images through existing image/DINO conditioning does not enforce correct per-surface symbol placement for this fixture. Do not repeat reference-count/seed/step sweeps. Existing best Ranger GLB unchanged; bust single-reference GLB remains technically valid but visual-gate failure. Next substantive quality work must address explicit image-to-surface correspondence or generation conditioning, not atlas sharpness alone. No active GPU job remains from these trials.
