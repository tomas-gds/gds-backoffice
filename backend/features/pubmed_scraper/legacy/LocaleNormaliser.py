import re
import json
from babel import Locale
import pycountry
from pathlib import Path

class LocaleNormaliser:
    VALID_SHORT = {"USA", "UK", "UAE"}

    def __init__(self,country):
        self.country_names = self._load_country_names()
        self.country = country
        self.translated_country_name = self._translate_country_local()

    def _load_country_names(self, path=None):
        path = Path(path) if path is not None else Path(__file__).resolve().parent / "country_names.json"

        with open(path, "r", encoding="utf-8") as f:
            return set(json.load(f))

    def _translate_country_local(self):
        COUNTRY_TO_LANG = {
            "germany": "de",
            "france": "fr",
            "netherlands": "nl",
            "spain": "es",
            "italy": "it",
            "portugal": "pt",
            "brazil": "pt",
            "austria": "de",
            "switzerland": "de",
            "belgium": "nl",
            "united states": "en",
            "uk": "en",
            "united kingdom": "en",
        }

        try:
            country = pycountry.countries.lookup(self.country)
            lang = COUNTRY_TO_LANG.get(self.country.lower())

            if not lang:
                return None

            locale = Locale.parse(lang)
            return locale.territories.get(country.alpha_2)

        except:
            return None


    def is_country(self, name):
        if not isinstance(name, str):
            return False

        name = name.strip().lower()
        return name in self.country_names

    def clean_city(self,city):
        if not isinstance(city, str):
            return ""

        # keep unicode letters + spaces + hyphens
        city = re.sub(r"[^\w\s\-]", "", city, flags=re.UNICODE)

        # remove digits separately
        city = re.sub(r"\d", "", city)

        city = re.sub(r"\s+", " ", city).strip()

        return city

    def _is_bundesland(self, str):
        bundeslaender = [
            "Baden-Württemberg",
            "Bavaria", "Bayern",
            # "Berlin", # also a city
            "Brandenburg",
            "Bremen",
            # "Hamburg", # also a city
            "Hesse", "Hessen",
            "Lower Saxony", "Niedersachsen",
            "Mecklenburg-Western Pomerania", "Mecklenburg-Vorpommern",
            "North Rhine-Westphalia", "Nordrhein-Westfalen",
            "Rhineland-Palatinate", "Rheinland-Pfalz",
            "Saarland",
            "Saxony", "Sachsen",
            "Saxony-Anhalt", "Sachsen-Anhalt",
            "Schleswig-Holstein",
            "Thuringia", "Thüringen"
        ]
        return str in bundeslaender

    def extract_countries_cities(self, affiliations_str, not_target_country=False):
        EXCLUDE_WORDS = [
            "univer",
            "hospital",
            "department",
            "faculty",
            "institute",
            "center",
            "centre",
            "clinic",
            "division",
            "school",
            "program",
            "research",
            "service",
            "division",
            "campus",
            "klinik",
            "clinic",
            "europ",
            "medic"
        ]

        CITY_TRANSLATIONS = {
            "münchen": "München",
            "minich": "München",
            "munchen": "München",
            "biberach": "Biberach An Der Riss",
            "muenster": "Münster",
            "hannover": "Hanover",
            "goettingen": "Göttingen",
            "frankfurt": "Frankfurt Am Main",
            "frankfurtmain": "Frankfurt Am Main",
            "freiburg": "Freiburg Im Breisgau",
            "ingelheim": "Ingelheim Am Rhein",
            "duesseldorf": "Düsseldorf",
            "koln": "Cologne",
            "köln": "Cologne",
            "wien": "Vienna",
            "roma": "Rome",
            "firenze": "Florence",
            "napoli": "Naples",
            "milano": "Milan",
        }



        if not isinstance(affiliations_str, str) or not affiliations_str.strip():
            return ["", ""]

        countries = set()
        cities = set()

        for aff in affiliations_str.split(";"):
            original_aff = aff
            aff = aff.strip().lower()
            if not aff:
                continue

            parts = [p.strip() for p in aff.split(",") if p.strip()]
            if len(parts) < 2:
                continue

            country = parts[-1].replace(".", "").replace(":", "").strip()
            country = country.replace("the netherlands", "netherlands")

            if "@" in country:
                country = country.replace("electronic address", "").strip()
                if " " in country:
                    country = country.rsplit(" ", 1)[0].strip()

            if country == "united states of america":
                country = "USA"

            if country == "united kingdom":
                country = "UK"

            if not_target_country:
                if self.is_country(country):
                    city = self.clean_city(parts[-2])
                    if country in ["china", "people's republic of china", "p r china", "pr china"]:
                        country = "china"

                    if country == "netherlands":
                        country = "the netherlands"

                    if country.upper() in self.VALID_SHORT:
                        countries.add(country.upper())
                    else:
                        countries.add(country.title())

                    if city and len(city) > 2 and not any(word in city for word in EXCLUDE_WORDS):
                        if city in CITY_TRANSLATIONS.keys():
                            city = CITY_TRANSLATIONS[city]

                        if not self._is_bundesland(city.title()):
                            cities.add(city.title())
                        elif len(parts)>= 3 and not any(word in city for word in parts[-3]):
                            cities.add(parts[-3])
                elif self.check_if_usa(original_aff):
                    countries = {"USA"}
                    cities.add(parts[-2])


            else:

                original_country = self.country.lower()
                translated_country = (self.translated_country_name or "").lower()

                if original_country in aff or (translated_country and translated_country in aff):
                    city = self.clean_city(parts[-2])
                    if city and len(city) > 2 and not any(word in city for word in EXCLUDE_WORDS):
                        if city in CITY_TRANSLATIONS.keys():
                            city = CITY_TRANSLATIONS[city]
                        if not self._is_bundesland(city.title()):
                            cities.add(city.title())
                        elif len(parts)>= 3 and not any(word in city for word in parts[-3]):
                            cities.add(parts[-3])

                countries = {self.country}

        return [", ".join(countries), ", ".join(cities)]

    def check_if_usa(self, aff):
        us_state_abbreviations = {
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
        }

        parts = [p.strip() for p in aff.split(",") if p.strip()]
        if not parts:
            return False

        last_part = re.sub(r"[\W_]+", "", parts[-1])
        return last_part in us_state_abbreviations