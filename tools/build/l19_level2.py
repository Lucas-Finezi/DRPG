#!/usr/bin/env python3
"""L19 — Level 2 spells (57) and the Otherworldly Steed stat block (Find Steed).

Usage: python3 -I tools/build/l19_level2.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spelllib import (DC, EACH_END, INHERIT, SELF, SLOT, SP, SPELL, above, area, attack, cond, creatures, dmg,  # noqa: E402
                      heal, light, md, ref, save, touch, until_turn, up, updice, write_all, C)
from statblock import creature_entry  # noqa: E402

LOT = "L19"
HL = "***Using a Higher-Level Spell Slot.***"
MOD = {"var": "spellcasting_mod"}
EXTRA = lambda n=1: up(n, 2)  # noqa: E731
ACTIVE = lambda slug: {"pred": "effect_active", "args": {"effect": slug}}  # noqa: E731
STUDY = {"op": "check", "ability": "int", "skill": "investigation", "dc": DC}
BLOCKED = {"id": "blocked_by", "blocked_by": ["1_foot_stone_dirt_or_wood", "1_inch_metal", "thin_sheet_of_lead"]}
MAGIC = {"cost": "action", "action": "dnd5e/action/magic"}
ALL_BUT = lambda *ex: [t for t in ("acid", "bludgeoning", "cold", "fire", "force", "lightning", "necrotic",  # noqa: E731
                                   "piercing", "poison", "psychic", "radiant", "slashing", "thunder") if t not in ex]


def S(name, items, **kw):
    return SPELL(name, items, LOT, **kw)


def entries():
    E = []
    E.append(S("Acid Arrow", [
        ("^", "fx", attack("ranged_spell", [dmg(updice(4, 4, 2), "acid"),
                                            {"op": "trigger", "event": {"event": "turn_end", "whose": "target"},
                                             "then": [dmg(updice(2, 4, 2), "acid", target=INHERIT)]}],
                           target=creatures(),
                           on_miss=[dmg({"op": "div", "args": [updice(4, 4, 2), 2]}, "acid",
                                        note="Half the initial damage only.")])),
        (HL, "sys", ["/effects/0/on_hit/0/amount", "/effects/0/on_hit/1/then/0/amount", "/effects/0/on_miss/0/amount"])]))
    E.append(S("Aid", [
        ("^", "fx", [{"op": "modifier", "stat": "hp_max", "mode": "add", "value": up(5, 2, 5), "target": creatures(3),
                      "duration": "@duration"},
                     heal(up(5, 2, 5), target=creatures(3), note="Current Hit Points increase by the same amount.")]),
        (HL, "sys", ["/effects/0/value", "/effects/1/amount"])]))
    E.append(S("Alter Self", [
        ("^", "fx", {"op": "choice", "id": "alter_self", "choose": 1, "options": [
            {"id": "aquatic_adaptation", "label": "Aquatic Adaptation", "effects": [
                {"op": "modifier", "stat": "breathe_underwater", "mode": "set", "value": 1, "duration": "@duration"},
                {"op": "speed", "movement": "swim", "mode": "equal_to_walk", "value": 0, "duration": "@duration"}]},
            {"id": "change_appearance", "label": "Change Appearance", "effects": [
                {"op": "master_decision", "decision": "appearance"}]},
            {"id": "natural_weapons", "label": "Natural Weapons", "effects": [
                {"op": "modifier", "stat": "weapon_damage_die", "mode": "set", "value": "1d6",
                 "when": {"pred": "attack_is_unarmed_strike"}, "duration": "@duration",
                 "note": "Claws (Slashing), fangs or horns (Piercing), hooves (Bludgeoning)."},
                {"op": "modifier", "stat": "attack_ability", "mode": "set", "value": MOD,
                 "when": {"pred": "attack_is_unarmed_strike"}, "duration": "@duration"}]}]}),
        ("^", "fx", {"op": "activation", **MAGIC, "then": [ref(SP("alter-self"), note="Replace the chosen option.")]}),
        ("***Aquatic Adaptation.***", "sys", ["/effects/0/options/0"]),
        ("***Change Appearance.***", "md", md("appearance", "What does the caster look like?",
                                             "You decide what you look like, including your height, weight, facial features, sound of your voice, hair length, coloration, and other distinguishing characteristics.",
                                             reason="player_choice_open")),
        ("***Change Appearance.***", "rule", {"id": "appearance_limits", "statistics_change": False, "same_size": True,
                                             "same_basic_shape": True, "magic_action_to_change_again": True}),
        ("***Natural Weapons.***", "sys", ["/effects/0/options/2"])]))
    E.append(S("Animal Messenger", [
        ("^", "fx", save("cha", ref(SP("animal-messenger"), note="The Beast attempts to deliver the message."),
                         target=creatures(must_see=True, creature_types=["beast"], sizes=["tiny"]),
                         note="A target whose Challenge Rating isn't 0 automatically succeeds.")),
        ("^", "rule", {"id": "message", "location": "visited_by_caster", "recipient": "general_description",
                       "max_words": 25, "miles_per_24_hours": 25, "flying_miles_per_24_hours": 50}),
        ("When the Beast arrives", "rule", {"id": "delivery", "mimics_communication": True,
                                            "late": "message_lost_beast_returns"}),
        (HL, "rule", {"id": "duration", "hours": up(24, 2, 48)})]))
    E.append(S("Arcane Lock", [("^", "rule", {
        "id": "lock", "targets": ["door", "window", "gate", "container", "hatch"], "nonmagical_unlocking": False,
        "exempt": "designated_creatures", "password_unlocks_minutes": 1, "password_range_feet": 5})]))
    E.append(S("Arcanist’s Magic Aura", [
        ("^", "rule", {"id": "aura", "targets": ["willing_creature", "object_not_worn_or_carried"],
                       "permanent_after_daily_casts": 30}),
        ("***Mask (Creature).***", "rule", {"id": "mask", "apparent_creature_type": "chosen", "applies_to": "spells_and_magical_effects"}),
        ("***False Aura (Object).***", "rule", {"id": "false_aura", "options": ["appear_magical", "appear_nonmagical",
                                                                               "apparent_school"], "example": SP("detect-magic")})]))
    E.append(S("Augury", [
        ("^", "md", md("omen", "Which omen does the GM choose from the Omens table?",
                       "The GM chooses the omen from the Omens table.",
                       options=[{"id": "weal", "label": "Weal"}, {"id": "woe", "label": "Woe"},
                                {"id": "weal_and_woe", "label": "Weal and woe"}, {"id": "indifference", "label": "Indifference"}])),
        ("##### Omens", "table", {"id": "omens", "caption": "Omens", "columns": ["Omen", "For Results That Will Be …"],
                                  "rows": [["Weal", "Good"], ["Woe", "Bad"], ["Weal and woe", "Good and bad"],
                                           ["Indifference", "Neither good nor bad"]]}),
        ("The spell doesn’t account for circumstances", "rule", {"id": "limits", "ignores_changing_circumstances": True}),
        ("If you cast the spell more than once", "rule", {"id": "repeat_casting", "no_answer_chance_percent": {
            "op": "mul", "args": [25, {"var": "uses_since_rest.augury"}]}, "reset_on": "long_rest_finished"})]))
    E.append(S("Barkskin", [("^", "fx", {"op": "modifier", "stat": "ac", "mode": "min", "value": 17,
                                         "target": touch(willing=True), "duration": "@duration"})]))
    E.append(S("Blindness/Deafness", [
        ("^", "fx", save("con", {"op": "choice", "id": "condition", "choose": 1, "options": [
            {"id": "blinded", "label": "Blinded", "effects": [cond("blinded")]},
            {"id": "deafened", "label": "Deafened", "effects": [cond("deafened")]}]},
                         target=creatures(EXTRA(), must_see=True), repeat=EACH_END)),
        (HL, "sys", ["/effects/0/target/count"])]))
    E.append(S("Blur", [("^", "fx", {"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll"],
                                     "direction": "against", "duration": "@duration",
                                     "when": {"not": {"pred": "attacker_perceives_with", "args": {"senses": ["blindsight", "truesight"]}}}})]))
    E.append(S("Calm Emotions", [
        ("^", "fx", save("cha", {"op": "choice", "id": "calm", "choose": 1, "chooser": "owner", "options": [
            {"id": "immunity", "label": "Immunity to Charmed and Frightened", "effects": [
                {"op": "defense", "kind": "immunity", "conditions": [C("charmed"), C("frightened")], "duration": "@duration",
                 "note": "Existing Charmed or Frightened conditions are suppressed for the duration."}]},
            {"id": "indifferent", "label": "Indifferent", "effects": [
                ref("dnd5e/attitude/indifferent", note="Toward creatures of your choice it is Hostile toward; ends if it takes damage or witnesses its allies taking damage.")]}]},
            target=area("sphere", 20, creature_types=["humanoid"]))),
        ("- The creature has Immunity", "sys", ["/effects/0/on_fail/0/options/0"]),
        ("- The creature becomes Indifferent", "sys", ["/effects/0/on_fail/0/options/1"])]))
    E.append(S("Continual Flame", [("^", "rule", {"id": "flame", "light": light(20, 20), "heat": False, "fuel": False,
                                                  "can_be_covered": True, "can_be_smothered": False})]))
    E.append(S("Darkness", [
        ("^", "rule", {"id": "darkness", "area": {"shape": "sphere", "radius_feet": 15}, "magical_darkness": True,
                       "darkvision_sees_through": False, "nonmagical_light_illuminates": False, "rule": "dnd5e/rule/darkness"}),
        ("Alternatively, you cast the spell on an object", "rule", {"id": "object", "area": {"shape": "emanation", "size_feet": 15},
                                                                    "opaque_cover_blocks": True}),
        ("If any of this spell’s area overlaps", "rule", {"id": "dispel_light", "dispels_light_spells_of_level_at_most": 2})]))
    E.append(S("Darkvision", [("^", "fx", {"op": "sense", "sense": "darkvision", "range_feet": 150, "target": touch(willing=True),
                                           "duration": "@duration"})]))
    E.append(S("Detect Thoughts", [
        ("^", "rule", {"id": "activation", "choose": ["sense_thoughts", "read_thoughts"],
                       "later_turns_cost": "dnd5e/action/magic"}),
        ("***Sense Thoughts.***", "fx", {"op": "sense", "sense": "sense_thoughts", "range_feet": 30, "duration": "@duration"}),
        ("The spell is blocked", "rule", BLOCKED),
        ("***Read Thoughts.***", "md", md("surface_thoughts", "What is most on the target's mind right now?",
                                         "You learn what is most on the target’s mind right now.", reason="narrative")),
        ("***Read Thoughts.***", "rule", {"id": "read", "range_feet": 30, "requires": "target_knows_language_or_telepathic"}),
        ("As a Magic action on your next turn", "fx", {"op": "activation", **MAGIC, "then": [
            save("wis", ref(SP("detect-thoughts"), note="Discern reasoning, emotions and something that looms large."),
                 on_success={"op": "end_effect", "scope": "this_entry"}, target=INHERIT)]}),
        ("As a Magic action on your next turn", "fx", {"op": "activation", "cost": "action", "note": "The target, while you probe its mind.",
                                                       "then": [{"op": "check", "ability": "int", "skill": "arcana", "dc": DC,
                                                                 "on_success": [{"op": "end_effect", "scope": "this_entry"}]}]})]))
    E.append(S("Dragon’s Breath", [
        ("^", "fx", {"op": "activation", **MAGIC, "target": touch(willing=True), "duration": "@duration",
                     "then": [save("dex", dmg(updice(3, 6, 2), ["acid", "cold", "fire", "lightning", "poison"]), half=True,
                                   target=area("cone", 15, "self"))],
                     "note": "The target takes the Magic action; damage type chosen when casting."}),
        (HL, "sys", ["/effects/0/then/0/on_fail/0/amount"])]))
    E.append(S("Enhance Ability", [
        ("^", "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["ability_check"], "target": touch(),
                     "when": {"pred": "check_uses_ability", "args": {"ability": "chosen.ability"}}, "duration": "@duration",
                     "note": "Strength, Dexterity, Intelligence, Wisdom or Charisma."}),
        (HL, "rule", {"id": "targets", "count": EXTRA(), "different_ability_each": True})]))
    E.append(S("Enlarge/Reduce", [
        ("^", "fx", save("con", None, target={"kind": "creature_or_object", "range": "@range", "must_see": True},
                         note="Only an unwilling creature saves; on a success the spell has no effect.")),
        ("^", "rule", {"id": "targets", "object_not_worn_or_carried": True}),
        ("Everything that a targeted creature", "rule", {"id": "gear", "gear_changes_size": True, "dropped_items_revert": True,
                                                         "thrown_or_ammunition_reverts_after_attack": True}),
        ("***Enlarge.***", "fx", [{"op": "modifier", "stat": "size", "mode": "add", "value": 1, "duration": "@duration"},
                                 {"op": "roll_mode", "mode": "advantage", "rolls": ["ability_check.str", "saving_throw.str"],
                                  "duration": "@duration"},
                                 {"op": "trigger", "event": {"event": "hits_with_attack_roll"}, "duration": "@duration",
                                  "condition": {"any": [{"pred": "attack_uses_weapon"}, {"pred": "attack_is_unarmed_strike"}]},
                                  "then": [dmg("1d4", {"var": "chosen.weapon_damage_type"}, target=INHERIT)]}]),
        ("***Reduce.***", "fx", [{"op": "modifier", "stat": "size", "mode": "add", "value": -1, "duration": "@duration"},
                                {"op": "roll_mode", "mode": "disadvantage", "rolls": ["ability_check.str", "saving_throw.str"],
                                 "duration": "@duration"},
                                {"op": "modifier", "stat": "damage_roll", "mode": "add", "value": {"op": "neg", "args": ["1d4"]},
                                 "duration": "@duration", "note": "Weapons or Unarmed Strikes; damage can't drop below 1.",
                                 "when": {"any": [{"pred": "attack_uses_weapon"}, {"pred": "attack_is_unarmed_strike"}]}}])]))
    E.append(S("Enthrall", [("^", "fx", save("wis", [
        {"op": "modifier", "stat": "ability_check.wis", "mode": "add", "value": -10, "duration": "@duration",
         "when": {"pred": "check_uses_skill", "args": {"skill": "perception"}}},
        {"op": "modifier", "stat": "passive_perception", "mode": "add", "value": -10, "duration": "@duration"}],
        target=creatures(must_see=True), note="A creature you or your companions are fighting automatically succeeds."))]))
    E.append(S("Find Steed", [
        ("^", "fx", {"op": "summon", "creature": "dnd5e/creature/otherworldly-steed", "controller": "summoner",
                     "initiative": "shared", "note": "Replaces a steed already summoned by this spell."}),
        ("The steed resembles", "rule", {"id": "form", "size": "large", "rideable_animal_of_choice": True,
                                         "creature_type_choice": ["celestial", "fey", "fiend"]}),
        ("***Combat.***", "rule", {"id": "combat", "ally": True, "shares_initiative": True, "controlled_mount_when_ridden": True,
                                  "rule": "dnd5e/rule/mounted-combat", "if_you_incapacitated": "acts_independently_after_you"}),
        ("***Disappearance of the Steed.***", "rule", {"id": "disappearance", "on": ["steed_0_hp", "you_die"],
                                                      "leaves_gear": True, "recast_choice": "same_or_different"}),
        (HL, "rule", {"id": "stat_block_level", "spell_level_in_stat_block": SLOT})]))
    E.append(S("Find Traps", [
        ("^", "rule", {"id": "sense_traps", "line_of_sight": True, "trap_definition": "object_or_mechanism_created_to_cause_damage_or_danger",
                       "examples": [SP("alarm"), SP("glyph-of-warding")], "excludes_natural_hazards": True}),
        ("This spell reveals that a trap is present", "rule", {"id": "reveals", "location": False, "general_nature": True})]))
    E.append(S("Flame Blade", [
        ("^", "rule", {"id": "blade", "size_like": "dnd5e/weapon/scimitar", "reevoke": "bonus_action"}),
        ("As a Magic action, you can make", "fx", {"op": "activation", **MAGIC, "then": [
            attack("melee_spell", dmg({"op": "add", "args": [updice(3, 6, 2), MOD]}, "fire"))]}),
        ("The flaming blade sheds", "rule", {"id": "light", "light": light(10, 10)}),
        (HL, "sys", ["/effects/0/then/0/on_hit/0/amount"])]))
    E.append(S("Flaming Sphere", [
        ("^", "fx", {"op": "trigger", "event": {"event": "ends_turn_within_feet_of_effect", "whose": "any"}, "duration": "@duration",
                     "then": [save("dex", dmg(updice(2, 6, 2), "fire"), half=True, target=INHERIT)],
                     "note": "A creature that ends its turn within 5 feet of the sphere."}),
        ("As a Bonus Action, you can move the sphere", "fx", {"op": "activation", "cost": "bonus_action", "then": [
            {"op": "move", "mode": "move", "distance_feet": 30,
             "note": "Rolling along the ground; entering a creature's space forces the save and stops the sphere for the turn."}]}),
        ("When you move the sphere", "rule", {"id": "movement", "over_barriers_feet": 5, "across_pits_feet": 10,
                                              "ignites": "dnd5e/hazard/burning", "light": light(20, 20)}),
        (HL, "sys", ["/effects/0/then/0/on_fail/0/amount"])]))
    E.append(S("Gentle Repose", [
        ("^", "rule", {"id": "protection", "no_decay": True, "cannot_become_undead": True}),
        ("The spell also effectively extends", "rule", {"id": "raise_dead_limit", "days_dont_count": True,
                                                        "example": SP("raise-dead")})]))
    E.append(S("Gust of Wind", [
        ("^", "fx", [save("str", {"op": "move", "mode": "push", "distance_feet": 15}, target=area("line", 60, "self")),
                     {"op": "trigger", "event": {"event": "turn_end", "whose": "any"}, "duration": "@duration",
                      "condition": {"pred": "in_spell_area"}, "then": [save("str", {"op": "move", "mode": "push", "distance_feet": 15}, target=INHERIT)]}]),
        ("^", "rule", {"id": "line", "length_feet": 60, "width_feet": 10}),
        ("Any creature in the Line must spend", "rule", {"id": "headwind", "movement_cost_multiplier": 2, "when": "moving_closer_to_you"}),
        ("The gust disperses gas", "rule", {"id": "flames", "disperses": ["gas", "vapor"], "extinguishes": "unprotected_flames",
                                           "protected_flames_extinguish_chance_percent": 50}),
        ("As a Bonus Action on your later turns", "fx", {"op": "activation", "cost": "bonus_action",
                                                         "then": [ref(SP("gust-of-wind"), note="Change the Line's direction.")]})]))
    E.append(S("Heat Metal", [
        ("^", "fx", [dmg(updice(2, 8, 2), "fire", target={"kind": "creature"},
                         note="Each creature in physical contact with the chosen metal object."),
                     {"op": "activation", "cost": "bonus_action", "duration": "@duration",
                      "then": [dmg(updice(2, 8, 2), "fire")], "note": "Again on later turns, if the object is within range."}]),
        ("If a creature is holding or wearing", "fx", save("con", {"op": "restrict", "restrictions": ["hold_items"],
                                                                   "note": "Drops the object if it can; if it doesn't, Disadvantage on attack rolls and ability checks until the start of your next turn."},
                                                           target=INHERIT)),
        (HL, "sys", ["/effects/0/amount", "/effects/1/then/0/amount"])]))
    E.append(S("Hold Person", [
        ("^", "fx", save("wis", cond("paralyzed"), target=creatures(EXTRA(), must_see=True, creature_types=["humanoid"]),
                         repeat=EACH_END)),
        (HL, "sys", ["/effects/0/target/count"])]))
    E.append(S("Invisibility", [
        ("^", "fx", cond("invisible", {"kind": "hours", "amount": 1, "up_to": True, "concentration": True,
                                       "ends_on": [{"event": "attacks_deals_damage_or_casts"}]}, target=touch())),
        (HL, "rule", {"id": "targets", "count": EXTRA()})]))
    E.append(S("Knock", [
        ("^", "rule", {"id": "target", "objects": ["door", "box", "chest", "manacles", "padlock", "other_access_preventing_object"]}),
        ("A target that is held shut", "rule", {"id": "mundane", "unlocks_one_lock": True, "unsticks": True, "unbars": True}),
        ("If the target is held shut by", "rule", {"id": "arcane_lock", "spell": SP("arcane-lock"), "suppressed_minutes": 10}),
        ("When you cast the spell, a loud knock", "rule", {"id": "knock", "audible_feet": 300})]))
    E.append(S("Lesser Restoration", [("^", "fx", {"op": "remove_condition", "count": 1, "target": touch(),
                                                   "conditions": [C("blinded"), C("deafened"), C("paralyzed"), C("poisoned")]})]))
    E.append(S("Levitate", [
        ("^", "fx", save("con", {"op": "move", "mode": "move", "distance_feet": 20, "note": "Rises vertically and stays suspended."},
                         target={"kind": "creature_or_object", "range": "@range", "must_see": True},
                         note="Only an unwilling creature saves; a loose object can weigh up to 500 pounds.")),
        ("The target can move only by pushing", "rule", {"id": "movement", "moves_as_climbing_against_surfaces": True,
                                                         "altitude_change_feet": 20, "self_as_part_of_move": True,
                                                         "other_target_cost": "dnd5e/action/magic"}),
        ("When the spell ends, the target floats", "rule", {"id": "end", "floats_gently_down": True})]))
    E.append(S("Locate Animals or Plants", [("^", "rule", {"id": "locate", "kinds": ["beast", "plant_creature", "nonmagical_plant"],
                                                           "range_miles": 5, "learns": ["direction", "distance"]})]))
    E.append(S("Locate Object", [
        ("^", "rule", {"id": "locate", "range_feet": 1000, "learns": ["direction", "movement_direction"]}),
        ("The spell can locate a specific object", "rule", {"id": "known", "seen_within_feet": 30, "or": "nearest_of_kind"}),
        ("This spell can’t locate an object if", "rule", {"id": "blocked", "blocked_by": "any_thickness_of_lead"})]))
    E.append(S("Magic Mouth", [
        ("^", "rule", {"id": "message", "max_words": 25, "max_minutes": 10, "object_not_worn_or_carried_by_another": True}),
        ("When that trigger occurs", "rule", {"id": "delivery", "voice": "caster", "ends_after_message_or_repeats": True}),
        ("The trigger can be as general", "md", md("trigger", "Does the stated trigger occur?",
                                                   "The trigger can be as general or as detailed as you like, though it must be based on visual or audible conditions that occur within 30 feet of the object."))]))
    E.append(S("Magic Weapon", [
        ("^", "fx", {"op": "modifier", "stat": "weapon_bonus", "mode": "set", "duration": "@duration",
                     "value": {"scale": {"by": "spell_slot_level", "steps": [{"from": 2, "value": 1}, {"from": 3, "value": 2},
                                                                              {"from": 6, "value": 3}]}},
                     "note": "A nonmagical weapon becomes magic; bonus to attack and damage rolls; ends if cast again."}),
        (HL, "sys", ["/effects/0/value"])]))
    E.append(S("Mind Spike", [
        ("^", "fx", save("wis", [dmg(updice(3, 8, 2), "psychic"),
                                 {"op": "sense", "sense": "know_target_location", "range_feet": 0, "duration": "@duration",
                                  "note": "Same plane only; the target can't hide from you and gains no benefit from Invisible against you."}],
                         half=True, target=creatures(must_see=True))),
        (HL, "sys", ["/effects/0/on_fail/0/amount"])]))
    E.append(S("Mirror Image", [
        ("^", "rule", {"id": "duplicates", "count": 3}),
        ("Each time a creature hits you", "fx", {"op": "trigger", "event": {"event": "hit_by_attack_roll"}, "duration": "@duration",
                                                 "condition": {"not": {"pred": "attacker_perceives_with", "args": {"senses": ["blindsight", "truesight"]}}},
                                                 "then": [ref(SP("mirror-image"), note="Roll a d6 per remaining duplicate; on any 3+, a duplicate is hit and destroyed instead.")]}),
        ("A creature is unaffected", "rule", {"id": "unaffected", "if": ["blinded", "blindsight", "truesight"]})]))
    E.append(S("Misty Step", [("^", "fx", {"op": "move", "mode": "teleport", "distance_feet": 30, "target": SELF,
                                           "note": "To an unoccupied space you can see."})]))
    E.append(S("Moonbeam", [
        ("^", "rule", {"id": "beam", "area": {"shape": "cylinder", "radius_feet": 5, "height_feet": 40}, "light": light(dim=5)}),
        ("^", "fx", {"op": "activation", **MAGIC, "then": [{"op": "move", "mode": "move", "distance_feet": 60, "note": "The Cylinder."}]}),
        ("When the Cylinder appears", "fx", save("con", [dmg(updice(2, 10, 2), "radiant"),
                                                         ref("dnd5e/rule/shape-shifting", note="A shape-shifted creature reverts and can't shape-shift until it leaves the Cylinder.")],
                                                 half=True, target=area("cylinder", 5),
                                                 note="Also when the area moves into its space, when it enters or ends its turn there; once per turn.")),
        (HL, "sys", ["/effects/1/on_fail/0/amount"])]))
    E.append(S("Pass without Trace", [("^", "fx", [
        {"op": "modifier", "stat": "ability_check.dex", "mode": "add", "value": 10, "duration": "@duration",
         "target": area("emanation", 30, "self"), "when": {"pred": "check_uses_skill", "args": {"skill": "stealth"}}},
        {"op": "modifier", "stat": "leaves_tracks", "mode": "set", "value": 0, "duration": "@duration"}])]))
    E.append(S("Phantasmal Force", [
        ("^", "fx", save("int", ref(SP("phantasmal-force"), note="A phantasm no larger than a 10-foot Cube, perceivable only by the target."),
                         target=creatures(must_see=True))),
        ("The target can take a Study action", "fx", {**STUDY, "on_success": [{"op": "end_effect", "scope": "this_entry"}]}),
        ("While affected by the spell", "md", md("rationalize", "How does the target rationalize interactions with the phantasm?",
                                                 "While affected by the spell, the target treats the phantasm as if it were real and rationalizes any illogical outcomes from interacting with it.",
                                                 reason="narrative")),
        ("An affected target can even take damage", "fx", {"op": "trigger", "event": {"event": "turn_start", "whose": "self", "which": "each"},
                                                           "condition": {"pred": "phantasm_is_dangerous"},
                                                           "then": [dmg("2d8", "psychic", target=INHERIT,
                                                                        note="If the target is in the phantasm's area or within 5 feet of it; perceived as a type appropriate to the illusion.")]})]))
    E.append(S("Prayer of Healing", [
        ("^", "fx", [ref("dnd5e/rule/short-rest", target=creatures(5), note="The benefits of a Short Rest."),
                     heal(updice(2, 8, 2, 1), target=creatures(5))]),
        ("^", "rule", {"id": "limit", "once_per": "long_rest_finished", "must_stay_in_range_for_casting": True}),
        (HL, "sys", ["/effects/1/amount"])]))
    E.append(S("Protection from Poison", [("^", "fx", [
        {"op": "remove_condition", "conditions": [C("poisoned")], "target": touch()},
        {"op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw"], "duration": "@duration",
         "when": {"pred": "save_against_condition", "args": {"condition": "poisoned"}}},
        {"op": "defense", "kind": "resistance", "damage_types": ["poison"], "duration": "@duration"}])]))
    E.append(S("Ray of Enfeeblement", [
        ("^", "fx", save("con", None, target=creatures(),
                         on_success={"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll"],
                                     "duration": until_turn("turn_start", "source"), "note": "Next attack roll only."})),
        ("On a failed save", "fx", [
            {"op": "roll_mode", "mode": "disadvantage", "rolls": ["d20_test"], "duration": "@duration",
             "when": {"pred": "roll_uses_ability", "args": {"ability": "str"}}},
            {"op": "modifier", "stat": "damage_roll", "mode": "add", "value": {"op": "neg", "args": ["1d8"]}, "duration": "@duration"},
            save("con", None, target=INHERIT, repeat=EACH_END, note="Repeated at the end of each of its turns; ends the spell on a success.")])]))
    E.append(S("Rope Trick", [
        ("^", "rule", {"id": "portal", "portal_feet": [3, 5], "invisible": True, "extradimensional": True,
                       "access": "climb_rope", "rope_can_be_pulled_in": True}),
        ("The space can hold", "rule", {"id": "space", "capacity": 8, "max_size": "medium",
                                        "effects_pass_portal": False, "see_out": True, "contents_drop_out_on_end": True})]))
    E.append(S("Scorching Ray", [
        ("^", "fx", {"op": "repeat", "times": up(3, 2), "then": [attack("ranged_spell", dmg("2d6", "fire"), target=creatures())],
                     "note": "One target or several; separate attack roll per ray."}),
        (HL, "sys", ["/effects/0/times"])]))
    E.append(S("See Invisibility", [("^", "fx", [
        {"op": "sense", "sense": "see_invisible", "range_feet": 0, "duration": "@duration", "note": "No range limit beyond sight."},
        {"op": "sense", "sense": "see_ethereal", "range_feet": 0, "duration": "@duration"}])]))
    E.append(S("Shatter", [
        ("^", "fx", save("con", dmg(updice(3, 8, 2), "thunder"), half=True, target=area("sphere", 10),
                         note="A Construct has Disadvantage on the save.")),
        ("A nonmagical object", "rule", {"id": "objects", "nonmagical_objects_not_worn_or_carried_take_damage": True}),
        (HL, "sys", ["/effects/0/on_fail/0/amount"])]))
    E.append(S("Shining Smite", [
        ("^", "fx", [dmg(updice(2, 6, 2), "radiant", target=INHERIT),
                     {"op": "roll_mode", "mode": "advantage", "rolls": ["attack_roll"], "direction": "against", "target": INHERIT,
                      "duration": "@duration"},
                     {"op": "restrict", "restrictions": ["benefit_from_invisible"], "target": INHERIT, "duration": "@duration"}]),
        ("^", "rule", {"id": "light", "light": light(bright=5)}),
        (HL, "sys", ["/effects/0/amount"])]))
    E.append(S("Silence", [("^", "fx", [
        {"op": "defense", "kind": "immunity", "damage_types": ["thunder"], "target": area("sphere", 20), "duration": "@duration"},
        cond("deafened", target=area("sphere", 20), note="While entirely inside the Sphere."),
        {"op": "restrict", "restrictions": ["cast_verbal_spells"], "target": area("sphere", 20), "duration": "@duration"}]),
        ("^", "rule", {"id": "silence", "no_sound_created_or_passes": True})]))
    E.append(S("Spider Climb", [
        ("^", "fx", [{"op": "speed", "movement": "climb", "mode": "equal_to_walk", "value": 0, "target": touch(willing=True),
                      "duration": "@duration"},
                     {"op": "modifier", "stat": "spider_climb", "mode": "set", "value": 1, "duration": "@duration",
                      "note": "Move on vertical surfaces and ceilings with hands free."}]),
        (HL, "rule", {"id": "targets", "count": EXTRA()})]))
    E.append(S("Spike Growth", [
        ("^", "rule", {"id": "terrain", "area": {"shape": "sphere", "radius_feet": 20}, "difficult_terrain": True}),
        ("^", "fx", {"op": "trigger", "event": {"event": "moves_within_area"}, "duration": "@duration",
                     "then": [dmg("2d4", "piercing", target=INHERIT, note="For every 5 feet it travels.")]}),
        ("The transformation of the ground", "rule", {"id": "camouflage", "recognize": {
            "action": "dnd5e/action/search", "check": {"ability": "wis", "skills": ["perception", "survival"], "dc": "spell_save_dc"}},
            "applies_to": "creatures_that_cant_see_area_at_casting"})]))
    E.append(S("Spiritual Weapon", [
        ("^", "fx", attack("melee_spell", dmg({"op": "add", "args": [updice(1, 8, 2), MOD]}, "force"),
                           note="Against a creature within 5 feet of the force.")),
        ("As a Bonus Action on your later turns", "fx", {"op": "activation", "cost": "bonus_action", "then": [
            {"op": "move", "mode": "move", "distance_feet": 20, "note": "The force."},
            attack("melee_spell", dmg({"op": "add", "args": [updice(1, 8, 2), MOD]}, "force"))]}),
        (HL, "sys", ["/effects/0/on_hit/0/amount", "/effects/1/then/1/on_hit/0/amount"])]))
    E.append(S("Suggestion", [
        ("^", "rule", {"id": "suggestion", "max_words": 25, "must_sound_achievable": True, "no_obvious_harm": True,
                       "target_must_hear_and_understand": True}),
        ("The target must succeed on a Wisdom", "fx", save("wis", cond("charmed", note="Ends if you or your allies damage it; pursues the suggestion; ends when completed."),
                                                           target=creatures(must_see=True)))]))
    E.append(S("Warding Bond", [
        ("^", "fx", [{"op": "modifier", "stat": "ac", "mode": "add", "value": 1, "target": touch(willing=True), "duration": "@duration",
                      "when": {"pred": "within_feet", "args": {"feet": 60}}},
                     {"op": "modifier", "stat": "saving_throw", "mode": "add", "value": 1, "duration": "@duration",
                      "when": {"pred": "within_feet", "args": {"feet": 60}}},
                     {"op": "defense", "kind": "resistance", "damage_types": ALL_BUT(), "duration": "@duration",
                      "when": {"pred": "within_feet", "args": {"feet": 60}}},
                     {"op": "trigger", "event": {"event": "damage_taken", "whose": "target"}, "duration": "@duration",
                      "then": [dmg({"var": "damage_amount"}, {"var": "chosen.trigger_damage_type"}, target=SELF,
                                   note="You take the same amount of damage.")]}]),
        ("The spell ends if you drop to 0", "rule", {"id": "ends", "ends_on": ["you_drop_to_0_hp", "separated_by_more_than_60_feet",
                                                                               "cast_again_on_either"]})]))
    E.append(S("Web", [
        ("^", "rule", {"id": "webs", "area": {"shape": "cube", "size_feet": 20}, "difficult_terrain": True,
                       "lightly_obscured": "dnd5e/rule/lightly-obscured"}),
        ("If the webs aren’t anchored", "rule", {"id": "anchoring", "unanchored_ends_at": "start_of_your_next_turn",
                                                 "layer_depth_feet": 5}),
        ("The first time a creature enters", "fx", {"op": "trigger", "event": {"event": "enters_or_starts_turn_in_area"},
                                                    "frequency": {"count": 1, "per": "turn"}, "duration": "@duration",
                                                    "then": [save("dex", cond("restrained", note="While in the webs or until it breaks free."), target=INHERIT)]}),
        ("A creature Restrained by the webs", "fx", {"op": "activation", "cost": "action", "then": [
            {"op": "check", "ability": "str", "skill": "athletics", "dc": DC,
             "on_success": [{"op": "remove_condition", "conditions": [C("restrained")]}]}]}),
        ("The webs are flammable", "fx", {"op": "trigger", "event": {"event": "turn_start", "whose": "any"},
                                          "condition": {"pred": "in_burning_webs"},
                                          "then": [dmg("2d4", "fire", target=INHERIT)],
                                          "note": "Any 5-foot Cube of webs exposed to fire burns away in 1 round."})]))
    E.append(S("Zone of Truth", [
        ("^", "fx", {"op": "trigger", "event": {"event": "enters_or_starts_turn_in_area"}, "frequency": {"count": 1, "per": "turn"},
                     "duration": "@duration", "then": [save("cha", {"op": "restrict", "restrictions": ["speak_deliberate_lie"]},
                                                           target=INHERIT, note="You know whether it succeeds.")]}),
        ("^", "rule", {"id": "zone", "area": {"shape": "sphere", "radius_feet": 15}}),
        ("An affected creature is aware", "rule", {"id": "aware", "can_evade_questions": True, "must_be_truthful": True})]))
    E.append(creature_entry("Otherworldly Steed", 131, LOT, "Spells/Spell Descriptions/Find Steed/Otherworldly Steed",
                            overrides={
                                "ac": {"value": {"op": "add", "args": [10, {"var": "spell_level"}]}},
                                "hp": {"value": {"op": "add", "args": [5, {"op": "mul", "args": [10, {"var": "spell_level"}]}]},
                                       "hit_dice": {"count": {"var": "spell_level"}, "die": "d10"}},
                                "speed": {"walk": 60, "fly": 60, "fly_requires_spell_level": 4},
                                "summoned_by": SP("find-steed")},
                            fx={"Otherworldly Slam": [attack("melee", dmg({"op": "add", "args": ["1d8", {"var": "spell_level"}]},
                                                                          ["radiant", "psychic", "necrotic"],
                                                                          note="Radiant (Celestial), Psychic (Fey) or Necrotic (Fiend)."),
                                                             bonus={"var": "spell_attack_bonus"})],
                                "Healing Touch": [heal({"op": "add", "args": ["2d8", {"var": "spell_level"}]})]}))
    return E


REGISTRY = {
    "stats": [
        {"id": "weapon_bonus", "description": "Magic bonus of a weapon to attack and damage rolls.", "pages": [148]},
        {"id": "leaves_tracks", "description": "The creature leaves tracks (1) or not (0).", "pages": [151]},
        {"id": "spider_climb", "description": "The creature can move on vertical surfaces and ceilings with hands free.", "pages": [164]}],
    "senses": [
        {"id": "sense_thoughts", "description": "Sense the presence of thinking creatures within range.", "pages": [124]},
        {"id": "know_target_location", "description": "Always know the target's location (same plane).", "pages": [149]},
        {"id": "see_invisible", "description": "See Invisible creatures and objects as if visible.", "pages": [161]},
        {"id": "see_ethereal", "description": "See into the Ethereal Plane.", "pages": [161]}],
    "restrictions": [
        {"id": "cast_verbal_spells", "description": "The creature can't cast a spell that includes a Verbal component.", "pages": [163]},
        {"id": "speak_deliberate_lie", "description": "The creature can't speak a deliberate lie.", "pages": [174]}],
    "events": [
        {"id": "ends_turn_within_feet_of_effect", "description": "A creature ends its turn within a distance of the spell's effect.", "pages": [132]},
        {"id": "attacks_deals_damage_or_casts", "description": "The creature makes an attack roll, deals damage, or casts a spell.", "pages": [142]},
        {"id": "moves_within_area", "description": "A creature moves into or within the area.", "pages": [164]},
        {"id": "enters_or_starts_turn_in_area", "description": "A creature enters the area or starts its turn there.", "pages": [174]}],
    "predicates": [
        {"id": "attacker_perceives_with", "description": "The attacker perceives the target with one of these senses (param).", "params": ["senses"], "type": "predicate", "pages": [114]},
        {"id": "in_spell_area", "description": "The creature is in the spell's area.", "type": "predicate", "pages": [137]},
        {"id": "phantasm_is_dangerous", "description": "The phantasm represents a dangerous creature or hazard and the target is in or within 5 feet of it.", "type": "predicate", "pages": [152]},
        {"id": "roll_uses_ability", "description": "The D20 Test uses this ability (param).", "params": ["ability"], "type": "predicate", "pages": [157]},
        {"id": "in_burning_webs", "description": "The creature starts its turn in webs that are burning.", "type": "predicate", "pages": [174]}],
}

if __name__ == "__main__":
    write_all(entries(), REGISTRY, LOT)
