#!/usr/bin/env python3
"""L14 (part) — Cleric and Life Domain features."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classlib import CF, col, spell_table, spellcasting  # noqa: E402
from entrylib import extend_registries, write_entry  # noqa: E402

LOT = "L14"
K = "Cleric"
LONG = {"event": "long_rest_finished"}
SHORT = {"event": "short_rest_finished"}
C = lambda s: f"dnd5e/condition/{s}"  # noqa: E731
WIS = {"var": "ability_mod.wis"}
DC = {"var": "spell_save_dc"}
SPARK = {"scale": {"by": "class_level.cleric", "steps": [{"from": 2, "value": 1}, {"from": 7, "value": 2},
                                                        {"from": 13, "value": 3}, {"from": 18, "value": 4}]}}


def entries():
    E = []
    E.append(CF(K, "Spellcasting", 1, spellcasting(
        K, "wis", ["dnd5e/gear/holy-symbol"], 4, ["Bless", "Cure Wounds", "Guiding Bolt", "Shield of Faith"], "long_rest_any",
        cantrips=(3, ["Guidance", "Sacred Flame", "Thaumaturgy"], "level_gained"))))
    E.append(CF(K, "Divine Order", 1, [
        (None, "fx", {"op": "choice", "id": "divine_order", "choose": 1, "options": [
            {"id": "protector", "label": "Protector", "effects": [
                {"op": "proficiency", "category": "weapon", "items": ["martial"]},
                {"op": "proficiency", "category": "armor", "items": ["heavy"]}]},
            {"id": "thaumaturge", "label": "Thaumaturge", "effects": [
                {"op": "modifier", "stat": "cantrips_known", "mode": "add", "value": 1,
                 "note": "One extra cantrip from the Cleric spell list."},
                {"op": "modifier", "stat": "ability_check.int", "mode": "add", "value": {"op": "max", "args": [1, WIS]},
                 "when": {"any": [{"pred": "check_uses_skill", "args": {"skill": "arcana"}},
                                  {"pred": "check_uses_skill", "args": {"skill": "religion"}}]}}]}]}),
        ("***Protector.***", "sys", ["/effects/0/options/0"]),
        ("***Thaumaturge.***", "sys", ["/effects/0/options/1"])]))
    spark = {"op": "activation", "name": "Divine Spark", "cost": "action", "action": "dnd5e/action/magic",
             "uses": {"resource": "channel_divinity", "amount": 1},
             "requires": {"pred": "holds_item", "args": {"item": "holy_symbol"}},
             "target": {"kind": "creature", "range": {"kind": "distance", "feet": 30}, "must_see": True,
                        "filter": {"predicate": {"not": {"pred": "target_is_source"}}}},
             "then": [{"op": "choice", "id": "divine_spark_mode", "choose": 1, "options": [
                 {"id": "heal", "label": "Restore Hit Points", "effects": [
                     {"op": "heal", "amount": {"op": "add", "args": [
                         {"dice": {"count": SPARK, "faces": 8}}, WIS]}}]},
                 {"id": "harm", "label": "Constitution save", "effects": [
                     {"op": "save", "ability": "con", "dc": DC, "half_on_success": True, "on_fail": [
                         {"op": "damage", "amount": {"op": "add", "args": [
                             {"dice": {"count": SPARK, "faces": 8}}, WIS]},
                          "damage_type": {"choose_from": ["necrotic", "radiant"]}}]}]}]}]}
    turn = {"op": "activation", "name": "Turn Undead", "cost": "action", "action": "dnd5e/action/magic",
            "uses": {"resource": "channel_divinity", "amount": 1},
            "requires": {"pred": "holds_item", "args": {"item": "holy_symbol"}},
            "then": [{"op": "save", "ability": "wis", "dc": DC,
                      "target": {"kind": "area", "area": {"shape": "emanation", "size_feet": 30, "origin": "self"},
                                 "filter": {"creature_types": ["undead"], "predicate": {"pred": "chosen_by_source"}}},
                      "on_fail": [{"op": "apply_condition", "condition": C("frightened"), "id": "turned_frightened",
                                   "duration": {"kind": "minutes", "amount": 1}},
                                  {"op": "apply_condition", "condition": C("incapacitated"), "id": "turned_incapacitated",
                                   "duration": {"kind": "minutes", "amount": 1}}]}]}
    E.append(CF(K, "Channel Divinity", 2, [
        (None, "rule", {"id": "channel_divinity", "effects": ["divine_spark", "turn_undead"],
                        "one_effect_per_use": True, "more_options_at_higher_levels": True}),
        ("You can use this class’s Channel Divinity twice.", "fx", {
            "op": "resource", "resource": "channel_divinity", "name": "Channel Divinity", "max": col(K, "Channel Divinity"),
            "recovery": [{"on": SHORT, "amount": 1}, {"on": LONG, "amount": "all"}]}),
        ("If a Channel Divinity effect requires a saving throw", "rule", {"id": "save_dc", "dc": "spell_save_dc"}),
        ("***Divine Spark.***", "fx", spark),
        ("You roll an additional d8", "rule", {"id": "divine_spark_dice", "dice_by_level": [
            {"from": 2, "dice": 1}, {"from": 7, "dice": 2}, {"from": 13, "dice": 3}, {"from": 18, "dice": 4}]}),
        ("***Turn Undead.***", "fx", turn),
        ("For that duration, it tries to move", "rule", {
            "id": "turned", "behavior": "moves_as_far_from_source_as_it_can",
            "ends_early_if": ["takes_any_damage", "source_incapacitated", "source_dies"]})]))
    E.append(CF(K, "Cleric Subclass", 3, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/subclass/life-domain"], "choose": 1,
        "note": "Gain each subclass feature of your Cleric level or lower."})]))
    E.append(CF(K, "Ability Score Improvement", 4, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/ability-score-improvement"],
        "note": "Or another feat you qualify for; again at Cleric levels 8, 12 and 16."})]))
    E.append(CF(K, "Sear Undead", 5, [(None, "fx", {
        "op": "trigger", "event": {"event": "uses_feature.cleric-channel-divinity.turn_undead"}, "optional": True,
        "then": [{"op": "damage", "amount": {"dice": {"count": {"op": "max", "args": [1, WIS]}, "faces": 8}},
                  "damage_type": "radiant", "target": {"kind": "inherit"},
                  "note": "Each Undead that failed its save; this damage doesn't end the turn effect."}]})]))
    E.append(CF(K, "Blessed Strikes", 7, [
        (None, "fx", {"op": "choice", "id": "blessed_strikes", "choose": 1, "options": [
            {"id": "divine_strike", "label": "Divine Strike", "effects": [
                {"op": "trigger", "event": {"event": "hits_with_attack_roll"}, "optional": True,
                 "condition": {"all": [{"pred": "own_turn"}, {"pred": "attack_uses_weapon"}]},
                 "frequency": {"count": 1, "per": "turn"},
                 "then": [{"op": "damage", "amount": "1d8", "damage_type": {"choose_from": ["necrotic", "radiant"]},
                           "target": {"kind": "inherit"}}]}]},
            {"id": "potent_spellcasting", "label": "Potent Spellcasting", "effects": [
                {"op": "modifier", "stat": "damage_roll", "mode": "add", "value": WIS,
                 "when": {"pred": "cantrip_of_class", "args": {"class": "cleric"}}}]}]}),
        ("***Divine Strike.***", "sys", ["/effects/0/options/0"]),
        ("***Potent Spellcasting.***", "sys", ["/effects/0/options/1"])]))
    E.append(CF(K, "Divine Intervention", 10, [(None, "fx", {
        "op": "activation", "name": "Divine Intervention", "cost": "action", "action": "dnd5e/action/magic",
        "frequency": {"count": 1, "per": "long_rest"},
        "then": [{"op": "cast_spell", "spell": "dnd5e/spell-list/cleric", "slot": "none", "components": ["V", "S"],
                  "note": "Any Cleric spell of level 5 or lower that doesn't require a Reaction; no Material components."}]}),
        (None, "rule", {"id": "spell_choice", "spell_list": "dnd5e/spell-list/cleric", "max_level": 5,
                        "excludes_casting_time": "reaction", "no_spell_slot": True, "no_material_components": True})]))
    E.append(CF(K, "Improved Blessed Strikes", 14, [
        (None, "rule", {"id": "improves", "feature": "dnd5e/feature/cleric-blessed-strikes"}),
        ("***Divine Strike.***", "rule", {"id": "divine_strike", "damage": "2d8"}),
        ("***Potent Spellcasting.***", "fx", {
            "op": "trigger", "event": {"event": "deals_damage_with_spell"}, "optional": True,
            "condition": {"pred": "cantrip_of_class", "args": {"class": "cleric"}},
            "then": [{"op": "temp_hp", "amount": {"op": "mul", "args": [2, WIS]},
                      "target": {"kind": "creature", "range": {"kind": "distance", "feet": 60}},
                      "note": "You or another creature."}]})]))
    E.append(CF(K, "Epic Boon", 19, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/boon-of-fate"],
        "note": "An Epic Boon feat or another feat you qualify for; Boon of Fate is recommended."})]))
    E.append(CF(K, "Greater Divine Intervention", 20, [(None, "rule", {
        "id": "wish", "adds_spell_choice": "dnd5e/spell/wish", "feature": "dnd5e/feature/cleric-divine-intervention",
        "if_wish_cooldown": {"long_rests": "2d4"}})]))

    S = "Life Domain"
    E.append(CF(K, "Disciple of Life", 3, [(None, "fx", {
        "op": "trigger", "event": {"event": "spell_restores_hp"},
        "condition": {"pred": "spell_cast_with_slot"},
        "then": [{"op": "heal", "amount": {"op": "add", "args": [2, {"var": "spell_slot_level"}]},
                  "target": {"kind": "inherit"}, "note": "On the turn you cast the spell."}]})], sub=S))
    rows = spell_table("Life Domain Spells")
    E.append(CF(K, "Life Domain Spells", 3, [
        (None, "fx", [{"op": "grant", "refs": r["spells"], "when": {"pred": "class_level_at_least",
                                                                    "args": {"class": "cleric", "level": r["level"]}},
                       "note": "Always prepared."} for r in rows]),
        ("##### Life Domain Spells", "ref", ["dnd5e/spell-list/life-domain-spells"]),
        ("##### Life Domain Spells", "table", {
            "id": "life_domain_spells", "caption": "Life Domain Spells", "columns": ["Cleric Level", "Prepared Spells"],
            "rows": [[r["level"], r["spells"]] for r in rows]})], sub=S))
    E.append(CF(K, "Preserve Life", 3, [(None, "fx", {
        "op": "activation", "name": "Preserve Life", "cost": "action", "action": "dnd5e/action/magic",
        "uses": {"resource": "channel_divinity", "amount": 1},
        "requires": {"pred": "holds_item", "args": {"item": "holy_symbol"}},
        "then": [{"op": "heal", "amount": {"op": "mul", "args": [5, {"var": "class_level.cleric"}]},
                  "target": {"kind": "area", "area": {"shape": "emanation", "size_feet": 30, "origin": "self"},
                             "filter": {"predicate": {"all": [{"pred": "bloodied"}, {"pred": "chosen_by_source"}]}}},
                  "note": "Divided among the chosen creatures (can include you); no more than half each one's Hit Point maximum."}]})],
        sub=S))
    E.append(CF(K, "Blessed Healer", 6, [(None, "fx", {
        "op": "trigger", "event": {"event": "spell_restores_hp"},
        "condition": {"all": [{"pred": "spell_cast_with_slot"}, {"pred": "heals_other_creature"}]},
        "then": [{"op": "heal", "amount": {"op": "add", "args": [2, {"var": "spell_slot_level"}]},
                  "target": {"kind": "self"}}]})], sub=S))
    E.append(CF(K, "Supreme Healing", 17, [(None, "rule", {
        "id": "maximize_healing_dice", "sources": ["spell", "channel_divinity"], "healing_dice": "maximum"})], sub=S))
    return E


REGISTRY = {
    "stats": [{"id": "cantrips_known", "description": "Number of cantrips the creature knows from a feature.", "pages": [37]}],
    "events": [
        {"id": "uses_feature", "description": "The creature uses a feature (param: feature slug; optional option id).", "params": ["feature", "option"], "pages": [37]},
        {"id": "deals_damage_with_spell", "description": "The creature casts a spell and deals damage to a creature with it.", "pages": [38]},
        {"id": "spell_restores_hp", "description": "A spell the creature casts restores Hit Points to one or more creatures.", "pages": [40]}],
    "predicates": [
        {"id": "check_uses_skill", "description": "The ability check uses this skill (param).", "params": ["skill"], "type": "predicate", "pages": [37]},
        {"id": "holds_item", "description": "The creature holds or presents an item of this kind (param).", "params": ["item"], "type": "predicate", "pages": [37]},
        {"id": "attack_uses_weapon", "description": "The attack roll is made using a weapon.", "type": "predicate", "pages": [38]},
        {"id": "cantrip_of_class", "description": "The spell is a cantrip of this class (param) for the creature.", "params": ["class"], "type": "predicate", "pages": [38]},
        {"id": "spell_cast_with_slot", "description": "The spell was cast with a spell slot.", "type": "predicate", "pages": [40]},
        {"id": "heals_other_creature", "description": "The spell restores Hit Points to a creature other than the caster.", "type": "predicate", "pages": [40]},
        {"id": "class_level_at_least", "description": "The creature's level in a class is at least N (params: class, level).", "params": ["class", "level"], "type": "predicate", "pages": [40]}],
}

if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
