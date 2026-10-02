import re
import unicodedata
from array import array
from collections import Counter, defaultdict
from difflib import SequenceMatcher

import pandas as pd
import numpy as np


ALIASES = {
    "name": ["name", "provider_name", "full_name", "doctor_name", "hospital_name", "organization_name"],
    "npi": ["npi", "national_provider_id", "provider_npi"],
    "address": ["address", "address_1", "street", "practice_address"],
    "city": ["city", "practice_city"],
    "specialty": ["specialty", "taxonomy", "taxonomy_description"],
}

EXHAUSTIVE_PAIR_LIMIT = 250_000
CANDIDATE_LIMIT = 300
MAX_RETRIEVAL_POOL = 10_000
AUTO_APPROVE_THRESHOLD = 95


def normalize(value):
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    text = text.lower().replace("&", " and ")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def duplicated_rows(frame, columns):
    selected_columns = [columns] if isinstance(columns, str) else list(columns)
    normalized = pd.DataFrame(
        {
            f"column_{index}": frame[column].map(normalize)
            for index, column in enumerate(selected_columns)
        },
        index=frame.index,
    )
    return frame.loc[normalized.duplicated(keep=False)].copy()


def prepare_search_columns(frame, columns):
    cache = frame.attrs.setdefault("normalized_search_columns", {})
    for column in columns:
        if column not in cache:
            cache[column] = frame[column].map(normalize).astype("string")
    return cache


def search_rows(frame, primary_column, columns, query="", limit=100, filters=None):
    if filters is None:
        normalized_query = normalize(query)
        active_filters = [(column, normalized_query) for column in columns]
        match_any = True
    else:
        active_filters = [
            (column, normalize(filters.get(column, "")))
            for column in columns
            if normalize(filters.get(column, ""))
        ]
        match_any = False
    if not active_filters or (match_any and not normalized_query):
        return []

    normalized_columns = prepare_search_columns(
        frame, [column for column, _ in active_filters]
    )
    contains_masks = [
        normalized_columns[column].str.contains(filter_value, regex=False, na=False)
        for column, filter_value in active_filters
    ]
    eligible = contains_masks[0].copy()
    for mask in contains_masks[1:]:
        eligible = eligible | mask if match_any else eligible & mask

    exact = pd.Series(False, index=frame.index)
    starts = pd.Series(False, index=frame.index)
    for column, filter_value in active_filters:
        normalized = normalized_columns[column]
        exact = exact | normalized.eq(filter_value)
        starts = starts | normalized.str.startswith(filter_value, na=False)

    eligible_values = eligible.to_numpy(dtype=bool)
    exact_values = exact.to_numpy(dtype=bool)
    starts_values = starts.to_numpy(dtype=bool)
    ranked_positions = []
    for rank_mask in (
        eligible_values & exact_values,
        eligible_values & ~exact_values & starts_values,
        eligible_values & ~exact_values & ~starts_values,
    ):
        remaining = limit - len(ranked_positions)
        if remaining <= 0:
            break
        ranked_positions.extend(np.flatnonzero(rank_mask)[:remaining].tolist())

    matches = []
    for position in ranked_positions:
        primary_value = frame[primary_column].iat[position]
        matches.append(
            {
                "target_index": position,
                "target_name": "" if pd.isna(primary_value) else str(primary_value),
                "target_values": [
                    "" if pd.isna(frame[column].iat[position]) else str(frame[column].iat[position])
                    for column in columns
                ],
            }
        )
    return matches


def similarity(left, right):
    a, b = normalize(left), normalize(right)
    return SequenceMatcher(None, a, b).ratio() if a and b else 0.0


def detect_columns(frame):
    normalized = {normalize(column).replace(" ", "_"): str(column) for column in frame.columns}
    found = {}
    for field, candidates in ALIASES.items():
        for candidate in candidates:
            if candidate in normalized:
                found[field] = normalized[candidate]
                break
    return found


def suggest_pairs(source_frame, target_frame):
    source_detected = detect_columns(source_frame)
    target_detected = detect_columns(target_frame)
    pairs = []
    defaults = {"name": 55, "npi": 70, "address": 25, "city": 10, "specialty": 10}
    for semantic_field in ["name", "npi", "address", "city", "specialty"]:
        if semantic_field in source_detected and semantic_field in target_detected:
            pairs.append({
                "source": source_detected[semantic_field],
                "target": target_detected[semantic_field],
                "method": "exact" if semantic_field == "npi" else "similarity",
                "weight": defaults[semantic_field],
            })
    return pairs


def _pair_score(source_value, target_value, method):
    left, right = normalize(source_value), normalize(target_value)
    if not left or not right:
        return None
    if method == "exact":
        return 1.0 if left == right else 0.0
    return similarity(left, right)


def score_pair(source_row, target_row, column_pairs):
    components = []
    weighted_total = 0.0
    available_weight = 0.0

    for pair in column_pairs:
        source_value = source_row[pair["source"]]
        target_value = target_row[pair["target"]]
        score = _pair_score(source_value, target_value, pair["method"])
        if score is not None:
            weight = float(pair["weight"])
            weighted_total += score * weight
            available_weight += weight
        components.append({
            "source_column": pair["source"],
            "target_column": pair["target"],
            "source_value": str(source_value),
            "target_value": str(target_value),
            "method": pair["method"],
            "score": round(score * 100) if score is not None else None,
        })

    total = weighted_total / available_weight if available_weight else 0.0
    reasons = [
        f'{item["source_column"]} ↔ {item["target_column"]}: {item["score"]}%'
        for item in components if item["score"] is not None and item["score"] >= 60
    ]
    return round(total * 100), reasons, components


def _ngrams(value, size=3):
    text = normalize(value)
    if not text:
        return set()
    padded = f"  {text}  "
    return {padded[index:index + size] for index in range(len(padded) - size + 1)}


class CandidateIndex:
    def __init__(self, target_frame, column_pairs):
        self.target_frame = target_frame
        self.column_pairs = column_pairs
        self.primary_pair = column_pairs[0]
        self.gram_index = defaultdict(lambda: array("I"))
        self.exact_indexes = {}

        primary_column = self.primary_pair["target"]
        for position, value in enumerate(target_frame[primary_column]):
            for gram in _ngrams(value):
                self.gram_index[gram].append(position)

        for pair_index, pair in enumerate(column_pairs):
            if pair["method"] != "exact":
                continue
            value_index = defaultdict(lambda: array("I"))
            for position, value in enumerate(target_frame[pair["target"]]):
                normalized = normalize(value)
                if normalized:
                    value_index[normalized].append(position)
            self.exact_indexes[pair_index] = value_index

    def shortlist(self, source_row, limit=CANDIDATE_LIMIT):
        votes = Counter()

        for pair_index, value_index in self.exact_indexes.items():
            pair = self.column_pairs[pair_index]
            normalized = normalize(source_row[pair["source"]])
            if not normalized:
                continue
            for position in value_index.get(normalized, ()):
                votes[position] += 100

        grams = _ngrams(source_row[self.primary_pair["source"]])
        useful_grams = sorted(
            (gram for gram in grams if gram in self.gram_index),
            key=lambda gram: len(self.gram_index[gram]),
        )
        retrieved = set(votes)
        for gram in useful_grams:
            postings = self.gram_index[gram]
            if len(postings) > MAX_RETRIEVAL_POOL:
                continue
            for position in postings:
                votes[position] += 1
                retrieved.add(position)
            if len(retrieved) >= MAX_RETRIEVAL_POOL:
                break

        if not votes:
            return list(range(min(limit, len(self.target_frame))))
        return [position for position, _ in votes.most_common(limit)]


def matching_strategy(source_rows, target_rows, pair_limit=EXHAUSTIVE_PAIR_LIMIT):
    return "exhaustive" if source_rows * target_rows <= pair_limit else "indexed"


def match_frames(
    source_frame,
    target_frame,
    column_pairs,
    threshold=55,
    pair_limit=EXHAUSTIVE_PAIR_LIMIT,
    candidate_limit=CANDIDATE_LIMIT,
):
    source_frame = source_frame.fillna("").reset_index(drop=True)
    target_frame = target_frame.fillna("").reset_index(drop=True)
    display_pair = column_pairs[0]
    strategy = matching_strategy(len(source_frame), len(target_frame), pair_limit)
    candidate_index = (
        CandidateIndex(target_frame, column_pairs) if strategy == "indexed" else None
    )
    results = []

    for source_index, source_row in source_frame.iterrows():
        candidates = []
        target_positions = (
            range(len(target_frame))
            if candidate_index is None
            else candidate_index.shortlist(source_row, candidate_limit)
        )
        for target_index in target_positions:
            target_row = target_frame.iloc[target_index]
            score, reasons, components = score_pair(source_row, target_row, column_pairs)
            candidates.append({
                "target_index": int(target_index),
                "target_name": str(target_row[display_pair["target"]]),
                "score": score,
                "reasons": reasons,
                "components": components,
            })

        candidates.sort(key=lambda candidate: candidate["score"], reverse=True)
        best = candidates[0] if candidates else None
        second_score = candidates[1]["score"] if len(candidates) > 1 else None
        if best and best["score"] >= threshold:
            status = "Exact" if best["score"] == 100 else "Strong" if best["score"] >= 85 else "Review"
            target = best
        else:
            status = "Review"
            empty_components = [
                {
                    "source_column": pair["source"],
                    "target_column": pair["target"],
                    "source_value": str(source_row[pair["source"]]),
                    "target_value": "",
                    "method": pair["method"],
                    "score": None,
                }
                for pair in column_pairs
            ]
            target = best or {
                "target_index": None,
                "target_name": "No candidate",
                "score": 0,
                "reasons": [],
                "components": empty_components,
            }

        results.append({
            "id": int(source_index),
            "source_index": int(source_index),
            "source_name": str(source_row[display_pair["source"]]),
            **target,
            "candidates": candidates[:10],
            "candidates_considered": len(candidates),
            "runner_up_score": second_score,
            "status": status,
            "decision": "approved" if target["score"] >= AUTO_APPROVE_THRESHOLD else "pending",
        })
    return results
