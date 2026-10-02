# PubMed name review update

Extract this update into the `gds-backoffice` folder, replacing existing files.

The scraper now pauses after it finishes whenever its `Potential Mappings` sheet contains names to review. Choose the preferred spelling, or keep each pair separate. Accepted names are changed throughout the `Author` column of `PubMed Data`, moved into `Names Mapping`, and tagged `Potential Map` in its third column. Names kept separate remain in `Potential Mappings`.

The in-app save screen now uses Downloads by default. Selecting another location is optional. If a PubMed filename already exists in Downloads, the next saved file has a number before its name, such as `1 - pubmed_author_topic_country.xlsx`.

Because the desktop save command changed, rebuild the desktop application after extracting:

```powershell
npx.cmd --yes pnpm@11.25.0 desktop:build
```
