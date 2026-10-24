#!/usr/bin/env python3
"""L43 — Reference graph: every ref between catalog entries (and to the system file,
dnd5e/system/dnd5e), written to knowledge/dnd5e/graph/refs.json.

Fails if a ref does not resolve to an entry. Reports, per entry, outbound and inbound refs,
and lists entries nothing points to (roots/orphans are expected for e.g. top-level sections).

Usage: python3 -I tools/build/l43_ref_graph.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRIES = ROOT / "knowledge" / "dnd5e" / "entries"
OUT = ROOT / "knowledge" / "dnd5e" / "graph" / "refs.json"


def main():
    entries = {}
    for p in sorted(ENTRIES.rglob("*.json")):
        e = json.loads(p.read_text(encoding="utf-8"))
        entries[e["ref"]] = e
    system = json.loads((ROOT / "knowledge" / "dnd5e" / "system.json").read_text(encoding="utf-8"))
    entries[system["ref"]] = {"ref": system["ref"], "kind": "system", "refs": []}
    out_edges, in_edges, missing = {}, defaultdict(list), []
    for ref, e in entries.items():
        targets = sorted(set(e.get("refs", [])) - {ref})
        out_edges[ref] = targets
        for t in targets:
            if t not in entries:
                missing.append({"from": ref, "to": t})
            else:
                in_edges[t].append(ref)
    by_kind = defaultdict(int)
    for e in entries.values():
        by_kind[e["kind"]] += 1
    graph = {
        "system": "dnd5e", "document": "srd-5.2.1",
        "summary": {"entries": len(entries), "edges": sum(len(v) for v in out_edges.values()),
                    "unresolved": len(missing), "unreferenced": sum(1 for r in entries if not in_edges.get(r)),
                    "by_kind": dict(sorted(by_kind.items()))},
        "unresolved": missing,
        "nodes": [{"ref": r, "kind": entries[r]["kind"], "out": out_edges[r], "in": sorted(in_edges.get(r, []))} for r in sorted(entries)],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(graph, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(graph["summary"]))
    if missing:
        for m in missing[:20]:
            print("UNRESOLVED", m["from"], "->", m["to"])
        sys.exit(1)


if __name__ == "__main__":
    main()
