# Tools Workspace

A modular local desktop application that hosts independent tools. Database
Mapper is the first application; future tools can be added without coupling
their interfaces or backend logic to the mapper.

## Structure

```text
app/page.jsx                              shared tools homepage
features/database-mapper/                 Database Mapper frontend and storage
backend/app/main.py                       shared FastAPI entry point
backend/features/database_mapper/         matching and Excel export logic
backend/features/pubmed_scraper/          reserved future backend feature
public/database-mapper.svg                Database Mapper icon
src-tauri/                                Windows desktop shell
```

## First-time Windows setup

From the project root in PowerShell:

```powershell
py -3.12 -m venv backend\.venv
& ".\backend\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
npx.cmd --yes pnpm@11.25.0 install
```

Start the Python service:

```powershell
& ".\backend\.venv\Scripts\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Start the desktop application in a second terminal:

```powershell
npx.cmd --yes pnpm@11.25.0 desktop:dev
```

## Portable mapping projects

Database Mapper projects can be exported as `.dbmap` files. A package contains
the two original datasets and the complete saved workflow state, including
field pairs, matches, approvals, skips, replacements, and manual selections.
Importing creates a new local copy so it never overwrites an existing project.

Only share `.dbmap` packages through an approved channel because they contain
the original datasets.

## Adding another application

Create a sibling frontend folder under `features/` and a backend package under
`backend/features/`. Register the new application card and navigation target in
`app/page.jsx`, then register any new API routes in `backend/app/main.py`.
