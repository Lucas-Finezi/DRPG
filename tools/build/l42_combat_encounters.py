#!/usr/bin/env python3
"""L42 — Combat Encounters (Gameplay Toolbox): encounter features, difficulty, XP budget per
character and troubleshooting. Only what the source states.

Usage: python3 -I tools/build/l42_combat_encounters.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import build, md, section, table_rows, write_entry  # noqa: E402

LOT = "L42"


def R(slug, name, nodes, path, items):
    return build("rule", slug, name, nodes, LOT, path, items)


def entries():
    E = []
    E.append(R("combat-encounters", "Combat Encounters", section("Combat Encounters", 2, page=202, stop_titles=("Combat Encounter Difficulty",)),
               "Gameplay Toolbox/Combat Encounters", [
                   (None, "md", md("encounter_features", "Which features make this encounter more interesting?",
                                   "The following features can make a combat encounter more interesting or challenging:", reason="narrative")),
                   ("**Changes in Elevation.**", "desc", None), ("**Defensive Positions.**", "desc", None),
                   ("**Mixed Monster Groups.**", "desc", None), ("**Reasons to Move.**", "desc", None)]))
    d = section("Combat Encounter Difficulty", 3, page=202)
    rows = [r for r in table_rows(d) if r and r[0].isdigit()]
    E.append(R("combat-encounter-difficulty", "Combat Encounter Difficulty", d, "Gameplay Toolbox/Combat Encounters/Combat Encounter Difficulty", [
        (None, "rule", {"id": "steps", "order": ["choose_difficulty", "determine_xp_budget", "spend_budget"]}),
        ("#### Step 1: Choose a Difficulty", "rule", {"id": "difficulties", "values": ["low", "moderate", "high"]}),
        ("**Low Difficulty.**", "rule", {"id": "low", "benchmark": "one monster with CR equal to the level of a party of four"}),
        ("**Moderate Difficulty.**", "desc", None),
        ("**High Difficulty.**", "desc", None),
        ("#### Step 2: Determine Your XP Budget", "fx", {"op": "reference", "rule": "dnd5e/rule/combat-encounter-difficulty",
                                                         "note": "XP budget = XP Budget per Character (party level, difficulty) × number of characters."}),
        ("#### Step 2: Determine Your XP Budget", "rule", {"id": "xp_budget", "formula": "table[party_level][difficulty] × characters"}),
        ("##### XP Budget per Character", "table", {"id": "xp_budget_per_character", "caption": "XP Budget per Character",
                                                    "columns": ["Party’s Level", "Low", "Moderate", "High"], "rows": rows}),
        ("#### Step 3: Spend Your Budget", "rule", {"id": "spend", "deduct_creature_xp": True, "not_over_budget": True, "leftover_ok": True}),
        ("**Example 1.**", "desc", None), ("**Example 2.**", "desc", None)]))
    E.append(R("encounter-troubleshooting", "Troubleshooting (Combat Encounters)", section("Troubleshooting", 3, page=203),
               "Gameplay Toolbox/Combat Encounters/Troubleshooting", [
                   (None, "desc", None),
                   ("#### Many Creatures", "rule", {"id": "many_creatures", "over_two_per_character": "include fragile creatures"}),
                   ("#### Adjustments", "md", md("adjust_encounter", "Adjust the encounter on the fly (flee or reinforcements)?",
                                                 "You can adjust an encounter on the fly, such as by having creatures flee (making the encounter easier) or adding reinforcements (making the encounter harder).")),
                   ("#### CR 0 Creatures", "rule", {"id": "cr0", "use_sparingly": True, "many": "use swarms"}),
                   ("#### Number of Stat Blocks", "rule", {"id": "stat_blocks", "recommended_max": 3}),
                   ("#### Powerful Creatures", "rule", {"id": "powerful", "cr_above_party_level": "can kill with one action"}),
                   ("#### Unusual Features", "md", md("unusual_features", "Leave out a monster whose features low-level characters can't overcome?",
                                                      "consider not adding that monster to an encounter for characters whose level is lower than the monster’s Challenge Rating"))]))
    return E


if __name__ == "__main__":
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
