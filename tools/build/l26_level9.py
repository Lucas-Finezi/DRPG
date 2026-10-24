#!/usr/bin/env python3
"""L26 — Level 9 spells (16).

Usage: python3 -I tools/build/l26_level9.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spelllib import (C, DC, EACH_END, INHERIT, MAGIC, MOD, SELF, SLOT, SP, STUDY, S_for, active,  # noqa: E402
                      all_but, area, attack, cond, creatures, dmg, extra_targets, heal, light, md, ref, save, tab, touch,
                      until_turn, up, updice, write_all)

LOT = "L26"
S = S_for(LOT)


def prismatic_layers():
    layer = lambda lid, roll, eff: {"id": lid, "label": lid.title(), "roll": roll, "effects": eff}  # noqa: E731
    dmg_layer = lambda t: [save("dex", dmg("12d6", t), half=True, target=INHERIT)]  # noqa: E731
    return [layer("red", "1", dmg_layer("fire")), layer("orange", "2", dmg_layer("acid")),
            layer("yellow", "3", dmg_layer("lightning")), layer("green", "4", dmg_layer("poison")),
            layer("blue", "5", dmg_layer("cold")),
            layer("indigo", "6", [save("dex", cond("restrained", None,
                                                   note="Constitution save at the end of each of its turns: three successes end it, three failures: Petrified until freed by an effect like Greater Restoration."),
                                       target=INHERIT)]),
            layer("violet", "7", [save("dex", cond("blinded", None,
                                                   note="Wisdom save at the start of your next turn: success ends it; failure ends it and teleports the creature to another plane (GM's choice)."),
                                       target=INHERIT)])]


def entries():
    E = []
    E.append(S("Astral Projection", [
        ("^", "fx", [ref(SP("astral-projection"), target=creatures(9, willing=True),
                         note="You and up to eight willing creatures project into the Astral Plane; ends instantly if already there."),
                     cond("unconscious", note="The body, in suspended animation: no food or air needed, doesn't age.")]),
        ("A target’s astral form resembles", "rule", {"id": "astral_form", "replicates_statistics_and_possessions": True,
                                                      "silver_cord_visible_feet": 1, "cord_cut": "body_and_form_die",
                                                      "cut_only_when_effect_states": True}),
        ("A target’s astral form can travel", "rule", {"id": "travel", "leaving_astral_reunites_body_on_new_plane": True}),
        ("Any damage or other effects", "rule", {"id": "separation", "effects_dont_cross": True, "ends_at_0_hp": True,
                                                 "dismiss": "dnd5e/action/magic"}),
        ("When the spell ends for a target", "rule", {"id": "return", "reappears_in_body": True})]))
    E.append(S("Foresight", [("^", "fx", [
        {"op": "roll_mode", "mode": "advantage", "rolls": ["d20_test"], "target": touch(willing=True), "duration": "@duration"},
        {"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll"], "direction": "against", "duration": "@duration"}]),
        ("^", "rule", {"id": "ends", "ends_if_cast_again": True})]))
    E.append(S("Gate", [
        ("^", "rule", {"id": "portal", "diameter_feet": [5, 20], "any_orientation": True, "destination_visible": True}),
        ("The portal has a front and a back", "rule", {"id": "travel", "front_only": True, "arrival": "nearest_unoccupied_space"}),
        ("Deities and other planar rulers", "rule", {"id": "blocked_by", "deities_and_planar_rulers": True}),
        ("When you cast this spell, you can speak", "rule", {"id": "summon_named", "true_name_required": True,
                                                             "pulled_through_if_on_other_plane": True}),
        ("When you cast this spell, you can speak", "md", md("named_creature", "How does the summoned named creature act?",
                                                             "You gain no special power over the creature, and it is free to act as the GM deems appropriate. It might leave, attack you, or help you.",
                                                             options=[{"id": "leave", "label": "Leave"}, {"id": "attack", "label": "Attack"},
                                                                      {"id": "help", "label": "Help"}]))]))
    E.append(S("Imprisonment", [
        ("^", "fx", save("wis", [ref(SP("imprisonment"), note="Imprisoned: no need to breathe, eat or drink; doesn't age; can't be located by Divination; can't teleport."),
                                 {"op": "choice", "id": "prison", "choose": 1, "options": [
                                     {"id": "burial", "label": "Burial", "effects": [ref(SP("imprisonment"), note="Entombed in a globe of force; nothing passes in or out.")]},
                                     {"id": "chaining", "label": "Chaining", "effects": [cond("restrained", note="Can't be moved by any means.")]},
                                     {"id": "hedged_prison", "label": "Hedged Prison", "effects": [ref(SP("imprisonment"), note="Demiplane warded against teleportation and planar travel.")]},
                                     {"id": "minimus_containment", "label": "Minimus Containment", "effects": [ref(SP("imprisonment"), note="1 inch tall inside an indestructible gemstone; only light passes.")]},
                                     {"id": "slumber", "label": "Slumber", "effects": [cond("unconscious", note="Can't be awoken.")]}]}],
                         target=creatures(must_see=True), note="On a success, immune to this spell for 24 hours.")),
        ("**Burial.**", "sys", ["/effects/0/on_fail/1/options/0"]),
        ("**Chaining.**", "sys", ["/effects/0/on_fail/1/options/1"]),
        ("**Hedged Prison.**", "sys", ["/effects/0/on_fail/1/options/2"]),
        ("**Minimus Containment.**", "sys", ["/effects/0/on_fail/1/options/3"]),
        ("**Slumber.**", "sys", ["/effects/0/on_fail/1/options/4"]),
        ("***Ending the Spell.***", "md", md("imprisonment_trigger", "Does the GM agree the ending trigger is likely within a decade, and has it occurred?",
                                            "The trigger can be as simple or as elaborate as you choose, but the GM must agree that it has a high likelihood of happening within the next decade.")),
        ("A *Dispel Magic* spell", "rule", {"id": "dispel", "spell": SP("dispel-magic"), "slot_level": 9,
                                            "targets": ["prison", "component"]})]))
    E.append(S("Mass Heal", [("^", "fx", [
        heal(700, target=creatures(must_see=True), note="Up to 700 Hit Points divided among any number of creatures you can see."),
        {"op": "remove_condition", "conditions": [C("blinded"), C("deafened"), C("poisoned")], "target": INHERIT}])]))
    E.append(S("Meteor Swarm", [
        ("^", "fx", save("dex", [dmg("20d6", "fire"), dmg("20d6", "bludgeoning")], half=True,
                         target={"kind": "area", "area": {"shape": "sphere", "size_feet": 40, "origin": "point"}, "range": "@range",
                                 "count": 4, "must_see": True},
                         note="A creature in more than one Sphere is affected only once.")),
        ("A nonmagical object", "rule", {"id": "objects", "nonmagical_objects_take_damage": True, "flammable_ignite": "dnd5e/hazard/burning"})]))
    E.append(S("Power Word Heal", [
        ("^", "fx", [{"op": "modifier", "stat": "hp", "mode": "set", "value": {"var": "hp_max"}, "target": creatures(must_see=True)},
                     {"op": "remove_condition", "conditions": [C(c) for c in ("charmed", "frightened", "paralyzed", "poisoned", "stunned")],
                      "target": INHERIT},
                     {"op": "activation", "cost": "reaction", "then": [{"op": "remove_condition", "conditions": [C("prone")]}],
                      "note": "The target can use its Reaction to stand up."}])]))
    E.append(S("Power Word Kill", [("^", "fx", {"op": "choice", "id": "by_hp", "choose": 1, "chooser": "gm", "target": creatures(must_see=True),
                                                "options": [
        {"id": "dies", "label": "100 Hit Points or fewer", "effects": [{"op": "modifier", "stat": "hp", "mode": "set", "value": 0,
                                                                        "note": "It dies."}]},
        {"id": "damage", "label": "More than 100 Hit Points", "effects": [dmg("12d12", "psychic")]}]})]))
    E.append(S("Prismatic Wall", [
        ("^", "rule", {"id": "wall", "shapes": [{"length_feet": 90, "height_feet": 30, "thickness_inches": 1}, {"globe_diameter_feet": 30}],
                       "opaque": True, "fails_if_in_occupied_space": True}),
        ("The wall sheds Bright Light", "fx", {"op": "trigger", "event": {"event": "enters_or_starts_turn_in_area"}, "duration": "@duration",
                                               "condition": {"pred": "can_see_effect"},
                                               "then": [save("con", cond("blinded", {"kind": "minutes", "amount": 1}), target=INHERIT)],
                                               "note": "Within 20 feet; you and designated creatures are unaffected."}),
        ("The wall sheds Bright Light", "rule", {"id": "light", "light": light(100, 100)}),
        ("The wall consists of seven layers", "fx", {"op": "trigger", "event": {"event": "passes_through_effect"}, "duration": "@duration",
                                                     "then": [{"op": "repeat", "times": 7, "then": [
                                                         {"op": "choice", "id": "layer", "choose": 1, "chooser": "gm", "options": prismatic_layers(),
                                                          "note": "One layer at a time, in order."}]}]}),
        ("The wall, which has AC 10", "rule", {"id": "destruction", "ac": 10, "order": "red_to_violet",
                                               "antimagic_field": False, "dispel_magic": "violet_only"}),
        ("##### Prismatic Layers", "table", tab("Prismatic Layers", ["Order", "Effects"]))]))
    E.append(S("Shapechange", [
        ("^", "fx", [{"op": "transform", "into": {"exclude_creature_types": ["construct", "undead"],
                                                  "predicate": {"pred": "cr_at_most_target"}},
                      "keeps": ["creature_type", "alignment", "personality", "ability_score.int", "ability_score.wis", "ability_score.cha",
                                "hp", "hit_point_dice", "proficiencies", "languages", "spellcasting"],
                      "target": SELF, "duration": "@duration", "note": "A creature you have seen; CR no higher than your level or CR."},
                     {"op": "activation", **MAGIC, "then": [ref(SP("shapechange"), note="Shift into a different eligible form.")]}]),
        ("When you cast the spell, you gain", "fx", {"op": "temp_hp", "amount": {"var": "form_hp"}, "note": "Vanish when the spell ends."}),
        ("Your game statistics are replaced", "sys", ["/effects/0"]),
        ("Your game statistics are replaced", "ref", ["dnd5e/rule/shape-shifting"]),
        ("Upon shape-shifting", "rule", {"id": "equipment", "choose": ["drops", "resizes_to_fit"]})]))
    E.append(S("Storm of Vengeance", [
        ("^", "fx", save("con", [dmg("2d6", "thunder"), cond("deafened")], target=area("cylinder", 300))),
        ("At the start of each of your later turns", "rule", {"id": "rounds", "by_turn": True}),
        ("***Turn 2.***", "fx", dmg("4d6", "acid", target=area("cylinder", 300), note="Each creature and object under the cloud.")),
        ("***Turn 3.***", "fx", save("dex", dmg("10d6", "lightning"), half=True,
                                    target={"kind": "creature_or_object", "count": 6, "distinct": True},
                                    note="Six different creatures or objects beneath the cloud.")),
        ("***Turn 4.***", "fx", dmg("2d6", "bludgeoning", target=area("cylinder", 300))),
        ("***Turns 5–10.***", "fx", [dmg("1d6", "cold", target=area("cylinder", 300)),
                                     {"op": "restrict", "restrictions": ["ranged_weapon_attacks"], "duration": "@duration"}]),
        ("***Turns 5–10.***", "rule", {"id": "late_turns", "difficult_terrain": True, "heavily_obscured": True, "strong_wind": True})]))
    E.append(S("Time Stop", [
        ("^", "fx", {"op": "repeat", "times": {"op": "add", "args": ["1d4", 1]},
                     "then": [ref("dnd5e/rule/the-order-of-combat", note="You take a turn; no time passes for others.")]}),
        ("This spell ends if one of the actions", "rule", {"id": "ends", "affecting_others_ends": True, "max_distance_feet": 1000})]))
    E.append(S("True Polymorph", [
        ("^", "fx", save("wis", ref(SP("true-polymorph"), note="Transformation according to the chosen kind."),
                         target={"kind": "creature_or_object", "range": "@range", "must_see": True},
                         note="Only an unwilling creature saves; an object must be neither worn nor carried.")),
        ("^", "rule", {"id": "duration", "ends_on": ["target_dies_or_destroyed"], "full_concentration": "until_dispelled"}),
        ("***Creature into Creature.***", "fx", {"op": "transform", "into": {"predicate": {"pred": "cr_at_most_target"}},
                                                "keeps": ["hp", "hit_point_dice", "alignment", "personality"], "duration": "@duration"}),
        ("The target gains a number of Temporary Hit Points", "fx", {"op": "temp_hp", "amount": {"var": "form_hp"}, "note": "Vanish when the spell ends."}),
        ("The target is limited in the actions", "fx", {"op": "restrict", "restrictions": ["speak", "cast_spells"], "duration": "@duration"}),
        ("The target’s gear melds", "rule", {"id": "gear", "melds": True, "usable": False}),
        ("***Object into Creature.***", "rule", {"id": "object_into_creature", "size_at_most_object": True, "max_cr": 9,
                                                "attitude": "dnd5e/attitude/friendly", "turn_after_yours": True, "obeys": True}),
        ("If the spell lasts more than an hour", "md", md("control_lost", "Does the creature remain Friendly once you lose control?",
                                                          "It might remain Friendly to you, depending on how you have treated it.", reason="narrative")),
        ("***Creature into Object.***", "rule", {"id": "creature_into_object", "size_at_most_creature": True, "statistics_of_object": True,
                                                "no_memory": True})]))
    E.append(S("True Resurrection", [
        ("^", "fx", {"op": "modifier", "stat": "hp", "mode": "set", "value": {"var": "hp_max"}, "target": touch(),
                     "note": "Dead no longer than 200 years, for any reason except old age."}),
        ("This spell closes all wounds", "rule", {"id": "restoration", "closes_wounds": True, "neutralizes_poison": True,
                                                  "cures_magical_contagions": True, "lifts_curses": True, "restores_organs_and_limbs": True,
                                                  "undead_restored": True}),
        ("The spell can provide a new body", "rule", {"id": "new_body", "speak_name": True, "appears_within_feet": 10})]))
    E.append(S("Weird", [
        ("^", "fx", save("wis", [dmg("10d10", "psychic"), cond("frightened")], target=area("sphere", 30),
                         on_success=dmg({"op": "div", "args": ["10d10", 2]}, "psychic", note="Half damage only."))),
        ("A Frightened target makes", "fx", {"op": "trigger", "event": {"event": "turn_end", "whose": "target", "which": "each"},
                                             "duration": "@duration",
                                             "then": [save("wis", dmg("5d10", "psychic"), target=INHERIT,
                                                           on_success={"op": "end_effect", "scope": "this_entry_on_target"})]})]))
    wish_opts = {"op": "choice", "id": "wish", "choose": 1, "options": [
        {"id": "duplicate", "label": "Duplicate a spell", "effects": [ref(SP("wish"), note="Any spell of level 8 or lower, with no requirements.")]},
        {"id": "object_creation", "label": "Object Creation", "effects": [ref(SP("wish"), note="A nonmagical object worth up to 25,000 GP, no more than 300 feet in any dimension.")]},
        {"id": "instant_health", "label": "Instant Health", "effects": [
            {"op": "modifier", "stat": "hp", "mode": "set", "value": {"var": "hp_max"}, "target": creatures(21, must_see=True)},
            ref(SP("greater-restoration"), note="End all effects listed in Greater Restoration.")]},
        {"id": "resistance", "label": "Resistance", "effects": [
            {"op": "defense", "kind": "resistance", "damage_types": [{"var": "chosen.damage_type"}], "target": creatures(10, must_see=True),
             "duration": {"kind": "permanent"}}]},
        {"id": "spell_immunity", "label": "Spell Immunity", "effects": [
            ref(SP("wish"), target=creatures(10, must_see=True), duration={"kind": "hours", "amount": 8},
                note="Immunity to a single spell or other magical effect.")]},
        {"id": "sudden_learning", "label": "Sudden Learning", "effects": [ref(SP("wish"), note="Replace one feat with another you're eligible for.")]},
        {"id": "roll_redo", "label": "Roll Redo", "effects": [{"op": "reroll", "rolls": ["any_die"], "keep": "choice",
                                                               "note": "A roll made within the last round; with Advantage or Disadvantage if you choose."}]},
        {"id": "reshape_reality", "label": "Reshape Reality", "effects": [{"op": "master_decision", "decision": "reshape_reality"}]}]}
    E.append(S("Wish", [
        ("^", "desc", None),
        ("The basic use of this spell", "fx", wish_opts),
        ("Alternatively, you can create one", "desc", None),
        ("**Object Creation.**", "sys", ["/effects/0/options/1"]),
        ("**Instant Health.**", "sys", ["/effects/0/options/2"]),
        ("**Resistance.**", "sys", ["/effects/0/options/3"]),
        ("**Spell Immunity.**", "sys", ["/effects/0/options/4"]),
        ("**Sudden Learning.**", "sys", ["/effects/0/options/5"]),
        ("**Sudden Learning.**", "rule", {"id": "sudden_learning", "cannot_replace_prerequisite_feat": True}),
        ("**Roll Redo.**", "sys", ["/effects/0/options/6"]),
        ("**Reshape Reality.**", "md", md("reshape_reality", "What happens with the wish as stated?",
                                          "The GM has great latitude in ruling what occurs in such an instance; the greater the wish, the greater the likelihood that something goes wrong. This spell might simply fail, the effect you desire might be achieved only in part, or you might suffer an unforeseen consequence as a result of how you worded the wish.")),
        ("The stress of casting *Wish*", "fx", [
            {"op": "trigger", "event": {"event": "casts_spell"}, "target": SELF,
             "duration": {"kind": "until_event", "until": {"event": "long_rest_finished"}},
             "then": [dmg({"dice": {"count": {"var": "spell_level"}, "faces": 10}}, "necrotic", note="Can't be reduced or prevented.")]},
            {"op": "modifier", "stat": "ability_score.str", "mode": "set", "value": 3, "target": SELF,
             "duration": {"kind": "days", "amount": "2d4"}, "note": "Each day of rest and light activity reduces the remaining time by 2 days."}]),
        ("The stress of casting *Wish*", "rule", {"id": "stress", "applies_when": "not_duplicating_a_spell", "lose_wish_chance_percent": 33})]))
    return E


REGISTRY = {
    "restrictions": [{"id": "ranged_weapon_attacks", "description": "Ranged attacks with weapons are impossible.", "pages": [165]}],
    "events": [{"id": "passes_through_effect", "description": "A creature reaches into or passes through the effect.", "pages": [155]}],
    "predicates": [{"id": "can_see_effect", "description": "The creature can see the effect.", "type": "predicate", "pages": [155]}],
}

if __name__ == "__main__":
    write_all(entries(), REGISTRY, LOT)
