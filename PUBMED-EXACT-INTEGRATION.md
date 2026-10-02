# PubMed Scraper integration

Extract this update into the root of `gds-backoffice`, keeping the folder structure.

Then, from PowerShell in `gds-backoffice`, install the added Python packages:

```powershell
& ".\backend\.venv\Scripts\python.exe" -m pip install -r .\backend\requirements.txt
```

Restart the Python engine and then the desktop app.

For a distributable installer, rebuild the sidecar and installer after the package install:

```powershell
npx.cmd --yes pnpm@11.25.0 desktop:build
```

The PubMed screen calls the supplied scraper's original author/HCP, HCO, company, and HCP-file workflows. Its terminal questions are shown as application controls, and its Excel workbook is returned through the normal desktop save dialog.

To place a default contact email or PubMed API key in the code, edit the two empty values near the top of `backend\app\main.py`:

```python
PUBMED_DEFAULT_EMAIL = ""
PUBMED_DEFAULT_API_KEY = ""
```

Do not commit a real API key to a shared repository. A Windows environment variable remains supported as an alternative.
