# Face Textures 1.0 — lokaler Anime-Gesichtsschritt

Stand: 28.09.2026. Version 1.0.0. Reproduzierbarer optionaler Verarbeitungsschritt für das vorhandene Windows-Labor, kein fertiger Gesamtinstaller oder universeller Gesichtsrestaurierer.

## Start und Bedienung

`Start_Face_1_0.bat` im Paket führt das konfigurierte Projekt aus. Es startet keine Installation und verändert keine ComfyUI-Pakete. `anime_project.json` benennt Referenzbild, originales PBR-GLB, passenden UV-Cache und Ausgabeordner. `runtime.json` enthält die lokalen Laufzeiten und gepinnten Detektorgewichte. Alle Abhängigkeiten müssen bereits vorhanden sein.

Ergebnis: `Face_1_0.glb`, `report.json`, Gesichtsrenders, Masken und Diagnosen im Ausgabeordner. Der Bericht unterscheidet `processed`, `skipped` und `failed`. Bei übersprungener Erkennung und kontrollierten Laufzeitfehlern wird das originale GLB unverändert kopiert. Fehler vor erfolgreichem Lesen der Konfiguration/Eingabedateien können naturgemäß kein gültiges Ersatzmodell liefern; der Prozess endet mit Fehler.

In der späteren Oberfläche bleibt dies eine Option „Gesichtsdetails verbessern“. Projekt-JSON, Python und Detektoren sind interne Details. Die EXE-Gesamtoberfläche ist weiterhin ein eigenes Arbeitspaket. Fortschritt wird als echte Verarbeitungsstufe gemeldet; es wird keine geschätzte Prozentlaufzeit vorgetäuscht.

## Verarbeitung

1. Eingabemesh, UV-Cache, Texturen und Transformationen prüfen.
2. Frontansicht rendern; Anime-Gesichter und 28 Merkmale lokal auf CPU erkennen.
3. Augenabstand/-richtung automatisch ausrichten, Mundposition separat anpassen.
4. Die Gesichtsfarbe auf mehreren Auflösungsstufen überblenden. Der getestete Poisson-Abgleich dunkelte das Gesicht zu stark ab und ist kein Standardpfad.
5. Sichtbare, ausreichend frontal orientierte Gesichtspixel zurückprojizieren. Außerhalb der Maske bleibt der Atlas pixelgenau erhalten.
6. GLB exportieren, Geometrie/UVs/PBR prüfen und Merkmale im abschließenden Render erneut erkennen. Zu große Abweichung führt zurück zum Original.

Die Zielmerkmale stammen aus der vorhandenen Textur. Sie sind **kein unabhängiger Nachweis korrekter Mesh-Anatomie**. Es werden weder neue Gesichtsteile generiert noch Formfehler repariert.

## Geprüfter Stand

- Zwölf Tests bestanden: gültiger Fall, tatsächlich leeres Bild, tatsächlich zwei Gesichter, NaN, niedrige Detektor-/Augenwerte, abgeschnittene Punkte, unplausible Mundposition, zu kleines Gesicht, transparenter Quellbereich, unsicheres unabhängiges Gesicht und erfolgreiche Ausrichtung eines eingerahmten unabhängigen Anime-Kopfes.
- Der unabhängige Kopf ist ein 2D-Test aus den offiziellen Detektor-Demodaten. Er belegt **keinen zweiten vollständigen 3D-Charakterlauf**. Enge Ausschnitte wurden teils abgelehnt; Grenzwerte wurden nicht zum Bestehen abgesenkt.
- Vollständiger Durchlauf mit unserem Anime-Modell: 33,281 Sekunden inklusive abschließender Erkennung, auf dieser Maschine.
- Wiederholung: Atlas pixelidentisch, GLB-SHA identisch.
- Leere Referenz: ursprüngliches PBR-GLB byteidentisch zurückgegeben.
- Falscher UV-Cache: Fehler erkannt, Exitcode 1, Originalmodell als Rückfall ausgegeben.
- Ausgabe: 278.722 Vertices, 350.034 Dreiecke, 1,70 m, zwei eingebettete 2K-Texturen. Blender 5.2.0 LTS importiert erfolgreich.
- Materialkarten und Faktoren, UVs, Positionen und Normalen erhalten. 9.527 Atlaspixel geändert; außerhalb der Projektionsmaske keine Änderungen.
- Augen-/Mundzentren im finalen Render innerhalb von ca. 0,7–2,3 Pixeln ihrer Zielpositionen (2048px-Render). Das ist eine Konsistenzmessung, kein anatomischer Qualitätswert.

Ergebnis-SHA256: `15704c73f2cf1234ae119547fb77c462f8e7ed386afaaa40f58a7da78b174421`.

## Grenzen und Voraussetzungen

Ein einzelnes, weitgehend frontales Anime-Gesicht, 2K-Farbatlas, ungeriggtes einzelnes Y-up-Mesh und exakt passender Hunyuan-UV-Cache. Rigging/Animationen, mehrere Geometrien und nicht-identische Scene-Transformationen werden abgelehnt. Geometrie und UV-Dichte werden nicht verändert. Haaransatz und Gesichtsrand können weiterhin Übergänge zeigen; insbesondere seitliche Ansichten bleiben von Mesh-Form und verdeckten Referenzbereichen begrenzt. Detektorwerte sind keine kalibrierten Wahrscheinlichkeiten.

Die visuellen Änderungen gegenüber dem bereits guten automatischen Prototyp sind moderat. Der wesentliche 1.0-Fortschritt ist ein wiederholbarer, geprüfter Ablauf mit Materialerhalt und klaren Rückfallregeln. Keine Zusage fehlerfreier Ergebnisse für beliebige Charaktere.

## Abhängigkeiten und Versionen

- [Anime Face Detector](https://github.com/hysts/anime-face-detector), Code `98a9fb480fa04bdd96acbe4d98da191a898267f3`.
- HRNetV2 `9b3435248b26aeb82e2a8578fe9d86d5d57158af`; YOLOv3 `afdd4226a79ae8bb81f334dbcffd34f8cc000c38`. Gewichte werden nur über konkrete lokale Pfade geladen; kein automatischer Download beim Start.
- Bestehendes Python 3.13 für Detektion; `opencv-python-headless 4.12.0.88` liegt separat unter `face_detector_deps`.
- Bestehendes Python-3.10-Hunyuan-Labor mit CUDA-Rasterizer für Render/Bake.
- Vorschau nutzt model-viewer 4.3.1 vom CDN; Verarbeitung ist lokal, die Browserbibliothek noch nicht offline gebündelt.

## Nächste Abnahme

Zweiter vollständiger 3D-Charakter, breitere Stil-/Pose-Stichprobe, geometrisch fundierte Landmarkenprüfung, GUI-Worker-Anbindung und Quest-Messung. Bis dahin optionaler Anime-Modus, nicht verpflichtende Standardkorrektur.

