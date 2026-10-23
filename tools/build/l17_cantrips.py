#!/usr/bin/env python3
"""L17 — Cantrips: the 27 level 0 spells.

Usage: python3 -I tools/build/l17_cantrips.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spelllib import (INHERIT, SELF, SPELL, area, attack, cantrip_count, cantrip_dice, cond, creatures,  # noqa: E402
                      dmg, light, md, ref, save, touch, until_turn, write_all)

LOT = "L17"
UPGRADE = "***Cantrip Upgrade.***"
SPELL_MOD = {"var": "spellcasting_mod"}


def S(name, items, **kw):
    return SPELL(name, items, LOT, **kw)


def options(prefix, labels):
    """One rule item per labelled option paragraph."""
    return [(f"***{label}.***", "rule", {"id": f"{prefix}_{i}", "option": label, **payload})
            for i, (label, payload) in enumerate(labels)]


def entries():
    E = []
    E.append(S("Acid Splash", [
        ("^", "fx", save("dex", dmg(cantrip_dice(6), "acid"), target=area("sphere", 5))),
        (UPGRADE, "sys", ["/effects/0/on_fail/0/amount"])]))
    E.append(S("Chill Touch", [
        ("^", "fx", attack("melee_spell", [dmg(cantrip_dice(10), "necrotic"),
                                           {"op": "restrict", "restrictions": ["regain_hit_points"],
                                            "duration": until_turn("turn_end", "source")}],
                           target={"kind": "creature", "range": {"kind": "touch"}},
                           note="A target within reach.")),
        (UPGRADE, "sys", ["/effects/0/on_hit/0/amount"])]))
    E.append(S("Dancing Lights", [
        ("^", "rule", {"id": "lights", "count": 4, "forms": ["torches", "lanterns", "glowing_orbs"],
                       "alternative": "one_medium_vaguely_humanlike_form", "hover_for_duration": True,
                       "light": light(dim=10, each_light=True)}),
        ("As a Bonus Action, you can move the lights", "fx", {
            "op": "activation", "cost": "bonus_action",
            "then": [{"op": "move", "mode": "move", "distance_feet": 60,
                      "note": "The lights, to a space within range."}]}),
        ("As a Bonus Action, you can move the lights", "rule", {
            "id": "spacing", "max_feet_between_lights": 20, "vanish_beyond_range": True})]))
    E.append(S("Druidcraft", [("^", "rule", {"id": "choose_one", "effects": 1, "within": "range"})] + options("effect", [
        ("Weather Sensor", {"size": "tiny", "harmless": True, "predicts_weather_hours": 24, "persists_rounds": 1}),
        ("Bloom", {"instant": True, "targets": ["flower", "seed_pod", "leaf_bud"]}),
        ("Sensory Effect", {"harmless": True, "fits_cube_feet": 5}),
        ("Fire Play", {"light_or_snuff": ["candle", "torch", "campfire"]})])))
    E.append(S("Eldritch Blast", [
        ("^", "fx", {"op": "repeat", "times": cantrip_count(1), "then": [
            attack("ranged_spell", dmg("1d10", "force"),
                   target={"kind": "creature_or_object", "range": "@range"})],
            "note": "One beam at level 1; separate attack roll per beam; same or different targets."}),
        (UPGRADE, "sys", ["/effects/0/times"])]))
    E.append(S("Elementalism", [("^", "rule", {"id": "choose_one", "effects": 1, "within": "range"})] + options("effect", [
        ("Beckon Air", {"area_cube_feet": 5, "breeze": True, "closes_open_doors_and_shutters": True,
                        "not_if_held_open": True}),
        ("Beckon Earth", {"area_square_feet": 5, "dust_or_sand": True, "or_single_word_in_dirt": True}),
        ("Beckon Fire", {"area_cube_feet": 5, "harmless_embers_and_smoke": True, "embers_light": ["candles", "torches", "lamps"],
                         "scent_lingers_minutes": 1}),
        ("Beckon Water", {"area_cube_feet": 5, "mist": True, "or_clean_water_cups": 1, "water_evaporates_minutes": 1}),
        ("Sculpt Element", {"material_fits_cube_feet": 1, "crude_shape_hours": 1})])))
    E.append(S("Fire Bolt", [
        ("^", "fx", attack("ranged_spell", dmg(cantrip_dice(10), "fire"),
                           target={"kind": "creature_or_object", "range": "@range"})),
        ("A flammable object hit by this spell", "ref", ["dnd5e/hazard/burning"]),
        ("A flammable object hit by this spell", "rule", {"id": "ignite", "object_flammable": True,
                                                          "not_worn_or_carried": True}),
        (UPGRADE, "sys", ["/effects/0/on_hit/0/amount"])]))
    E.append(S("Guidance", [("^", "fx", {
        "op": "modifier", "stat": "ability_check", "mode": "add", "value": "1d4", "target": touch(willing=True),
        "when": {"pred": "check_uses_skill", "args": {"skill": "chosen.skill"}}, "duration": "@duration",
        "note": "Choose a skill when casting."})]))
    E.append(S("Light", [
        ("^", "rule", {"id": "light", "target": "object_large_or_smaller_not_worn_or_carried_by_another",
                       "light": light(bright=20, dim=20), "color": "any"}),
        ("Covering the object", "rule", {"id": "blocked", "opaque_cover_blocks_light": True,
                                         "ends_if_cast_again": True})]))
    E.append(S("Mage Hand", [
        ("^", "rule", {"id": "hand", "appears_at": "point_within_range", "vanishes_if_farther_than_feet": 30,
                       "ends_if_cast_again": True}),
        ("When you cast the spell", "rule", {"id": "uses", "can": ["manipulate_object", "open_unlocked_door_or_container",
                                                                   "stow_or_retrieve_item_from_open_container",
                                                                   "pour_out_vial"]}),
        ("As a Magic action on your later turns", "fx", {
            "op": "activation", "cost": "action", "action": "dnd5e/action/magic",
            "then": [{"op": "move", "mode": "move", "distance_feet": 30, "note": "The hand; then use it again."}]}),
        ("The hand can’t attack", "rule", {"id": "limits", "cannot": ["attack", "activate_magic_items"],
                                           "max_carry_lb": 10})]))
    E.append(S("Mending", [
        ("^", "rule", {"id": "repair", "target": "object_touched", "breaks": 1, "max_dimension_feet": 1,
                       "leaves_no_trace": True}),
        ("This spell can physically repair a magic item", "rule", {"id": "magic_items", "repairs_physically": True,
                                                                   "restores_magic": False})]))
    E.append(S("Message", [
        ("^", "rule", {"id": "message", "target": "creature_within_range", "only_target_hears": True,
                       "reply_whisper_only_caster_hears": True}),
        ("You can cast this spell through solid objects", "rule", {
            "id": "through_barriers", "requires": ["familiar_with_target", "knows_target_beyond_barrier"],
            "blocked_by": ["magical_silence", "1_foot_stone_metal_or_wood", "thin_sheet_of_lead"]})]))
    E.append(S("Minor Illusion", [
        ("^", "rule", {"id": "illusion", "choose": ["sound", "image"], "ends_if_cast_again": True}),
        ("^", "ref", ["dnd5e/rule/illusions"]),
        ("If a creature takes a Study action", "fx", {
            "op": "check", "ability": "int", "skill": "investigation", "dc": {"var": "spell_save_dc"},
            "note": "A creature that takes the Study action to examine it; on a success it discerns the illusion, which becomes faint to it."}),
        ("If a creature takes a Study action", "ref", ["dnd5e/action/study"]),
        ("***Sound.***", "rule", {"id": "sound", "volume": "whisper_to_scream", "continuous_or_discrete": True}),
        ("***Image.***", "rule", {"id": "image", "object_max_cube_feet": 5, "no_other_senses": True,
                                 "physical_interaction_reveals": True})]))
    E.append(S("Poison Spray", [
        ("^", "fx", attack("ranged_spell", dmg(cantrip_dice(12), "poison"), target=creatures())),
        (UPGRADE, "sys", ["/effects/0/on_hit/0/amount"])]))
    E.append(S("Prestidigitation", [
        ("^", "rule", {"id": "choose_one", "max_active_non_instantaneous": 3})] + options("effect", [
            ("Sensory Effect", {"instantaneous": True, "harmless": True}),
            ("Fire Play", {"instantaneous": True, "light_or_snuff": ["candle", "torch", "small_campfire"]}),
            ("Clean or Soil", {"instantaneous": True, "object_max_cubic_feet": 1}),
            ("Minor Sensation", {"chill_warm_or_flavor_cubic_feet": 1, "nonliving": True, "hours": 1}),
            ("Magic Mark", {"color_mark_or_symbol": True, "hours": 1}),
            ("Minor Creation", {"trinket_or_illusory_image": True, "fits_in_hand": True,
                                "lasts_until": "end_of_next_turn", "no_damage_no_value": True})])))
    E.append(S("Produce Flame", [
        ("^", "rule", {"id": "flame", "in_hand": True, "no_heat_ignites_nothing": True,
                       "light": light(bright=20, dim=20), "ends_if_cast_again": True}),
        ("Until the spell ends, you can take a Magic action", "fx", {
            "op": "activation", "cost": "action", "action": "dnd5e/action/magic",
            "then": [attack("ranged_spell", dmg(cantrip_dice(8), "fire"),
                            target={"kind": "creature_or_object", "range": {"kind": "distance", "feet": 60}})]}),
        (UPGRADE, "sys", ["/effects/0/then/0/on_hit/0/amount"])]))
    E.append(S("Ray of Frost", [
        ("^", "fx", attack("ranged_spell", [dmg(cantrip_dice(8), "cold"),
                                            {"op": "speed", "movement": "walk", "mode": "add", "value": -10,
                                             "duration": until_turn("turn_start", "source")}], target=creatures())),
        (UPGRADE, "sys", ["/effects/0/on_hit/0/amount"])]))
    E.append(S("Resistance", [("^", "fx", {
        "op": "trigger", "event": {"event": "damage_taken"}, "target": touch(willing=True),
        "condition": {"pred": "deals_damage_type", "args": {"type": "chosen.damage_type"}},
        "frequency": {"count": 1, "per": "turn"}, "duration": "@duration",
        "note": "Damage type chosen when casting: Acid, Bludgeoning, Cold, Fire, Lightning, Necrotic, Piercing, Poison, Radiant, Slashing or Thunder.",
        "then": [{"op": "modifier", "stat": "damage_taken", "mode": "add", "value": {"op": "neg", "args": ["1d4"]}}]})]))
    E.append(S("Sacred Flame", [
        ("^", "fx", save("dex", dmg(cantrip_dice(8), "radiant"), target=creatures(must_see=True))),
        ("The target gains no benefit", "rule", {"id": "ignores_cover", "cover_ignored": ["half", "three_quarters"],
                                                 "for": "this_save", "rule": "dnd5e/rule/cover"}),
        (UPGRADE, "sys", ["/effects/0/on_fail/0/amount"])]))
    E.append(S("Shillelagh", [
        ("^", "fx", [
            {"op": "modifier", "stat": "attack_ability", "mode": "set", "value": SPELL_MOD,
             "when": {"pred": "attack_with_chosen_weapon"}, "duration": "@duration",
             "note": "Club or Quarterstaff you are holding; melee attack and damage rolls; optional."},
            {"op": "modifier", "stat": "weapon_damage_die", "mode": "set", "when": {"pred": "attack_with_chosen_weapon"},
             "duration": "@duration",
             "value": {"scale": {"by": "level", "steps": [{"from": 1, "value": "1d8"}, {"from": 5, "value": "1d10"},
                                                          {"from": 11, "value": "1d12"}, {"from": 17, "value": "2d6"}]}}}]),
        ("^", "rule", {"id": "damage_type", "choose_from": ["force", "normal_damage_type"]}),
        ("The spell ends early", "rule", {"id": "ends", "ends_on": ["cast_again", "let_go_of_weapon"]}),
        (UPGRADE, "sys", ["/effects/1/value"])]))
    E.append(S("Shocking Grasp", [
        ("^", "fx", attack("melee_spell", [dmg(cantrip_dice(8), "lightning"),
                                           {"op": "restrict", "restrictions": ["make_opportunity_attacks"],
                                            "duration": until_turn("turn_start", "target")}],
                           target={"kind": "creature", "range": {"kind": "touch"}})),
        (UPGRADE, "sys", ["/effects/0/on_hit/0/amount"])]))
    E.append(S("Sorcerous Burst", [
        ("^", "fx", attack("ranged_spell", dmg(cantrip_dice(8), ["acid", "cold", "fire", "lightning", "poison",
                                                                "psychic", "thunder"]),
                           target={"kind": "creature_or_object", "range": "@range"})),
        ("If you roll an 8 on a d8", "rule", {"id": "exploding_d8", "on_roll": 8, "add_d8": True,
                                              "max_extra_dice": SPELL_MOD}),
        (UPGRADE, "sys", ["/effects/0/on_hit/0/amount"])]))
    E.append(S("Spare the Dying", [
        ("^", "fx", ref("dnd5e/rule/stable", target={"kind": "creature", "range": "@range",
                                                     "filter": {"predicate": {"pred": "at_zero_hp"}}},
                        note="A creature with 0 Hit Points that isn't dead becomes Stable.")),
        (UPGRADE, "rule", {"id": "range_upgrade", "range_feet": {"scale": {"by": "level", "steps": [
            {"from": 1, "value": 15}, {"from": 5, "value": 30}, {"from": 11, "value": 60}, {"from": 17, "value": 120}]}}})]))
    E.append(S("Starry Wisp", [
        ("^", "fx", attack("ranged_spell", [dmg(cantrip_dice(8), "radiant"),
                                            {"op": "restrict", "restrictions": ["benefit_from_invisible"],
                                             "duration": until_turn("turn_end", "source")}],
                           target={"kind": "creature_or_object", "range": "@range"})),
        ("^", "rule", {"id": "glow", "light": light(dim=10), "until": "end_of_your_next_turn"}),
        (UPGRADE, "sys", ["/effects/0/on_hit/0/amount"])]))
    E.append(S("Thaumaturgy", [("^", "rule", {"id": "choose_one", "max_active_1_minute_effects": 3})] + [
        ("***Altered Eyes.***", "rule", {"id": "altered_eyes", "minutes": 1}),
        ("***Booming Voice.***", "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["ability_check.cha"],
                                       "when": {"pred": "check_uses_skill", "args": {"skill": "intimidation"}},
                                       "duration": {"kind": "minutes", "amount": 1},
                                       "note": "Your voice booms up to three times as loud as normal."}),
        ("***Fire Play.***", "rule", {"id": "fire_play", "flicker_brighten_dim_or_recolor": True, "minutes": 1}),
        ("***Invisible Hand.***", "rule", {"id": "invisible_hand", "instantaneous": True,
                                          "open_or_slam": "unlocked_door_or_window"}),
        ("***Phantom Sound.***", "rule", {"id": "phantom_sound", "instantaneous": True, "origin": "point_within_range"}),
        ("***Tremors.***", "rule", {"id": "tremors", "harmless": True, "minutes": 1})]))
    E.append(S("True Strike", [
        ("^", "fx", {"op": "choice", "id": "weapon_attack", "choose": 1, "options": [
            {"id": k, "label": k.replace("_", " ").title(), "effects": [attack(k)]}
            for k in ("melee_weapon", "ranged_weapon")],
            "note": "One attack with the weapon used in the casting."}),
        ("^", "fx", {"op": "modifier", "stat": "attack_ability", "mode": "set", "value": SPELL_MOD,
                     "note": "Attack and damage rolls of that attack, instead of Strength or Dexterity."}),
        ("^", "rule", {"id": "damage_type", "choose_from": ["radiant", "normal_damage_type"]}),
        (UPGRADE, "fx", {"op": "trigger", "event": {"event": "hits_with_attack_roll"}, "then": [
            dmg({"dice": {"count": {"scale": {"by": "level", "steps": [
                {"from": 5, "value": 1}, {"from": 11, "value": 2}, {"from": 17, "value": 3}]}}, "faces": 6}},
                "radiant", target=INHERIT)],
            "condition": {"pred": "character_level_at_least", "args": {"level": 5}}})]))
    E.append(S("Vicious Mockery", [
        ("^", "fx", save("wis", [dmg(cantrip_dice(6), "psychic"),
                                 {"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll"],
                                  "duration": until_turn("turn_end", "target"),
                                  "note": "Only the next attack roll it makes."}],
                         target={"kind": "creature", "range": "@range",
                                 "filter": {"predicate": {"any": [{"pred": "can_be_seen_by", "args": {"who": "source"}},
                                                                  {"pred": "can_hear_source"}]}}})),
        (UPGRADE, "sys", ["/effects/0/on_fail/0/amount"])]))
    return E


REGISTRY = {
    "restrictions": [
        {"id": "regain_hit_points", "description": "The creature can't regain Hit Points.", "pages": [115]},
        {"id": "benefit_from_invisible", "description": "The creature can't benefit from the Invisible condition.", "pages": [165]}],
}

if __name__ == "__main__":
    write_all(entries(), REGISTRY, LOT)
