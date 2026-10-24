#!/usr/bin/env python3
"""Reference check: every ref used by an entry must resolve.

A ref resolves when it is
  - an existing entry (knowledge/<system>/entries/<kind>/<slug>.json) or the system itself;
  - an expected entry of the L00 inventory owned by a lot not built yet ("pending");
  - a rule entry for an outline section of a lot not built yet ("pending section").
Anything else is an error (typo or invented ref).

It also checks completeness: every expected inventory entry of a lot that has been built
(at least one entry extracted by it) must exist.

Usage: python3 -I tools/validate/refs.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "inventory"))
from srdmd import slugify  # noqa: E402

INV = ROOT / "inventory" / "dnd5e" / "srd-5.2.1"


def main():
    existing, used = {}, Counter()
    for p in (ROOT / "knowledge").glob("*/entries/**/*.json"):
        e = json.loads(p.read_text(encoding="utf-8"))
        existing[e["ref"]] = e["source"]["extracted_by"]
        for r in e.get("refs", []):
            used[(r, e["ref"])] += 1
    for p in (ROOT / "knowledge").glob("*/system.json"):
        existing[json.loads(p.read_text(encoding="utf-8"))["ref"]] = "L02"
    built = set(existing.values())
    expected = {e["ref"]: e["lot"] for e in json.loads((INV / "entries.json").read_text(encoding="utf-8"))["entries"]}
    sections = {}
    for o in json.loads((INV / "outline.json").read_text(encoding="utf-8"))["sections"]:
        sections.setdefault(f"dnd5e/rule/{slugify(o['title'])}", o["lot"])

    ok, pending, errors = 0, Counter(), []
    for (ref, src), _ in used.items():
        if ref in existing:
            ok += 1
        elif ref in expected and expected[ref] not in built:
            pending[expected[ref]] += 1
        elif ref in sections and sections[ref] not in built:
            pending[sections[ref] + " (section)"] += 1
        else:
            errors.append(f"{src} -> {ref}")
    missing = sorted(ref for ref, lot in expected.items() if lot in built and ref not in existing)
    for e in sorted(errors):
        print("UNRESOLVED", e)
    for ref in missing:
        print("MISSING", ref, f"(expected from {expected[ref]})")
    print(json.dumps({"resolved": ok, "pending_future_lots": dict(sorted(pending.items())), "unresolved": len(errors),
                      "missing_expected_entries": len(missing)}))
    return 1 if errors or missing else 0


if __name__ == "__main__":
    sys.exit(main())
