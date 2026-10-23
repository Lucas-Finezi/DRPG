#!/usr/bin/env python3
"""L22 — Level 5 spells (38) and the Animated Object and Draconic Spirit stat blocks.

Usage: python3 -I tools/build/l22_level5.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spelllib import (C, DC, EACH_END, INHERIT, MAGIC, MOD, SELF, SLOT, SP, STUDY, S_for, active,  # noqa: E402
                      all_but, area, attack, cond, creatures, dmg, extra_targets, heal, light, md, ref, save, touch,
                      until_turn, up, updice, write_all)
from statblock import creature_entry  # noqa: E402

LOT = "L22"
S = S_for(LOT)
HL = "***Using a Higher-Level Spell Slot.***"
SL = {"var": "spell_level"}
PLANAR = ["aberration", "celestial", "elemental", "fey", "fiend", "undead"]


def entries():
    E = []
    E.append(S("Animate Objects", [
        ("^", "rule", {"id": "objects", "nonmagical": True, "not_worn_carried_or_fixed": True, "not_gargantuan": True,
                       "max_count": MOD, "count_weight": {"medium_or_smaller": 1, "large": 2, "huge": 3}}),
        ("Each target animates", "fx", {"op": "summon", "creature": "dnd5e/creature/animated-object", "controller": "summoner",
                                        "initiative": "after_summoner",
                                        "note": "One per object; under your control until the spell ends or it drops to 0 Hit Points."}),
        ("Until the spell ends, you can take a Bonus Action", "fx", {"op": "activation", "cost": "bonus_action", "then": [
            ref(SP("animate-objects"), note="Command any or all of your creatures within 500 feet.")]}),
        ("Until the spell ends, you can take a Bonus Action", "rule", {"id": "behavior", "no_command": "dnd5e/action/dodge",
                                                                       "at_0_hp": "reverts_to_object_damage_carries_over"}),
        (HL, "rule", {"id": "upcast_slam", "extra_damage_per_level_above_5": {"medium_or_smaller": "1d4", "large": "1d6", "huge": "1d12"}})]))
    E.append(S("Antilife Shell", [
        ("^", "fx", {"op": "restrict", "restrictions": ["pass_or_reach_through_barrier"], "duration": "@duration",
                     "target": area("emanation", 10, "self", exclude_creature_types=["construct", "undead"]),
                     "note": "Affected creatures can still cast spells or make Ranged or Reach weapon attacks through it."}),
        ("If you move so that an affected creature", "rule", {"id": "ends", "ends_if_forcing_creature_through": True})]))
    hand = {"op": "choice", "id": "hand_effect", "choose": 1, "options": [
        {"id": "clenched_fist", "label": "Clenched Fist", "effects": [attack("melee_spell", dmg(updice(5, 8, 5, 2), "force"))]},
        {"id": "forceful_hand", "label": "Forceful Hand", "effects": [save("str", {"op": "move", "mode": "push",
                                                                                   "distance_feet": {"op": "add", "args": [5, {"op": "mul", "args": [5, MOD]}]}},
                                                                           target={"kind": "creature", "filter": {"sizes": ["tiny", "small", "medium", "large", "huge"]}})]},
        {"id": "grasping_hand", "label": "Grasping Hand", "effects": [
            save("dex", cond("grappled", None, params={"escape_dc": DC}),
                 target={"kind": "creature", "filter": {"sizes": ["tiny", "small", "medium", "large", "huge"]}}),
            {"op": "activation", "cost": "bonus_action", "then": [dmg({"op": "add", "args": [updice(4, 6, 5, 2), MOD]}, "bludgeoning")],
             "note": "Crush the grappled target."}]},
        {"id": "interposing_hand", "label": "Interposing Hand", "effects": [
            ref("dnd5e/rule/cover", note="Half Cover against attacks and effects from or through its space; its space is Difficult Terrain for your enemies.")]}]}
    E.append(S("Arcane Hand", [
        ("^", "rule", {"id": "hand", "size": "large", "object": True, "ac": 20, "hp": {"var": "hp_max"}, "occupies_space": False}),
        ("When you cast the spell and as a Bonus Action", "fx", {"op": "activation", "cost": "bonus_action", "then": [
            {"op": "move", "mode": "move", "distance_feet": 60, "note": "The hand; then one effect."}, hand]}),
        ("**Clenched Fist.**", "sys", ["/effects/0/then/1/options/0"]),
        ("**Forceful Hand.**", "sys", ["/effects/0/then/1/options/1"]),
        ("**Grasping Hand.**", "sys", ["/effects/0/then/1/options/2"]),
        ("**Interposing Hand.**", "sys", ["/effects/0/then/1/options/3"]),
        (HL, "sys", ["/effects/0/then/1/options/0/effects/0/on_hit/0/amount",
                     "/effects/0/then/1/options/2/effects/1/then/0/amount"])]))
    E.append(S("Awaken", [
        ("^", "rule", {"id": "awaken", "targets": ["beast_or_plant_creature_int_3_or_less", "natural_plant"],
                       "int": 10, "speaks_one_of_your_languages": True, "plant_becomes_creature": True}),
        ("^", "md", md("awakened_plant_stats", "Which statistics does the awakened Plant use?",
                       "The GM chooses statistics appropriate for the awakened Plant, such as the statistics for the Awakened Shrub or Awakened Tree in “Monsters.”",
                       options=[{"id": "awakened_shrub", "label": "Awakened Shrub"}, {"id": "awakened_tree", "label": "Awakened Tree"}])),
        ("^", "ref", ["dnd5e/creature/awakened-shrub", "dnd5e/creature/awakened-tree"]),
        ("The awakened target has the Charmed condition", "fx", cond("charmed", {"kind": "days", "amount": 30},
                                                                    note="Ends early if you or your allies damage it; it then chooses its attitude."))]))
    E.append(S("Cloudkill", [
        ("^", "rule", {"id": "fog", "area": {"shape": "sphere", "radius_feet": 20}, "heavily_obscured": True,
                       "dispersed_by_strong_wind": True, "example": SP("gust-of-wind")}),
        ("Each creature in the Sphere", "fx", [
            save("con", dmg(updice(5, 8, 5), "poison"), half=True, target=area("sphere", 20)),
            {"op": "trigger", "event": {"event": "enters_or_ends_turn_in_area"}, "frequency": {"count": 1, "per": "turn"},
             "duration": "@duration", "then": [save("con", dmg(updice(5, 8, 5), "poison"), half=True, target=INHERIT)]}]),
        ("The Sphere moves 10 feet away", "fx", {"op": "trigger", "event": {"event": "turn_start", "whose": "self", "which": "each"},
                                                 "duration": "@duration",
                                                 "then": [{"op": "move", "mode": "move", "distance_feet": 10, "note": "The Sphere, away from you."}]}),
        (HL, "sys", ["/effects/0/on_fail/0/amount", "/effects/1/then/0/on_fail/0/amount"])]))
    E.append(S("Commune", [
        ("^", "rule", {"id": "questions", "max": 3, "yes_or_no": True, "correct_answers": True}),
        ("Divine beings aren’t necessarily omniscient", "md", md("commune_answer", "What does the deity answer?",
                                                                 "Divine beings aren’t necessarily omniscient, so you might receive “unclear” as an answer if a question pertains to information that lies beyond the deity’s knowledge. In a case where a one-word answer could be misleading or contrary to the deity’s interests, the GM might offer a short phrase as an answer instead.",
                                                                 reason="narrative")),
        ("If you cast the spell more than once", "rule", {"id": "repeat_casting", "no_answer_chance_percent": {
            "op": "mul", "args": [25, {"var": "uses_since_rest.commune"}]}, "reset_on": "long_rest_finished"})]))
    E.append(S("Commune with Nature", [
        ("^", "rule", {"id": "area", "outdoors_miles": 3, "underground_feet": 300, "fails_in_constructed_areas": True}),
        ("Choose three of the following facts", "md", md("nature_facts", "What does the caster learn about the chosen facts?",
                                                         "Choose three of the following facts; you learn those facts as they pertain to the spell’s area", reason="narrative")),
        ("Choose three of the following facts", "rule", {"id": "facts", "choose": 3, "options": [
            "settlements", "planar_portals", "one_cr_10_plus_celestial_elemental_fey_fiend_or_undead_gm_choice",
            "most_prevalent_plant_mineral_or_beast", "bodies_of_water"]}),
        ("For example, you could determine", "desc", None)]))
    E.append(S("Cone of Cold", [
        ("^", "fx", save("con", dmg(updice(8, 8, 5), "cold"), half=True, target=area("cone", 60, "self"))),
        ("^", "rule", {"id": "frozen", "killed_creatures_become_frozen_statues": True}),
        (HL, "sys", ["/effects/0/on_fail/0/amount"])]))
    E.append(S("Conjure Elemental", [
        ("^", "rule", {"id": "spirit", "size": "large", "intangible": True,
                       "elements": {"air": "lightning", "earth": "thunder", "fire": "fire", "water": "cold"}}),
        ("Whenever a creature you can see enters", "fx", {
            "op": "trigger", "event": {"event": "enters_space_or_starts_turn_near_spirit"}, "optional": True, "duration": "@duration",
            "condition": {"not": {"pred": "spirit_restrains_creature"}},
            "then": [save("dex", [dmg(updice(8, 8, 5), {"var": "chosen.element_damage_type"}), cond("restrained")], target=INHERIT)]}),
        ("Whenever a creature you can see enters", "fx", {
            "op": "trigger", "event": {"event": "turn_start", "whose": "target", "which": "each"}, "duration": "@duration",
            "condition": {"pred": "has_condition", "args": {"condition": "restrained"}},
            "then": [save("dex", dmg(updice(4, 8, 5), {"var": "chosen.element_damage_type"}), target=INHERIT,
                          on_success={"op": "remove_condition", "conditions": [C("restrained")]})]}),
        (HL, "sys", ["/effects/0/then/0/on_fail/0/amount", "/effects/1/then/0/on_fail/0/amount"])]))
    E.append(S("Contact Other Plane", [
        ("^", "fx", {"op": "save", "ability": "int", "dc": 15, "target": SELF,
                     "on_fail": [dmg("6d6", "psychic"), cond("incapacitated", {"kind": "until_event", "until": {"event": "long_rest_finished"}})]}),
        ("^", "md", md("entity_answers", "What one-word answers does the entity give?",
                       "The GM answers each question with one word, such as “yes,” “no,” “maybe,” “never,” “irrelevant,” or “unclear” (if the entity doesn’t know the answer to the question). If a one-word answer would be misleading, the GM might instead offer a short phrase as an answer.")),
        ("^", "rule", {"id": "questions", "max": 5, "on": "successful_save"}),
        ("On a failed save", "rule", {"id": "cure", "ended_by": SP("greater-restoration")})]))
    E.append(S("Contagion", [
        ("^", "fx", save("con", [dmg("11d8", "necrotic"), cond("poisoned"),
                                 {"op": "roll_mode", "mode": "disadvantage", "rolls": ["saving_throw"], "duration": "@duration",
                                  "when": {"pred": "roll_uses_ability", "args": {"ability": "chosen.ability"}}}], target=touch())),
        ("The target must repeat the saving throw", "rule", {"id": "progression", "repeat_on": "end_of_each_turn",
                                                             "three_successes": "spell_ends", "three_failures": "lasts_7_days"}),
        ("Whenever the Poisoned target receives an effect", "fx", {"op": "trigger", "event": {"event": "condition_would_end.poisoned"},
                                                                   "then": [save("con", None, target=INHERIT,
                                                                                 note="On a failure the Poisoned condition doesn't end.")]})]))
    E.append(S("Creation", [
        ("^", "rule", {"id": "object", "matter": ["vegetable", "mineral"], "max_cube_feet": up(5, 5, 5), "seen_form_and_material": True}),
        ("The spell’s duration depends", "rule", {"id": "duration", "by_material": "materials", "multiple_materials": "shortest",
                                                  "as_material_component": "other_spell_fails"}),
        ("##### Materials", "table", {"id": "materials", "caption": "Materials", "columns": ["Material", "Duration"],
                                      "rows": [["Vegetable matter", "24 hours"], ["Stone or crystal", "12 hours"],
                                               ["Precious metals", "1 hour"], ["Gems", "10 minutes"],
                                               ["Adamantine or mithral", "1 minute"]]}),
        (HL, "sys", ["rule:object"])]))
    E.append(S("Dispel Evil and Good", [
        ("^", "fx", {"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll"], "direction": "against", "duration": "@duration",
                     "when": {"pred": "attacker_creature_type_in", "args": {"types": PLANAR[1:]}}}),
        ("***Break Enchantment.***", "fx", {"op": "activation", **MAGIC, "target": touch(), "then": [
            {"op": "remove_condition", "conditions": [C("charmed"), C("frightened")],
             "note": "Only those from Celestials, Elementals, Fey, Fiends or Undead; also ends possession."},
            {"op": "end_effect", "scope": "this_entry"}]}),
        ("***Dismissal.***", "fx", {"op": "activation", **MAGIC, "then": [
            save("cha", ref(SP("dispel-evil-and-good"), note="Sent to its home plane; Undead to the Shadowfell and Fey to the Feywild if not on their home plane."),
                 target={"kind": "creature", "range": {"kind": "distance", "feet": 5}, "must_see": True,
                         "filter": {"creature_types": PLANAR[1:]}}),
            {"op": "end_effect", "scope": "this_entry"}]})]))
    E.append(S("Dominate Person", [
        ("^", "fx", [save("wis", cond("charmed"), target=creatures(must_see=True, creature_types=["humanoid"]),
                          note="Advantage if you or your allies are fighting it."),
                     {"op": "trigger", "event": {"event": "damage_taken", "whose": "target"}, "duration": "@duration",
                      "then": [save("wis", None, target=INHERIT, on_success={"op": "end_effect", "scope": "this_entry"})]}]),
        ("You have a telepathic link", "rule", {"id": "commands", "telepathic_link": "same_plane", "command_cost": "none",
                                                "obeys_on_its_turn": True, "idle": "protects_itself"}),
        ("You can command the target to take a Reaction", "rule", {"id": "reaction", "costs_your_reaction": True}),
        (HL, "rule", {"id": "longer_concentration", "max_duration_minutes": {"scale": {"by": "spell_slot_level", "steps": [
            {"from": 5, "value": 1}, {"from": 6, "value": 10}, {"from": 7, "value": 60}, {"from": 8, "value": 480}]}}})]))
    E.append(S("Dream", [
        ("^", "rule", {"id": "messenger", "target": "known_creature_same_plane", "messenger": ["you", "willing_creature_touched"],
                       "messenger_state": [C("incapacitated"), "speed_0"]}),
        ("If the target is asleep", "md", md("dream_content", "What happens in the dream?",
                                             "The messenger can also shape the dream’s environment, creating landscapes, objects, and other images.",
                                             reason="narrative")),
        ("If the target is awake", "rule", {"id": "awake", "messenger_knows": True, "end_or_wait": True}),
        ("You can make the messenger terrifying", "fx", save("wis", [
            {"op": "restrict", "restrictions": ["benefit_from_rest"]},
            dmg("3d6", "psychic", note="When it wakes up.")], target=creatures(), note="After a message of no more than ten words."))]))
    E.append(S("Flame Strike", [
        ("^", "fx", save("dex", [dmg(updice(5, 6, 5), "fire"), dmg(updice(5, 6, 5), "radiant")], half=True, target=area("cylinder", 10))),
        ("^", "rule", {"id": "cylinder", "radius_feet": 10, "height_feet": 40}),
        (HL, "sys", ["/effects/0/on_fail/0/amount", "/effects/0/on_fail/1/amount"])]))
    E.append(S("Geas", [
        ("^", "fx", save("wis", cond("charmed"), target=creatures(must_see=True),
                         note="Automatically succeeds if it can't understand your command.")),
        ("While Charmed, the creature takes", "fx", {"op": "trigger", "event": {"event": "acts_against_command"}, "duration": "@duration",
                                                     "frequency": {"count": 1, "per": "day"}, "then": [dmg("5d10", "psychic", target=INHERIT)]}),
        ("You can issue any command", "md", md("geas_command", "Is the command suicidal (ending the spell), and is the creature acting directly counter to it?",
                                               "You can issue any command you choose, short of an activity that would result in certain death. Should you issue a suicidal command, the spell ends.")),
        ("A *Remove Curse*", "rule", {"id": "ended_by", "spells": [SP("remove-curse"), SP("greater-restoration"), SP("wish")]}),
        (HL, "rule", {"id": "upcast_duration", "by_slot_level": [{"slot": 7, "days": 365}, {"slot": 9, "duration": "until_ended_by_listed_spells"}]})]))
    E.append(S("Greater Restoration", [
        ("^", "fx", {"op": "choice", "id": "restoration", "choose": 1, "target": touch(), "options": [
            {"id": "exhaustion", "label": "1 Exhaustion level", "effects": [{"op": "remove_condition", "conditions": [C("exhaustion")], "levels": 1}]},
            {"id": "charmed_petrified", "label": "Charmed or Petrified", "effects": [{"op": "remove_condition", "conditions": [C("charmed"), C("petrified")], "count": 1}]},
            {"id": "curse", "label": "A curse", "effects": [ref("dnd5e/curse/cursed-magic-items", note="Including Attunement to a cursed magic item.")]},
            {"id": "ability_reduction", "label": "Ability score reduction", "effects": [{"op": "modifier", "stat": "ability_score_reduction", "mode": "set", "value": 0}]},
            {"id": "hp_max_reduction", "label": "Hit Point maximum reduction", "effects": [{"op": "modifier", "stat": "hp_max_reduction", "mode": "set", "value": 0}]}]}),
        ("- 1 Exhaustion level", "sys", ["/effects/0/options/0"]),
        ("- The Charmed or Petrified", "sys", ["/effects/0/options/1"]),
        ("- A curse", "sys", ["/effects/0/options/2"]),
        ("- Any reduction to one of the target’s ability scores", "sys", ["/effects/0/options/3"]),
        ("- Any reduction to the target’s Hit Point maximum", "sys", ["/effects/0/options/4"])]))
    hallow_extras = ["courage", "darkness", "daylight", "peaceful_rest", "extradimensional_interference", "fear", "resistance",
                     "silence", "tongues", "vulnerability"]
    E.append(S("Hallow", [
        ("^", "rule", {"id": "area", "max_radius_feet": 60, "fails_if_overlapping_hallow": True}),
        ("***Hallowed Ward.***", "fx", [
            {"op": "restrict", "restrictions": ["enter_area_willingly"], "duration": "@duration",
             "when": {"pred": "creature_type_chosen"}, "note": "Creatures of the chosen types."},
            {"op": "remove_condition", "conditions": [C("charmed"), C("frightened")], "duration": "@duration",
             "note": "Suppressed while in the area when caused by creatures of the chosen types; also possession."}]),
        ("***Hallowed Ward.***", "rule", {"id": "ward_types", "choose_any_of": PLANAR}),
        ("***Extra Effect.***", "rule", {"id": "extra_effect", "choose_one_of": hallow_extras}),
        ("**Courage.**", "fx", {"op": "defense", "kind": "immunity", "conditions": [C("frightened")], "duration": "@duration",
                               "when": {"pred": "creature_type_chosen"}}),
        ("**Darkness.**", "rule", {"id": "darkness", "fills_area": True, "blocks_light_from_spells_below_level": SL}),
        ("**Daylight.**", "rule", {"id": "daylight", "bright_light": True, "resists_darkness_from_spells_below_level": SL}),
        ("**Peaceful Rest.**", "rule", {"id": "peaceful_rest", "bodies_cannot_become_undead": True}),
        ("**Extradimensional Interference.**", "fx", {"op": "restrict", "restrictions": ["teleport_or_planar_travel_in_area"],
                                                     "duration": "@duration", "when": {"pred": "creature_type_chosen"}}),
        ("**Fear.**", "fx", cond("frightened", when={"pred": "creature_type_chosen"}, note="While in the area.")),
        ("**Resistance.**", "fx", {"op": "defense", "kind": "resistance", "damage_types": [{"var": "chosen.damage_type"}],
                                  "duration": "@duration", "when": {"pred": "creature_type_chosen"}}),
        ("**Silence.**", "rule", {"id": "silence", "no_sound_in_or_out": True}),
        ("**Tongues.**", "rule", {"id": "tongues", "communicate_with_any_creature": True}),
        ("**Vulnerability.**", "fx", {"op": "defense", "kind": "vulnerability", "damage_types": [{"var": "chosen.damage_type"}],
                                     "duration": "@duration", "when": {"pred": "creature_type_chosen"}})]))
    E.append(S("Hold Monster", [
        ("^", "fx", save("wis", cond("paralyzed"), target=creatures(extra_targets(5), must_see=True), repeat=EACH_END)),
        (HL, "sys", ["/effects/0/target/count"])]))
    E.append(S("Insect Plague", [
        ("^", "rule", {"id": "swarm", "area": {"shape": "sphere", "radius_feet": 20}, "lightly_obscured": True, "difficult_terrain": True}),
        ("When the swarm appears", "fx", [
            save("con", dmg(updice(4, 10, 5), "piercing"), half=True, target=area("sphere", 20)),
            {"op": "trigger", "event": {"event": "enters_or_ends_turn_in_area"}, "frequency": {"count": 1, "per": "turn"},
             "duration": "@duration", "then": [save("con", dmg(updice(4, 10, 5), "piercing"), half=True, target=INHERIT)]}]),
        (HL, "sys", ["/effects/0/on_fail/0/amount", "/effects/1/then/0/on_fail/0/amount"])]))
    E.append(S("Legend Lore", [
        ("^", "md", md("lore", "What lore does the caster learn?",
                       "The spell brings to your mind a brief summary of the significant lore about that famous thing, as described by the GM.",
                       reason="narrative")),
        ("The lore might consist", "desc", None),
        ("If the famous thing you chose", "rule", {"id": "not_famous", "spell_fails": True})]))
    E.append(S("Mass Cure Wounds", [
        ("^", "fx", heal({"op": "add", "args": [updice(5, 8, 5), MOD]}, target=area("sphere", 30), note="Up to six creatures in the Sphere.")),
        (HL, "sys", ["/effects/0/amount"])]))
    E.append(S("Mislead", [
        ("^", "fx", cond("invisible", {"kind": "hours", "amount": 1, "up_to": True, "concentration": True,
                                       "ends_on": [{"event": "attacks_deals_damage_or_casts"}]}, target=SELF)),
        ("^", "rule", {"id": "double", "illusory_double": True}),
        ("As a Magic action, you can move", "fx", {"op": "activation", **MAGIC, "then": [
            {"op": "move", "mode": "move", "distance_feet": {"op": "mul", "args": [2, {"var": "speed.walk"}]},
             "note": "The double; it gestures, speaks and behaves as you choose; intangible and invulnerable."}]}),
        ("You can see through its eyes", "rule", {"id": "senses", "see_and_hear_through_double": True})]))
    E.append(S("Modify Memory", [
        ("^", "fx", save("wis", [cond("charmed"), cond("incapacitated")], target=creatures(must_see=True),
                         note="Advantage if you are fighting it; it is unaware of its surroundings but hears you; ends with no change if it takes damage or is targeted by another spell.")),
        ("While this charm lasts", "rule", {"id": "memory", "event_within_hours": 24, "event_max_minutes": 10,
                                            "options": ["eliminate", "perfect_recall", "change_details", "create_other"]}),
        ("You must speak to the target", "rule", {"id": "describe", "target_must_understand": True,
                                                  "ends_early": "no_change", "takes_hold_on_end": True}),
        ("A modified memory doesn’t necessarily", "md", md("memory_effect", "Does the modified memory affect the creature's behavior, or is it too nonsensical?",
                                                            "The GM might deem a modified memory too nonsensical to affect a creature.")),
        ("A *Remove Curse*", "rule", {"id": "restored_by", "spells": [SP("remove-curse"), SP("greater-restoration")]}),
        (HL, "rule", {"id": "upcast", "event_age_days": {"scale": {"by": "spell_slot_level", "steps": [
            {"from": 5, "value": 1}, {"from": 6, "value": 7}, {"from": 7, "value": 30}, {"from": 8, "value": 365}]}},
                      "slot_9": "any_time"})]))
    E.append(S("Passwall", [
        ("^", "rule", {"id": "passage", "surfaces": ["wood", "plaster", "stone"], "max_feet": {"width": 5, "height": 8, "depth": 20},
                       "no_instability": True}),
        ("When the opening disappears", "rule", {"id": "ejection", "safe_ejection_to_nearest_space": True})]))
    E.append(S("Planar Binding", [
        ("^", "fx", save("cha", ref(SP("planar-binding"), note="Bound to serve you for the duration."),
                         target={"kind": "creature", "range": "@range", "filter": {"creature_types": ["celestial", "elemental", "fey", "fiend"]}})),
        ("^", "rule", {"id": "casting", "within_range_entire_casting": True, "typical_trap": SP("magic-circle"),
                       "extends_summoning_spell": True}),
        ("A bound creature must follow", "md", md("bound_service", "How does the bound creature carry out (or twist) the commands?",
                                                  "If the creature is Hostile, it strives to twist your commands to achieve its own objectives.",
                                                  reason="narrative")),
        ("A bound creature must follow", "rule", {"id": "report", "same_plane": "travels_to_report", "other_plane": "returns_to_binding_place"}),
        (HL, "rule", {"id": "upcast_duration_days", "by_slot_level": {"6": 10, "7": 30, "8": 180, "9": 366}})]))
    E.append(S("Raise Dead", [
        ("^", "fx", {"op": "modifier", "stat": "hp", "mode": "set", "value": 1, "target": touch(),
                     "note": "Dead no longer than 10 days and not Undead when it died."}),
        ("The creature returns to life", "rule", {"id": "poisons", "neutralizes_poisons": True}),
        ("This spell closes all mortal wounds", "rule", {"id": "body", "restores_missing_parts": False, "fails_without_vital_parts": True}),
        ("Coming back from the dead is an ordeal", "fx", {"op": "modifier", "stat": "d20_test", "mode": "add", "value": -4,
                                                          "note": "Reduced by 1 each time the target finishes a Long Rest."})]))
    species = [["1", "Roll again."], ["2", "Dragonborn"], ["3", "Dwarf"], ["4", "Elf"], ["5", "Gnome"],
               ["6", "Goliath"], ["7", "Halfling"], ["8", "Human"], ["9", "Orc"], ["10", "Tiefling"]]
    E.append(S("Reincarnate", [
        ("^", "fx", {"op": "choice", "id": "species", "choose": 1, "chooser": "random", "options": [
            {"id": "reroll", "label": "Roll again", "roll": "1", "effects": []}] + [
            {"id": r[1].lower(), "label": r[1], "roll": r[0], "effects": [{"op": "grant", "refs": [f"dnd5e/species/{r[1].lower()}"]}]}
            for r in species[1:]], "note": "Dead no longer than 10 days; a dead Humanoid or a piece of one."}),
        ("^", "md", md("other_species", "Does the GM choose another playable species instead of rolling?",
                       "Roll 1d10 and consult the table below to determine the body’s species, or the GM chooses another playable species.")),
        ("| **1d10**", "table", {"id": "reincarnate", "caption": "Reincarnate species", "columns": ["1d10", "Species"], "rows": species}),
        ("The reincarnated creature makes any choices", "rule", {"id": "result", "keeps_capabilities": True, "loses_old_species_traits": True,
                                                                 "gains_new_species_traits": True})]))
    E.append(S("Scrying", [
        ("^", "fx", save("wis", ref(SP("scrying"), note="An Invisible, intangible sensor within 10 feet of the target that moves with it."),
                         target={"kind": "creature"},
                         note="Save modified by knowledge and connection (tables).")),
        ("| **Your Knowledge", "table", {"id": "knowledge", "caption": "Your Knowledge of the Target Is …",
                                         "columns": ["Your Knowledge of the Target Is …", "Save Modifier"],
                                         "rows": [["Secondhand (heard of the target)", 5], ["Firsthand (met the target)", 0],
                                                  ["Extensive (know the target well)", -5]]}),
        ("| **Your Knowledge", "table", {"id": "connection", "caption": "You Have the Target’s …",
                                         "columns": ["You Have the Target’s …", "Save Modifier"],
                                         "rows": [["Picture or other likeness", -2], ["Garment or other possession", -4],
                                                  ["Body part, lock of hair, or bit of nail", -10]]}),
        ("On a successful save, the target isn’t affected", "rule", {"id": "immune", "hours": 24}),
        ("On a failed save, the spell creates", "rule", {"id": "sensor", "within_feet": 10, "moves_with_target": True,
                                                         "visible_as": "luminous_fist_sized_orb"}),
        ("Instead of targeting a creature", "rule", {"id": "location", "seen_location": True, "sensor_stationary": True})]))
    E.append(S("Seeming", [
        ("^", "fx", save("cha", ref(SP("seeming"), note="Illusory appearance; only unwilling targets save."),
                         target=creatures(must_see=True))),
        ("You can give the same appearance", "rule", {"id": "appearance", "height_change_feet": 1, "same_limb_arrangement": True}),
        ("You can give the same appearance", "md", md("seeming_extent", "What do the targets look like, within the limits?",
                                                      "the extent of the illusion is otherwise up to you", reason="player_choice_open")),
        ("The changes wrought by this spell", "rule", {"id": "physical_inspection", "fails_physical_inspection": True}),
        ("A creature that takes the Study action", "fx", STUDY)]))
    E.append(S("Summon Dragon", [
        ("^", "fx", {"op": "summon", "creature": "dnd5e/creature/draconic-spirit", "controller": "summoner",
                     "initiative": "after_summoner", "note": "Disappears at 0 Hit Points or when the spell ends."}),
        ("The creature is an ally", "rule", {"id": "ally", "obeys_verbal_commands": True, "idle": "dnd5e/action/dodge"}),
        (HL, "rule", {"id": "stat_block_level", "spell_level_in_stat_block": SLOT})]))
    E.append(S("Telekinesis", [
        ("^", "fx", {"op": "activation", **MAGIC, "then": [ref(SP("telekinesis"), note="Exert your will on one creature or object you can see within range.")]}),
        ("***Creature.***", "fx", save("str", [{"op": "move", "mode": "move", "distance_feet": 30},
                                               cond("restrained", until_turn("turn_end", "source"))],
                                       target={"kind": "creature", "range": "@range", "filter": {"sizes": ["tiny", "small", "medium", "large", "huge"]}})),
        ("***Object.***", "fx", {"op": "move", "mode": "move", "distance_feet": 30, "note": "A Huge or smaller object not worn or carried."}),
        ("If the object is worn or carried", "fx", save("str", {"op": "move", "mode": "move", "distance_feet": 30,
                                                                 "note": "Pull the object away and move it."}, target=INHERIT)),
        ("You can exert fine control", "md", md("fine_control", "What fine manipulation is possible with the telekinetic grip?",
                                                "You can exert fine control on objects with your telekinetic grip, such as manipulating a simple tool,",
                                                reason="ambiguous_source", pages=[168]))]))
    E.append(S("Telepathic Bond", [("^", "rule", {"id": "bond", "max_creatures": 8, "requires_language": True,
                                                  "any_distance": True, "other_planes": False})]))
    E.append(S("Teleportation Circle", [
        ("^", "rule", {"id": "circle", "radius_feet": 5, "destination": "known_permanent_circle_same_plane", "portal_open_until": "end_of_next_turn",
                       "arrival": "within_5_feet_of_destination"}),
        ("Many major temples", "desc", None),
        ("When you first gain the ability", "md", md("sigil_sequences", "Which two Material Plane destinations does the caster know?",
                                                     "When you first gain the ability to cast this spell, you learn the sigil sequences for two destinations on the Material Plane, determined by the GM.")),
        ("When you first gain the ability", "rule", {"id": "learning", "memorize_minutes": 1}),
        ("You can create a permanent teleportation circle", "rule", {"id": "permanent", "daily_castings": 365})]))
    E.append(S("Tree Stride", [
        ("^", "fx", {"op": "activation", "cost": "none", "movement_cost": 5, "frequency": {"count": 1, "per": "turn"},
                     "duration": "@duration",
                     "then": [{"op": "move", "mode": "teleport", "distance_feet": 500,
                               "note": "Enter a living tree at least your size and pass into another of the same kind within 500 feet (or step out); appear within 5 feet of it using another 5 feet of movement."}]}),
        ("^", "rule", {"id": "trees", "living": True, "min_size": "own_size", "same_kind": True, "know_locations_within_feet": 500,
                       "no_movement_left": "appear_near_entered_tree"}),
        ("You can use this transportation ability", "rule", {"id": "limits", "once_per_turn": True, "must_end_turn_outside": True})]))
    E.append(S("Wall of Force", [
        ("^", "rule", {"id": "wall", "invisible": True, "orientation": "any", "shapes": [
            {"dome_or_globe_radius_feet": 10}, {"panels": 10, "panel_feet": [10, 10], "contiguous": True}],
            "thickness_inches": 0.25, "displaces_creatures_to_chosen_side": True}),
        ("Nothing can physically pass through the wall", "rule", {
            "id": "properties", "impassable": True, "immune_to_damage": True, "dispel_magic": False,
            "destroyed_by": SP("disintegrate"), "blocks_ethereal": True})]))
    E.append(S("Wall of Stone", [
        ("^", "rule", {"id": "wall", "nonmagical": True, "panels": 10, "options": [
            {"panel_feet": [10, 10], "thickness_inches": 6}, {"panel_feet": [10, 20], "thickness_inches": 3}], "contiguous": True}),
        ("If the wall cuts through a creature’s space", "fx", save("dex", None, target={"kind": "creature"},
                                                                    on_success={"op": "move", "mode": "move", "distance_feet": {"var": "speed.walk"},
                                                                                "note": "With its Reaction, so it is no longer enclosed."},
                                                                    note="Only a creature that would be surrounded on all sides.")),
        ("If the wall cuts through a creature’s space", "rule", {"id": "displacement", "pushed_to_chosen_side": True}),
        ("The wall can have any shape", "rule", {"id": "shape", "any_shape": True, "must_merge_with_existing_stone": True,
                                                 "span_over_20_feet": "halve_panels_for_supports", "crude_shaping": True}),
        ("The wall is an object made of stone", "rule", {"id": "durability", "ac": 15, "hp_per_inch": 30,
                                                         "immunities": ["poison", "psychic"]}),
        ("The wall is an object made of stone", "md", md("panel_collapse", "Do connected panels collapse when a panel is destroyed?",
                                                         "Reducing a panel to 0 Hit Points destroys it and might cause connected panels to collapse at the GM’s discretion.")),
        ("If you maintain your Concentration", "rule", {"id": "permanent", "full_concentration": "permanent_undispellable",
                                                        "otherwise": "disappears"})]))
    E.append(creature_entry("Animated Object", 109, LOT, "Spells/Spell Descriptions/Animate Objects/Animated Object",
                            overrides={"ac": {"value": 15}, "hp": {"by_size": {"medium_or_smaller": 10, "large": 20, "huge": 40}},
                                       "speed": {"walk": 30}, "summoned_by": SP("animate-objects")},
                            fx={"Slam": [attack("melee", dmg({"op": "add", "args": ["1d4", 3]}, "force",
                                                             note="Medium or smaller; Large: 2d6 + 3 + your spellcasting ability modifier; Huge: 2d12 + 3 + your spellcasting ability modifier."),
                                                bonus={"var": "spell_attack_bonus"})]}))
    E.append(creature_entry("Draconic Spirit", 166, LOT, "Spells/Spell Descriptions/Summon Dragon/Draconic Spirit",
                            overrides={"ac": {"value": {"op": "add", "args": [14, SL]}},
                                       "hp": {"value": {"op": "add", "args": [50, {"op": "mul", "args": [10, {"op": "sub", "args": [SL, 5]}]}]}},
                                       "speed": {"walk": 30, "fly": 60, "swim": 30}, "summoned_by": SP("summon-dragon")},
                            fx={"Shared Resistances": [{"op": "defense", "kind": "resistance", "target": SELF,
                                                        "damage_types": [{"choose_from": ["acid", "cold", "fire", "lightning", "poison"]}],
                                                        "note": "The summoner, until the spell ends."}],
                                "Multiattack": [{"op": "repeat", "times": {"op": "div", "args": [SL, 2]}, "then": [attack("melee", note="Rend.")]}],
                                "Rend": [attack("melee", dmg({"op": "add", "args": ["1d6", 4, SL]}, "piercing"), bonus={"var": "spell_attack_bonus"})],
                                "Breath Weapon": [save("dex", dmg("2d6", ["acid", "cold", "fire", "lightning", "poison"]), half=True,
                                                       target={"kind": "area", "area": {"shape": "cone", "size_feet": 30, "origin": "self"}})]}))
    return E


REGISTRY = {
    "stats": [
        {"id": "ability_score_reduction", "description": "Total reduction applied to the creature's ability scores.", "pages": [138]},
        {"id": "hp_max_reduction", "description": "Total reduction applied to the creature's Hit Point maximum.", "pages": [138]}],
    "restrictions": [
        {"id": "pass_or_reach_through_barrier", "description": "The creature can't pass or reach through the barrier.", "pages": [109]},
        {"id": "benefit_from_rest", "description": "The creature gains no benefit from its rest.", "pages": [127]},
        {"id": "enter_area_willingly", "description": "The creature can't willingly enter the area.", "pages": [139]},
        {"id": "teleport_or_planar_travel_in_area", "description": "The creature can't enter or exit the area by teleportation or interplanar travel.", "pages": [139]}],
    "events": [
        {"id": "enters_space_or_starts_turn_near_spirit", "description": "A creature enters the spirit's space or starts its turn within 5 feet of it.", "pages": [119]},
        {"id": "condition_would_end", "description": "An effect would end a condition (param) on the creature.", "params": ["condition"], "pages": [121]},
        {"id": "acts_against_command", "description": "The Charmed creature acts in a manner directly counter to the command.", "pages": [137]}],
    "predicates": [
        {"id": "spirit_restrains_creature", "description": "The spirit already has a creature Restrained.", "type": "predicate", "pages": [119]},
        {"id": "creature_type_chosen", "description": "The creature is of a type chosen for the effect.", "type": "predicate", "pages": [139]}],
}

if __name__ == "__main__":
    write_all(entries(), REGISTRY, LOT)
