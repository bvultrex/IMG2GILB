# IMG2GILB: einfache Bedienung

Verbindlicher Nutzerwunsch, 28.09.2026. Zielbild; noch keine fertig implementierte Anwendung.

## Normaler Ablauf

1. Eine Windows-EXE starten. Oberfläche öffnet sich; benötigte Dienste starten verborgen und werden auf Bereitschaft geprüft. Bereits laufende passende Dienste wiederverwenden.
2. Ein Bild oder mehrere benannte Ansichten hochladen. Vorschau mit Front/Rücken/Links/Rechts-Zuordnung; fehlende Ansichten sind erlaubt, sofern das gewählte interne Verfahren sie unterstützt.
3. Wenige Einstellungen: Qualitätsprofil, Ziel-Dreieckszahl, Texturierung an/aus und Auflösung, Rigging an/aus, reale Höhe mit Einheit. Dreiecke und exportierte Vertices nicht gleichsetzen; tatsächliche Werte im Ergebnis zeigen.
4. Ein eindeutiger Button „Modell erstellen“. Upload allein startet keine kostspielige Verarbeitung.
5. Fortschritt mit Stufen: Bildvorbereitung, Geometrie, Optimierung, Texturen, optional Rigging, Export. Prozentwerte nur bei messbarem Fortschritt; andernfalls laufende Stufe und vergangene Zeit. Abbrechen unterstützen.
6. Dreh-/zoombare 3D-Vorschau mit Farbe/PBR-Umschaltung, Größe und Modellstatistik. GLB speichern, optional Projekt mit Einstellungen speichern. Zweites Bild ohne Neustart verarbeiten.

## Hintergrund und Fehlerbehandlung

- Modellwahl, Python, Ports, CUDA, UV-Bake und Hilfsskripte sind interne Details; technische Ansicht bleibt optional.
- Erstmalige Einrichtung und Downloads gesondert anzeigen. Keine wiederholte Installation beim normalen Start.
- Fehlermeldung nennt betroffene Stufe und bietet Wiederholen sowie Diagnosepaket; erfolgreiche Zwischenstände erhalten.
- GPU-Aufgaben sequenziell ausführen, Dienste nicht mehrfach starten, Speicher nach Stufen freigeben.
- Lokaler Upload bedeutet lokale Verarbeitung. Cloud-Dienste erfordern eine erkennbare separate Auswahl.
- Rigging-Schalter erst aktivieren, wenn ein tatsächlich integrierter Weg funktioniert. Bestehender manueller Mixamo-Test ist noch keine automatische lokale Rigging-Funktion.
- Anime-Gesichtsverbesserung als internes Profil testen; keine zusätzliche Sammlung technischer Regler im Hauptablauf.

## Abnahme

Start per EXE auf bestehendem Shadow-PC, zwei aufeinanderfolgende Projekte ohne Terminal, Einzelbild und Mehransichten, Abbruch/Wiederholung, korrekt skaliertes GLB mit eingebetteten Texturen, funktionsfähiger Exportdialog. Quest-Leistung getrennt auf echter Hardware prüfen.

