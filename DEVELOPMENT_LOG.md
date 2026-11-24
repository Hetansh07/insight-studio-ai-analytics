# Development log

## 2026-11-09

- Verified the Python package wheel build with Python 3.13.
- Verified the FastAPI mock server and `/docs` endpoint.
- Fixed FAISS fallback cosine similarity and deterministic text features.
- Added CSV, JSON, and XLSX dataset upload support with generated identifiers,
  preserved originals, dataset listing, bounded previews, and metadata storage.
- Added ingestion API regression tests and documented the new endpoints.
- Backend regression status: 225 passed, 46 skipped.
- Frontend production build status: passed with `npm run build`.
- Security review identified missing demo-server dataset authorization and raw
  exception leakage. Fixes were deferred; limitations are documented in the
  README.

## Changes recorded after the project-completion prompt

### Repository audit

- Inspected the existing Vanna 2.0 backend, FastAPI routes, Lit web component
  frontend, SQLite data-quality services, SQL tools, configuration, and tests.
- Confirmed that profiling, cleaning, immutable versions, rollback, selected
  version SQL context, visualization components, and chat integration already
  existed.
- Confirmed the frontend production build and backend regression baseline.

### Dataset ingestion and management

- Added `GET /api/data-quality/datasets` for dataset and SQLite table listing.
- Added `POST /api/data-quality/datasets/upload` for CSV, JSON, and XLSX files.
- Added `POST /api/data-quality/datasets/preview` for bounded previews and
  column datatype metadata.
- Added server-generated dataset identifiers.
- Added upload metadata persistence in `_vanna_datasets`.
- Preserved original uploads under the database directory's `uploads` folder.
- Added filename, extension, empty-file, size-limit, and parsing validation.
- Added cleanup handling so failed database writes remove partially persisted
  original files.
- Added `openpyxl` and `python-multipart` to the project dependencies.

### FAISS memory correction

- Replaced the unrelated MD5-derived fallback vectors with deterministic
  token-feature embeddings.
- Added basic synonym normalization for related natural-language questions.
- Corrected fallback cosine search ranking to return cosine similarity rather
  than cosine distance.

### Tests and verification

- Added `tests/test_dataset_ingestion_api.py`.
- Verified upload, listing, preview, profiling, persistence, invalid filename,
  and unsupported-extension behavior.
- Focused data-quality and security-context tests: `16 passed`.
- Full backend test suite: `225 passed, 46 skipped`.
- Python syntax check passed with `python -m compileall -q src tests`.
- Frontend production build passed with `npm run build`.
- Python wheel build passed with `python -m build --wheel`.
- FastAPI server startup and `/docs` endpoint returned HTTP 200.

### Security review and limitations

- Reviewed SQL execution, dataset context, file handling, CORS, error handling,
  and data-quality routes.
- Identified missing authentication and dataset ownership authorization on
  data-quality endpoints.
- Identified possible raw backend exception leakage through chat responses.
- Security fixes were explicitly deferred by the user.
- Documented these limitations in `README.md`; the demo server must not be
  exposed directly to an untrusted network.

### Current readiness

- Local SQLite data ingestion, profiling, cleaning, versioning, rollback, SQL
  validation, frontend build, backend tests, and package build are verified.
- Live LLM integration remains unverified because provider credentials were not
  configured.
- External PostgreSQL, MySQL, and MSSQL service connectivity was not tested.
- Frontend automated tests are not available because the existing package
  defines no real test script.
- GitHub commit readiness could not be verified because the workspace is not a
  Git repository.

## Final completion and end-to-end verification

### Security fixes

- Added signed-session authentication helpers in `servers/base/auth.py`.
- Added secure-mode authentication using `VANNA_AUTH_SECRET`,
  `VANNA_ADMIN_EMAIL`, and `vanna_session`.
- Added per-upload `owner_id` metadata and authorization checks for listing,
  preview, profiling, recommendations, cleaning, versions, history, rollback,
  and dataset-aware chat.
- Preserved local demo compatibility when `require_auth` is disabled.
- Replaced raw FastAPI and Flask chat exception responses with generic client
  messages and server-side exception logging.
- Replaced forgeable admin email-cookie checks with signed-session checks in
  secure mode.
- Disabled permissive CORS by default; explicit origins are supported through
  `VANNA_CORS_ORIGINS`.
- Added `tests/test_security_controls.py`.

### Live LLM and configuration verification

- Confirmed supported live configuration variables for Gemini, OpenAI,
  Anthropic, and Azure OpenAI.
- Checked the environment without exposing values; no live provider credentials
  are configured.
- Live LLM generation and provider failure testing are therefore BLOCKED until
  a provider is configured outside chat.
- Added `.env.example` with documented non-secret configuration names.

### Frontend browser testing

- Added Playwright configuration and `tests/dashboard.spec.ts`.
- Added `npm run test:e2e`.
- Installed Chromium for local browser execution.
- Verified dashboard login, custom component loading, health endpoint, and
  dataset API reachability in a real browser context.
- Browser test result at that stage: `2 passed`.
- Frontend build remains passing with `npm run build`.
- Full visual chart interaction remains not tested.

### Complete workflow and demonstration materials

- Added `examples/demo_sales.csv` containing dates, categories, numeric values,
  missing values, and a duplicate record.
- Added `tests/test_end_to_end_demo_workflow.py` covering upload, preview,
  profiling, recommendations, cleaning preview, execution, version creation,
  version retrieval, and rollback.
- Added `docs/ARCHITECTURE.md`, `docs/DEMO_GUIDE.md`, `docs/VIVA_QA.md`, and
  `TESTING_REPORT.md`.
- Added 30 concise viva questions and answers.
- Documented live demonstration commands, limitations, and secure deployment
  configuration.
- Moved the demonstration guide, viva questions, architecture document, and
  testing report into this repository's `docs/` and root documentation
  locations.

### Dependency and repository checks

- Added Playwright as a frontend development dependency.
- Ran non-breaking `npm audit fix`; three moderate Storybook/uuid findings
  remain and require a breaking Storybook upgrade.
- Confirmed the workspace is still not a Git repository; no remotes or history
  were modified.

### Final measured verification

- Full backend suite from the project root: `230 passed, 46 skipped`.
- The added end-to-end sales workflow and security regression tests are included
  in that passing total.
- Documentation deliverables are stored in `docs/` and
  `TESTING_REPORT.md` within this repository.

### Final release validation

- Confirmed all provider variables are unset without exposing values:
  `GOOGLE_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`,
  `ANTHROPIC_API_KEY`, and `AZURE_OPENAI_API_KEY`.
- Live LLM generation, provider connectivity, generated SQL, and LLM-backed
  visualization are BLOCKED until a provider is configured outside chat.
- Expanded browser coverage to four passing tests: login, API reachability,
  complete local data-quality workflow, and API failure rendering.
- Full backend suite remains `231 passed, 46 skipped`; compilation and wheel
  build passed.
- The 46 skips are classified as optional ChromaDB/Qdrant/Ollama dependencies,
  missing provider credentials for Anthropic/OpenAI/Azure/Gemini, and related
  optional integration coverage; no actionable local implementation skip was
  identified.
- PyMySQL, mysql-connector-python, pyodbc, pymssql,
  snowflake-connector-python, and psycopg imports are available, but no
  external database services or credentials are configured, so connectivity is
  BLOCKED.
- `npm audit` reports three moderate Storybook/uuid findings; available fixes
  require a breaking Storybook major upgrade and were not applied.

### Dashboard box sizing refinement

- Added shared spacing, border, color, and control-height tokens to the Lit
  dashboard component.
- Standardized navigation gaps, metric-card dimensions, dataset control rows,
  panel padding, chart preview sizing, and mobile control wrapping.
- Reduced outer hero/status/configuration spacing in the FastAPI page template
  so the dashboard uses the viewport more efficiently.
- Verified the updated layout with the production frontend build, the complete
  Playwright suite (`7 passed`), the backend suite (`232 passed, 46 skipped`),
  and Python template syntax compilation.

### Dashboard upload and cleaning repair

- Root cause: the existing dashboard component had profiling and cleaning
  internals but no upload, dataset-list, preview, or visible management
  controls. The development server loads the compiled bundle, so the repaired
  component was rebuilt before browser validation.
- Added visible `Upload Dataset` file selection for CSV, JSON, and XLSX with
  client-side extension/10 MiB validation, loading state, success/error
  messages, generated dataset ID, and automatic list refresh.
- Added actual dataset listing, selection, metadata, bounded preview, and
  visible profiling and cleaning sections using the existing API routes.
- Expanded browser coverage to exercise real CSV upload, preview, profiling,
  cleaning preview/execution, version switching, rollback, and API error UI.
- Fixed rollback operation ID collisions across datasets by including the
  dataset identifier in the generated operation ID.
- Added JSON and XLSX ingestion regression coverage.
- Fresh browser validation against the rebuilt backend: `4 passed`.
- Final full backend suite after the dashboard and rollback fixes:
  `231 passed, 46 skipped`.

### Main-page dashboard rendering fix

- Traced the screenshot's live page at `http://127.0.0.1:8000`: the HTML
  contained `<data-quality-dashboard>`, but the server process was started
  without `--dev` and loaded `https://img.vanna.ai/vanna-components.js`.
- The external CDN bundle did not register this repository's custom dashboard,
  so the custom element was blank while Vanna Chat rendered normally.
- Restarted the actual application with `--dev`; `/static/vanna-components.js`
  returned HTTP 200 and contained both the dashboard registration and upload
  UI.
- Verified in the real browser that the dashboard is registered, the upload
  button and seven navigation sections are visible, and Vanna Chat remains
  available.
- Browser suite against the actual port 8000: `4 passed`.

### Compact dashboard and floating chat refinement

- Reworked the main workspace into compact navigable sections with a
  scrollable dataset list, compact quality metrics, and responsive mobile
  layout.
- Replaced the permanently expanded chat area with a fixed floating AI
  launcher and responsive popup while preserving the existing Vanna chat
  component and dataset/version context.
- Disabled the chat progress sidebar and hid the nested chat header in popup
  mode to avoid duplicated controls and wasted space.
- Rebuilt the frontend bundle and verified the actual running application.
- Final browser suite: `6 passed`; backend suite: `231 passed, 46 skipped`.

### Master UI/UX chat refinement

- Corrected the popup flex hierarchy so the Vanna host and inner layout fill
  the popup while the conversation area owns scrolling.
- Kept the composer as a non-shrinking bottom region and constrained popup
  height to the viewport.
- Replaced the oversized starter card in popup mode with a compact
  `Welcome to Insight Studio` state and existing prompt chips.
- Updated the composer placeholder to `Ask anything about your data...`.
- Added browser checks for welcome/composer visibility and popup viewport fit.
- Captured a live screenshot showing the refined desktop popup.
- Final validation: frontend build passed, `6` browser tests passed, and
  `231` backend tests passed with `46` environment-dependent skips.

### Interactive AI Analytics visualization builder

- Replaced the analytics placeholder with a real visualization builder using
  the existing Lit dashboard and `plotly-chart` component.
- Added dynamic chart controls for chart type, X-axis, Y-axis, Group By,
  aggregation, sorting, title, and bounded result limit.
- Added authenticated `POST /api/data-quality/chart-data`; it resolves the
  selected trusted dataset version and validates requested columns before
  aggregating with pandas.
- Supported bar, horizontal bar, line, area, pie, donut, scatter, histogram,
  box, and heatmap chart traces.
- Added backend tests for actual aggregation and invalid column handling plus a
  browser test for real chart generation.
- Final milestone validation: `232 passed, 46 skipped`, frontend build passed,
  and `7` browser tests passed.
