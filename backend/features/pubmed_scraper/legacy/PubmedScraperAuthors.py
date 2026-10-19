import pandas as pd

from .PubmedScraper import PubmedScraper
from .LocaleNormaliser import LocaleNormaliser
from .HCONormaliser import HCONormaliser

from .utilities import *


class PubmedScraperAuthors:
    def __init__(self, search, country, numyears=5, rare=False):
        self.search = search
        self.country = country.lower().title()
        self.numyears = numyears
        self.rare = rare

        self.df = pd.DataFrame()
        self.names_mapping = {}
        self.names_mapping_df = pd.DataFrame()
        self.potential_mapping_df = pd.DataFrame()
        self.collaborators_df = pd.DataFrame()

        self.pubmed_scraper = PubmedScraper(self.search, self.country, rare=self.rare, numyears=self.numyears)
        self.locale_normaliser = LocaleNormaliser(self.country, self.rare)
        self.hco_normaliser = HCONormaliser(self.df, self.country)

        self.country_aliases = self.locale_normaliser.build_country_aliases()
        self.rows = [] #[ {"Author":, "AuthorKey":, "Title":, "Country":, "Affiliations":, "Other affiliations":,"PMID":,"URL":,"Source":}, ...]
        self.author_keys = set() # [ "de Roux A", ...]
        self.seen_pmid_author = set() # (pmid, author_key)
        self.first_cols = ["Author", "Author Role","Title", "Publication Type", "HCO", "Department", "City", "Country"]

    def _pubmed_author_key(self,author):
        """
        PubMed-friendly author key: 'LastName Initials' (e.g., 'de Roux A').
        """
        if not author:
            return ""

        ln = norm_spaces(author.get("LastName", "") or "")
        initials = norm_spaces(author.get("Initials", "") or "")

        if not initials:
            fn = norm_spaces(author.get("ForeName", "") or "")
            initials = "".join(p[0] for p in re.split(r"[\s\-]+", fn) if p)

        key = norm_spaces(f"{ln} {initials}")
        key = strip_accents(key)
        key = norm_spaces(key)
        return key

    def author_query_builder(self,author_keys):
        # author_keys are PubMed-style keys: "LastName Initials" (e.g., "de Roux A")
        parts = []
        for k in author_keys:
            if not k:
                continue
            k = norm_spaces(strip_accents(k))
            parts.append(f'"{k}"[Author]')
        return "(" + " OR ".join(parts) + ")"

    def get_pubmeds_Author(self,query,allowed_author_keys=None):
        pubmeds = self.pubmed_scraper.get_pubmeds(query)

        if not pubmeds:
            return pd.DataFrame()

        new_rows = []
        for pubmed in pubmeds:
            for i,author in enumerate(pubmed["author_list"]):
                if not author:
                    continue

                display_name = display_name_from_xml(author)
                author_key = self._pubmed_author_key(author)
                author_role = pubmed["author_role_list"][i]


                if not author_key:
                    continue

                if allowed_author_keys is not None and author_key not in allowed_author_keys:
                    continue


                pair = (pubmed["pmid"], author_key)

                if pair in self.seen_pmid_author:
                    continue

                self.seen_pmid_author.add(pair)

                author_affs = author.get("AffiliationInfo", [])

                if (len(author_affs) == 1) and ";" in author_affs[0].get("Affiliation", ""):
                    author_affs_list = (author_affs[0].get("Affiliation", "") or "").split("; ")
                else:
                    author_affs_list = [aff.get("Affiliation", "") for aff in author_affs]

                in_country = "; ".join(
                    aff for aff in author_affs_list
                    # to avoid China-Germany affiliations
                    if aff and any(alias in aff.lower() for alias in self.country_aliases) and not any(f"-{alias}" in aff.lower() for alias in self.country_aliases)
                )

                other_aff = "; ".join(
                    aff for aff in author_affs_list
                    if aff and not any(alias in aff.lower() for alias in self.country_aliases)
                )


                country, cities = self.locale_normaliser.extract_countries_cities(in_country) if in_country else [
                    self.country, ""]

                other_country, other_cities = self.locale_normaliser.extract_countries_cities(other_aff,
                                                                                         not_target_country=True) if other_aff else [
                    "", ""]



                if allowed_author_keys is None and "" not in [in_country, author_key, display_name]:
                    self.author_keys.add(author_key)



                row = {
                    "Author": display_name,
                    "Author Role": author_role,
                    "Author key": author_key,
                    "Title": pubmed["title"],
                    "Publication Type": pubmed["publication_types"],
                    "NCT Code": pubmed["nct_codes"],
                    "Collaborators": pubmed["collaborators"],
                    "Study Groups": pubmed["study_group_names"],
                    "City": cities,
                    "Country": self.country if in_country else other_country,
                    "Affiliations": in_country,
                    "COI Statement": pubmed["coi_statements"][i],
                    "COI Statements All": pubmed["coi_statements_all"],
                    "Other Cities": other_cities,
                    "Other affiliations": other_aff,
                    "Year": pubmed["year"] if pubmed["year"] is not None else "",
                    "doi": f"https://doi.org/{pubmed['doi']}" if pubmed["doi"] else "",
                    "URL": pubmed["url"],
                }

                new_rows.append(row)
                self.rows.append(row)

        self.df = pd.DataFrame(self.rows)
        return pd.DataFrame(new_rows)

    def extract(self):
        print("     Running first query...")
        # first query: build author/article list only from in-country affiliations
        first_query = fix_query_affil(self.search, self.country)
        self.get_pubmeds_Author(first_query)

        author_keys = sorted(self.author_keys)

        print("     Running second query...")
        for author_batch in chunked(author_keys, 30):
            authors_clause = self.author_query_builder(author_batch)
            second_query = f'(({self.search})[Title/Abstract]) AND {authors_clause}'

            # second query: get all relevant publications of the authors found in query #1 even if not in the country of interest
            self.get_pubmeds_Author(second_query,allowed_author_keys=set(author_batch))

        self.hco_normaliser.df = self.df.copy()

    def build_name_mapping(self):
        GERMAN_SPECIALS = "äöüÄÖÜß"
        
        # self._get_clean_names(self.df)
        clean_names = get_clean_names(self.df)

        # Group by (first,last,mi) when middle exists; otherwise by (first,last)
        strict_groups = {}  # (first,last,mi)
        loose_groups = {}  # (first,last)

        # Keep initial-first-name entries out of confirmed mapping
        initial_first_names = set()

        for name in clean_names:
            first, mi, last = parse_for_match(name)
            if not first or not last:
                continue

            # Do not confirmed-map names whose first name is only an initial
            if token_is_initial(first, allow_dots=False):
                initial_first_names.add(name)
                continue

            if mi:
                strict_groups.setdefault((first, last, mi), []).append(name)
            else:
                loose_groups.setdefault((first, last), []).append(name)

        # Choose best display form in each group
        strict_best = {}
        for k, variants in strict_groups.items():
            strict_best[k] = max(variants, key=score_display)

        loose_best = {}
        for k, variants in loose_groups.items():
            loose_best[k] = max(variants, key=score_display)

        self.names_mapping = {}

        # Strict groups: full first name only
        for (first, last, mi), variants in strict_groups.items():
            best = strict_best[(first, last, mi)]
            for v in variants:
                self.names_mapping[v] = best

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
                self.names_mapping[v] = best

        # Initial-first-name entries map to themselves
        for name in initial_first_names:
            self.names_mapping[name] = name

        # Default identity for anything not mapped yet
        for name in clean_names:
            self.names_mapping.setdefault(name, name)

        # Final override:
        # if any (first,last) has a German-special variant, force all FULL-first-name
        # variants to that variant. Do NOT apply this to initial-first-name names.
        special_best = {}
        for name in clean_names:
            first, mi, last = parse_for_match(name)
            if not first or not last:
                continue

            if token_is_initial(first, allow_dots=False):
                continue

            if any(ch in name for ch in GERMAN_SPECIALS):
                key = (first, last)
                prev = special_best.get(key)
                if prev is None or len(display_clean(name)) > len(display_clean(prev)):
                    special_best[key] = name

        for name in clean_names:
            first, mi, last = parse_for_match(name)
            if not first or not last:
                continue

            # Never override initial-first-name entries
            if token_is_initial(first, allow_dots=False):
                self.names_mapping[name] = name
                continue

            best = special_best.get((first, last))
            if best is not None:
                self.names_mapping[name] = best

        rows = []
        for original, canonical in self.names_mapping.items():
            if original == canonical:
                continue
            rows.append({"Original": original, "Canonical": canonical})

        rows.sort(key=lambda r: (r["Canonical"], r["Original"]))

        self.names_mapping_df = pd.DataFrame(rows)

        self.df["Author"] = self.df["Author"].map(self.names_mapping).fillna(self.df["Author"])

    def build_potential_mappings_df(self):

        """
        Manual-review candidates:
        - last names start with same letter
        - last or first names are exactly 1 edit apart (typo-like)

        Also include:
        - abbreviated names like "A Koitschev" that match multiple
          possible full names for the same author key (initial, last)
        """
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
            first, mi, last = parse_for_match(name)
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

                    if one_edit_apart(a_first, b_first):
                        rows.append({
                            "Name 1": a,
                            "Name 2": b,
                            "Reason": "first name 1 edit apart"
                        })

                    if one_edit_apart(a_last, b_last):
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

        clean_names = get_clean_names(self.df)
        inital_index = get_initial_index(self.df)

        for name in clean_names:
            first, mi, last = parse_for_match(name)
            if not first or not last:
                continue

            if not token_is_initial(first, allow_dots=False):
                continue

            candidates = inital_index.get((first, last), [])
            matched_candidates = set()

            for c in candidates:
                if c == name:
                    continue

                c_first, c_mi, c_last = parse_for_match(c)
                if not c_first or not c_last:
                    continue

                if c_last != last:
                    continue

                if token_is_initial(c_first, allow_dots=False):
                    continue

                if not middle_compatible(mi, c_mi):
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
    
    def build_names_mappings(self):
        # 1. Names Mapping
        self.build_name_mapping()

        # 2. Potential Mappings
        self.build_potential_mappings_df()

        return self.df, self.names_mapping_df, self.potential_mapping_df

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
                group_target_df = group_df.loc[self.locale_normaliser.country_is_target(group_df["Country"])].copy()

                # condition 1: no target-country affiliation at all
                has_target_country = not group_target_df.empty

                if not self.rare:
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


                else:
                    countries = group_df["Country"]

                    # Missing country includes NaN, None, and blank strings.
                    has_missing_country = (countries.isna() | countries.astype("string").str.strip().eq("").fillna(False)).any()

                    # Delete only when every record has a known, non-target country.
                    if not group_df.empty and not has_target_country and not has_missing_country:
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
            if hasattr(self, "mapping") and self.names_mapping:
                names_to_delete_in_df.update(
                    self.names_mapping.get(name, name) for name in deleted_from_potential
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
            protected_names = {self.names_mapping.get(name, name) for name in protected_names}

        return protected_names

    def clean_dfs(self):
        self.clean_potential_mappings_df()

        # we should not delete the names left in potential mapping, as they might be in the country
        protected_names = self.build_protected_names()
        mask_protected = self.df["Author"].isin(protected_names)

        if not self.rare:
            # authors that have affiliations in the country of interest
            mask_country_aff = self.locale_normaliser.country_is_target(self.df["Country"]).groupby(self.df["Author"]).transform("any")

            # keep only the protected authors and those with affil in the country
            self.df = self.df[mask_country_aff | mask_protected].reset_index(drop=True)
        else:
            # authors that have affiliations in the country of interest or unknown
            is_unknown_country = self.df["Country"].isna() | self.df["Country"].astype("string").str.strip().eq(
                "").fillna(False)
            mask_country_aff = (self.locale_normaliser.country_is_target(self.df["Country"]) | is_unknown_country).groupby(
                self.df["Author"]).transform("any")

            # keep only the protected authors and those with affil in the country or unknown
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
                self.potential_mapping_df[col1].map(lambda x: self.names_mapping.get(x, x)).isin(remaining_authors) &
                self.potential_mapping_df[col2].map(lambda x: self.names_mapping.get(x, x)).isin(remaining_authors)
                ].reset_index(drop=True)

        # return self.df, self.names_mapping_df, self.potential_mapping_df

    def get_collaborators_tab(self):
        expanded_rows = []

        for _, row in self.df.iterrows():
            study_group = row["Study Groups"]

            if pd.isna(study_group) or str(study_group).strip() == "":
                continue

            author = row["Author"]
            collaborators = row["Collaborators"]
            title = row["Title"]
            pub_type = row["Publication Type"]
            year = row["Year"]
            url = row["URL"]

            rows = []

            # --- Author ---
            if pd.notna(author):
                rows.append({
                    "Name": str(author).strip(),
                    "Role": "Author",
                    "Study Group": study_group,
                    "Title": title,
                    "Publication Type": pub_type,
                    "Year": year,
                    "URL": url,
                })

            # --- Collaborators ---
            if pd.notna(collaborators):
                for name in str(collaborators).split(","):
                    name = name.strip()
                    if name:
                        rows.append({
                            "Name": name,
                            "Role": "Collaborator",
                            "Study Group": study_group,
                            "Title": title,
                            "Publication Type": pub_type,
                            "Year": year,
                            "URL": url,
                        })

            expanded_rows.extend(rows)

        expected_cols = ["Name", "Role", "Study Group", "Title", "Publication Type", "Year", "URL"]
        self.collaborators_df = pd.DataFrame(expanded_rows, columns=expected_cols)

        if self.collaborators_df.empty:
            return self.collaborators_df

        self.collaborators_df["Name"] = self.collaborators_df["Name"].map(self.names_mapping).fillna(self.collaborators_df["Name"])
        self.collaborators_df = self.collaborators_df.drop_duplicates(
            subset=["Name", "Study Group", "Title"]
        )
        self.collaborators_df = self.collaborators_df[
            self.collaborators_df["Name"].isin(self.df["Author"])
        ]

        return self.collaborators_df

    def main(self):
        print("Starting Pubmed extraction...")
        self.extract()

        if self.df.empty:
            print("NO PUBMEDS WERE FOUND")
            return

        print("Cleaning author names...")
        self.build_names_mappings()
        self.clean_dfs()

        print("Normalizing HCO and departments...")
        self.df = self.hco_normaliser.get_HCO_and_dept(self.df,self.first_cols,dedupe_level="author")

        if not self.df.empty:
            self.df = self.df.drop_duplicates(subset=["Author", "URL"]).reset_index(drop=True)

        print("Extracting collaborators...")
        self.get_collaborators_tab()

        print("Writing Excel output...")
        self.pubmed_scraper.write_excel(self.df,self.names_mapping_df,self.potential_mapping_df,self.collaborators_df,scraper="author")



