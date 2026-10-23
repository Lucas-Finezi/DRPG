#!/usr/bin/env python3
"""L14 (part) — Warlock, Eldritch Invocation options and Fiend Patron features."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classlib import CF, OPT, col, spell_table  # noqa: E402
from entrylib import extend_registries, write_entry  # noqa: E402

LOT = "L14"
W = "Warlock"
LONG = {"event": "long_rest_finished"}
SHORT = {"event": "short_rest_finished"}
C = lambda s: f"dnd5e/condition/{s}"  # noqa: E731
SP = lambda s: f"dnd5e/spell/{s}"  # noqa: E731
INV = lambda s: f"dnd5e/feature/warlock-invocation-{s}"  # noqa: E731
CHA = {"var": "ability_mod.cha"}
CHA1 = {"op": "max", "args": [1, CHA]}
PACT_SLOT = {"resource": "pact_magic_slot", "amount": 1}
EIO = "Eldritch Invocation Options"
REPEATABLE = ("***Repeatable.***", "rule", {"id": "repeatable", "repeatable": True, "each_time": "different_choice"})


def prereq(level=None, invocation=None, other=None):
    d = {"id": "prerequisite"}
    if level:
        d["warlock_level"] = level
    if invocation:
        d["invocation"] = INV(invocation)
    if other:
        d["other"] = other
    return (None, "rule", d)


def free_cast(spell, self_only=False, **kw):
    fx = {"op": "activation", "cost": "none", "then": [{"op": "cast_spell", "spell": SP(spell), "slot": "none",
                                                         **({"target": {"kind": "self"}} if self_only else {})}],
          "note": "Casting time as normal for the spell."}
    fx.update(kw)
    return fx


def inv(name, items):
    return OPT(W, name, "eldritch_invocation", EIO, items)


def entries():
    E = []
    E.append(CF(W, "Eldritch Invocations", 1, [
        (None, "fx", {"op": "grant", "refs": [INV("pact-of-the-tome")], "choose": col(W, "Eldritch Invocations"),
                      "note": "Invocations of your choice from Eldritch Invocation Options (feature_type eldritch_invocation); Pact of the Tome is an example."}),
        ("Invocations are described in", "ref", ["dnd5e/rule/eldritch-invocation-options"]),
        ("***Prerequisites.***", "rule", {"id": "prerequisites", "must_meet_prerequisite": True}),
        ("***Replacing and Gaining Invocations.***", "rule", {
            "id": "replace", "on": "level_gained", "count": 1, "must_qualify": True,
            "cannot_replace_if_prerequisite_of_another": True}),
        ("When you gain certain Warlock levels", "sys", ["/effects/0"]),
        ("You can’t pick the same invocation more than once", "rule", {"id": "unique", "unless": "repeatable"})]))
    E.append(CF(W, "Pact Magic", 1, [
        (None, "rule", {"id": "spellcasting", "spell_list_of": "dnd5e/spell-list/warlock",
                        "note": "Spells whose class list includes this class (D-001)."}),
        ("See “Spells”", "ref", ["dnd5e/rule/spells"]),
        ("***Cantrips.***", "rule", {"id": "cantrips", "known": col(W, "Cantrips"), "start": 2,
                                    "from": "dnd5e/spell-list/warlock",
                                    "recommended": [SP("eldritch-blast"), SP("prestidigitation")],
                                    "replace": {"on": "level_gained", "count": 1}, "gain_at_levels": [4, 10]}),
        ("***Spell Slots.***", "fx", {"op": "resource", "resource": "pact_magic_slot", "name": "Pact Magic spell slots",
                                     "max": col(W, "Spell Slots"),
                                     "recovery": [{"on": SHORT, "amount": "all"}, {"on": LONG, "amount": "all"}]}),
        ("***Spell Slots.***", "rule", {"id": "slot_level", "level": col(W, "Slot Level"), "all_slots_same_level": True,
                                       "spell_levels": [1, 5], "cast_at_slot_level": True}),
        ("***Prepared Spells of Level 1+", "rule", {
            "id": "prepared_spells", "count": col(W, "Prepared Spells"), "start_level_1_spells": 2,
            "from": "dnd5e/spell-list/warlock", "recommended": [SP("charm-person"), SP("hex")],
            "max_spell_level": col(W, "Slot Level"), "always_prepared_from_features_do_not_count": True}),
        ("***Changing Your Prepared Spells.***", "rule", {"id": "changing_prepared_spells", "mode": "level_gain_one"}),
        ("***Spellcasting Ability.***", "rule", {"id": "spellcasting_ability", "ability": "cha"}),
        ("***Spellcasting Focus.***", "rule", {"id": "spellcasting_focus", "focus": ["dnd5e/gear/arcane-focus"]})]))
    E.append(CF(W, "Magical Cunning", 2, [(None, "fx", {
        "op": "activation", "name": "Magical Cunning", "cost": "none", "frequency": {"count": 1, "per": "long_rest"},
        "note": "An esoteric rite lasting 1 minute.",
        "then": [{"op": "restore", "resource": "pact_magic_slot", "amount": {
            "op": "div", "round": "up", "args": [col(W, "Spell Slots"), 2]}}]})]))
    E.append(CF(W, "Warlock Subclass", 3, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/subclass/fiend-patron"], "choose": 1,
        "note": "Gain each subclass feature of your Warlock level or lower."})]))
    E.append(CF(W, "Ability Score Improvement", 4, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/ability-score-improvement"],
        "note": "Or another feat you qualify for; again at Warlock levels 8, 12 and 16."})]))
    E.append(CF(W, "Contact Patron", 9, [
        (None, "fx", [{"op": "grant", "refs": [SP("contact-other-plane")], "note": "Always prepared."},
                      free_cast("contact-other-plane", frequency={"count": 1, "per": "long_rest"}),
                      {"op": "auto_result", "rolls": ["saving_throw"], "result": "success",
                       "when": {"pred": "save_against_spell", "args": {"spell": "contact-other-plane"}},
                       "note": "Only when cast with this feature to contact your patron."}]),
        ("Once you cast the spell with this feature", "sys", ["/effects/1"])]))
    E.append(CF(W, "Mystic Arcanum", 11, [
        (None, "rule", {"id": "arcanum", "spells": [{"level": 6, "from_warlock_level": 11}, {"level": 7, "from_warlock_level": 13},
                                                    {"level": 8, "from_warlock_level": 15}, {"level": 9, "from_warlock_level": 17}],
                        "from": "dnd5e/spell-list/warlock"}),
        ("You can cast your arcanum spell once", "fx", {
            "op": "activation", "cost": "none", "frequency": {"count": 1, "per": "long_rest"},
            "then": [{"op": "cast_spell", "spell": "dnd5e/spell-list/warlock", "slot": "none"}],
            "note": "Once per Long Rest for each arcanum spell."}),
        ("As shown in the Warlock Features table", "sys", ["/data/rules/0"]),
        ("Whenever you gain a Warlock level", "rule", {"id": "replace", "on": "level_gained", "count": 1,
                                                       "same_level": True})]))
    E.append(CF(W, "Epic Boon", 19, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/boon-of-fate"],
        "note": "An Epic Boon feat or another feat you qualify for; Boon of Fate is recommended."})]))
    E.append(CF(W, "Eldritch Master", 20, [(None, "rule", {
        "id": "full_restore", "feature": "dnd5e/feature/warlock-magical-cunning", "restores": "all_pact_magic_slots"})]))

    E.append(inv("Agonizing Blast", [
        prereq(2, other="warlock_cantrip_that_deals_damage"),
        ("Choose one of your known Warlock cantrips", "fx", {
            "op": "modifier", "stat": "damage_roll", "mode": "add", "value": CHA,
            "when": {"pred": "is_chosen_spell", "args": {"choice": "agonizing_blast"}}}),
        REPEATABLE]))
    E.append(inv("Armor of Shadows", [(None, "fx", free_cast("mage-armor", self_only=True))]))
    E.append(inv("Ascendant Step", [prereq(5), ("You can cast", "fx", free_cast("levitate", self_only=True))]))
    E.append(inv("Devil’s Sight", [prereq(2), ("You can see normally", "fx", {
        "op": "sense", "sense": "devils_sight", "range_feet": 120})]))
    E.append(inv("Devouring Blade", [prereq(12, "thirsting-blade"), ("The Extra Attack", "rule", {
        "id": "extra_attacks", "feature": INV("thirsting-blade"), "extra_attacks": 2})]))
    E.append(inv("Eldritch Mind", [(None, "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw.con"],
                                                 "when": {"pred": "concentration_save"}})]))
    E.append(inv("Eldritch Smite", [prereq(5, "pact-of-the-blade"), ("Once per turn when you hit", "fx", {
        "op": "trigger", "event": {"event": "hits_with_attack_roll"}, "optional": True,
        "condition": {"pred": "attack_with_pact_weapon"}, "frequency": {"count": 1, "per": "turn"},
        "then": [{"op": "spend", "resource": "pact_magic_slot", "amount": 1},
                 {"op": "damage", "damage_type": "force", "target": {"kind": "inherit"},
                  "amount": {"dice": {"count": {"op": "add", "args": [1, {"var": "spell_slot_level"}]}, "faces": 8}}},
                 {"op": "apply_condition", "condition": C("prone"), "note": "Optional; Huge or smaller.",
                  "target": {"kind": "inherit", "filter": {"sizes": ["tiny", "small", "medium", "large", "huge"]}}}]})]))
    E.append(inv("Eldritch Spear", [
        prereq(2, other="warlock_cantrip_that_deals_damage"),
        ("Choose one of your known Warlock cantrips", "fx", {
            "op": "modifier", "stat": "spell_range", "mode": "add",
            "value": {"op": "mul", "args": [30, {"var": "class_level.warlock"}]},
            "when": {"pred": "is_chosen_spell", "args": {"choice": "eldritch_spear"}},
            "note": "A damaging cantrip with a range of 10+ feet."}),
        REPEATABLE]))
    E.append(inv("Fiendish Vigor", [prereq(2), ("You can cast", "fx", free_cast("false-life", self_only=True)),
                                     ("When you cast the spell with this feature", "rule", {
                                         "id": "max_die", "temporary_hit_points_die": "maximum"})]))
    E.append(inv("Gaze of Two Minds", [
        prereq(5),
        ("You can use a Bonus Action", "fx", {
            "op": "activation", "name": "Gaze of Two Minds", "cost": "bonus_action",
            "target": {"kind": "creature", "range": {"kind": "touch"}, "filter": {"willing": True}},
            "then": [{"op": "sense", "sense": "shared_senses", "range_feet": 0,
                      "duration": {"kind": "until_event", "until": {"event": "turn_end", "whose": "self", "which": "next"}}}],
            "note": "Maintain with a Bonus Action on later turns while on the same plane; ends if not maintained."}),
        ("While perceiving through the other creature’s senses", "rule", {
            "id": "shared_senses", "gains_target_special_senses": True,
            "cast_from_either_space_within_feet": 60})]))
    E.append(inv("Gift of the Depths", [
        prereq(5),
        ("You can breathe underwater", "fx", [{"op": "modifier", "stat": "breathe_underwater", "mode": "set", "value": 1},
                                              {"op": "speed", "movement": "swim", "mode": "equal_to_walk", "value": 0}]),
        ("You can also cast", "fx", free_cast("water-breathing", frequency={"count": 1, "per": "long_rest"}))]))
    E.append(inv("Gift of the Protectors", [
        prereq(9, "pact-of-the-tome"),
        ("A new page appears", "rule", {"id": "page", "names_max": CHA1, "writing_cost": "action",
                                        "requires_permission": True}),
        ("When any creature whose name is on the page", "fx", {
            "op": "trigger", "event": {"event": "reduced_to_0_hp_not_killed"},
            "condition": {"pred": "name_on_page"}, "frequency": {"count": 1, "per": "long_rest"},
            "then": [{"op": "modifier", "stat": "hp", "mode": "set", "value": 1, "target": {"kind": "inherit"}}]}),
        ("As a Magic action, you can erase", "rule", {"id": "erase", "cost": "dnd5e/action/magic", "touch": True})]))
    E.append(inv("Investment of the Chain Master", [
        prereq(5, "pact-of-the-chain"),
        ("When you cast", "ref", [SP("find-familiar")]),
        ("***Aerial or Aquatic.***", "fx", {"op": "choice", "id": "familiar_movement", "choose": 1, "options": [
            {"id": "fly", "label": "Fly Speed", "effects": [{"op": "speed", "movement": "fly", "mode": "set", "value": 40}]},
            {"id": "swim", "label": "Swim Speed", "effects": [{"op": "speed", "movement": "swim", "mode": "set", "value": 40}]}]}),
        ("***Quick Attack.***", "fx", {"op": "activation", "cost": "bonus_action",
                                      "then": [{"op": "reference", "rule": "dnd5e/action/attack",
                                                "note": "The familiar takes the Attack action."}]}),
        ("***Necrotic or Radiant Damage.***", "rule", {"id": "damage_type", "replaces": ["bludgeoning", "piercing", "slashing"],
                                                       "choose_from": ["necrotic", "radiant"]}),
        ("***Your Save DC.***", "rule", {"id": "save_dc", "familiar_uses": "spell_save_dc"}),
        ("***Resistance.***", "fx", {"op": "trigger", "event": {"event": "familiar_takes_damage"}, "cost": "reaction",
                                    "optional": True,
                                    "then": [{"op": "defense", "kind": "resistance",
                                              "damage_types": [{"var": "chosen.trigger_damage_type"}],
                                              "note": "The familiar, against that damage."}]})]))
    E.append(inv("Lessons of the First Ones", [
        prereq(2),
        ("You have received knowledge", "fx", {"op": "grant", "choose": 1, "refs": [
            "dnd5e/feat/alert", "dnd5e/feat/magic-initiate", "dnd5e/feat/savage-attacker", "dnd5e/feat/skilled"],
            "note": "One Origin feat of your choice."}),
        REPEATABLE]))
    E.append(inv("Lifedrinker", [prereq(9, "pact-of-the-blade"), ("Once per turn when you hit", "fx", {
        "op": "trigger", "event": {"event": "hits_with_attack_roll"}, "optional": True,
        "condition": {"pred": "attack_with_pact_weapon"}, "frequency": {"count": 1, "per": "turn"},
        "then": [{"op": "damage", "amount": "1d6", "target": {"kind": "inherit"},
                  "damage_type": {"choose_from": ["necrotic", "psychic", "radiant"]}},
                 {"op": "activation", "cost": "none", "uses": {"resource": "hit_point_dice", "amount": 1},
                  "then": [{"op": "heal", "target": {"kind": "self"}, "amount": {"op": "max", "args": [
                      1, {"op": "add", "args": [{"var": "hit_point_die"}, {"var": "ability_mod.con"}]}]}}]}]})]))
    for name, level, spell, self_only in (("Mask of Many Faces", 2, "disguise-self", False),
                                          ("Master of Myriad Forms", 5, "alter-self", False),
                                          ("Misty Visions", 2, "silent-image", False),
                                          ("Otherworldly Leap", 2, "jump", True),
                                          ("Visions of Distant Realms", 9, "arcane-eye", False),
                                          ("Whispers of the Grave", 7, "speak-with-dead", False)):
        E.append(inv(name, [prereq(level), ("You can cast", "fx", free_cast(spell, self_only=self_only))]))
    E.append(inv("One with Shadows", [prereq(5), ("While you’re in an area", "fx", free_cast(
        "invisibility", self_only=True, requires={"any": [{"pred": "in_dim_light"}, {"pred": "in_darkness"}]}))]))
    E.append(inv("Pact of the Blade", [
        (None, "fx", {"op": "activation", "name": "Pact of the Blade", "cost": "bonus_action",
                      "then": [{"op": "choice", "id": "pact_weapon", "choose": 1, "options": [
                          {"id": "conjure", "label": "Conjure a Simple or Martial Melee weapon", "effects": [
                              {"op": "reference", "rule": INV("pact-of-the-blade"), "note": "Weapon of your choice, in your hand."}]},
                          {"id": "bond", "label": "Bond with a magic weapon you touch", "effects": [
                              {"op": "reference", "rule": INV("pact-of-the-blade"),
                               "note": "Not if someone else is attuned to it or another Warlock is bonded with it."}]}]}]}),
        ("Until the bond ends", "fx", [
            {"op": "proficiency", "category": "weapon", "items": ["pact_weapon"]},
            {"op": "modifier", "stat": "spellcasting_focus", "mode": "set", "value": 1, "note": "The pact weapon."}]),
        ("Whenever you attack with the bonded weapon", "fx", [
            {"op": "modifier", "stat": "attack_ability", "mode": "set", "value": CHA,
             "when": {"pred": "attack_with_pact_weapon"}, "note": "Optional: instead of Strength or Dexterity."},
            {"op": "choice", "id": "pact_damage_type", "choose": 1, "options": [
                {"id": t, "label": t.title(), "value": t, "effects": []}
                for t in ("necrotic", "psychic", "radiant", "normal_damage_type")]}]),
        ("Your bond with the weapon ends", "rule", {"id": "bond_ends", "ends_on": [
            "bonus_action_used_again", "weapon_more_than_5_feet_away_for_1_minute", "death"],
            "conjured_weapon_disappears": True})]))
    E.append(inv("Pact of the Chain", [
        (None, "fx", [{"op": "grant", "refs": [SP("find-familiar")]},
                      {"op": "activation", "cost": "action", "action": "dnd5e/action/magic",
                       "then": [{"op": "cast_spell", "spell": SP("find-familiar"), "slot": "none"}]}]),
        ("When you cast the spell, you choose", "rule", {"id": "special_forms", "forms": [
            "dnd5e/creature/imp", "dnd5e/creature/pseudodragon", "dnd5e/creature/quasit", "dnd5e/creature/skeleton",
            "dnd5e/creature/sphinx-of-wonder", "dnd5e/creature/sprite", "dnd5e/creature/venomous-snake"]}),
        ("Additionally, when you take the Attack action", "fx", {
            "op": "trigger", "event": {"event": "takes_attack_action"}, "optional": True,
            "then": [{"op": "attack", "attack_type": "melee", "note": "Forgo one of your attacks: the familiar makes one attack with its Reaction."}]})]))
    E.append(inv("Pact of the Tome", [
        (None, "fx", {"op": "trigger", "event": {"event": "rest_finished"}, "optional": True,
                      "then": [{"op": "reference", "rule": "dnd5e/feature/warlock-invocation-pact-of-the-tome",
                                "note": "Conjure the Book of Shadows; it disappears if you conjure another or die."}]}),
        ("***Cantrips and Rituals.***", "rule", {"id": "book_spells", "cantrips": 3, "level_1_ritual_spells": 2,
                                                "from": "any_class_spell_list", "not_already_prepared": True,
                                                "prepared_while_on_person": True, "count_as": "dnd5e/class/warlock"}),
        ("***Spellcasting Focus.***", "rule", {"id": "focus", "book_is_spellcasting_focus": True})]))
    E.append(inv("Repelling Blast", [
        prereq(2, other="warlock_cantrip_that_deals_damage_via_attack_roll"),
        ("Choose one of your known Warlock cantrips", "fx", {
            "op": "trigger", "event": {"event": "hits_with_attack_roll"}, "optional": True,
            "condition": {"pred": "is_chosen_spell", "args": {"choice": "repelling_blast"}},
            "then": [{"op": "move", "mode": "push", "distance_feet": 10,
                      "target": {"kind": "inherit", "filter": {"sizes": ["tiny", "small", "medium", "large"]}}}]}),
        REPEATABLE]))
    E.append(inv("Thirsting Blade", [prereq(5, "pact-of-the-blade"), ("You gain the Extra Attack feature", "fx", {
        "op": "modifier", "stat": "attacks_per_attack_action", "mode": "max", "value": 2,
        "when": {"pred": "attack_with_pact_weapon"}})]))
    E.append(inv("Witch Sight", [prereq(15), ("You have Truesight", "fx", {
        "op": "sense", "sense": "truesight", "range_feet": 30})]))

    S = "Fiend Patron"
    E.append(CF(W, "Dark One’s Blessing", 3, [(None, "fx", {
        "op": "trigger", "event": {"event": "enemy_reduced_to_0_hp"},
        "condition": {"any": [{"pred": "reduced_by_source"}, {"pred": "within_feet", "args": {"feet": 10}}]},
        "then": [{"op": "temp_hp", "target": {"kind": "self"}, "amount": {"op": "max", "args": [
            1, {"op": "add", "args": [CHA, {"var": "class_level.warlock"}]}]}}]})], sub=S))
    rows = spell_table("Fiend Spells")
    E.append(CF(W, "Fiend Spells", 3, [
        (None, "fx", [{"op": "grant", "refs": r["spells"], "note": "Always prepared.",
                       "when": {"pred": "class_level_at_least", "args": {"class": "warlock", "level": r["level"]}}}
                      for r in rows]),
        ("##### Fiend Spells", "ref", ["dnd5e/spell-list/fiend-spells"]),
        ("##### Fiend Spells", "table", {"id": "fiend_spells", "caption": "Fiend Spells",
                                         "columns": ["Warlock Level", "Spells"],
                                         "rows": [[r["level"], r["spells"]] for r in rows]})], sub=S))
    E.append(CF(W, "Dark One’s Own Luck", 6, [
        (None, "fx", {"op": "trigger", "event": {"event": "d20_rolled"}, "optional": True,
                      "condition": {"any": [{"pred": "roll_is", "args": {"roll": "ability_check"}},
                                            {"pred": "roll_is", "args": {"roll": "saving_throw"}}]},
                      "frequency": {"count": 1, "per": "instance"},
                      "then": [{"op": "spend", "resource": "dark_ones_own_luck", "amount": 1},
                               {"op": "modifier", "stat": "triggering_roll", "mode": "add", "value": "1d10",
                                "note": "After seeing the roll, before its effects."}]}),
        ("You can use this feature a number of times", "fx", {
            "op": "resource", "resource": "dark_ones_own_luck", "max": CHA1,
            "recovery": [{"on": LONG, "amount": "all"}]})], sub=S))
    E.append(CF(W, "Fiendish Resilience", 10, [(None, "fx", {
        "op": "trigger", "event": {"event": "rest_finished"},
        "then": [{"op": "defense", "kind": "resistance", "damage_types": [{"var": "chosen.fiendish_resilience"}],
                  "note": "One damage type other than Force, until you choose a different one."}]})], sub=S))
    E.append(CF(W, "Hurl Through Hell", 14, [
        (None, "fx", {"op": "trigger", "event": {"event": "hits_with_attack_roll"}, "optional": True,
                      "frequency": {"count": 1, "per": "turn"},
                      "condition": {"pred": "resource_available", "args": {"resource": "hurl_through_hell"}},
                      "then": [{"op": "spend", "resource": "hurl_through_hell", "amount": 1},
                               {"op": "save", "ability": "cha", "dc": {"var": "spell_save_dc"}, "target": {"kind": "inherit"},
                                "on_fail": [{"op": "damage", "amount": "8d10", "damage_type": "psychic",
                                             "when": {"not": {"pred": "creature_type", "args": {"type": "fiend"}}}},
                                            {"op": "apply_condition", "condition": C("incapacitated"),
                                             "duration": {"kind": "until_event", "until": {"event": "turn_end", "whose": "source", "which": "next"}},
                                             "note": "The target disappears, then returns to its previous space or the nearest unoccupied one."}]}]}),
        ("Once you use this feature", "fx", [
            {"op": "resource", "resource": "hurl_through_hell", "max": 1, "recovery": [{"on": LONG, "amount": "all"}]},
            {"op": "activation", "cost": "none", "uses": PACT_SLOT,
             "then": [{"op": "restore", "resource": "hurl_through_hell", "amount": 1}]}])], sub=S))
    return E


REGISTRY = {
    "stats": [
        {"id": "breathe_underwater", "description": "The creature can breathe underwater (1) or not (0).", "pages": [73]},
        {"id": "spellcasting_focus", "description": "The item can be used as a Spellcasting Focus.", "pages": [74]}],
    "senses": [
        {"id": "devils_sight", "description": "See normally in Dim Light and Darkness, both magical and nonmagical, within range.", "pages": [72]},
        {"id": "shared_senses", "description": "Perceive through another creature's senses.", "pages": [73]}],
    "events": [
        {"id": "enemy_reduced_to_0_hp", "description": "An enemy is reduced to 0 Hit Points.", "pages": [76]},
        {"id": "familiar_takes_damage", "description": "The creature's familiar takes damage.", "pages": [73]},
        {"id": "rest_finished", "description": "The creature finishes a Short or Long Rest.", "pages": [74]}],
    "predicates": [
        {"id": "save_against_spell", "description": "The saving throw is against this spell (param: spell slug).", "params": ["spell"], "type": "predicate", "pages": [72]},
        {"id": "is_chosen_spell", "description": "The spell is the one chosen for this feature (param: choice id).", "params": ["choice"], "type": "predicate", "pages": [72]},
        {"id": "concentration_save", "description": "The saving throw is made to maintain Concentration.", "type": "predicate", "pages": [72]},
        {"id": "attack_with_pact_weapon", "description": "The attack uses the Warlock's pact weapon.", "type": "predicate", "pages": [72]},
        {"id": "name_on_page", "description": "The creature's name is on the Gift of the Protectors page.", "type": "predicate", "pages": [73]},
        {"id": "in_dim_light", "description": "The creature is in an area of Dim Light.", "type": "predicate", "pages": [74]},
        {"id": "in_darkness", "description": "The creature is in an area of Darkness.", "type": "predicate", "pages": [74]},
        {"id": "reduced_by_source", "description": "The source reduced the creature to 0 Hit Points.", "type": "predicate", "pages": [76]}],
}

if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
