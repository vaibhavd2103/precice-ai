"""Tests for the canonical KB chunk format: schema, cleaning, chunking,
stores, compatibility errors and the validator. Run with:

    python -m unittest discover -s tests      (or: pytest tests)
"""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from precice_ai.kb import store
from precice_ai.kb.builder import build_forum_chunks, build_github_chunks
from precice_ai.kb.chunking import (
    HARD_MAX_CHARS,
    TARGET_MAX_CHARS,
    Deduper,
    RawChunk,
    Segment,
    assemble_document,
    chunk_markdown,
    chunk_segments,
)
from precice_ai.kb.cleaning import clean_forum_post, clean_markdown, html_to_markdown, parse_frontmatter
from precice_ai.kb.fetch import is_bot_user
from precice_ai.kb.schema import (
    SCHEMA_VERSION,
    KBFormatError,
    is_excluded_path,
    make_chunk_id,
    make_doc_id,
    normalize_url,
    validate_chunk_dict,
)
from precice_ai.kb.validate import _ends_mid_word, validate_chunks, validate_directory

PROSE = "Mapping data between meshes is a core feature of preCICE and works for many solvers. " * 6


def _make_chunks(category="documentation", url="https://precice.org/a.html", texts=None, title="Doc"):
    texts = texts or [PROSE + "<mapping:nearest-neighbor> `x`", PROSE + " second"]
    return assemble_document(
        category=category, source=f"{category}-website", url=url, title=title,
        raw_chunks=[RawChunk(["Sec"], t) for t in texts], dedup=Deduper(),
    )


class SchemaTests(unittest.TestCase):
    def test_url_normalisation(self):
        self.assertEqual(
            normalize_url("http://www.precice.org/docs/?utm_source=x&a=1#frag"),
            "https://precice.org/docs?a=1",
        )
        self.assertEqual(normalize_url("https://precice.org/index.html"), "https://precice.org")
        self.assertEqual(normalize_url("https://precice.github.io/x.html/"), "https://precice.org/x.html")

    def test_ids_are_deterministic(self):
        a = make_doc_id(normalize_url("https://precice.org/x.html"))
        self.assertEqual(a, make_doc_id(normalize_url("http://precice.org/x.html/")))
        self.assertEqual(make_chunk_id(a, 3), f"{a}#3")

    def test_exclusions(self):
        for p in (
            "tutorials/flap/changelog-entries/12.md", "CHANGELOG.md", "docs/CONTRIBUTING.md",
            "LICENSE", "https://github.com/precice/precice/blob/develop/LICENSE.txt",
            "https://precice.org/changelog.html",
        ):
            self.assertTrue(is_excluded_path(p), p)
        for p in ("docs/configuration-mapping.md", "https://precice.org/community-contribute.html"):
            self.assertFalse(is_excluded_path(p), p)

    def test_validate_chunk_dict(self):
        good = _make_chunks()[0].to_dict()
        self.assertEqual(validate_chunk_dict(good), [])
        for key, value in (("text", "  "), ("url", ""), ("chunk_id", "nope"), ("category", "x")):
            bad = {**good, key: value}
            self.assertTrue(validate_chunk_dict(bad), key)
        self.assertTrue(validate_chunk_dict({k: v for k, v in good.items() if k != "extra"}))


class CleaningTests(unittest.TestCase):
    def test_inline_code_survives(self):
        text = "Use `<mapping:nearest-neighbor>` here. In LaTeX, use `\\hyphenation{preCICE}`."
        self.assertEqual(clean_markdown(text), text)

    def test_bare_precice_tags_are_kept_but_html_removed(self):
        out = clean_markdown("Set <participant> and <mapping:rbf> in <b>bold</b><br>next")
        self.assertIn("<participant>", out)
        self.assertIn("<mapping:rbf>", out)
        self.assertNotIn("<b>", out)

    def test_fences_are_verbatim(self):
        code = '```xml\n<m2n:sockets acceptor="A" connector="B"/>\n{{ not liquid }}\n<!-- keep -->\n```'
        self.assertIn(code, clean_markdown(f"intro\n\n{code}\n\noutro"))

    def test_liquid_and_comments(self):
        out = clean_markdown(
            '{% include note.html content="Mind `<tag>`!" %}\n<!-- hidden -->\n{% include toc.html %}\ntext'
        )
        self.assertIn("> **Note:** Mind `<tag>`!", out)
        self.assertNotIn("hidden", out)
        self.assertNotIn("{%", out)

    def test_links_images_frontmatter(self):
        meta, body = parse_frontmatter("---\ntitle: T\npermalink: /x.html\n---\nbody")
        self.assertEqual((meta["title"], body), ("T", "body"))
        self.assertEqual(clean_markdown("See [the docs](a/b.html) ![img](x.png) now"), "See the docs  now")

    def test_forum_quotes_and_emoji(self):
        out = clean_forum_post('[quote="a, post:1"]old[/quote]\nThanks :smile: see `a:b:c`')
        self.assertNotIn("old", out)
        self.assertNotIn(":smile:", out)
        self.assertIn("`a:b:c`", out)

    def test_html_to_markdown_keeps_code_drops_boilerplate(self):
        title, md = html_to_markdown(
            "<html><head><title>T</title></head><body><nav>MENU</nav><div class='cookie-banner'>cookies</div>"
            "<main><h2>Mapping</h2><p>Use <code>&lt;mapping:nn&gt;</code> now.</p>"
            "<pre>a\nb</pre></main><footer>FOOT</footer></body></html>"
        )
        self.assertEqual(title, "T")
        self.assertIn("## Mapping", md)
        self.assertIn("`<mapping:nn>`", md)
        self.assertIn("```\na\nb\n```", md)
        for junk in ("MENU", "cookies", "FOOT"):
            self.assertNotIn(junk, md)


class ChunkingTests(unittest.TestCase):
    def test_sections_and_atomic_code(self):
        code = "```xml\n" + "\n".join(f'<mapping:nearest-neighbor from="A{i}" to="B"/>' for i in range(40)) + "\n```"
        md = f"# Doc\n\n## Config\n\n{PROSE}\n\n{code}\n\n### Mapping\n\n{PROSE}\n\n{PROSE}\n\n{PROSE}"
        chunks = chunk_markdown(md, "Doc")
        self.assertTrue(any(code in c.text for c in chunks), "code block must stay in one chunk")
        self.assertEqual(chunks[0].section_path, ["Config"])
        self.assertTrue(all(len(c.text) <= HARD_MAX_CHARS for c in chunks))
        for c in chunks:
            self.assertEqual(c.text.count("```") % 2, 0, "no fence may be cut in half")

    def test_overlap_between_consecutive_chunks(self):
        paragraphs = [f"Paragraph {i}. " + "word " * 60 for i in range(12)]
        chunks = chunk_markdown("\n\n".join(paragraphs), "T")
        self.assertGreater(len(chunks), 2)
        for a, b in zip(chunks, chunks[1:]):
            self.assertLessEqual(len(b.text) - len(b.text.split("\n\n", 1)[-1]), 160 + 2)
            self.assertIn(b.text[:40], a.text)
        self.assertTrue(all(len(c.text) <= TARGET_MAX_CHARS + 200 for c in chunks))

    def test_oversized_code_block_is_split_with_fences(self):
        code = "```\n" + "\n".join("line %d %s" % (i, "x" * 60) for i in range(300)) + "\n```"
        chunks = chunk_markdown(code, "T")
        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertTrue(c.text.startswith("```") and c.text.rstrip().endswith("```"))
            self.assertLessEqual(len(c.text), HARD_MAX_CHARS)

    def test_assemble_numbers_drops_short_and_duplicates(self):
        dedup = Deduper()
        raw = [RawChunk([], PROSE), RawChunk([], "tiny"), RawChunk([], PROSE), RawChunk([], PROSE + "other")]
        stats: dict = {}
        out = assemble_document(
            category="about", source="about-website", url="https://precice.org/x", title="X",
            raw_chunks=raw, dedup=dedup, stats=stats,
        )
        self.assertEqual([c.chunk_index for c in out], [0, 1])
        self.assertTrue(all(c.chunk_count == 2 for c in out))
        self.assertEqual((stats["dropped_short"], stats["dropped_duplicate"]), (1, 1))
        self.assertTrue(out[0].embed_text.startswith("X\n\n"))

    def test_embed_text_has_title_and_section_path(self):
        c = _make_chunks(title="Cfg")[0]
        self.assertTrue(c.embed_text.startswith("Cfg > Sec\n\n"))

    def test_segments_merge_short_posts_keep_order(self):
        segs = [Segment(f"Post {i}", "short reply number %d" % i, {"post_number": i}) for i in range(1, 6)]
        out = chunk_segments(segs)
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0][1].startswith("[Post 1]"))
        self.assertEqual([e["post_number"] for e in out[0][2]], [1, 2, 3, 4, 5])


@dataclass
class _Post:
    post_number: int
    raw: str
    is_accepted_solution: bool = False


@dataclass
class _Topic:
    title: str
    url: str
    posts: list = field(default_factory=list)
    created_at: str = "2026-01-01T00:00:00Z"
    updated_at: str = "2026-01-02T00:00:00Z"
    reply_count: int = 2
    tags: list = field(default_factory=lambda: ["mapping"])


class SourceBuilderTests(unittest.TestCase):
    def test_forum_chunks_metadata(self):
        topic = _Topic("How to map?", "https://precice.discourse.group/t/how-to-map/1", [
            _Post(2, "Try `<mapping:rbf>` " + PROSE, True),
            _Post(1, "I need help mapping data. " + PROSE),
        ])
        chunks = build_forum_chunks([topic])
        self.assertTrue(chunks[0].text.startswith("[Post 1]"), "opening post first")
        accepted = [c for c in chunks if c.extra["is_accepted_solution"]]
        self.assertEqual(len(accepted), 1)
        self.assertEqual(chunks[0].extra["tags"], ["mapping"])
        self.assertIn("How to map?", chunks[0].embed_text)

    def test_github_chunks_metadata_and_template_removal(self):
        checklist = "- [ ] I added a changelog file\n"
        items = [
            {"number": n, "title": f"Fix {n}", "url": f"https://github.com/precice/precice/pull/{n}",
             "state": "closed", "labels": ["bug"], "merged": True, "closed_at": "2026-01-01T00:00:00Z",
             "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
             "body": f"{checklist}Unique description {n}. " + PROSE.replace("Mapping", f"Case{n}"),
             "comments": [{"body": f"Looks good {n}. " + PROSE.replace("Mapping", f"Rev{n}"), "created_at": None}]}
            for n in range(1, 8)
        ]
        chunks = build_github_chunks("pulls", "precice/precice", items)
        self.assertTrue(all("changelog file" not in c.text for c in chunks))
        first = chunks[0]
        self.assertEqual(first.extra["number"], 1)
        self.assertTrue(first.extra["merged"])
        self.assertEqual(first.title, "#1 Fix 1")

    def test_bot_detection(self):
        self.assertTrue(is_bot_user({"login": "dependabot[bot]", "type": "Bot"}))
        self.assertTrue(is_bot_user({"login": "github-actions"}))
        self.assertFalse(is_bot_user({"login": "uekerman", "type": "User"}))


class StoreAndValidationTests(unittest.TestCase):
    def _write_store(self, directory: Path, model="m1"):
        for cat in ("documentation", "forum"):
            chunks = _make_chunks(category=cat, url=f"https://example.org/{cat}")
            emb = np.random.default_rng(0).normal(size=(len(chunks), 4)).astype(np.float32)
            store.write_vector_store(directory / store.npz_name(cat), cat, chunks, emb, model)
        return store.finalize_store(directory, lexical_name="knowledge_base.json")

    def test_roundtrip_finalize_and_validate(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            manifest = self._write_store(d)
            self.assertEqual(manifest["schema_version"], SCHEMA_VERSION)
            self.assertEqual((manifest["model"], manifest["dim"]), ("m1", 4))
            self.assertEqual(manifest["totals"]["chunks"], 4)
            report = validate_directory(d)
            self.assertTrue(report["ok"], report["errors"])
            self.assertEqual(report["stats"]["forum"]["documents"], 1)
            # identical ids in both stores
            lex = {c["chunk_id"] for c in store.read_lexical_store(d / "knowledge_base.json")["chunks"]}
            _, vec_chunks, _ = store.read_vector_store(d / store.npz_name("documentation"))
            self.assertTrue({c["chunk_id"] for c in vec_chunks} <= lex)

    def test_model_and_schema_mismatch_raise_clear_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            self._write_store(d)
            path = d / store.npz_name("documentation")
            with self.assertRaisesRegex(KBFormatError, "EMBEDDING_MODEL.*re-ingest|Re-ingest"):
                store.read_vector_store(path, expected_model="other-model")
            np.savez_compressed(
                path, embeddings=np.zeros((1, 4), np.float32), chunks=np.array("[]"),
                chunk_ids=np.array(["x"]),
                meta=np.array(json.dumps({"schema_version": 0, "model": "m1"})),
            )
            with self.assertRaisesRegex(KBFormatError, "schema_version 0"):
                store.read_vector_store(path)
            legacy = d / "legacy.npz"
            np.savez_compressed(legacy, embeddings=np.zeros((1, 4), np.float32), chunks=np.array("[]"))
            self.assertIn("legacy", store.check_npz_compat(legacy))
            lex = d / "lex.json"
            lex.write_text(json.dumps({"updated_at": "x", "chunks": []}))
            with self.assertRaisesRegex(KBFormatError, "legacy or incompatible"):
                store.read_lexical_store(lex)

    def test_validator_catches_problems(self):
        good = [c.to_dict() for c in _make_chunks()]
        ok = validate_chunks({"documentation": good}, good)
        self.assertEqual(ok["errors"], [])

        def errors(vec, lex=None):
            return validate_chunks({"documentation": vec}, lex if lex is not None else vec)["errors"]

        gap = [dict(good[1], chunk_index=2, chunk_id=make_chunk_id(good[1]["doc_id"], 2))]
        self.assertTrue(any("contiguous" in e for e in errors([good[0]] + gap)))
        self.assertTrue(any("not unique" in e for e in errors([good[0], good[0]])))
        self.assertTrue(any("disagree" in e for e in errors(good, good[:1])))
        excluded = [dict(c, url="https://x.org/changelog-entries/1.md") for c in good]
        self.assertTrue(any("excluded URL" in e for e in errors(excluded)))
        no_code = [dict(c, text=PROSE + str(i)) for i, c in enumerate(good)]
        for c in no_code:
            c["char_len"] = len(c["text"])
        self.assertTrue(any("inline code" in e for e in errors(no_code)))

    def test_truncation_detector(self):
        a = {"text": "This sentence stops inform"}
        self.assertTrue(_ends_mid_word(a, {"text": "information about the rest"}))
        self.assertFalse(_ends_mid_word({"text": "A complete sentence."}, {"text": "Next"}))
        overlap = {"text": "end of previous chunk with overlap"}
        self.assertFalse(_ends_mid_word({"text": "start. end of previous chunk with overlap"}, overlap))


if __name__ == "__main__":
    unittest.main()
