from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass


PREFIXES = """PREFIX ex: <http://example.org/>
PREFIX schema: <https://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>"""


@dataclass(frozen=True)
class EntityMatch:
    token: str
    uri: str


SUPER_CLASSES = [
    EntityMatch("antiheld", "ex:Antihero"),
    EntityMatch("superheld", "ex:Superhero"),
]

TEAMS = [
    EntityMatch("justice league", "ex:JusticeLeague"),
    EntityMatch("x men", "ex:XMen"),
    EntityMatch("avengers", "ex:Avengers"),
]

PUBLISHERS = [
    EntityMatch("dc comics", "ex:DCComics"),
    EntityMatch("marvel", "ex:Marvel"),
]

POWERS = [
    EntityMatch("super strength", "ex:SuperStrength"),
    EntityMatch("flight", "ex:Flight"),
    EntityMatch("fliegen", "ex:Flight"),
]

CITIES = [
    EntityMatch("new york city", "ex:NewYorkCity"),
    EntityMatch("gotham city", "ex:GothamCity"),
]

SPECIES = [
    EntityMatch("kryptonian", "ex:Kryptonian"),
    EntityMatch("mutant", "ex:Mutant"),
]

PEOPLE = [
    EntityMatch("spider man", "ex:SpiderMan"),
    EntityMatch("batman", "ex:Batman"),
]

DIETS = [
    EntityMatch("vegetar", "ex:Vegetarian"),
    EntityMatch("vegan", "ex:Vegan"),
]

INGREDIENTS = [
    EntityMatch("soy sauce", "ex:SoySauce"),
    EntityMatch("chickpeas", "ex:Chickpeas"),
    EntityMatch("tofu", "ex:Tofu"),
    EntityMatch("rice", "ex:Rice"),
]

MEAL_TYPES = [
    EntityMatch("breakfast", "ex:Breakfast"),
    EntityMatch("fruehstueck", "ex:Breakfast"),
    EntityMatch("dinner", "ex:Dinner"),
]

CUISINES = [
    EntityMatch("italien", "ex:Italian"),
    EntityMatch("japan", "ex:Japanese"),
]

DIFFICULTIES = [
    EntityMatch("easy", "ex:Easy"),
]

NUMBER_WORDS = {
    "null": 0,
    "ein": 1,
    "eine": 1,
    "zwei": 2,
    "drei": 3,
    "vier": 4,
    "fuenf": 5,
    "funf": 5,
    "sechs": 6,
    "sieben": 7,
    "acht": 8,
    "neun": 9,
    "zehn": 10,
}


def generate_sparql(question: dict[str, object]) -> str:
    text = normalize(str(question["question_de"]))
    graph = str(question["graph"])
    if graph == "superhero_universe":
        return generate_superhero_query(text)
    if graph == "recipes_100":
        return generate_recipe_query(text)
    return ""


def normalize(text: str) -> str:
    text = text.lower()
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "-": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def generate_superhero_query(text: str) -> str:
    if "pro rolle" in text:
        return superhero_count_by_role()
    if "pro publisher" in text:
        return superhero_count_by_publisher()
    if "publisher" in text and "mehr als" in text:
        return superhero_publishers_over(parse_number(text, default=10))
    if "mindestens" in text and "power" in text:
        return superhero_min_power_count(parse_number(text, default=2))
    if "ersten auftritt" in text or "erstmals" in text:
        if "vor" in text:
            return superhero_first_appearance("<", parse_number(text, default=1970))
        return superhero_first_appearance(">=", parse_number(text, default=1980))
    if "gegner" in text:
        person = require_match(text, PEOPLE)
        return superhero_relation(person.uri, "enemy", "ex:enemyOf")
    if "verbuend" in text:
        person = require_match(text, PEOPLE)
        return superhero_relation(person.uri, "ally", "ex:allyOf")
    if "artefakt" in text:
        return superhero_name_conditions(["?x ex:usesArtifact ?artifact ."])

    conditions: list[str] = []
    if class_match := find_match(text, SUPER_CLASSES):
        conditions.append(f"?x a {class_match.uri} .")
    if team := find_match(text, TEAMS):
        conditions.append(f"?x ex:memberOf {team.uri} .")
    if publisher := find_match(text, PUBLISHERS):
        conditions.append(f"?x ex:publishedBy {publisher.uri} .")
    if power := find_match(text, POWERS):
        conditions.append(f"?x ex:hasPower {power.uri} .")
    if city := find_match(text, CITIES):
        conditions.append(f"?x ex:operatesIn {city.uri} .")
    if species := find_match(text, SPECIES):
        conditions.append(f"?x ex:species {species.uri} .")

    if not conditions:
        return ""
    return superhero_name_conditions(conditions)


def generate_recipe_query(text: str) -> str:
    if "pro diet" in text or "diet typen" in text:
        return recipe_count_by_diet()
    if "durchschnitt" in text and "kalorien" in text:
        threshold = parse_number(text, default=None) if "mehr als" in text else None
        return recipe_avg_calories_by_cuisine(threshold)
    if "pro cuisine" in text:
        return recipe_count_by_cuisine()
    if "mindestens" in text and "zutaten" in text:
        return recipe_min_ingredient_count(parse_number(text, default=6))
    if "gesamtzeit" in text or "minuten" in text:
        if "zwischen" in text:
            numbers = parse_numbers(text)
            minimum, maximum = (numbers + [20, 35])[:2]
            return recipe_time_between(minimum, maximum)
        return recipe_numeric_filter("ex:totalTimeMinutes", "time", "<=", parse_number(text, default=30))
    if "spice level" in text:
        if "genau" in text:
            return recipe_numeric_filter("ex:spiceLevel", "level", "=", parse_number(text, default=0))
        return recipe_numeric_filter("ex:spiceLevel", "level", ">=", parse_number(text, default=3), descending=True)
    if "kalorien" in text:
        return recipe_numeric_filter("ex:calories", "calories", "<", parse_number(text, default=500))
    if "portionen" in text:
        return recipe_numeric_filter("ex:servings", "servings", ">", parse_number(text, default=3), descending=True)

    conditions: list[str] = []
    for ingredient in find_all_matches(text, INGREDIENTS):
        conditions.append(f"?r ex:hasIngredient {ingredient.uri} .")
    if diet := find_match(text, DIETS):
        conditions.append(f"?r ex:diet {diet.uri} .")
    if meal_type := find_match(text, MEAL_TYPES):
        conditions.append(f"?r ex:mealType {meal_type.uri} .")
    if cuisine := find_match(text, CUISINES):
        conditions.append(f"?r ex:cuisineType {cuisine.uri} .")
    if difficulty := find_match(text, DIFFICULTIES):
        conditions.append(f"?r ex:difficulty {difficulty.uri} .")

    if not conditions:
        return ""
    return recipe_name_conditions(conditions)


def superhero_name_conditions(conditions: Iterable[str]) -> str:
    condition_text = indent_conditions([*conditions, "?x schema:name ?name ."])
    return f"""{PREFIXES}

SELECT ?name
WHERE {{
{condition_text}
}}
ORDER BY ?name"""


def superhero_relation(person_uri: str, relation_name: str, property_uri: str) -> str:
    return f"""{PREFIXES}

SELECT ?{relation_name}Name
WHERE {{
  {person_uri} {property_uri} ?{relation_name} .
  ?{relation_name} schema:name ?{relation_name}Name .
}}
ORDER BY ?{relation_name}Name"""


def superhero_min_power_count(minimum: int) -> str:
    return f"""{PREFIXES}

SELECT ?name (COUNT(?power) AS ?powerCount)
WHERE {{
  ?x schema:name ?name ;
     ex:hasPower ?power .
}}
GROUP BY ?x ?name
HAVING (COUNT(?power) >= {minimum})
ORDER BY DESC(?powerCount) ?name"""


def superhero_count_by_publisher() -> str:
    return f"""{PREFIXES}

SELECT ?publisherName (COUNT(?x) AS ?count)
WHERE {{
  ?x ex:publishedBy ?publisher .
  ?publisher schema:name ?publisherName .
}}
GROUP BY ?publisherName
ORDER BY DESC(?count) ?publisherName"""


def superhero_publishers_over(minimum: int) -> str:
    return f"""{PREFIXES}

SELECT ?publisherName (COUNT(?x) AS ?count)
WHERE {{
  ?x ex:publishedBy ?publisher .
  ?publisher schema:name ?publisherName .
}}
GROUP BY ?publisherName
HAVING (COUNT(?x) > {minimum})
ORDER BY DESC(?count) ?publisherName"""


def superhero_count_by_role() -> str:
    return f"""{PREFIXES}

SELECT ?role (COUNT(?x) AS ?count)
WHERE {{
  ?x ex:roleLabel ?role .
}}
GROUP BY ?role
ORDER BY DESC(?count) ?role"""


def superhero_first_appearance(operator: str, year: int) -> str:
    return f"""{PREFIXES}

SELECT ?name ?year
WHERE {{
  ?x schema:name ?name ;
     ex:firstAppearanceYear ?year .
  FILTER(?year {operator} "{year}"^^xsd:gYear)
}}
ORDER BY ?year ?name"""


def recipe_name_conditions(conditions: Iterable[str]) -> str:
    condition_text = indent_conditions(["?r a schema:Recipe .", *conditions, "?r schema:name ?name ."])
    return f"""{PREFIXES}

SELECT ?name
WHERE {{
{condition_text}
}}
ORDER BY ?name"""


def recipe_numeric_filter(
    property_uri: str,
    variable_name: str,
    operator: str,
    value: int,
    *,
    descending: bool = False,
) -> str:
    order = f"DESC(?{variable_name}) ?name" if descending else f"?{variable_name} ?name"
    return f"""{PREFIXES}

SELECT ?name ?{variable_name}
WHERE {{
  ?r a schema:Recipe ;
     schema:name ?name ;
     {property_uri} ?{variable_name} .
  FILTER(?{variable_name} {operator} {value})
}}
ORDER BY {order}"""


def recipe_time_between(minimum: int, maximum: int) -> str:
    return f"""{PREFIXES}

SELECT ?name ?time
WHERE {{
  ?r a schema:Recipe ;
     schema:name ?name ;
     ex:totalTimeMinutes ?time .
  FILTER(?time >= {minimum} && ?time <= {maximum})
}}
ORDER BY ?time ?name"""


def recipe_count_by_diet() -> str:
    return f"""{PREFIXES}

SELECT ?dietName (COUNT(?r) AS ?count)
WHERE {{
  ?r a schema:Recipe ;
     ex:diet ?diet .
  ?diet schema:name ?dietName .
}}
GROUP BY ?dietName
ORDER BY DESC(?count) ?dietName"""


def recipe_count_by_cuisine() -> str:
    return f"""{PREFIXES}

SELECT ?cuisineName (COUNT(?r) AS ?count)
WHERE {{
  ?r a schema:Recipe ;
     ex:cuisineType ?cuisine .
  ?cuisine schema:name ?cuisineName .
}}
GROUP BY ?cuisineName
ORDER BY DESC(?count) ?cuisineName"""


def recipe_avg_calories_by_cuisine(threshold: int | None = None) -> str:
    having = f"\nHAVING (AVG(?cal) > {threshold})" if threshold is not None else ""
    return f"""{PREFIXES}

SELECT ?cuisineName (AVG(?cal) AS ?avgCalories)
WHERE {{
  ?r a schema:Recipe ;
     ex:cuisineType ?cuisine ;
     ex:calories ?cal .
  ?cuisine schema:name ?cuisineName .
}}
GROUP BY ?cuisineName{having}
ORDER BY DESC(?avgCalories) ?cuisineName"""


def recipe_min_ingredient_count(minimum: int) -> str:
    return f"""{PREFIXES}

SELECT ?name (COUNT(?ingredient) AS ?ingredientCount)
WHERE {{
  ?r a schema:Recipe ;
     schema:name ?name ;
     ex:hasIngredient ?ingredient .
}}
GROUP BY ?r ?name
HAVING (COUNT(?ingredient) >= {minimum})
ORDER BY DESC(?ingredientCount) ?name"""


def indent_conditions(conditions: list[str]) -> str:
    return "\n".join(f"  {condition}" for condition in conditions)


def find_match(text: str, matches: Iterable[EntityMatch]) -> EntityMatch | None:
    return next((match for match in matches if match.token in text), None)


def find_all_matches(text: str, matches: Iterable[EntityMatch]) -> list[EntityMatch]:
    return [match for match in matches if match.token in text]


def require_match(text: str, matches: Iterable[EntityMatch]) -> EntityMatch:
    if match := find_match(text, matches):
        return match
    raise ValueError(f"No entity match for question: {text}")


def parse_numbers(text: str) -> list[int]:
    found = [int(number) for number in re.findall(r"\d+", text)]
    found.extend(value for word, value in NUMBER_WORDS.items() if re.search(rf"\b{word}\b", text))
    return found


def parse_number(text: str, *, default: int | None) -> int:
    numbers = parse_numbers(text)
    if numbers:
        return numbers[0]
    if default is None:
        raise ValueError(f"No number found in question: {text}")
    return default
