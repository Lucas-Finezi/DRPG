#!/usr/bin/env python3
"""L33 — Monster stat block rules (Stat Block Overview, Parts of a Stat Block, Running a Monster)
and the creatures A–C (Monsters A–Z and Animals).

Usage: python3 -I tools/build/l33_monsters_a_c.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import NODES, build, find, md, section, sidebar, table_rows  # noqa: E402
from monsterlib import build_lot, write_lot  # noqa: E402

LOT = "L33"
P = "Monsters/Parts of a Stat Block"
# The PDF prints the last three paragraphs of the "Running a Monster" sidebar after the
# Initiative section (p. 254, no sidebar marker): they are given back to the sidebar.
RUNNING = ("**Special Abilities.**", "**Multiattack.**", "**Bonus Actions, Reactions, Legendary Actions.**")


def R(slug, name, nodes, path, items):
    return build("rule", slug, name, nodes, LOT, path, items)


def part(title, page, items, slug=None, nodes=None):
    return R(slug or f"stat-block-{title.lower().replace(' ', '-')}", f"{title} (Stat Block)", nodes or section(title, 3, page=page),
             f"{P}/{title}", items)


def sections():
    E = []
    ov = section("Stat Block Overview", 2, page=254)
    E.append(R("stat-block-overview", "Stat Block Overview", ov, "Monsters/Stat Block Overview", [
        (None, "rule", {"id": "parts", "order": ["name_and_general_details", "combat_highlights", "ability_scores", "other_details",
                                                 "traits", "actions", "bonus_actions", "reactions", "legendary_actions"]}),
        ("**Name and General Details.**", "sys", ["/data/rules/0"]),
        ("**Combat Highlights.**", "sys", ["/data/rules/0"]),
        ("**Ability Scores.**", "sys", ["/data/rules/0"]),
        ("**Other Details.**", "rule", {"id": "optional_entries", "absent_when_lacking": True}),
        ("**Traits.**", "sys", ["/data/rules/0"]),
        ("**Actions.**", "ref", ["dnd5e/rule/actions"]),
        ("**Bonus Actions.**", "sys", ["/data/rules/0"]),
        ("**Reactions and Legendary Actions.**", "sys", ["/data/rules/0"])]))
    E.append(R("parts-of-a-stat-block", "Parts of a Stat Block", section("Parts of a Stat Block", 2, page=254, stop_titles=("Size",)),
               P, [(None, "desc", None)]))
    E.append(part("Size", 254, [(None, "rule", {"id": "size", "options_choose": True}), (None, "ref", ["dnd5e/rule/size"])]))
    E.append(part("Creature Type", 254, [
        (None, "rule", {"id": "type_tag", "interacts_with_effects": True}),
        ("The game includes the following creature types", "rule", {"id": "types", "values": ["aberration", "beast", "celestial", "construct", "dragon",
                                                                                            "elemental", "fey", "fiend", "giant", "humanoid", "monstrosity",
                                                                                            "ooze", "plant", "undead"], "no_rules_of_their_own": True})]
        + [(f"**{t}**", "desc", None) for t in ("Aberrations", "Beasts", "Celestials", "Constructs", "Dragons", "Elementals", "Fey", "Fiends",
                                                "Giants", "Humanoids", "Monstrosities", "Oozes", "Plants", "Undead")]))
    E.append(part("Alignment", 254, [
        (None, "md", md("monster_alignment", "Change this monster's alignment for the story?",
                        "Change a monster’s alignment to suit your storytelling needs.", reason="narrative")),
        ("“Character Creation” describes", "ref", ["dnd5e/rule/alignment"])]))
    E.append(part("Armor Class", 254, [(None, "rule", {"id": "ac", "includes": ["natural_armor", "dexterity", "gear", "other_defenses"]})]))
    ini = [n for n in section("Initiative", 3, page=254) if not n.text.startswith(RUNNING)]
    E.append(part("Initiative", 254, [
        (None, "rule", {"id": "initiative", "modifier": "rolled", "score": "static alternative"}),
        ("If you don’t want to roll", "ref", ["dnd5e/rule/initiative"])], nodes=ini))
    hp = section("Hit Points", 3, page=255)
    E.append(part("Hit Points", 255, [
        (None, "rule", {"id": "hp", "use_average_or_roll": True, "not_both": True}),
        ("A monster’s size typically", "rule", {"id": "hit_die_by_size", "table": "hit_dice_by_size"}),
        ("##### Hit Dice by Size", "table", {"id": "hit_dice_by_size", "caption": "Hit Dice by Size", "columns": ["Monster Size", "Hit Die", "Average HP per Die"],
                                             "rows": table_rows(hp)}),
        ("A monster’s Constitution modifier", "fx", {"op": "modifier", "stat": "hp_max", "mode": "add",
                                                     "value": {"op": "mul", "args": [{"var": "ability_mod.con"}, {"var": "hit_point_dice_count"}]},
                                                     "note": "Constitution modifier × number of Hit Dice."}),
        ("For more on Hit Points", "ref", ["dnd5e/rule/hit-points"])]))
    E.append(part("Speed", 255, [(None, "ref", ["dnd5e/rule/speed"])]))
    E.append(part("Ability Scores", 255, [(None, "rule", {"id": "abilities", "scores_modifiers_saves": True})]))
    E.append(part("Skills", 255, [(None, "rule", {"id": "skills", "bonus": "ability modifier + Proficiency Bonus"})]))
    E.append(part("Resistances and Vulnerabilities", 255, [(None, "ref", ["dnd5e/rule/resistance", "dnd5e/rule/vulnerability"])]))
    E.append(part("Immunities", 255, [(None, "rule", {"id": "order", "damage_then_conditions": True}), (None, "ref", ["dnd5e/rule/immunity"])]))
    E.append(part("Gear", 255, [
        (None, "rule", {"id": "gear", "proficient": True, "retrievable_listed": True, "others_use_equipment_rules": True}),
        ("The Gear entry doesn’t", "rule", {"id": "not_exhaustive", "clothes_assumed": True}),
        ("Equipment mentioned outside", "rule", {"id": "unlisted", "unusable_when_defeated": True})]))
    E.append(part("Senses", 256, [(None, "ref", ["dnd5e/rule/passive-perception"])]))
    E.append(part("Languages", 256, [(None, "rule", {"id": "languages", "none_means_no_comprehension": True})]))
    E.append(part("Challenge Rating", 256, [(None, "ref", ["dnd5e/rule/challenge-rating", "dnd5e/rule/combat-encounters"])]))
    E.append(part("Traits", 256, [(None, "rule", {"id": "traits", "active": "always or in certain situations"})]))
    E.append(part("Actions", 256, [(None, "ref", ["dnd5e/rule/actions"])]))
    E.append(part("Bonus Action", 257, [(None, "ref", ["dnd5e/rule/bonus-action"])]))
    E.append(part("Reactions", 257, [(None, "ref", ["dnd5e/rule/reaction"])]))
    E.append(part("Legendary Actions", 257, [
        (None, "rule", {"id": "legendary_action", "after_another_creatures_turn": True, "one_at_a_time": True, "not_if_incapacitated": True}),
        ("The monster has a limited number", "rule", {"id": "uses", "resource": "legendary_actions", "regain": "start of its turn"})]))
    E.append(part("Limited Usage", 257, [
        (None, "desc", None),
        ("**X/Day.**", "rule", {"id": "per_day", "regain": "long_rest"}),
        ("**Recharge X–Y.**", "rule", {"id": "recharge", "roll": "1d6", "when": "start of each of its turns", "also_on": "short_or_long_rest"}),
        ("**Recharge after a Short or Long Rest.**", "rule", {"id": "recharge_rest", "once": True, "regain": "short_or_long_rest"})]))
    run = sidebar("Running a Monster") + [n for n in section("Initiative", 3, page=254) if n.text.startswith(RUNNING)]
    E.append(build("rule", "running-a-monster", "Running a Monster", run, LOT, "Monsters/Running a Monster (sidebar)", [
        (None, "desc", None),
        ("**Special Abilities.**", "rule", {"id": "special_abilities", "use_early_and_often": True}),
        ("**Multiattack.**", "rule", {"id": "multiattack", "use_when_not_using_stronger": True}),
        ("**Bonus Actions, Reactions, Legendary Actions.**", "rule", {"id": "use_often", "bonus_actions": True, "reactions": True,
                                                                       "legendary_actions": True})]))
    return E


REG = {"variables": [{"id": "hit_point_dice_count", "description": "Number of Hit Dice in a monster's Hit Point expression.", "type": "number", "pages": [255]}]}

if __name__ == "__main__":
    from entrylib import extend_registries
    extend_registries(REG, LOT)
    write_lot(LOT, sections() + build_lot(LOT))
