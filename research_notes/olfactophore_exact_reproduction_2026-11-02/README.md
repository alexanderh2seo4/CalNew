# Exakte Olfaktophor-Reproduktion: Quellenprüfung und fehlende Eingaben

Begonnen: 2. November 2026; Quellenprüfung abgeschlossen: 3. November 2026. Ziel ist ein tatsächlich berechnendes 3D-Modell mit denselben Merkmalen, Ligandenposen und Zahlen wie die Originale, anschließend Inferenz für andere Moleküle. **Dieses Verzeichnis enthält noch kein solches Modell.** Die Herstellung ist derzeit durch fehlende Originalparameter und einen nicht nachgewiesenen ausführbaren Originalworkflow blockiert. Es enthält die geprüften Sollwerte und eine konkrete Eingabeliste, keine erfundenen Modellkoordinaten.

## Was geprüft wurde

- Der vorhandene lokale Export von *Scent and Chemistry*, zweite Auflage, wurde gelesen. Die PDF hat 438 Seiten. Gedruckte Seitenzahl + 22 ergibt die PDF-Seite. Die Marine-Abbildungen auf gedruckt 109–111/PDF 131–133 sowie Muguet auf gedruckt 100/PDF 122 wurden direkt gerendert und visuell geprüft. Die bibliographische Angabe „Second Edition“ und die Verfasser wurden im Export kontrolliert. Dateipfad und SHA-256 stehen in [source_manifest.json](source_manifest.json).
- Das Originalpaper Kraft/Eichenberger 2003 wurde auf S. 3738, Tabelle 1 und Abbildung 3, direkt visuell geprüft. Die Hypothese wird dort ausdrücklich als mit Catalyst erzeugt beschrieben; der Artikel nennt an dieser Stelle keine genaue Version. [Originalarbeit](https://doi.org/10.1002/ejoc.200300174).
- GoodNotes wurde geöffnet, zeigte aber den Anmeldebildschirm. Der vorhandene PDF-Export erlaubt die Quellenprüfung unabhängig davon. Es wurde nicht behauptet, eine eingeloggte Bibliothek gelesen zu haben.

## Was im Buch tatsächlich steht

| Modell | Buchstelle | Belastbare Angaben | Für ein originales Rechenmodell noch offen |
|---|---|---|---|
| Muguet, bifunktional | Abb. 3.26, S. 97/PDF 119; Text S. 96 | Zwei Hydrophobe, Donor-/Akzeptor-Einheit; einzelne Liganden erfüllen drei von vier Merkmalen | Vollständiges Trainingsset, Originalhypothese, Richtungen, Toleranzen, quantitative Gewichte |
| Muguet-Aldehyde, revidiert | Abb. 3.28, S. 100/PDF 122; Text S. 99 | 57 aktive Muguet-Aldehyde, ein Akzeptor, drei Hydrophobe, neun Ausschlussvolumina | Trainingsarchiv, Koordinaten/Radien, quantitative Gleichung, ursprüngliche Einstellungen |
| Marine/Calone, ursprünglich | Abb. 3.33, S. 110/PDF 132; Text S. 109–110 | Drei Akzeptoren und ein aromatischer Ort fixieren den Kern; ein aliphatischer Hydrophob bei 6,3 Å; 3-kcal/mol-Konformerfenster; **drei Ausschlussvolumina von Hand gesetzt** | Vollständige numerische Hypothese, manuelle Koordinaten/Radien, Mapping- und Schwellenfunktion |
| Marine, revidiert | Abb. 3.34, S. 111/PDF 133; Text S. 110–112 | Zwei statt drei Akzeptoren; ein aromatischer Ort; ein Hydrophob bei 7,23 Å; sechs Ausschlussvolumina; Drauf- und Seitenansicht | Vollständige Hypothese, verifizierte Originalversion/Protokoll, erweiterter Trainings- und Konformersatz |
| Birne | Abb. 3.35, S. 112/PDF 134; Text S. 113 | Zwei Akzeptoren, drei hydrophobe Orte, mehrere veröffentlichte Abstände; 3-kcal/mol-Fenster; Catalyst; ein gesetztes Ausschlussvolumen | Eindeutige volle 3D-Geometrie, Dictionary, Originaldaten und quantitative Parameter |
| Sandelholz, Ambergris, Moschus, Galbanum | Abb. 3.36a–d, S. 114/PDF 136 | Modelle und beispielhaft ausgerichtete Liganden, Literaturverweise | Jeweils eigenes Modell-/Trainingsarchiv und quantitative Parameter; keine gemeinsame universelle Hypothese |

Quelle dieser Tabelle: der lokal vorliegende Buchtext, besonders Kapitel 3.9 und 3.10; die relevanten Seiten sind im Manifest bezeichnet. Einige Bildunterschriften des Buchs enthalten offenbar verschobene Literaturziffern: Die Marine-Abbildungen verweisen auf [169]/[171], während der Text und das Literaturverzeichnis die passenden Originalarbeiten unter [188]/[190] aufführen. Für die Herkunft werden Titel und DOI abgeglichen, nicht die Bildnummern allein.

Die ursprüngliche Marine-Arbeit ist Kraft/Eichenberger 2003, DOI [10.1002/ejoc.200300174](https://doi.org/10.1002/ejoc.200300174). Das revidierte Modell wird über Buchreferenz 190 auf *“Vanilla Oceanics”*, Kraft/Popaj/Müller/Schär, *Synthesis* 2010, 3029–3036 zurückgeführt, DOI [10.1055/s-0030-1258142](https://doi.org/10.1055/s-0030-1258142). Der [institutionelle Publikationseintrag](https://pure.johnshopkins.edu/en/publications/vanilla-oceanics-synthesis-and-olfactory-properties-of-1e-7-prop--2/) bestätigt ein verbessertes Olfaktophormodell. Der 2010er Verlagsvolltext und seine vollständigen Originalmodellparameter wurden in dieser Sitzung nicht erhalten.

Die im Buch verwendeten Prozentzahlen zur „predictability“ sind keine nachgewiesenen Erfolgswahrscheinlichkeiten für neue Moleküle. Die erste Arbeit bezeichnet 0,59 als Korrelation. Ebenso sind eine Trainingskorrelation und eine externe Vorhersageleistung unterschiedliche Ergebnisse.

## Wie das Fitting gemacht wird

Für das ursprüngliche Marine-Modell lässt sich aus dem Buch der Ablauf konkreter bestimmen: Die drei Akzeptoren und der aromatische Ort verankern den Kern; die Lage des aliphatischen Hydrophoben wird mit den Liganden und gemessenen Schwellen in Catalyst bestimmt. Es folgt eine **manuelle** Ergänzung der ausgeschlossenen Bereiche. Das Paper beschreibt Auswahl des am besten passenden Konformers innerhalb des Energiefensters und Schätzung der Aktivität aus dem Merkmals-Mapping. Die vollständige numerische Scoring-/Schwellenfunktion ist damit noch nicht spezifiziert.

Die Hersteller unterscheiden zwei Rechenaufgaben: qualitative gemeinsame Merkmale mit **HipHop** und quantitative Aktivitätsmodelle mit **HypoGen**; Refinement kann inaktive Liganden und Ausschlussvolumina nutzen. „3D-Fit berechnen“ und „aus diesem Fit einen Schwellenwert berechnen“ benötigen deshalb unterschiedliche Informationen. Dass Catalyst diese Algorithmen anbietet, belegt nicht automatisch den exakten Algorithmus und sämtliche Einstellungen des 2003er Laufs. Quelle: [BIOVIA, Pharmacophore/Ligand-based Design](https://www.3ds.com/fileadmin/PRODUCTS-SERVICES/BIOVIA/PDF/Pharmacophore-Ligand-based-Design-with-BIOVIA-Discovery-Studio.pdf).

Die Recherche zu Originalversionen, Algorithmen, Datenformaten und aktuell zugänglicher Software steht ergänzend in [exact-reproduction-methods.md](../AlphaFold%20Docking%20und%20Pharmakophore%202026-11-02/exact-reproduction-methods.md).

**Warum der kostenlose Visualizer die Aufgabe nicht allein löst:** Der Hersteller nennt dort unter anderem Darstellung, manuelle Pharmakophore und flexible Überlagerung. Die Ausführung der Discovery-Studio-/Pipeline-Pilot-Protokolle wird davon getrennt als Fähigkeit der lizenzierten Umgebung beschrieben. Ein sichtbares oder editierbares 3D-Modell beweist daher noch keinen verfügbaren HypoGen-/Search3D-Rechenworkflow. Quelle: [Herstellervergleich](https://www.3ds.com/fileadmin/PRODUCTS-SERVICES/BIOVIA/PDF/discovery-studio-visualizer.pdf).

## Was konkret benötigt wird

Für die **Wiederverwendung derselben trainierten Hypothese** braucht es ein vollständiges natives Modellprojekt oder einen gleichwertigen numerischen Export: sämtliche Feature-Koordinaten, Radien, Richtungen, erforderliche/optionale Zuordnungen, Ausschlussvolumina und quantitative Modellparameter. Ein Discovery-Studio-Export kann etwa `.chm` verwenden; der genaue Format- und Versionskontext muss aus der Herkunft hervorgehen. Das Hypothesenfile allein muss nicht sämtliche Konformer, Protokolle und Aktivitätsskalierung enthalten.

Für die **Wiederholung der ursprünglichen Modellherstellung** kommen der Original-Trainingssatz einschließlich Stereochemie und Schwellen, alle Konformer oder ihre vollständig reproduzierbaren Erzeugungseinstellungen, Feature-Definitionen, Optimierungseinstellungen, Seeds und manuellen Eingriffe hinzu. Die exakte ursprüngliche Softwareversion ist derzeit insbesondere für 2003 noch offen.

Für das **gleiche Bild** braucht es anschließend die ausgerechneten/alignten Liganden und die ursprüngliche Szene: Kamera, Projektion, Farben, Transparenz, Drahtgitter, Darstellungsradien und Beschriftung. Diese Einstellungen werden nach der numerischen Übereinstimmung angepasst. Änderungen an Modellkoordinaten nur für eine schönere Grafik wären wissenschaftlich keine Reproduktion.

Für **Vorhersagen neuer Moleküle** muss der ausführbare Workflow tatsächlich neue 3D-Konformere erzeugen, diese gegen die vollständige Hypothese fitten, Ausschlussvolumina prüfen und die originale quantitative Funktion anwenden. Zurückzugeben sind mindestens Molekülidentität, gewählter Konformer, ausgerichtete Koordinaten, Feature-Zuordnung, Fit, Ausschlussverletzungen und gegebenenfalls der daraus berechnete Schwellenwert samt Einheit. Ohne quantitative Funktion bleibt das Ergebnis ein geometrischer Score.

Die prüfbare Liste mit Status steht in [required_inputs.json](required_inputs.json). Keine der fehlenden Zahlen wurde aus Pixelpositionen geschätzt oder durch nachträgliches Fitting an die publizierten *berechneten* Werte ersetzt.

## Vorbereitete Original-Sollwerte

- [calone_2003_reference.csv](calone_2003_reference.csv): 20 Zeilen aus Originaltabelle 1; gemessene Schwellen und **publizierte berechnete** Schwellen sind separate Spalten. Die R-Gruppen sind als gedruckte Strukturbezeichnungen transkribiert. Es sind keine unabhängig verifizierten SMILES und keine fertigen 3D-Liganden enthalten. Die letzten drei Zeilen gehören zum im Tabellenkopf getrennt dargestellten Indenon-Gerüst. Wiederkehrende Referenznummern sind durch eindeutige Zeilen-IDs getrennt.
- [book_marine_reference.csv](book_marine_reference.csv): neun Verbindungen auf Buchseite 109, darunter sechs mit Zahlen für ursprüngliches und revidiertes Modell und ein weiterer, laut Buch nicht im Trainingssatz enthaltener Prüfstoff. Leere Felder bedeuten „an dieser Stelle nicht publiziert“ und ausdrücklich nicht Null.
- [source_manifest.json](source_manifest.json): Quelldateien, SHA-256 und Seitenzuordnung. Die Buchdatei wurde nicht in den Projektordner dupliziert oder hochgeladen.

Diese Spalten sind **Referenzausgaben zur Reproduktionsprüfung**, keine neuen Vorhersagen und kein Ersatz für die Originalhypothese. Übereinstimmung mit gerundeten Tabellenwerten ist notwendig, aber beweist allein keine identischen Koordinaten oder eine brauchbare externe Generalisierung. Die Daten wurden anhand der gerenderten Quellseiten geprüft; es wurden keine neuen chemischen Fits oder Modelltests ausgeführt.

## Entscheidung für den nächsten Rechenschritt

Ein nachweisbar lizenziertes Programm **plus** ein vollständiger Originalmodell-/Protokollexport ermöglicht den strengen Wiederholungslauf. Bei vorhandenem Programm, aber fehlendem Originalexport lässt sich ein neues quantitatives 3D-Modell aus experimentellen Schwellen trainieren; es wäre als unabhängiges Modell zu kennzeichnen und könnte von den publizierten Bildern abweichen. Bei vorhandenem Export mit vollständig dokumentiertem Score ist auch eine überprüfte alternative Implementierung denkbar. Diese drei Wege dürfen nicht als dasselbe Ergebnis dargestellt werden.

**Aktuelles Ergebnis:** Die Quellenlage und Sollwerte sind konkretisiert. Ein identisches, vorhersagefähiges 3D-Modell ist noch nicht hergestellt. Der nächste abhängige Schritt benötigt den fehlenden Originalexport und/oder die Entscheidung für ein unabhängig neu trainiertes Modell mit einem verfügbaren Rechenworkflow. Eine bloße Nachzeichnung wird hier nicht als Ersatz geliefert.
