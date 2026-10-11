"""Structure-preserving cleaning for KB ingestion.

Unlike the legacy `strip_markdown`, this keeps headings, lists, tables, fenced
code blocks and *inline code* (as backticked text). It only removes things that
are boilerplate: front matter, HTML/Liquid comments and tags, images, link
targets, navigation/footers/cookie banners (HTML path), Discourse quote blocks.

Inline code and code fences are protected with placeholders while the other
rewrites run, so nothing inside them is ever altered.
"""

from __future__ import annotations

import re

_FENCE_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})(?P<info>[^\n]*)$")
_FENCED_BLOCK_RE = re.compile(
    r"^[ \t]*(?P<f>`{3,}|~{3,})[^\n]*\n.*?^[ \t]*(?P=f)[ \t]*$", re.MULTILINE | re.DOTALL
)
# Inline code never spans a blank line, so a stray backtick can't swallow a paragraph.
_INLINE_CODE_RE = re.compile(r"(?<!`)(`+)(?!`)((?:(?!\n[ \t]*\n).)+?)(?<!`)\1(?!`)", re.DOTALL)

# Tags that are real HTML layout/markup. Anything else (e.g. the preCICE config
# tags <mapping:nearest-neighbor>, <participant>, <m2n:sockets>) is content.
_HTML_TAGS = (
    "a abbr address article aside audio b big blockquote body br button caption center cite "
    "col colgroup dd del details dfn div dl dt em embed fieldset figcaption figure font footer "
    "form h1 h2 h3 h4 h5 h6 head header hr html i iframe img input ins label legend li link main "
    "mark menu meta nav noscript object ol optgroup option p param picture pre s section select "
    "small source span strike strong style sub summary sup svg table tbody td tfoot th thead "
    "time title tr u ul video wbr script"
).split()
_HTML_TAG_RE = re.compile(r"</?(?:%s)(?=[\s/>])[^>]*>" % "|".join(_HTML_TAGS), re.IGNORECASE)

_LIQUID_NOTE_RE = re.compile(
    r"\{%-?\s*include\s+(?P<kind>note|important|warning|tip|todo|info)\.html\s+content\s*=\s*"
    r"(?P<q>[\"'])(?P<body>.*?)(?P=q)\s*-?%\}",
    re.DOTALL,
)

_PH = "\x00KB%d\x00"


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return (meta, body) for a document with optional YAML front matter."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    meta: dict[str, str] = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line and not line.startswith((" ", "\t", "-")):
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip("\"'")
    body = text[end + 4:].lstrip("\n")
    return meta, body


def _protect(text: str, store: list[str]) -> str:
    def stash(m: re.Match) -> str:
        store.append(m.group(0))
        return _PH % (len(store) - 1)

    text = _FENCED_BLOCK_RE.sub(stash, text)
    return _INLINE_CODE_RE.sub(stash, text)


def _restore(text: str, store: list[str]) -> str:
    return re.sub(r"\x00KB(\d+)\x00", lambda m: store[int(m.group(1))], text)


def clean_markdown(text: str) -> str:
    """Clean Markdown (optionally with Jekyll/Liquid and inline HTML) while
    preserving structure, code fences and inline code."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")

    # Protect code first: comments, Liquid and HTML inside fences/inline code are content.
    store: list[str] = []
    text = _protect(text, store)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)  # also kills disabled blocks
    # Liquid callouts carry real prose in their content="" attribute; keep it.
    text = _LIQUID_NOTE_RE.sub(
        lambda m: "\n> **%s:** %s\n" % (m.group("kind").capitalize(), m.group("body").strip()), text
    )

    text = re.sub(r"\{%-?\s*comment\s*-?%\}.*?\{%-?\s*endcomment\s*-?%\}", "", text, flags=re.DOTALL)
    text = re.sub(r"\{%.*?%\}", "", text, flags=re.DOTALL)           # Liquid tags
    text = re.sub(r"\{\{.*?\}\}", "", text, flags=re.DOTALL)         # Liquid output
    text = re.sub(r"^\{:[^}\n]*\}\s*$", "", text, flags=re.MULTILINE)  # kramdown attrs
    text = re.sub(r"\{:[^}\n]*\}", "", text)

    # Discourse BBCode-ish blocks / emoji / uploads
    text = re.sub(r"\[quote[^\]]*\].*?\[/quote\]", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"\[/?details[^\]]*\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)                  # images
    text = re.sub(r"!\[[^\]]*\]\[[^\]]*\]", "", text)
    text = re.sub(r"\[([^\]]+)\]\((?:[^()]|\([^)]*\))*\)", r"\1", text)  # links → text
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)             # ref links
    text = re.sub(r"^\[[^\]]+\]:\s+\S+.*$", "", text, flags=re.MULTILINE)  # link defs

    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<(script|style)\b.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<pre[^>]*>\s*(?:<code[^>]*>)?(.*?)(?:</code>)?\s*</pre>", r"\n```\n\1\n```\n",
                  text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<code[^>]*>(.*?)</code>", lambda m: "`%s`" % m.group(1).strip(),
                  text, flags=re.DOTALL | re.IGNORECASE)
    text = _HTML_TAG_RE.sub("", text)
    text = _unescape_entities(text)

    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return _restore(text, store).strip()


def _unescape_entities(text: str) -> str:
    return (
        text.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
        .replace("&quot;", '"').replace("&#39;", "'").replace("&amp;", "&")
    )


def clean_forum_post(raw: str) -> str:
    """Discourse raw post → cleaned markdown (also drops :emoji: shortcodes)."""
    cleaned = clean_markdown(raw)
    store: list[str] = []
    protected = _protect(cleaned, store)
    protected = re.sub(r"(?<![\w:/]):[a-z0-9_+\-]{2,}:(?![\w:/])", "", protected)
    protected = re.sub(r"upload://\S+", "", protected)
    return _restore(protected, store).strip()


# ---------------------------------------------------------------------------
# HTML → Markdown (live-crawl fallback path)
# ---------------------------------------------------------------------------

_BOILERPLATE_XPATH = (
    "//script|//style|//noscript|//nav|//footer|//aside|//form|//iframe|//svg|//header"
    "|//*[@role='navigation' or @role='banner' or @role='contentinfo']"
    "|//*[contains(translate(@class,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
    "'cookie') or contains(translate(@id,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'cookie')"
    " or contains(@class,'sidebar') or contains(@class,'navbar') or contains(@class,'footer')"
    " or contains(@class,'breadcrumb') or contains(@id,'sidebar') or contains(@id,'toc')"
    " or contains(@class,'consent') or contains(@class,'banner')]"
)


def html_to_markdown(raw_html: str) -> tuple[str, str]:
    """Convert a rendered HTML page into (title, markdown). Keeps headings,
    paragraphs, lists, tables, <pre> blocks and inline <code> as backticks."""
    from lxml import html as lxml_html

    tree = lxml_html.fromstring(raw_html)
    title_nodes = tree.xpath("//title/text()")
    title = re.sub(r"\s+", " ", title_nodes[0]).strip() if title_nodes else ""

    for node in tree.xpath(_BOILERPLATE_XPATH):
        parent = node.getparent()
        if parent is not None and node is not tree:
            parent.remove(node)

    roots = tree.xpath("//main|//article|//*[@id='content']|//*[contains(@class,'post-content')]")
    root = roots[0] if roots else (tree.find("body") if tree.find("body") is not None else tree)

    out: list[str] = []

    def inline(el) -> str:
        parts: list[str] = [el.text or ""]
        for child in el:
            tag = child.tag if isinstance(child.tag, str) else ""
            if tag == "code":
                parts.append("`%s`" % child.text_content().strip())
            elif tag == "br":
                parts.append("\n")
            elif tag in ("b", "strong"):
                parts.append("**%s**" % inline(child).strip())
            elif tag in ("i", "em"):
                parts.append("*%s*" % inline(child).strip())
            elif tag:
                parts.append(inline(child))
            parts.append(child.tail or "")
        return re.sub(r"[ \t\r\f\v]+", " ", "".join(parts))

    def walk(el) -> None:
        for child in el:
            tag = child.tag if isinstance(child.tag, str) else ""
            if re.fullmatch(r"h[1-6]", tag):
                out.append("%s %s" % ("#" * int(tag[1]), inline(child).strip()))
            elif tag == "pre":
                out.append("```\n%s\n```" % child.text_content().strip("\n"))
            elif tag == "p":
                out.append(inline(child).strip())
            elif tag in ("ul", "ol"):
                for i, li in enumerate(child.xpath("./li"), 1):
                    bullet = "-" if tag == "ul" else "%d." % i
                    out.append("%s %s" % (bullet, inline(li).strip()))
                out.append("")
            elif tag == "table":
                for tr in child.xpath(".//tr"):
                    cells = [inline(c).strip() for c in tr.xpath("./th|./td")]
                    out.append("| " + " | ".join(cells) + " |")
                out.append("")
            elif tag in ("blockquote",):
                out.append("> " + inline(child).strip())
            elif tag in ("div", "section", "article", "main", "span", "body", "details", "dl"):
                if len(child) == 0 and (child.text or "").strip():
                    out.append(inline(child).strip())
                else:
                    walk(child)
        out.append("")

    walk(root)
    return title, clean_markdown("\n\n".join(s for s in out if s is not None))
