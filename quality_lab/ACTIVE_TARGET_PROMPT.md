# Aktiver Zielprompt: sichtbarer Texturgewinn bis zum finalen GLB

Gesamtziel bleibt: automatisch erzeugte Modelle und Texturen in Meshy-Qualität oder besser, einfache Oberfläche, wiederholbare Bild-/Mehransichten-Verarbeitung, Preview, Export und optionales Rigging. Dieses Ziel ist nicht erreicht.

Nächster zusammenhängender Lieferblock: Erzeuge für den vollständig bekleideten Ranger eine sichtbar bessere Textur auf unveränderter vorhandener Geometrie und UVs. Liefere ein ladbares GLB und gleich gerenderte Vorher-/Nachher-Bilder. Keine neue Installation, kein Training, keine parallelen GPU-Jobs, keine Änderung der Produktionsdefaults.

Erster Kandidat: tatsächlich generierte Paint-Ansichten von768 auf1024Pixel erhöhen. Sechs Kameras, identische Referenz, Seed und übrige Samplingparameter beibehalten. Das ist eine zu prüfende Hypothese, kein garantierter Gewinn. Der2K-Atlas bleibt konstant. Neue Dateien in eigenem Verzeichnis. Vorhandene Kontrollbilder und UVs werden bewusst als feste Versuchsbedingungen wiederverwendet; der Lauf ist kein frischer End-to-end-Abnahmetest.

Abnahme: Gesicht/Augen/Mund, Gürtel-/Kleidungsdetails und Schrägansichten auf Schärfe UND Referenztreue prüfen. Keine neuen Doppelkonturen oder stärkeren Nähte. Geometrie/UV und nicht bearbeitete Materialkanäle erhalten. GLB unabhängig laden und embedded Textur prüfen. Vergleich mit bestehendem generativen Baseline-GLB; bisherige Hybrid-Ausgabe zusätzlich getrennt kennzeichnen.

Wenn der Kandidat scheitert oder visuell nichts bringt: Ursache am frühesten verlustbehafteten Stadium bestimmen und genau eine begründete Korrektur durchführen. Keine ungerichtete Parameterreihe. Kein Erfolg allein wegen Polygonzahl, Auflösung oder bestandener Imports melden. Nach sichtbarem Gewinn Integration und zweites Motiv prüfen; bisherige Produktionsgates bleiben verbindlich.
