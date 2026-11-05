---
date: 2026-11-02
type: research
status: primary-source-reproduction-audit
---

# Exakte Reproduktion der publizierten Olfaktophore: Verfahren, Software und fehlende Daten

**Ergebnis:** Die publizierten Modelle beruhen auf echten ligandbasierten 3D-Rechnungen. Die verfügbaren Quellen tragen einen ernsthaften Nachbau der beschriebenen Arbeitsweise und neue, ausdrücklich eigene Modelle. Sie tragen derzeit keine Behauptung, die vollständigen Originalhypothesen oder deren numerische Vorhersagen exakt reproduziert zu haben. Besonders entscheidend sind die ursprünglichen Merkmalsdefinitionen, Gewichte, Toleranzen und die von Hand gesetzten Ausschlussvolumina. Ein Softwarekauf allein würde diese Informationslücke nicht schließen.

Diese Prüfung umfasst den vollständigen lokalen Calone-Artikel von 2003, die relevanten Buchseiten der zweiten Auflage von *Scent and Chemistry* (2022), den Rosen-Artikel von 2020, die öffentlich erreichbare Verlagsseite der Muguet-Arbeit von 2023 und Herstellerinformationen. Sie enthält keine neuen Fits, Modellparameter oder Benchmarkresultate.

## 1. Welche Originalmodelle und Softwarestände belegt sind

| Quelle / Modell | Nachweisbare Software | Nachweisbare Berechnung; Grenze des Nachweises |
|---|---|---|
| Kraft & Eichenberger 2003, Marine / Calone | **Accelrys Catalyst**. Ref. 22 nennt Produkt und URL, **keine Versionsnummer**. | Tabelle 1 liefert gemessene und berechnete Schwellen; Abb. 3 zeigt das Modell und ein Distanzschema; Konformerfenster 3 kcal/mol. Der konkrete Algorithmusname HypoGen steht nicht im Artikel. [Originalarbeit](https://doi.org/10.1002/ejoc.200300174), lokal: PDF (local artifact omitted from the public snapshot), S. 3737–3738 und 3743. |
| Revidiertes Marine-Modell, im Buch Abb. 3.34 | Der Buchtext ordnet die Modellfamilie Catalyst / später Discovery Studio zu. Eine konkrete Versionsnummer für die Revision ist daraus nicht belegt. | Die zugrunde liegende Arbeit ist **Kraft, Popaj, Müller & Schär, Synthesis 2010, 3029–3036**, DOI **10.1055/s-0030-1258142**, nicht der Rosen-Artikel von 2020. Der primäre Autoren-Repositoriumseintrag bestätigt ausdrücklich ein verbessertes Olfaktophormodell. [Autoren-Repositorium](https://pure.johnshopkins.edu/en/publications/vanilla-oceanics-synthesis-and-olfactory-properties-of-1e-7-prop--2/), [Originalartikel](https://doi.org/10.1055/s-0030-1258142). |
| Hauser, Kraft & Carreira 2020, Rosen-Nitrile | **Discovery Studio 18.1.100.18065**, explizit in Text, Abb. 8 und Ref. 29. Für die gesonderte flexible Überlagerung in Abb. 9: **MOE 2016.08.02**, Amber10:EHT. | Zwölf Trainingsmoleküle, quantitatives Modell; Konformerfenster 20 kcal/mol und `uncert = 3`. Das MOE-Alignment ist eine zweite Analyse mit eigener Zielfunktion. [Originalartikel, DOI](https://doi.org/10.2533/chimia.2020.247), lokaler Volltext (local artifact omitted from the public snapshot), S. 249–251. |
| Ohrmann et al. 2023, Nympheal / Muguet | Ref. 9 belegt **BIOVIA Discovery Studio 2022, v22.1.0.21297**; die Referenz nennt außerdem das Jahr 2021. | Das Publikationsjahr 2023 ist kein Softwareversionsname. Die öffentlich lesbare Referenzliste verweist außerdem auf *Scent and Chemistry*, 2. Aufl. 2022, S. 94. Die vollständigen Modellparameter waren aus dem hier zugänglichen Abstract nicht prüfbar. [Verlagsseite und Referenzen](https://onlinelibrary.wiley.com/doi/abs/10.1002/hlca.202300040). |
| Riad et al. 2021, Calone-Abbildung | Der Review nennt **Phase 3.4**. | Daraus lässt sich die Software der Originalrechnung von 2003 nicht ableiten. Die vollständige Originalhypothese ist durch die hier zitierten öffentlichen Quellen nicht belegt. [Review](https://doi.org/10.3390/chemistry3040103). |

Eine Aussage wie „Calone wurde mit HypoGen in Discovery Studio 2022 gerechnet“ würde hier drei verschiedene Quellen und Zeitstände vermischen. Die durch die Buchlektüre zusätzlich belegte manuelle Fixierung des Grundgerüsts spricht außerdem gegen die Annahme, das 2003-Modell sei allein durch einen unbeschränkten Standard-HypoGen-Lauf entstanden.

## 2. Das Buch präzisiert den tatsächlichen Marine-Workflow

Die lokal vorliegende zweite Buchauflage ist eine direkte Quelle des Mitautors der Originalmodelle. Auf **S. 109–111** beschreibt sie mehr als der Methodenabsatz von 2003:

- Beim ursprünglichen Modell wurde der Benzodioxepinon-Kern über **drei H-Brückenakzeptoren und eine aromatische Merkmalsposition fixiert**. Aus den synthetisierten Verbindungen und ihren Schwellen wurde die zusätzliche aliphatisch-hydrophobe Position berechnet. Das zulässige Konformerfenster betrug 3 kcal/mol.
- **Drei Ausschlussvolumina wurden von Hand platziert.** Die hydrophobe Position liegt 6,3 Å vom aromatischen Zentrum entfernt. Die Angabe 59 % entspricht der im Originalartikel berichteten Korrelation 0,59; sie ist keine 59-prozentige Trefferquote.
- Die stark wirksamen vinylierten Calone-Derivate wurden vom alten Modell unzureichend vorhergesagt. Die Revision verschob den Hydrophob stärker in die aromatische Ebene und auf **7,23 Å** Abstand. Sie enthält **zwei Akzeptoren und sechs Ausschlussvolumina**. Das Buch bezeichnet die verbesserte Kennzahl als 85 % „predictability“; ohne die Primäranalyse darf daraus keine externe Genauigkeit oder Trefferquote von 85 % gemacht werden.
- Das Buch berichtet auch eine Vorhersage für einen Indanylaldehyd außerhalb des Trainingsgerüsts: 0,064 ng/L Luft berechnet gegenüber später 0,018 ng/L gemessen. Das ist ein konkreter Literatur-Präzedenzfall für neue Kandidaten, keine Validierung beliebiger Strukturen.

Quelle: *Scent and Chemistry*, 2. Auflage (2022), S. 109–112, Literatur S. 128. Die Buchdatei wird nicht mitveröffentlicht.

**Folgerung für Reproduktion:** Eine vollautomatische neue Merkmalsclusterung wäre bereits methodisch eine andere Untersuchung. Die Originalarbeit muss als Kombination aus chemisch vorgegebenem Gerüst, rechnerischer Anpassung und manuellen geometrischen Beschränkungen verstanden werden.

## 3. Catalyst / HypoGen und Phase sind unterschiedliche Rechenverfahren

### Catalyst ist die Plattform; HypoGen ist ein bestimmter Trainingsalgorithmus

BIOVIA unterscheidet ausdrücklich **HipHop** für qualitative gemeinsame Merkmale, **HypoGen** für quantitative Struktur-Aktivitätsbeziehungen sowie **HipHopRefine / HypoGenRefine** zur Einbeziehung inaktiver Verbindungen. Der Hersteller nennt eigene Catalyst-Merkmalsdefinitionen, Form- und Ausschlussvolumina sowie vollständiges, partielles und erforderliches Mapping. Daher bezeichnet „mit Catalyst gerechnet“ noch kein vollständig festgelegtes Training. [Hersteller-Datenblatt](https://www.3ds.com/fileadmin/PRODUCTS-SERVICES/BIOVIA/PDF/Pharmacophore-Ligand-based-Design-with-BIOVIA-Discovery-Studio.pdf).

Für den allgemeinen **HypoGen-Ablauf** sind drei Schritte dokumentiert: gemeinsame Hypothesen unter hochaktiven Molekülen konstruieren, auch zu inaktiven Molekülen passende Hypothesen ausscheiden, anschließend Geometrie / Merkmale mittels Simulated Annealing optimieren. Die Primäranwendung von Roy et al. beschreibt die Abfolge ausdrücklich für Discovery Studio 3.0; sie ist kein Beweis, dass alle diese Schritte unverändert im Calone-Lauf verwendet wurden. [Originalstudie, Methoden „3D Pharmacophore generation“](https://pubs.rsc.org/en/content/articlehtml/2011/md/c1md00135c).

Die ursprüngliche Entwicklerdarstellung von **Li, Sutter & Hoffmann**, „HypoGen: An Automated System for Generating 3D Predictive Pharmacophore Models“, befindet sich in *Pharmacophore Perception, Development, and Use in Drug Design*, Kapitel 10, S. 171 ff. Die Verlagsseite bestätigt Inhalt und Autoren; der vollständige Algorithmustext wurde hier nicht zugänglich. [Originalverlag](https://iul-press.us/product/pharmaciphore-perception-development-and-use-in-drug-design/). Die Entwicklerübersicht von Kurogi & Güner behandelt zudem HipHop, HypoGen und catSearch; die frei erreichbare Seite enthält hier nur Abstract und bibliographische Daten. [Verlag, DOI 10.2174/0929867013372481](https://www.benthamscience.com/article/10328). Diese Zugriffslücke sollte ausdrücklich stehen bleiben, statt eine angeblich exakte Eigenimplementation aus knappen Sekundärbeschreibungen abzuleiten.

**Fitting ist eine andere Aufgabe als Training.** Nach Festlegung einer Hypothese werden Merkmale eines Moleküls in mehreren Konformeren zugeordnet und räumlich überlagert. Der Score hängt von gemappten Merkmalen, ihren Gewichten und normierten Abweichungen von Merkmalszentren ab. Eine publizierte HypoGen-Anwendung gibt eine gewichtete Fitfunktion mit quadratischem Verhältnis `Abweichung / Toleranz` sowie getrennte Fehler-, Gewichts- und Konfigurationskosten an. Die Originalhypothese enthält deshalb mehr Information als einen Satz farbiger Koordinaten. Die Gleichung einer anderen Studie einschließlich deren Defaultwerten darf nicht ohne Prüfung auf Calone übertragen werden. [Originalstudie mit Gleichungen 4–5](https://eacademic.ju.edu.jo/mutasem/Shared%20Documents/Pharmacophore%20Modeling%20Quantitative%20Structure%E2%80%93Activity%20Relationship%20Analysis%20for%20GSK%20inhibitors%2C.pdf).

Für quantitative Schwellen gehören zusätzlich die genaue Zielgrößentransformation, Einheiten und Kalibrierung zum Modell. Beispielsweise trainiert die Rosen-Arbeit mit molaren Aktivitäten, während sie Schwellen auch in ng/L aufführt. Ein geometrischer Fit ist ohne diese quantitative Beziehung keine Schwellenprognose. Im Rosen-Artikel bestehen außerdem erkennbare Nummerierungswidersprüche zwischen Tabelle, Fließtext und Bildunterschrift, unter anderem 23/24 und 22/23; eine Neuberechnung muss Strukturen, nicht nur Nummern abgleichen. Lokale Originalquelle, S. 249–250 (local artifact omitted from the public snapshot).

### Phase: gemeinsame Pharmakophore, danach optional ein eigenes QSAR

Die Entwicklerarbeit von **Dixon et al. 2006** beschreibt eine baumbasierte Suche nach gemeinsamen räumlichen Merkmalsanordnungen in Konformerensembles. Hypothesen werden nach Überlagerung der Merkmalspositionen, Richtungsvektoren und Molekülvolumina bewertet; Treffer in inaktiven Trainingsmolekülen werden bestraft. Die quantitative Stufe des dort demonstrierten Verfahrens verwendet **Gitterbelegungen aus den ausgerichteten Molekülen und Partial Least Squares (PLS)**. Das ist keine bloße Umbenennung der Catalyst-Fitfunktion. [Entwickler-Originalarbeit](https://onlinelibrary.wiley.com/doi/10.1111/j.1747-0285.2006.00384.x).

Die ausführliche Methodenpublikation ist [Dixon et al., J. Comput.-Aided Mol. Des. 2006, 20, 647–671](https://link.springer.com/article/10.1007/s10822-006-9087-6). Ihr öffentlich lesbarer Anhang definiert etwa die Hypothesenselektivität als negative Zehnerlogarithmus-Wahrscheinlichkeit eines zufälligen Treffers in einer Arzneistoffpopulation. Dieser Score ist keine Marine-Geruchswahrscheinlichkeit. Auch die aktuelle [Phase-Produktseite](https://www.schrodinger.com/platform/products/phase/) trennt Hypothesenerzeugung, Konformersuche und Screening; heutige OPLS4-Optionen belegen keine identischen historischen Defaults.

**Praktische Konsequenz:** Ein Phase-Neutraining, ein eigenes RDKit-Matching und ein Catalyst/HypoGen-Neutraining können alle echte 3D-Rechnungen sein. Numerische Übereinstimmung mit dem historischen Catalyst-Modell folgt aus keiner dieser Methodenbezeichnungen. Geometrie, Merkmalssemantik, Suchraum und quantitative Vorhersagefunktion müssen gemeinsam übereinstimmen.

## 4. Was an Dateien und Supplementen tatsächlich geprüft wurde

| Quelle | Erreichbarer Befund | Was daraus nicht folgt |
|---|---|---|
| Marine 2003 | Vollständiges lokales PDF, neun Seiten; Tabelle 1 und Abb. 3 vorhanden. Im PDF keine eingebettete maschinenlesbare Hypothese identifiziert. Die Verlagsseite war beim Abruf nicht erreichbar. | Kein Nachweis, dass weltweit kein Supplement oder Originalarchiv existiert. |
| Revidiertes Marine-Modell 2010 | DOI, Titel, Autoren und Abstract über das Autoren-Repositorium verifiziert. Thieme-Zugriff lieferte hier eine Zugriffschallenge; Volltext und mögliche Supplemente konnten nicht inhaltlich geprüft werden. | Keine Aussage „kein Supplement“. Die genaue Datei- und Parameterlage von 2010 bleibt offen. |
| Rose 2020 | Offener Artikel mit Messdaten, berechneten Aktivitäten und ausgewählten Trainingsparametern lokal vorhanden. Die publizierte Abb. 8 ist eine Darstellung, kein überprüfter Modell-Export. | Keine vollständige Originalgeometrie oder Laufdatei aus einer Abbildung ableiten. |
| Muguet 2023 | Wiley nennt ausdrücklich **hlca202300040-sup-0001-misc_information.pdf**, 8,9 MB, und eine Datenverfügbarkeitserklärung zugunsten der Supplemente. Download wurde hier mit HTTP 403 abgewiesen. [Verlagsseite](https://onlinelibrary.wiley.com/doi/abs/10.1002/hlca.202300040), [offizieller Supplement-Link](https://onlinelibrary.wiley.com/action/downloadSupplement?doi=10.1002%2Fhlca.202300040&file=hlca202300040-sup-0001-misc_information.pdf). | Der Inhalt ist ungeprüft. Weder ein Geometrieexport noch dessen Fehlen ist damit bewiesen. |
| Lokal vorhandenes `muguet_s2.zip` | Das Archiv enthält `Bourg.pse` und vier `hOR174_Bourg*_ext80.log`-Dateien; das passt zur **Rezeptor-/Dockingarbeit 2017**. | Diese Datei ist kein nachgewiesenes Supplement des Nympheal-Modells 2023 und keine quantitative Muguet-Hypothese. |

Die 2018 erschienene **Primärdarstellung der Nympheal-Entdeckung** nennt Discovery Studio, **57 Muguetaldehyde**, molare sensorische Detektionsschwellen sowie drei hydrophobe Regionen. Sie zeigt auch den Bezug zum älteren bifunktionalen Muguet-Modell von 1999. Der öffentlich lesbare Text ersetzt jedoch keine vollständige strukturidentifizierte 57er-Trainingsdatei. [Goeke, Kraft, Lelievre & Alchenberger 2018](https://www.perfumerflavorist.com/fragrance/ingredients/article/21856694/discovery-of-nympheal-the-definitive-muguet-aldehyde).

Die öffentliche Verfügbarkeit der vollständigen Originalparameter ist hier nicht belegt. Ein eigenständiger Nachbau muss seine Annahmen dokumentieren und darf nicht als exakte Reproduktion bezeichnet werden.

## 5. Welche Exportformate belegt sind

- **Discovery Studio / Catalyst:** Ein Herstellerbeispiel beschreibt **`.chm`** als Query für `Ligand Pharmacophore Mapping` und `Search 3D Database`. [Herstellerforum, Beispiel für DS 2.1](https://3dswym.3dexperience.3ds.com/question/biovia-drug-discovery-development/create-shape-feature-one-per-ligand-and-save-to-chm-file_cxRPAa5rR167p5AYo_msKg). Eine Primärstudie mit DS 4.0 bestätigt `.chm` und berichtet, dass diese Dateien unter anderem Merkmalsnamen, Koordinaten, Vektoren und Toleranzen enthalten. [Zhou et al. 2014, „Parsing pharmacophore files“](https://link.springer.com/article/10.1186/1471-2105-15-S16-S5).
- **Phase:** Die Hersteller-API definiert **`.phypo`** als gzip-komprimierte Maestro-Datei mit einem Hypothesenobjekt. [Öffentlicher Hersteller-Quelltext, `is_hypothesis_file`](https://learn.schrodinger.com/public/python_api/2022-4/_modules/schrodinger/utils/fileutils.html). Eine offizielle KNIME-Präsentation bestätigt `.phypo` / `.mae` für neuere und `.xyz` für ältere Hypothesenformate. [Schrödinger 2023-4](https://www.schrodinger.com/wp-content/uploads/2023/11/knime-_new_features_2023-4.pdf).

Damit sind `.hypo`, allgemeine `.xml`-Dateien oder irgendeine `.ds*`-Datei **nicht als verifizierte Originalausgabe dieser Arbeiten** belegt. Auch ein echtes `.chm` würde allein noch nicht beweisen, dass Trainingsdaten, Konformer, Aktivitätstransformation und sämtliche Einstellungen vollständig erhalten sind. Für exaktes Neutraining braucht man das Laufarchiv zusätzlich zum fertigen Modell.

## 6. Präzise Reproduktionsblocker

| Benötigte Information | Warum sie für Exaktheit nötig ist | Aktueller Befund |
|---|---|---|
| Vollständige finale Featuregeometrie einschließlich Richtungen, Gewichten, Toleranzen und Mappingregeln | Unterschiedliche Definitionen ändern die zulässigen Treffer und den Score. | Distanzschema 2003 und Buchdarstellungen sind vorhanden; vollständiger nativer Export nicht verfügbar. |
| Zentren und Radien aller Ausschlussvolumina | Zwei gleich aussehende Modelle können unterschiedliche Moleküle ausschließen. | Drei manuell platzierte Volumina beim Original, sechs bei der Revision; vollständige numerische Definition nicht festgestellt. |
| Historisches Dictionary und exakter Softwarestand | Featurewahrnehmung und Suchverfahren können sich ändern. | Catalyst-Version 2003 unbekannt; DS-Versionen 2020 und 2023 belegt. |
| Konformer- und Suchprotokoll, Fixierungen, Ausgangsstrukturen | Das 3-kcal-Fenster legt weder Generator noch Anzahl / Startgeometrie / Referenzminimum fest. | Kernfixierung und Energiegrenze aus dem Buch belegt; komplettes Protokoll fehlt. |
| Quantitative Kalibrierung und Zielgrößenkonvention | Dieselbe Geometrie kann je nach Gewichtung und Transformation andere Schwellen liefern. | Vergleichswerte publiziert; die vollständige Originalfunktion muss aus Lauf / Modellarchiv bestätigt werden. |
| Vollständige, strukturidentifizierte Trainingsdaten mit Stereo- und Mischungsstatus | Namens- und Nummernfehler wirken direkt auf Training und Prüfergebnis. | Calone-Tabelle als Ausgangspunkt vorhanden; Rose enthält Nummerierungswidersprüche; 57er-Muguet-Satz nicht vollständig gesichert. |

Eine vollständige, exakte Distanzmatrix kann ideale Merkmalszentren im Allgemeinen bis auf starre Bewegung und gegebenenfalls Spiegelung festlegen. **Das ist hier nicht gleichbedeutend mit dem Originalmodell:** Gerundete Teilabstände legen keine Akzeptorrichtungen, Toleranzen, Gewichte oder handplatzierten Ausschlusskugeln fest. Die fehlende absolute Orientierung im Raum wäre dagegen unproblematisch, solange alle Modellteile gemeinsam transformiert werden. Eine Bilddigitalisierung liefert zusätzliche Bedingungen mit Messfehlern, keinen Originalexport.

## 7. Legitimer aktueller Softwarezugang

**Für dieselbe Softwarefamilie ist Discovery Studio mit lizenziertem Catalyst-/Pharmakophor-Modul die sachlich passende Wahl.** Der Hersteller führt weiterhin Catalyst-Merkmalswahrnehmung, quantitative / qualitative Pharmakophore und flexible Ligandenanpassung auf. [Aktuelles Herstellerdatenblatt](https://www.3ds.com/assets/invest/2023-10/biovia-discovery-studio-overview.pdf). Zugangswege sind vorhandene Institutionslizenzen, eine eigene passende Lizenz oder eine vom Lizenzinhaber erlaubte Zusammenarbeit. Historische Versionen und ihre Kompatibilität müssen gesondert beim jeweiligen Lizenzinhaber / Hersteller geklärt werden.

Der kostenlose **Discovery Studio Visualizer** bietet Betrachtung und grundlegende Analyse; fortgeschrittene Simulationen benötigen laut Hersteller überwiegend eine bezahlte Lizenz. Er ist daher kein belegter kostenloser Ersatz für das HypoGen-Training. [Offizielle Produktseite](https://www.3ds.com/products/biovia/discovery-studio). Ebenso stellt der kostenlose akademische **Maestro Viewer** keine Moleküleigenschaftsvorhersagen oder Simulationen bereit. Für Phase ist eine tatsächlich Phase einschließende Lizenz erforderlich; eine Academic Site License ist ein offizieller Zugangsweg. [Schrödinger Academic Research & Teaching](https://www.schrodinger.com/life-science/use-cases/academics/), [Academic-Site-License-Broschüre](https://newsite.schrodinger.com/wp-content/uploads/2024/01/23_510_Academic-Site-License-Flyer_Sales_R7-3_Digital.pdf).

Es wurde kein Kauf, Testzugang, Downloadvertrag oder Kontoantrag ausgelöst. Ein rechtmäßig zugänglicher aktueller Catalyst-Nachfolger erlaubt methodisch nahe neue Rechnungen; die unveränderte Reproduktion eines nicht vollständig erhaltenen historischen Laufs ist damit nicht zugesichert.

## 8. Was real rechnerisch möglich bleibt

1. **Das publizierte Modell numerisch prüfen**, sobald ein vollständiger nativer Export vorliegt: historische Tabellenwerte als Referenz verwenden, identische Moleküle anpassen und Abweichungen von Geometrie, Fit und Schwellenwert getrennt ausweisen. Ein erfolgreicher Trainingsfit allein genügt nicht als Identitätsnachweis.
2. **Die historische Arbeitsweise mit offengelegten Annahmen nachbauen:** Grundgerüst und Merkmale gemäß Quelle fixieren, Konformere unter dokumentierter Energiedefinition erzeugen, die übrigen Merkmale quantitativ optimieren, Ausschlussvolumina ausdrücklich neu festlegen und neue Kandidaten im selben Verfahren berechnen. Ergebnisname: *eigene Rekonstruktion nach Kraft & Eichenberger* beziehungsweise *eigenes quantitatives Marine-Modell*.
3. **Mit offenen 3D-Werkzeugen eigenständige Hypothesen rechnen:** Konformer, Featurezuordnung, geometrisches Matching und Exklusionsprüfung sind unabhängig von einer Darstellung echte Berechnungen. Eine darüber trainierte Schwellenfunktion wäre ein neues Modell, dessen Daten und Validierung separat dokumentiert werden müssen. Beispiel für eine explizite programmierbare Repräsentation: [RDKit Pharm3D](https://www.rdkit.org/docs/source/rdkit.Chem.Pharm3D.html). Ihre Featuredefinitionen sind nicht automatisch die Catalyst-Definitionen.
4. **Die erreichbaren Supplemente weiter bibliographisch prüfen**, insbesondere 2010 und 2023. Ihre Existenz / Inhalte bleiben eine überprüfbare offene Recherchefrage. Erst ein tatsächlich gelesener Export rechtfertigt den Status „Originalgeometrie vorhanden“.

Für neue Moleküle muss das Ergebnis als geometrischer Fit, modellbasierte quantitative Schätzung oder experimentell bestätigter Befund getrennt ausgewiesen werden. Keine dieser Rechnungen setzt einen bekannten Geruchsrezeptor voraus; ein späteres Protein-Docking wäre ein weiterer Modelltyp und reproduzierte die ligandbasierten Originalmodelle nicht.

**Arbeitsentscheidung:** Die Originaltreue hat zuerst eine Daten- und Provenienzprüfung, dann einen überprüfbaren Reproduktionsversuch zur Voraussetzung. Solange die genannten Parameter fehlen, ist eine echte neue 3D-Rechnung möglich, ein numerisch identisches Originalmodell jedoch nicht nachgewiesen. Ein bloß ähnliches Kugelbild beantwortet diese Frage nicht.
