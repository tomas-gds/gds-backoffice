# PubMed code defaults

Extract this archive into:

```text
C:\Users\TomásCarrilho\GitHub-Projects\gds-backoffice
```

Replace the existing `backend\app\main.py` file.

Open `backend\app\main.py` and set the two values near the top:

```python
PUBMED_DEFAULT_EMAIL = "your.email@company.com"
PUBMED_DEFAULT_API_KEY = "your-api-key"
```

Restart the Python Matching Engine after saving the file. The PubMed app then
uses these defaults automatically; users do not need to enter them under
**See more**. Values written here take precedence over Windows environment
variables.

Do not commit this file to a public Git repository with a real API key in it.
