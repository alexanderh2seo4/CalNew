---
title: AlphaFold und Rezeptor-Docking für CALNEW
date: 2026-11-02
type: primary-source-research
status: research-only; no computation or code changes
---

# AlphaFold und Rezeptor-Docking für CALNEW

**Empfehlung:** Ein kleiner, rezeptorspezifischer Versuch mit experimentellen Aktivitätsdaten ist sinnvoll. Ein vollständiger AlphaFold/Docking-Block für menschliche Geruchsqualität, Intensität oder Luftschwellen ist durch die hier geprüfte Evidenz noch nicht gerechtfertigt. Zuerst müssen Posequalität, funktionelle Aktivität und zusätzlicher Nutzen gegenüber einfachen Ligandenmodellen getrennt gezeigt werden.

Stand: Webrecherche am 2. November 2026. „Belegt“ bezeichnet Ergebnisse der jeweils verlinkten Primärarbeit oder offizielle Softwaredokumentation. „Empfehlung“ bezeichnet die daraus für CALNEW abgeleitete eigene Versuchsgestaltung. Dies ist eine gezielte Recherche, keine vollständige systematische Erfassung aller OR-Strukturen oder aller Dockingverfahren. Einige Verlagsvolltexte waren technisch nicht abrufbar; dort stützt sich die Zusammenfassung auf den Abstract der Originalarbeit in PubMed bzw. auf den offiziellen PDB-Eintrag. Keine Modelle wurden gerechnet und keine geschlossenen CALNEW-Testdaten geöffnet.

## 1. Was AlphaFold beiträgt

**Belegt:** AlphaFold 2 liefert Proteinstrukturmodelle; für ein kleines Duftmolekül ist anschließend ein separates Docking- oder Simulationsverfahren erforderlich. AlphaFold 3 modelliert dagegen Proteine und Liganden gemeinsam aus Sequenz und chemischer Definition. Seine Originalarbeit zeigt bessere Strukturvorhersagen auf ihren Vergleichssätzen, dokumentiert aber auch falsche Stereochemie, Kollisionen und falsch gewählte Konformationszustände. Verschiedene Seeds bilden kein thermodynamisches Lösungsensemble ab. Das Verfahren liefert damit Strukturhypothesen; die berichteten Konfidenzen bewerten deren Genauigkeit und sind keine gemessenen Bindungsaffinitäten. [AF2-Implementierung](https://github.com/google-deepmind/alphafold), [Abramson et al., Nature 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11168924/).

**OR-spezifischer Befund:** Beim experimentellen OR51E2 unterscheiden sich ECL3 und die Seitenkette R262 zwischen ligandengebundener Struktur und AF2-Modell. Gerade ein insgesamt plausibles Siebenhelixmodell kann somit eine für Bindung oder Aktivierung relevante lokale Abweichung enthalten. Die Arbeit beschreibt niedrige AF2-Konfidenz für ECL3 über viele menschliche ORs. [Billesbølle et al., Nature 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10580732/).

**Eigene Schlussfolgerung:** Rezeptor-pLDDT allein ist kein ausreichendes Auswahlkriterium. Zu prüfen sind die konkrete Tasche, Schleifen, Protonierung, Zustand und Ligandenchemie. Bei Duftstoffen mit wenigen Schweratomen können alternative Orientierungen funktionell relevant sein, auch wenn globale Proteinmetriken gut aussehen.

## 2. Experimentelle OR-Strukturen: nützliche Anker, keine Vollabdeckung

| Belegter Anker | Experimenteller Gegenstand | Bedeutung und Abgrenzung |
|---|---|---|
| OR51E2, 2023 | Propionatgebundener menschlicher OR im Gs-Komplex; PDB 8F76 | Gut definierter Kontrollfall für kleine Carboxylate; die Zellantwort wurde separat untersucht. [Originalarbeit](https://www.nature.com/articles/s41586-023-05798-y) |
| OR52cs, 2023 | Konsensrezeptor der menschlichen OR52-Familie, apo und octanoatgebunden | Ein seltener Vergleich unterschiedlicher Zustände; ein synthetischer Konsens ist kein nativer Einzelrezeptor. [Choi et al.](https://www.nature.com/articles/s41467-023-43983-9) |
| consOR51/1/2/4, 2024 | Vier Konsens-OR-Strukturen; Klassen I und II | Erweitern die verfügbaren Vorlagen. OR51E1-Homologiemodelle führten zu experimentell bestätigten Vorhersagen veränderter Fettsäurepräferenz nach Mutation. Das ist mechanistische Validierung, keine prospektive Duftstoffbibliothek. [de March et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC13504986/) |
| Olfr110 und consOR5, 2026 | Klasse-II-Strukturen mit dem Fettsäuremetaboliten PL45; auch 12(S)-HEPE funktionell betrachtet | Mausrezeptor bzw. Konsens, große hydrophobe Tasche; nicht auf alle flüchtigen Parfümstoffe übertragbar. [Han et al., Cell](https://pubmed.ncbi.nlm.nih.gov/41570821/) |
| bmOR6A2 und consOR6, 2026 | Durch Rückmutation erzeugte OR6A2-Variante; mehrere Aldehydkomplexe | Reversible Schiff-Base-Bindung an K4.60, durch Massenspektrometrie gestützt. Ein Standardmodell ausschließlich nichtkovalenter Kontakte wäre hier unvollständig. Das Konstrukt ist gezielt verändert. [Wang et al., Cell](https://pubmed.ncbi.nlm.nih.gov/41570822/), [PDB 9LE0](https://www.rcsb.org/structure/9LE0) |
| OR52cs mit OR52E8-Tasche, 2026 | HMHA-Komplex eines konstruierten OR52cs-E8pocket-Rezeptors | Reproduziert unter anderem Enantiomerselektivität; keine unmittelbar bestimmte Wildtyp-OR52E8-Struktur. [Choi et al., Communications Biology](https://pubmed.ncbi.nlm.nih.gov/42162228/) |

**Eigene Schlussfolgerung:** „Es gibt keine OR-Strukturen“ ist überholt. Ebenso falsch wäre „die menschlichen OR-Taschen sind strukturell gelöst“. Für jeden Zielrezeptor muss ein Strukturmanifest Spezies, Sequenz, Mutationen, Chimären/Konsensstatus, Ligand, G-Protein, Zustand und PDB-Version enthalten. Die Tabelle ist eine Auswahl relevanter Anker, keine behauptete vollständige Zählung.

## 3. Wie stark ist der nachgewiesene Nutzen?

**Prospektiv, experimentell und stark – aber außerhalb olfaktorischer ORs:** Lyu et al. verglichen AF2-basierte und experimentelle Strukturen für Ligandensuche. Mit DOCK3.8 wurden für σ2 64 von 119 AF2-priorisierten Molekülen im Bindungstest aktiv (54 %), für 5-HT2A 42 von 161 (26 %). Die Vergleichskampagnen an experimentellen Strukturen lieferten 51 % bzw. 23 %; die Unterschiede der Hit-Raten waren nicht signifikant. 5-HT2A ist ein GPCR, σ2 nicht. Das belegt, dass ein AF2-Modell produktive neue Chemie liefern kann; weder ist es ein Vina-/GNINA-Test noch ein Beweis für ORs oder Geruch. Die σ2-Kurzfassung nennt gerundet 55 %, der Ergebnistext nennt 64/119 und 54 %. [Lyu et al., Science 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11253030/).

**OR-nah, aber retrospektiv:** Hirao et al. untersuchten OR9Q2 mit AF2/ColabFold, Docking, Membran-MD und pharmakophorbasierter Poseauswahl. Die 13 Agonisten kamen zuerst aus einem zellbasierten Screen von 2.630 Geruchsstoffen; anschließend wurde das Modell mit diesen Liganden und 612 generierten DUD-E-Decoys bewertet. Die Dockingaufgabe ist somit keine verblindete prospektive Entdeckung neuer Agonisten. Generierte Decoys dürfen zudem nicht als experimentell gemessene Nichtaktivierer behandelt werden. Die Arbeit ist ein konkretes Methodenbeispiel und eine potenzielle Datenquelle für einen Pilot, kein belegter Trefferanteil für neue Duftstoffe. [Hirao et al., online 2025, Band 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC12686088/).

**Boltz-2, aktuelle experimentelle Demonstration außerhalb ORs:** Eine 2026 erschienene AKR1B10-Arbeit testete 40 ausgewählte Verbindungen nach Eingrenzung auf 867 Kandidaten und Diversitätsauswahl. 28/40 hemmten mit IC50 <10 µM. Dies ist ein relevanter experimenteller Erfolg eines Co-Folding-Workflows, aber an einem Enzym und mit zusätzlicher Auswahl; der Anteil ist keine allgemeine, unselektierte Modellgenauigkeit. [Kawano et al., JCIM 2026](https://pubmed.ncbi.nlm.nih.gov/42906054/). Die frühere Boltz-2-Ankündigung bezeichnete einen TYK2-Versuch als prospektiv, verwendete dort jedoch ABFE-Simulationen als Bestätigung; das ist von Nasslabortreffern zu unterscheiden. [Boltz-2-Projektbericht](https://www.boltz.com/boltz2).

**Rezeptorstruktur als ML-Merkmal, besonders direkt passend, aber Preprint:** „Decoding Smell from Receptor Structure“ kombiniert AF3-Taschenmerkmale, ESM2 und in-vivo-pS6-IP-Seq-Aktivierung. Das Modell nutzt 349 auf mindestens einen von 48 Geruchsstoffen reagierende ORs und trennt zufällig auf Rezeptorebene (70/15/15). Mutationen werden funktionell nachgeprüft. Dies adressiert Generalisierung auf Rezeptoren innerhalb eines festen Geruchspanels; es demonstriert keine freie Vorhersage beliebiger neuer Moleküle. Die Aktivierungsdaten stammen von Maus-ORs. Der Bezug zu menschlichen Geruchsdeskriptoren wird unter anderem mit OpenPOM-Vorhersagen analysiert und ist daher kein unabhängiger menschlicher Panelbenchmark. Die Arbeit bleibt in den geprüften Einträgen ein **Preprint**. [Lu et al., Research Square 2026](https://pubmed.ncbi.nlm.nih.gov/42326533/), [Volltext](https://pmc.ncbi.nlm.nih.gov/articles/PMC13278317/).

**Eigene Bewertung:** Das rechtfertigt einen untersuchten biologischen Zusatzkanal. Es rechtfertigt weder ein pauschales „Docking funktioniert bei ORs nicht“ noch die Behauptung eines bereits bewiesenen End-to-End-Vorteils für CALNEWs menschliche Luftschwellen oder Intensität.

## 4. Methodenvergleich für einen begrenzten Versuch

| Verfahren | Was es praktisch liefert | Grenze für CALNEW | Eigene Rolle im Pilot |
|---|---|---|---|
| AutoDock Vina 1.2.x | Suche flexibler Ligandenposen in einer vorbereiteten Rezeptortasche, empirische Scoringfunktionen; Batch-/Python-Unterstützung | Ergebnis hängt von Tasche und Vorbereitung ab; Score ist kein direkt gemessener Kd oder EC50. [Originalarbeit](https://pmc.ncbi.nlm.nih.gov/articles/PMC10683950/) | Reproduzierbare CPU-Baseline, mehrere Seeds und wenige vorher festgelegte Rezeptormodelle |
| GNINA 1.3 | Vina-/smina-basierte Suche mit CNN-Auswertung; gegenüber 1.0 aktualisierte Modelle und PyTorch; getrennte Optionen für Rescoring und Refinement | Gelerntes Scoring muss bei ORs validiert werden; verschiedene Ausgaben nicht als dieselbe physikalische Größe behandeln. [1.3-Paper](https://doi.org/10.1186/s13321-025-00973-x), [offizielle Dokumentation](https://github.com/gnina/gnina) | Zweite Scoringfamilie; zunächst Standard-Rescoring, getrennt von teurerem Refinement |
| DiffDock / DiffDock-L | Diffusionsbasierte Protein-Ligand-Posen; neuere L-Version verbessert Generalisierung | Die Entwickler sagen ausdrücklich: kein Affinitätsprädiktor. Confidence bewertet die Pose und hängt von Eingabeverteilung und Rezeptorkonformation ab. [offizielles Repository/FAQ](https://github.com/gcorso/DiffDock), [Originalpaper](https://arxiv.org/abs/2210.01776) | Optionaler unabhängiger Posegenerator, anschließend Geometrieprüfung und festgelegtes Rescoring |
| AlphaFold 3 | Gemeinsame Vorhersage des Komplexes; kann strukturelle Anpassung modellieren | Strukturkonfidenz ersetzt weder Aktivitätsassay noch Affinitätskalibration; dynamische Zustände bleiben schwierig. [Originalpaper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11168924/) | Kleine, vorab festgelegte Teilmenge als Vergleich zu AF2 + Docking; mehrere Seeds mit derselben Auswahlregel |
| Boltz-2 | Gemeinsame Struktur plus gesonderte Binder-/Affinitätsausgaben | Offizielle Doku unterscheidet Binderwahrscheinlichkeit von einem Affinitätswert in log10(IC50/µM); letzterer ist nicht automatisch OR-EC50 oder menschliche Schwelle. [offizielle Dokumentation](https://github.com/jwohlwend/boltz) | Praktische offene Alternative für denselben kleinen Vergleich, OR-Kalibration zwingend |

Ein Vergleich allein nach RMSD oder einer erfolgreichen Referenzpose wäre zu schwach: PoseBusters ergänzt Prüfungen auf Chemie, Stereochemie, Ligandengeometrie und Kollisionen. Die 2024er Arbeit zeigte erhebliche Probleme damaliger ML-Docker auf neuen Strukturen; das ist kein endgültiges Ranking späterer DiffDock-L-, AF3- oder Boltz-Versionen. [Buttenschoen et al., Chemical Science 2024](https://pubs.rsc.org/en/content/articlepdf/2024/sc/d3sc04185a).

## 5. Binding, Aktivierung und menschlicher Geruch sind verschiedene Zielgrößen

**Belegt:** OR-Strukturarbeiten kombinieren Struktur, Mutagenese und cAMP-/Funktionsassays, statt aus geometrischem Fit unmittelbar Aktivierung abzulesen. Genetische Variation menschlicher ORs kann Wahrnehmung verändern; zellbasierte Aktivität kann dabei biologisch relevante Rezeptoren identifizieren. [OR51E2](https://pmc.ncbi.nlm.nih.gov/articles/PMC10580732/), [Trimmer et al., PNAS 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6511007/).

**Eigene Konsequenz für die Interpretation:**

1. Eine mögliche Pose beantwortet zunächst, ob und wie ein Molekül räumlich in ein Modell passt.
2. Bindung betrifft Affinität/Besetzung; Aktivierung zusätzlich Wirksamkeit, Signalzustand und Messsystem. Ein Antagonist kann binden, ohne den Agonistenreadout auszulösen. EC50 und Kd sind deshalb nicht austauschbar.
3. Geruchsqualität und Intensität betreffen Aktivierungsmuster vieler Rezeptoren sowie weitere Verarbeitung. Luftschwellen hängen zusätzlich davon ab, welche Konzentration den Rezeptor erreicht. Ein einzelner Rezeptorscore begründet kein menschliches Deskriptorlabel und keine Umrechnung in ppbv.
4. Nichtantwort im Zellassay ist konzentrations- und systemspezifisch. Schlechte Expression oder Löslichkeit darf nicht ungeprüft als echter Nichtbinder etikettiert werden.

Der lokale Projektbericht hält dieselbe Endpunkttrennung bereits fest: B1 verwendet Luftschwellen, B2 nominelle Keller-Lösungsverdünnungen, Ravia einen separaten Endpunkt. Das vorhandene Olfr73-Pharmakophor betrifft einen **Mausrezeptor** und ist nicht in die menschlichen Vorhersageköpfe integriert. [Lokale Projektbasis](../../CALNEW%20Project%20Architecture%20and%20Performance.md), [Pipeline](../../docs/PIPELINE.md).

## 6. Eigene Empfehlung: kleiner Pilot mit drei getrennten Erfolgsfragen

**Frage A – können die Strukturen lokale Kontakte reproduzieren?** OR51E2/Propionat als technischer Kontrollfall; optional eine zweite, chemisch deutlich andere veröffentlichte OR-Struktur. Experimentelle Tasche, AF2-Modell und kleine Co-Folding-Stichprobe getrennt vergleichen. Referenzligand nur zum definierten Redocking entfernen; veröffentlichte mutierte Konstrukte nicht stillschweigend in Wildtyp umbenennen. Redocking ist ein positiver Funktionstest der Pipeline, kein blinder Leistungstest. Kleine symmetrische Carboxylate zusätzlich über Interaktionsmuster beurteilen, nicht nur RMSD.

**Frage B – rangieren Scores echte funktionelle Aktivitäten besser als Ligandenbaselines?** Einen gut gemessenen menschlichen Rezeptor auswählen, etwa OR9Q2, sofern Originalaktivitätsdaten und Nutzungsrechte verfügbar sind. Zielumfang als Planung: 50–200 definierte Moleküle einschließlich gemessener Nichtantworten und naher inaktiver Analoga; alle Verbindungen mit Messkonzentration, Protokoll und Identität. Falls die Quelle nur 13 Positive und künstliche Decoys liefert, ist das ausdrücklich ein Machbarkeitsversuch, kein Aktivitätsbenchmark mit echten Negativen. Das bestehende Olfr73-Panel kann parallel einen separaten Maus-Kontrollfall bilden, darf aber die menschliche Zielaufgabe nicht ersetzen.

Für diesen ersten Benchmark reichen Vina, GNINA und **eine** Co-Folding-Alternative; DiffDock ergänzen, wenn Posegenerierung als eigene Frage untersucht werden soll. Vorgeschlagenes Budget: wenige vorab festgelegte Rezeptormodelle, drei Docking-Seeds, einheitliche Ligandenprotonierung und ein fixes Seedbudget für Co-Folding. Der Vergleich muss Suchraum und verfügbare Tascheninformation offenlegen: Ein bekannter Taschenmittelpunkt und blindes Whole-Protein-Docking sind verschiedene Aufgaben.

Vorab festlegen:

- **Ligandenbaselines:** nächster aktiver Nachbar mit chiralem Morgan-Fingerprint, einfache 2D-Deskriptoren, das vorhandene rezeptorspezifische Pharmakophor falls passend. Aktuelle CALNEW-Sensorikmodelle sind zusätzliche Kandidatenauswahlbaselines, kein Ersatz für Rezeptoraktivitätslabels.
- **Trennung:** analoge/scaffoldverwandte Moleküle gruppieren; Rezeptorkonformation, Scoregewicht und Schwelle nur innerhalb von Trainings-/Validierungsdaten wählen. Keine Wahl der „besten“ Rezeptorstruktur anhand desselben später berichteten Tests. Experimentelle Struktur mit ihrem bekannten Liganden und vortrainierte Co-Folding-Systeme separat auf mögliche Struktur-/Liganden-Vorinformation dokumentieren.
- **Primärmetrik:** AP und Treffer unter den ersten k Kandidaten bei vorhandenen gemessenen Negativen; AUROC ergänzend, mit Gruppierungs-/Bootstrap-Unsicherheit. EF@k nur mit ausdrücklich berichteter Grundrate. Korrelation mit pEC50 nur innerhalb konsistent gemessener Agonisten und getrennt von Klassifikation; zensierte Werte bewahren.
- **Qualität/Kosten:** RMSD plus Kontakt-/Geometrieprüfung nur dort, wo Referenzstrukturen vorhanden sind; ansonsten keine fiktive RMSD-Ground-Truth. Ausfallrate, Rechenzeit, GPU-Stunden und Sensitivität gegenüber Seeds/Rezeptormodellen mitberichten.

**Frage C – bringt die Priorisierung neue experimentelle Treffer?** Erst nach B einen eingefrorenen Prospektivplan: beispielsweise 24–48 neue Moleküle, nach Score und Diversität ausgewählt, mit Baseline- und Zufalls-/Diversitätskontrollen. Verblindeter cAMP-Assay, Dosisreihen, Positiv- und Vektorkontrollen; bei Bedarf Expression/Löslichkeit prüfen. Das ist eine Größenordnung für einen Pilot, keine formale Powerberechnung. Der Trefferanteil muss pro Auswahlarm und mit Unsicherheit berichtet werden. Ein fehlender Vorteil gegenüber Fingerprint/Pharmakophor ist ein legitimes Stoppsignal.

**Integration erst danach:** Einen Rezeptorblock mit Scores, Kontakten, Modellen und Verfügbarkeitsflag als versionierte optionale Merkmalsfamilie prüfen. Bei nur 186 lokalen Luftschwellen ist ein großer frei trainierter Rezeptorvektor besonders überfittingsanfällig. Ein Einfluss auf B1/B2/A muss in den vorhandenen strukturellen Entwicklungsfalten per Ablation nachgewiesen werden; alle reservierten Tests bleiben geschlossen. Ein guter Rezeptorbenchmark allein genügt dafür nicht. Diese Empfehlung folgt den bereits dokumentierten CALNEW-Evaluationsgrenzen, sie ist kein ausgeführtes Experiment.

## 7. Lizenzen und Kommerzialisierung, knapp und aktuell geprüft

| Komponente | Offiziell dokumentierter Stand | Praktische Folgerung |
|---|---|---|
| AF2 | Code Apache-2.0, Parameter CC BY 4.0. [Repository](https://github.com/google-deepmind/alphafold) | Nutzungsbedingungen der Datenbanken/Abhängigkeiten zusätzlich beachten. |
| AF3 lokal | Aktuelles README: Code Apache-2.0; Gewichte und damit erzeugte Outputs unter gesonderten Bedingungen für bestimmte nichtkommerzielle Nutzungen durch nichtkommerzielle Organisationen. [README](https://github.com/google-deepmind/alphafold3), [Gewichtbedingungen](https://github.com/google-deepmind/alphafold3/blob/main/WEIGHTS_TERMS_OF_USE.md) | Offener Code bedeutet hier keine frei kommerziell nutzbaren Gewichte/Outputs. |
| AF3 kommerzieller Cloud-Zugang | Google dokumentiert kommerziellen Zugang mit Subscription und Allowlist in Model Garden. [Google Cloud](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/open-models/alphafold-3) | Eine pauschale Aussage „AF3 ist überhaupt nicht kommerziell verfügbar“ wäre am Recherchestand überholt. Bedingungen des konkreten Zugangs prüfen. |
| Vina | Apache-2.0. [Offizielle Lizenz](https://github.com/forlilab/AutoDock-Vina/blob/develop/LICENSE) | Geeignete offene Baseline. |
| GNINA | Offizielles README erklärt GPL-/Apache-Doppellizenz; Apache-only erfordert Entfernen aller OpenBabel-Referenzen. [Lizenzabschnitt](https://github.com/gnina/gnina#license) | Nicht pauschal als reines Apache-Paket einordnen; Distribution/Einbettung anhand des konkreten Builds prüfen. |
| DiffDock | MIT im offiziellen Repository. [Repository](https://github.com/gcorso/DiffDock) | Konkrete Gewichte/Abhängigkeiten im Manifest festhalten. |
| Boltz-2 | Code und Gewichte laut offiziellem Repository MIT, akademisch und kommerziell verwendbar. [Repository](https://github.com/jwohlwend/boltz) | Für einen offenen Pilot attraktiv; Daten-/Assayrechte bleiben eigenständig. |

Die Lizenzangaben beschreiben die geprüften offiziellen Seiten, keine Rechtsberatung und keine Freigabe fremder experimenteller Datensätze. Technische Nutzungsaussagen ersetzen keine Prüfung des gewählten Softwarestands und Vertragszugangs.
