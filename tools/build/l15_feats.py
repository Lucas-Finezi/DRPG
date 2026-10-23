#!/usr/bin/env python3
"""L15 — Feats: the Feats chapter, Parts of a Feat, the four categories and the 17 feats.

Usage: python3 -I tools/build/l15_feats.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import build, extend_registries, section, sidebar, slugify, write_entry  # noqa: E402

LOT = "L15"
C = lambda s: f"dnd5e/condition/{s}"  # noqa: E731
SP = lambda s: f"dnd5e/spell/{s}"  # noqa: E731
CATS = {"Origin": ["Alert", "Magic Initiate", "Savage Attacker", "Skilled"],
        "General": ["Ability Score Improvement", "Grappler"],
        "Fighting Style": ["Archery", "Defense", "Great Weapon Fighting", "Two-Weapon Fighting"],
        "Epic Boon": ["Boon of Combat Prowess", "Boon of Dimensional Travel", "Boon of Fate",
                      "Boon of Irresistible Offense", "Boon of Spell Recall", "Boon of the Night Spirit",
                      "Boon of Truesight"]}
PREREQ = {"Ability Score Improvement": {"character_level": 4},
          "Grappler": {"character_level": 4, "ability_any_of": {"str": 13, "dex": 13}},
          **{n: {"feature": "fighting_style"} for n in CATS["Fighting Style"]},
          **{n: {"character_level": 19} for n in CATS["Epic Boon"]}}
PREREQ["Boon of Spell Recall"] = {"character_level": 19, "feature": "spellcasting"}
INV_PREREQ = {e["ref"]: e["facets"].get("prerequisite") for e in __import__("json").loads(
    (Path(__file__).resolve().parents[2] / "inventory/dnd5e/srd-5.2.1/entries.json").read_text(encoding="utf-8"))["entries"]
    if e["kind"] == "feat"}
ABILITIES = ["str", "dex", "con", "int", "wis", "cha"]
REPEATABLE = ("***Repeatable.***", "rule", {"id": "repeatable", "repeatable": True})


def asi(choices, maximum):
    """'Ability Score Increase' benefit: +1 to one of `choices`, to a maximum."""
    return ("***Ability Score Increase.***", "fx", {
        "op": "choice", "id": "ability_score_increase", "choose": 1, "options": [
            {"id": a, "label": a.upper(), "effects": [
                {"op": "modifier", "stat": f"ability_score.{a}", "mode": "add", "value": 1},
                {"op": "modifier", "stat": f"ability_score_max.{a}", "mode": "max", "value": maximum}]}
            for a in choices]})


def benefits():
    return {
        "Alert": [
            ("***Initiative Proficiency.***", "fx", {"op": "modifier", "stat": "initiative", "mode": "add",
                                                    "value": {"var": "proficiency_bonus"}}),
            ("***Initiative Swap.***", "fx", {
                "op": "trigger", "event": {"event": "initiative_rolled"}, "optional": True,
                "condition": {"not": {"pred": "has_condition", "args": {"condition": "incapacitated"}}},
                "then": [{"op": "modifier", "stat": "initiative", "mode": "set", "value": {"var": "chosen.ally_initiative"},
                          "note": "Swap Initiative with one willing ally in the same combat; not if either has the Incapacitated condition."}]})],
        "Magic Initiate": [
            ("***Two Cantrips.***", "fx", [
                {"op": "choice", "id": "spell_list", "choose": 1, "options": [
                    {"id": c, "label": c.title(), "value": f"dnd5e/spell-list/{c}", "effects": [
                        {"op": "grant", "refs": [f"dnd5e/spell-list/{c}"], "choose": 2, "note": "Two cantrips."}]}
                    for c in ("cleric", "druid", "wizard")]},
                {"op": "choice", "id": "spellcasting_ability", "choose": 1, "options": [
                    {"id": a, "label": a.upper(), "value": a, "effects": []} for a in ("int", "wis", "cha")]}]),
            ("***Level 1 Spell.***", "fx", [
                {"op": "grant", "refs": ["dnd5e/spell-list/cleric", "dnd5e/spell-list/druid", "dnd5e/spell-list/wizard"],
                 "choose": 1, "note": "One level 1 spell from the chosen list; always prepared."},
                {"op": "activation", "cost": "none", "frequency": {"count": 1, "per": "long_rest"},
                 "then": [{"op": "cast_spell", "spell": "dnd5e/feat/magic-initiate", "slot": "none",
                           "ability": {"var": "chosen.spellcasting_ability"}}],
                 "note": "The chosen level 1 spell; it can also be cast with any spell slots you have."}]),
            ("***Spell Change.***", "rule", {"id": "spell_change", "on": "level_gained", "count": 1, "same_level": True,
                                            "same_list": True}),
            ("***Repeatable.***", "rule", {"id": "repeatable", "repeatable": True, "each_time": "different_spell_list"})],
        "Savage Attacker": [(None, "fx", {
            "op": "trigger", "event": {"event": "hits_with_attack_roll"}, "optional": True,
            "condition": {"pred": "attack_uses_weapon"}, "frequency": {"count": 1, "per": "turn"},
            "then": [{"op": "reroll", "rolls": ["damage_roll"], "keep": "choice",
                      "note": "Roll the weapon's damage dice twice and use either roll."}]})],
        "Skilled": [
            (None, "fx", {"op": "choice", "id": "skilled", "choose": 3, "distinct": False, "options": [
                {"id": "skill", "label": "Skill", "effects": [{"op": "proficiency", "category": "skill", "choose": 1,
                                                               "from": ["any"]}]},
                {"id": "tool", "label": "Tool", "effects": [{"op": "proficiency", "category": "tool", "choose": 1,
                                                             "from": ["any"]}]}]}),
            REPEATABLE],
        "Ability Score Improvement": [
            (None, "fx", {"op": "choice", "id": "asi", "choose": 1, "options": [
                {"id": "plus_two", "label": "+2 to one ability score", "effects": [
                    {"op": "modifier", "stat": "ability_score.chosen", "mode": "add", "value": 2}]},
                {"id": "plus_one_two", "label": "+1 to two ability scores", "effects": [
                    {"op": "modifier", "stat": "ability_score.chosen", "mode": "add", "value": 1},
                    {"op": "modifier", "stat": "ability_score.chosen_second", "mode": "add", "value": 1}]}]}),
            (None, "rule", {"id": "cap", "max_score": 20}),
            REPEATABLE],
        "Grappler": [
            asi(["str", "dex"], 20),
            ("***Punch and Grab.***", "fx", {
                "op": "trigger", "event": {"event": "hits_with_attack_roll"}, "optional": True,
                "condition": {"all": [{"pred": "attack_is_unarmed_strike"}, {"pred": "own_turn"},
                                      {"pred": "attack_from_feature", "args": {"feature": "attack_action"}}]},
                "frequency": {"count": 1, "per": "turn"},
                "then": [{"op": "reference", "rule": "dnd5e/rule/unarmed-strike",
                          "note": "Use both the Damage and the Grapple option."}]}),
            ("***Attack Advantage.***", "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["attack_roll"],
                                              "when": {"pred": "target_grappled_by_source"}}),
            ("***Fast Wrestler.***", "rule", {"id": "fast_wrestler", "move_grappled_creature_extra_cost": 0,
                                             "max_size": "own_size_or_smaller"})],
        "Archery": [(None, "fx", {"op": "modifier", "stat": "attack_roll", "mode": "add", "value": 2,
                                  "when": {"pred": "attack_with_ranged_weapon"}})],
        "Defense": [(None, "fx", {"op": "modifier", "stat": "ac", "mode": "add", "value": 1,
                                  "when": {"any": [{"pred": "wearing_armor", "args": {"category": c}}
                                                   for c in ("light", "medium", "heavy")]}})],
        "Great Weapon Fighting": [(None, "fx", {
            "op": "modifier", "stat": "damage_die_min", "mode": "min", "value": 3,
            "when": {"all": [{"pred": "attack_with_melee_weapon"}, {"pred": "wielded_two_handed"},
                             {"any": [{"pred": "attack_with_weapon_property", "args": {"property": "two-handed"}},
                                      {"pred": "attack_with_weapon_property", "args": {"property": "versatile"}}]}]},
            "note": "Treat any 1 or 2 on a damage die as a 3."})],
        "Two-Weapon Fighting": [(None, "fx", {
            "op": "modifier", "stat": "damage_roll", "mode": "add", "value": {"var": "chosen.attack_ability_mod"},
            "when": {"all": [{"pred": "extra_attack_from_light_property"}, {"not": {"pred": "adds_ability_mod_to_damage"}}]}})],
        "Boon of Combat Prowess": [
            asi(ABILITIES, 30),
            ("***Peerless Aim.***", "fx", {
                "op": "trigger", "event": {"event": "misses_with_attack_roll"}, "optional": True,
                "frequency": {"count": 1, "per": "turn"},
                "then": [{"op": "auto_result", "rolls": ["attack_roll"], "result": "hit",
                          "note": "Usable again from the start of your next turn."}]})],
        "Boon of Dimensional Travel": [
            asi(ABILITIES, 30),
            ("***Blink Steps.***", "fx", {
                "op": "trigger", "event": {"event": "takes_attack_or_magic_action"}, "optional": True,
                "then": [{"op": "move", "mode": "teleport", "distance_feet": 30,
                          "note": "To an unoccupied space you can see."}]})],
        "Boon of Fate": [
            asi(ABILITIES, 30),
            ("***Improve Fate.***", "fx", {
                "op": "trigger", "event": {"event": "d20_test_resolved"}, "optional": True,
                "condition": {"any": [{"pred": "target_is_source"}, {"pred": "within_feet", "args": {"feet": 60}}]},
                "frequency": {"count": 1, "per": "improve_fate"},
                "then": [{"op": "modifier", "stat": "triggering_roll", "mode": "add",
                          "value": {"op": "mul", "args": [{"var": "chosen.sign"}, "2d4"]},
                          "note": "Bonus or penalty; recharges when you roll Initiative or finish a Short or Long Rest."}]})],
        "Boon of Irresistible Offense": [
            asi(["str", "dex"], 30),
            ("***Overcome Defenses.***", "rule", {"id": "ignore_resistance",
                                                 "damage_types": ["bludgeoning", "piercing", "slashing"]}),
            ("***Overwhelming Strike.***", "fx", {
                "op": "trigger", "event": {"event": "rolls_natural_20_attack"}, "optional": True,
                "then": [{"op": "damage", "target": {"kind": "inherit"},
                          "amount": {"var": "ability_score.chosen"}, "damage_type": {"var": "chosen.attack_damage_type"},
                          "note": "Equal to the ability score increased by this feat."}]})],
        "Boon of Spell Recall": [
            asi(["int", "wis", "cha"], 30),
            ("***Free Casting.***", "rule", {"id": "free_casting", "slot_levels": [1, 4], "roll": "1d4",
                                            "slot_not_expended_if_roll_equals_slot_level": True})],
        "Boon of the Night Spirit": [
            asi(ABILITIES, 30),
            ("***Merge with Shadows.***", "fx", {
                "op": "activation", "cost": "bonus_action",
                "requires": {"any": [{"pred": "in_dim_light"}, {"pred": "in_darkness"}]},
                "then": [{"op": "apply_condition", "condition": C("invisible"), "target": {"kind": "self"},
                          "note": "Ends immediately after you take an action, a Bonus Action, or a Reaction."}]}),
            ("***Shadowy Form.***", "fx", {
                "op": "defense", "kind": "resistance",
                "damage_types": ["acid", "bludgeoning", "cold", "fire", "force", "lightning", "necrotic", "piercing",
                                 "poison", "slashing", "thunder"],
                "when": {"any": [{"pred": "in_dim_light"}, {"pred": "in_darkness"}]},
                "note": "All damage except Psychic and Radiant."})],
        "Boon of Truesight": [
            asi(ABILITIES, 30),
            ("***Truesight.***", "fx", {"op": "sense", "sense": "truesight", "range_feet": 60})],
    }


def feat_entries():
    E, B = [], benefits()
    for cat, names in CATS.items():
        for name in names:
            nodes = section(name, 4, page=None if name != "Ability Score Improvement" else 87)
            pre = PREREQ.get(name)
            facets = {"category": slugify(cat).replace("-", "_")}
            if pre:
                facets["prerequisite"] = INV_PREREQ[f"dnd5e/feat/{slugify(name)}"]
            facets["repeatable"] = any(a == "***Repeatable.***" for a, _, _ in B[name])
            items = [(None, "rule", {"id": "category", "category": cat, **({"prerequisite": pre} if pre else {})})]
            items += B[name]
            E.append(build("feat", slugify(name), name, nodes, LOT,
                           f"Feats/Feat Descriptions/{cat} Feats/{name}", fix_anchors(nodes, items),
                           facets=facets))
    return E


def fix_anchors(nodes, items):
    """The benefit text follows the category line: anchor benefit items with no anchor at that paragraph."""
    body = [n for n in nodes if n.type == "p" and not n.text.startswith("*") or n.text.startswith("***")]
    first = body[0].text[:40] if body else None
    out = [items[0]]
    for a, tag, payload in items[1:]:
        out.append((first if a is None else a, tag, payload))
    return out


def section_entries():
    E = []
    E.append(build("rule", "feats", "Feats", section("Feats", 1, include_heading=True, stop_titles=("Feat Descriptions",)),
                   LOT, "Feats", [(None, "desc", None)], data={"sections": ["dnd5e/rule/feat-descriptions"]}))
    E.append(build("rule", "feat-descriptions", "Feat Descriptions",
                   section("Feat Descriptions", 2, stop_titles=("Parts of a Feat",)), LOT, "Feats/Feat Descriptions", [
                       (None, "rule", {"id": "categories", "categories": ["origin", "general", "fighting_style", "epic_boon"],
                                       "order": "alphabetical_within_category"})]))
    E.append(build("rule", "parts-of-a-feat", "Parts of a Feat", section("Parts of a Feat", 3), LOT,
                   "Feats/Feat Descriptions/Parts of a Feat", [
                       (None, "desc", None),
                       ("***Category.***", "rule", {"id": "category", "choose_from_category_when_specified": True,
                                                   "unspecified_any_category": True}),
                       ("***Prerequisite.***", "rule", {"id": "prerequisite", "must_meet_unless_feature_waives": True,
                                                       "class_prerequisite_min_level": 1}),
                       ("***Benefit.***", "rule", {"id": "benefit", "gain_benefits_when_had": True}),
                       ("***Repeatable.***", "rule", {"id": "repeatable", "default": False,
                                                     "only_with_repeatable_subsection": True})]))
    for cat, names in CATS.items():
        title = f"{cat} Feats"
        E.append(build("rule", slugify(title), title, section(title, 3, include_heading=True, stop_titles=tuple(names)),
                       LOT, f"Feats/Feat Descriptions/{title}", [(None, "sys", ["/data/feats"])],
                       data={"feats": [f"dnd5e/feat/{slugify(n)}" for n in names]}))
    E.append(build("rule", "sidebar-bonus-feats-at-level-20", "Bonus Feats at Level 20",
                   sidebar("Bonus Feats at Level 20"), LOT, "Character Creation/Level Advancement", [
                       (None, "md", {"id": "use_bonus_feats", "reason": "gm_judgment",
                                     "prompt": "Does the GM use feats as advancement after level 20?",
                                     "source_text": "A GM can use feats as a form of advancement after characters reach "
                                                    "level 20 to provide greater power to characters who have no more "
                                                    "levels to gain.", "pages": [23]}),
                       ("With this approach", "rule", {"id": "bonus_feats", "requires_character_level": 20,
                                                       "xp_threshold": 355000, "xp_per_feat": 30000,
                                                       "recommended_category": "epic_boon",
                                                       "any_qualifying_feat": True})]))
    return E


REGISTRY = {
    "stats": [{"id": "damage_die_min", "description": "Lowest value a damage die counts as.", "pages": [88]}],
    "frequencies": [{"id": "improve_fate", "description": "Until the creature rolls Initiative or finishes a Short or Long Rest.", "pages": [88]}],
    "events": [
        {"id": "takes_attack_or_magic_action", "description": "The creature takes the Attack action or the Magic action.", "pages": [88]},
        {"id": "d20_test_resolved", "description": "A creature succeeds on or fails a D20 Test.", "pages": [88]},
        {"id": "rolls_natural_20_attack", "description": "The creature rolls a 20 on the d20 for an attack roll.", "pages": [88]}],
    "predicates": [
        {"id": "target_grappled_by_source", "description": "The target has the Grappled condition from the source.", "type": "predicate", "pages": [87]},
        {"id": "wielded_two_handed", "description": "The weapon is held with two hands.", "type": "predicate", "pages": [88]},
        {"id": "extra_attack_from_light_property", "description": "The attack is the extra attack from using a Light weapon.", "type": "predicate", "pages": [88]},
        {"id": "adds_ability_mod_to_damage", "description": "The attack already adds the ability modifier to its damage.", "type": "predicate", "pages": [88]}],
}

if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = section_entries() + feat_entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
