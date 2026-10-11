"""Validate the local KB stores (vector npz files + lexical JSON + manifest).

    precice-ai kb validate [--dir DIR]
    python scripts/validate_kb.py [--dir DIR]

Exit status is non-zero when any check fails. Checks:
  * every chunk matches the schema, with non-empty text and url
  * chunk_ids are unique, and identical across the vector and lexical stores
  * chunk_index is contiguous 0..chunk_count-1 per document
  * no excluded URL patterns (changelog entries, CONTRIBUTING, licences)
  * no chunk text is truncated mid-word with a following chunk
  * inline code survived cleaning (`<mapping:` appears in documentation)
  * the manifest agrees with the stores
Also prints per-category documents / chunks / average and median characters.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from precice_ai.kb import store
from precice_ai.kb.schema import CATEGORIES, SCHEMA_VERSION, KBFormatError, is_excluded_path, validate_chunk_dict

# Symptom of the old cleaner stripping inline code: a verb/linking word followed
# straight by punctuation, e.g. "In LaTeX, use ." or "then becomes :".
_GAP_RE = re.compile(r"\b(?:use|then|becomes?|set|call|named|tag|using)\s+[.,:;](?:\s|$)")
_MAX_REPORTED = 20


def _ends_mid_word(chunk: dict, following: dict) -> bool:
    """True when `chunk` stops inside a word that the next chunk continues."""
    text = chunk["text"].rstrip()
    next_tokens = following["text"].split()
    if not text or not text[-1].isalnum() or not next_tokens:
        return False
    last, first = text.split()[-1], next_tokens[0]
    if following["text"][:30] in text[-200:]:  # next chunk starts with the overlap: chunk is whole
        return False
    return last.isalpha() and first.isalpha() and len(first) > len(last) and first.startswith(last)


def validate_chunks(vector: dict[str, list[dict]], lexical: list[dict]) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    def err(msg: str) -> None:
        errors.append(msg)

    vec_all = [c for cat in vector.values() for c in cat]
    for label, chunks in (("vector", vec_all), ("lexical", lexical)):
        ids = [c.get("chunk_id") for c in chunks]
        if len(set(ids)) != len(ids):
            dupes = [i for i in set(ids) if ids.count(i) > 1][:5]
            err(f"{label}: chunk_ids are not unique (e.g. {dupes})")
        bad = 0
        for c in chunks:
            problems = validate_chunk_dict(c)
            if problems and bad < _MAX_REPORTED:
                err(f"{label}: {c.get('chunk_id', '?')}: {'; '.join(problems)}")
            bad += bool(problems)
        if bad > _MAX_REPORTED:
            err(f"{label}: {bad - _MAX_REPORTED} more schema violations not shown")

    # Cross-store identity: same ids, same records.
    v_by_id = {c["chunk_id"]: c for c in vec_all if "chunk_id" in c}
    l_by_id = {c["chunk_id"]: c for c in lexical if "chunk_id" in c}
    only_v, only_l = set(v_by_id) - set(l_by_id), set(l_by_id) - set(v_by_id)
    if only_v or only_l:
        err(f"stores disagree on chunk_ids: {len(only_v)} only in vector, {len(only_l)} only in lexical")
    differing = [i for i in v_by_id.keys() & l_by_id.keys() if v_by_id[i] != l_by_id[i]]
    if differing:
        err(f"{len(differing)} chunk records differ between vector and lexical stores (e.g. {differing[:3]})")

    # Per-document contiguity, exclusions, truncation.
    docs: dict[str, list[dict]] = defaultdict(list)
    for c in vec_all:
        if "doc_id" in c:
            docs[c["doc_id"]].append(c)
    truncated = 0
    for doc_id, items in docs.items():
        items.sort(key=lambda c: c.get("chunk_index", -1))
        counts = {c.get("chunk_count") for c in items}
        if [c.get("chunk_index") for c in items] != list(range(len(items))) or counts != {len(items)}:
            err(f"doc {doc_id} ({items[0].get('url')}): chunk_index not contiguous 0..{len(items) - 1} "
                f"or chunk_count {sorted(counts, key=str)} != {len(items)}")
        if is_excluded_path(items[0].get("url", "")):
            err(f"excluded URL present: {items[0].get('url')}")
        for a, b in zip(items, items[1:]):
            if _ends_mid_word(a, b):
                truncated += 1
                if truncated <= _MAX_REPORTED:
                    err(f"possible truncation: {a['chunk_id']} ends mid-word ({a['text'][-30:]!r})")
    if truncated > _MAX_REPORTED:
        err(f"{truncated - _MAX_REPORTED} more possibly-truncated chunks not shown")

    # Inline code must survive cleaning.
    docs_like = [c for cat in ("documentation", "tutorials") for c in vector.get(cat, [])]
    if docs_like:
        if not any("<mapping:" in c["text"] for c in docs_like):
            err("inline code check failed: no documentation/tutorials chunk contains '<mapping:'")
        if not any(re.search(r"`[^`\n]+`", c["text"]) for c in docs_like):
            err("inline code check failed: no backticked inline code in documentation/tutorials chunks")
    gaps = [c["chunk_id"] for c in vec_all if _GAP_RE.search(c.get("text", ""))]
    if gaps:
        warnings.append(f"{len(gaps)} chunks look like they lost inline code (e.g. {gaps[:3]})")

    return {"errors": errors, "warnings": warnings}


def category_table(vector: dict[str, list[dict]]) -> dict[str, dict]:
    return {cat: store.category_stats(chunks) for cat, chunks in vector.items()}


def validate_directory(directory: Path, *, lexical_name: str = "knowledge_base.json") -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    vector: dict[str, list[dict]] = {}
    for cat in CATEGORIES:
        path = directory / store.npz_name(cat)
        if not path.exists():
            warnings.append(f"category {cat}: no {path.name}")
            continue
        try:
            _, chunks, _ = store.read_vector_store(path)
        except KBFormatError as exc:
            errors.append(str(exc))
            continue
        vector[cat] = chunks
    lexical: list[dict] = []
    lex_path = directory / lexical_name
    if not lex_path.exists():
        errors.append(f"{lexical_name} not found in {directory}")
    else:
        try:
            lexical = store.read_lexical_store(lex_path)["chunks"]
        except KBFormatError as exc:
            errors.append(str(exc))
    if vector and lexical:
        # Lexical store may hold only the categories that exist as vectors.
        lexical = [c for c in lexical if c.get("category") in vector]
        result = validate_chunks(vector, lexical)
        errors += result["errors"]
        warnings += result["warnings"]

    manifest = store.read_manifest(directory)
    if manifest is None:
        warnings.append(f"{store.MANIFEST_NAME} missing")
    else:
        if manifest.get("schema_version") != SCHEMA_VERSION or not isinstance(manifest.get("categories"), dict):
            # Advisory file: a legacy one just means it has not been re-synced yet.
            warnings.append(
                f"{store.MANIFEST_NAME} is legacy/stale (schema_version {manifest.get('schema_version')!r}); "
                "run `precice-ai kb ingest` to refresh it"
            )
        else:
            for cat, chunks in vector.items():
                declared = store.manifest_categories(manifest).get(cat, {}).get("chunks")
                if declared != len(chunks):
                    errors.append(f"manifest says {declared} chunks for {cat}, store has {len(chunks)}")

    return {"ok": not errors, "errors": errors, "warnings": warnings, "stats": category_table(vector)}


def print_report(report: dict, file=sys.stdout) -> None:
    print(f"{'category':<14}{'documents':>10}{'chunks':>9}{'avg chars':>11}{'median':>9}", file=file)
    for cat, s in report["stats"].items():
        print(f"{cat:<14}{s['documents']:>10}{s['chunks']:>9}{s['avg_chars']:>11}{s['median_chars']:>9}", file=file)
    for w in report["warnings"]:
        print(f"WARNING: {w}", file=file)
    for e in report["errors"]:
        print(f"ERROR: {e}", file=file)
    print("KB validation " + ("PASSED" if report["ok"] else "FAILED"), file=file)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dir", type=Path, default=None, help="Store directory (default: the local kb_store).")
    p.add_argument("--lexical-name", default="knowledge_base.json")
    p.add_argument("--json", action="store_true", help="Print the report as JSON.")
    args = p.parse_args(argv)
    if args.dir is None:
        from precice_ai.core.knowledge_base import _get_kb_dir

        args.dir = _get_kb_dir()
    report = validate_directory(args.dir, lexical_name=args.lexical_name)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
