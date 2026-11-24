# Natural Language to Data Insights architecture

## Runtime flow

1. The Lit dashboard sends dataset and chat requests to FastAPI.
2. FastAPI validates request schemas and resolves the selected dataset version.
3. `SQLiteDataQualityService` imports files into generated SQLite tables,
   profiles data with pandas, and stores immutable cleaning versions.
4. Vanna's `Agent` resolves the request user, retrieves schema/tool context,
   and calls the configured LLM.
5. `RunSqlTool` accepts one read-only `SELECT` or CTE, applies the trusted
   selected version, executes through the injected SQL runner, and emits table
   metadata.
6. `VisualizeDataTool` and the Plotly web component render suitable results.

## Data ownership and authentication

Local demo mode preserves the existing cookie-based UI and is not suitable for
untrusted networks. Secure deployments set `require_auth=true` and provide
`VANNA_AUTH_SECRET` (at least 32 characters). Requests then require a signed
`vanna_session`; uploaded datasets are stored with the authenticated owner ID.
The configured admin identity can access legacy SQLite tables and all owned
uploads.

## Persistence

- Original uploaded bytes: `uploads/<generated-dataset-id>.<extension>`
- Imported data: generated SQLite table
- Dataset metadata: `_vanna_datasets`
- Cleaning lineage: `_vanna_data_quality_history`
- Cleaned and rollback versions: `_vanna_<dataset>_v<number>`
