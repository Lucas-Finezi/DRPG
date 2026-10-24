#!/usr/bin/env python3
"""L27 — Spell lists: the eight class spell lists and the eight subclass spell lists.

A class list keeps the printed tables (spell, school, Special) as data and gives the
effective list under decision D-001: the classes named in each spell's description header
decide access, so a spell whose header names the class is on the effective list even when
the printed list omits it. Every divergence between a printed list and the spell
descriptions (class, school, Concentration/Ritual/Material flags) is recorded in the
entry's `inconsistencies`, never corrected in the printed data.

A subclass list is the "always prepared" table of a subclass feature (built in L14); the
spell-list entry repeats that table as a list by class level.

Usage: python3 -I tools/build/l27_spell_lists.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import build, section, slugify, table_nodes, write_entry  # noqa: E402

LOT = "L27"
ROOT = Path(__file__).resolve().parents[2]
SPELLS = {}
for p in (ROOT / "knowledge/dnd5e/entries/spell").glob("*.json"):
    e = json.loads(p.read_text(encoding="utf-8"))
    SPELLS[e["name"]] = e
CLASSES = ["Bard", "Cleric", "Druid", "Paladin", "Ranger", "Sorcerer", "Warlock", "Wizard"]
SUBCLASS_LISTS = [  # (spell-list slug, table caption, class, column label, feature ref)
    ("life-domain-spells", "Life Domain Spells", "cleric", "Cleric Level", "dnd5e/feature/life-domain-life-domain-spells"),
    ("circle-of-the-land-spells-arid-land", "Arid Land", "druid", "Druid Level", "dnd5e/feature/circle-of-the-land-circle-of-the-land-spells"),
    ("circle-of-the-land-spells-polar-land", "Polar Land", "druid", "Druid Level", "dnd5e/feature/circle-of-the-land-circle-of-the-land-spells"),
    ("circle-of-the-land-spells-temperate-land", "Temperate Land", "druid", "Druid Level", "dnd5e/feature/circle-of-the-land-circle-of-the-land-spells"),
    ("circle-of-the-land-spells-tropical-land", "Tropical Land", "druid", "Druid Level", "dnd5e/feature/circle-of-the-land-circle-of-the-land-spells"),
    ("oath-of-devotion-spells", "Oath of Devotion Spells", "paladin", "Paladin Level", "dnd5e/feature/oath-of-devotion-oath-of-devotion-spells"),
    ("draconic-spells", "Draconic Spells", "sorcerer", "Sorcerer Level", "dnd5e/feature/draconic-sorcery-draconic-spells"),
    ("fiend-spells", "Fiend Spells", "warlock", "Warlock Level", "dnd5e/feature/fiend-patron-fiend-spells"),
]
SPECIAL = {"C": "concentration", "R": "ritual", "M": "specific_material_component"}


def plain(s):
    return re.sub(r"\s+", " ", s.replace("*", "")).strip()


def class_list(cls):
    nodes = section(f"{cls} Spell List", 3)
    slug = slugify(cls)
    items = [(None, "rule", {"id": "columns", "special": SPECIAL, "order": "level_then_alphabetical"})]
    printed, inconsistencies = [], []
    level = None
    for n in nodes:
        if n.type == "h":
            level = 0 if n.text.startswith("Cantrips") else int(re.search(r"Level (\d)", n.text).group(1))
            rows = [m.cells for m in table_nodes(n.text)[1:] if m.type == "t" and not m.text.startswith("| **")]
            table = {"id": f"level_{level}", "caption": n.text, "columns": ["Spell", "School", "Special"],
                     "rows": [[plain(r[0]), r[1], r[2]] for r in rows]}
            items.append((f"##### {n.text}", "table", table))
            for r in rows:
                name = plain(r[0])
                spell = SPELLS[name]
                printed.append(spell["ref"])
                f = spell["facets"]
                flags = {x.strip() for x in r[2].split(",") if x.strip() not in ("—", "")}
                if f["level"] != level:
                    inconsistencies.append({"detail": f"{name}: listed under level {level} but its description says level {f['level']}",
                                            "pages": sorted({n.page, spell['source']['pages'][0]})})
                if r[1].lower() != f["school"]:
                    inconsistencies.append({"detail": f"{name}: school '{r[1]}' in the {cls} spell list but '{f['school'].title()}' in its description (D-001: the description is authoritative)",
                                            "pages": sorted({n.page, spell['source']['pages'][0]})})
                if ("C" in flags) != f["concentration"]:
                    inconsistencies.append({"detail": f"{name}: Special column {'has' if 'C' in flags else 'lacks'} C but the description's duration {'does not require' if 'C' in flags else 'requires'} Concentration",
                                            "pages": sorted({n.page, spell['source']['pages'][0]})})
                if ("R" in flags) != f["ritual"]:
                    inconsistencies.append({"detail": f"{name}: Special column {'has' if 'R' in flags else 'lacks'} R but the description's casting time {'has no' if 'R' in flags else 'has a'} Ritual option",
                                            "pages": sorted({n.page, spell['source']['pages'][0]})})
                comp = spell["data"]["components"]
                if ("M" in flags) != bool("material_cost_gp" in comp or comp.get("material_consumed")):
                    inconsistencies.append({"detail": f"{name}: Special column {'has' if 'M' in flags else 'lacks'} M but the description's material component {'has no' if 'M' in flags else 'has a'} cost or consumption",
                                            "pages": sorted({n.page, spell['source']['pages'][0]})})
                if slug not in f["classes"]:
                    inconsistencies.append({"detail": f"{name}: on the printed {cls} spell list but its description header doesn't name {cls}",
                                            "pages": sorted({n.page, spell['source']['pages'][0]})})
    header = sorted(e["ref"] for e in SPELLS.values() if slug in e["facets"]["classes"])
    added = sorted(set(header) - set(printed))
    for ref in added:
        e = next(s for s in SPELLS.values() if s["ref"] == ref)
        inconsistencies.append({"detail": f"{e['name']}: its description header names {cls} but the printed {cls} spell list omits it (D-001: enabled for {cls})",
                                "pages": [e["source"]["pages"][0]]})
    effective = sorted(set(printed) | set(header))
    data = {"class": f"dnd5e/class/{slug}", "printed_spells": printed, "spells": effective, "added_by_decision_d001": added,
            "decision": "D-001"}
    e = build("spell-list", slug, f"{cls} Spell List", nodes, LOT, f"Classes/{cls}/{cls} Spell List",
              [(None, "sys", ["/data/class", "/data/spells", "/data/printed_spells", "/data/added_by_decision_d001"])] + items,
              facets={"class": f"dnd5e/class/{slug}", "spell_count": len(effective)}, data=data)
    if inconsistencies:
        e["inconsistencies"] = inconsistencies
    return e


def subclass_list(slug, caption, cls, col, feature):
    nodes = table_nodes(caption)
    rows = []
    for n in nodes[1:]:
        if n.type != "t" or n.text.startswith("| **"):
            continue
        names = [plain(x) for x in n.cells[1].split(",")]
        rows.append({"class_level": int(n.cells[0]), "spells": [SPELLS[x]["ref"] for x in names]})
    title = caption if caption.endswith("Spells") else f"Circle of the Land Spells: {caption}"
    data = {"class": f"dnd5e/class/{cls}", "granted_by": feature, "always_prepared": True, "by_level": rows,
            "spells": [s for r in rows for s in r["spells"]]}
    return build("spell-list", slug, title, nodes, LOT, f"Classes/{cls.title()}/{title}",
                 [(None, "sys", ["/data/by_level", "/data/spells"]), (None, "ref", [feature])],
                 facets={"class": f"dnd5e/class/{cls}", "subclass_list": True, "spell_count": len(data["spells"])}, data=data)


if __name__ == "__main__":
    out = [class_list(c) for c in CLASSES] + [subclass_list(*s) for s in SUBCLASS_LISTS]
    for e in out:
        write_entry(e)
        for i in e.get("inconsistencies", []):
            print(e["name"], "|", i["detail"])
    print(f"wrote {len(out)} entries")
