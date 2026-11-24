# Professor demonstration guide

## Start

```powershell
cd "D:\Jg Uni Sem-3\Project\college_project\Natural-Language-to-Data-Insights"
$env:PYTHONIOENCODING="utf-8"
py -3.13 -m vanna.servers.cli.server_runner --framework fastapi `
  --example mock_quickstart --host 127.0.0.1 --port 8000 --dev
```

Open `http://127.0.0.1:8000`, choose `user@example.com`, and use
`examples/demo_sales.csv` for the upload demonstration.

## Demonstration sequence

1. Click the visible **Upload Dataset** control, choose the sales CSV, and
   show the generated dataset ID and refreshed dataset list.
2. Select the upload, click **Preview dataset**, and show inferred columns.
3. Generate the profile; point out missing cells and the duplicate Ben row.
4. Open **Cleaning recommendations** and select duplicate removal plus
   median/mode filling.
5. Click **Preview cleaning** and review the before-and-after metrics.
6. Click **Approve and create version** to create the immutable cleaned version.
7. Switch between original and cleaned versions and compare quality metrics.
8. Use the version history **Rollback** button and confirm the new rollback
   request succeeds.
9. Ask a read-only analytical question such as “show sales by region”.
10. Show generated SQL, returned rows, and the Plotly visualization.

The automated browser validation covers steps 1–7 and API error handling.
Steps 8–9 require a real provider call. Configure `GOOGLE_API_KEY` or
`GEMINI_API_KEY` plus an appropriate `GEMINI_MODEL` (or another supported
provider) outside chat before presenting generated SQL or charts. Without
credentials, demonstrate steps 1–7 and clearly label the LLM step as blocked;
never use the mock server as evidence of live AI connectivity.

## Short explanation

**Two minutes:** This project lets a user upload tabular data, measure its
quality, safely clean it into immutable versions, and ask analytical questions
in natural language. FastAPI exposes the workflow, pandas calculates actual
quality metrics, SQLite preserves lineage, and Vanna connects the user question
to an LLM and validated SQL tool. The frontend is a Lit web component that
displays profiles, versions, tables, and charts.

**Five minutes:** Start with ingestion and metadata, show the profile's
completeness and uniqueness scores, preview a deterministic cleaning operation,
execute it into a new table, compare the reports, and roll back without
overwriting the original. Then explain that generated SQL is restricted to one
read-only statement and is rewritten against the server-resolved version, not
an arbitrary frontend table name. Finish with the visualization and discuss
authentication, provider credentials, and remaining production hardening.
