import unittest

import pandas as pd

from backend.features.database_mapper.exporter import append_unmapped_target_rows

from backend.features.database_mapper.matcher import (
    duplicated_rows,
    match_frames,
    matching_strategy,
    search_rows,
)


class MatcherTests(unittest.TestCase):
    def test_manual_search_scans_full_target_and_returns_selected_columns(self):
        frame = pd.DataFrame(
            [
                {"Name": "Other", "City": "Paris"},
                {"Name": "Clinique des Pensees", "City": "Lyon"},
                {"Name": "Clinique des Pensées", "City": "Marseille"},
            ]
        )

        results = search_rows(frame, "Name", ["Name", "City"], "pensées")

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["target_values"], ["Clinique des Pensees", "Lyon"])
        self.assertEqual(results[1]["target_values"], ["Clinique des Pensées", "Marseille"])

    def test_manual_search_scans_supporting_fields_too(self):
        frame = pd.DataFrame(
            [
                {"Name": "Alpha Hospital", "City": "Paris", "Address": "Rue A"},
                {"Name": "Beta Clinic", "City": "Berlin", "Address": "Charitéplatz"},
            ]
        )

        city_results = search_rows(frame, "Name", ["Name", "City", "Address"], "Berlin")
        address_results = search_rows(frame, "Name", ["Name", "City", "Address"], "Charite")

        self.assertEqual(city_results[0]["target_name"], "Beta Clinic")
        self.assertEqual(address_results[0]["target_name"], "Beta Clinic")

    def test_manual_search_combines_field_filters(self):
        frame = pd.DataFrame(
            [
                {"Name": "Central Hospital", "City": "Paris", "Postcode": "75001"},
                {"Name": "Central Hospital", "City": "Lyon", "Postcode": "69001"},
                {"Name": "West Clinic", "City": "Paris", "Postcode": "75015"},
            ]
        )

        results = search_rows(
            frame,
            "Name",
            ["Name", "City", "Postcode"],
            filters={"Name": "central", "City": "lyon", "Postcode": ""},
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["target_values"], ["Central Hospital", "Lyon", "69001"])

    def test_duplicate_detection_uses_all_fields_and_ignores_accents(self):
        frame = pd.DataFrame(
            [
                {"Name": "Hopital Nord", "City": "Paris"},
                {"Name": "Hopital Nord", "City": "Bordeaux"},
                {"Name": "Charite", "City": "Berlin"},
                {"Name": "Charité", "City": "Berlin"},
            ]
        )

        duplicates = duplicated_rows(frame, ["Name", "City"])

        self.assertEqual(list(duplicates.index), [2, 3])

    def test_duplicate_detection_uses_combination_of_selected_columns(self):
        frame = pd.DataFrame(
            [
                {"Name": "Same", "Country": "Portugal"},
                {"Name": "Same", "Country": "France"},
                {"Name": "Same", "Country": "Portugal"},
            ]
        )

        duplicates = duplicated_rows(frame, ["Name", "Country"])

        self.assertEqual(list(duplicates.index), [0, 2])

    def test_uses_explicitly_paired_different_headers(self):
        source = pd.DataFrame([
            {"Doctor": "Maria Silva", "Town": "Porto", "Area": "Oncology"},
            {"Doctor": "John Smith", "Town": "London", "Area": "Cardiology"},
        ])
        target = pd.DataFrame([
            {"Provider Full Name": "John A Smith", "Municipality": "London", "Specialism": "Cardiology"},
            {"Provider Full Name": "Maria da Silva", "Municipality": "Porto", "Specialism": "Oncology"},
        ])
        pairs = [
            {"source": "Doctor", "target": "Provider Full Name", "method": "similarity", "weight": 60},
            {"source": "Town", "target": "Municipality", "method": "exact", "weight": 20},
            {"source": "Area", "target": "Specialism", "method": "similarity", "weight": 20},
        ]

        matches = match_frames(source, target, pairs)

        self.assertEqual(matches[0]["target_index"], 1)
        self.assertEqual(matches[1]["target_index"], 0)
        self.assertGreater(matches[0]["score"], 85)
        self.assertEqual(matches[0]["components"][1]["source_column"], "Town")
        self.assertEqual(matches[0]["components"][1]["source_value"], "Porto")
        self.assertEqual(matches[0]["components"][1]["target_column"], "Municipality")
        self.assertEqual(matches[0]["components"][1]["target_value"], "Porto")
        self.assertEqual(len(matches[0]["candidates"]), 2)
        self.assertEqual(matches[0]["candidates"][0]["target_index"], 1)

    def test_automatic_matching_can_reuse_the_same_file_b_row(self):
        """Matching is many-to-one; duplicate review happens after matching."""
        source = pd.DataFrame(
            [
                {"Name": "Hopital Beaujon", "City": "Clichy"},
                {"Name": "Hôpital Beaujon", "City": "Clichy"},
            ]
        )
        target = pd.DataFrame(
            [{"Provider": "Hôpital Beaujon", "Town": "Clichy"}]
        )
        pairs = [
            {"source": "Name", "target": "Provider", "method": "similarity", "weight": 80},
            {"source": "City", "target": "Town", "method": "exact", "weight": 20},
        ]

        matches = match_frames(source, target, pairs)

        self.assertEqual([match["target_index"] for match in matches], [0, 0])
        self.assertTrue(all(match["decision"] == "approved" for match in matches))

    def test_keeps_blank_supporting_values_for_review(self):
        source = pd.DataFrame([{"Doctor": "Maria Silva", "Town": ""}])
        target = pd.DataFrame([{"Name": "Maria Silva", "City": "Porto"}])
        pairs = [
            {"source": "Doctor", "target": "Name", "method": "similarity", "weight": 80},
            {"source": "Town", "target": "City", "method": "exact", "weight": 20},
        ]

        match = match_frames(source, target, pairs)[0]

        self.assertEqual(match["components"][1]["source_value"], "")
        self.assertEqual(match["components"][1]["target_value"], "Porto")
        self.assertIsNone(match["components"][1]["score"])

    def test_keeps_source_values_when_reference_file_has_no_rows(self):
        source = pd.DataFrame([{"Doctor": "Maria Silva", "Town": "Porto"}])
        target = pd.DataFrame(columns=["Name", "City"])
        pairs = [
            {"source": "Doctor", "target": "Name", "method": "similarity", "weight": 80},
            {"source": "Town", "target": "City", "method": "exact", "weight": 20},
        ]

        match = match_frames(source, target, pairs)[0]

        self.assertEqual(match["target_name"], "No candidate")
        self.assertEqual(match["components"][0]["source_value"], "Maria Silva")
        self.assertEqual(match["components"][1]["source_value"], "Porto")

    def test_switches_strategy_using_total_pair_count(self):
        self.assertEqual(matching_strategy(500, 500), "exhaustive")
        self.assertEqual(matching_strategy(501, 500), "indexed")
        self.assertEqual(matching_strategy(1_000, 200_000), "indexed")

    def test_indexed_strategy_finds_match_without_scoring_every_target(self):
        source = pd.DataFrame([{"Label": "Alpha Medical Group", "Type": "Clinic"}])
        target = pd.DataFrame(
            [
                {"Candidate": f"Unrelated Provider {index}", "Category": "Other"}
                for index in range(500)
            ]
            + [{"Candidate": "Alpha Medical Grp", "Category": "Clinic"}]
        )
        pairs = [
            {"source": "Label", "target": "Candidate", "method": "similarity", "weight": 80},
            {"source": "Type", "target": "Category", "method": "exact", "weight": 20},
        ]

        match = match_frames(source, target, pairs, pair_limit=0, candidate_limit=25)[0]

        self.assertEqual(match["target_index"], 500)
        self.assertLessEqual(match["candidates_considered"], 25)

    def test_automatically_approves_scores_at_or_above_95(self):
        source = pd.DataFrame([{"Name": "Alpha Clinic", "Code": "A"}])
        target = pd.DataFrame([{"Provider": "Alpha Clinic", "Identifier": "B"}])
        pairs = [
            {"source": "Name", "target": "Provider", "method": "similarity", "weight": 95},
            {"source": "Code", "target": "Identifier", "method": "exact", "weight": 5},
        ]

        match = match_frames(source, target, pairs)[0]

        self.assertEqual(match["score"], 95)
        self.assertEqual(match["decision"], "approved")

    def test_does_not_automatically_approve_scores_below_95(self):
        source = pd.DataFrame([{"Name": "Alpha Clinic", "Code": "A"}])
        target = pd.DataFrame([{"Provider": "Alpha Clinic", "Identifier": "B"}])
        pairs = [
            {"source": "Name", "target": "Provider", "method": "similarity", "weight": 94},
            {"source": "Code", "target": "Identifier", "method": "exact", "weight": 6},
        ]

        match = match_frames(source, target, pairs)[0]

        self.assertEqual(match["score"], 94)
        self.assertEqual(match["decision"], "pending")

    def test_appends_only_unmapped_target_rows_with_blank_source_columns(self):
        target = pd.DataFrame(
            [
                {"Name": "Alpha", "City": "Paris"},
                {"Name": "Beta", "City": "Berlin"},
                {"Name": "Gamma", "City": "Porto"},
            ]
        )

        rows = append_unmapped_target_rows(
            [["Source Alpha", "Lisbon", "Alpha", "Paris"]],
            target,
            ["Name", "City"],
            [0],
            2,
        )

        self.assertEqual(
            rows,
            [
                ["Source Alpha", "Lisbon", "Alpha", "Paris"],
                ["", "", "Beta", "Berlin"],
                ["", "", "Gamma", "Porto"],
            ],
        )


if __name__ == "__main__":
    unittest.main()
