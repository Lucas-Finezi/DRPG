#!/usr/bin/env python3
"""L14 (part) — Wizard and Evoker features."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classlib import CF, spellcasting  # noqa: E402
from entrylib import extend_registries, write_entry  # noqa: E402

LOT = "L14"
W = "Wizard"
LONG = {"event": "long_rest_finished"}
SHORT = {"event": "short_rest_finished"}
INT = {"var": "ability_mod.int"}
SP = lambda s: f"dnd5e/spell/{s}"  # noqa: E731
EVOCATION = {"pred": "spell_school", "args": {"school": "evocation"}}


def entries():
    E = []
    items = spellcasting(W, "int", ["dnd5e/gear/arcane-focus", "spellbook"], 4, [], "long_rest_any",
                         cantrips=(3, ["Light", "Mage Hand", "Ray of Frost"], "long_rest_finished"))
    k = next(i for i, it in enumerate(items) if it[0] == "***Spell Slots.***")
    items[k:k] = [("***Spellbook.***", "rule", {
        "id": "spellbook", "object_size": "tiny", "weight_lb": 3, "pages": 100,
        "readable_by": ["owner", SP("identify")], "start_level_1_spells": 6,
        "recommended": [SP(s) for s in ("detect-magic", "feather-fall", "mage-armor", "magic-missile", "sleep",
                                        "thunderwave")],
        "per_level_gained_after_1": 2, "must_have_slot_level": True, "from": "dnd5e/spell-list/wizard"}),
                  ("***Spellbook.***", "ref", ["dnd5e/rule/sidebar-expanding-and-replacing-a-spellbook"])]
    E.append(CF(W, "Spellcasting", 1, items))
    E.append(CF(W, "Ritual Adept", 1, [(None, "rule", {
        "id": "ritual_adept", "cast_as_ritual": "ritual_tag_spells_in_spellbook", "needs_prepared": False,
        "must_read_from_book": True, "ritual_rules": "dnd5e/rule/spell-level"})]))
    E.append(CF(W, "Arcane Recovery", 1, [
        (None, "fx", {"op": "trigger", "event": SHORT, "optional": True, "frequency": {"count": 1, "per": "long_rest"},
                      "then": [{"op": "restore", "resource": "spell_slot", "amount": {
                          "op": "div", "round": "up", "args": [{"var": "class_level.wizard"}, 2]},
                          "note": "Combined slot levels; none of level 6 or higher."}]}),
        ("Once you use this feature", "sys", ["/effects/0"])]))
    E.append(CF(W, "Scholar", 2, [(None, "fx", {
        "op": "proficiency", "category": "skill", "expertise": True, "choose": 1,
        "from": ["arcana", "history", "investigation", "medicine", "nature", "religion"],
        "note": "A skill you have proficiency in."})]))
    E.append(CF(W, "Wizard Subclass", 3, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/subclass/evoker"], "choose": 1,
        "note": "Gain each subclass feature of your Wizard level or lower."})]))
    E.append(CF(W, "Ability Score Improvement", 4, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/ability-score-improvement"],
        "note": "Or another feat you qualify for; again at Wizard levels 8, 12 and 16."})]))
    E.append(CF(W, "Memorize Spell", 5, [(None, "rule", {
        "id": "memorize", "on": "short_rest_finished", "replace_prepared": 1, "levels": "1+", "from": "spellbook"})]))
    E.append(CF(W, "Spell Mastery", 18, [
        (None, "fx", {"op": "activation", "cost": "action",
                      "then": [{"op": "cast_spell", "spell": "dnd5e/spell-list/wizard", "slot": "none"}],
                      "note": "One of the chosen level 1 and level 2 spells, at its lowest level; at will."}),
        (None, "rule", {"id": "mastery_spells", "levels": [1, 2], "from": "spellbook", "casting_time": "action",
                        "always_prepared": True, "higher_level_requires_slot": True}),
        ("Whenever you finish a Long Rest", "rule", {"id": "replace", "on": "long_rest_finished", "count": 1,
                                                     "same_level": True})]))
    E.append(CF(W, "Epic Boon", 19, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/boon-of-spell-recall"],
        "note": "An Epic Boon feat or another feat you qualify for; Boon of Spell Recall is recommended."})]))
    E.append(CF(W, "Signature Spells", 20, [
        (None, "rule", {"id": "signature_spells", "count": 2, "level": 3, "from": "spellbook", "always_prepared": True,
                        "higher_level_requires_slot": True}),
        (None, "fx", {"op": "resource", "resource": "signature_spells", "max": 2, "note": "One free casting of each.",
                      "recovery": [{"on": SHORT, "amount": "all"}, {"on": LONG, "amount": "all"}]})]))

    S = "Evoker"
    E.append(CF(W, "Evocation Savant", 3, [
        (None, "rule", {"id": "free_spells", "count": 2, "school": "evocation", "max_level": 2,
                        "from": "dnd5e/spell-list/wizard", "to": "spellbook", "cost": 0}),
        ("In addition, whenever you gain access", "rule", {
            "id": "new_slot_level", "on": "new_spell_slot_level", "count": 1, "school": "evocation", "cost": 0})], sub=S))
    E.append(CF(W, "Potent Cantrip", 3, [(None, "fx", {
        "op": "trigger", "event": {"event": "cantrip_misses_or_saved"},
        "then": [{"op": "damage", "amount": {"op": "div", "args": [{"var": "damage_amount"}, 2]},
                  "damage_type": {"var": "chosen.cantrip_damage_type"}, "target": {"kind": "inherit"},
                  "note": "Half the cantrip's damage (if any) and no additional effect."}]})], sub=S))
    E.append(CF(W, "Sculpt Spells", 6, [(None, "fx", {
        "op": "trigger", "event": {"event": "casts_spell"}, "optional": True, "condition": EVOCATION,
        "then": [{"op": "auto_result", "rolls": ["saving_throw"], "result": "success",
                  "target": {"kind": "creature", "must_see": True,
                             "count": {"op": "add", "args": [1, {"var": "spell_level"}]}},
                  "note": "No damage instead of half damage on a successful save."}]})], sub=S))
    E.append(CF(W, "Empowered Evocation", 10, [(None, "fx", {
        "op": "modifier", "stat": "damage_roll", "mode": "add", "value": INT,
        "when": {"all": [EVOCATION, {"pred": "spell_of_class", "args": {"class": "wizard"}}]},
        "note": "One damage roll of that spell."})], sub=S))
    E.append(CF(W, "Overchannel", 14, [
        (None, "fx", {"op": "trigger", "event": {"event": "casts_spell"}, "optional": True,
                      "condition": {"all": [{"pred": "spell_of_class", "args": {"class": "wizard"}},
                                            {"pred": "spell_slot_level_between", "args": {"min": 1, "max": 5}}]},
                      "then": [{"op": "modifier", "stat": "spell_damage_dice", "mode": "set", "value": 0,
                                "note": "Maximum damage on the turn you cast it."}]}),
        ("The first time you do so", "fx", {
            "op": "damage", "damage_type": "necrotic", "target": {"kind": "self"},
            "when": {"pred": "used_since_long_rest", "args": {"feature": "evoker-overchannel"}},
            "amount": {"dice": {"count": {"op": "mul", "args": [
                {"var": "spell_slot_level"}, {"op": "add", "args": [1, {"var": "uses_since_rest.evoker-overchannel"}]}]},
                "faces": 12}},
            "note": "2d12 per slot level on the second use, +1d12 per level on each later use; ignores Resistance and Immunity."}),
        ("Each time you use this feature again", "sys", ["/effects/1"])], sub=S))
    return E


REGISTRY = {
    "stats": [{"id": "spell_damage_dice", "description": "How the spell's damage dice are resolved (0 = maximum).", "pages": [82]}],
    "events": [{"id": "cantrip_misses_or_saved", "description": "The creature casts a cantrip at a creature and misses with the attack roll or the target succeeds on its save.", "pages": [82]}],
    "predicates": [
        {"id": "spell_school", "description": "The spell belongs to this school (param).", "params": ["school"], "type": "predicate", "pages": [82]},
        {"id": "spell_slot_level_between", "description": "The spell slot level is within [min, max] (params).", "params": ["min", "max"], "type": "predicate", "pages": [82]},
        {"id": "used_since_long_rest", "description": "The feature (param) was already used since the last Long Rest.", "params": ["feature"], "type": "predicate", "pages": [82]}],
}

if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
