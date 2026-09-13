#!/usr/bin/env python3
"""One-time-ish WordPress WXR export -> Zola content converter.

Conservative on purpose: only paragraph/heading/list blocks (the prose a
non-technical editor will actually retype) get converted to real markdown
syntax. Everything else (images, tables, blockquotes, embeds, raw wp:html
blocks like the Plant Safari widget) is left as the original HTML, verbatim,
inside the markdown file - Zola's CommonMark renderer passes raw HTML blocks
through unchanged, so this is safe rather than lossy.

Usage: python3 scripts/migrate-from-wordpress.py <path-to-wxr.xml> <content-dir>
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}

BLOCK_RE = re.compile(r"<!--\s*/?wp:[\w/-]+(?:\s+\{.*?\})?\s*-->\n?")


def inline_to_md(node) -> str:
    """Render inline content (text + a/strong/em/b/i) of a single tag as markdown text."""
    out = []
    for child in node.children:
        if isinstance(child, NavigableString):
            out.append(str(child))
        elif isinstance(child, Tag):
            if child.name in ("strong", "b"):
                out.append(f"**{inline_to_md(child)}**")
            elif child.name in ("em", "i"):
                out.append(f"*{inline_to_md(child)}*")
            elif child.name == "a" and child.get("href"):
                out.append(f"[{inline_to_md(child)}]({child['href']})")
            elif child.name == "br":
                out.append("  \n")
            else:
                out.append(inline_to_md(child))
    return "".join(out).strip()


def convert_list(tag, ordered: bool, depth: int = 0) -> str:
    lines = []
    indent = "  " * depth
    idx = 1
    for li in tag.find_all("li", recursive=False):
        nested = li.find(["ul", "ol"])
        text_parts = []
        for child in li.children:
            if isinstance(child, Tag) and child.name in ("ul", "ol"):
                continue
            if isinstance(child, NavigableString):
                text_parts.append(str(child))
            elif isinstance(child, Tag):
                text_parts.append(inline_to_md(BeautifulSoup(f"<span>{child}</span>", "html.parser").span))
        text = "".join(text_parts).strip()
        marker = f"{idx}." if ordered else "-"
        lines.append(f"{indent}{marker} {text}")
        if nested:
            lines.append(convert_list(nested, nested.name == "ol", depth + 1))
        idx += 1
    return "\n".join(lines)


def html_fragment_to_md(html: str) -> str:
    """Convert one WP block's inner HTML to markdown where recognized, else pass through raw."""
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for el in soup.find_all(recursive=False):
        if el.name == "p":
            text = inline_to_md(el)
            if text:
                out.append(text)
        elif el.name and re.fullmatch(r"h[1-6]", el.name):
            level = int(el.name[1])
            out.append(f"{'#' * level} {inline_to_md(el)}")
        elif el.name == "ul":
            out.append(convert_list(el, ordered=False))
        elif el.name == "ol":
            out.append(convert_list(el, ordered=True))
        else:
            # images, tables, blockquotes, embeds, raw html blocks, etc. -
            # keep verbatim, Zola/CommonMark passes raw HTML blocks through.
            out.append(str(el).strip())
    return "\n\n".join(part for part in out if part)


def wp_content_to_markdown(raw: str) -> str:
    # Split on the wp:xxx block comments, keeping each block's inner HTML as
    # one chunk - simplest robust way to avoid one block's tags leaking into
    # the next.
    chunks = [c.strip() for c in BLOCK_RE.split(raw) if c.strip()]
    return "\n\n".join(html_fragment_to_md(chunk) for chunk in chunks if html_fragment_to_md(chunk))


def toml_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def write_page(path: Path, title: str, date: str, content_md: str, *, draft: bool = False, extra_front: str = ""):
    # Zola section files (_index.md) don't accept a `date` field at all - only
    # regular pages do.
    is_section = path.name == "_index.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    front = f'+++\ntitle = "{toml_escape(title)}"\n'
    if not is_section:
        front += f"date = {date[:10]}\n"
    if draft:
        front += "draft = true\n"
    front += extra_front
    front += "+++\n\n"
    path.write_text(front + content_md + "\n")


def main():
    wxr_path = Path(sys.argv[1])
    content_dir = Path(sys.argv[2])

    tree = ET.parse(wxr_path)
    channel = tree.getroot().find("channel")
    items = channel.findall("item")

    by_id = {}
    for item in items:
        pid = item.findtext("wp:post_id", namespaces=NS)
        by_id[pid] = item

    def slug_of(item):
        return item.findtext("wp:post_name", namespaces=NS)

    for item in items:
        post_type = item.findtext("wp:post_type", namespaces=NS)
        if post_type not in ("page", "post"):
            continue

        title = item.findtext("title") or ""
        slug = slug_of(item) or "untitled"
        date = item.findtext("wp:post_date", namespaces=NS) or "2025-01-01 00:00:00"
        status = item.findtext("wp:status", namespaces=NS)
        raw_content = item.findtext("content:encoded", namespaces=NS) or ""
        md = wp_content_to_markdown(raw_content)
        draft = status == "draft"

        if post_type == "page":
            parent_id = item.findtext("wp:post_parent", namespaces=NS)
            if slug == "home":
                write_page(content_dir / "_index.md", title, date, md, draft=draft)
            elif parent_id and parent_id != "0" and parent_id in by_id:
                parent_slug = slug_of(by_id[parent_id])
                write_page(content_dir / parent_slug / f"{slug}.md", title, date, md, draft=draft)
            else:
                # Give every top-level page its own directory (_index.md) so
                # it can later grow child pages without restructuring, and so
                # a page with no body content (e.g. "News") still becomes a
                # valid Zola section.
                write_page(content_dir / slug / "_index.md", title, date, md, draft=draft)
        else:  # post
            cats = sorted({c.text for c in item.findall("category") if c.text}, key=str.lower)
            tags_list = ", ".join(f'"{toml_escape(c)}"' for c in cats)
            tags_toml = f"[taxonomies]\ntags = [{tags_list}]\n" if cats else ""
            write_page(content_dir / "blog" / f"{slug}.md", title, date, md, draft=draft, extra_front=tags_toml)

    print("Done.")


if __name__ == "__main__":
    main()
