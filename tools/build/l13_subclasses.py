#!/usr/bin/env python3
"""L13 — Subclasses: the twelve subclasses, level by level, linked to their base class.

A subclass entry keeps its introduction (and any non-feature text such as the Oath of
Devotion tenets) and lists its features by level; the base class's Features table marks
the levels that grant a "Subclass feature". Feature descriptions are L14 entries.

Usage: python3 -I tools/build/l13_subclasses.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classlib import INV, subclass_features  # noqa: E402
from entrylib import NODES, build, find, render, slugify, write_entry  # noqa: E402

LOT = "L13"


def subclass_nodes(heading):
    i = find(heading, 3)
    out, excluded = [NODES[i]], False
    for n in NODES[i + 1:]:
        if n.type == "h" and n.level <= 3 and not n.sidebar:
            break
        if n.sidebar:
            continue
        if n.type == "h" and n.level == 4:
            excluded = bool(re.match(r"^Level \d+: ", n.text))
        if not excluded:
            out.append(n)
    return out


def entries():
    E = []
    for e in [x for x in INV if x["kind"] == "subclass"]:
        cls_ref = e["facets"]["class"]
        cls = cls_ref.rsplit("/", 1)[1].title()
        heading = f"{cls} Subclass: {e['name']}"
        nodes = subclass_nodes(heading)
        text = render(nodes)
        feats = subclass_features(e["ref"])
        by_level = {}
        for lv, name, ref in sorted(feats):
            by_level.setdefault(str(lv), []).append(ref)
        cls_id = cls.lower()
        items = [(None, "fx", [{"op": "grant", "refs": by_level[lv],
                                "when": {"pred": "level_at_least", "args": {"class": cls_id, "level": int(lv)}},
                                "note": f"Subclass feature at {cls} level {lv}."}
                               for lv in sorted(by_level, key=int)])]
        tagline = re.search(r"^\*([^*]+)\*$", text, flags=re.M)
        first_para = re.search(r"^(?!#|\*)(.{20,40})", text, flags=re.M)
        items.append((first_para.group(1), "desc", None))
        if "These paladins share the following tenets" in text:
            items.append(("These paladins share the following tenets", "desc", None))
        data = {"class": cls_ref, "levels": by_level, "tagline": tagline.group(1) if tagline else None}
        E.append(build("subclass", e["ref"].rsplit("/", 1)[1], e["name"], nodes, LOT,
                       f"Classes/{cls}/{heading}", items, text=text,
                       facets={"class": cls.lower(), "feature_levels": sorted(int(k) for k in by_level)},
                       data={k: v for k, v in data.items() if v is not None}))
    return E


if __name__ == "__main__":
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
