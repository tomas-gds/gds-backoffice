# Database Mapper text export update

Extract this ZIP into the root of `gds-backoffice` and choose **Replace files in the destination**.

This update makes the Database Mapper treat every imported value as text before matching and saves all Excel output cells as text. This protects leading zeroes in values such as postcodes, IDs, and codes.

It applies to:

- the completed mapping download;
- unused File B rows added to an export; and
- the duplicate-values workbook, including both the File A and File B sheets.

CSV is already a text-only format. The updated CSV writer quotes every field to preserve values exactly for CSV-aware programs.

Restart the backend/desktop app after replacing these files.
