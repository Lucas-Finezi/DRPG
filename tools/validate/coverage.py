#!/usr/bin/env python3
"""Source coverage audit: is every paragraph, table row and heading of the SRD inside some entry?

Each markdown node gets an owning lot (outline section or sidebar from the L00 inventory).
A node is covered when its text occurs in the `text` of an entry, or in a rule quoted in
system.json. Chapter titles and section headings that only group other sections count as
structure, not content.

Usage: python3 -I tools/validate/coverage.py [L02 L03 ...]   (default: lots that have entries)
Exit status 1 if a requested lot has uncovered nodes.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "inventory"))
from srdmd import load, strip_md  # noqa: E402

INV = ROOT / "inventory" / "dnd5e" / "srd-5.2.1"


def norm(s):
    return re.sub(r"\s+", " ", strip_md(s)).strip()


def main(lots):
    nodes = load(ROOT / "extraction" / "SRD_CC_v5.2.1.md")
    outline = json.loads((INV / "outline.json").read_text(encoding="utf-8"))
    sections, sidebars = outline["sections"], {s["title"]: s["lot"] for s in outline["sidebars"]}

    # owner lot per node: the last outline heading (levels 1-4, in document order) before it,
    # or the sidebar it belongs to
    relocated = {t["caption"]: t["lot"] for t in outline.get("relocated_tables", [])}
    heads = [n for n in nodes if n.type == "h" and n.level <= 4 and not n.sidebar]
    owner, k, current, side_lot, table_lot = {}, 0, None, None, None
    for n in nodes:
        if k < len(heads) and n is heads[k]:
            current = sections[k]["lot"]
            k += 1
        if n.sidebar and n.type == "h" and n.level == 5:
            side_lot = sidebars.get(n.text, current)
        if n.type == "h" and n.level == 5 and not n.sidebar:
            table_lot = relocated.get(n.text)
        elif n.type != "t":
            table_lot = None
        owner[n.index] = side_lot if n.sidebar else (table_lot if table_lot and n.type in ("t", "h") else current)
        for f in outline.get("relocated_fragments", []):
            if n.page == f["page"] and n.text.startswith(f["prefix"]):
                owner[n.index] = f["lot"]

    texts = defaultdict(str)
    for p in (ROOT / "knowledge").glob("*/entries/**/*.json"):
        e = json.loads(p.read_text(encoding="utf-8"))
        texts[e["source"]["extracted_by"]] += " " + norm(e["name"]) + " | " + norm(e.get("text", "")) + " "
    for p in (ROOT / "knowledge").glob("*/system.json"):
        s = json.loads(p.read_text(encoding="utf-8"))
        texts[s["source"]["extracted_by"]] += " " + norm(json.dumps(s, ensure_ascii=False)) + " "
    all_text = " ".join(texts.values())

    lots = lots or sorted(texts)
    report, failed = {}, False
    for lot in lots:
        own = [n for n in nodes if owner[n.index] == lot]
        missing = []
        for n in own:
            # headings: a "[Tag]" suffix and a "Level N: " prefix (kept in the entry's facets) are not text
            t = norm(n.text if n.type != "h" else re.sub(r"^Level \d+: | \[[^\]]+\]$", "", n.text))
            if not t or (n.type == "h" and n.level <= 2):
                continue
            nxt = nodes[n.index + 1] if n.index + 1 < len(nodes) else None
            if n.type == "h" and nxt is not None and nxt.type == "h" and nxt.level > n.level:
                continue  # a grouping heading with no text of its own
            if t not in all_text:
                missing.append({"page": n.page, "type": n.type, "text": t[:120]})
        report[lot] = {"nodes": len(own), "uncovered": len(missing), "examples": missing[:40]}
        failed |= bool(missing)
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
