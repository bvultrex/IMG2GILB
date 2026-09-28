# IMG2GILB Studio – lokaler Entwicklungsstand

Die Windows-EXE startet eine lokale Oberfläche und verwendet die bestehende
ComfyUI-/Hunyuan-Lab-Installation. Beim Start werden keine Pakete installiert.
Dieser Stand ist kein eigenständiger Installer für einen neuen PC.

## Benutzung

1. `IMG2GILB.exe` starten; vorhandenen lokalen Dienst wiederverwenden.
2. Frontbild wählen, optional Rücken und beide Seiten hinzufügen.
3. Qualitätsprofil, Ziel-Dreiecke, reale Höhe und Texturauflösung einstellen.
4. „Modell erstellen“ starten. Nach Abschluss das Modell drehen und als GLB
   oder zusammen mit Referenzbildern und Einstellungen als Projekt-ZIP speichern.

Die Form verwendet alle zugeordneten Ansichten. Paint wird derzeit vom
Frontbild geführt; zusätzliche Ansichten garantieren keine originalgetreue
Rückseitentextur. Anime Face 1.0 verbessert nur ausreichend sicher erkannte
Frontalgesichter. Bei unsicherer Erkennung bleibt die Originaltextur erhalten.
Rigging ist sichtbar deaktiviert und noch nicht implementiert.

## Laufzeit und Entwicklung

`runtime.json` beschreibt vorhandene Python-, Modell-, ComfyUI- und Face-Pfade.
Die Konfiguration ist lokal und wird nicht versioniert. Port 8190 ist nur an
Loopback gebunden. Modellgewichte und Eingabebilder werden nicht mitgeliefert.
`server.py` nutzt die Python-Standardbibliothek und Pillow aus der bestehenden
Lab-Umgebung. `pipeline.py` steuert Stufen in separaten Prozessen; Zwischenstände
werden vor Wiederverwendung anhand von SHA-256-Prüfsummen geprüft.

Der Launcher lässt sich mit dem vorhandenen Windows-.NET-Framework-Compiler
erstellen: Ziel `winexe`, Referenzen `System.Windows.Forms.dll` und
`System.Web.Extensions.dll`, Quelldatei `Launcher.cs`.

`python test_contracts.py` prüft veränderte Cache-Dateien, Prozessbaum-Lebensdauer
und Fehlerzustände. Ein fertiges Projekt kann unabhängig in Blender geprüft
werden: `blender --background --python validate_blender.py -- <Projektordner>`.
Dieser Test kontrolliert Import, eingebettete Texturen, Dreiecke und reale Höhe.

## Bisherige reale Tests (28.09.2026)

- Stuhl, ein Bild: vollständig erzeugt; 7.998 Dreiecke, 40 cm, zwei 1K-Texturen;
  Blender 5.2 importiert erfolgreich.
- Bekleideter Anime-Charakter, vier Bilder: vollständig erzeugt; 8.000 Dreiecke,
  40 cm, zwei 1K-Texturen; Blender-Import erfolgreich. Face-Korrektur konservativ
  übersprungen, weil das generierte Gesicht nicht sicher erkannt wurde.
- Beide Projekte liefen nacheinander im selben Dienst ohne Neuinstallation.
- Detaillierter Charaktervergleich mit 100.000 Ziel-Dreiecken/2K läuft noch.

Nicht als fertig abgenommen: Rigging, Quest-Hardwareleistung, Einrichtung auf
einem neuen PC und allgemeine Gesichtskorrektur bei beliebigen Charakteren.

Qualitätsvergleich abgeschlossen: 99.996 Dreiecke, 64.540 Vertices, 170 cm, 2K-PBR-Texturen. Gesichtskorrektur verarbeitet; Blender-Import und UI-Downloads geprüft. Neues helles Studio-Design auf Port 8190 aktiv. Der bestehende Dienst wurde nicht neu gestartet; ProcessGuard-Änderungen auf Disk benötigen noch eine Dienst-Abnahme.


## 2026-09-28 - Lokale Studio-Entwuerfe
Referenzbilder werden jetzt als Blobs im browserlokalen IndexedDB gespeichert, zusammen mit Qualitaet, Dreiecken, Modellhoehe, Texturaufloesung und Schaltern. Kein externer Upload und kein Hintergrundjob beim Wiederherstellen. Bilder zuruecksetzen entfernt die Entwurfsreferenzen; bestehende Projekte/Originaldateien bleiben erhalten.
Browserpruefung bestanden: Frontbild speichern und nach Reload wiederherstellen; 175 cm/1K nach Reload erhalten; Zuruecksetzen nach Reload erhalten; anschliessend alle vier Originalansichten des gelben Charakters mit 170 cm/2K wiederhergestellt. Keine Konsolenfehler beobachtet. Screenshot: D:/SF3D_QualityLab/male_anime_validation/studio-persistent-draft.png.
Grenze: Entwurf gilt fuer denselben Browser und dieselbe lokale Adresse. Das ist kein Ersatz fuer den Projektexport. Ein erneuter vollstaendiger Generierungslauf wurde in diesem Paket nicht gestartet. Rigging und Aktivierung der Dienstreparatur bleiben offen.
