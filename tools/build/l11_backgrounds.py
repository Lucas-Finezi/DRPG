#!/usr/bin/env python3
"""L11 — Backgrounds: Character Backgrounds (parts and the four backgrounds) and the
Gameplay Toolbox guidance for creating a background.

Usage: python3 -I tools/build/l11_backgrounds.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import build, md, ref_of, section, write_entry  # noqa: E402

LOT = "L11"
F = lambda slug: f"dnd5e/feat/{slug}"  # noqa: E731
G = lambda slug: f"dnd5e/gear/{slug}"  # noqa: E731
T = lambda slug: f"dnd5e/tool/{slug}"  # noqa: E731
W = lambda slug: f"dnd5e/weapon/{slug}"  # noqa: E731

BACKGROUNDS = {
    "Acolyte": {
        "abilities": ["int", "wis", "cha"], "feat": F("magic-initiate"), "feat_param": {"spell_list": "cleric"},
        "skills": ["insight", "religion"], "tool": T("calligraphers-supplies"),
        "equipment_a": [(T("calligraphers-supplies"), 1, None), (G("book"), 1, "prayers"), (G("holy-symbol"), 1, None),
                        (G("parchment"), 10, "sheets"), (G("robe"), 1, None)], "gp_a": 8},
    "Criminal": {
        "abilities": ["dex", "con", "int"], "feat": F("alert"),
        "skills": ["sleight_of_hand", "stealth"], "tool": T("thieves-tools"),
        "equipment_a": [(W("dagger"), 2, None), (T("thieves-tools"), 1, None), (G("crowbar"), 1, None),
                        (G("pouch"), 2, None), (G("clothes-travelers"), 1, None)], "gp_a": 16},
    "Sage": {
        "abilities": ["con", "int", "wis"], "feat": F("magic-initiate"), "feat_param": {"spell_list": "wizard"},
        "skills": ["arcana", "history"], "tool": T("calligraphers-supplies"),
        "equipment_a": [(W("quarterstaff"), 1, None), (T("calligraphers-supplies"), 1, None), (G("book"), 1, "history"),
                        (G("parchment"), 8, "sheets"), (G("robe"), 1, None)], "gp_a": 8},
    "Soldier": {
        "abilities": ["str", "dex", "con"], "feat": F("savage-attacker"),
        "skills": ["athletics", "intimidation"], "tool": {"choose_from_category": T("gaming-set")},
        "equipment_a": [(W("spear"), 1, None), (W("shortbow"), 1, None), (G("ammunition-arrows"), 20, "arrows"),
                        (T("gaming-set"), 1, "same as the tool proficiency"), (G("healers-kit"), 1, None),
                        (G("quiver"), 1, None), (G("clothes-travelers"), 1, None)], "gp_a": 14},
}


def background(name):
    b = BACKGROUNDS[name]
    package = [{"ref": r, "quantity": q, **({"note": n} if n else {})} for r, q, n in b["equipment_a"]]
    feat = {"op": "grant", "refs": [b["feat"]]}
    if "feat_param" in b:
        feat["note"] = f"Spell list: {b['feat_param']['spell_list'].title()}."
    tool = b["tool"]
    tool_fx = ({"op": "proficiency", "category": "tool", "items": [tool]} if isinstance(tool, str) else
               {"op": "proficiency", "category": "tool", "choose": 1, "from": [tool["choose_from_category"]],
                "note": "One kind of Gaming Set."})
    equip = {"op": "choice", "choose": 1, "options": [
        {"id": "a", "label": "Package (A)", "effects": [{"op": "reference", "rule": "dnd5e/rule/character-backgrounds",
                                                          "note": "Gain the package in data.equipment.a."}]},
        {"id": "b", "label": "50 GP", "effects": [{"op": "reference", "rule": "dnd5e/rule/coins",
                                                   "note": "Gain 50 GP."}]}]}
    data = {"ability_scores": b["abilities"], "feat": b["feat"], "skills": b["skills"], "tool": tool,
            "equipment": {"a": {"items": package, "gp": b["gp_a"]}, "b": {"gp": 50}}}
    if "feat_param" in b:
        data["feat_options"] = b["feat_param"]
    items = [
        (None, "rule", {"id": "ability_scores", "abilities": b["abilities"],
                        "increase": "plus_2_and_plus_1_or_plus_1_to_all_three", "max_score": 20}),
        ("**Feat:**", "fx", feat),
        ("**Skill Proficiencies:**", "fx", {"op": "proficiency", "category": "skill", "items": b["skills"]}),
        ("**Tool Proficiency:**", "fx", tool_fx),
        ("**Equipment:**", "fx", equip),
    ]
    return build("background", name.lower(), name, section(name, 4, page=83), LOT,
                 f"Character Origins/Character Backgrounds/Background Descriptions/{name}", items,
                 facets={"ability_scores": b["abilities"], "skills": b["skills"],
                         "feat": b["feat"].rsplit("/", 1)[1]}, data=data)


def entries():
    E = []
    nodes = section("Character Backgrounds", 2, stop_titles=("Parts of a Background",))
    E.append(build("rule", "character-backgrounds", "Character Backgrounds", nodes, LOT,
                   "Character Origins/Character Backgrounds", [(None, "desc", None)],
                   data={"backgrounds": [f"dnd5e/background/{n.lower()}" for n in BACKGROUNDS]}))
    nodes = section("Parts of a Background", 3)
    E.append(build("rule", "parts-of-a-background", "Parts of a Background", nodes, LOT,
                   "Character Origins/Character Backgrounds/Parts of a Background", [
        (None, "desc", None),
        ("#### Ability Scores", "rule", {"id": "ability_scores", "listed": 3, "options": [
            {"plus_2": 1, "plus_1": 1, "distinct": True}, {"plus_1": 3}], "max_score": 20}),
        ("#### Feat", "rule", {"id": "feat", "category": "origin", "count": 1}),
        ("#### Skill Proficiencies", "rule", {"id": "skills", "count": 2}),
        ("#### Tool Proficiency", "rule", {"id": "tool", "count": 1, "specific_or_artisans_tools": True}),
        ("#### Tool Proficiency", "ref", ["dnd5e/rule/tools"]),
        ("#### Equipment", "rule", {"id": "equipment", "choice": ["package", "50_gp"]})]))
    E += [background(n) for n in BACKGROUNDS]

    path = "Gameplay Toolbox/Creating a Background"
    nodes = section("Creating a Background", 2, skip_tables=("Travel Terrain",))
    E.append(build("rule", "creating-a-background", "Creating a Background", nodes, LOT, path, [
        (None, "md", md("custom_background", "Create or customize a background for this campaign?",
                        "Creating a unique background or customizing an existing one can reflect the particular theme "
                        "of your campaign or elements of your world.", when="campaign_setup", pages=[192])),
        ("This section describes, step by step", "desc", None),
        ("### 1: Choose Abilities", "rule", {"id": "choose_abilities", "count": 3}),
        ("**Strength or Dexterity.**", "desc", None),
        ("### 2: Choose a Feat", "rule", {"id": "choose_feat", "category": "origin", "count": 1}),
        ("### 2: Choose a Feat", "ref", ["dnd5e/rule/origin-feats"]),
        ("### 3: Choose Skill Proficiencies", "rule", {"id": "choose_skills", "count": 2,
                                                       "related_to_abilities": False}),
        ("### 4: Choose a Tool Proficiency", "rule", {"id": "choose_tool", "count": 1}),
        ("### 5: Choose Equipment", "rule", {"id": "choose_equipment", "value_gp": 50, "includes_unspent_gold": True,
                                             "excluded": ["martial_weapons", "armor"]})]))
    return E


if __name__ == "__main__":
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
