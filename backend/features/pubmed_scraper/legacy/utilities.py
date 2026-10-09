import pycountry
import json
import os
import re
from itertools import product

from .LocaleNormaliser import LocaleNormaliser
from .NameNormaliser import NameNormaliser

def build_country_file(path="country_names.json"):
    # Function used to build the country_names.json file with the names of all the countries in the world (including variations)

    # If file already exists, do not overwrite
    if os.path.exists(path):
        print(f"{path} already exists. Skipping creation.")
        return

    country_names = set()

    for country in pycountry.countries:
        if hasattr(country, "name") and country.name:
            country_names.add(country.name.lower())

        if hasattr(country, "official_name") and country.official_name:
            country_names.add(country.official_name.lower())

        if hasattr(country, "common_name") and country.common_name:
            country_names.add(country.common_name.lower())

    # Optional additions
    country_names.update({
        "usa", "u.s.a", "u.s.a.",
        "us", "u.s", "u.s.",
        "uk", "u.k", "u.k.",
    })

    # Save as sorted list (nice for debugging)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(country_names), f, indent=2)

    print(f"Saved {len(country_names)} country names to {path}")

def check_spellinng(text: str) -> str:
    pairs = [
        ("tumour", "tumor"),
        ("anaesthesia", "anesthesia"),
        ("anemia", "anaemia"),
        ("anemic", "anaemic"),
        ("hematologic", "haematologic"),
        ("center", "centre"),
        ("leukemia", "leukaemia"),
        ("hypophosphatemia", "hypophosphataemia"),
        ("hypophosphatemic", "hypophosphataemic"),
        ("pediatric", "paediatric"),
        ("organisation", "organization"),
        ("immunisation", "immunization"),
        ("oestrogen", "estrogen"),
        ("oestrogenic", "estrogenic"),
        ("signalling", "signaling"),
    ]

    alternatives = {}
    for first, second in pairs:
        alternatives[first] = second
        alternatives[second] = first

    pattern = re.compile(
        r"\b(?:" + "|".join(map(re.escape, alternatives)) + r")\b",
        re.IGNORECASE,
    )

    text = text.strip()
    matches = list(pattern.finditer(text))

    if not matches:
        return text

    choices = [
        (match.group(), alternatives[match.group().lower()])
        for match in matches
    ]

    variants = []
    for replacements in product(*choices):
        parts = []
        previous_end = 0

        for match, replacement in zip(matches, replacements):
            parts.append(text[previous_end:match.start()])
            parts.append(replacement)
            previous_end = match.end()

        parts.append(text[previous_end:])
        variants.append("".join(parts))

    return "(" + " OR ".join(dict.fromkeys(variants)) + ")"

def fix_query_affil(search,country):
    if country.lower() in ["united kingdom", "uk"]:
        query = f"""({search}) AND (UK[Affiliation] OR "United Kingdom"[Affiliation] OR "Scotland"[Affiliation] OR "Nothern Ireland"[Affiliation])"""
    elif "netherlands" in country.lower():
        query = f"""({search}) AND (Netherlands[Affiliation] OR "The Netherlands"[Affiliation])"""
    elif "spain" in country.lower():
        query = f"""({search}) AND (Spain[Affiliation] OR España[Affiliation])"""
    elif "germany" in country.lower():
        query = f"""({search}) AND (Germany[Affiliation] OR Deutschland[Affiliation])"""
    elif "italy" in country.lower():
        query = f"""({search}) AND (Italy[Affiliation] OR Italia[Affiliation])"""
    elif "switzerland" in country.lower():
        query = f"""({search}) AND (Switzerland[Affiliation] OR Schweiz[Affiliation]) OR Suisse[Affiliation]) OR Svizzera[Affiliation])"""
    else:
        query = f"({search}) AND ({country}[Affiliation])"
    
    return query

def build_country_aliases(country,locale_normaliser,name_normaliser=None):
    country_aliases = set()

    if country.lower() in ["usa", "uk", "uae"]:
        country = country.upper()

    country_aliases.add(country.lower())
    translated_country_name = locale_normaliser.translated_country_name

    if translated_country_name:
        country_aliases.add(translated_country_name.lower())
    if country.lower() in ["uk", "united kingdom"]:
        country_aliases.add("united kingdom")
        country_aliases.add("uk")
        country_aliases.add("scotland")
        country_aliases.add("nothern ireland")

    if country.lower() == "germany":
        country_aliases.add("deutschland")

    if country.lower() == "italy":
        country_aliases.add("italia")

    if country.lower() == "spain":
        country_aliases.add("españa")

    if "netherlands" in country.lower():
        country_aliases.add("the netherlands")
        country_aliases.add("netherlands")

    if country.lower() == "switzerland":
        country_aliases.add("schweiz")
        country_aliases.add("suisse")
        country_aliases.add("svizzera")

    if name_normaliser:
        name_normaliser.country_aliases = country_aliases
        return country_aliases, locale_normaliser,name_normaliser
    else:
        return country_aliases, locale_normaliser

