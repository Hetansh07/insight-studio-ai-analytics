# Viva questions and concise answers

1. **What problem is solved?** Natural-language analysis of tabular data without requiring users to write SQL.
2. **Why Vanna 2.0?** It provides an agent, tool registry, user context, streaming, and LLM integration.
3. **Why FastAPI?** It provides typed request validation, async handlers, and OpenAPI documentation.
4. **Why pandas?** It provides reliable tabular parsing, profiling, and deterministic transformations.
5. **Why SQLite locally?** It is portable, transactional, and requires no separate database service.
6. **How are uploads identified?** The server generates a random dataset identifier.
7. **Are original files overwritten?** No, original bytes and source tables remain preserved.
8. **How are duplicates detected?** pandas `duplicated()` counts repeated complete rows.
9. **How is completeness scored?** Missing cells are divided by total cells and converted to a 0–100 score.
10. **How is uniqueness scored?** Duplicate rows are divided by row count and deducted from 100.
11. **What happens on an empty dataset?** Division-by-zero guards return zero percentages and safe scores.
12. **How is cleaning approved?** Preview is separate; execution requires `approved=true`.
13. **How is lineage stored?** `_vanna_data_quality_history` records actions, versions, timestamps, and reports.
14. **How does rollback work?** It copies a historical table into a new version rather than overwriting data.
15. **Can one user read another user's upload?** Secure mode checks the stored owner ID before every access.
16. **How is SQL protected?** Only one read-only `SELECT` or CTE is accepted.
17. **Can the frontend choose any table?** No, the server resolves the selected version from trusted metadata.
18. **How are results visualized?** Vanna components and Plotly render returned tabular data.
19. **What is a CTE?** A read-only common table expression that can precede a final `SELECT`.
20. **How are provider keys handled?** They come from environment variables or transient admin configuration and are not committed.
21. **What is demo authentication?** A local UI cookie demonstration; it is not production authentication.
22. **What enables secure authentication?** A signed `vanna_session` with `VANNA_AUTH_SECRET`.
23. **What happens on provider failure?** The backend logs details and returns a generic client-facing failure.
24. **Why are some tests skipped?** They require optional packages, external services, or credentials.
25. **What is the main limitation?** A live LLM cannot be verified without a configured provider credential.
26. **How is SQL executed?** The selected injected `SqlRunner` executes the validated query.
27. **Why use immutable versions?** They make comparisons, auditability, and rollback safe.
28. **How is file traversal prevented?** Filenames must be basename-only and have an allowed extension.
29. **How are large uploads handled?** The API enforces a 10 MiB default limit.
30. **What is needed for production?** Real identity/session infrastructure, strict CORS origins, secret management, and read-only database credentials.
