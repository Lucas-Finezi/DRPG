#!/usr/bin/env python3
"""Shared helpers for the equipment lots (L28-L30): costs, weights, and catalog entries built
from one row of an equipment table.

A row entry's text is the row as printed (with its table's caption kept in data); its
coverage is one structured segment pointing at the parsed columns. The table caption,
header row and group labels are covered by the section entry that presents the table.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import NODES, build, find, slugify  # noqa: E402

CP = {"cp": 1, "sp": 10, "ep": 50, "gp": 100, "pp": 1000}


def money(text):
    """'25 GP' -> {'amount': 25, 'unit': 'gp', 'cp': 2500}; other wording -> {'text': ...}."""
    t = text.strip()
    m = re.fullmatch(r"([\d,]+(?:\.\d+)?) (CP|SP|EP|GP|PP)", t)
    if not m:
        return {"text": t}
    amount = float(m.group(1).replace(",", ""))
    amount = int(amount) if amount.is_integer() else amount
    unit = m.group(2).lower()
    return {"amount": amount, "unit": unit, "cp": amount * CP[unit]}


def weight(text):
    """'2 lb.' / '1/4 lb.' / '1½ lb.' -> pounds; '—' -> None."""
    t = text.strip()
    if t in ("—", "-", ""):
        return None
    m = re.fullmatch(r"(\d+)?\s*(?:(\d+)/(\d+)|(½|¼|¾))?\s*lb\.?", t)
    if not m:
        return {"text": t}
    v = float(m.group(1) or 0)
    if m.group(2):
        v += int(m.group(2)) / int(m.group(3))
    if m.group(4):
        v += {"½": 0.5, "¼": 0.25, "¾": 0.75}[m.group(4)]
    return int(v) if v.is_integer() else v


def table_rows(caption, page=None, level=5):
    """(group label, row node) for every body row of a captioned table (group labels in italics)."""
    i = find(caption, level, page)
    out, group = [], None
    for n in NODES[i + 1:]:
        if n.type == "t":
            if n.text.startswith("| **"):
                continue
            out.append((group, n))
        elif n.type == "p" and re.match(r"^\*[^*].*\*$", n.text):
            group = n.text.strip("*")
        else:
            break
    return out


def row_entry(kind, name, node, lot, path, data, items=None, slug=None, facets=None, **kw):
    """Entry for one table row: text = the printed row, covered by the parsed data (and items)."""
    plan = [(None, "sys", ["/data/" + k for k in data if k not in ("rules", "tables")])] + list(items or [])
    return build(kind, slug or slugify(name), name, [node], lot, path, plan, data=data, facets=facets, **kw)
