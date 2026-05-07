# Schema Overview: Text-to-SPARQL Challenge

## Zweck

Diese Übersicht fasst die wichtigsten Klassen, Properties, Instanzen und Query-Muster der beiden RDF-Datengraphen zusammen.

Sie ist bewusst kompakt gehalten und soll euch beim:
- Verstehen der Graphen
- Formulieren von SPARQL-Queries
- Prompting eines LLM
- Mapping zwischen Frage und RDF-Struktur

unterstützen.

---

# 1. Allgemeine Prefixe

In den bereitgestellten Beispielen werden typischerweise folgende Prefixe verwendet:

```sparql
PREFIX ex: <http://example.org/>
PREFIX schema: <https://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
```

Wichtige allgemeine Patterns:
- `a` für Typzuweisung
- `schema:name` für Namen / Labels
- `FILTER(...)` für numerische oder logische Einschränkungen
- `GROUP BY`, `HAVING`, `COUNT`, `AVG` für Aggregationen

---

# 2. Superhero Graph

Datei:
- `superhero_universe.ttl`

## 2.1 Wichtige Klassen

- `ex:Superhero`
- `ex:Villain`
- `ex:Antihero`
- `ex:Civilian`
- `ex:Team`
- `ex:Power`
- `ex:Publisher`
- `ex:City`
- `ex:Nation`
- `ex:Organization`
- `ex:Artifact`
- `ex:Species`

Zusätzlich werden Figuren oft auch als `schema:Person` modelliert.

## 2.2 Wichtige Properties

- `schema:name`  
  Name einer Ressource

- `ex:realName`  
  bürgerlicher Name / Realname

- `ex:alias`  
  Alias oder Bezeichnung

- `ex:alignment`  
  grobe Einordnung, z. B. hero, villain, antihero

- `ex:hasPower`  
  Verknüpfung zu einer Power

- `ex:memberOf`  
  Mitgliedschaft in einem Team

- `ex:enemyOf`  
  Gegnerbeziehung

- `ex:allyOf`  
  Verbündet mit

- `ex:operatesIn`  
  Ort / Stadt, in der die Figur aktiv ist

- `ex:originWorld`  
  Herkunftswelt oder Herkunftsort

- `ex:publishedBy`  
  Publisher, z. B. Marvel oder DC Comics

- `ex:firstAppearanceYear`  
  erstes Auftreten als Jahr

- `ex:affiliatedWith`  
  Zugehörigkeit zu Organisationen

- `ex:usesArtifact`  
  genutztes Artefakt

- `ex:species`  
  Spezies, z. B. Human, Mutant, Kryptonian

- `ex:roleLabel`  
  Rollenbezeichnung als Literal

## 2.3 Typische Instanzen

### Figuren
- `ex:Batman`
- `ex:Superman`
- `ex:WonderWoman`
- `ex:IronMan`
- `ex:SpiderMan`
- `ex:Wolverine`
- `ex:DoctorStrange`

### Teams
- `ex:Avengers`
- `ex:JusticeLeague`
- `ex:XMen`
- `ex:FantasticFour`
- `ex:GuardiansOfTheGalaxy`

### Powers
- `ex:Flight`
- `ex:SuperStrength`
- `ex:SuperSpeed`
- `ex:Magic`
- `ex:Telepathy`
- `ex:MartialArts`

### Publisher
- `ex:Marvel`
- `ex:DCComics`

### Orte
- `ex:GothamCity`
- `ex:Metropolis`
- `ex:NewYorkCity`
- `ex:Atlantis`
- `ex:Wakanda`

### Species
- `ex:Human`
- `ex:Mutant`
- `ex:Kryptonian`
- `ex:Alien`
- `ex:Asgardian`

## 2.4 Typische Fragetypen

### Lookup
- Welche Figuren sind Superheld:innen?
- Welche Figuren gehören zu den Avengers?

### Filter
- Welche Figuren haben `ex:Flight`?
- Welche Figuren stammen von `ex:Marvel`?
- Welche Figuren operieren in `ex:GothamCity`?

### Kombinationen
- Welche Figuren gehören zu den X-Men und sind Mutant:innen?
- Welche Figuren können fliegen und stammen von Marvel?

### Relationen
- Welche Gegner:innen hat Batman?
- Welche Verbündeten hat Spider-Man?

### Aggregationen
- Wie viele Figuren gibt es pro Publisher?
- Welche Figuren haben mindestens zwei Powers?

## 2.5 Typische Query-Muster

### Alle Superheld:innen
```sparql
PREFIX ex: <http://example.org/>
PREFIX schema: <https://schema.org/>

SELECT ?name
WHERE {
  ?x a ex:Superhero ;
     schema:name ?name .
}
ORDER BY ?name
```

### Mitglieder eines Teams
```sparql
PREFIX ex: <http://example.org/>
PREFIX schema: <https://schema.org/>

SELECT ?name
WHERE {
  ?x ex:memberOf ex:Avengers ;
     schema:name ?name .
}
ORDER BY ?name
```

### Figuren mit einer Power
```sparql
PREFIX ex: <http://example.org/>
PREFIX schema: <https://schema.org/>

SELECT ?name
WHERE {
  ?x ex:hasPower ex:Flight ;
     schema:name ?name .
}
ORDER BY ?name
```

---

# 3. Recipe Graph

Datei:
- `recipes_100.ttl`

## 3.1 Wichtige Klassen

- `schema:Recipe`
- `ex:Ingredient`
- `ex:Cuisine`
- `ex:DietType`
- `ex:RecipeCategory`
- `ex:MealType`
- `ex:SkillLevel`

## 3.2 Wichtige Properties

- `schema:name`  
  Name des Rezepts oder einer Ressource

- `ex:hasIngredient`  
  Zutat eines Rezepts

- `ex:cuisineType`  
  Küchenstil / Cuisine

- `ex:prepTimeMinutes`  
  Vorbereitungszeit

- `ex:cookTimeMinutes`  
  Kochzeit

- `ex:totalTimeMinutes`  
  Gesamtzeit

- `ex:difficulty`  
  Schwierigkeitsgrad

- `ex:diet`  
  Ernährungsstil / Diet-Typ

- `ex:calories`  
  Kalorien

- `ex:servings`  
  Portionen

- `ex:mealType`  
  z. B. Breakfast, Lunch, Dinner

- `ex:recipeCategory`  
  z. B. Soup, Salad, Pasta, Stir Fry

- `ex:spiceLevel`  
  Schärfegrad

- `ex:mainProtein`  
  Hauptprotein als Literal

- `ex:countryOfOrigin`  
  Land / Küche als Literal

## 3.3 Typische Instanzen

### Zutaten
- `ex:Tofu`
- `ex:Tomato`
- `ex:Rice`
- `ex:Chickpeas`
- `ex:SoySauce`
- `ex:Chicken`
- `ex:Garlic`

### Cuisines
- `ex:Italian`
- `ex:Japanese`
- `ex:Indian`
- `ex:Mexican`
- `ex:Thai`
- `ex:French`

### Diet Types
- `ex:Vegan`
- `ex:Vegetarian`
- `ex:Pescatarian`
- `ex:Omnivore`
- `ex:HighProtein`

### Meal Types
- `ex:Breakfast`
- `ex:Lunch`
- `ex:Dinner`

### Difficulty
- `ex:Easy`
- `ex:Medium`
- `ex:Hard`

## 3.4 Typische Fragetypen

### Lookup
- Welche Rezepte sind vegan?
- Welche Rezepte enthalten Tofu?

### Filter
- Welche italienischen Rezepte gibt es?
- Welche Rezepte haben maximal 30 Minuten Gesamtzeit?
- Welche Rezepte haben Spice Level mindestens 3?

### Kombinationen
- Welche Rezepte haben Tofu und sind vegan?
- Welche Rezepte sind Breakfast und Easy?
- Welche Rezepte enthalten Rice und Soy Sauce?

### Aggregationen
- Wie viele Rezepte gibt es pro Diet-Typ?
- Wie hoch sind die durchschnittlichen Kalorien pro Cuisine?
- Welche Rezepte haben mindestens sechs Zutaten?

## 3.5 Typische Query-Muster

### Vegane Rezepte
```sparql
PREFIX ex: <http://example.org/>
PREFIX schema: <https://schema.org/>

SELECT ?name
WHERE {
  ?r a schema:Recipe ;
     ex:diet ex:Vegan ;
     schema:name ?name .
}
ORDER BY ?name
```

### Rezepte mit bestimmter Zutat
```sparql
PREFIX ex: <http://example.org/>
PREFIX schema: <https://schema.org/>

SELECT ?name
WHERE {
  ?r a schema:Recipe ;
     ex:hasIngredient ex:Tofu ;
     schema:name ?name .
}
ORDER BY ?name
```

### Rezepte mit Zeitfilter
```sparql
PREFIX ex: <http://example.org/>
PREFIX schema: <https://schema.org/>

SELECT ?name ?time
WHERE {
  ?r a schema:Recipe ;
     schema:name ?name ;
     ex:totalTimeMinutes ?time .
  FILTER(?time <= 30)
}
ORDER BY ?time ?name
```

---

# 4. Hinweise für Prompting und Mapping

Beim Prompting kann es helfen, dem Modell explizit mitzuteilen:

- welche Prefixe vorhanden sind
- welche Klassen und Properties wichtig sind
- dass nur bestehende URIs verwendet werden dürfen
- dass die Ausgabe nur SPARQL enthalten soll

Besonders nützlich sind im Prompt oft:
- zentrale Klassen
- zentrale Properties
- 2 bis 4 Beispiele aus dem Dev-Set
- Hinweis auf das gewünschte Output-Format

---

# 5. Hinweise zur Evaluation

Für die finale Bewertung zählt primär das Resultat, nicht nur die exakte Form der Query.

Wichtig:
- ungültige oder nicht ausführbare Queries führen zu `execution_success = false`
- die JSON-Struktur der Abgabe muss exakt eingehalten werden
- bei der zentralen Auswertung werden `Precision`, `Recall` und `F1` berechnet

---

# 6. Empfehlung

Beginnt mit einfachen Query-Typen:
- Lookup
- einzelner Filter
- Kombination zweier Bedingungen

Erst danach:
- Aggregationen
- schwierigere Prompting-Strategien
- zusätzliche NLP-Techniken

Eine einfache, stabile Lösung ist für diese Challenge oft besser als eine sehr komplexe, aber fehleranfällige Pipeline.
