#!/usr/bin/env python3
"""L44 — Global manifest: one row per catalog entry (ref, kind, name, facets, tier, file, lot,
pages, coverage status counts, master decision count), written to knowledge/dnd5e/manifest.json.

Usage: python3 -I tools/build/l44_manifest.py
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KNOW = ROOT / "knowledge" / "dnd5e"


def main():
    rows, by_kind, by_tier, by_lot, status = [], Counter(), Counter(), Counter(), Counter()
    names = defaultdict(list)
    for p in sorted((KNOW / "entries").rglob("*.json")):
        e = json.loads(p.read_text(encoding="utf-8"))
        cov = Counter(s["status"] for s in e["coverage"])
        status.update(cov)
        rows.append({"ref": e["ref"], "kind": e["kind"], "name": e["name"], "facets": e.get("facets", {}), "tier": e["tier"],
                     "file": str(p.relative_to(ROOT)), "lot": e["source"]["extracted_by"], "pages": e["source"]["pages"],
                     "coverage": dict(cov), "master_decisions": len(e.get("master_decisions", [])),
                     "effects": len(e.get("effects", []))})
        by_kind[e["kind"]] += 1
        by_tier[e["tier"]] += 1
        by_lot[e["source"]["extracted_by"]] += 1
        names[(e["kind"], e["name"])].append(e["ref"])
    system = json.loads((KNOW / "system.json").read_text(encoding="utf-8"))
    manifest = {
        "system": "dnd5e", "document": "srd-5.2.1", "schema_version": "1.0",
        "license": {"id": "CC-BY-4.0", "attribution": system["source"]["license"]["attribution"] if "license" in system["source"] else None},
        "system_file": "knowledge/dnd5e/system.json",
        "summary": {"entries": len(rows), "by_kind": dict(sorted(by_kind.items())), "by_tier": {str(k): v for k, v in sorted(by_tier.items())},
                    "by_lot": dict(sorted(by_lot.items(), key=lambda kv: int(kv[0][1:]))), "coverage_segments": dict(status),
                    "master_decisions": sum(r["master_decisions"] for r in rows), "effects": sum(r["effects"] for r in rows)},
        "duplicate_names": [{"kind": k, "name": n, "refs": refs} for (k, n), refs in sorted(names.items()) if len(refs) > 1],
        "entries": rows,
    }
    (KNOW / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(manifest["summary"]))


if __name__ == "__main__":
    main()
