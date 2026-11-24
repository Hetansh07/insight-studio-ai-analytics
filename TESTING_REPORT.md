# Testing report

## Latest AI Analytics milestone

- Backend: `232 passed, 46 skipped`
- Frontend production build: passed
- Browser suite: `7 passed`
- Added authenticated `POST /api/data-quality/chart-data` with trusted
  dataset-version resolution, validated columns, bounded limits, numeric
  aggregation, grouping, sorting, and chart-ready Plotly traces.
- AI Analytics builder now exposes dynamic X/Y/Group By controls from actual
  profile columns, aggregation, sorting, title, limit, reset, and interactive
  Plotly preview.
- Verified a real browser-generated bar chart against the `Customer` dataset:
  25 actual plotted rows rendered in the Plotly preview.
- Backend chart regression verifies numeric aggregation, descending sort,
  column metadata, and invalid-column rejection.
- Floating Vanna AI chat remains available throughout dashboard navigation.

## Latest visual layout refinement

- Standardized dashboard spacing and control heights using shared CSS tokens.
- Equalized navigation buttons, metric cards, panel padding, and analytics
  control/preview geometry.
- Added bounded chart preview sizing and mobile wrapping to prevent horizontal
  overflow.
- Compacted the outer status and configuration panels in the page template.
- Validation: frontend build passed, browser suite `7 passed`, backend suite
  `232 passed, 46 skipped`, and Python template syntax check passed.

## Verified

- Backend: `231 passed, 46 skipped`
- Security and workflow subset: `16 passed`
- Python syntax: `py -3.13 -m compileall -q src tests`
- Frontend build: `npm run build`
- Browser tests against the actual application: `npm run test:e2e` —
  `6 passed` (login, API reachability, data-quality workflow, API error UI,
  floating chat, and mobile layout)
- Python package: `py -3.13 -m build --wheel`
- FastAPI health endpoint: HTTP 200
- Dataset upload, preview, profile, cleaning, versioning, rollback, and SQL
  selected-version tests pass.
- Security regression subset: `16 passed`
- Dashboard upload/workflow browser suite: `6 passed`
- Upload format regression coverage: CSV, JSON, and XLSX
- Live page verification: `data-quality-dashboard` registered, upload controls
  and navigation visible, local bundle returned HTTP 200, and Vanna chat
  remained present.
- Database driver imports: PyMySQL, mysql-connector-python, pyodbc, pymssql,
  snowflake-connector-python, and psycopg are available.

## Blocked or not tested

- Live LLM: BLOCKED; `GOOGLE_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`,
  `ANTHROPIC_API_KEY`, and `AZURE_OPENAI_API_KEY` are all unset. No provider
  call, generated SQL, or LLM-backed database result was claimed.
- External PostgreSQL, MySQL, and MSSQL service connectivity: BLOCKED because
  no configured service endpoints or credentials are available. Drivers import
  successfully.
- Full Plotly chart interaction: NOT TESTED; browser coverage verifies the
  data-quality workflow, while chat and chart rendering require live LLM output.
- GitHub commit/push: BLOCKED; the workspace is not a Git repository.
- npm audit: 3 moderate findings remain in Storybook/uuid dependency paths.
  The available fixes require a major Storybook upgrade and were not applied.

## Security regression coverage

`tests/test_security_controls.py` verifies signed authentication, forged-cookie
rejection, per-user dataset ownership, admin access to legacy tables, and
authenticated upload/profile access.

## Skipped-test classification

All 46 skips are environment-dependent: optional ChromaDB/Qdrant/Ollama
dependencies or missing Anthropic, OpenAI, Azure OpenAI, and Gemini
credentials. No skipped test was removed or falsely passed, and no actionable
local implementation skip was identified.

## Live LLM configuration

The repository supports Gemini (`GOOGLE_API_KEY` or `GEMINI_API_KEY`, with
`GEMINI_MODEL` such as `gemini-2.5-pro`), OpenAI, Anthropic, and Azure OpenAI.
The current environment has no provider configured, so live compatibility and
connectivity remain unverified. Configure a provider outside chat, then rerun
the provider-marked tests and the natural-language SQL workflow.

## Dashboard rendering diagnosis

The page HTML already contained the `<data-quality-dashboard>` element, but the
running port-8000 process had been started without `--dev`. It therefore loaded
the external CDN bundle, which does not register this repository's custom
dashboard element; the element rendered blank while Vanna Chat remained
visible. Restarting with `--dev` serves the rebuilt local bundle from
`/static/vanna-components.js`, which includes and registers the dashboard.
## Compact dashboard verification

- Rebuilt the Lit bundle after the floating-chat refinement.
- Verified the real port-8000 page shows the compact dashboard, visible upload
  action, section navigation, and floating AI launcher.
- Verified the popup opens with one application-level header, an accessible
  question input, and no progress sidebar.
- Browser regression suite: `6 passed`.

## Live Gemini and Vanna chat verification

- Provider integration: Gemini via `GeminiLlmService`.
- SDK status: `google-genai` installed successfully from the declared optional
  dependency.
- Effective model configuration: `gemini-2.5-pro` code default; `GEMINI_MODEL`
  is unset.
- Credential status: BLOCKED. `GOOGLE_API_KEY` and `GEMINI_API_KEY` are both
  unset. Values were not read or exposed.
- Provider connectivity: NOT RUN because initialization stops at the missing
  credential validation.
- Vanna-generated SQL, SQL validation, selected-version execution, result
  tables, Plotly charts, conversation history, and live error/timeout behavior:
  NOT VERIFIED against Gemini.
- The running browser server uses `mock_quickstart`, so its mock behavior was
  not counted as live AI verification.
- Exact blocker and setup instructions are recorded in [ERROR_REPORT.md](./ERROR_REPORT.md).

## Live Gemini verification result

- Website configuration status: `Gemini configured for this server session.`
- Real question sent through the floating chat popup:
  `What are the total sales by country?`
- Provider-backed response completed successfully.
- Actual result table rendered with 24 country rows and 2 columns
  (`Country`, `TotalSales`).
- Actual Plotly visualization rendered with title `Total Sales by Country`.
- Final natural-language response ranked the returned results, including USA
  `$523.06`, Canada `$303.96`, and France `$195.10`.
- Follow-up question `What is the square root of the moon's revenue?` also
  produced an actual one-row SQL result (`NULL`) and a completed response.
- Conversation history remained visible in the popup.
- Selected dataset context was `Customer`, original version.
- No API key value was logged, persisted, or included in this report.

This confirms one real Gemini-to-Vanna-to-SQL-to-SQLite-to-table/chart workflow.
Provider timeout and missing-credential paths remain covered by existing error
handling but were not forced during the successful configured session.

## Master UI/UX refinement verification

- Refined popup layout uses a constrained flex column with only the
  conversation area scrolling; the composer remains visible.
- Popup mode no longer requests the large backend starter card. It uses the
  compact Insight Studio welcome state and existing quick prompts instead.
- Welcome text is now `Welcome to Insight Studio` with compact responsive
  spacing.
- Composer placeholder is `Ask anything about your data...`.
- Live screenshot verified the popup fits the viewport, shows the welcome card,
  quick prompts, textarea, and send button without clipping.
- Browser assertions verify welcome visibility, composer visibility, popup
  viewport fit, minimize/reopen behavior, and mobile no-overflow behavior.
- Final browser suite after the refinement: `6 passed`.
