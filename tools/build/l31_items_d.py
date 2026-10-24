#!/usr/bin/env python3
"""L31 — Magic items A–Z, part 4 (Oathbow … Rod of Absorption; potions and oils are L32).

Usage: python3 -I tools/build/l31_items_d.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import extend_registries, write_entry  # noqa: E402
from magiclib import (ATTUNED, DAWN, HOLD, INHERIT, MI, SELF, SP, THIS, WEAR, WIELD, act, adv, area, cast,  # noqa: E402
                      charges, check, cond, creature, dmg, hours, item_nodes, md, mins, mod, ref, resist, rows_of,
                      save, sense, setv, speed, spells_table, tab, trig, until_turn, while_)
from l31_registry import REGISTRY  # noqa: E402

LOT = "L31"
EACH_END = {"on": {"event": "turn_end", "whose": "target", "which": "each"}, "ends": "effect_on_self"}
SWORN = {"pred": "target_is_marked"}
POSSESS = {"pred": "possesses_item", "args": THIS}


def plus_weapon(n):
    return [mod("attack_roll", n, WIELD), mod("damage_roll", n, WIELD)]


def lang(name):
    return {"op": "proficiency", "category": "language", "items": [name], "when": WEAR}


def spell_store(name, levels, found):
    return [
        ("^", "rule", {"id": "storage", "max_levels": levels, "found_with_levels": found}),
        ("^", "md", md("stored_spells", "Which spells are stored when found?", f"When found, it contains {found} levels of stored spells chosen by the GM.")),
        ("Any creature can cast a spell", "rule", {"id": "store", "spell_levels": [1, levels], "by_touch": True, "space": "slot level used",
                                                   "overflow": "expended without effect"}),
        ("While wearing this ring, you can cast any spell" if name == "ring" else "While this stone", "rule",
         {"id": "cast_stored", "uses_original": ["slot_level", "spell_save_dc", "spell_attack_bonus", "spellcasting_ability"], "frees_space": True})]


def entries():
    E = []
    E.append(MI("Oathbow", [
        ("^", "fx", trig("attack_roll_made", ref("dnd5e/magic-item/oathbow", note="Command words: the target becomes your sworn enemy until it dies or dawn 7 days later."),
                         optional=True, condition={"all": [{"pred": "attack_uses_weapon", "args": THIS}, {"not": {"pred": "has_marked_target"}}]})),
        ("^", "rule", {"id": "sworn_enemy", "max": 1, "ends": ["dies", "dawn_after_7_days"], "new_after": "next dawn after it dies"}),
        ("When you make a ranged attack roll", "fx", [
            adv("attack_roll", {"all": [{"pred": "attack_uses_weapon", "args": THIS}, SWORN]}),
            {"op": "restrict", "restrictions": ["cover_benefit_half_three_quarters", "long_range_disadvantage"],
             "when": {"all": [{"pred": "attack_uses_weapon", "args": THIS}, SWORN]}},
            trig("hits_with_attack_roll", dmg("3d6", "piercing", target=INHERIT), condition={"all": [{"pred": "attack_uses_weapon", "args": THIS}, SWORN]})]),
        ("While your sworn enemy lives", "fx", adv("attack_roll", {"all": [{"pred": "has_marked_target"},
                                                                           {"not": {"pred": "attack_uses_weapon", "args": THIS}}]}, mode="disadvantage"))]))
    E.append(MI("Pearl of Power", [
        ("^", "fx", act({"op": "restore", "resource": "spell_slot", "amount": 1, "level": {"op": "min", "args": [3, {"var": "spell_slot_level"}]},
                         "note": "One expended spell slot of level 3 or lower."}, freq=DAWN, requires=POSSESS))]))
    E.append(MI("Periapt of Health", [
        ("^", "fx", act({"op": "heal", "amount": {"op": "add", "args": ["2d4", 2]}}, freq=DAWN, requires=WEAR)),
        ("In addition, you have Advantage", "fx", adv("saving_throw", {"all": [WEAR, {"pred": "save_against_condition", "args": {"condition": "poisoned"}}]}))]))
    E.append(MI("Periapt of Proof against Poison", [
        ("^", "desc", None),
        ("While you wear it", "fx", [resist("poison", WEAR, kind="immunity"),
                                     {"op": "defense", "kind": "immunity", "conditions": ["dnd5e/condition/poisoned"], "when": WEAR}])]))
    E.append(MI("Periapt of Wound Closure", [
        ("^", "desc", None),
        ("***Life Preservation.***", "fx",
         {"op": "modifier", "stat": "d20_roll", "mode": "max", "value": 10,
          "when": {"all": [WEAR, {"pred": "roll_is", "args": {"roll": "death_saving_throw"}}]},
          "note": "You can change a roll of 9 or lower to a 10 (a success)."}),
        ("***Natural Healing Boost.***", "fx", {"op": "modifier", "stat": "healing_dice", "mode": "multiply", "value": 2,
                                                "when": {"all": [WEAR, {"pred": "roll_is", "args": {"roll": "hit_point_die"}}]}})]))
    E.append(MI("Pipes of Haunting", [
        ("^", "fx", [charges(3, "1d3"),
                     act(save("wis", 15, on_fail=cond("frightened", mins(1)), repeat=EACH_END,
                              target={"kind": "area", "area": {"shape": "emanation", "size_feet": 30, "origin": "self"},
                                      "filter": {"predicate": {"pred": "chosen_by_source"}}},
                              note="A creature that succeeds is immune to these pipes for 24 hours."), uses=1)])]))
    E.append(MI("Pipes of the Sewers", [
        ("^", "rule", {"id": "rats", "attitude": "indifferent", "creatures": ["dnd5e/creature/rat", "dnd5e/creature/giant-rat"],
                       "unless": "threatened or harmed", "while": "on your person"}),
        ("The pipes have 3 charges", "fx", [charges(3, "1d3"),
                                           act({"op": "summon", "creature": "dnd5e/creature/swarm-of-rats", "count": {"var": "charges_spent"},
                                                "controller": "none", "note": "If enough rats are within half a mile (GM); otherwise the charge is wasted."},
                                               cost="bonus_action", uses={"var": "charges_spent"},
                                               requires={"pred": "playing_item", "args": THIS})]),
        ("The pipes have 3 charges", "md", md("enough_rats", "Are enough rats within half a mile to form a swarm?",
                                              "if enough rats are within half a mile of you to be called in this fashion (as determined by the GM)")),
        ("Whenever a **Swarm of Rats**", "fx", trig({"event": "comes_within_feet_of_target", "whose": "any", "which": "each"},
                                                   save("wis", 15, on_fail=ref("dnd5e/magic-item/pipes-of-the-sewers", note="Friendly while you keep playing each round; obeys you; control ends if it starts its turn more than 30 feet away."),
                                                        on_success=ref("dnd5e/magic-item/pipes-of-the-sewers", note="Can't be swayed for 24 hours.")),
                                                   condition={"pred": "playing_item", "args": THIS}))]))
    E.append(MI("Plate Armor of Etherealness", [
        ("^", "fx", act(cast("Etherealness", note="Ends if you remove the armor or repeat the command word (Magic action)."), freq=DAWN, requires=WEAR))]))
    E.append(MI("Portable Hole", [
        ("^", "rule", {"id": "cloth", "unfolded_diameter_feet": 6}),
        ("You can take a Magic action to unfold", "fx", act(ref("dnd5e/magic-item/portable-hole", note="An extradimensional hole 10 feet deep on a solid surface; no open passages; climb out to exit."))),
        ("You can take a Magic action to close", "rule", {"id": "close", "cost": "dnd5e/action/magic", "contents_remain": True, "weight": "next to nothing"}),
        ("If the hole is folded up", "fx", check("str", 10, skill="athletics", on_success=ref("dnd5e/magic-item/portable-hole", note="Forces its way out within 5 feet."),
                                                 note="A creature inside a closed hole; takes an action.")),
        ("If the hole is folded up", "rule", {"id": "air", "hours": 1, "divided_by_breathers": True}),
        ("Placing a *Portable Hole*", "rule", {"id": "extradimensional_conflict", "with": ["dnd5e/magic-item/bag-of-holding", "dnd5e/magic-item/handy-haversack"],
                                               "both_destroyed": True, "gate": "astral_plane", "one_way": True}),
        ("Placing a *Portable Hole*", "fx", {"op": "move", "mode": "teleport", "target": area("emanation", 10, origin="point"),
                                             "when": {"not": {"pred": "behind_cover", "args": {"cover": "total"}}},
                                             "note": "Creatures within 10 feet of the gate and not behind Total Cover go to a random location on the Astral Plane."})]))
    E.append(MI("Quarterstaff of the Acrobat", [
        ("^", "fx", plus_weapon(2)),
        ("While holding this weapon, you can cause it to emit", "rule", {"id": "light", "dim_feet": 10, "on": ["bonus_action", "after_initiative"],
                                                                         "off": "bonus_action", "requires": "held"}),
        ("While holding this weapon, you can take a Bonus Action to alter", "rule", {"id": "forms", "cost": "bonus_action",
                                                                                     "forms": ["quarterstaff", "rod_6_inches", "pole_10_feet"],
                                                                                     "limited_by_space": True}),
        ("In certain forms", "desc", None),
        ("***Acrobatic Assist", "fx", adv("ability_check", {"all": [HOLD, {"pred": "item_form_in", "args": {"forms": ["quarterstaff", "pole_10_feet"]}},
                                                                     {"pred": "check_uses_skill", "args": {"skill": "acrobatics"}}]})),
        ("***Attack Deflection", "fx", trig("hit_by_attack_roll", mod("ac", 5, note="Against the triggering attack."), cost="reaction", optional=True,
                                            frequency={"count": 1, "per": "short_rest"},
                                            condition={"all": [HOLD, {"pred": "item_form_in", "args": {"forms": ["quarterstaff"]}}]})),
        ("***Ranged Weapon", "fx", {"op": "grant", "refs": ["dnd5e/weapon-property/thrown"],
                                    "when": {"all": [HOLD, {"pred": "item_form_in", "args": {"forms": ["quarterstaff"]}}]},
                                    "note": "Normal range 30 feet, long range 120 feet; flies back to your hand after a ranged attack."})]))
    E.append(MI("Ring of Animal Influence", [
        ("^", "fx", [charges(3, "1d3")] + [act(cast(s, dc=13, note=n), uses=1, requires=WEAR) for s, n in
                                           (("Animal Friendship", None), ("Fear", "Affects Beasts only."), ("Speak with Animals", None))]),
        ("- *Animal Friendship*", "sys", ["/effects/1"]),
        ("- *Fear*", "sys", ["/effects/2"]),
        ("- *Speak with Animals*", "sys", ["/effects/3"])]))
    E.append(MI("Ring of Djinni Summoning", [
        ("^", "fx", act({"op": "summon", "creature": "dnd5e/creature/djinni", "controller": "summoner",
                         "duration": {"kind": "hours", "amount": 1, "up_to": True, "concentration": True, "ends_on": [{"event": "drops_to_0_hp"}]},
                         "note": "Within 120 feet."}, requires=WEAR)),
        ("While summoned, the djinni", "rule", {"id": "djinni", "attitude": "friendly", "obeys": True, "no_commands": "defends_only"}),
        ("After the djinni departs", "rule", {"id": "recharge", "hours": 24, "djinni_dies": "ring becomes nonmagical"}),
        ("*Rings of Djinni Summoning* are often", "desc", None)]))
    rec = item_nodes("Ring of Elemental Command")
    plane_spells = {"air": [("Chain Lightning", 3), ("Feather Fall", 0), ("Gust of Wind", 2), ("Wind Wall", 1)],
                    "earth": [("Earthquake", 5), ("Stone Shape", 2), ("Stoneskin", 3), ("Wall of Stone", 3)],
                    "fire": [("Burning Hands", 1), ("Fireball", 2), ("Fire Storm", 4), ("Wall of Fire", 3)],
                    "water": [("Create or Destroy Water", 1), ("Ice Storm", 2), ("Tsunami", 5), ("Wall of Ice", 3), ("Water Walk", 2)]}

    def linked(p):
        return {"all": [WEAR, {"pred": "item_variant_is", "args": {"variant": p}}]}
    E.append(MI("Ring of Elemental Command", [
        ("^", "md", md("linked_plane", "Which Elemental Plane is the ring linked to?", "The GM chooses or randomly determines the linked plane.",
                       options=["air", "earth", "fire", "water"])),
        ("Every *Ring of Elemental Command*", "desc", None),
        ("**Elemental Bane.**", "fx", [adv("attack_roll", {"all": [WEAR, {"pred": "creature_type_in", "args": {"types": ["elemental"]}}]}),
                                       adv("attack_roll", {"all": [WEAR, {"pred": "attacker_creature_type_in", "args": {"types": ["elemental"]}}]},
                                           mode="disadvantage", direction="against")]),
        ("**Elemental Compulsion.**", "fx", act(save("wis", 18, on_fail=[cond("charmed", until_turn()),
                                                                         ref("dnd5e/magic-item/ring-of-elemental-command", note="You determine its move and action on its next turn.")],
                                                     target={"kind": "creature", "range": {"kind": "distance", "feet": 60}, "must_see": True,
                                                             "filter": {"creature_types": ["elemental"]}}), requires=WEAR)),
        ("***Elemental Focus.***", "desc", None),
        ("**Air.**", "fx", [lang("auran") | {"when": linked("air")}, resist("lightning", linked("air")),
                            speed("fly", 0, mode="equal_to_walk", when=linked("air"), hover=True)]),
        ("**Earth.**", "fx", [lang("terran") | {"when": linked("earth")}, resist("acid", linked("earth")),
                              {"op": "modifier", "stat": "ignores_difficult_terrain", "mode": "set", "value": 1,
                               "when": {"all": [linked("earth"), {"pred": "terrain_from", "args": {"source": ["rubble", "rocks", "dirt"]}}]}}]),
        ("**Earth.**", "rule", {"id": "earth_glide", "through": ["solid earth", "rock"], "as": "difficult_terrain", "end_turn_inside": "shunted to last unoccupied space"}),
        ("**Fire.**", "fx", [lang("ignan") | {"when": linked("fire")}, resist("fire", linked("fire"), kind="immunity")]),
        ("**Water.**", "fx", [lang("aquan") | {"when": linked("water")}, speed("swim", 60, when=linked("water")),
                              {"op": "modifier", "stat": "breathe_underwater", "mode": "set", "value": 1, "when": linked("water")}]),
        ("***Spellcasting.***", "fx", [charges(5, "1d4 + 1")] + [
            act(cast(s, dc=18), uses=n, requires=linked(p)) for p, lst in plane_spells.items() for s, n in lst]),
        ("| **Plane**", "table", tab("Ring of Elemental Command", ["Plane", "Spells (Charges)"], rows_of(rec)))]))
    E.append(MI("Ring of Evasion", [
        ("^", "fx", [charges(3, "1d3"), trig("fails_saving_throw", {"op": "auto_result", "rolls": ["saving_throw.dex"], "result": "success"},
                                             cost="reaction", optional=True, condition={"all": [WEAR, {"pred": "roll_is", "args": {"roll": "saving_throw.dex"}}]},
                                             note="Expend 1 charge.")])]))
    E.append(MI("Ring of Feather Falling", [
        ("^", "fx", [setv("fall_rate_feet_per_round", 60, WEAR),
                     {"op": "defense", "kind": "immunity", "damage_types": ["bludgeoning"], "when": {"all": [WEAR, {"pred": "damage_from_falling"}]},
                      "note": "No damage from falling."}])]))
    E.append(MI("Ring of Free Action", [
        ("^", "fx", [{"op": "modifier", "stat": "ignores_difficult_terrain", "mode": "set", "value": 1, "when": WEAR},
                     {"op": "restrict", "restrictions": ["speed_reduced_by_magic"], "when": WEAR},
                     {"op": "defense", "kind": "immunity", "conditions": ["dnd5e/condition/paralyzed", "dnd5e/condition/restrained"],
                      "when": WEAR, "note": "From magic only."}])]))
    E.append(MI("Ring of Invisibility", [
        ("^", "fx", act(cond("invisible", {"kind": "until_event", "until": {"event": "unequips_item"}, "ends_on": [{"event": "bonus_action_taken"}]},
                             note="Until the ring is removed or you take a Bonus Action to become visible."), requires=WEAR))]))
    E.append(MI("Ring of Jumping", [("^", "fx", act(cast("Jump", target=SELF, note="Can target only yourself."), requires=WEAR))]))
    E.append(MI("Ring of Mind Shielding", [
        ("^", "fx", {"op": "restrict", "restrictions": ["read_thoughts_or_lie_detection_by_magic"], "when": WEAR,
                     "note": "Also alignment and creature type; telepathy only if you allow it."}),
        ("You can take a Magic action to cause", "rule", {"id": "imperceptible", "toggle": "dnd5e/action/magic", "ends": ["removed", "you_die"]}),
        ("If you die while wearing the ring", "rule", {"id": "soul", "enters_ring_unless_occupied": True, "may_depart": True,
                                                       "telepathy_with_wearer": True, "wearer_cannot_prevent": True})]))
    E.append(MI("Ring of Protection", [("^", "fx", [mod("ac", 1, WEAR), mod("saving_throw", 1, WEAR)])]))
    E.append(MI("Ring of Regeneration", [
        ("^", "fx", trig({"event": "minutes_elapsed", "which": "each"}, {"op": "heal", "amount": "1d6"},
                         condition={"all": [WEAR, {"not": {"pred": "at_zero_hp"}}]}, note="Every 10 minutes.")),
        ("^", "rule", {"id": "regrowth", "days": "1d6 + 1", "requires": "at least 1 Hit Point the whole time"})]))
    rr = item_nodes("Ring of Resistance")
    E.append(MI("Ring of Resistance", [
        ("^", "fx", resist([{"var": "chosen.resistance_type"}], WEAR)),
        ("^", "md", md("resistance_type", "Which damage type (and gemstone) does the ring have? (choose or roll 1d10)",
                       "which the GM chooses or determines randomly by rolling on the following table")),
        ("| **1d10**", "table", tab("Ring of Resistance", ["1d10", "Damage Type", "Gemstone"], rows_of(rr)))]))
    stars = item_nodes("Ring of Shooting Stars")
    E.append(MI("Ring of Shooting Stars", [
        ("^", "fx", [act(cast("Dancing Lights"), requires=WEAR), act(cast("Light"), requires=WEAR)]),
        ("The ring has 6 charges", "fx", charges(6, "1d6")),
        ("***Faerie Fire.***", "fx", act(cast("Faerie Fire"), uses=1, requires=WEAR)),
        ("***Lightning Spheres.***", "fx", act(ref("dnd5e/magic-item/ring-of-shooting-stars", duration={"kind": "minutes", "amount": 1, "up_to": True, "concentration": True},
                                                   note="Up to four spheres within 120 feet; each sheds Dim Light 30 feet."), uses=2, requires=WEAR)),
        ("As a Bonus Action, you can move each sphere", "fx", act(save("dex", 15, on_fail=dmg({"var": "item_spheres_damage"}, "lightning"), half=True,
                                                                      note="When a sphere first comes within 5 feet of a creature other than you not behind Total Cover; damage by number of spheres (table)."),
                                                                 cost="bonus_action", requires={"pred": "effect_active"})),
        ("| **Number of**", "table", tab("Lightning Spheres", ["Number of Spheres", "Lightning Damage", "Number of Spheres", "Lightning Damage"],
                                         [r for r in rows_of(stars) if r[0].isdigit()])),
        ("***Shooting Stars.***", "fx", act(save("dex", 15, on_fail=dmg("5d4", "radiant"), half=True,
                                                 target=area("cube", 15, origin="point"), note="One mote per charge, each at a point within 60 feet."),
                                            uses={"var": "charges_spent"}, requires=WEAR))]))
    E.append(MI("Ring of Spell Storing", spell_store("ring", 5, "1d6 − 1")))
    E.append(MI("Ring of Spell Turning", [
        ("^", "fx", [adv("saving_throw", {"all": [WEAR, {"pred": "save_against_spell"}]}),
                     trig({"event": "succeeds_saving_throw", "which": "each"}, ref("dnd5e/magic-item/ring-of-spell-turning", note="The spell has no effect on you."),
                          condition={"all": [WEAR, {"pred": "spell_level_at_most", "args": {"level": 7}}]}),
                     trig({"event": "succeeds_saving_throw", "which": "each"},
                          ref("dnd5e/magic-item/ring-of-spell-turning", note="Deflect the spell at its caster, who saves against its own spell save DC."),
                          cost="reaction", optional=True,
                          condition={"all": [WEAR, {"pred": "spell_targeted_only_you"}, {"pred": "spell_level_at_most", "args": {"level": 7}}]})])]))
    E.append(MI("Ring of Swimming", [("^", "fx", speed("swim", 40, when=WEAR))]))
    E.append(MI("Ring of Telekinesis", [("^", "fx", act(cast("Telekinesis"), requires=WEAR))]))
    E.append(MI("Ring of the Ram", [
        ("^", "fx", [charges(3, "1d3"),
                     act({"op": "attack", "attack_type": "ranged_spell", "bonus": 7, "target": creature(60, must_see=True),
                          "on_hit": [dmg({"dice": {"count": {"op": "mul", "args": [2, {"var": "charges_spent"}]}, "faces": 10}}, "force"),
                                     {"op": "move", "mode": "push", "distance_feet": {"op": "mul", "args": [5, {"var": "charges_spent"}]}}]},
                         uses={"var": "charges_spent"}, requires=WEAR)]),
        ("Alternatively, you can expend 1 to 3", "fx", act({"op": "check", "ability": "str", "note": "Ring's check with +5 per charge spent; breaks an unattended nonmagical object within 60 feet."},
                                                           uses={"var": "charges_spent"}, requires=WEAR))]))
    E.append(MI("Ring of Three Wishes", [("^", "fx", [charges(3), act(cast("Wish"), uses=1, requires=WEAR)]),
                                         ("^", "rule", {"id": "last_charge", "becomes_nonmagical": True})]))
    E.append(MI("Ring of Warmth", [
        ("^", "fx", {"op": "modifier", "stat": "damage_taken", "mode": "add", "value": {"op": "neg", "args": ["2d8"]},
                     "when": {"all": [WEAR, {"pred": "deals_damage_type", "args": {"type": "cold"}}]}}),
        ("In addition, while wearing", "rule", {"id": "cold_tolerance", "min_fahrenheit": 0, "includes_gear": True})]))
    E.append(MI("Ring of Water Walking", [("^", "fx", act(cast("Water Walk", target=SELF, note="Targeting only yourself."), requires=WEAR))]))
    E.append(MI("Ring of X-ray Vision", [
        ("^", "fx", act(sense("xray_vision", 30, duration=mins(1)), requires=WEAR)),
        ("^", "rule", {"id": "penetration", "stone_feet": 1, "metal_inches": 1, "wood_or_dirt_feet": 3, "blocked_by": ["thicker", "thin sheet of lead"]}),
        ("Whenever you use the ring again", "fx", save("con", 15, on_fail={"op": "apply_condition", "condition": "dnd5e/condition/exhaustion", "params": {"levels": 1}},
                                                     when={"pred": "used_since_long_rest"}))]))
    E.append(MI("Robe of Eyes", [
        ("^", "desc", None),
        ("**All-Around Vision.**", "fx", adv("ability_check", {"all": [WEAR, {"pred": "check_uses_skill", "args": {"skill": "perception"}}, {"pred": "requires_sight"}]})),
        ("**Special Senses.**", "fx", [sense("darkvision", 120, WEAR), sense("truesight", 120, WEAR)]),
        ("***Drawbacks.***", "fx", [trig({"event": "targeted_by_spell", "which": "each"}, cond("blinded", mins(1)), condition=WEAR,
                                         note="Light cast on the robe (save DC 11) or Daylight within 5 feet (DC 15); Constitution save at the end of each of your turns ends it.")])]))
    E.append(MI("Robe of Scintillating Colors", [
        ("^", "fx", [charges(3, "1d3"),
                     act([adv("attack_roll", {"pred": "attacker_can_see_target"}, mode="disadvantage", direction="against", duration=until_turn("turn_end")),
                          save("wis", 15, on_fail=cond("stunned", until_turn("turn_end")),
                               target={"kind": "area", "area": {"shape": "emanation", "size_feet": 30, "origin": "self"},
                                       "filter": {"predicate": {"pred": "can_see"}}})],
                         uses=1, requires=WEAR)]),
        ("^", "rule", {"id": "light", "bright_feet": 30, "dim_feet": 30, "until": "end of your next turn"})]))
    E.append(MI("Robe of Stars", [
        ("^", "fx", mod("saving_throw", 1, WEAR)),
        ("Six stars", "fx", [charges(6, "1d6", note="Stars; 1d6 removed stars reappear daily at dusk."),
                             act(cast("Magic Missile", level=5), uses=1, requires=WEAR)]),
        ("While you wear the robe, you can take a Magic action to enter", "fx", act({"op": "move", "mode": "teleport",
                                                                                   "note": "To the Astral Plane with your gear; return with another Magic action to the last space or the nearest unoccupied one."},
                                                                                  requires=WEAR))]))
    E.append(MI("Robe of the Archmagi", [
        ("^", "desc", None),
        ("You gain these benefits", "desc", None),
        ("***Armor.***", "fx", setv("base_ac", {"op": "add", "args": [15, {"var": "ability_mod.dex"}]}, {"all": [WEAR, {"not": {"pred": "wearing_armor_any"}}]})),
        ("***Magic Resistance.***", "fx", adv("saving_throw", {"all": [WEAR, {"pred": "save_against_spell_or_magic"}]})),
        ("***War Mage.***", "fx", [mod("spell_save_dc", 2, WEAR), mod("spell_attack_bonus", 2, WEAR)])]))
    useful = item_nodes("Robe of Useful Items")
    E.append(MI("Robe of Useful Items", [
        ("^", "fx", act(ref("dnd5e/magic-item/robe-of-useful-items", note="Detach a patch: it becomes the object or creature it represents."), requires=WEAR)),
        ("^", "rule", {"id": "last_patch", "becomes_ordinary": True}),
        ("The robe has two of each", "rule", {"id": "standard_patches", "each": 2,
                                              "patches": ["dnd5e/gear/lantern-bullseye", "dnd5e/weapon/dagger", "dnd5e/gear/mirror", "dnd5e/gear/pole",
                                                          "dnd5e/gear/rope", "dnd5e/gear/sack"]}),
        ("In addition, the robe has 4d4", "md", md("extra_patches", "Which 4d4 other patches does the robe have? (choose or roll 1d100 each)",
                                                   "The GM chooses the patches or determines them randomly by rolling on the following table.")),
        ("| **1d100**", "table", tab("Robe of Useful Items", ["1d100", "Patch"], rows_of(useful)))]))
    E.append(MI("Rod of Absorption", [
        ("^", "fx", trig("targeted_by_spell", ref("dnd5e/magic-item/rod-of-absorption", note="Absorb a spell targeting only you without an area: canceled; its level is stored."),
                         cost="reaction", optional=True, condition={"all": [HOLD, {"pred": "spell_targeted_only_you"}]})),
        ("^", "rule", {"id": "capacity", "lifetime_levels": 50, "full": "no effect"}),
        ("When you become attuned", "rule", {"id": "knowledge", "on_attune": ["lifetime_levels", "stored_levels"]}),
        ("If you are a spellcaster holding the rod", "rule", {"id": "convert", "max_slot_level": 5, "not_above_own_slots": True,
                                                              "stored_levels_as_slot": True}),
        ("A newly found rod", "rule", {"id": "found", "stored_levels": "1d10", "empty_and_full": "becomes nonmagical"})]))
    return E


if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
