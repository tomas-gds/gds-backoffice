# Corrected PubMed integration

Copy the backend/features/pubmed_scraper folder over the same folder in your full app. Restart the Python backend. No frontend files or backend routes were changed. The zip contains the app excerpt you supplied, not a complete runnable application.

## Structure

- app/page.jsx is the frontend landing page. It imports the PubMed, database mapping and Account components; those component files were not supplied.
- backend/app/main.py contains FastAPI routes. /pubmed/export reads UI choices, validates inputs and calls run_legacy_workflow. It also exposes upload inspection and the app's additional name-review endpoints.
- backend/features/pubmed_scraper/legacy_adapter.py is the bridge from web-form values to the original scripts. It selects a scraper, provides HCP-file prompt answers, installs Account credentials and returns an Excel download. Processing now calls the original main() rather than repeating its steps.
- legacy/PubmedScraper.py handles PubMed retrieval, retries, article parsing and Excel export.
- legacy/PubmedScraperAuthors.py runs the country query and subsequent author queries, then names, affiliations and collaborators processing. Company mode uses this same workflow, as in the CMD menu.
- legacy/PubmedScraperHCO.py extracts country-specific affiliations and normalizes institutions/departments.
- legacy/PubmedScraperHCP.py loads clinician names, searches their articles and optionally expands the coauthor network.
- legacy/NameNormaliser.py handles automatic name mappings and potential mappings. HCONormaliser.py handles institutions and departments, including country-specific rules. LocaleNormaliser.py handles countries/cities and loads country_names.json.
- review.py is the app's additional manual name-review feature. It runs after extraction and is outside CMD parity. It is unchanged.
- engine.py is a separate, simplified implementation. The supplied API does not import it, so it is not the active scraper.

## Corrections

Restored Authors, HCO and HCP modules from the uploaded CMD source, changing only imports to package-relative imports. This restores original search clauses and filtering, and removes the unsupported rare argument in get_pubmeds_Author. Institution/name normalizers were already identical. Kept the module-relative country_names.json path so the backend works from different working directories.

The adapter now executes original main() methods. Original write_excel accepts an optional stream destination, preserving counting, sorting, sheet names and column rules. Author/company exports remove Author key; HCP-file exports retain it. Empty searches still return a minimal PubMed Data workbook for compatibility with the app download route; CMD writes no file in this case.

HCP input is answered by prompt rather than position. Single-sheet Excel, multi-sheet Excel and CSV therefore receive the right choices. Uploaded sheet/column choices are validated, and displayed headers use the same newline/space cleanup as the original loader. Temporary files are removed on success and failure. Python's global input is no longer replaced. A process-local lock protects the legacy module prompt override and global Entrez credentials; previous credentials are restored afterward.

UK/United Kingdom input is converted to UK just as in the CMD menu. Credentials come from the app's Account/environment settings; the original embedded credentials are not included in this package.

## Rare-disease checkbox

The supplied CMD code has no rare-disease behavior. The earlier app code used this flag to retain additional authors and foreign HCO affiliations, changing results. The UI and API field remain as supplied, but rare_disease does not change processing in this parity version. Both checkbox values execute the original workflow. If you want the checkbox to control a distinct rare-disease workflow, that would be an intentional change from this CMD baseline.

## Validation and limits

Run `python validation/parity_check.py` from an environment with pandas, openpyxl, biopython, babel and pycountry installed (Python 3.12 or newer; the original source uses Python 3.12 f-string syntax). The test reference contains the supplied CMD modules with embedded credentials removed.

Twelve fixture-based comparisons passed: author, company, HCO, HCP CSV, HCP single-sheet Excel and HCP multi-sheet Excel with full-network expansion, each for both checkbox values. The checks compare generated PubMed query sequences and every worksheet's columns, rows, order and values against the original CMD workflows. Real name, country and HCO processing runs; only PubMed retrieval and delays are mocked.

This establishes parity for those cases, not proof for every PubMed record. No live PubMed request or complete app UI launch was performed. The supplied frontend feature components, database_mapper modules and dependency/startup configuration are missing, so full app integration cannot be verified from this excerpt. For identical live outputs, compare the same inputs and the same PubMed response data/date. Manual name review can subsequently modify the export.
