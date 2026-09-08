"""Shared text-cleaning helpers for every KB ingestion path.

Strips Markdown syntax, embedded/raw HTML, and Jekyll/Liquid template
tags so git-checked-out docs, live-fetched HTML pages, forum posts, and
GitHub issue/PR bodies all produce the same kind of plain text before
chunking and embedding.
"""

from __future__ import annotations

import re


def strip_markdown(text: str) -> str:
    """Best-effort Markdown/HTML/Liquid → plain text."""
    # Comments (including disabled Jekyll/Liquid blocks) must go first and
    # be dropped whole, not unwrapped — otherwise their contents leak in.
    text = re.sub(r"<!--[\s\S]*?-->", " ", text)
    text = re.sub(r"\{%.*?%\}", " ", text, flags=re.DOTALL)   # Liquid tags
    text = re.sub(r"\{\{.*?\}\}", " ", text, flags=re.DOTALL) # Liquid output
    text = re.sub(r"```[\s\S]*?```", " ", text)                # code blocks
    text = re.sub(r"`[^`]+`", " ", text)                       # inline code
    text = re.sub(r"!\[.*?\]\(.*?\)", " ", text)               # images
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)      # links → text
    text = re.sub(r"^#{1,6}\s+(.*)$", r"\n\1.\n", text, flags=re.MULTILINE)  # headings
    text = re.sub(r"[*_]{1,2}([^*_]+)[*_]{1,2}", r"\1", text)  # bold/italic
    text = re.sub(r"^\s*[-*+]\s+", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"\|[^\n]+\|", " ", text)                    # tables
    text = re.sub(r"<[^>]+>", " ", text)                       # any remaining raw HTML tags
    text = re.sub(r"[ \t]+", " ", text)
    return text