---
date: 2026-11-02
type: research
status: literature-and-project-review
---

# AlphaFold, Docking und Pharmakophore für CALNEW

> **Nachprüfung mit dem Buch, abgeschlossen 2026-11-03:** Der vorhandene Export von *Scent and Chemistry*, 2. Auflage, wurde inzwischen direkt geprüft. Er beschreibt die manuelle Platzierung der Ausschlussvolumina und ordnet das revidierte Marine-Modell *Vanilla Oceanics* (2010, DOI 10.1055/s-0030-1258142) zu. Vollständige Originalhypothesen und die quantitative Modellfunktion fehlen weiterhin. Buchstellen, Original-Sollwerte und konkrete Reproduktionsvoraussetzungen stehen im [neuen Reproduktionsdossier](../research_notes/olfactophore_exact_reproduction_2026-11-02/README.md).

**Empfehlung:** CALNEW sollte zuerst ligandbasierte 3D-Pharmakophore und Formähnlichkeit als zusätzliche Merkmale evaluieren. Ein kleiner, rezeptorspezifischer Docking-Vergleich ist danach sinnvoll. AlphaFold kann die strukturelle Grundlage dafür liefern; eine zuverlässige Vorhersage menschlicher Geruchsschwellen folgt daraus noch nicht. Das ist eine aus der Literatur und dem Projektstand abgeleitete Priorisierung, kein bereits gemessener Modellgewinn.

Mit dem genannten Calone-Paper ist hier vermutlich Riad et al. (2021), *Occurrence of Marine Ingredients in Fragrance*, gemeint: Es ist in den Projektnotizen und eurer Korrespondenz ausdrücklich mit dem Calone-1951-Modell verknüpft. Zusätzlich wurde der bereits im Vault besprochene Lu-Preprint von 2026 berücksichtigt.

## 1. Was im Projekt tatsächlich vorhanden ist

Die Hauptpipeline erzeugt im Block `pharmacophore` **2D-Gobbi-Merkmale, gefaltet auf 1.024 Zählwerte**. Diese beschreiben chemische Merkmale und topologische Abstände. Sie enthalten keine explizite 3D-Geometrie eines Calone- oder Muguet-Modells. Daneben gibt es Konformergenerierung und einen optionalen Uni-Mol2-Zweig: CALNEW beginnt bei 3D also nicht bei null. Quellen: [blocks.py](../src/calnew/pipeline/blocks.py), [conformers.py](../src/calnew/conformers.py), [Projektarchitektur](../CALNEW%20Project%20Architecture%20and%20Performance.md).

Der separate **Olfr73-Prototyp** richtet Konformere bekannter Liganden aus und berechnet sechs gemeinsame Merkmalspositionen. Er verwendet weder einen Rezeptor noch Docking. Im gespeicherten 25er-Testpanel erreicht er ROC-AUC 0,691 mit breitem Bootstrap-Intervall von etwa 0,471–0,890; die Korrelation des Fits mit pEC50 ist schwach. Das Panel war bereits vom Originalpaper vorausgewählt. Damit ist der Prototyp eine vorhandene technische Basis für 3D-Matching, aber noch kein belastbarer Potenzprädiktor und kein Nachweis für menschliche Geruchsqualität. Quelle: [Methodik und Grenzen des lokalen Modells](../research_notes/olfactory_pharmacophore_2026-10-09/local_model/README.md).

**Konsequenz für eine Verbesserung:** Ein neuer Zweig muss Zusatznutzen gegenüber Fingerprints, den vorhandenen Strukturblöcken und Uni-Mol2 zeigen. Ein Vergleich ausschließlich mit einem schwachen 2D-Basismodell würde die Projektfrage nicht beantworten.

## 2. Wie die Pharmakophor-Abbildungen in Papers entstehen

Ein Pharmakophor ist eine abstrahierte räumliche Anordnung von Wechselwirkungsmerkmalen: beispielsweise Wasserstoffbrückenakzeptor, Donor, aromatisches Zentrum und hydrophober Bereich. Im Duftstoffkontext wird häufig von **Olfaktophoren** gesprochen. Es gibt zwei grundlegende Wege:

| Weg | Ausgangspunkt | Entstehung der Merkmalspositionen |
|---|---|---|
| Ligandbasiert | Moleküle mit gemeinsamem experimentellem Endpunkt | Konformere ausrichten; gemeinsame chemische Merkmale identifizieren |
| Strukturbasiert | Protein-Ligand-Komplex oder modellierte Bindetasche | Merkmale aus Kontakten und räumlichen Beschränkungen der Tasche ableiten |

Die ligandbasierte Variante benötigt keine bekannte Rezeptorstruktur. Eine didaktisch nachvollziehbare Implementierung mit Merkmalsextraktion und Clustering liefert [TeachOpenCADD T009](https://projects.volkamerlab.org/teachopencadd/talktorials/T009_compound_ensemble_pharmacophores.html). Für den strukturbasierten Weg beschreibt die ursprüngliche [LigandScout-Arbeit](https://doi.org/10.1021/ci049885e) die Ableitung von Merkmalen und Volumenbeschränkungen aus Protein-Ligand-Komplexen.

Ein sinnvoller ligandbasierter Arbeitsablauf ist:

1. **Endpunkt festlegen:** gleicher Geruchseindruck, ähnliche menschliche Luftschwelle oder Aktivierung desselben Rezeptors sind verschiedene Aufgaben.
2. **Moleküle und Messungen kuratieren:** Struktur, Stereochemie, Reinheit, Messmedium, Protokoll sowie gemessene Nichtantworten erfassen. Ein fehlendes Label ist kein experimenteller Negativbefund.
3. **Konformere erzeugen:** mehrere plausible räumliche Zustände pro Molekül; Protonierung und Tautomere berücksichtigen, soweit relevant.
4. **Merkmale zuweisen und ausrichten:** passende Akzeptoren, Donoren, hydrophobe und aromatische Zentren zwischen Molekülen überlagern. Verschiedene Alignments als konkurrierende Hypothesen behandeln.
5. **Hypothesen auswählen:** Positionen, Toleranzradien, Richtungsvektoren, verpflichtende oder optionale Merkmale und gegebenenfalls ausgeschlossene Volumina bestimmen.
6. **Fit und Vorhersage trennen:** geometrischen Fit zunächst als Merkmal betrachten. Eine quantitative Schwellenvorhersage braucht zusätzlich eine mit Schwellenwerten trainierte und extern geprüfte Beziehung.
7. **Erst danach visualisieren:** Molekülüberlagerungen, farbige Kugeln, Vektoren und ausgeschlossene Bereiche darstellen. Die Grafik zeigt das Modell; ihre Anschaulichkeit validiert es nicht.

Das ist eine methodische Synthese für CALNEW. Der originale **PHASE**-Algorithmus sucht gemeinsame Merkmalsanordnungen über Ligandkonformere und prüft Hypothesen unter anderem an Testliganden und Screening-Aufgaben. Die heutige Software kann auch ligand- und strukturbezogene Hypothesen verbinden. Quellen: [Dixon et al. 2006](https://doi.org/10.1111/j.1747-0285.2006.00384.x), [offizielle Phase-Beschreibung](https://www.schrodinger.com/platform/products/phase/).

Die Kugeln sind dabei abstrahierte Merkmalsregionen mit Modell-Toleranzen. Sie sind keine direkt gemessenen Elektronenwolken. Auch die Bezeichnung einer Merkmalsregion als „binding site“ in einer ligandbasierten Darstellung beweist keinen Kontakt zu einem identifizierten Rezeptor.

## 3. Was sich beim Calone-Modell konkret belegen lässt

### Review von 2021: nachvollziehbare Herkunftslücke

Riad et al. nennen **Phase 3.4** und zeigen in Abbildung 3 vier strukturelle Elemente: hydrophobe Gruppe, aromatischen Ring, Siebenring als Abstandshalter und Carbonylgruppe. Die Abbildung ist eine schematische Struktur mit Markierungen, keine vollständige exportierte 3D-Hypothese. Der Verweis auf ein revidiertes Marine-Modell führt zu Referenz 203, einer Arbeit über Rosen-Duftstoffe. Das lässt die genaue Herkunft offen. Quelle: [Review, S. 1446–1447 und Literaturverzeichnis](https://doi.org/10.3390/chemistry3040103).


### Originalarbeit von 2003: mehr reproduzierbare Information als bisher erfasst

Kraft und Eichenberger bauten ein **Catalyst-Modell aus gemessenen Geruchsschwellen** auf. Sie beschreiben Akzeptoren, ein aromatisches und ein aliphatisches Zentrum sowie ausgeschlossene Volumina; das Konformerfenster beträgt 3 kcal/mol. **Abbildung 3 auf S. 3738 enthält mehrere Distanzangaben**, darunter die im Abstract genannten 6,3 Å zwischen aromatischem Zentrum und aliphatischem Hydrophob. Tabelle 1 stellt experimentelle und berechnete Schwellen gegenüber. Die berichtete Korrelation beträgt 0,59; Calone selbst ist ein deutlicher Ausreißer: 0,031 gegenüber berechneten 0,53 ng/L Luft. Die Schwellen stammen aus GC-Olfaktometrie. Quelle: [Originalarbeit, DOI](https://doi.org/10.1002/ejoc.200300174); lokal gesicherte, visuell geprüfte PDF-Kopie (local artifact omitted from the public snapshot).

**Eigene Bewertung:** Eine teilweise Rekonstruktion ist damit realistischer als im bisherigen Report dargestellt. Ein Distanzschema ersetzt jedoch keine vollständigen 3D-Koordinaten, Richtungsvektoren, Toleranzen und ursprünglichen Softwareparameter. Eine neue Implementierung wäre deshalb als Rekonstruktion mit offengelegten Annahmen zu kennzeichnen. GC-O-Schwellen sollten außerdem beim Zusammenführen mit CALNEW-Messdaten ihre Protokollkennung behalten.

### Gut dokumentierter Vergleich: Rosen-Nitrile

Hauser, Kraft und Carreira beschreiben ein Modell in **Discovery Studio 18.1** mit zwölf Trainingsmolekülen: ein Akzeptor, zwei hydrophobe Bereiche und ein Doppelbindungsmerkmal. Trainingsdaten und berechnete Aktivitäten werden gegenübergestellt; das Konformerfenster beträgt 20 kcal/mol. Die Korrelation von 77,1 % ist keine externe Validierung. Die Autoren nennen die Darstellung vor allem illustrativ; ausgeschlossene Volumina verbesserten den Fit nicht. Das zeigt gut, welche Rolle Modellierung und welche Rolle nachträgliche Interpretation spielen. Quelle: [CHIMIA 2020, Originalarbeit im ETH-Repositorium](https://www.research-collection.ethz.ch/bitstreams/c7cec7da-db9a-44c3-97be-857bcd300ab8/download); vorhandene lokale Quelle (local artifact omitted from the public snapshot).

## 4. Wo AlphaFold und Docking helfen können

AlphaFold2 liefert Proteinstrukturen; AlphaFold3 kann auch Protein-Ligand-Komplexe vorhersagen. Klassisches Docking sucht Ligandenposen in einer vorbereiteten Rezeptorstruktur. Für CALNEW sind folgende Anwendungen sinnvoll zu prüfen:

| Anwendung | Möglicher Projektgewinn | Was noch gemessen werden muss |
|---|---|---|
| Rezeptortasche modellieren | Auswahl plausibler Kontakte, Volumengrenzen und Ligandenposen | Kontakt- und Aktivierungshypothesen |
| Strukturbasiertes Pharmakophor ableiten | Ligandbasiertes Modell um Taschengeometrie ergänzen | Zusatznutzen gegenüber ligandbasiertem Fit |
| Mehrere Posen/Strukturen auswerten | Merkmale zu Kontaktmustern, Konflikten und Stabilität der Vorhersage | Robustheit gegen Struktur- und Seedwahl |
| Rezeptoraktivität zusätzlich lernen | Experimentelle OR-Daten als zusätzliche Supervision | Generalisierung auf neue Moleküle und später menschliche Sensorik |
| Kandidaten für Experimente priorisieren | Informativere Auswahl aus einer kleineren Kandidatenliste | Prospektive Trefferquote gegenüber einfacher Ähnlichkeit |

Die evidenzbasierte Toolauswahl, neue Rezeptorstrukturen, aktuelle Lizenzen und ein genauer Docking-Pilot stehen im [begleitenden Recherchebericht](../research_notes/AlphaFold%20Docking%20und%20Pharmakophore%202026-11-02/receptor_docking.md). Dort werden AlphaFold2/3, Vina, GNINA, DiffDock und Boltz-2 getrennt eingeordnet.

Die zentrale biologische Einschränkung ist die Kette **Bindepose → Bindung → Aktivierung → Rezeptorprofil → menschlicher Eindruck bei einer Dosis**. Ein guter Score an einem Glied ersetzt die übrigen Messungen nicht. Insbesondere sind Strukturkonfidenz und Docking-Scores keine Aktivierungswahrscheinlichkeiten und keine direkt berechenbaren Luftschwellen.

Ein passender Präzedenzfall für strukturelle Merkmale ist der **Lu-Preprint von 2026**: Er verbindet AlphaFold3-Rezeptormodelle mit Sequenzmerkmalen und experimenteller Aktivierung. Sein Status bleibt Preprint; für CALNEW sind insbesondere die Grenzen der Rezeptor- gegenüber der Molekülgeneralisation relevant. Quelle: [Lu et al., PubMed und Preprint-Status](https://pubmed.ncbi.nlm.nih.gov/42326533/).

## 5. Welche Literatur einen Modellgewinn tatsächlich stützt

**3D-Form und Pharmakophore:** Ihara et al. untersuchten 23 Eugenol-/Vanillin-verwandte Duftstoffe. Ihre Strukturmerkmale wurden mit MOE, OMEGA und ROCS aus Konformer-Ensembles erzeugt: kontinuierliche Ähnlichkeiten zu Referenzmolekülen, keine einzelne universelle Kugel-Hypothese. Für sensorische Ähnlichkeit berichten sie in wiederholter Kreuzvalidierung R² = 0,514 ± 0,078; ein Modell mit gemessenen Rezeptorprofilen erreicht 0,687 ± 0,059. Die Unsicherheitsangaben sind als Standardfehler ausgewiesen. Die Aufgabe ist eng begrenzt und betrifft weder allgemeine Geruchsqualität noch Luftschwellen. Quelle: [Ihara et al. 2025](https://academic.oup.com/chemse/article/doi/10.1093/chemse/bjaf002/7994243).

**Rezeptoren und menschliche Schwellen:** Emter et al. verknüpfen OR5A2-Aktivierung, Genotyp und menschliche Moschuswahrnehmung. Eine Variante reduziert Rezeptorempfindlichkeit etwa 50-fach; homozygote Träger zeigen für selektive Liganden etwa 40–60-fach höhere sensorische Schwellen. Das stützt den Nutzen rezeptorspezifischer Messungen in passenden Stoffklassen. Es validiert keine allgemeine Umrechnung von Docking-Scores in Schwellen. Quelle: [Emter et al. 2024](https://academic.oup.com/chemse/article/doi/10.1093/chemse/bjae015/7642668).

**Eigene Schlussfolgerung:** Der aussichtsreiche Hebel ist zusätzliche, passende biologische oder geometrische Information. Eine aufwendigere Simulation ohne passende Trainings- und Prüfdaten ist für sich noch keine Modellverbesserung.

## 6. Konkreter Vorschlag für CALNEW

Die folgenden Schritte sind ein vorgeschlagener Versuchsplan; sie wurden in dieser Recherche nicht gerechnet.

### A. Zuerst einen kleinen 3D-Zweig evaluieren

Als direkten Anknüpfungspunkt den Olfr73-Prototyp methodisch verbessern; als projektbezogene Duftstofffamilie Marine/Calone und die Abgrenzung zu Muguet kuratieren. Diese Aufgaben getrennt halten: Mausrezeptoraktivierung und menschliche Duftqualität sind unterschiedliche Labels.

Pro Molekül könnten wenige nachvollziehbare Merkmale entstehen: bester Pharmakophor-Fit, Formähnlichkeit zu Trainingsreferenzen, Anteil gut passender Konformere, relative Energie des passenden Konformers innerhalb desselben Moleküls, fehlende Merkmale, Verletzungen ausgeschlossener Volumina und Streuung über alternative Hypothesen. Energie-Unterschiede sind zunächst Kraftfeldmerkmale, keine gemessenen Bindungsenergien.

Ein einzelnes Alignment nicht als gegeben behandeln: mehrere Referenzen und Hypothesen vergleichen. Unterstützung eines Merkmals nach unabhängigen Molekülen zählen, damit ein flexibles Molekül mit vielen Konformeren das Modell nicht dominiert. Fehlende Berechenbarkeit explizit markieren.

Für einen ersten offenen Workflow reichen die bereits verwendete RDKit-Basis und bei Bedarf CDPKit: RDKit stellt explizite Pharmakophore mit Punkten/Radien und Abstandsgrenzen bereit; CDPKit bietet Konformer, Pharmakophorverarbeitung, Matching und Export. Quellen: [RDKit Pharm3D](https://www.rdkit.org/docs/source/rdkit.Chem.Pharm3D.html), [CDPKit-Tutorial](https://cdpkit.org/cdpl_python_tutorial/cdpl_python_tutorial.html).

### B. Danach ein begrenzter Rezeptorvergleich

Zunächst ein bis drei Rezeptoren mit passenden experimentellen Liganden und expliziten Nichtantworten auswählen. Vina als nachvollziehbare Referenz und GNINA als alternative Bewertung vergleichen. AlphaFold3 oder Boltz-2 zunächst nur für ausgewählte Ligand-Rezeptor-Paare einsetzen. Den vorhandenen Olfr73-Datensatz als technischen Anschluss nutzen; für Aussagen zu menschlicher Wahrnehmung einen separaten menschlichen Rezeptor-/Sensorikdatensatz wählen.

Je nach Datenlage können Kontaktmuster oder Taschenmerkmale nützlicher sein als ein einzelner bester Docking-Score. Vorhersagen über mehrere Proteinmodelle und Seeds vergleichen; Ergebnisse mit hoher Modellabhängigkeit als unsicher behandeln. Erst bei Zusatznutzen über Ligandenähnlichkeit hinaus ausweiten.

### C. Den Gewinn mit denselben Prüfbedingungen messen

Vergleichsarme: **beste bestehende Pipeline**, **+ 3D-Pharmakophor/Form**, **+ Rezeptormerkmale**, **+ beide**. Gleiche Moleküle, gleiche Datenaufteilung und gleiche Zielgrößen verwenden; Berechnungsfehler und fehlende Rezeptordaten ebenfalls auswerten.

Pharmakophore, gelernte Referenzauswahl und Schwellenwerte ausschließlich innerhalb der Trainingsfalten bestimmen. Stereoisomere und nahe Analoga so gruppieren, dass fast identische Moleküle nicht über Train/Test verteilt werden. Für Rezeptortransfer zusätzlich Molekül-Holdout prüfen; ein unbekannter Rezeptor bei bekannten Liganden ist eine andere Aufgabe als ein neues Duftstoffmolekül.

Bei Aktivierung PR-AUC, ROC-AUC und Trefferanreicherung bei festem Experimentbudget berichten; bei Schwellen Fehler in logarithmischen Einheiten; bei Qualität die vorhandenen Projektmetriken sowie Ergebnisse pro Duftfamilie. Konfidenzintervalle über Moleküle/Strukturgruppen berechnen. Die reservierten finalen Projekt-Testdaten während dieser Auswahl unangetastet lassen.

Ein Erfolg wäre ein stabiler Zusatznutzen auf zurückgehaltenen Strukturgruppen oder eine bessere prospektive Kandidatenauswahl. Eine anschaulichere Abbildung oder ein besserer Trainingsfit genügt als Kriterium nicht.

## 7. Korrekturen und offene Punkte

- **Korrektur:** Die Originalarbeit von 2003 nennt Catalyst und veröffentlicht ein Abstandsdiagramm. Die frühere Einschränkung auf die einzige im Abstract sichtbare Distanz war zugangsbedingt und ist überholt.
- **Offen:** vollständige maschinenlesbare Calone-Hypothese und exakte Herkunft der im Review als Phase bezeichneten Darstellung.
- **Offen:** welcher 3D- oder Rezeptorzweig CALNEW messbar verbessert. Literaturergebnisse aus anderen Stofffamilien beantworten das nicht.
- **Offen:** ein für Calone ausreichend belegter Rezeptor als Ziel eines konkreten Docking-Experiments. Die Recherche legt sich ohne passenden Primärnachweis nicht auf einen „Marine-Rezeptor“ fest.

Rechercheumfang: lokale Projektdokumentation, Modellcode, vorhandene Autorenkorrespondenz sowie Originalpublikationen und offizielle Werkzeugdokumentation. Historische Modellmetriken wurden gelesen, nicht neu berechnet. Die Originalabbildung von 2003 wurde zusätzlich direkt im PDF geprüft. Bestehender Modellcode wurde nicht geändert.
