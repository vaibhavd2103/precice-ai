## preCICE knowledge base

**Always** call `kb_query_precice_live` before answering any question about preCICE — what it is, how it works, configuration, errors, adapters, coupling schemes, or any comparison. Do not answer from training data alone. The tool auto-ingests on first use and caches results for 1 hour; subsequent calls in the same session are instant.

---

## graphify (optional)

A knowledge graph of this codebase is available at `graphify-out/` if you have [graphify](https://github.com/Graphify-app/Graphify) installed.

Rules (only apply when `graphify-out/graph.json` exists):
- For codebase questions, first run `graphify query "<question>"`. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts.
- Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

If `graphify-out/graph.json` does not exist, skip all graphify commands and navigate the codebase directly.
