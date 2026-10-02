import re
import unicodedata
import pandas as pd




class NameNormaliser:
    GERMAN_SPECIALS = "äöüÄÖÜß"
    _RE_WS = re.compile(r"\s+")
    _RE_PUNCT = re.compile(r"[^\w\s]")

    def __init__(self):
        self.clean_names = []
        self.initial_index = {}
        self.country_aliases = None
        self.mapping = None
        self.names_mapping_df = None
        self.potential_mapping_df = None

    def _get_clean_names(self,df):
        self.clean_names = []

        # Delete additional whitespaces
        names = df["Author"].dropna().unique()

        for name in names:
            if isinstance(name, str) and name.strip():
                self.clean_names.append(name)
    def _get_initial_index(self):
        self.initial_index = {}
        for name in self.clean_names:
            first, mi, last = self._parse_for_match(name)
            if first and last and len(first) > 1:
                key = (first[0], last)
                self.initial_index.setdefault(key, []).append(name)
    def _collapse_whitespaces(self, s):
        return self._RE_WS.sub(" ", s).strip()
    def _strip_punctuation_keep_spaces(self, s):
        return self._RE_PUNCT.sub("", s)
    def _remove_accents(self, s):
        return "".join(
            ch for ch in unicodedata.normalize("NFKD", s)
            if not unicodedata.combining(ch)
        )
    def _german_equivalents(self, s):
        # Matching-only: make Köln / Koeln / Koln collide
        s = s.replace("ae", "a").replace("oe", "o").replace("ue", "u")
        s = s.replace("ä", "a").replace("ö", "o").replace("ü", "u")
        return s
    def _match_clean(self, s):
        s = s.strip().replace("-", " ")
        s = s.casefold()
        s = self._remove_accents(s)
        s = self._german_equivalents(s)
        s = self._strip_punctuation_keep_spaces(s)
        return self._collapse_whitespaces(s)
    def _display_clean(self, s):
        s = s.strip().replace("-", " ")
        s = self._collapse_whitespaces(s)
        s = self._strip_punctuation_keep_spaces(s)
        return self._collapse_whitespaces(s)
    def _parse_for_match(self, name):
        parts = self._match_clean(name).split()
        if not parts:
            return "", "", ""
        # if len(parts) == 1:
        #     return parts[0], "", ""

        first = parts[0]
        last = parts[-1]

        mi = ""
        for p in parts[1:-1]:
            if p:
                mi += p[0]

        return first, mi, last
    def _is_initial_firstname(self, first):
        return len(first) == 1 and first.isalpha()
    def _middle_compatible(self, mi1, mi2):
        if mi1 and mi2:
            return (mi1 == mi2) or (mi1[0] == mi2[0])
        return True
    def _score_display(self, original_name):
        """
        Canonical priorities:
        1) If any variant has German specials (äöüß), pick one of those
        2) If multiple, pick the longest (after display cleaning)
        3) Then prefer other accents/diacritics
        4) Then prefer more tokens
        5) Then prefer longer
        """
        disp = self._display_clean(original_name)

        has_german_special = any(ch in original_name for ch in self.GERMAN_SPECIALS)
        has_accent = (self._remove_accents(original_name) != original_name)

        return (
            has_german_special,
            len(disp),
            has_accent,
            len(disp.split()),
            len(original_name),
        )
    def _one_edit_apart(self, a, b):
        """
        True if strings are exactly 1 edit apart (insert/delete/replace one char).
        """
        if a == b:
            return False

        la, lb = len(a), len(b)
        if abs(la - lb) > 1:
            return False

        # Ensure a is the shorter (or equal)
        if la > lb:
            a, b = b, a
            la, lb = lb, la

        # Case 1: same length -> one replacement
        if la == lb:
            diff = 0
            for i in range(la):
                if a[i] != b[i]:
                    diff += 1
                    if diff > 1:
                        return False
            return diff == 1

        # Case 2: lengths differ by 1 -> one insert/delete
        i = j = 0
        used = False
        while i < la and j < lb:
            if a[i] == b[j]:
                i += 1
                j += 1
            else:
                if used:
                    return False
                used = True
                j += 1  # skip one char in longer string
        return True  # if we reach here, it's exactly one edit

    def _country_is_target(self,series):
        return (
            series.fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            .isin(self.country_aliases)
        )

    def build_name_mapping(self, df):
        self.df = df.copy()
        self._get_clean_names(self.df)
        self._get_initial_index()

        # Group by (first,last,mi) when middle exists; otherwise by (first,last)
        strict_groups = {}  # (first,last,mi)
        loose_groups = {}  # (first,last)

        # Keep initial-first-name entries out of confirmed mapping
        initial_first_names = set()

        for name in self.clean_names:
            first, mi, last = self._parse_for_match(name)
            if not first or not last:
                continue

            # Do not confirmed-map names whose first name is only an initial
            if self._is_initial_firstname(first):
                initial_first_names.add(name)
                continue

            if mi:
                strict_groups.setdefault((first, last, mi), []).append(name)
            else:
                loose_groups.setdefault((first, last), []).append(name)

        # Choose best display form in each group
        strict_best = {}
        for k, variants in strict_groups.items():
            strict_best[k] = max(variants, key=self._score_display)

        loose_best = {}
        for k, variants in loose_groups.items():
            loose_best[k] = max(variants, key=self._score_display)

        mapping = {}

        # Strict groups: full first name only
        for (first, last, mi), variants in strict_groups.items():
            best = strict_best[(first, last, mi)]
            for v in variants:
                mapping[v] = best

        # Loose groups: full first name only
        strict_mi_by_fl = {}
        for (first, last, mi) in strict_groups.keys():
            strict_mi_by_fl.setdefault((first, last), []).append(mi)

        for (first, last), variants in loose_groups.items():
            candidates_mi = strict_mi_by_fl.get((first, last), [])
            if len(candidates_mi) == 1:
                best = strict_best[(first, last, candidates_mi[0])]
            else:
                best = loose_best[(first, last)]

            for v in variants:
                mapping[v] = best

        # Initial-first-name entries map to themselves
        for name in initial_first_names:
            mapping[name] = name

        # Default identity for anything not mapped yet
        for name in self.clean_names:
            mapping.setdefault(name, name)

        # Final override:
        # if any (first,last) has a German-special variant, force all FULL-first-name
        # variants to that variant. Do NOT apply this to initial-first-name names.
        special_best = {}
        for name in self.clean_names:
            first, mi, last = self._parse_for_match(name)
            if not first or not last:
                continue

            if self._is_initial_firstname(first):
                continue

            if any(ch in name for ch in self.GERMAN_SPECIALS):
                key = (first, last)
                prev = special_best.get(key)
                if prev is None or len(self._display_clean(name)) > len(self._display_clean(prev)):
                    special_best[key] = name

        for name in self.clean_names:
            first, mi, last = self._parse_for_match(name)
            if not first or not last:
                continue

            # Never override initial-first-name entries
            if self._is_initial_firstname(first):
                mapping[name] = name
                continue

            best = special_best.get((first, last))
            if best is not None:
                mapping[name] = best

        rows = []
        for original, canonical in mapping.items():
            if original == canonical:
                continue
            rows.append({"Original": original, "Canonical": canonical})

        rows.sort(key=lambda r: (r["Canonical"], r["Original"]))

        self.mapping = mapping
        self.names_mapping_df = pd.DataFrame(rows)

        self.df["Author"] = self.df["Author"].map(mapping).fillna(self.df["Author"])

        return self.df,self.names_mapping_df,mapping

    def build_potential_mappings_df(self, df):
        """
        Manual-review candidates:
        - last names start with same letter
        - last or first names are exactly 1 edit apart (typo-like)

        Also include:
        - abbreviated names like "A Koitschev" that match multiple
          possible full names for the same author key (initial, last)
        """
        self.df = df.copy()
        names = self.df["Author"].dropna().unique()
        mapping = {name: name for name in names}

        valid_names = [name for name in names if isinstance(name, str) and name.strip()]
        canonical_names = sorted(set(mapping.get(name, name) for name in valid_names))

        rows = []

        # --------------------------------------------------
        # PART 1: potential last names typos (first name =, last name ~=)
        # --------------------------------------------------
        buckets = {}
        parsed = {}

        for name in canonical_names:
            first, mi, last = self._parse_for_match(name)
            if not first or not last:
                continue
            parsed[name] = (first, mi, last)
            key = (first, last[0])
            buckets.setdefault(key, []).append(name)

        for key, group in buckets.items():
            if len(group) < 2:
                continue

            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    a = group[i]
                    b = group[j]

                    if mapping.get(a, a) == mapping.get(b, b):
                        continue

                    a_first, a_mi, a_last = parsed[a]
                    b_first, b_mi, b_last = parsed[b]

                    if self._one_edit_apart(a_first, b_first):
                        rows.append({
                            "Name 1": a,
                            "Name 2": b,
                            "Reason": "first name 1 edit apart"
                        })

                    if self._one_edit_apart(a_last, b_last):
                        rows.append({
                            "Name 1": a,
                            "Name 2": b,
                            "Reason": "last name 1 edit apart"
                        })

        # --------------------------------------------------
        # PART 2: same initial + same last name
        # Example:
        #   A Konichec -> Antonio Konichec
        #   A Konichec -> Ancarl Konichec
        # --------------------------------------------------
        potential_mapping = {}
        self._get_clean_names(self.df)
        self._get_initial_index()

        for name in self.clean_names:
            first, mi, last = self._parse_for_match(name)
            if not first or not last:
                continue

            if not self._is_initial_firstname(first):
                continue

            candidates = self.initial_index.get((first, last), [])
            matched_candidates = set()

            for c in candidates:
                if c == name:
                    continue

                c_first, c_mi, c_last = self._parse_for_match(c)
                if not c_first or not c_last:
                    continue

                if c_last != last:
                    continue

                if self._is_initial_firstname(c_first):
                    continue

                if not self._middle_compatible(mi, c_mi):
                    continue

                # keep raw candidate for manual review
                matched_candidates.add(c)

            if matched_candidates:
                potential_mapping[name] = sorted(matched_candidates)

        for abbreviated_name, aliases in potential_mapping.items():
            for alias in aliases:
                rows.append({
                    "Name 1": abbreviated_name,
                    "Name 2": alias,
                    "Reason": "share same author key"
                })

        # --------------------------------------------------
        # PART 3: build potential_mapping_df
        # --------------------------------------------------
        self.potential_mapping_df = pd.DataFrame(rows)

        if not self.potential_mapping_df.empty:
            self.potential_mapping_df = self.potential_mapping_df.drop_duplicates(subset=["Name 1", "Name 2", "Reason"])
            self.potential_mapping_df = self.potential_mapping_df.sort_values(["Name 1", "Name 2", "Reason"]).reset_index(drop=True)


        return self.potential_mapping_df


    def clean_potential_mappings_df(self):
        deleted_from_potential = set()

        if not self.potential_mapping_df.empty:
            col1 = self.potential_mapping_df.columns[0]
            col2 = self.potential_mapping_df.columns[1]

            # Names in column 2
            unique_targets = self.potential_mapping_df[col2].dropna().unique()

            for target in unique_targets:
                # All the names in column 1 that map to the same name in column 2
                source_names = set(
                    self.potential_mapping_df.loc[
                        self.potential_mapping_df[col2] == target, col1
                    ].dropna()
                )

                group_names = source_names | {target}

                # rows in self.df belonging to this mapping group
                group_df = self.df.loc[self.df["Author"].isin(group_names)].copy()

                # keep only target-country rows
                group_target_df = group_df.loc[
                    self._country_is_target(group_df["Country"])
                ].copy()

                # condition 1: no target-country affiliation at all
                has_target_country = not group_target_df.empty

                # condition 2: fewer than 2 publications in target country
                if "PMID" in group_target_df.columns:
                    n_target_pubs = group_target_df["PMID"].dropna().nunique()
                elif "URL" in group_target_df.columns:
                    n_target_pubs = group_target_df["URL"].dropna().nunique()
                else:
                    # fallback if neither PMID nor URL exists
                    n_target_pubs = len(group_target_df)

                if (not has_target_country) or (n_target_pubs < 2):
                    deleted_from_potential.update(group_names)

            # remove from potential mapping df
            self.potential_mapping_df = self.potential_mapping_df[
                ~self.potential_mapping_df[col1].isin(deleted_from_potential) &
                ~self.potential_mapping_df[col2].isin(deleted_from_potential)
                ].reset_index(drop=True)

        # remove same names from self.df
        if deleted_from_potential:
            names_to_delete_in_df = set(deleted_from_potential)

            # also include normalized / mapped versions if self.df["Author"] is normalized
            if hasattr(self, "mapping") and self.mapping:
                names_to_delete_in_df.update(
                    self.mapping.get(name, name) for name in deleted_from_potential
                )

            self.df = self.df[
                ~self.df["Author"].isin(names_to_delete_in_df)
            ].reset_index(drop=True)

    def build_protected_names(self):
        # we should not delete the names left in potential mapping, as they might be in the country
        protected_names = set()

        if not self.potential_mapping_df.empty:
            col1 = self.potential_mapping_df.columns[0]
            col2 = self.potential_mapping_df.columns[1]

            protected_names.update(self.potential_mapping_df[col1].dropna())
            protected_names.update(self.potential_mapping_df[col2].dropna())
            protected_names = {self.mapping.get(name, name) for name in protected_names}

        return protected_names

    def clean_dfs(self):
        self.clean_potential_mappings_df()

        # we should not delete the names left in potential mapping, as they might be in the country
        protected_names = self.build_protected_names()
        mask_protected = self.df["Author"].isin(protected_names)

        # authors that have affiliations in the country of interest
        mask_country_aff = self._country_is_target(self.df["Country"]).groupby(self.df["Author"]).transform("any")

        # keep only the protected authors and those with affil in the country
        self.df = self.df[mask_country_aff | mask_protected].reset_index(drop=True)

        remaining_authors = set(self.df["Author"].dropna())

        # final clean for the names_mapping_df and potential_mapping_df
        if not self.names_mapping_df.empty:
            self.names_mapping_df = self.names_mapping_df[
                self.names_mapping_df.iloc[:, 1].isin(remaining_authors)
            ].reset_index(drop=True)

        if not self.potential_mapping_df.empty:
            col1 = self.potential_mapping_df.columns[0]
            col2 = self.potential_mapping_df.columns[1]

            self.potential_mapping_df = self.potential_mapping_df[
                self.potential_mapping_df[col1].map(lambda x: self.mapping.get(x, x)).isin(remaining_authors) &
                self.potential_mapping_df[col2].map(lambda x: self.mapping.get(x, x)).isin(remaining_authors)
                ].reset_index(drop=True)

        return self.df,self.names_mapping_df,self.potential_mapping_df



