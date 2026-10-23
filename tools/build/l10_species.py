#!/usr/bin/env python3
"""L10 — Species: the Character Origins/Character Species chapter and the nine species.

A species entry holds its creature type, size, Speed and lineage tables, and grants its
special traits. Each trait is a feature entry of its own (built by L14), so the species'
coverage points each trait paragraph to that feature.

Usage: python3 -I tools/build/l10_species.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import (build, ref_of, render, section, slugify, table_nodes,  # noqa: E402
                      write_entry)

LOT = "L10"
SYS = "dnd5e/system/dnd5e"

SPECIES = {
    "Dragonborn": {"sizes": ["medium"], "speed": 30, "height": {"medium": "about 5–7 feet tall"}},
    "Dwarf": {"sizes": ["medium"], "speed": 30, "height": {"medium": "about 4–5 feet tall"}},
    "Elf": {"sizes": ["medium"], "speed": 30, "height": {"medium": "about 5–6 feet tall"}},
    "Gnome": {"sizes": ["small"], "speed": 30, "height": {"small": "about 3–4 feet tall"}},
    "Goliath": {"sizes": ["medium"], "speed": 35, "height": {"medium": "about 7–8 feet tall"}},
    "Halfling": {"sizes": ["small"], "speed": 30, "height": {"small": "about 2–3 feet tall"}},
    "Human": {"sizes": ["medium", "small"], "speed": 30,
              "height": {"medium": "about 4–7 feet tall", "small": "about 2–4 feet tall"}},
    "Orc": {"sizes": ["medium"], "speed": 30, "height": {"medium": "about 6–7 feet tall"}},
    "Tiefling": {"sizes": ["medium", "small"], "speed": 30,
                 "height": {"medium": "about 4–7 feet tall", "small": "about 3–4 feet tall"}},
}
TABLES = {"Dragonborn": "Draconic Ancestors", "Elf": "Elven Lineages", "Tiefling": "Fiendish Legacies"}


def table_data(caption):
    """Rows of a species table; two-column-pair tables (Draconic Ancestors) are unfolded."""
    rows, columns = [], None
    for n in table_nodes(caption)[1:]:
        if n.type != "t":
            continue
        if n.text.startswith("| **"):
            columns = n.cells
            continue
        rows.append(n.cells)
    if columns and len(columns) == 4 and columns[0] == columns[2]:  # Dragon | Type | Dragon | Type
        columns = columns[:2]
        rows = [r[:2] for r in rows] + [r[2:] for r in rows if len(r) == 4]
    return {"id": slugify(caption).replace("-", "_"), "caption": caption, "columns": columns, "rows": rows}


def species_entry(name):
    info = SPECIES[name]
    skip = tuple(c for s, c in TABLES.items() if s != name)
    extra = table_nodes(TABLES[name]) if name == "Elf" else ()
    nodes = section(name, 4, skip_tables=skip, extra=extra)
    text = render(nodes)
    traits = re.findall(r"^\*\*\*(.+?)\.\*\*\*", text, flags=re.M)
    trait_refs = [f"dnd5e/feature/{slugify(name)}-{slugify(t)}" for t in traits]
    data = {"creature_type": "humanoid", "sizes": info["sizes"], "height": info["height"], "speed": info["speed"],
            "traits": trait_refs}
    if len(info["sizes"]) > 1:
        data["size_choice"] = "chosen when you select this species"
    items = [(None, "rule", {"id": "creature_type", "creature_type": "humanoid"}),
             ("**Size:**", "rule", {"id": "size", "sizes": info["sizes"]}),
             ("**Speed:**", "rule", {"id": "speed", "walk": info["speed"]}),
             ("As a" if f"As a {name}" in text or f"As an {name}" in text else "As a", "fx",
              {"op": "grant", "refs": trait_refs})]
    for t, r in zip(traits, trait_refs):
        items.append((f"***{t}.***", "ref", [r]))
    if name in TABLES:
        items.append((f"##### {TABLES[name]}", "table", table_data(TABLES[name])))
    items.sort(key=lambda it: 0 if it[0] is None else text.find(it[0]))  # anchors in text order
    return build("species", slugify(name), name, nodes, LOT,
                 f"Character Origins/Character Species/Species Descriptions/{name}", items,
                 facets={"creature_type": "humanoid", "size": info["sizes"], "speed": info["speed"]},
                 data=data)


def chapter_entries():
    E = []
    intro = section("Character Origins", 1, stop_titles=("Character Backgrounds",))
    if intro:
        E.append(build("rule", "character-origins", "Character Origins", intro, LOT, "Character Origins",
                       [(None, "desc", None)]))
    nodes = section("Character Species", 2, stop_titles=("Parts of a Species",))
    E.append(build("rule", "character-species", "Character Species", nodes, LOT, "Character Origins/Character Species", [
        (None, "desc", None),
        ("Members of most species live for about 80 years", "rule", {
            "id": "life_span", "typical_years": 80, "exceptions_in_species_text": True,
            "maturity_age": "about_the_same_for_all", "character_age": "within_species_life_span"})]))
    nodes = section("Parts of a Species", 3)
    E.append(build("rule", "parts-of-a-species", "Parts of a Species", nodes, LOT,
                   "Character Origins/Character Species/Parts of a Species", [
        (None, "desc", None),
        ("#### Creature Type", "ref", [ref_of("Creature Type", "rule")]),
        ("#### Creature Type", "rule", {"id": "species_creature_type", "all_srd_species": "humanoid"}),
        ("#### Size", "rule", {"id": "species_size", "some_species_choose": ["small", "medium"]}),
        ("#### Speed", "rule", {"id": "species_speed", "set_by_species": True}),
        ("#### Special Traits", "rule", {"id": "special_traits", "all_listed_traits": True,
                                         "some_offer_choices": True})]))
    nodes = section("Species Descriptions", 3, stop_titles=("Dragonborn",))
    if nodes:
        E.append(build("rule", "species-descriptions", "Species Descriptions", nodes, LOT,
                       "Character Origins/Character Species/Species Descriptions", [(None, "desc", None)]))
    return E


if __name__ == "__main__":
    out = chapter_entries() + [species_entry(n) for n in SPECIES]
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
