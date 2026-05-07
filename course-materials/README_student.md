# README für Studierende: Text-to-SPARQL Challenge

## Ziel

In dieser Challenge entwickelt ihr in Gruppen ein System, das natürlichsprachliche Fragen automatisch in **SPARQL-Queries** überführt, diese auf einem RDF-Graphen ausführt und die Resultate in einer definierten JSON-Struktur zurückgibt.

Die Aufgabe ist als **Prototyp-Challenge** angelegt und soll **innerhalb von maximal vier Lektionen** lösbar sein.

---

## Ihr bekommt

- `superhero_universe.ttl`
- `recipes_100.ttl`
- `dev_set.json`
- `test_set_public.json`
- `query.py`
- `submission_template.json`
- `submission_template.py`
- optional weitere Hilfsdateien wie `schema_overview.md`

---

## Wozu dienen die Dateien?

### RDF-Datengraphen
- `superhero_universe.ttl`
- `recipes_100.ttl`

Diese Dateien enthalten die RDF-Daten, auf denen eure SPARQL-Queries ausgeführt werden.

### Dev-Set
- `dev_set.json`

Das Dev-Set dient zum:
- Verstehen der Aufgabe
- Testen eurer Pipeline
- Prompting
- Debugging
- Vergleichen mit Referenzqueries und Goldresultaten

### Test-Set
- `test_set_public.json`

Dieses Set dient für die finale Abgabe.  
Es enthält nur die Fragen. Die Goldqueries und Goldresultate bleiben bei der Lehrperson.

### Templates
- `query.py`
- `submission_template.py`
- `submission_template.json`

Diese Dateien zeigen:
- wie ein Turtle-Graph geladen wird
- wie SPARQL mit Python ausgeführt werden kann
- wie das erwartete Abgabeformat aussieht

---

## Projektstruktur (Vorschlag)

```text
hackathon/
├── knowledge-graphs/
│   ├── superhero_universe.ttl
│   └── recipes_100.ttl
├── dev-test-set/
│   ├── dev_set.json
│   └── test_set_public.json
├── templates/
│   ├── query.py
│   ├── submission_template.json
│   ├── submission_template.json
│   └── evaluate_all_submissions.py
├── src/
│   ├── main.py
│   ├── pipeline.py
│   └── prompts.py
├── submissions/
│   └── submission.json
├── README_student.md
├── schema_overview.md
```

---

## Technischer Rahmen

Ihr dürft frei entscheiden, wie ihr eure Lösung aufbaut.

Erlaubt sind zum Beispiel:
- Prompt Engineering
- Few-shot Prompting
- Ontologie-Kontext im Prompt
- mehrstufige Pipelines
- regelbasierte Vorverarbeitung
- Query-Reparatur
- zusätzliche NLP-Techniken wie NER, NED, Entity Linking oder andere Verfahren

Ihr dürft arbeiten auf:
- DGX Spark Workstations
- lokalen Rechnern
- FHGR-GPU-Servern

Als möglicher Startpunkt kann **LLM Studio** verwendet werden. Ihr dürft aber auch eigene Python-Lösungen bauen.

---

## Setup mit uv

## 1. uv installieren

### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Alternativ:

```bash
wget -qO- https://astral.sh/uv/install.sh | sh
```

### Windows PowerShell

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 2. Projektordner erstellen

```bash
mkdir hackathon
cd hackathon
```

Kopiert danach die bereitgestellten Dateien in diesen Ordner.

## 3. Projekt initialisieren

```bash
uv init --bare
```

## 4. Abhängigkeiten installieren

Für die Basis genügt:

```bash
uv add rdflib
```

Wenn ihr zusätzlich APIs oder andere Bibliotheken verwendet, könnt ihr diese ergänzen.

## 5. Umgebung synchronisieren

```bash
uv sync
```

## 6. Skripte ausführen

```bash
uv run python query.py
uv run python lmstudio.py
uv run python submission_template.py
```

## 7. LM Studio installieren (headless)
Siehe die Anleitung:

  https://lmstudio.ai/docs/developer/core/headless
  https://build.nvidia.com/spark/lm-studio/instructions


Variante um einen SSH Tunnel zum DGX-Spark herzustellen:

  ssh -L 1234:127.0.0.1:1234 BENUTZERNAME@IP-ADRESSE-DGX

---

## Empfohlener Arbeitsablauf

### Schritt 1: Graphen verstehen
- Öffnet `dev_set.json`
- schaut euch Fragen, Referenzqueries und Goldresultate an
- testet Beispielqueries mit `query.py`

### Schritt 2: Pipeline bauen
Entwickelt eine Funktion, die:
1. eine Frage liest
2. eine SPARQL-Query erzeugt
3. die Query auf dem richtigen Graphen ausführt
4. das Resultat zurückgibt

### Schritt 3: Auf Dev-Set testen
Prüft eure Lösung zuerst mit dem Dev-Set.  
Ziel ist nicht Perfektion, sondern eine robuste, nachvollziehbare Pipeline.

### Schritt 4: Test-Set bearbeiten
Wenn eure Lösung auf dem Dev-Set funktioniert, lasst sie auf dem öffentlichen Test-Set laufen und erzeugt eure finale `submission.json`.

---

## Erwartetes Abgabeformat

Die Abgabe erfolgt als **eine JSON-Datei**.  
Pro Testfrage gibt es genau ein Objekt.

Beispiel:

```json
[
  {
    "id": "test_super_01",
    "graph": "superhero_universe",
    "difficulty": "easy",
    "question_de": "Nenne alle Antiheld:innen.",
    "generated_sparql": "PREFIX ex: <http://example.org/> ...",
    "execution_success": true,
    "predicted_result": [
      {"name": "Catwoman"},
      {"name": "Deadpool"},
      {"name": "Harley Quinn"}
    ]
  }
]
```

### Pflichtfelder
- `id`
- `graph`
- `difficulty`
- `question_de`
- `generated_sparql`
- `execution_success`
- `predicted_result`

### Falls die Query fehlschlägt
Dann gilt:
- `execution_success = false`
- `predicted_result = []`

---

## Was wird abgegeben?

Bitte reicht ein:

- eure `submission.json`
- den reproduzierbaren Code
- eine sehr kurze Präsentation eurer Strategie
  - Flipchart
  - oder ein Slide

Ein schriftlicher Bericht ist **nicht erforderlich**.

---

## Wie wird bewertet?

Die finale Rangliste basiert auf dem **mittleren F1-Score auf dem Hidden Test-Set**.

Wichtig:
- Die offizielle Evaluation erfolgt **zentral durch die Lehrperson**
- ihr dürft lokal auf dem Dev-Set testen
- die finale Wertung basiert aber nur auf der zentralen Auswertung gegen den Goldstandard

Mögliche zusätzliche Kennzahlen:
- Execution Rate
- F1 pro Graph
- F1 nach Schwierigkeitsgrad

---

## Kurze Präsentation

In eurer Kurzpräsentation solltet ihr knapp zeigen:

- Grundidee eurer Lösung
- Prompt- oder Pipeline-Design
- verwendete Modelle oder Tools
- eingesetzte NLP-Techniken
- eine Stärke und eine Schwäche eures Verfahrens

---

## Typische Fehlerquellen

Achtet besonders auf:
- falsche Prefixe
- nicht existierende Klassen oder Properties
- ungültige SPARQL-Syntax
- falsche JSON-Struktur
- inkonsistente Resultatformate
- leere oder unvollständige Resultate

---

## Praktische Tipps

- Beginnt einfach.
- Baut zuerst eine minimale funktionierende Pipeline.
- Nutzt das Dev-Set intensiv.
- Zusätzliche NLP-Techniken sind erlaubt, aber nicht zwingend nötig.
- Achtet darauf, dass eure Ausgabe exakt das erwartete JSON-Format hat.

---

## Minimaler Testlauf

Wenn alles korrekt eingerichtet ist, sollte mindestens Folgendes funktionieren:

```bash
uv sync
uv run python query.py
uv run python submission_template.py
```

---

## Zusammenfassung

Ziel ist ein **funktionierender Prototyp**, der:
- natürlichsprachliche Fragen verarbeitet
- SPARQL generiert
- Queries auf RDF-Daten ausführt
- Resultate in einem sauberen JSON-Format speichert

Arbeitet pragmatisch, testet früh und haltet eure Lösung reproduzierbar.
