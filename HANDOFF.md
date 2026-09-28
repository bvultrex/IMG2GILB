# IMG2GILB – Projekt-Handoff

Stand: 28. September 2026. Windows-/Shadow-PC-Labor, ComfyUI, Stable Fast 3D, Hunyuan3D und Quest-3-Zielviewer.

Dieses Dokument beschreibt den überprüften Arbeitsstand. Es ist kein vollständiger Installer und enthält keine Modellgewichte oder Referenzbilder. Die unten genannten lokalen Pfade beziehen sich auf den bestehenden Shadow-PC. Forschungsergebnisse, visuelle Einschätzungen und offene Tests sind ausdrücklich getrennt.

## 1. Ziel und Arbeitsweise

Aus einem Referenzbild beziehungsweise mehreren konsistenten Ansichten soll ein texturiertes, korrekt skaliertes und möglichst riggbares GLB entstehen. Endziel ist eine flüssige Darstellung in [Quest3-MR-ModelViewer](https://github.com/bvultrex/Quest3-MR-ModelViewer) auf Meta Quest 3. Etwa 100.000 Vertices und 2K-Texturen waren bisher ein funktionierender Erfahrungswert, keine verbindliche Qualitätsgrenze oder gemessene universelle Hardwaregrenze.

Der Nutzer möchte selbst nur dann eingreifen, wenn Anmeldung, externe Freigabe oder physische Bedienung erforderlich sind. Logs selbst auswerten, jeweils den ersten relevanten Fehler beheben und denselben Test wiederholen. Die funktionierende Installation nicht von vorne aufbauen. Änderungen und überprüfte Ergebnisse im lokalen `DEBUG_LOG.md` festhalten.

Ursprüngliche Abnahmekette: Bild laden → BRIA → Geometrie → Remesh/UV/Bake → Vorschau → GLB → normaler Viewer/Blender → reale Größe → zweites Bild ohne erneute Reparatur. Diese SF3D-Basiskette funktioniert. Der erweiterte Qualitäts-/Rigging-/Quest-Workflow ist noch nicht insgesamt abgeschlossen.

## 2. Wichtigster aktueller Stand

- **SF3D läuft.** DINOv2/Transformers-v5-, Baker- und kleine-Modell-Vorschau-Probleme sind repariert.
- **Hunyuan3D 2.0 läuft separat.** Form- und Texturtests sind ausgeführt, nicht nur recherchiert.
- **Paint 2.1 läuft mit sechs echten generierten 768px-Ansichten.** CPU-Offloading und sequenzielles Laden der Modelle reichen auf dieser GPU aus. Ein Vier-Ansichten-Sparmodus war für diese Tests nicht nötig.
- **Mehransichten-Geometrie ist jetzt getestet:** Hunyuan3D-2mv mit einer, zwei und vier Referenzen eines neuen Anime-Charakters.
- **DINOv3-Zugang ist freigegeben.** Konfiguration und vollständige Gewichte wurden erfolgreich offiziell heruntergeladen. Frühere Hinweise auf eine ausstehende Genehmigung sind überholt.
- **TRELLIS.2 wurde noch nicht ausgeführt.** Zugang ist gelöst; separate kompatible Windows-Laufzeit und End-to-End-Test fehlen weiterhin.
- **Quest-Gerätemessungen fehlen.** Die Quest ist nicht direkt per USB mit dem Shadow-PC verbunden; der Nutzer kann Virtual Desktop/Tailscale oder Sideloading verwenden.

## 3. Umgebungen strikt auseinanderhalten

| Bestandteil | Bestehender Pfad / Stand |
|---|---|
| Arbeitsverzeichnis / Logs | `C:\Users\Shadow\Documents\ComfyUI` |
| Aktive ComfyUI-Installation | `C:\Users\Shadow\Downloads\ComfyUI_windows_portable\ComfyUI` |
| ComfyUI-Python | `C:\Users\Shadow\Downloads\ComfyUI_windows_portable\python_embeded\python.exe` |
| ComfyUI-Versionen | Python 3.13.14, Torch 2.13.0+cu130, Transformers 5.15.1 |
| ComfyUI-Server | `http://127.0.0.1:8188` |
| SF3D-Node | Portable-ComfyUI `custom_nodes\stable-fast-3d` |
| Isoliertes Labor | `D:\SF3D_QualityLab` |
| Labor-Python | `D:\SF3D_QualityLab\venv\Scripts\python.exe` |
| Labor-Versionen | Python 3.10, Torch 2.6.0+cu124, Diffusers 0.32.2, Transformers 4.48.3, Accelerate 1.3.0 |
| Hunyuan-2-Code | `C:\Users\Shadow\Documents\ComfyUI\Hunyuan3D-2-Lab` |
| Hunyuan-2.1-Code | `D:\SF3D_QualityLab\research\Hunyuan3D-2.1` |
| TRELLIS-Wrapper, bisher nur vorbereitet | `D:\SF3D_QualityLab\research\ComfyUI-Trellis2` |
| Modelle | `D:\SF3D_QualityLab\models` |
| HF-Cache | `D:\SF3D_QualityLab\hf` |
| Blender | `C:\Users\Shadow\Downloads\SF3D_Tools\Blender_5.2\Blender Foundation\Blender 5.2\blender.exe` |
| Quest-Repository | `C:\Users\Shadow\Documents\ComfyUI\Quest3-MR-ModelViewer` |

GPU: NVIDIA RTX A4500, zuletzt **20.470 MiB gesamter VRAM** gemessen. Ältere Berichte über etwa 19 GiB dürfen nicht mit einer anderen GPU gleichgesetzt werden. Freien Speicher vor weiteren großen Downloads erneut prüfen. Modelle werden im Labor nacheinander geladen; unabhängige GPU-Benchmarks nicht gleichzeitig starten.

Die Labor-Pakete nicht in das eingebettete ComfyUI-Python installieren. Neue TRELLIS-Wheels passen nicht automatisch zu einem dieser beiden vorhandenen Python-/Torch-Paare.

## 4. Reparierter SF3D-Basisstand

Lokales Reparaturpaket: `C:\Users\Shadow\Downloads\SF3D_Final_v14.zip`.

- v12: vendortes DINOv2 mit Transformers v5 kompatibel gemacht; lokaler Pruning-Helfer und Inferenzpfad ohne benutzerdefinierte Head-Masks. Der frühere Fehler `Dinov2Model ... get_head_mask` ist behoben. Benutzerdefinierte Head-Masks bleiben ausdrücklich nicht unterstützt.
- v13: Texture-Baker-Dispatch verwendet vorhandene CPU-Kernel, wenn keine CUDA-Kernel eingebaut sind. Eingaben zusammenhängend und passend typisiert (`float32`/`int32`), Ergebnisse zurück zum aufrufenden Gerät. Quellen und installierte Baker-Datei berücksichtigt; kein Neuaufbau der ganzen Umgebung.
- v14: Kamera-Clipping und Framing folgen der physikalischen Modellgröße, nur ein Render-Loop, Ressourcen beim Austausch freigeben, Loader-Fehler korrekt behandeln.
- Optionaler `rembg`-Import bleibt optional; BRIA übernimmt die Maskierung.

Workflow `Img2GLB_SF3D_BRIA_v14.json` ist unter Portable-ComfyUI `user/default/workflows/` installiert. Basistest: Dreiecke, circa 8.000 Vertices vor UV-Auftrennung, 1K-Texturen, längste Ausdehnung 100 mm. Mehrere unterschiedliche Eingaben wurden im selben Server erfolgreich verarbeitet. Baker-Tests und zwölf Achsen-/Einheitenkombinationen des Größen-Nodes bestanden.

Späterer SF3D-Charaktervergleich mit ungefähr 100K/2K funktionierte ebenfalls, brachte aber nicht automatisch die Formtreue des Meshy-Modells. Mehr Remesh-Vertices erzeugen keine fehlenden semantischen Details.

Das v14-Paket repariert bekannte Dateistände mit Prüfsummen und Backups. Es ist kein allgemeiner Neuinstallationsassistent. Vorhandene lokale Änderungen nicht blind überschreiben.

## 5. Referenzen und faire Vergleiche

### Realistisch stilisierter erster Charakter

- Meshy-Referenz lokal: `C:\Users\Shadow\Downloads\Meshy_AI_Midnight_Defiance_Running.glb`.
- Diese Meshy-Erzeugung hatte **Front und Rücken** als Referenzen. Das bisherige Hunyuan-2-Seed42-Mesh entstand dagegen aus **nur der Frontansicht**. Nachträgliches Texturieren mit dem Rückenbild ändert diese Geometrie nicht.
- Meshy-Referenzanalyse: ungefähr 105.082 Vertices, 102.852 Dreiecke, 28 Bones, zwei Clips; 2K-Farb-/Normaltexturen und 4K-Metallic/Roughness. Das ist ein Vergleichsasset, keine lokale Generierung.
- Nachgereichte Original-JPEGs: 853×1280 statt bisher 832×1248. Nur circa 5,15 % mehr Pixel; nach Größenanpassung sehr ähnliche Bilddaten. Kein großer Auflösungssprung.
- Originalkopien: `D:\SF3D_QualityLab\original_references`; Analyse: `original_reference_comparison.json`.
- Schwarze Haare vor schwarzem Hintergrund werden in der Rückenmaske teilweise abgeschnitten. Das ist ein Eingabe-/Maskenproblem und muss unabhängig von Texturschärfe behandelt werden.

### Neuer Anime-Charakter

Vier Original-JPEGs mit 1280×1280: Rücken, Front, Profil nach Bild-rechts, Profil nach Bild-links. Lokale Kopien und alle BRIA-Ausgaben liegen in `D:\SF3D_QualityLab\anime_test`.

View-Zuordnung im Test: Front → `front`, Rücken → `back`, Profil nach Bild-rechts → `left`, Profil nach Bild-links → `right`. Quelle/Hash/BRIA-Prompt-IDs stehen in `anime_test/inputs.json`. Zeichnungen sind keine kalibrierten Fotos einer exakt identischen Pose; Gesicht, Haare und sichtbare Armteile sind nicht vollständig konsistent.

## 6. Hunyuan- und Texturversuche

### Hunyuan 2.0

`run_shape.py`: Standardmodell, zwei Seeds, 50 Schritte, Guidance 5, Octree 384; ungefähr 90 Sekunden und 5,6 GiB Torch-Spitzenallokation. Seed42 wurde als erste Formbasis gewählt. Dateiname: `outputs/Hunyuan2_shape_seed42.glb`.

Geometrie Seed42: 271.524 Dreiecke, rund 135.764 geometrische Vertices; durch UV-Nähte 213.165 exportierte Vertices. Vergleichshöhe 1,70 m. Texturierung, UV-Bake, Validator und Blender-Import ausgeführt.

RealESRGAN_x4plus und RealESRNet_x4plus wurden auf denselben sechs erzeugten Ansichten getestet und neu gebacken. Etwas schärfere Darstellung, aber keine Reparatur erfundener Schrift, falscher Geometrie oder verlorener Haare. Kein Hauptpfad mehr. Details: `UPSCALE_REVIEW.md`.

### Paint 2.1 – tatsächlich gemessene Ergebnisse

| Fall | Generierung | Laden + Generierung | Torch allocated | Torch reserved | Gemessene gesamte GPU-Spitze |
|---|---:|---:|---:|---:|---:|
| Erster Charakter, 6×512 | 38,938 s | 70,156 s | 6,524 GiB | 7,420 GiB | 9.888 MiB |
| Erster Charakter, 6×768 | 126,234 s | 158,656 s | 9,760 GiB | 11,801 GiB | 14.359 MiB |
| Anime, 6×768 | 135,515 s | 168,125 s | 9,760 GiB | 11,801 GiB | 13.907 MiB |

GPU-Gesamtspeicher wurde sekündlich abgefragt; kurze Spitzen können fehlen. Baking und UV-Erstellung sind in diesen Zeiten nicht enthalten. Das sind Messungen dieser Konfiguration, keine universellen Speicherzusagen.

Reparaturen ausschließlich im Labor:

1. Trainingsabhängigkeit Lightning nicht schon beim Inferenz-Paketimport erzwingen.
2. Offizielle UNet/VAE/Textencoder/Tokenizer/Scheduler-Komponenten explizit laden, weil der generische Diffusers-Loader am serialisierten benutzerdefinierten UNet scheitert. Striktes Laden der UNet-Gewichte bleibt aktiv.
3. VAE-Eingaben vor `encode` auf das tatsächliche Ausführungsgerät verschieben; CPU-Offload ließ sonst Eingaben auf CPU und Modell auf CUDA auseinanderlaufen.
4. DINOv2-Features vorab berechnen, DINOv2 freigeben, erst danach Paint laden. CPU-Offload plus VAE-Slicing/-Tiling, 15 Schritte, CFG 3, ursprüngliche drei Guidance-Zweige.

**Sechs generierte Paint-Kameraansichten sind keine sechs Eingabereferenzen für die Form.** Der aktuelle Paint-2.1-Adapter nutzt nur eine Frontreferenz für die Farbführung. Auch beim Anime-Test wurden vier Referenzen für die Form, aber nur eine für die Farbe verwendet.

Erster Charakter: Farb- und PBR-GLB exportiert; beide Geometrie-/Normalenprüfungen bestanden. PBR in Blender mit zwei eingebetteten 2048×2048-Texturen und korrekter Höhe geöffnet. Farbe 14.003.964 Bytes, PBR 16.793.120 Bytes. Beide Karten zusammen zu backen dauerte 228,609 Sekunden.

Generierte MR-Kanäle: R = Metallic, G = Roughness. glTF benötigt G = Roughness, B = Metallic. Die Exportkonvertierung berücksichtigt das. Farbvergleich: Metallic 0, Roughness 0,8. PBR-Variante: Faktoren jeweils 1 und gepackte MR-Karte.

### Projektion echter Referenzdetails

`project_references.py` testet sichtbarkeits- und winkelgewichtete Front-/Rückenprojektion in die bestehende UV-Textur. Alpha und vormultiplizierte Farben begrenzen Hintergrundübertragungen.

Nur Bounding-Box-Ausrichtung scheiterte sichtbar. Individuell gesetzte Bildpunkte verbesserten die Silhouettenüberlappung vorne von 0,747 auf 0,838, hinten von 0,551 auf 0,842. Diese Zahl ist **kein allgemeiner Qualitätswert**. Die Landmark-Datei gilt nur für den ersten Charakter und darf nicht auf den Anime-Charakter übertragen werden.

Originaltreue von Gesicht/Schrift/Tattoos in passenden Bereichen verbessert; Übergänge, Fotoschatten und geometrisch falsche Haarlänge bleiben. Als Experiment archiviert, nicht als fertiger automatischer Ersatz aktiviert. Details: `REFERENCE_PROJECTION_RESULTS.md`.

## 7. Anime-Vergleich – ausgeführt

Hunyuan3D-2mv, gleicher Seed42,50 Schritte, Guidance5, Octree384. Auch der Front-only-Vergleich verwendet hier das MV-Modell; nicht mit dem älteren Standardmodell-A/B verwechseln.

| Eingaben | Laufzeit Form | Vertices vor UV | Dreiecke | Raw-Mesh watertight | Torch-Spitze |
|---|---:|---:|---:|---|---:|
| Front | 86,094 s | 185.801 | 371.562 | nein | 5,574 GiB |
| Front + Rücken | 101,688 s | 160.850 | 321.696 | nein | 5,582 GiB |
| Vier Ansichten | 140,062 s | 175.001 | 350.034 | ja | 5,597 GiB |

Vier Ansichten wurden für den Texturtest ausgewählt: hinterer Haarverlauf und Profil erkennbar, geschlossenes Raw-Mesh. Hände/Finger und Gesicht bleiben vereinfacht. Kein Rigging und kein Nachweis, dass vier Ansichten allgemein immer besser sind.

UV-Unwrapping:136,391 Sekunden;12.657 Inseln; interne Packgröße4113×4111, Ausgabe2048×2048;278.722 Vertices nach UV-Auftrennung. Die nominellen8px Padding entsprechen bei der späteren Verkleinerung nicht8px finalem Padding. Diese Fragmentierung ist ein späterer Optimierungspunkt.

Paint2.1 hat die sechs768px-Ansichten erfolgreich erzeugt. Grobe Farbgebung, Kragen und Schmuck bleiben erkennbar; Augen werden sehr dunkel, feine gezeichnete Details gehen verloren. Daher bislang **erkennbare stilisierte Ausgangsfigur**, keine zugesagte vorlagentreue Anime-Endqualität.

Farb-GLB wurde bereits exportiert und validiert:16.657.324 Bytes,278.722 Vertices,350.034 Dreiecke,2K-Farbtextur,1,70m; keine Positionsänderung, Normalenfehler unter3e-8. Abschluss von MR-Bake/Blender wird im untenstehenden Abschlussvermerk festgehalten.

### Nicht aktivierte Beschleunigung

Die Python-UV-Füllung dauert bei dieser Geometrie erheblich länger. Die vorhandene C++-Implementierung wurde separat in `native_inpaint` gebaut. Synthetischer Vergleich bestand, der Vergleich mit dem vollständigen Atlas jedoch nicht: mittlerer8-Bit-Fehler0,05676;0,3665% der Farbkanäle weichen um mehr als2 ab; Maximum186. Anpassung der Rundung beseitigte das nicht. Ursache nicht abschließend geklärt.

**C++ ist nicht im gelieferten Bake-Runner aktiviert.** Keine Behauptung identischer Ergebnisse oder eines validierten Produktions-Speedups. Der Python-Lauf wurde während dieser Untersuchung nicht abgebrochen. Build-/Diagnoseskripte bleiben separat für spätere Analyse erhalten.

## 8. DINOv3 / TRELLIS.2 – nächster Modellvergleich

Der ursprüngliche HTTP403 mit ausstehender Freigabe ist erledigt. Offizieller vollständiger Download am28.09.2026 erfolgreich:

`D:\SF3D_QualityLab\models\facebook\dinov3-vitl16-pretrain-lvd1689m`

Revision: `ea8dc2863c51be0a264bab82070e3e8836b02d51`.

Vorbereiteter Windows-Wrapper: [visualbruno/ComfyUI-Trellis2](https://github.com/visualbruno/ComfyUI-Trellis2). Der gelesene Stand dokumentiert Python3.11/Torch2.7+cu128 sowie versionsgebundene Wheels. Aktive ComfyUI-Umgebung nicht entsprechend downgraden. Separate Umgebung und passende Wheels für CuMesh, nvdiffrast, flex_gemm, o_voxel etc. wählen; optionales Pixal3D nicht gleichzeitig zum Pflichtumfang machen.

Noch offen: kompatible TRELLIS-Laufzeit einrichten, Native-Imports prüfen, offizielle passende Modellgewichte laden, einen kontrollierten Charaktertest ausführen, Geometrie/Material/GLB/Blender validieren. Erst danach Qualitäts- oder Speicherbehauptungen machen. Die DINO-Freigabe allein beweist noch keine funktionierende TRELLIS-Installation.

## 9. Modell-/Quellrevisionen

| Quelle | Verwendete Revision |
|---|---|
| Hunyuan3D-2 Quellcode | `f8db63096c8282cb27354314d896feba5ba6ff8a` plus dokumentierte lokale Änderungen |
| Hunyuan3D-2 Modelle | `9cd649ba6913f7a852e3286bad86bfa9a2d83dcf` |
| Hunyuan3D-2mv Modelle | `3a761b539b29fe4ff64714813aa9560fd66f5de0` |
| Hunyuan3D-2.1 Quellcode | `82920d643c0dc2f7bfd7255f45f62d386edfe60c` plus Inferenzpatch |
| Hunyuan3D-2.1 Paint-Gewichte | `0b94677654c57bb9a6b6845cd7b704ccf551d327` |
| DINOv2 giant | `611a9d42f2335e0f921f1e313ad3c1b7178d206d` |
| DINOv3 ViT-L/16 | `ea8dc2863c51be0a264bab82070e3e8836b02d51` |

## 10. Lokale Runner und Nachweise

Alle folgenden Laborpfade sind relativ zu `D:\SF3D_QualityLab`:

| Datei | Zweck |
|---|---|
| `Run_Paint21_Test.bat` | Ersten Charakter mit vorhandenen Kontrollansichten und UVs erneut texturieren |
| `run_paint21.py` | Parameter `--input`, `--controls`, `--output`, `--views`, `--resolution`; alte Defaults erhalten |
| `bake_paint21.py` | Parameter `--input`, `--uv-cache`, `--output-prefix`; Farb-/MR-Bake und GLB |
| `validate_paint.py OUTPUT.glb [SOURCE.glb]` | Geometrie, Normalen, UVs,2K-Textur, Maße; zweite Angabe erlaubt andere Charaktere |
| `check_paint_blender.py` | Blender-Import und1,70m-Testhöhe; JSON-Bericht prüfen |
| `Run_Anime_Test.bat [front\|front_back\|four]` | Neue Referenzen → BRIA →1/2/4-Geometrie → ausgewählte UVs → Paint → Bake → Validierung → Viewer |
| `prepare_anime_test.py` | Originalkopien, BRIA-API-Jobs, RGB/Alpha-Vorbereitung |
| `run_anime_shape.py` | Gleicher Seed und Parameter für die drei View-Konfigurationen |
| `prepare_anime_paint.py` | Neue UVs und sechs Normal-/Positions-Kontrollansichten |
| `Run_Reference_Projection.bat` | Erster Charakter mit spezifischen manuellen Landmarken |
| `apply_paint21_patches.py` | Prüfsummenbasierte Inferenzpatches, idempotent; Payload/Manifest lokal |
| `PAINT21_RESULTS.md` | Messwerte und bekannte Grenzen erster Paint2.1-Test |
| `anime_test/README.md` | Neuer Charakter, Ergebnisse und Einschränkungen |
| `QUALITY_STRATEGY_AUDIT.md` | Forschungsstand und Prüfung des echten Vier-/Sechs-View-Verhaltens |
| `MESHY_TRIPO_WORKFLOW_RESEARCH.md` | Primärquellen und daraus abgeleitete Testreihenfolge |

Blender im Batch mit `--python-exit-code 1` starten. Bei älteren Runnern zusätzlich Ergebnis-JSON prüfen, da Blender trotz Pythonfehlern mit Exitcode0 enden kann. Für die Prüfung gespeicherter Normalen die einzelne Geometrie aus `trimesh.load(..., process=False)` verwenden; `force='mesh'` kann Geometrien zusammenführen und Normalen neu berechnen.

Diese Runner setzen das bestehende Labor voraus. Sie sind keine ortsunabhängigen Installer; `prepare_anime_test.py` enthält die aktuellen lokalen Quellpfade. Bereits erzeugte Originalkopien und Inputs nicht mit dem alten Charakter überschreiben.

Lokale Vergleichsseiten unter `http://127.0.0.1:8188/extensions/stable-fast-3d/web/`:

- `paint21-comparison.html`: Paint2.0 / Paint2.1 / Meshy.
- `projection-comparison.html`: Paint2.1 / individuell ausgerichtete Referenzprojektion / Meshy.
- `anime-comparison.html`:1/2/4-Geometrie und ausgewählte texturierte Figur.

Modellbytes werden lokal geliefert. Die Viewer-Bibliothek model-viewer4.3.1 wird vom Google-CDN geladen. Das ist kein komplett offline gepackter Viewer.

Lokale ZIPs im Downloads-Ordner: `SF3D_Final_v14.zip`, `Hunyuan2_Texture_Test.zip`, `Hunyuan2_Upscale_Comparison.zip`, `Hunyuan21_Texture_Test.zip`, `Hunyuan21_Reference_Projection_Test.zip`. Experimentpakete sind keine finale, universelle Installationsversion. Anime-Paket siehe Abschlussvermerk.

Zentrales Arbeitslog: `C:\Users\Shadow\Documents\ComfyUI\DEBUG_LOG.md`. Aktuelles lokales Labor-Handoff: `HUNYUAN_HANDOFF.md` im selben Verzeichnis. Alte Abschnitte darin sind chronologische Historie; dieser konsolidierte Stand und spätere Logeinträge haben Vorrang vor überholten Statusmeldungen.

## 11. Rigging und Quest-Viewer

Ein früherer anderer SF3D-Testcharakter wurde über Mixamo geriggt und mit einer Laufanimation wieder als texturiertes GLB exportiert.25 Bones, keine Fingerketten; Blender-Import, Größe und Animation geprüft. Das beweist nicht, dass die neuen Hunyuan-/Anime-Figuren bereits geriggt sind.

Der lokale Quest-Viewer-Stand basiert auf Commit `a479095d`. Lokaler Performance-Patch vermeidet wiederholte Uploads eingefrorener Bone-Paletten über objektbezogene UBOs. Patch-Kette und ein C++-Lifecycle-Test wurden geprüft. Keine neue APK und keine Messung auf dem Headset als erfolgreich behaupten.

Der aktuelle Renderer verarbeitet vier Gewichte pro Vertex. Exportierte Rigs entsprechend auf die vier stärksten normalisierten Einflüsse begrenzen und Verformungen prüfen. Texturkompression, Draco/KTX2/WebP etc. nur nach bestätigter Loader-Unterstützung aktivieren. Polygon-, Vertex-, Material- und Texturspeicherbudgets unterscheiden.

Nächster Quest-Schritt nach Auswahl guter Geometrie: Qualitätsmaster behalten, reduzierte Varianten herstellen, UVs/Normal-Bake prüfen, riggen und konkrete Viewer-/Headset-Messung. Normalmaps verbessern Beleuchtungsdetails, nicht die tatsächliche Silhouette.

## 12. Lehren und nächste Reihenfolge

1. Abgeschlossenen Anime-Test als Vergleichsbasis sichern; besonders Gesicht, Finger und Texturtreue beurteilen.
2. TRELLIS.2 jetzt nach erteilter DINOv3-Freigabe isoliert testen. Gleiche Referenzen und nach Möglichkeit gleiche Betrachtungsbedingungen verwenden.
3. Form vor Textur beurteilen. Zusätzliche generierte Ansichten sind keine zusätzliche beobachtete Information.
4. Für echte Originaldetail-Übertragung Beleuchtung und zuverlässige Bild-/Mesh-Ausrichtung getrennt testen. Keine alten manuellen Landmarken auf neue Figuren übertragen.
5. Erst akzeptierte Form/Materialien für Quest reduzieren und riggen. Danach auf Hardware messen.
6. Finale Patch-/Installer-Version erst veröffentlichen, wenn Wiederholbarkeit, Pfadkonfiguration und Abhängigkeiten geprüft sind. Bestehende Reparaturpakete und Experimente nicht pauschal als endgültigen Gesamtworkflow bezeichnen.

## 13. Öffentliche Quellen und Grenzen der Aussagen

- [Meshy Multi-Image API](https://docs.meshy.ai/en/api/multi-image-to-3d): getrennte Geometrie-/Textursteuerung, mehrere Eingaben, Lighting-Removal, optionale Remesh-Stufe. Daraus lässt sich nicht der genaue private Algorithmus oder die konkrete Erzeugungseinstellung der vorhandenen Referenz ableiten.
- [Tripo Multiview API](https://developers.tripo3d.ai/en/docs/generation-multiview-to-model/p): benannte Ansichten, getrennte Modellversionen, Bild-/Geometriepriorität bei Texturierung; [Texturing](https://developers.tripo3d.ai/en/docs/models-texture) dokumentiert Beleuchtungsentfernung für unterstützte Versionen.
- [Hunyuan3D-2](https://github.com/Tencent-Hunyuan/Hunyuan3D-2), [offizielles MV-Beispiel](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/blob/main/examples/shape_gen_multiview.py), [Hunyuan3D-2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1).
- [TRELLIS.2](https://github.com/microsoft/TRELLIS.2): Herstellervorgaben und Community-Sparpfade nicht mit eigenen Messungen verwechseln.
- [ComfyUI-Tripo](https://github.com/VAST-AI-Research/ComfyUI-Tripo) bindet die Cloud-API ein; es installiert nicht das kommerzielle Tripo-Modell lokal. Kein kostenpflichtiger Cloud-Test wurde im aktuellen Forschungs-/Anime-Lauf beauftragt.

## Abschlussvermerk

Anime-Python-Bake abgeschlossen: 694,859 Sekunden für Farbe und MR. PBR-Export `Anime_Paint21_2K_pbr.glb`: 18.467.536 Bytes, 278.722 Vertices, 350.034 Dreiecke, Höhe 1,699999988 m. Geometrie-/Normalenprüfung bestanden (maximaler Positionsfehler 0, Normalenfehler unter 3e-8). Blender 5.2.0 LTS importiert ein Mesh und zwei eingebettete 2048×2048-Texturen erfolgreich.

PBR-SHA256: `51bd2b279079ba9e69515e5b9ff6b7c4858cd53fe396f822e0509498f0908171`.

Lokales Archiv: `C:\Users\Shadow\Downloads\Anime_Multiview_Test.zip`. Es enthält Runner, Referenzen und Testergebnisse und wird wegen der enthaltenen Nutzerassets nicht automatisch in dieses öffentliche Repository hochgeladen. Der abgeschlossene Export beseitigt nicht die oben beschriebenen Qualitätsgrenzen. Rigging, Quest-Reduktion und Headset-Messung dieses Charakters stehen aus.



## Nachtrag: Face Textures 1.0 (28.09.2026)

[Release-Stand, Tests und Grenzen](FACE_TEXTURES_1_0.md). Automatische Anime-Gesichtsausrichtung mit weicherem Farbabschluss, unabhängig verschobenem Mund, PBR-Erhalt, Rückfall auf das byteidentische Original bei abgelehnter Erkennung und abschließender Landmarkenprüfung. Zwölf Tests, Wiederholung, Fehlerfall und Blender-Import geprüft; rund 33 Sekunden auf dem Shadow-PC. Lokaler Code: `D:\SF3D_QualityLab\face_v1`; Ergebnis: `D:\SF3D_QualityLab\anime_test\face_1_0\Face_1_0.glb`; Paket: `C:\Users\Shadow\Downloads\Face_Textures_1_0.zip`.

Der 1.0-Stand ist auf einen optionalen lokalen Anime-Gesichtsschritt begrenzt. Ein zweiter vollständiger 3D-Charakter, EXE-Gesamtoberfläche, Rigging und Quest-Gerätetest bleiben offen. Haaransatz und geometrische Gesichtsgrenzen können weiterhin Übergänge zeigen.


## 2026-09-28 - Face Refining 1.0.1 / Dark Studio
- Augenweiss und Brauen: geschuetzte Referenzfarben, erweiterte Brauenmaske, gezielte Projektionsgewichte und keine erodierten Kleinstmerkmale. Farbige Haarpalette verhindert eine Verwechslung dunkler Brauen mit Haaren.
- 21 Face-/Detektor-Tests und 4 Desktop-Vertragstests bestanden. Zwei vorhandene Anime-Meshes erneut verarbeitet. Männlicher Wiederholungslauf erzeugt byteidentisches GLB (5c5c7a7edc0e347205238fc3e260b5cc490b67319b178895fc0769d3d4c54424).
- Studio-Ergebnis 34d5260d03fe47f196324946addb3ebf: 99996 Dreiecke, 64540 Vertices, 170 cm, 2K, Blender-Import bestanden. 6736924707f441ea803278066387f0ef bleibt als Zwischenstand erhalten.
- Lokaler Farbvergleich: 439 helle Augenpixel, RGB-MAE 0.159823 -> 0.031626. Kein allgemeiner Qualitaetswert. Finale Landmarkabweichungen 0.410/0.583/0.594 px.
- Front-/Rueckentexturen separat unter D:/SF3D_QualityLab/male_anime_validation/body_reference_face_1_0_1: 973556 Atlaspixel geaendert, 0 geschuetzte Gesichtspixel. Geometrie/UV/Materialkarten erhalten. Seiten-Doppelkonturen; experimentell, nicht Standard.
- Studio dunkel/anthrazit mit neongruenen Akzenten; Theme bleibt beim Reload erhalten. Projektwahl uebernimmt nun Einstellungen, Ergebnisbezeichnungen sichtbar. Vorschau geprueft.
- Fehler f2b1d1e142464374a485a5dc76409578: Windows PermissionError beim state.tmp-Austausch, Worker bereits beendet. Status nach API-/Logabgleich auf fehlgeschlagen berichtigt. Einzigartige Tempdateien und begrenzte Wiederholung getestet. Cache beruecksichtigt jetzt auch detect.py, detection_policy.py und render_adapter.py.
- Dienstneustart weiterhin ausstehend: vorheriger Neustart wurde durch automatische Freigabepruefung blockiert (keine weitere Begruendung). Nicht umgangen. Auf Datentraeger vorbereitete Pipeline-Reparaturen sind noch nicht im laufenden Server aktiviert; unabhaengige Face-Laeufe und neue Vorschau funktionieren.
- Code lokal in IMG2GILB/face_refining; Sicherung C:/Users/Shadow/Downloads/IMG2GILB_Face_1_0_1_Patch.zip. Kein neuer Gesamtinstaller, kein neuer Modelldownload, kein Rigging. Git-Push dieses Pakets nicht ausgefuehrt.
- Naechstes Qualitaetspaket: semantische Registrierung der Kleidungsdetails/Profilansichten und robuste Seitenuebergaenge. Keine blinde Vieransichten-Projektion. Anschliessend aktivierter Dienst-End-to-End-Lauf; Quest-Messung weiterhin ohne verbundenes Headset offen.


## 2026-09-28 - Lokale Studio-Entwuerfe
Referenzbilder werden jetzt als Blobs im browserlokalen IndexedDB gespeichert, zusammen mit Qualitaet, Dreiecken, Modellhoehe, Texturaufloesung und Schaltern. Kein externer Upload und kein Hintergrundjob beim Wiederherstellen. Bilder zuruecksetzen entfernt die Entwurfsreferenzen; bestehende Projekte/Originaldateien bleiben erhalten.
Browserpruefung bestanden: Frontbild speichern und nach Reload wiederherstellen; 175 cm/1K nach Reload erhalten; Zuruecksetzen nach Reload erhalten; anschliessend alle vier Originalansichten des gelben Charakters mit 170 cm/2K wiederhergestellt. Keine Konsolenfehler beobachtet. Screenshot: D:/SF3D_QualityLab/male_anime_validation/studio-persistent-draft.png.
Grenze: Entwurf gilt fuer denselben Browser und dieselbe lokale Adresse. Das ist kein Ersatz fuer den Projektexport. Ein erneuter vollstaendiger Generierungslauf wurde in diesem Paket nicht gestartet. Rigging und Aktivierung der Dienstreparatur bleiben offen.


## 2026-09-28 - Rigging-Laufzeit vorbereitet
Separate Python-3.11.16-Umgebung unter IMG2GILB-rig-runtime angelegt; bestehende ComfyUI-/Hunyuan-Laufzeiten unangetastet. Torch 2.7.0+cu128, Transformers 4.57.6, Diffusers 0.35.2, bpy 4.3.0 und weitere Anforderungen installiert (Lockdatei desktop/rig-requirements-lock.txt). SkinTokens-Checkpoints 1.62 GB revisionsgebunden geladen; Qwen nur Konfiguration.
Windows-SDPA-Adapter im separaten Forschungscheckout: zwei harte FlashAttention-Imports ersetzt, TokenRig Backend sdpa. FP32-GPU-Test gegen explizite Attention fuer normale und gruppierte Heads bestanden; volle Inferenz noch nicht bewiesen. bpy-Hilfsserver auf 127.0.0.1 beschraenkt. demo.py --help erfolgreich.
Rigging-Validator desktop/validate_rig.py samt sechs bestandenen Tests. Meshy-Referenz: 105082 Vertices, 28 Gelenke, zwei Animationen, normalisierte Gewichte. Nicht als eigener Rigging-Erfolg zu verstehen.
Erster eigener Lauf gestartet: gelber Charakter, 100k/2K, --use_transfer, Ausgabe D:/SF3D_QualityLab/male_anime_validation/rig_trial/character_rig.glb. Session 34582; vor Fortsetzung Status abfragen, keinen parallelen Rigging-Lauf starten. UI-Rig-Schalter bleibt deaktiviert bis Struktur, Texturerhalt und sichtbare Deformation geprueft sind.


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


## 2026-09-28 — Mechanical bust detail benchmark (completed)
User supplied four 1024x1280 references, no rigging. Dataset/mapping and settings: D:/SF3D_QualityLab/bust_validation/test.json. Baseline Studio job 9c9d771bfdf844bc8e15b60509ef308d completed the existing four-view geometry -> UV -> Paint -> bake -> GLB pipeline in 832.51 s. Standard shape settings, 100k target triangles, 2K texture, 40cm assumed test height, face=false, rig=false. Actual 99,990 triangles / 69,423 exported vertices; no skins/animations. Blender import and 40cm bounds passed. GLB is NOT watertight; not a print-ready acceptance.

Controlled Paint comparison job 9b9128933bd944f9b9e30a7fc82312a6 uses FOUR reference images instead of the production front-only paint conditioning. Geometry, faces and UV arrays verified exactly identical. Six generated views at 768px, 2K atlas; no AI upscaler. Paint 209.156s, bake 300.641s; peak device memory 14,670 MiB. Existing installed Paint API accepts multiple image references; sequential DINO features are concatenated along tokens and released before paint loading. No installation or production pipeline replacement.

Visual review: front/back Blender renders compared under identical settings. Four references alter local details but do not provide a clear overall fidelity gain. Both variants simplify small mechanisms, alter lettering/emblems, miss the back hood symbol and contain baked lighting. Generated views can mix front/back details. Do not promote this experimental path as an automatic quality improvement. Raw 1,184,372-triangle geometry already lacks important small details; 100k decimation is not the principal bottleneck. Clay comparison forces equal smooth shading (raw/reduced GLBs lacked normal attributes); this is QA rendering, not a production fix.

References themselves are not fully consistent: side torso rotates while pedestal plaque remains frontal; small markings also differ. Next quality work should address reconstruction detail and camera/part-aware reference transfer, with held-out views to detect leakage, rather than simply increasing atlas size or blind sharpening.

Reports/renders: D:/SF3D_QualityLab/bust_validation/acceptance.json and four_reference/acceptance.json. Scripts: quality_lab/run_paint_multiref.py, run_bust_comparison.py, validate_bust.py, render_bust.py, render_bust_geometry.py. These are local fixture experiments. render_bust.py accepts --model and --output after Blender's -- separator. Studio history has separately labelled 1-reference control and 4-reference comparison. Existing unrelated rig/cache acceptance tasks remain open.

## 2026-09-28 — Meshy bust reference inspection
Imported user-provided Meshy_AI_Ironjaw_Warlord_0928073922_texture.glb in Blender without modifying source. 139,627,668 bytes, 3,053,548 triangles, 1,956,336 imported vertices, one mesh/material. Base color, metallic-roughness and normal images each 2048x2048. Our baseline: 99,990 triangles,69,423 vertices,9,367,400 bytes,2K base color/MR but no normal map.
Normalized both to 40cm solely in the render scene; same Workbench camera/light/smooth shading. Untextured Meshy clearly has one large plus two small lenses, corrugated hoses, grille and rivets in geometry. Our geometry has two simplified eye forms. Workbench clay does not use material normal maps, so this difference is actual shape. Source file alone cannot establish Meshy's model architecture. Current local shape stage uses Hunyuan3D-2mv at octree384/50steps; no explicit mirror operation in desktop/stages.py. Do not call this a proven mirror bug.
Scripts/renders/report: quality_lab/compare_meshy_bust.py and D:/SF3D_QualityLab/bust_validation/meshy_comparison. Reduced probe is geometry-only: seam-split vertices must be welded before decimation; naive decimation of imported glTF created severe artifacts. Only clay renders from the welded probe are valid (earlier meshy100k texture renders are superseded, not production exports). Original GLB unchanged. Next controlled reconstruction test: front-only vs four-view conditioning with same seed/extraction parameters, then evaluate shape backend/resolution separately. No further inference started in this comparison turn.
Welded Meshy geometry-only reduction completed: 99,999 triangles,49,428 vertices. Clay close-up visually checked: three asymmetric lenses and hose corrugation remain, although fine detail degrades. This supports reconstruction fidelity, not only final polygon budget, as the main gap. This diagnostic reduction is not an optimized textured/Quest-ready export.

## 2026-09-28 — Focused geometry research / ablation in progress
Completed same-seed 42, 50-step, octree384 Hunyuan2mv ablations: front only (92.05s;1,065,608 raw triangles) and front+back (104.875s;1,176,796). Both still generate two lenses, as does previous four-view run. Hunyuan Shape2.1 separately downloaded from official tencent/Hunyuan3D-2.1 revision 0b94677654c57bb9a6b6845cd7b704ccf551d327, code82920d643c0dc2f7bfd7255f45f62d386edfe60c. Missing timm1.0.15 installed only in D:/SF3D_QualityLab/shape21_deps. Shape2.1 front test120.516s,1,172,900 raw triangles,7.63GiB Torch peak; better local form but still two lenses. Not promoted.
TRELLIS isolated runtime C:/Users/Shadow/Documents/ComfyUI/IMG2GILB-trellis-runtime uses existing rig Python3.11/Torch2.7+cu128 without modifying its packages. Extra deps loaded through process-local path. Official source75fbf0183001ed9876c8dbb35de6b68552ee08bd; official model revisions in runtime/models/revisions.json. Geometry-only weights downloaded to C; reuse existing local DINOv3 and BRIA RGBA. Windows native wheels from previously prepared visualbruno wrapper Torch270 directory. triton-windows3.3.1.post21,opencv-headless4.11.0.86,easydict1.13,plyfile1.1.5,zstandard0.25.0 installed with --no-deps into runtime/deps. CC/CUDA_PATH point to Triton's bundled compiler/CUDA in this target folder.
Added sparse SDPA dispatch to official source; ragged self/cross attention matched explicit attention on CPU/CUDA. Patch saved in quality_lab/trellis_sdpa.patch. No ComfyUI reinstall. TRELLIS512 completed83.641s excluding model load,2,809,162 raw triangles,2.645GiB Torch peak. Raw FDG winding needs unification before export; Blender recalc shows improved mechanics but still two eyes and residual rough/open geometry. Do not promote raw output. 1024 cascade currently running; inspect runtime/bust1024.log and session66171 before further GPU work. Latents saved for decode-only recovery.
Primary research: https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1 (shape3.3B, published10GB VRAM); https://github.com/microsoft/TRELLIS.2 (official24GB/Linux baseline, native low_vram API). Our measured Windows behavior must not be generalized to all resolutions/assets. All experiments in quality_lab and D:/SF3D_QualityLab/bust_validation/shape_ablation.

## 2026-09-28 — Geometry ablations completed; no production promotion
Supersedes the earlier in-progress/session66171 note: all ten new geometry runs completed. Full results, commands, pinned revisions and limitations: IMG2GILB/quality_lab/GEOMETRY_BENCHMARK_2026-09-28.md (relative from workspace); quality_lab/GEOMETRY_BENCHMARK_2026-09-28.md within repo.
TRELLIS1024 cascade (152.20s), direct (79.75s), full-guidance interval (84.81s) all retain two lenses. A fixed head-only diagnostic crop (122.83s) partly recovers the large lens plus two stacked small lenses; upper lens is malformed and mesh remains rough/open. This is NOT a full-bust success or automatic region detection. Concatenating whole-image/crop DINO tokens (89.16s) fails to preserve the three-lens layout. Reject promotion.
TripoSG independently tested from official source fc5c40990181e2a756c4e0b1c2f4d6b5202faf8c and weights2c1c516d22d58db486a058d98d31bb6177344e06. Existing lab Python3.10 with isolated IMG2GILB-triposg-runtime/deps (jaxtyping0.3.3,typeguard4.4.4,wadler-lindig0.1.7). Optional DISO import moved inside unused flash path; official non-flash extraction dense7/final9 completed. Existing BRIA RGBA reused. 50steps/seed42/guidance7:37.953s,2,127,972 raw triangles,5.342GiB Torch peak. Blender clay inspection: two distorted lens rings; no whole-object breakthrough.
TRELLIS raw winding cleanup and narrow-band remesh512 probes at target100k remain non-watertight. Do not present them as print-ready or final textured assets. Head-only geometry normalized to40cm for diagnostic display is not physically scaled to the full bust. No production UI/backend default or existing ComfyUI/rig packages changed. No active GPU benchmark remains.
Next: spatially localized detail reconstruction with automatic ROI selection/registration/seam handling and rejection checks; feature concatenation alone is insufficient. Require three lenses on the complete bust, preserved silhouette, clean mesh and second-fixture validation before UI integration. Current findings are single-fixture, single-seed evidence, not a general model ranking. No claim of Meshy parity.
