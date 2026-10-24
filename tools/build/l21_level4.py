#!/usr/bin/env python3
"""L21 — Level 4 spells (34) and the Giant Insect stat block.

Usage: python3 -I tools/build/l21_level4.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spelllib import (BLOCKED, C, DC, EACH_END, INHERIT, MAGIC, MOD, SELF, SLOT, SP, STUDY, S_for, active,  # noqa: E402
                      all_but, area, attack, cond, creatures, dmg, extra_targets, heal, light, md, ref, save, touch,
                      until_turn, up, updice, write_all)
from statblock import creature_entry  # noqa: E402

LOT = "L21"
S = S_for(LOT)
HL = "***Using a Higher-Level Spell Slot.***"
SL = {"var": "spell_level"}


def entries():
    E = []
    E.append(S("Arcane Eye", [
        ("^", "rule", {"id": "eye", "invisible": True, "invulnerable": True, "hovers": True, "sees_all_directions": True,
                       "darkvision_feet": 30, "you_receive_visual_information": True}),
        ("As a Bonus Action, you can move the eye", "fx", {"op": "activation", "cost": "bonus_action", "then": [
            {"op": "move", "mode": "move", "distance_feet": 30, "note": "The eye, in any direction; blocked by solid barriers; passes 1-inch openings."}]})]))
    E.append(S("Aura of Life", [("^", "fx", [
        {"op": "defense", "kind": "resistance", "damage_types": ["necrotic"], "target": area("emanation", 30, "self", allies_only=True),
         "duration": "@duration", "note": "You and your allies in the aura."},
        {"op": "restrict", "restrictions": ["hp_max_reduced"], "target": area("emanation", 30, "self", allies_only=True),
         "duration": "@duration"},
        {"op": "trigger", "event": {"event": "turn_start", "whose": "any"}, "duration": "@duration",
         "condition": {"all": [{"pred": "is_ally"}, {"pred": "at_zero_hp"}, {"pred": "in_spell_area"}]},
         "then": [heal(1, target=INHERIT)]}])]))
    E.append(S("Banishment", [
        ("^", "fx", save("cha", [cond("incapacitated", note="Transported to a harmless demiplane for the duration; reappears in its space or the nearest unoccupied one.")],
                         target=creatures(extra_targets(4), must_see=True))),
        ("If the target is an Aberration", "rule", {"id": "permanent", "creature_types": ["aberration", "celestial", "elemental", "fey", "fiend"],
                                                    "if_full_duration_minutes": 1, "sent_to": "plane_associated_with_type"}),
        ("If the target is an Aberration", "md", md("banishment_plane", "To which location on the associated plane is the target sent?",
                                                    "The target is instead transported to a random location on a plane (GM’s choice) associated with its creature type.")),
        (HL, "sys", ["/effects/0/target/count"])]))
    E.append(S("Black Tentacles", [
        ("^", "rule", {"id": "terrain", "area_square_feet": 20, "difficult_terrain": True}),
        ("Each creature in that area makes", "fx", [
            save("str", [dmg("3d6", "bludgeoning"), cond("restrained")], target=area("cube", 20)),
            {"op": "trigger", "event": {"event": "enters_or_ends_turn_in_area"}, "frequency": {"count": 1, "per": "turn"},
             "duration": "@duration", "then": [save("str", [dmg("3d6", "bludgeoning"), cond("restrained")], target=INHERIT)]}]),
        ("A Restrained creature can take an action", "fx", {"op": "activation", "cost": "action", "then": [
            {"op": "check", "ability": "str", "skill": "athletics", "dc": DC,
             "on_success": [{"op": "remove_condition", "conditions": [C("restrained")]}]}]})]))
    E.append(S("Blight", [
        ("^", "fx", save("con", dmg(updice(8, 8, 4), "necrotic"), half=True, target=creatures(must_see=True),
                         note="A Plant creature automatically fails the save.")),
        ("Alternatively, target a nonmagical plant", "rule", {"id": "plant", "nonmagical_plant_withers": True, "no_save": True}),
        (HL, "sys", ["/effects/0/on_fail/0/amount"])]))
    E.append(S("Charm Monster", [
        ("^", "fx", save("wis", cond("charmed"), target=creatures(extra_targets(4), must_see=True))),
        ("^", "rule", {"id": "details", "save_advantage_if_fighting": True, "ends_on": "you_or_allies_damage_it",
                       "attitude": "dnd5e/attitude/friendly", "knows_afterwards": True}),
        (HL, "sys", ["/effects/0/target/count"])]))
    E.append(S("Compulsion", [
        ("^", "fx", save("wis", cond("charmed"), target=creatures(must_see=True), note="Each creature of your choice within range.")),
        ("For the duration, you can take a Bonus Action", "fx", {"op": "activation", "cost": "bonus_action", "then": [
            {"op": "move", "mode": "move", "note": "Each Charmed target uses as much movement as possible in the designated horizontal direction on its next turn, by the safest route."},
            save("wis", None, target=INHERIT, on_success={"op": "end_effect", "scope": "this_entry_on_target"},
                 note="After moving this way.")]})]))
    confusion = [["1", "The target doesn’t take an action, and it uses all its movement to move. Roll 1d4 for the direction: 1, north; 2, east; 3, south; or 4, west."],
                 ["2–6", "The target doesn’t move or take actions."],
                 ["7–8", "The target doesn’t move, and it takes the Attack action to make one melee attack against a random creature within reach. If none are within reach, the target takes no action."],
                 ["9–10", "The target chooses its behavior."]]
    E.append(S("Confusion", [
        ("^", "fx", save("wis", [{"op": "restrict", "restrictions": ["take_bonus_actions", "take_reactions"], "duration": "@duration"},
                                 {"op": "trigger", "event": {"event": "turn_start", "whose": "target", "which": "each"}, "duration": "@duration",
                                  "then": [{"op": "choice", "id": "behavior", "choose": 1, "chooser": "random", "options": [
                                      {"id": "wander", "label": "Move randomly", "roll": "1", "effects": [
                                          {"op": "move", "mode": "move", "note": "All its movement; 1d4 for direction: north, east, south, west."}]},
                                      {"id": "nothing", "label": "No move or action", "roll": "2-6", "effects": [
                                          {"op": "restrict", "restrictions": ["move", "take_actions"]}]},
                                      {"id": "attack", "label": "Attack a random creature", "roll": "7-8", "effects": [
                                          attack("melee", note="One melee attack against a random creature within reach, if any.")]},
                                      {"id": "free", "label": "Chooses its behavior", "roll": "9-10", "effects": []}]}]}],
                         target=area("sphere", up(10, 4, 5)), repeat=EACH_END)),
        ("| **1d10**", "table", {"id": "confusion_behavior", "caption": "Confusion behavior",
                                "columns": ["1d10", "Behavior for the Turn"], "rows": confusion}),
        ("At the end of each of its turns", "sys", ["/effects/0/repeat"]),
        (HL, "sys", ["/effects/0/target/area/size_feet"])]))
    E.append(S("Conjure Minor Elementals", [
        ("^", "fx", {"op": "trigger", "event": {"event": "hits_with_attack_roll"}, "duration": "@duration",
                     "condition": {"pred": "target_in_area"},
                     "then": [dmg(updice(2, 8, 4), ["acid", "cold", "fire", "lightning"], target=INHERIT)]}),
        ("^", "rule", {"id": "emanation", "size_feet": 15}),
        ("In addition, the ground in the Emanation", "rule", {"id": "terrain", "difficult_for": "enemies"}),
        (HL, "sys", ["/effects/0/then/0/amount"])]))
    E.append(S("Conjure Woodland Beings", [
        ("^", "fx", {"op": "trigger", "event": {"event": "creature_within_feet_of_effect"}, "optional": True,
                     "frequency": {"count": 1, "per": "turn"}, "duration": "@duration",
                     "then": [save("wis", dmg(updice(5, 8, 4), "force"), half=True, target=INHERIT)],
                     "note": "10-foot Emanation; a creature you can see."}),
        ("In addition, you can take the Disengage action", "fx", {"op": "activation", "cost": "bonus_action", "duration": "@duration",
                                                                  "then": [ref("dnd5e/action/disengage")]}),
        (HL, "sys", ["/effects/0/then/0/on_fail/0/amount"])]))
    E.append(S("Control Water", [
        ("^", "rule", {"id": "area", "cube_feet_max": 100, "repeat_or_change": "dnd5e/action/magic"}),
        ("***Flood.***", "rule", {"id": "flood", "rise_feet": 20, "large_body": {"wave_feet": 20, "vehicles_max_size": "huge",
                                                                                 "capsize_percent": 25}}),
        ("The water level remains elevated", "rule", {"id": "flood_duration", "until": ["spell_ends", "other_effect_chosen"],
                                                      "wave_repeats": "start_of_your_next_turn"}),
        ("***Part Water.***", "rule", {"id": "part_water", "trench": True, "refills_over_rounds": 1}),
        ("***Redirect Flow.***", "rule", {"id": "redirect_flow", "direction": "chosen", "outside_area_resumes": True}),
        ("***Whirlpool.***", "fx", [
            {"op": "move", "mode": "pull", "distance_feet": 10, "note": "Creatures in the water within 25 feet of the whirlpool."},
            {"op": "trigger", "event": {"event": "enters_or_ends_turn_in_area"}, "frequency": {"count": 1, "per": "turn"},
             "then": [save("str", dmg("2d8", "bludgeoning"), half=True, target=INHERIT)]}]),
        ("***Whirlpool.***", "rule", {"id": "whirlpool", "min_area_square_feet": 50, "min_depth_feet": 25, "base_feet": 5,
                                     "top_feet": 50, "height_feet": 25,
                                     "swim_away": {"action": True, "check": {"ability": "str", "skill": "athletics", "dc": "spell_save_dc"}}})]))
    E.append(S("Death Ward", [
        ("^", "fx", {"op": "trigger", "event": {"event": "would_drop_to_0_hp"}, "target": touch(), "duration": "@duration",
                     "then": [{"op": "modifier", "stat": "hp", "mode": "set", "value": 1}, {"op": "end_effect", "scope": "this_entry"}]}),
        ("If the spell is still in effect", "fx", {"op": "trigger", "event": {"event": "instant_death_effect"}, "duration": "@duration",
                                                   "then": [ref(SP("death-ward"), note="The effect is negated."),
                                                            {"op": "end_effect", "scope": "this_entry"}]})]))
    E.append(S("Dimension Door", [
        ("^", "fx", {"op": "move", "mode": "teleport", "distance_feet": 500, "target": SELF,
                     "note": "A place you can see, visualize, or describe by distance and direction."}),
        ("You can also teleport one willing creature", "rule", {"id": "passenger", "count": 1, "within_feet": 5, "arrives_within_feet": 5}),
        ("If you, the other creature, or both", "fx", {"op": "trigger", "event": {"event": "teleport_destination_occupied"},
                                                       "then": [dmg("4d6", "force", note="You and any creature traveling with you; the teleportation fails.")]})]))
    E.append(S("Divination", [
        ("^", "md", md("divination_answer", "What truthful reply does the GM give?",
                       "The GM offers a truthful reply, which might be a short phrase or cryptic rhyme.", reason="narrative")),
        ("^", "rule", {"id": "question", "count": 1, "within_days": 7, "ignores_changing_circumstances": True}),
        ("If you cast the spell more than once", "rule", {"id": "repeat_casting", "no_answer_chance_percent": {
            "op": "mul", "args": [25, {"var": "uses_since_rest.divination"}]}, "reset_on": "long_rest_finished"})]))
    E.append(S("Dominate Beast", [
        ("^", "fx", [save("wis", cond("charmed"), target=creatures(must_see=True, creature_types=["beast"]),
                          note="Advantage if you or your allies are fighting it."),
                     {"op": "trigger", "event": {"event": "damage_taken", "whose": "target"}, "duration": "@duration",
                      "then": [save("wis", None, target=INHERIT, on_success={"op": "end_effect", "scope": "this_entry"})]}]),
        ("You have a telepathic link", "rule", {"id": "commands", "telepathic_link": "same_plane", "command_cost": "none",
                                                "obeys_on_its_turn": True, "idle": "protects_itself"}),
        ("You can command the target to take a Reaction", "rule", {"id": "reaction", "costs_your_reaction": True}),
        (HL, "rule", {"id": "longer_concentration", "max_duration_minutes": {"scale": {"by": "spell_slot_level", "steps": [
            {"from": 4, "value": 1}, {"from": 5, "value": 10}, {"from": 6, "value": 60}, {"from": 7, "value": 480}]}}})]))
    E.append(S("Fabricate", [
        ("^", "rule", {"id": "convert", "same_material": True}),
        ("Choose raw materials", "rule", {"id": "size", "max": "large", "cube_feet": 10, "or_connected_5_foot_cubes": 8,
                                          "mineral_max": "medium", "quality_from_materials": True}),
        ("Creatures and magic items can’t be created", "rule", {"id": "limits", "no_creatures_or_magic_items": True,
                                                                "skilled_items_require": "artisans_tools_proficiency"})]))
    E.append(S("Faithful Hound", [
        ("^", "rule", {"id": "hound", "ends_if_farther_than_feet": 300}),
        ("No one but you can see the hound", "rule", {"id": "watch", "visible_only_to_you": True, "intangible": True, "invulnerable": True,
                                                      "barks_at": "small_or_larger_within_30_feet_without_password", "truesight_feet": 30}),
        ("At the start of each of your turns", "fx", {"op": "trigger", "event": {"event": "turn_start", "whose": "self", "which": "each"},
                                                      "duration": "@duration",
                                                      "then": [save("dex", dmg("4d8", "force"), target={"kind": "creature"},
                                                                    note="One enemy within 5 feet of the hound.")]}),
        ("On your later turns, you can take a Magic action", "fx", {"op": "activation", **MAGIC, "then": [
            {"op": "move", "mode": "move", "distance_feet": 30, "note": "The hound."}]})]))
    E.append(S("Fire Shield", [
        ("^", "rule", {"id": "light", "light": light(10, 10)}),
        ("The flames provide you", "fx", {"op": "choice", "id": "shield", "choose": 1, "options": [
            {"id": "warm", "label": "Warm shield", "value": "fire", "effects": [
                {"op": "defense", "kind": "resistance", "damage_types": ["cold"], "duration": "@duration"}]},
            {"id": "chill", "label": "Chill shield", "value": "cold", "effects": [
                {"op": "defense", "kind": "resistance", "damage_types": ["fire"], "duration": "@duration"}]}]}),
        ("In addition, whenever a creature within 5 feet", "fx", {
            "op": "trigger", "event": {"event": "hit_by_melee_attack_within_feet.5"}, "duration": "@duration",
            "then": [dmg("2d8", {"var": "chosen.shield"}, target=INHERIT, note="Fire (warm shield) or Cold (chill shield).")]})]))
    E.append(S("Freedom of Movement", [
        ("^", "fx", [{"op": "modifier", "stat": "ignores_difficult_terrain", "mode": "set", "value": 1, "target": touch(willing=True),
                      "duration": "@duration"},
                     {"op": "restrict", "restrictions": ["speed_reduced_by_magic"], "duration": "@duration"},
                     {"op": "defense", "kind": "immunity", "conditions": [C("paralyzed"), C("restrained")], "duration": "@duration",
                      "note": "Against spells and other magical effects."},
                     {"op": "speed", "movement": "swim", "mode": "equal_to_walk", "value": 0, "duration": "@duration"}]),
        ("In addition, the target can spend 5 feet", "fx", {"op": "activation", "cost": "none", "movement_cost": 5,
                                                           "then": [ref("dnd5e/rule/grappling", note="Escape nonmagical restraints or the Grappled condition.")]}),
        (HL, "rule", {"id": "targets", "count": extra_targets(4)})]))
    E.append(S("Giant Insect", [
        ("^", "fx", {"op": "choice", "id": "insect", "choose": 1, "options": [
            {"id": f, "label": f.title(), "effects": [{"op": "summon", "creature": "dnd5e/creature/giant-insect",
                                                       "controller": "summoner", "initiative": "after_summoner"}]}
            for f in ("centipede", "spider", "wasp")], "note": "Disappears at 0 Hit Points or when the spell ends."}),
        ("The creature is an ally", "rule", {"id": "ally", "obeys_verbal_commands": True, "idle": "dnd5e/action/dodge"}),
        (HL, "rule", {"id": "stat_block_level", "spell_level_in_stat_block": SLOT})]))
    E.append(S("Greater Invisibility", [("^", "fx", cond("invisible", target=touch()))]))
    E.append(S("Guardian of Faith", [
        ("^", "rule", {"id": "guardian", "size": "large", "invulnerable": True, "occupies_space": True}),
        ("Any enemy that moves to a space within 10 feet", "fx", {
            "op": "trigger", "event": {"event": "enters_or_starts_turn_in_area"}, "frequency": {"count": 1, "per": "turn"},
            "condition": {"pred": "is_enemy"}, "duration": "@duration",
            "then": [save("dex", dmg(20, "radiant"), half=True, target=INHERIT)]}),
        ("Any enemy that moves to a space within 10 feet", "rule", {"id": "limit", "vanishes_after_total_damage": 60})]))
    E.append(S("Hallucinatory Terrain", [
        ("^", "rule", {"id": "illusion", "cube_feet": 150, "senses": ["sight", "sound", "smell"], "natural_terrain_only": True,
                       "structures_equipment_creatures_unchanged": True}),
        ("The tactile characteristics", "fx", STUDY),
        ("The tactile characteristics", "rule", {"id": "touch", "tactile_unchanged": True, "discerned": "vague_image_superimposed"})]))
    E.append(S("Ice Storm", [
        ("^", "fx", save("dex", [dmg(updice(2, 10, 4), "bludgeoning"), dmg("4d6", "cold")], half=True, target=area("cylinder", 20))),
        ("^", "rule", {"id": "cylinder", "radius_feet": 20, "height_feet": 40}),
        ("Hailstones turn ground", "rule", {"id": "terrain", "difficult_terrain_until": "end_of_your_next_turn"}),
        (HL, "sys", ["/effects/0/on_fail/0/amount"])]))
    E.append(S("Locate Creature", [
        ("^", "rule", {"id": "locate", "range_feet": 1000, "learns": ["direction", "movement_direction"]}),
        ("The spell can locate a specific creature", "rule", {"id": "known", "seen_within_feet": 30, "or": "nearest_of_kind",
                                                              "fails_on_different_form": [SP("flesh-to-stone"), SP("polymorph")]}),
        ("This spell can’t locate a creature", "rule", {"id": "blocked", "blocked_by": "any_thickness_of_lead"})]))
    E.append(S("Phantasmal Killer", [
        ("^", "fx", save("wis", [dmg(updice(4, 10, 4), "psychic"),
                                 {"op": "roll_mode", "mode": "disadvantage", "rolls": ["ability_check", "attack_roll"], "duration": "@duration"}],
                         half=True, target=creatures(must_see=True), on_success={"op": "end_effect", "scope": "this_entry"})),
        ("For the duration, the target makes", "fx", {"op": "trigger", "event": {"event": "turn_end", "whose": "target", "which": "each"},
                                                      "duration": "@duration",
                                                      "then": [save("wis", dmg(updice(4, 10, 4), "psychic"), target=INHERIT,
                                                                    on_success={"op": "end_effect", "scope": "this_entry"})]}),
        (HL, "sys", ["/effects/0/on_fail/0/amount", "/effects/1/then/0/on_fail/0/amount"])]))
    E.append(S("Polymorph", [
        ("^", "fx", save("wis", [{"op": "transform", "into": {"creature_types": ["beast"], "predicate": {"pred": "cr_at_most_target"}},
                                  "keeps": ["alignment", "personality", "creature_type", "hp", "hit_point_dice"], "duration": "@duration"},
                                 {"op": "temp_hp", "amount": {"var": "form_hp"}}], target=creatures(must_see=True))),
        ("^", "ref", ["dnd5e/rule/shape-shifting"]),
        ("The target gains a number of Temporary Hit Points", "rule", {"id": "temp_hp", "vanish_on_end": True,
                                                                       "ends_when_temp_hp_gone": True}),
        ("The target is limited in the actions", "fx", {"op": "restrict", "restrictions": ["speak", "cast_spells"], "duration": "@duration",
                                                        "note": "Actions limited by the new form's anatomy."}),
        ("The target’s gear melds", "rule", {"id": "gear", "melds": True, "usable": False})]))
    E.append(S("Private Sanctum", [
        ("^", "rule", {"id": "area", "cube_feet_min": 5, "cube_feet_max": up(100, 4, 100)}),
        ("When you cast the spell, you decide", "rule", {"id": "properties", "choose_any_of": [
            "block_sound", "block_vision", "block_divination_sensors", "block_divination_targeting", "block_teleportation",
            "block_planar_travel"]}),
        ("Casting this spell on the same spot", "rule", {"id": "permanent", "daily_castings": 365, "then": "until_dispelled"}),
        (HL, "sys", ["rule:area"])]))
    E.append(S("Resilient Sphere", [
        ("^", "fx", save("dex", ref(SP("resilient-sphere"), note="Enclosed for the duration."),
                         target={"kind": "creature_or_object", "range": "@range", "filter": {"sizes": ["tiny", "small", "medium", "large"]}},
                         note="Only an unwilling creature saves.")),
        ("Nothing—not physical objects", "rule", {"id": "barrier", "impassable": True, "breathable": True, "immune_to_damage": True,
                                                   "no_damage_across": True}),
        ("The sphere is weightless", "rule", {"id": "movement", "roll_with_action_speed_fraction": 0.5, "can_be_carried": True}),
        ("A *Disintegrate* spell", "rule", {"id": "disintegrate", "spell": SP("disintegrate"), "destroys_globe_harmlessly": True})]))
    E.append(S("Secret Chest", [
        ("^", "rule", {"id": "chest", "plane": "ethereal", "capacity_cubic_feet": 12, "dimensions_feet": [3, 2, 2],
                       "requires_touching_chest_and_replica": True}),
        ("While the chest remains on the Ethereal Plane", "fx", {"op": "activation", **MAGIC, "then": [
            ref(SP("secret-chest"), note="Recall the chest within 5 feet of you, or send it back.")]}),
        ("After 60 days", "rule", {"id": "end", "after_days": 60, "daily_end_chance_percent_cumulative": 5,
                                   "ends_on": ["cast_again", "replica_destroyed"], "chest_stays_on_ethereal": True})]))
    E.append(S("Stone Shape", [("^", "rule", {"id": "shape", "max_object_size": "medium", "max_section_feet": 5,
                                              "max_hinges": 2, "latch": True, "fine_mechanics": False})]))
    E.append(S("Stoneskin", [("^", "fx", {"op": "defense", "kind": "resistance", "damage_types": ["bludgeoning", "piercing", "slashing"],
                                          "target": touch(willing=True), "duration": "@duration"})]))
    E.append(S("Vitriolic Sphere", [
        ("^", "fx", save("dex", [dmg(updice(10, 4, 4, 2), "acid"),
                                 {"op": "trigger", "event": {"event": "turn_end", "whose": "target"}, "then": [dmg("5d4", "acid", target=INHERIT)]}],
                         target=area("sphere", 20),
                         on_success=dmg({"op": "div", "args": [updice(10, 4, 4, 2), 2]}, "acid", note="Half the initial damage only."))),
        (HL, "sys", ["/effects/0/on_fail/0/amount", "/effects/0/on_success/0/amount"])]))
    E.append(S("Wall of Fire", [
        ("^", "rule", {"id": "wall", "shapes": [{"length_feet": 60, "height_feet": 20, "thickness_feet": 1},
                                                {"ring_diameter_feet": 20, "height_feet": 20, "thickness_feet": 1}], "opaque": True}),
        ("When the wall appears", "fx", save("dex", dmg(updice(5, 8, 4), "fire"), half=True,
                                             target={"kind": "area", "area": {"shape": "line", "size_feet": 60, "origin": "point"}, "range": "@range"})),
        ("One side of the wall", "fx", {"op": "trigger", "event": {"event": "enters_or_ends_turn_near_wall"}, "duration": "@duration",
                                        "frequency": {"count": 1, "per": "turn"},
                                        "then": [dmg(updice(5, 8, 4), "fire", target=INHERIT,
                                                     note="Ends its turn within 10 feet of the chosen side or inside the wall, or enters the wall.")]}),
        (HL, "sys", ["/effects/0/on_fail/0/amount", "/effects/1/then/0/amount"])]))
    E.append(creature_entry("Giant Insect", 136, LOT, "Spells/Spell Descriptions/Giant Insect/Giant Insect",
                            overrides={"ac": {"value": {"op": "add", "args": [11, SL]}},
                                       "hp": {"value": {"op": "add", "args": [30, {"op": "mul", "args": [10, {"op": "sub", "args": [SL, 4]}]}]}},
                                       "speed": {"walk": 40, "climb": 40, "fly": 40, "fly_only": "wasp"},
                                       "summoned_by": SP("giant-insect")},
                            fx={"Multiattack": [{"op": "repeat", "times": {"op": "div", "args": [SL, 2]},
                                                 "then": [attack("melee", note="Poison Jab or Web Bolt.")]}],
                                "Poison Jab": [attack("melee", [dmg({"op": "add", "args": ["1d6", 3, SL]}, "piercing"), dmg("1d4", "poison")],
                                                      bonus={"var": "spell_attack_bonus"})],
                                "Web Bolt": [attack("ranged", [dmg({"op": "add", "args": ["1d10", 3, SL]}, "bludgeoning"),
                                                               {"op": "speed", "movement": "walk", "mode": "set", "value": 0,
                                                                "duration": until_turn("turn_start", "source")}],
                                                    bonus={"var": "spell_attack_bonus"})],
                                "Venomous Spew": [save("con", cond("poisoned", until_turn("turn_start", "source")))]}))
    return E


REGISTRY = {
    "variables": [{"id": "form_hp", "description": "Hit Points of the form a creature transformed into.", "type": "number", "pages": [153]}],
    "stats": [{"id": "ignores_difficult_terrain", "description": "The creature's movement is unaffected by Difficult Terrain.", "pages": [134]}],
    "restrictions": [
        {"id": "hp_max_reduced", "description": "The creature's Hit Point maximum can't be reduced.", "pages": [111]},
        {"id": "speed_reduced_by_magic", "description": "Spells and other magical effects can't reduce the creature's Speed.", "pages": [134]}],
    "events": [
        {"id": "would_drop_to_0_hp", "description": "The creature would drop to 0 Hit Points.", "pages": [122]},
        {"id": "instant_death_effect", "description": "The creature is subjected to an effect that would kill it instantly without dealing damage.", "pages": [122]},
        {"id": "teleport_destination_occupied", "description": "A teleporting creature would arrive in an occupied or filled space.", "pages": [124]},
        {"id": "hit_by_melee_attack_within_feet", "description": "A creature within N feet (param) hits the creature with a melee attack roll.", "params": ["feet"], "pages": [133]},
        {"id": "enters_or_ends_turn_near_wall", "description": "A creature ends its turn near the damaging side of the wall or inside it, or enters it.", "pages": [172]}],
    "predicates": [
        {"id": "cr_at_most_target", "description": "The form's Challenge Rating is at most the target's (or its level).", "type": "predicate", "pages": [153]}],
}

if __name__ == "__main__":
    write_all(entries(), REGISTRY, LOT)
