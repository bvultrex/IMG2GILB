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
