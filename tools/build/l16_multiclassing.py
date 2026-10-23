#!/usr/bin/env python3
"""L16 — Multiclassing: prerequisites, XP, Hit Points, Proficiency Bonus, proficiencies and the
special rules for Armor Class, Extra Attack and Spellcasting (with the Multiclass Spellcaster table).

The 'Starting Equipment at Higher Levels' table printed inside 'Prerequisites' belongs to L02.

Usage: python3 -I tools/build/l16_multiclassing.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import build, section, table_nodes, write_entry  # noqa: E402

LOT = "L16"
BASE = "Character Creation/Multiclassing"
CLASSES = ["barbarian", "bard", "cleric", "druid", "fighter", "monk", "paladin", "ranger", "rogue", "sorcerer",
           "warlock", "wizard"]
SYS = "dnd5e/system/dnd5e"


def slots_table():
    rows = [n.cells for n in table_nodes("Spell Slots per Spell Level", 26)[1:]
            if n.type == "t" and not n.text.startswith("| **")]
    return {"id": "multiclass_spellcaster", "caption": "Multiclass Spellcaster: Spell Slots per Spell Level",
            "columns": ["Level", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "rows": rows}


def entries():
    E = []
    sec = lambda slug, title, level, items, **kw: build(  # noqa: E731
        "rule", slug, title, section(title, level, page=kw.pop("page", None), **kw), LOT,
        f"{BASE}/{title}" if level == 3 else (BASE if level == 2 else f"{BASE}/Class Features/{title}"), items)
    E.append(build("rule", "multiclassing", "Multiclassing", section("Multiclassing", 2, stop_titles=("Prerequisites",)),
                   LOT, BASE, [(None, "rule", {
                       "id": "multiclassing", "optional_rule": True, "on": "level_gained",
                       "may_gain_level_in_new_class_instead": True})]))
    E.append(sec("multiclassing-prerequisites", "Prerequisites", 3, [
        (None, "rule", {"id": "prerequisites", "min_score": 13,
                        "abilities": "primary_ability_of_new_and_current_classes",
                        "primary_ability_from": [f"dnd5e/class/{c}" for c in CLASSES]})],
        page=24, skip_tables=("Starting Equipment at Higher Levels",)))
    E.append(sec("multiclassing-experience-points", "Experience Points", 3, [
        (None, "rule", {"id": "xp", "level_cost_based_on": "total_character_level"}),
        ("as shown in the Character Advancement table", "ref", ["dnd5e/rule/level-advancement"])], page=25))
    E.append(sec("multiclassing-hit-points-and-hit-point-dice", "Hit Points and Hit Point Dice", 3, [
        (None, "rule", {"id": "hit_points", "new_class_hp": "levels_after_1",
                        "level_1_hp_only_when_total_level_is": 1}),
        ("Add together the Hit Dice", "rule", {"id": "hit_dice", "pool": "sum_of_all_classes",
                                               "same_die_type": "pooled", "different_die_types": "tracked_separately"}),
        ("Add together the Hit Dice", "ref", ["dnd5e/rule/hit-point-dice"])], page=25))
    E.append(sec("multiclassing-proficiency-bonus", "Proficiency Bonus", 3, [
        (None, "rule", {"id": "proficiency_bonus", "based_on": "total_character_level"}),
        (None, "sys", [f"{SYS}#/proficiency_bonus"])], page=25))
    E.append(sec("multiclassing-proficiencies", "Proficiencies", 3, [
        (None, "rule", {"id": "proficiencies", "first_level_in_non_initial_class": "multiclass_proficiencies_of_class",
                        "see": [f"dnd5e/class/{c}" for c in CLASSES]})], page=25))
    E.append(build("rule", "multiclassing-class-features", "Class Features",
                   section("Class Features", 3, page=25, stop_titles=("Armor Class",)), LOT, f"{BASE}/Class Features", [
                       (None, "rule", {"id": "class_features", "gain_features_of_new_class_level": True,
                                       "check_each_class_multiclass_notes": True}),
                       ("Special rules apply", "rule", {"id": "special_rules", "for": [
                           "dnd5e/rule/multiclassing-armor-class", "dnd5e/rule/multiclassing-extra-attack",
                           "dnd5e/rule/multiclassing-spellcasting"]})]))
    E.append(sec("multiclassing-armor-class", "Armor Class", 4, [
        (None, "rule", {"id": "one_ac_calculation", "multiple_ac_calculations": "choose_one_at_a_time",
                        "example_features": ["dnd5e/feature/monk-unarmored-defense",
                                             "dnd5e/feature/draconic-sorcery-draconic-resilience"]})], page=25))
    E.append(sec("multiclassing-extra-attack", "Extra Attack", 4, [
        (None, "rule", {"id": "no_stacking", "extra_attack_from_multiple_classes_stacks": False, "max_attacks": 2,
                        "unless_feature_says": ["dnd5e/feature/fighter-two-extra-attacks"]}),
        ("Similarly, the Warlock’s Thirsting Blade", "rule", {
            "id": "thirsting_blade", "feature": "dnd5e/feature/warlock-invocation-thirsting-blade",
            "adds_attacks_with_extra_attack": False})], page=25))
    E.append(sec("multiclassing-spellcasting", "Spellcasting", 4, [
        (None, "rule", {"id": "applies", "when": "spellcasting_feature_from_more_than_one_class",
                        "single_spellcasting_class": "follow_that_class"}),
        ("***Spells Prepared.***", "rule", {"id": "spells_prepared", "per_class_as_single_classed": True,
                                           "spell_uses_class_spellcasting_ability": True}),
        ("***Cantrips.***", "rule", {"id": "cantrips", "scaling_based_on": "total_character_level",
                                    "unless_spell_says_otherwise": True}),
        ("***Spell Slots.***", "rule", {"id": "spell_slots", "caster_level": {"op": "add", "args": [
            {"var": "class_level.bard"}, {"var": "class_level.cleric"}, {"var": "class_level.druid"},
            {"var": "class_level.sorcerer"}, {"var": "class_level.wizard"},
            {"op": "div", "round": "up", "args": [{"var": "class_level.paladin"}, 2]},
            {"op": "div", "round": "up", "args": [{"var": "class_level.ranger"}, 2]}]},
            "table": "/data/tables/0", "slots_usable_for": "any_class_with_spellcasting"}),
        ("This table might give you spell slots", "rule", {
            "id": "higher_slots", "usable_only_for_lower_level_spells": True, "upcast_effects_apply": True}),
        ("***Pact Magic.***", "rule", {"id": "pact_magic", "pact_slots_cast_spellcasting_spells": True,
                                      "spellcasting_slots_cast_warlock_spells": True,
                                      "feature": "dnd5e/feature/warlock-pact-magic"}),
        ("##### Multiclass Spellcaster:", "table", slots_table())], page=25))
    return E


if __name__ == "__main__":
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
