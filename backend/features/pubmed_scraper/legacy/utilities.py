from itertools import islice, product
import operator
import re
import unicodedata

import pandas as pd



# ============================================================================
# Shared constants and compiled patterns
# ============================================================================

_LOWER_PARTICLES = frozenset({
    "da", "de", "del", "della", "der", "di", "la", "le",
    "van", "von", "den", "ten", "ter", "du",
})
_SURNAME_PARTICLES = _LOWER_PARTICLES | {"st", "st."}
_SPACES_RE = re.compile(r"\s+")
_PUNCTUATION_RE = re.compile(r"[^\w\s]")
_NAME_SEPARATORS_RE = re.compile(r"([-'])")
_TITLES_RE = re.compile(r"\b(dr|prof|mr|mrs|ms|md|phd|professor)\b\.?", re.IGNORECASE)
_SUFFIXES_RE = re.compile(r"(?:,\s*)?\b(jr|sr|ii|iii|iv)\b\.?", re.IGNORECASE)
_FILENAME_FORBIDDEN_RE = re.compile(r'[<>:"/\\|?*]')
_FILENAME_OTHER_RE = re.compile(r"[^A-Za-z0-9._-]")
_UNDERSCORES_RE = re.compile(r"_+")

# One source of aliases for affiliation queries and local affiliation matching.
_COUNTRY_ALIASES = {
    "united kingdom": ("UK", "United Kingdom", "Great Britain", "England", "Scotland", "Wales", "Northern Ireland"),
    "united states": ("USA", "United States", "United States of America"),
    "netherlands": ("Netherlands", "The Netherlands"),
    "spain": ("Spain", "España"),
    "germany": ("Germany", "Deutschland"),
    "italy": ("Italy", "Italia"),
    "switzerland": ("Switzerland", "Schweiz", "Suisse", "Svizzera"),
    "austria": ("Austria", "Österreich"),
    "belgium": ("Belgium", "Belgique", "België", "Belgien"),
    "denmark": ("Denmark", "Danmark"),
    "finland": ("Finland", "Suomi"),
    "norway": ("Norway", "Norge", "Noreg"),
    "sweden": ("Sweden", "Sverige"),
    "brazil": ("Brazil", "Brasil"),
    "czechia": ("Czechia", "Czech Republic"),
    "south korea": ("South Korea", "Republic of Korea"),
    "united arab emirates": ("United Arab Emirates", "UAE"),
}

_COUNTRY_KEYS = {
    "uk": "united kingdom", "usa": "united states", "us": "united states",
    "united states of america": "united states", "uae": "united arab emirates",
    "czech republic": "czechia", "republic of korea": "south korea",
}

_SPELLING_PAIRS = (
    ("tumour", "tumor"), ("anaesthesia", "anesthesia"),
    ("anemia", "anaemia"), ("anemic", "anaemic"),
    ("hematologic", "haematologic"), ("center", "centre"),
    ("leukemia", "leukaemia"), ("hypophosphatemia", "hypophosphataemia"),
    ("hypophosphatemic", "hypophosphataemic"), ("pediatric", "paediatric"),
    ("organisation", "organization"), ("immunisation", "immunization"),
    ("oestrogen", "estrogen"), ("oestrogenic", "estrogenic"),
    ("signalling", "signaling"),
)
_SPELLING_ALTERNATIVES = {
    word: alternative
    for first, second in _SPELLING_PAIRS
    for word, alternative in ((first, second), (second, first))
}
_SPELLING_RE = re.compile(
    r"\b(?:" + "|".join(map(re.escape, _SPELLING_ALTERNATIVES)) + r")\b",
    re.IGNORECASE,
)
_GERMAN_SPECIALS = frozenset("äöüÄÖÜß")


# ============================================================================
# Text normalization
# ============================================================================

def _text(value):
    """Convert a scalar text field to str, treating pandas missing values as empty."""
    if isinstance(value, str):
        return value
    if value is None or pd.isna(value):
        return ""
    return str(value)


def norm_spaces(s):
    return _SPACES_RE.sub(" ", _text(s)).strip()


def strip_accents(s):
    return "".join(
        character for character in unicodedata.normalize("NFKD", _text(s))
        if not unicodedata.combining(character)
    )


def strip_punctuation_keep_spaces(s):
    return _PUNCTUATION_RE.sub("", _text(s))


# ============================================================================
# File names and batched processing
# ============================================================================

def sanitize_input_string(text, max_length=120):
    text = unicodedata.normalize("NFKD", _text(text)).encode("ascii", "ignore").decode("ascii")
    text = _FILENAME_FORBIDDEN_RE.sub("_", text)
    text = _SPACES_RE.sub("_", text.strip())
    text = _FILENAME_OTHER_RE.sub("_", text)
    text = _UNDERSCORES_RE.sub("_", text).strip("._") or "unknown"
    return text[:max_length]


def chunked(iterable, n):
    """Yield lists of at most n items without materializing the whole iterable."""
    n = operator.index(n)
    if n <= 0:
        raise ValueError("Chunk size must be a positive integer.")
    iterator = iter(iterable)
    while True:
        batch = list(islice(iterator, n))
        if not batch:
            return
        yield batch


# ============================================================================
# Name formatting and parsing
# ============================================================================

def smart_title(text):
    """Preserve the existing capitalization of particles, hyphens and apostrophes."""
    result = []
    for word in _text(text).split():
        if word.lower() in _LOWER_PARTICLES:
            result.append(word.lower())
        else:
            result.append("".join(
                part if part in {"-", "'"} else part.capitalize()
                for part in _NAME_SEPARATORS_RE.split(word)
            ))
    return " ".join(result)


def normalize_initials(text):
    return "".join(character for character in _text(text).upper() if character.isalpha())


def token_is_initial(tok, *, allow_dots=True):
    """Check a single letter; allow_dots=False replaces token_is_initial(, allow_dots=False).

    The default accepts surrounding whitespace and dots, as before. Strict mode
    tests the original text without removing whitespace or punctuation.
    """
    tok = _text(tok)
    if allow_dots:
        tok = tok.strip().replace(".", "")
    return len(tok) == 1 and tok.isalpha()


def split_first_name_tokens(first_name):
    return strip_accents(first_name).lower().replace("-", " ").split()


def strip_titles_suffixes(name):
    return norm_spaces(_SUFFIXES_RE.sub("", _TITLES_RE.sub("", _text(name))))


def _split_name_parts(name):
    """Share surname detection while leaving display/strict formatting to callers."""
    if "," in name:
        surname, given = name.split(",", 1)
        return surname.strip(), given.split()
    tokens = name.split()
    if not tokens:
        return "", []
    if len(tokens) == 1:
        return tokens[0], []
    # Preserve the original surname-first heuristic, including dotted initials.
    if len(tokens) == 2 and len(tokens[1].replace(".", "")) == 1:
        return tokens[0], [tokens[1]]
    surname_start = len(tokens) - 1
    while surname_start > 0 and tokens[surname_start - 1].lower() in _SURNAME_PARTICLES:
        surname_start -= 1
    return " ".join(tokens[surname_start:]), tokens[:surname_start]


def _token_initials(tokens):
    return "".join(token[0] for token in tokens if token and token[0].isalpha())


def parse_name(name, *, strict=False):
    """Parse a name using one shared surname-detection implementation.

    strict=False: (display surname, uppercase initials), e.g. ("Smith", "JA").
    strict=True: (normalized surname, first name, middle initials), matching
    the former parse_name(, strict=True) return format and compound-name rules.
    """
    if not strict:
        surname, given_tokens = _split_name_parts(_text(name))
        return smart_title(surname), _token_initials(given_tokens).upper()

    raw_name = strip_titles_suffixes(name)
    normalized = norm_spaces(strip_accents(raw_name).lower().replace("-", " "))
    last_name, given_tokens = _split_name_parts(normalized)
    if not given_tokens:
        return last_name, "", ""
    if "," in raw_name:
        return last_name, given_tokens[0], _token_initials(given_tokens[1:])
    tokens = normalized.split()
    if len(tokens) == 2 and len(tokens[1].replace(".", "")) == 1:
        return last_name, given_tokens[0].replace(".", ""), ""
    # Preserve the existing interpretation of the second full given-name token.
    first_count = 2 if len(given_tokens) > 1 and len(given_tokens[1].replace(".", "")) > 1 else 1
    return last_name, " ".join(given_tokens[:first_count]), _token_initials(given_tokens[first_count:])


def build_author_key_from_name(name):
    """Return the existing PubMed-style key, or None for an empty name.

    Titles and suffixes share the same cleanup used by the strict parser.
    Hyphenated given names keep the original one-initial-per-token convention.
    """
    name = strip_titles_suffixes(strip_accents(name))
    if not name:
        return None
    last_name, initials = parse_name(name)
    if not last_name:
        return None
    return f"{last_name} {initials}".strip()


def display_clean(s):
    """Remove hyphens/punctuation and excess spaces without removing accents."""
    s = norm_spaces(_text(s).strip().replace("-", " "))
    return norm_spaces(strip_punctuation_keep_spaces(s))


# ============================================================================
# Name matching and canonical-name scoring
# ============================================================================

def _german_equivalents(s):
    """Matching-only German spelling reduction; do not use for displayed names."""
    return (_text(s).replace("ae", "a").replace("oe", "o").replace("ue", "u")
            .replace("ä", "a").replace("ö", "o").replace("ü", "u"))


def _match_clean(s):
    """Preserve the supplied normalization order for matching names."""
    s = _text(s).strip().replace("-", " ").casefold()
    s = _german_equivalents(strip_accents(s))
    return norm_spaces(strip_punctuation_keep_spaces(s))


def parse_for_match(name):
    """Return (first token, middle initials, last token) for matching.

    This deliberately keeps the supplied first/last-token interpretation; it is
    not the surname-particle/comma parser used by parse_name().
    """
    parts = _match_clean(name).split()
    if not parts:
        return "", "", ""
    return parts[0], "".join(part[0] for part in parts[1:-1]), parts[-1]


def first_names_compatible(a, b):
    """Preserve the existing prefix and single-initial compatibility rules."""
    a_tokens, b_tokens = split_first_name_tokens(a), split_first_name_tokens(b)
    if not a_tokens or not b_tokens:
        return False
    length = min(len(a_tokens), len(b_tokens))
    if a_tokens[:length] == b_tokens[:length]:
        return True
    if len(a_tokens) == len(b_tokens) == 1:
        a0, b0 = a_tokens[0].replace(".", ""), b_tokens[0].replace(".", "")
        return (a0 == b0
                or (token_is_initial(a0) and bool(b0) and a0 == b0[0])
                or (token_is_initial(b0) and bool(a0) and b0 == a0[0]))
    return False


def middle_compatible(mi1, mi2):
    """Keep the supplied rule: missing initials or the same leading initial match."""
    mi1, mi2 = _text(mi1), _text(mi2)
    return not (mi1 and mi2) or mi1 == mi2 or mi1[0] == mi2[0]


def one_edit_apart(a, b):
    """True for exactly one insertion, deletion or replacement; equal is False."""
    a, b = _text(a), _text(b)
    if a == b or abs(len(a) - len(b)) > 1:
        return False
    if len(a) > len(b):
        a, b = b, a
    if len(a) == len(b):
        differences = 0
        for left, right in zip(a, b):
            if left != right:
                differences += 1
                if differences > 1:
                    return False
        return differences == 1
    i = j = 0
    skipped = False
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            i += 1
            j += 1
        else:
            if skipped:
                return False
            skipped = True
            j += 1
    return True


def score_display(original_name):
    """Canonical-name ranking; larger tuples are preferred.

    Priority: German specials, cleaned length, other accents, token count,
    original length. Keep the supplied tuple order and display-cleaning rules.
    """
    original_name = _text(original_name)
    display = display_clean(original_name)
    return (
        any(character in original_name for character in _GERMAN_SPECIALS),
        len(display),
        strip_accents(original_name) != original_name,
        len(display.split()),
        len(original_name),
    )


# ============================================================================
# DataFrame author extraction and indexes
# ============================================================================

def get_clean_names(df):
    """Return unique, nonempty strings from Author, preserving their display text.

    Whitespace-only values and missing/non-string values are ignored. Remaining
    names retain their original whitespace, matching the supplied helper.
    """
    return [
        name for name in df["Author"].dropna().unique()
        if isinstance(name, str) and name.strip()
    ]


def get_initial_index(df):
    """Index full-first-name Author values by (first initial, normalized surname)."""
    initial_index = {}
    for name in get_clean_names(df):
        first, _, last = parse_for_match(name)
        if first and last and len(first) > 1:
            initial_index.setdefault((first[0], last), []).append(name)
    return initial_index


# ============================================================================
# PubMed XML authors and matching patterns
# ============================================================================

def display_name_from_xml(author):
    first_name = norm_spaces(author.get("ForeName", ""))
    last_name = norm_spaces(author.get("LastName", ""))
    return norm_spaces(f"{first_name} {last_name}")


def build_author_patterns(author):
    """Return regex strings using XML surname and given-name initials separately."""
    display_name = display_name_from_xml(author)
    if not display_name:
        return []
    patterns = [re.escape(display_name)]
    last_name = norm_spaces(author.get("LastName", ""))
    if not last_name:
        return patterns
    patterns.append(rf"\b{re.escape(last_name)}\b")
    initials = normalize_initials(author.get("Initials", ""))
    if not initials:
        initials = _token_initials(norm_spaces(author.get("ForeName", "")).split()).upper()
    if initials:
        patterns.append(rf"\b{re.escape(initials[0])}\.\s*{re.escape(last_name)}\b")
        initials_pattern = r"[.\s]*".join(map(re.escape, initials)) + r"\.?"
        patterns.append(rf"\b{initials_pattern}\b")
        patterns.append(rf"\b{re.escape(last_name)}\s*{re.escape(initials[0])}\b")
    return patterns


# ============================================================================
# PubMed query spelling
# ============================================================================

def _spelling_variants(text, matches):
    choices = [(match.group(), _SPELLING_ALTERNATIVES[match.group().lower()]) for match in matches]
    for replacements in product(*choices):
        parts, previous_end = [], 0
        for match, replacement in zip(matches, replacements):
            parts.extend((text[previous_end:match.start()], replacement))
            previous_end = match.end()
        parts.append(text[previous_end:])
        yield "".join(parts)


def check_spelling(text: str) -> str:
    """Expand spelling alternatives, preserving the historical query output.

    Expanding all whole-query combinations is still exponential. Deliberately
    avoid rewriting quoted phrases/field tags or Boolean grouping during cleanup.
    """
    text = _text(text).strip()
    matches = list(_SPELLING_RE.finditer(text))
    if not matches:
        return text
    return "(" + " OR ".join(dict.fromkeys(_spelling_variants(text, matches))) + ")"


# ============================================================================
# Country aliases and affiliation queries
# ============================================================================

def _country_aliases(country, allow_substring=False):
    country = norm_spaces(country)
    key = country.lower()
    key = _COUNTRY_KEYS.get(key, key)
    # Retain acceptance of inputs such as "The Netherlands".
    if "netherlands" in key:
        key = "netherlands"
    if allow_substring:
        for candidate in ("spain", "germany", "italy", "switzerland"):
            if candidate in key:
                key = candidate
                break
    return _COUNTRY_ALIASES.get(key, (country,))


def fix_query_affil(search, country):
    aliases = _country_aliases(country, allow_substring=True)
    terms = [f'"{alias}"[Affiliation]' if " " in alias else f"{alias}[Affiliation]" for alias in aliases]
    return f"({search}) AND ({' OR '.join(terms)})"


def build_country_aliases(country, locale_normaliser, name_normaliser=None):
    """Preserve the optional mutation and the existing two-/three-item tuple."""
    country_aliases = {alias.lower() for alias in _country_aliases(country) if alias}
    original_country = norm_spaces(country).lower()
    if original_country:
        country_aliases.add(original_country)
    translated_country = _text(locale_normaliser.translated_country_name)
    if translated_country:
        country_aliases.add(translated_country.lower())
    if name_normaliser:
        name_normaliser.country_aliases = country_aliases
        return country_aliases, locale_normaliser, name_normaliser
    return country_aliases, locale_normaliser
