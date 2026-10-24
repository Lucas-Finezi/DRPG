#!/usr/bin/env python3
"""L18 — Level 1 spells (57).

Usage: python3 -I tools/build/l18_level1.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spelllib import (DC, EACH_END, INHERIT, SELF, SLOT, SP, SPELL, above, area, attack, cond, creatures, dmg,  # noqa: E402
                      heal, light, md, ref, save, touch, until_turn, up, updice, write_all, C)

LOT = "L18"
HL = "***Using a Higher-Level Spell Slot.***"
MOD = {"var": "spellcasting_mod"}
STUDY = {"op": "check", "ability": "int", "skill": "investigation", "dc": DC,
         "note": "A creature that takes the Study action; on a success it discerns the illusion."}
ACTIVE = lambda slug: {"pred": "effect_active", "args": {"effect": slug}}  # noqa: E731
BLOCKED = {"id": "blocked_by", "blocked_by": ["1_foot_stone_dirt_or_wood", "1_inch_metal", "thin_sheet_of_lead"]}
EXTRA = lambda n=1: up(n, 1)  # noqa: E731  one additional target per slot level above 1


def S(name, items, **kw):
    return SPELL(name, items, LOT, **kw)


def entries():
    E = []
    E.append(S("Alarm", [
        ("^", "rule", {"id": "ward", "area": "door_window_or_area_up_to_20_foot_cube", "trigger": "creature_touches_or_enters",
                       "exempt": "creatures_designated_at_casting", "choose": ["audible", "mental"]}),
        ("**Audible Alarm.**", "rule", {"id": "audible", "sound": "handbell", "seconds": 10, "audible_within_feet": 60}),
        ("**Mental Alarm.**", "rule", {"id": "mental", "ping_within_miles": 1, "wakes_you": True})]))
    E.append(S("Animal Friendship", [
        ("^", "fx", save("wis", cond("charmed"), target=creatures(EXTRA(), must_see=True, creature_types=["beast"]))),
        ("^", "rule", {"id": "ends", "ends_on": "you_or_ally_damages_target"}),
        (HL, "sys", ["/effects/0/target/count"])]))
    E.append(S("Bane", [
        ("^", "fx", save("cha", {"op": "modifier", "stat": "d20_test", "mode": "add", "value": {"op": "neg", "args": ["1d4"]},
                                 "when": {"any": [{"pred": "roll_is", "args": {"roll": "attack_roll"}},
                                                  {"pred": "roll_is", "args": {"roll": "saving_throw"}}]},
                                 "duration": "@duration"},
                         target=creatures(up(3, 1), must_see=True))),
        (HL, "sys", ["/effects/0/target/count"])]))
    E.append(S("Bless", [
        ("^", "fx", {"op": "modifier", "stat": "d20_test", "mode": "add", "value": "1d4", "target": creatures(up(3, 1)),
                     "when": {"any": [{"pred": "roll_is", "args": {"roll": "attack_roll"}},
                                      {"pred": "roll_is", "args": {"roll": "saving_throw"}}]},
                     "duration": "@duration"}),
        (HL, "sys", ["/effects/0/target/count"])]))
    E.append(S("Burning Hands", [
        ("^", "fx", save("dex", dmg(updice(3, 6, 1), "fire"), half=True, target=area("cone", 15, "self"))),
        ("Flammable objects in the Cone", "ref", ["dnd5e/hazard/burning"]),
        ("Flammable objects in the Cone", "rule", {"id": "ignite", "objects_in_area": True, "not_worn_or_carried": True}),
        (HL, "sys", ["/effects/0/on_fail/0/amount"])]))
    E.append(S("Charm Person", [
        ("^", "fx", save("wis", [cond("charmed")],
                         target=creatures(EXTRA(), must_see=True, creature_types=["humanoid"]))),
        ("^", "rule", {"id": "details", "save_advantage_if_fighting": True, "ends_on": "you_or_allies_damage_it",
                       "attitude": "dnd5e/attitude/friendly", "knows_afterwards": True}),
        (HL, "sys", ["/effects/0/target/count"])]))
    E.append(S("Chromatic Orb", [
        ("^", "fx", attack("ranged_spell", dmg(updice(3, 8, 1), ["acid", "cold", "fire", "lightning", "poison", "thunder"]),
                           target=creatures())),
        ("If you roll the same number", "rule", {"id": "leap", "on": "two_or_more_d8_same_number", "new_target_within_feet": 30,
                                                  "new_attack_and_damage_roll": True,
                                                  "max_leaps": {"op": "sub", "args": [SLOT, 1]}}),
        (HL, "sys", ["/effects/0/on_hit/0/amount", "rule:leap"]),
        (HL, "rule", {"id": "leap_limits", "max_leaps": SLOT, "each_creature_targeted_once": True})]))
    E.append(S("Color Spray", [("^", "fx", save("con", cond("blinded", until_turn("turn_end", "source")),
                                                target=area("cone", 15, "self")))]))
    E.append(S("Command", [
        ("^", "fx", save("wis", {"op": "choice", "id": "command", "choose": 1, "options": [
            {"id": "approach", "label": "Approach", "effects": [{"op": "move", "mode": "move", "note": "Toward you by the shortest route; ends its turn within 5 feet of you."}]},
            {"id": "drop", "label": "Drop", "effects": [{"op": "restrict", "restrictions": ["hold_items"], "note": "Drops what it holds, then ends its turn."}]},
            {"id": "flee", "label": "Flee", "effects": [{"op": "move", "mode": "move", "note": "Away from you by the fastest means for its turn."}]},
            {"id": "grovel", "label": "Grovel", "effects": [cond("prone", None, note="Then it ends its turn.")]},
            {"id": "halt", "label": "Halt", "effects": [{"op": "restrict", "restrictions": ["move", "take_actions", "take_bonus_actions"],
                                                        "duration": until_turn("turn_end", "target")}]}]},
                         target=creatures(EXTRA(), must_see=True))),
        ("**Approach.**", "sys", ["/effects/0/on_fail/0/options/0"]),
        ("**Drop.**", "sys", ["/effects/0/on_fail/0/options/1"]),
        ("**Flee.**", "sys", ["/effects/0/on_fail/0/options/2"]),
        ("**Grovel.**", "sys", ["/effects/0/on_fail/0/options/3"]),
        ("**Halt.**", "sys", ["/effects/0/on_fail/0/options/4"]),
        (HL, "sys", ["/effects/0/target/count"])]))
    E.append(S("Comprehend Languages", [("^", "rule", {
        "id": "comprehend", "understand": ["spoken", "signed", "written_while_touching_surface"],
        "minutes_per_page": 1, "decodes_symbols_or_secret_messages": False})]))
    E.append(S("Create or Destroy Water", [
        ("^", "rule", {"id": "choose", "options": ["create_water", "destroy_water"]}),
        ("**Create Water.**", "rule", {"id": "create", "gallons": up(10, 1, 10), "or_rain_cube_feet": up(30, 1, 5),
                                      "rain_extinguishes_exposed_flames": True}),
        ("**Destroy Water.**", "rule", {"id": "destroy", "gallons": up(10, 1, 10), "or_fog_cube_feet": up(30, 1, 5)}),
        (HL, "sys", ["rule:create", "rule:destroy"])]))
    E.append(S("Cure Wounds", [
        ("^", "fx", heal({"op": "add", "args": [updice(2, 8, 1, 2), MOD]}, target=touch())),
        (HL, "sys", ["/effects/0/amount"])]))
    E.append(S("Detect Evil and Good", [
        ("^", "fx", {"op": "sense", "sense": "detect_creature_types", "range_feet": 30, "duration": "@duration",
                     "note": "Location of Aberrations, Celestials, Elementals, Fey, Fiends and Undead; whether Hallow is active and where."}),
        ("The spell is blocked", "rule", BLOCKED)]))
    E.append(S("Detect Magic", [
        ("^", "fx", {"op": "sense", "sense": "detect_magic", "range_feet": 30, "duration": "@duration"}),
        ("^", "fx", {"op": "activation", "cost": "action", "action": "dnd5e/action/magic",
                     "then": [ref(SP("detect-magic"), note="See a faint aura around visible magical creatures or objects in the area; learn the school of a spell's effect.")]}),
        ("The spell is blocked", "rule", BLOCKED)]))
    E.append(S("Detect Poison and Disease", [
        ("^", "fx", {"op": "sense", "sense": "detect_poison_and_disease", "range_feet": 30, "duration": "@duration"}),
        ("The spell is blocked", "rule", BLOCKED)]))
    E.append(S("Disguise Self", [
        ("^", "rule", {"id": "disguise", "includes_belongings": True, "height_change_feet": 1, "weight": "heavier_or_lighter",
                       "same_limb_arrangement": True}),
        ("^", "md", md("disguise_extent", "What does the disguise look like, within the spell's limits?",
                       "Otherwise, the extent of the illusion is up to you.", reason="player_choice_open")),
        ("The changes wrought by this spell", "rule", {"id": "physical_inspection", "fails_physical_inspection": True}),
        ("To discern that you are disguised", "fx", STUDY)]))
    E.append(S("Dissonant Whispers", [
        ("^", "fx", save("wis", [dmg(updice(3, 6, 1), "psychic"),
                                 {"op": "move", "mode": "move", "note": "Must use its Reaction, if available, to move as far from you as it can by the safest route."}],
                         half=True, target=creatures(must_see=True))),
        (HL, "sys", ["/effects/0/on_fail/0/amount"])]))
    E.append(S("Divine Favor", [("^", "fx", {
        "op": "trigger", "event": {"event": "hits_with_attack_roll"}, "condition": {"pred": "attack_uses_weapon"},
        "duration": "@duration", "then": [dmg("1d4", "radiant", target=INHERIT)]})]))
    E.append(S("Divine Smite", [
        ("^", "fx", [dmg(updice(2, 8, 1), "radiant", target=INHERIT),
                     dmg("1d8", "radiant", target=INHERIT,
                         when={"any": [{"pred": "creature_type", "args": {"type": "fiend"}},
                                       {"pred": "creature_type", "args": {"type": "undead"}}]})]),
        (HL, "sys", ["/effects/0/amount"])]))
    E.append(S("Ensnaring Strike", [
        ("^", "fx", save("str", cond("restrained"), target=INHERIT,
                         on_success={"op": "end_effect", "scope": "this_entry"},
                         note="A Large or larger creature has Advantage on this save.")),
        ("While Restrained", "fx", [
            {"op": "trigger", "event": {"event": "turn_start", "whose": "target", "which": "each"},
             "condition": {"pred": "has_condition", "args": {"condition": "restrained"}},
             "then": [dmg(updice(1, 6, 1), "piercing", target=INHERIT)]},
            {"op": "activation", "cost": "action", "note": "The target or a creature within its reach.",
             "then": [{"op": "check", "ability": "str", "skill": "athletics", "dc": DC,
                       "on_success": [{"op": "end_effect", "scope": "this_entry"}]}]}]),
        (HL, "sys", ["/effects/1/then/0/amount"])]))
    E.append(S("Entangle", [
        ("^", "rule", {"id": "terrain", "area_square_feet": 20, "difficult_terrain": True, "rule": "dnd5e/rule/difficult-terrain"}),
        ("Each creature (other than you)", "fx", [
            save("str", cond("restrained"), target=area("cube", 20)),
            {"op": "activation", "cost": "action", "note": "A Restrained creature, to free itself.",
             "then": [{"op": "check", "ability": "str", "skill": "athletics", "dc": DC,
                       "on_success": [{"op": "remove_condition", "conditions": [C("restrained")]}]}]}])]))
    E.append(S("Expeditious Retreat", [("^", "fx", [
        ref("dnd5e/action/dash"),
        {"op": "activation", "cost": "bonus_action", "duration": "@duration", "then": [ref("dnd5e/action/dash")]}])]))
    E.append(S("Faerie Fire", [
        ("^", "fx", save("dex", [{"op": "restrict", "restrictions": ["benefit_from_invisible"], "duration": "@duration"},
                                 {"op": "roll_mode", "mode": "advantage", "rolls": ["attack_roll"], "direction": "against",
                                  "when": {"pred": "attacker_can_see_target"}, "duration": "@duration"}],
                         target=area("cube", 20))),
        ("^", "rule", {"id": "outline", "objects_in_cube_outlined": True, "color_choice": ["blue", "green", "violet"],
                       "light": light(dim=10)}),
        ("Attack rolls against an affected creature", "sys", ["/effects/0/on_fail/1"])]))
    E.append(S("False Life", [
        ("^", "fx", {"op": "temp_hp", "amount": {"op": "add", "args": ["2d4", 4, above(1, 5)]}, "target": SELF}),
        (HL, "sys", ["/effects/0/amount"])]))
    E.append(S("Feather Fall", [("^", "fx", {
        "op": "modifier", "stat": "fall_rate_feet_per_round", "mode": "min", "value": 60, "duration": "@duration",
        "target": creatures(5),
        "note": "Falling creatures; a creature that lands takes no falling damage and the spell ends for it."})]))
    fam = ["bat", "cat", "frog", "hawk", "lizard", "octopus", "owl", "rat", "raven", "spider", "weasel"]
    E.append(S("Find Familiar", [
        ("^", "fx", {"op": "choice", "id": "familiar_form", "choose": 1, "options": [
            {"id": f, "label": f.title(), "effects": [{"op": "summon", "creature": f"dnd5e/creature/{f}",
                                                       "controller": "summoner", "initiative": "own"}]} for f in fam],
            "note": "Or another Beast with a Challenge Rating of 0; its creature type is Celestial, Fey or Fiend (your choice)."}),
        ("^", "rule", {"id": "forms", "or": "beast_cr_0",
                       "creature_type_choice": ["celestial", "fey", "fiend"], "acts_independently_obeys": True}),
        ("***Telepathic Connection.***", "rule", {"id": "telepathy", "range_feet": 100,
                                                 "bonus_action_share_senses_until": "start_of_next_turn"}),
        ("Finally, when you cast a spell with a range of touch", "rule", {
            "id": "deliver_touch", "within_feet": 100, "familiar_uses_reaction": True}),
        ("***Combat.***", "rule", {"id": "combat", "ally": True, "own_initiative": True, "can_attack": False}),
        ("***Disappearance of the Familiar.***", "rule", {
            "id": "disappearance", "at_0_hp": "disappears_until_recast", "dismiss": "dnd5e/action/magic",
            "recall_within_feet": 30, "leaves_gear_behind": True}),
        ("***One Familiar Only.***", "rule", {"id": "one_only", "recast_changes_form": True})]))
    E.append(S("Floating Disk", [
        ("^", "rule", {"id": "disk", "diameter_feet": 3, "thickness_inches": 1, "hover_feet": 3, "capacity_lb": 500,
                       "overload": "spell_ends_contents_fall"}),
        ("The disk is immobile", "rule", {"id": "movement", "follows_within_feet": 20, "max_elevation_change_feet": 10}),
        ("If you move more than 100 feet", "rule", {"id": "ends", "ends_if_farther_than_feet": 100})]))
    E.append(S("Fog Cloud", [
        ("^", "rule", {"id": "fog", "shape": "sphere", "radius_feet": up(20, 1, 20), "heavily_obscured": True,
                       "rule": "dnd5e/rule/heavily-obscured", "dispersed_by": "strong_wind",
                       "example": SP("gust-of-wind")}),
        (HL, "sys", ["rule:fog"])]))
    E.append(S("Goodberry", [
        ("^", "rule", {"id": "berries", "count": 10}),
        ("^", "fx", {"op": "activation", "cost": "bonus_action", "note": "Any creature eats one berry.",
                     "then": [heal(1), ref("dnd5e/hazard/malnutrition", note="Nourishment for one day.")]}),
        ("Uneaten berries disappear", "rule", {"id": "disappear", "on": "spell_ends"})]))
    E.append(S("Grease", [
        ("^", "rule", {"id": "grease", "area_square_feet": 10, "difficult_terrain": True, "nonflammable": True}),
        ("When the grease appears", "fx", [
            save("dex", cond("prone", None), target=area("cube", 10)),
            {"op": "trigger", "event": {"event": "enters_or_ends_turn_in_area"},
             "then": [save("dex", cond("prone", None), target=INHERIT)]}])]))
    E.append(S("Guiding Bolt", [
        ("^", "fx", attack("ranged_spell", [dmg(updice(4, 6, 1), "radiant"),
                                            {"op": "roll_mode", "mode": "advantage", "rolls": ["attack_roll"],
                                             "direction": "against",
                                             "duration": {**until_turn("turn_end", "source"),
                                                          "ends_on": [{"event": "targeted_by_attack_roll", "whose": "target"}]},
                                             "note": "Only the next attack roll against it."}], target=creatures())),
        (HL, "sys", ["/effects/0/on_hit/0/amount"])]))
    E.append(S("Healing Word", [
        ("^", "fx", heal({"op": "add", "args": [updice(2, 4, 1, 2), MOD]}, target=creatures(must_see=True))),
        (HL, "sys", ["/effects/0/amount"])]))
    E.append(S("Hellish Rebuke", [
        ("^", "fx", save("dex", dmg(updice(2, 10, 1), "fire"), half=True,
                         target={"kind": "creature"}, note="The creature that damaged you.")),
        (HL, "sys", ["/effects/0/on_fail/0/amount"])]))
    E.append(S("Heroism", [
        ("^", "fx", [{"op": "defense", "kind": "immunity", "conditions": [C("frightened")], "target": touch(willing=True),
                      "duration": "@duration"},
                     {"op": "trigger", "event": {"event": "turn_start", "whose": "target", "which": "each"},
                      "duration": "@duration", "then": [{"op": "temp_hp", "amount": MOD}]}]),
        (HL, "rule", {"id": "targets", "count": EXTRA()})]))
    E.append(S("Hex", [
        ("^", "fx", [{"op": "trigger", "event": {"event": "hits_with_attack_roll"}, "duration": "@duration",
                      "condition": {"pred": "target_is_marked"},
                      "then": [dmg("1d6", "necrotic", target=INHERIT)]},
                     {"op": "roll_mode", "mode": "disadvantage", "rolls": ["ability_check"], "target": creatures(must_see=True),
                      "when": {"pred": "check_uses_ability", "args": {"ability": "chosen.ability"}}, "duration": "@duration"}]),
        ("If the target drops to 0 Hit Points", "fx", {
            "op": "activation", "cost": "bonus_action", "requires": {"pred": "marked_target_at_0_hp"},
            "then": [ref(SP("hex"), note="Curse a new creature, on a later turn.")]}),
        (HL, "rule", {"id": "longer_concentration", "max_duration_hours": {"scale": {"by": "spell_slot_level", "steps": [
            {"from": 1, "value": 1}, {"from": 2, "value": 4}, {"from": 3, "value": 8}, {"from": 5, "value": 24}]}}})]))
    E.append(S("Hideous Laughter", [
        ("^", "fx", save("wis", [cond("prone"), cond("incapacitated"),
                                 {"op": "restrict", "restrictions": ["end_prone_on_self"], "duration": "@duration"}],
                         target=creatures(EXTRA(), must_see=True),
                         repeat={"on": {"event": "turn_end", "whose": "target", "which": "each"}, "ends": "effect_on_self"})),
        ("At the end of each of its turns", "fx", {
            "op": "trigger", "event": {"event": "damage_taken"}, "condition": ACTIVE("hideous-laughter"),
            "then": [save("wis", None, target=INHERIT, on_success={"op": "end_effect", "scope": "this_entry_on_target"},
                          note="With Advantage, since the save is triggered by damage.")]}),
        (HL, "sys", ["/effects/0/target/count"])]))
    E.append(S("Hunter’s Mark", [
        ("^", "fx", [{"op": "trigger", "event": {"event": "hits_with_attack_roll"}, "duration": "@duration",
                      "condition": {"pred": "target_is_marked"}, "then": [dmg("1d6", "force", target=INHERIT)]},
                     {"op": "roll_mode", "mode": "advantage", "rolls": ["ability_check.wis"], "duration": "@duration",
                      "when": {"all": [{"pred": "check_to_find_marked_target"},
                                       {"any": [{"pred": "check_uses_skill", "args": {"skill": "perception"}},
                                                {"pred": "check_uses_skill", "args": {"skill": "survival"}}]}]}}]),
        ("If the target drops to 0 Hit Points", "fx", {
            "op": "activation", "cost": "bonus_action", "requires": {"pred": "marked_target_at_0_hp"},
            "then": [ref(SP("hunters-mark"), note="Move the mark to a new creature you can see within range.")]}),
        (HL, "rule", {"id": "longer_concentration", "max_duration_hours": {"scale": {"by": "spell_slot_level", "steps": [
            {"from": 1, "value": 1}, {"from": 3, "value": 8}, {"from": 5, "value": 24}]}}})]))
    E.append(S("Ice Knife", [
        ("^", "fx", [attack("ranged_spell", dmg("1d10", "piercing"), target=creatures()),
                     save("dex", dmg(updice(2, 6, 1), "cold"), note="Hit or miss: the target and each creature within 5 feet of it.",
                          target={"kind": "area", "area": {"shape": "emanation", "size_feet": 5, "origin": "target"}})]),
        (HL, "sys", ["/effects/1/on_fail/0/amount"])]))
    E.append(S("Identify", [
        ("^", "rule", {"id": "object", "touch_throughout_casting": True,
                       "learns": ["properties_and_use", "attunement_required", "charges", "ongoing_spells", "creating_spell"]}),
        ("If you instead touch a creature", "rule", {"id": "creature", "learns": ["ongoing_spells_affecting_it"]})]))
    E.append(S("Illusory Script", [
        ("^", "rule", {"id": "script", "readers": ["you", "designated_creatures"], "others_see": "unintelligible_script",
                       "alternative": "alter_meaning_handwriting_language", "language_must_be_known": True}),
        ("If the spell is dispelled", "rule", {"id": "dispelled", "both_disappear": True}),
        ("A creature that has Truesight", "rule", {"id": "truesight", "can_read_hidden_message": True})]))
    E.append(S("Inflict Wounds", [
        ("^", "fx", save("con", dmg(updice(2, 10, 1), "necrotic"), half=True, target=touch())),
        (HL, "sys", ["/effects/0/on_fail/0/amount"])]))
    E.append(S("Jump", [
        ("^", "fx", {"op": "activation", "cost": "none", "movement_cost": 10, "frequency": {"count": 1, "per": "turn"},
                     "target": touch(willing=True), "duration": "@duration",
                     "then": [{"op": "move", "mode": "jump", "distance_feet": 30}]}),
        (HL, "rule", {"id": "targets", "count": EXTRA()})]))
    E.append(S("Longstrider", [
        ("^", "fx", {"op": "speed", "movement": "walk", "mode": "add", "value": 10, "target": touch(),
                     "duration": "@duration"}),
        (HL, "rule", {"id": "targets", "count": EXTRA()})]))
    E.append(S("Mage Armor", [("^", "fx", {
        "op": "modifier", "stat": "base_ac", "mode": "set", "value": {"op": "add", "args": [13, {"var": "ability_mod.dex"}]},
        "target": touch(willing=True), "duration": {"kind": "hours", "amount": 8, "ends_on": [{"event": "dons_armor"}]},
        "when": {"not": {"pred": "wearing_armor_any"}}})]))
    E.append(S("Magic Missile", [
        ("^", "fx", {"op": "repeat", "times": up(3, 1), "then": [
            dmg({"op": "add", "args": ["1d4", 1]}, "force", target=creatures(must_see=True))],
            "note": "Darts strike simultaneously; one creature or several."}),
        (HL, "sys", ["/effects/0/times"])]))
    planar = ["aberration", "celestial", "elemental", "fey", "fiend", "undead"]
    E.append(S("Protection from Evil and Good", [("^", "fx", [
        {"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll"], "direction": "against", "target": touch(willing=True),
         "when": {"pred": "attacker_creature_type_in", "args": {"types": planar}}, "duration": "@duration"},
        {"op": "defense", "kind": "immunity", "conditions": [C("charmed"), C("frightened")], "duration": "@duration",
         "when": {"pred": "source_creature_type_in", "args": {"types": planar}}, "note": "Also can't be possessed by them."},
        {"op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw"], "duration": "@duration",
         "when": {"pred": "save_against_effect_of_types", "args": {"types": planar}},
         "note": "New saves against possession, Charmed or Frightened already caused by such a creature."}])]))
    E.append(S("Purify Food and Drink", [("^", "rule", {
        "id": "purify", "removes": ["poison", "rot"], "from": "nonmagical_food_and_drink", "area": {"shape": "sphere", "radius_feet": 5}})]))
    E.append(S("Ray of Sickness", [
        ("^", "fx", attack("ranged_spell", [dmg(updice(2, 8, 1), "poison"), cond("poisoned", until_turn("turn_end", "source"))],
                           target=creatures())),
        (HL, "sys", ["/effects/0/on_hit/0/amount"])]))
    E.append(S("Sanctuary", [("^", "fx", {
        "op": "trigger", "event": {"event": "targeted_by_attack_or_damaging_spell"}, "target": creatures(),
        "duration": {"kind": "minutes", "amount": 1, "ends_on": [{"event": "warded_creature_attacks_casts_or_damages"}]},
        "then": [save("wis", {"op": "restrict", "restrictions": ["target_warded_creature"],
                              "note": "Choose a new target or lose the attack or spell."},
                      target=INHERIT)],
        "note": "No protection from areas of effect."})]))
    E.append(S("Searing Smite", [
        ("^", "fx", [dmg(updice(1, 6, 1), "fire", target=INHERIT),
                     {"op": "trigger", "event": {"event": "turn_start", "whose": "target", "which": "each"},
                      "duration": "@duration", "then": [
                          dmg(updice(1, 6, 1), "fire", target=INHERIT),
                          save("con", None, target=INHERIT, on_success={"op": "end_effect", "scope": "this_entry"})]}]),
        (HL, "sys", ["/effects/0/amount", "/effects/1/then/0/amount"])]))
    E.append(S("Shield", [("^", "fx", [
        {"op": "modifier", "stat": "ac", "mode": "add", "value": 5, "target": SELF,
         "duration": until_turn("turn_start", "self"), "note": "Including against the triggering attack."},
        {"op": "defense", "kind": "immunity", "damage_types": ["force"], "when": {"pred": "damage_from_spell", "args": {"spell": "magic-missile"}},
         "duration": until_turn("turn_start", "self"), "note": "No damage from Magic Missile."}])],
        ))
    E.append(S("Shield of Faith", [("^", "fx", {"op": "modifier", "stat": "ac", "mode": "add", "value": 2,
                                                "target": creatures(), "duration": "@duration"})]))
    E.append(S("Silent Image", [
        ("^", "rule", {"id": "image", "max_cube_feet": 15, "visual_only": True}),
        ("As a Magic action", "fx", {"op": "activation", "cost": "action", "action": "dnd5e/action/magic",
                                     "then": [{"op": "move", "mode": "move", "note": "The image, to any spot within range; its appearance can change to look natural."}]}),
        ("Physical interaction with the image", "rule", {"id": "physical_interaction", "reveals_illusion": True}),
        ("Physical interaction with the image", "fx", STUDY),
        ("Physical interaction with the image", "ref", ["dnd5e/rule/illusions"])]))
    WAKE = {"event": "damage_taken", "whose": "target"}  # the spell ends on a target that takes damage
    E.append(S("Sleep", [
        ("^", "fx", save("wis", [
            cond("incapacitated", {**until_turn("turn_end", "target"), "ends_on": [WAKE]}),
            {"op": "trigger", "event": {"event": "turn_end", "whose": "target", "which": "next"}, "target": INHERIT,
             "duration": {**until_turn("turn_end", "target"), "ends_on": [WAKE]},
             "then": [save("wis", cond("unconscious", {"kind": "minutes", "amount": 1, "concentration": True, "up_to": True,
                                                       "ends_on": [WAKE]}), target=INHERIT)],
             "note": "Repeated at the end of its next turn."}],
            target=area("sphere", 5))),
        ("^", "rule", {"id": "wake", "ends_on": ["takes_damage", "shaken_awake_by_action_within_5_feet"]}),
        ("Creatures that don’t sleep", "fx", {"op": "auto_result", "rolls": ["saving_throw"], "result": "success",
                                              "when": {"any": [{"pred": "doesnt_sleep"},
                                                               {"pred": "immune_to_condition", "args": {"condition": "exhaustion"}}]}})]))
    E.append(S("Speak with Animals", [
        ("^", "rule", {"id": "speak", "creature_types": ["beast"], "influence_skill_options": True,
                       "action": "dnd5e/action/influence"}),
        ("Most Beasts have little to say", "md", md("beast_knowledge", "What does the Beast know and say?",
                                                    "Most Beasts have little to say about topics that don’t pertain to survival or companionship, but at minimum, a Beast can give you information about nearby locations and monsters, including whatever it has perceived within the past day.",
                                                    reason="narrative"))]))
    E.append(S("Thunderwave", [
        ("^", "fx", save("con", [dmg(updice(2, 8, 1), "thunder"), {"op": "move", "mode": "push", "distance_feet": 10}],
                         half=True, target=area("cube", 15, "self"))),
        ("In addition, unsecured objects", "rule", {"id": "objects", "unsecured_objects_pushed_feet": 10,
                                                    "boom_audible_feet": 300}),
        (HL, "sys", ["/effects/0/on_fail/0/amount"])]))
    E.append(S("Unseen Servant", [
        ("^", "rule", {"id": "servant", "invisible": True, "size": "medium", "ac": 10, "hp": 1, "str": 2, "can_attack": False,
                       "ends_at_0_hp": True}),
        ("Once on each of your turns", "fx", {"op": "activation", "cost": "bonus_action", "frequency": {"count": 1, "per": "turn"},
                                               "then": [{"op": "move", "mode": "move", "distance_feet": 15,
                                                         "note": "The servant moves and interacts with an object; it performs simple tasks until done."}]}),
        ("If you command the servant", "rule", {"id": "range", "ends_if_task_takes_it_beyond_feet": 60})]))
    return E


REGISTRY = {
    "stats": [{"id": "fall_rate_feet_per_round", "description": "Rate of descent of a falling creature, in feet per round.", "pages": [130]}],
    "senses": [
        {"id": "detect_creature_types", "description": "Sense the location of creatures of certain types within range.", "pages": [124]},
        {"id": "detect_magic", "description": "Sense the presence of magical effects within range.", "pages": [124]},
        {"id": "detect_poison_and_disease", "description": "Sense poisons, poisonous or venomous creatures, and magical contagions within range.", "pages": [124]}],
    "restrictions": [
        {"id": "move", "description": "The creature can't move.", "pages": [117]},
        {"id": "end_prone_on_self", "description": "The creature can't end the Prone condition on itself.", "pages": [140]},
        {"id": "target_warded_creature", "description": "The creature can't target the warded creature with this attack or spell.", "pages": [161]}],
    "events": [
        {"id": "sees_creature_casting_spell", "description": "A creature the caster can see within range casts a spell with Verbal, Somatic or Material components.", "pages": [119]},
        {"id": "enters_or_ends_turn_in_area", "description": "A creature enters the area or ends its turn there.", "pages": [138]},
        {"id": "targeted_by_attack_or_damaging_spell", "description": "A creature targets the warded creature with an attack roll or a damaging spell.", "pages": [161]},
        {"id": "warded_creature_attacks_casts_or_damages", "description": "The warded creature makes an attack roll, casts a spell, or deals damage.", "pages": [161]},
        {"id": "dons_armor", "description": "The creature dons armor.", "pages": [146]}],
    "predicates": [
        {"id": "attacker_can_see_target", "description": "The attacker can see the target.", "type": "predicate", "pages": [129]},
        {"id": "target_is_marked", "description": "The target is the creature marked by this spell.", "type": "predicate", "pages": [140]},
        {"id": "marked_target_at_0_hp", "description": "The creature marked by this spell has dropped to 0 Hit Points.", "type": "predicate", "pages": [140]},
        {"id": "check_uses_ability", "description": "The ability check uses this ability (param).", "params": ["ability"], "type": "predicate", "pages": [140]},
        {"id": "check_to_find_marked_target", "description": "The check is made to find the marked creature.", "type": "predicate", "pages": [141]},
        {"id": "attacker_creature_type_in", "description": "The attacker's creature type is one of these (param).", "params": ["types"], "type": "predicate", "pages": [156]},
        {"id": "source_creature_type_in", "description": "The effect's source creature is of one of these types (param).", "params": ["types"], "type": "predicate", "pages": [156]},
        {"id": "save_against_effect_of_types", "description": "The save is against possession, Charmed or Frightened caused by a creature of these types (param).", "params": ["types"], "type": "predicate", "pages": [156]},
        {"id": "damage_from_spell", "description": "The damage comes from this spell (param).", "params": ["spell"], "type": "predicate", "pages": [162]},
        {"id": "doesnt_sleep", "description": "The creature doesn't sleep.", "type": "predicate", "pages": [163]},
        {"id": "immune_to_condition", "description": "The creature has Immunity to this condition (param).", "params": ["condition"], "type": "predicate", "pages": [163]}],
}

if __name__ == "__main__":
    write_all(entries(), REGISTRY, LOT)
