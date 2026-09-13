## preCICE knowledge base

Before answering any question about preCICE — what it is, how it works, configuration, errors, adapters, coupling schemes, or any comparison — first call `kb_precice_status()` and inspect the relevant category in `.precice-ai/kb_store`.

Use this decision tree:

- If the relevant category is present and `is_fresh` is true (less than 96 hours old), use `kb_query_precice(...)`.
- If the relevant category is missing, freshness is unknown, or it is 96 hours old or older, use `kb_query_precice_live(...)` so it refreshes the category first and then answers from the updated local KB.
- If you need an explicit refresh step before querying, call `kb_ingest_precice_data(...)` for that category.
- Do not answer from training data alone when a KB tool should be used.

---

## graphify (optional)

A knowledge graph of this codebase is available at `graphify-out/` if you have [graphify](https://github.com/Graphify-app/Graphify) installed.

Rules (only apply when `graphify-out/graph.json` exists):
- For codebase questions, first run `graphify query "<question>"`. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts.
- Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

If `graphify-out/graph.json` does not exist, skip all graphify commands and navigate the codebase directly.
