# Face Refining 1.0.1 - 28.09.2026

Lokaler Patch fuer das vorhandene IMG2GILB/Hunyuan-Labor. Keine Neuinstallation und keine neuen Gewichte erforderlich.

## Aenderungen
- Augenweiss und Brauenfarben werden im Mehrband-Blending gezielt erhalten.
- Die Gesichtsmaske umfasst die gesamte Braue. Die Rueckprojektion entfernt kleine Augendetails nicht mehr durch die bisherige Kanten-Erosion.
- Farbige Haarstraehnen werden anhand einer lokal beobachteten Haarpalette geschuetzt. Dies ist eine begrenzte Heuristik, keine allgemeine Haarsegmentierung.
- Eine einzelne unsichere Erkennung kann mit Kontextausschnitt erneut geprueft werden. Nur raeumlich konsistente, ausreichend starke Ergebnisse werden angenommen.
- Geometrie, UVs, PBR-Material und Atlas ausserhalb der Gesichtsmaske bleiben erhalten. Unsichere Faelle behalten das Original.

## Nachweise
21 CPU-Tests bestanden. Vollstaendige Face-Laeufe mit zwei bestehenden Anime-Meshes bestanden; dies sind keine zwei neuen Geometriegenerierungen.
Gelber Charakter: 99.996 Dreiecke, 64.540 Vertices, 170 cm, zwei eingebettete 2K-Karten. Blender 5.2 importiert den finalisierten Studio-Export erfolgreich.
Mittlerer absoluter RGB-Fehler an 439 ausgerichteten hellen Augenpixeln: 0.159823 -> 0.031626. Die Messung beurteilt diese Pixel, nicht die Gesamtqualitaet.
Augen-/Mundzentren im abschliessenden 2048px-Render: 0.410 / 0.583 / 0.594 px Abweichung von den Zielzentren.

## Ergebnis
Studio-Projekt: 34d5260d03fe47f196324946addb3ebf.
Gesichts-GLB vor Studio-Skalierung: SHA256 5c5c7a7edc0e347205238fc3e260b5cc490b67319b178895fc0769d3d4c54424.
Die Dateien liegen unter D:/SF3D_QualityLab/male_anime_validation/face_palette_guard.

## Anwendung
Das aktive lokale face_v1-Verzeichnis enthaelt bereits diesen Stand. Bestehende Startskripte und runtime.json bleiben verwendbar. Kein Installerlauf noetig.
Das ZIP ist eine Sicherung des Codes samt lokalem Projektbeispiel; Tests verwenden vorhandene Labor-Testdaten. Es ist kein portabler Gesamtinstaller.
Der Studio-Dienst muss fuer die vorbereiteten Pipeline-/Statusschreibreparaturen noch neu gestartet werden. Die neu erzeugten Ergebnisse sind bereits im laufenden Studio sichtbar.

## Grenzen
Nur weitgehend frontale, einzelne Anime-Gesichter. Zielmerkmale stammen aus der Textur, nicht aus unabhaengig gemessener 3D-Anatomie. Haaransatz, Nase und Seitenansichten koennen Artefakte behalten. Kein Rigging und keine Geometriekorrektur.
Front-/Rueckenprojektion der Kleidung ist separat experimentell: Logo klarer, aber Seiten-Doppelkonturen. Nicht in den Standardablauf integriert.
