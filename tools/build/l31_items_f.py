#!/usr/bin/env python3
"""L31 — Magic items A–Z, part 6 (Talisman of Pure Good … Wings of Flying).

Usage: python3 -I tools/build/l31_items_f.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import extend_registries, write_entry  # noqa: E402
from magiclib import (ATTUNED, DAWN, DESTROYED, DIES, HOLD, INHERIT, MI, SELF, SP, THIS, WEAR, WIELD, act, adv,  # noqa: E402
                      area, cast, charges, check, cond, creature, dmg, hours, item_nodes, md, mins, mod, ref, rows_of,
                      save, setv, speed, tab, trig, until_turn)
from l31_items_e import YOUR_DC, regain, spell_pairs, staff_spells  # noqa: E402
from l31_registry import REGISTRY  # noqa: E402

LOT = "L31"
EACH_END = {"on": {"event": "turn_end", "whose": "target", "which": "each"}, "ends": "effect_on_self"}
WEAR_OR_HOLD = {"any": [WEAR, HOLD]}
ASHES = DESTROYED | {"note": "The wand crumbles into ashes and is destroyed."}


def plus_weapon(n):
    return [mod("attack_roll", n, WIELD), mod("damage_roll", n, WIELD)]


def talisman(name, touch_dmg, touch_filter, fissure_name, n, disadv_types, end_note):
    return MI(name, [
        ("^", "desc", None),
        ("^", "fx", trig({"event": "touches_effect", "whose": "any", "which": "each"}, dmg("8d6", touch_dmg),
                         condition=touch_filter, note="Again each time it ends its turn holding or carrying the talisman.")),
        ("***Holy Symbol.***", "fx", [setv("spellcasting_focus", 1, WEAR_OR_HOLD, note="Usable as a Holy Symbol."),
                                      mod("spell_attack_bonus", 2, WEAR_OR_HOLD)]),
        (f"***{fissure_name}.***", "fx", [charges(n, note=end_note),
                                          act(save("dex", 20, on_fail={"op": "end_effect", "scope": "this_entry_on_target", "note": "Falls into the fissure and is destroyed, leaving no remains."},
                                                   on_success=dmg("4d6", "psychic"), target=creature(120, must_see=True),
                                                   note=f"A creature on the ground; Disadvantage if it is {' or '.join(disadv_types)}."),
                                              uses=1, requires=WEAR_OR_HOLD)])])


def wand_charges(n=7):
    return ("^", "fx", charges(n))


def wand_regain(death=ASHES):
    return ("***Regaining Charges.***", "fx", regain("1d6 + 1", death))


def upcast_wand(name, spell, base, dc=None):
    return MI(name, [
        ("^", "fx", [charges(7), act(cast(spell, dc=dc, level={"op": "add", "args": [base - 1, {"var": "charges_spent"}]},
                                          note=f"1 charge = level {base}; +1 level per extra charge (max 3 charges)."),
                                     uses={"var": "charges_spent"}, requires=HOLD)]),
        wand_regain()])


def entries():
    E = []
    fiend_undead = {"pred": "creature_type_in", "args": {"types": ["fiend", "undead"]}}
    E.append(talisman("Talisman of Pure Good", "radiant", fiend_undead, "Pure Rebuke", 7, ["a Fiend", "an Undead"],
                      "When the last charge is expended, the talisman is destroyed."))
    E.append(MI("Talisman of the Sphere", [
        ("^", "fx", [adv("ability_check", {"all": [WEAR_OR_HOLD, {"pred": "check_uses_skill", "args": {"skill": "arcana"}},
                                                   {"pred": "check_to_control_item", "args": {"item": "dnd5e/magic-item/sphere-of-annihilation"}}]}),
                     act({"op": "move", "mode": "move", "distance_feet": {"op": "add", "args": [10, {"op": "mul", "args": [10, {"var": "ability_mod.int"}]}]},
                          "note": "Move the Sphere of Annihilation you control; not necessarily in a straight line."},
                         requires={"pred": "controls_item", "args": {"item": "dnd5e/magic-item/sphere-of-annihilation"}})])]))
    E.append(talisman("Talisman of Ultimate Evil", "necrotic", {"not": fiend_undead}, "Ultimate End", 6, ["a Celestial"],
                      "When the last charge is expended, the talisman is destroyed."))
    E.append(MI("Thunderous Greatclub", [
        ("^", "fx", [setv("ability_score.str", 20, ATTUNED, note="Unless already 20 or higher."),
                     trig("hits_with_attack_roll", dmg("1d8", "thunder", target=INHERIT), condition={"pred": "attack_uses_weapon", "args": THIS}),
                     trig("hits_with_attack_roll", dmg("3d8", "thunder", target=INHERIT),
                          condition={"all": [{"pred": "attack_uses_weapon", "args": THIS}, {"pred": "target_is_object"}]},
                          note="Objects not worn or carried (instead of 1d8).")]),
        ("The weapon has the following", "desc", None),
        ("***Clap of Thunder.***", "fx", act([save("str", 15, on_fail=cond("prone"), target=area("cone", 30, origin="self")),
                                              dmg("3d8", "thunder", target={"kind": "object", "area": {"shape": "cone", "size_feet": 30, "origin": "self"},
                                                                            "filter": {"objects": "not_worn_or_carried"}}, note="Nonmagical objects.")])),
        ("***Earthquake.***", "fx", act([dmg(50, "bludgeoning", target={"kind": "object", "area": {"shape": "cylinder", "size_feet": 50, "origin": "point"}},
                                             note="Structures in contact with the ground."),
                                         save("dex", 20, on_fail=cond("prone"), target={"kind": "area", "area": {"shape": "cylinder", "size_feet": 50, "origin": "point"}}),
                                         save("con", 20, on_fail={"op": "end_effect", "scope": "concentration"}, when={"pred": "concentrating"}),
                                         save("dex", 20, on_fail={"op": "move", "mode": "fall", "note": "Into the 30-foot-deep, 10-foot-wide fissure."},
                                              note="Creatures where the optional fissure opens; structures there collapse.")], freq=DAWN))]))
    for nm, ab in (("Tome of Clear Thought", "int"), ("Tome of Leadership and Influence", "cha"), ("Tome of Understanding", "wis")):
        E.append(MI(nm, [
            ("^", "fx", act(mod(f"ability_score.{ab}", 2, note="To a maximum of 30."), cost="none", action=None, note="48 hours of study over 6 days or fewer.")),
            ("^", "rule", {"id": "study", "hours": 48, "within_days": 6, "max_score": 30, "then": "loses its magic", "regains_after_years": 100})]))
    E.append(MI("Trident of Fish Command", [
        ("^", "fx", [charges(3, "1d3"), act(cast("Dominate Beast", dc=15, note="On a Beast that has a Swim Speed."), uses=1,
                                            requires={"pred": "possesses_item", "args": THIS})])]))
    E.append(MI("Universal Solvent", [
        ("^", "rule", {"id": "tube", "found_ounces": "1d6 + 1"}),
        ("You can take a Utilize action", "rule", {"id": "dissolve", "action": "dnd5e/action/utilize", "sq_feet_per_ounce": 1,
                                                   "dissolves": ["adhesive", "dnd5e/magic-item/sovereign-glue"]})]))
    E.append(MI("Vicious Weapon", [
        ("^", "fx", trig("hits_with_attack_roll", dmg("2d6", {"var": "weapon_damage_type"}, target=INHERIT),
                         condition={"pred": "attack_uses_weapon", "args": THIS}))]))
    E.append(MI("Vorpal Sword", [
        ("^", "fx", plus_weapon(3) + [{"op": "restrict", "restrictions": ["resistance_to_slashing_applies"], "when": {"pred": "attack_uses_weapon", "args": THIS},
                                       "note": "Ignores Resistance to Slashing damage."}]),
        ("When you use this weapon", "fx", trig("rolls_natural_20_attack", {"op": "choice", "id": "head", "choose": 1, "chooser": "gm", "options": [
            {"id": "beheaded", "label": "Head cut off", "effects": [DIES | {"note": "Dies if it can't survive without the lost head."}]},
            {"id": "immune", "label": "Immune (Slashing immunity, no head needed, too big) or Legendary Resistance", "effects": [dmg(30, "slashing", target=INHERIT)]}]},
            condition={"all": [{"pred": "attack_uses_weapon", "args": THIS}, {"pred": "has_head"}]})),
        ("When you use this weapon", "md", md("too_big", "Is the creature too big for its head to be cut off with this weapon?",
                                              "if the GM decides that the creature is too big for its head to be cut off with this weapon"))]))
    E.append(MI("Wand of Binding", [
        wand_charges(),
        ("***Spells.***", "fx", staff_spells("Wand of Binding", dc=17)),
        ("| **Spell**", "table", tab("Wand of Binding", ["Spell", "Charge Cost"], [list(p) for p in spell_pairs("Wand of Binding")])),
        wand_regain()]))
    E.append(MI("Wand of Enemy Detection", [
        ("^", "fx", [charges(7), act(ref("dnd5e/magic-item/wand-of-enemy-detection", duration=mins(1, ends_on=[{"event": "unequips_item"}]),
                                         note="Direction (not distance) of the nearest Hostile creature within 60 feet, even Invisible, ethereal, disguised or hidden."),
                                     uses=1, requires=HOLD)]),
        wand_regain()]))
    E.append(MI("Wand of Fear", [
        wand_charges(),
        ("***Spells.***", "fx", [act(cast("Command", dc=15, note="“Flee” or “grovel” only."), uses=1, requires=HOLD),
                                 act(cast("Fear", dc=15, note="60-foot Cone."), uses=3, requires=HOLD)]),
        ("| **Spell**", "table", tab("Wand of Fear", ["Spell", "Charge Cost"], [list(p) for p in spell_pairs("Wand of Fear")])),
        wand_regain()]))
    E.append(upcast_wand("Wand of Fireballs", "Fireball", 3, dc=15))
    E.append(upcast_wand("Wand of Lightning Bolts", "Lightning Bolt", 3, dc=15))
    E.append(MI("Wand of Magic Detection", [("^", "fx", [charges(3, "1d3"), act(cast("Detect Magic"), uses=1, requires=HOLD)])]))
    E.append(upcast_wand("Wand of Magic Missiles", "Magic Missile", 1))
    E.append(MI("Wand of Paralysis", [
        ("^", "fx", [charges(7), act(save("con", 15, on_fail=cond("paralyzed", mins(1)), repeat=EACH_END, target=creature(60, must_see=True)),
                                     uses=1, requires=HOLD)]),
        wand_regain()]))
    E.append(MI("Wand of Polymorph", [("^", "fx", [charges(7), act(cast("Polymorph", dc=15), uses=1, requires=HOLD)]), wand_regain()]))
    E.append(MI("Wand of Secrets", [
        ("^", "fx", [charges(3, "1d3"), act(ref("dnd5e/magic-item/wand-of-secrets", note="Points at the nearest secret door or trap within 60 feet."),
                                            uses=1, requires=HOLD)])]))
    E.append(MI("Wand of the War Mage, +1, +2, or +3", [
        ("^", "fx", [mod("spell_attack_bonus", {"var": "item_bonus"}, HOLD),
                     {"op": "restrict", "restrictions": ["half_cover_against_spell_attacks"], "when": HOLD, "note": "You ignore Half Cover on spell attack rolls."}])]))
    E.append(MI("Wand of Web", [("^", "fx", [charges(7), act(cast("Web", dc=13), uses=1, requires=HOLD)]), wand_regain()]))
    wonder = item_nodes("Wand of Wonder")
    E.append(MI("Wand of Wonder", [
        ("^", "fx", [charges(7), act(ref("dnd5e/magic-item/wand-of-wonder", note="Choose a point within 120 feet; roll 1d100 on the Wand of Wonder Effects table."),
                                     uses=1, requires=HOLD)]),
        ("^", "rule", {"id": "numbers", "save_dc": 15, "min_range_feet": 120}),
        ("^", "md", md("wonder_subjects", "Which of several possible subjects are affected?",
                       "If an effect has multiple possible subjects, the GM determines randomly which among them are affected.", reason="not_automatable")),
        wand_regain(DESTROYED | {"note": "The wand crumbles into dust and is destroyed."}),
        ("##### Wand of Wonder Effects", "table", tab("Wand of Wonder Effects", ["1d100", "Effect"], rows_of(wonder)))]))
    E.append(MI("Weapon, +1, +2, or +3", [("^", "fx", [mod("attack_roll", {"var": "item_bonus"}, WIELD), mod("damage_roll", {"var": "item_bonus"}, WIELD)])]))
    near = {"all": [ATTUNED, {"pred": "within_feet_of_item", "args": {"feet": 30, "item": "this"}}]}
    E.append(MI("Weapon of Warning", [
        ("^", "rule", {"id": "subjects", "you_and_allies_within_feet": 30, "weapon_within_reach": True}),
        ("***Alarm.***", "fx", trig({"event": "initiative_rolled", "whose": "any", "which": "each"},
                                    {"op": "remove_condition", "conditions": ["dnd5e/condition/unconscious"], "note": "Natural sleep only, not magical sleep."},
                                    condition=near)),
        ("***Supernatural Readiness.***", "fx", adv("initiative", near))]))
    E.append(MI("Well of Many Worlds", [
        ("^", "rule", {"id": "cloth", "unfolded_diameter_feet": 6}),
        ("You can take a Magic action to unfold", "fx", act(ref("dnd5e/magic-item/well-of-many-worlds",
                                                                note="Two-way, 6-foot portal to another world or plane; closed by a creature within 5 feet (Magic action)."))),
        ("You can take a Magic action to unfold", "md", md("well_destination", "Where does this portal lead?", "Each time the item opens a portal, the GM decides where it leads.")),
        ("Once the *Well of Many Worlds*", "rule", {"id": "recharge", "hours": "1d8"})]))
    E.append(MI("Wind Fan", [
        ("^", "fx", act(cast("Gust of Wind", dc=13), requires=HOLD)),
        ("^", "rule", {"id": "failure", "cumulative_percent_per_use": 20, "resets": "dawn", "on_failure": "tears into nonmagical tatters"})]))
    E.append(MI("Winged Boots", [
        ("^", "fx", [charges(4, "1d4"), act(speed("fly", 30, duration=hours(1)), uses=1, requires=WEAR)]),
        ("^", "rule", {"id": "expiry", "descent_feet_per_round": 30})]))
    E.append(MI("Wings of Flying", [
        ("^", "fx", act(speed("fly", 60, duration=hours(1, ends_on=[{"event": "effect_ends"}])), requires=WEAR,
                        note="Ends early as a Magic action; if aloft when the wings vanish, you fall.")),
        ("^", "rule", {"id": "recharge", "hours": "1d12"})]))
    return E


if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
