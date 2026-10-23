"""Shared reader for extraction/SRD_CC_v5.2.1.md.

The markdown is produced by tools/extract/extract_srd.py. This module turns it into a flat
list of nodes, each carrying the PDF page it came from, so every consumer can cite pages.
"""
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

PAGE_RE = re.compile(r"<!-- page (\d+) -->")
HEAD_RE = re.compile(r"^(#{1,6}) (.*)$")


@dataclass
class Node:
    page: int
    type: str          # "h" heading | "p" paragraph | "t" table row
    text: str
    level: int = 0
    cells: list = field(default_factory=list)
    index: int = 0
    indented: bool = False  # table row printed indented under an italic group label ("↳ ")
    sidebar: bool = False   # inside a boxed sidebar (<!-- sidebar --> ... <!-- /sidebar -->)


def strip_md(text):
    """Remove markdown emphasis and escapes, keep the words."""
    text = text.replace("\\*", "\u0000").replace("\\|", "|")
    text = re.sub(r"\*+", "", text)
    return re.sub(r"\s+", " ", text.replace("\u0000", "*")).strip()


def slugify(name):
    s = unicodedata.normalize("NFKD", name)
    s = s.replace("’", "").replace("'", "").replace("+", "plus")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^A-Za-z0-9]+", "-", s.lower()).strip("-")
    return s


def split_cells(row):
    inner = row.strip()[1:-1]
    parts = re.split(r"(?<!\\) \| ", " " + inner + " ")
    return [strip_md(p) for p in parts]


def load(path):
    nodes, page, side = [], 0, False
    for raw in Path(path).read_text(encoding="utf-8").split("\n"):
        m = PAGE_RE.match(raw)
        if m:
            page = int(m.group(1))
            continue
        if raw.startswith("<!-- sidebar -->"):
            side = True
            continue
        if raw.startswith("<!-- /sidebar -->"):
            side = False
            continue
        if not raw.strip() or raw.startswith("<!--"):
            continue
        h = HEAD_RE.match(raw)
        if h:
            nodes.append(Node(page, "h", strip_md(h.group(2)), level=len(h.group(1)), sidebar=side))
        elif raw.startswith("| ") and raw.rstrip().endswith("|"):
            cells = split_cells(raw)
            indented = cells[0].startswith("↳ ")
            if indented:
                cells[0] = cells[0][2:]
            nodes.append(Node(page, "t", raw, cells=cells, indented=indented, sidebar=side))
        else:
            nodes.append(Node(page, "p", raw, sidebar=side))
    for i, n in enumerate(nodes):
        n.index = i
        n.sidebar = n.sidebar or False
    return nodes
