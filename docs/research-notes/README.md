# CALNEW – Forschungsnotizen und nächste Schritte

Stand: 5. November 2026. Anonymisierte Zusammenfassung von Gesprächsnotizen aus Ende Oktober und Anfang November. Die Punkte sind Forschungsfragen und Arbeitsvorschläge; sie belegen keine zugesagte Kooperation, abgeschlossene Untersuchung oder gesicherte Modellleistung. Personen, Kontaktdaten, individuelle Verfügbarkeiten und persönliche Rückmeldungen sind ausgelassen.

## Ziel und Umfang

CALNEW verbindet molekulare Geruchsvorhersage, experimentelle Geruchsmessung und die Untersuchung möglicher Rezeptorbezüge. Rezeptorstruktur, gemessene Zellantwort, menschliche Geruchsschwelle, Intensität und Geruchsqualität sollen als getrennte Zielgrößen behandelt werden. Der vollständige Umfang kann ein Promotionsprojekt tragen; für die nächste Phase ist ein klar begrenzter Pilot sinnvoll.

## Datengrundlage und chemische Repräsentation

- Moleküle mit isomeren SMILES und stabilen Kennungen erfassen; Identität, Stereochemie, Protonierung und Tautomere nachvollziehbar behandeln.
- Lückenhafte Datensätze, fehlende Messwerte und unterschiedliche Messprotokolle ausdrücklich dokumentieren. Ein fehlender Messwert ist kein negatives Ergebnis.
- Öffentliche Quellen wie PubChem und The Good Scents Company als mögliche Recherche- und Identitätsquellen prüfen; Verfügbarkeit und Nutzungsrechte je Quelle festhalten.
- GC–MS als analytischen Baustein prüfen und chemische Identifizierung von sensorischen Messwerten unterscheiden.
- Mögliche Verzerrungen von LSER-/PAULY-basierten Daten, Quellen und Übertragungen untersuchen. Die Gesprächsnotizen enthalten hierzu eine Prüfaufgabe, keinen bestätigten Fehlerbefund.
- Neu erhobene, aus Literatur extrahierte und synthetisch erzeugte Daten kennzeichnen. Generierte Daten nicht als unabhängige experimentelle Bestätigung verwenden.

## Modelle und faire Benchmarks

- Morgan-Fingerprints, einfache statistische Modelle und Chemprop als Vergleichsrouten berücksichtigen.
- Hyperparameter einschließlich Schichtzahl, Neuronenzahl und Regularisierung ausschließlich auf Trainings-/Validierungsdaten auswählen.
- Prüfen, ob kleinere Netze bei strukturell ähnlichen Molekülen ausreichen. Größere Netze nur anhand eines dokumentierten Leistungsgewinns rechtfertigen.
- Ähnliche Moleküle, Tautomere und gemeinsame Grundgerüste beim Aufteilen der Daten berücksichtigen; Datenleckage und Mehrfachzählung vermeiden.
- Geruchsschwelle, Intensität, Qualität, Gefallen und Rezeptorantwort getrennt berichten. Literaturwerte und Vorhersagen nicht zu einem gemeinsamen Messdatensatz umetikettieren.
- Bestehende reservierte finale Tests erhalten. Neue Modellideen zunächst an unveränderten Entwicklungsprotokollen vergleichen.

## Rezeptorstrukturen, Docking und Dynamik

Zunächst vier Zielrezeptoren und die zugehörigen experimentellen Endpunkte verbindlich festlegen. Die folgende Strukturliste liefert Rechercheanker und legt diese vier Ziele nicht fest.

Als Pilot die Bindungstaschen, Strukturqualität und Ligandenpräparation prüfen. Experimentelle Strukturen und gegebenenfalls AlphaFold-Modelle getrennt kennzeichnen. Docking kann ein begrenzter erster Rechenschritt sein; es ersetzt keine Strukturvalidierung und liefert ohne experimentelle Kalibrierung keine gemessene Bindungsaffinität.

Weitere Prüfaufgaben:

- Aktive, inaktive, intermediäre und G-Protein-gekoppelte Zustände berücksichtigen, soweit geeignete Strukturen oder begründete Modelle vorliegen.
- Basale Aktivität, inverse Agonisten und zustandsabhängige Bindung als mögliche Einflussgrößen untersuchen.
- Flexibles Docking und mehrere Rezeptorkonformationen mit einem einfacheren starren Ausgangsmodell vergleichen.
- Für ausgewählte Fragen Membran-, Wasser- und Rezeptordynamik mit GROMACS untersuchen; ein vollständiger Dynamikansatz ist ein eigener Aufwandsposten.
- Rezeptorbasierte Merkmale beziehungsweise Embeddings zunächst als zusätzliche Klassifikations- oder Regressionsmerkmale testen.
- Docking-Scores, funktionelle Aktivierungswerte und Bindungsaffinität getrennt aufbewahren. Eine gemeinsame eigene Skala für vier Rezeptoren erst nach Definition der Messgröße, Referenzliganden und Kalibrierung entwickeln.

### Öffentliche Strukturreferenzen

Einträge am 5. November 2026 anhand der RCSB-PDB-Seiten geprüft. Alle fünf Einträge verwenden Elektronenmikroskopie; die Liste ist eine Auswahl und keine vollständige Bestandsaufnahme.

| PDB | Strukturbezug |
| --- | --- |
| [8F76](https://www.rcsb.org/structure/8F76) | Humaner OR51E2 mit Propionat und miniGs399. |
| [8UXY](https://www.rcsb.org/structure/8UXY) | Konsensusrezeptor consOR1 mit L-Menthol und trimerem mini-Gs-Komplex. |
| [9LKB](https://www.rcsb.org/structure/9LKB) | PL45–Olfr110–Gs-Komplex; Bezug zum Mausrezeptor Olfr110. |
| [9LDZ](https://www.rcsb.org/structure/9LDZ) | Konsensusrezeptor consOR6 mit trimerem Gs-Komplex. |
| [8W77](https://www.rcsb.org/structure/8W77) | Humaner Konsensusrezeptor OR52c im Apo-Zustand, ohne Ligand. |

## Experimentelle Übertragung und Geräte

**Aktueller Gerätestand, 5. November 2026:** Ein Olfaktometer ist durch Sponsoring gesichert. Die experimentelle Planung richtet sich auf Messungen mit diesem Gerät.

- Prüfen, wie gut eine Zelllinienantwort die Situation im Riechepithel abbildet. Lokale Anreicherung, Membranumgebung und Signalverarbeitung bleiben offene Erklärungsansätze.
- Kontrollierte Geruchsdarbietung mit einem Olfaktometer und sensorbasierte Detektion beziehungsweise elektrische Signalaufzeichnung als unterschiedliche Messaufgaben planen.
- Für Mischungsexperimente Konzentration, Mischungsverhältnis, Transportweg und zeitliche Abfolge dokumentieren.
- Schwellenmessung und Modellbenchmark mit klaren Referenzstoffen, Kontrollen und reproduzierbaren Protokollen verbinden.

## Organisation und Folgearbeiten

1. Einen kurzen Fortschrittsbericht mit Datensatzstand, Benchmark, offenen Fragen und nächstem Experiment erstellen. Wissenschaftliche Updates ohne persönliche Kontaktdaten im Repository führen.
2. Fachliche Rückmeldungen zu Geruchsschwellen, Rezeptorstruktur, sensorischen Messungen und Mischungen in konkrete prüfbare Aufgaben übersetzen.
3. Zusätzliche Labor- und Methodenkompetenz nach fachlichem Bedarf recherchieren. Keine Beteiligung oder Zustimmung einzelner Einrichtungen aus diesen Notizen ableiten.
4. Förder- und Gründungsoptionen, darunter ZIM sowie mögliche Bedingungen für ein Start-up in Neuseeland, separat recherchieren. Konditionen, Eignung und Zusagen sind offen; ebenso Bank- und Investorenfinanzierung.
5. Unklare Firmen-, Produkt- und Literaturstichworte vor Aufnahme als Referenz verifizieren. Aus den ursprünglichen Gesprächsstichworten allein folgen keine bestätigten Unternehmenszugehörigkeiten oder Publikationsnachweise.

## Nächster begrenzter Pilot

Vier Rezeptoren auswählen, einen versionierten Liganden-/Messdatensatz kuratieren, einen einfachen Fingerprint-Benchmark festlegen und anschließend den Zusatznutzen von Docking-Merkmalen prüfen. Ergebnis soll ein reproduzierbarer Vergleich mit dokumentierten Grenzen sein.
