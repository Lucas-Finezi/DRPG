#!/usr/bin/env python3
"""L14 (part) — Bard and College of Lore features."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classlib import CF, col, spellcasting  # noqa: E402
from entrylib import extend_registries, write_entry  # noqa: E402

LOT = "L14"
B = "Bard"
LONG = {"event": "long_rest_finished"}
SHORT = {"event": "short_rest_finished"}
BI_DIE = col(B, "Bardic Die")


def entries():
    E = []
    E.append(CF(B, "Bardic Inspiration", 1, [
        (None, "rule", {"id": "bardic_inspiration_die", "die": BI_DIE, "start": "d6"}),
        ("***Using Bardic Inspiration.***", "fx", {
            "op": "activation", "name": "Bardic Inspiration", "cost": "bonus_action",
            "uses": {"resource": "bardic_inspiration", "amount": 1},
            "target": {"kind": "creature", "count": 1, "range": {"kind": "distance", "feet": 60},
                       "filter": {"predicate": {"all": [{"not": {"pred": "target_is_source"}},
                                                        {"any": [{"pred": "can_see", "args": {"who": "source"}},
                                                                 {"pred": "can_hear_source"}]}]}}},
            "then": [{"op": "grant", "refs": ["dnd5e/feature/bard-bardic-inspiration"],
                      "note": "The creature gains one Bardic Inspiration die (only one at a time).",
                      "duration": {"kind": "hours", "amount": 1}}]}),
        ("Once within the next hour", "fx", {
            "op": "trigger", "event": {"event": "fails_d20_test"}, "optional": True,
            "condition": {"pred": "holds_bardic_inspiration_die"},
            "then": [{"op": "modifier", "stat": "d20_test", "mode": "add", "value": {"var": "rolled.bardic_inspiration_die"},
                      "note": "Roll the die and add it to the d20; the die is expended when rolled."}]}),
        ("***Number of Uses.***", "fx", {
            "op": "resource", "resource": "bardic_inspiration", "name": "Bardic Inspiration",
            "max": {"op": "max", "args": [1, {"var": "ability_mod.cha"}]},
            "recovery": [{"on": LONG, "amount": "all"}]}),
        ("***At Higher Levels.***", "sys", ["/data/rules/0"])]))
    E.append(CF(B, "Spellcasting", 1, spellcasting(
        B, "cha", ["dnd5e/tool/musical-instrument"], 4, ["Charm Person", "Color Spray", "Dissonant Whispers", "Healing Word"],
        "level_gain_one", cantrips=(2, ["Dancing Lights", "Vicious Mockery"], "level_gained"))))
    E.append(CF(B, "Expertise", 2, [
        (None, "fx", {"op": "proficiency", "category": "skill", "expertise": True, "choose": 2,
                      "from": ["proficient_skills"], "note": "Performance and Persuasion are recommended if proficient."}),
        ("At Bard level 9", "rule", {"id": "expertise_level_9", "level": 9, "choose": 2})]))
    E.append(CF(B, "Jack of All Trades", 2, [(None, "fx", {
        "op": "modifier", "stat": "ability_check", "mode": "add",
        "value": {"op": "div", "args": [{"var": "proficiency_bonus"}, 2]},
        "when": {"all": [{"pred": "check_uses_unproficient_skill"}, {"not": {"pred": "check_adds_proficiency_bonus"}}]}})]))
    E.append(CF(B, "Bard Subclass", 3, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/subclass/college-of-lore"], "choose": 1,
        "note": "Gain each subclass feature of your Bard level or lower."})]))
    E.append(CF(B, "Ability Score Improvement", 4, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/ability-score-improvement"],
        "note": "Or another feat you qualify for; again at Bard levels 8, 12 and 16."})]))
    E.append(CF(B, "Font of Inspiration", 5, [
        (None, "rule", {"id": "short_rest_recovery", "resource": "bardic_inspiration",
                        "recovery": [{"on": SHORT, "amount": "all"}, {"on": LONG, "amount": "all"}]}),
        ("In addition, you can expend a spell slot", "fx", {
            "op": "activation", "name": "Font of Inspiration", "cost": "none",
            "uses": {"resource": "spell_slot", "amount": 1},
            "then": [{"op": "restore", "resource": "bardic_inspiration", "amount": 1}]})]))
    E.append(CF(B, "Countercharm", 7, [(None, "fx", {
        "op": "trigger", "event": {"event": "fails_saving_throw"}, "cost": "reaction", "optional": True,
        "condition": {"all": [{"any": [{"pred": "target_is_source"}, {"pred": "within_feet", "args": {"feet": 30}}]},
                              {"any": [{"pred": "save_against_condition", "args": {"condition": "charmed"}},
                                       {"pred": "save_against_condition", "args": {"condition": "frightened"}}]}]},
        "then": [{"op": "reroll", "rolls": ["saving_throw"], "keep": "new"},
                 {"op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw"], "note": "The new roll."}]})]))
    E.append(CF(B, "Magical Secrets", 10, [(None, "rule", {
        "id": "magical_secrets", "extra_spell_lists": ["dnd5e/spell-list/bard", "dnd5e/spell-list/cleric", "dnd5e/spell-list/druid",
                                                       "dnd5e/spell-list/wizard"],
        "applies_to": ["new_prepared_spells_on_level_gain", "replacement_spells"], "count_as": "dnd5e/class/bard"})]))
    E.append(CF(B, "Superior Inspiration", 18, [(None, "fx", {
        "op": "trigger", "event": {"event": "initiative_rolled"},
        "then": [{"op": "restore", "resource": "bardic_inspiration", "amount": {
            "op": "max", "args": [0, {"op": "sub", "args": [2, {"var": "resource.bardic_inspiration"}]}]}}]})]))
    E.append(CF(B, "Epic Boon", 19, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/boon-of-spell-recall"],
        "note": "An Epic Boon feat or another feat you qualify for; Boon of Spell Recall is recommended."})]))
    E.append(CF(B, "Words of Creation", 20, [
        (None, "fx", {"op": "grant", "refs": ["dnd5e/spell/power-word-heal", "dnd5e/spell/power-word-kill"],
                      "note": "Always prepared."}),
        ("When you cast either spell", "rule", {"id": "second_target", "spells": ["dnd5e/spell/power-word-heal",
                                                                                  "dnd5e/spell/power-word-kill"],
                                                "extra_targets": 1, "within_feet_of_first_target": 10})]))

    S = "College of Lore"
    E.append(CF(B, "Bonus Proficiencies", 3, [(None, "fx", {
        "op": "proficiency", "category": "skill", "choose": 3, "from": ["any"]})], sub=S))
    E.append(CF(B, "Cutting Words", 3, [(None, "fx", {
        "op": "trigger", "cost": "reaction", "optional": True,
        "event": {"event": "creature_roll_made"},
        "condition": {"all": [{"pred": "can_see", "args": {"who": "creature"}}, {"pred": "within_feet", "args": {"feet": 60}},
                              {"any": [{"pred": "roll_is", "args": {"roll": "damage_roll"}},
                                       {"pred": "roll_succeeded", "args": {"roll": "ability_check"}},
                                       {"pred": "roll_succeeded", "args": {"roll": "attack_roll"}}]}]},
        "then": [{"op": "spend", "resource": "bardic_inspiration", "amount": 1},
                 {"op": "modifier", "stat": "triggering_roll", "mode": "add",
                  "value": {"op": "mul", "args": [-1, {"var": "rolled.bardic_inspiration_die"}]}}]})], sub=S))
    E.append(CF(B, "Magical Discoveries", 6, [
        (None, "rule", {"id": "magical_discoveries", "count": 2,
                        "from": ["dnd5e/spell-list/cleric", "dnd5e/spell-list/druid", "dnd5e/spell-list/wizard"],
                        "level": "cantrip_or_has_slots"}),
        ("You always have the chosen spells prepared", "rule", {
            "id": "always_prepared", "always_prepared": True, "replace_on": "level_gained", "replace_count": 1})],
        sub=S))
    E.append(CF(B, "Peerless Skill", 14, [(None, "fx", {
        "op": "trigger", "event": {"event": "fails_roll"}, "optional": True,
        "condition": {"any": [{"pred": "roll_is", "args": {"roll": "ability_check"}},
                              {"pred": "roll_is", "args": {"roll": "attack_roll"}}]},
        "then": [{"op": "modifier", "stat": "triggering_roll", "mode": "add", "value": {"var": "rolled.bardic_inspiration_die"}},
                 {"op": "spend", "resource": "bardic_inspiration", "amount": 1,
                  "when": {"pred": "roll_succeeded", "args": {"roll": "triggering_roll"}},
                  "note": "On a failure, the Bardic Inspiration isn't expended."}]})], sub=S))
    return E


REGISTRY = {
    "variables": [
        {"id": "rolled", "description": "Result of a die rolled by the effect (param: die name, e.g. bardic_inspiration_die).", "params": ["die"], "type": "number", "pages": [31]},
        {"id": "resource", "description": "Current (unexpended) uses of a resource of the creature (param: resource id).", "params": ["resource"], "type": "number", "pages": [33]}],
    "stats": [{"id": "triggering_roll", "description": "The roll that caused the trigger.", "pages": [35]}],
    "events": [
        {"id": "fails_d20_test", "description": "The creature fails a D20 Test.", "pages": [31]},
        {"id": "fails_saving_throw", "description": "A creature fails a saving throw.", "pages": [33]},
        {"id": "fails_roll", "description": "The creature makes a roll and fails.", "pages": [35]},
        {"id": "creature_roll_made", "description": "A creature makes a roll (damage roll, ability check, attack roll...).", "pages": [35]}],
    "predicates": [
        {"id": "can_hear_source", "description": "The creature can hear the source.", "type": "predicate", "pages": [31]},
        {"id": "holds_bardic_inspiration_die", "description": "The creature has an unexpended Bardic Inspiration die.", "type": "predicate", "pages": [31]},
        {"id": "check_uses_unproficient_skill", "description": "The ability check uses a skill the creature lacks proficiency in.", "type": "predicate", "pages": [32]},
        {"id": "check_adds_proficiency_bonus", "description": "The check already uses the Proficiency Bonus.", "type": "predicate", "pages": [32]},
        {"id": "roll_is", "description": "The triggering roll is of this kind (param: roll).", "params": ["roll"], "type": "predicate", "pages": [35]},
        {"id": "roll_succeeded", "description": "The roll (param) succeeds.", "params": ["roll"], "type": "predicate", "pages": [35]}],
}

if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
