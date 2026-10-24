#!/usr/bin/env python3
"""L31 — Magic items A–Z, part 5 (Rod of Alertness … Sword of Wounding; Spell Scroll is L32).

Usage: python3 -I tools/build/l31_items_e.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import extend_registries, write_entry  # noqa: E402
from magiclib import (ATTUNED, DAWN, DESTROYED, DIES, HOLD, INHERIT, MI, SELF, SP, THIS, WEAR, WIELD, act, adv,  # noqa: E402
                      area, cast, charges, check, cond, creature, dmg, hours, item_nodes, last_charge, md, mins, mod,
                      ref, resist, rows_of, save, sense, setv, speed, spells_table, tab, trig, until_turn, while_)
from l31_registry import REGISTRY  # noqa: E402

LOT = "L31"
EACH_END = {"on": {"event": "turn_end", "whose": "target", "which": "each"}, "ends": "effect_on_self"}
POSSESS = {"pred": "possesses_item", "args": THIS}
YOUR_DC = {"var": "spell_save_dc"}
MELEE_HIT = {"all": [{"pred": "attack_uses_weapon", "args": THIS}, {"pred": "attack_is_melee"}]}


def plus_weapon(n, when=WIELD):
    return [mod("attack_roll", n, when), mod("damage_roll", n, when)]


def spell_pairs(name):
    """(spell, cost) pairs from a staff's charge table (one or two spells per row)."""
    out = []
    for r in rows_of(item_nodes(name)):
        for k in range(0, len(r) - 1, 2):
            if r[k] and not r[k].startswith("("):
                out.append((r[k], r[k + 1]))
    return out


def staff_spells(name, dc=YOUR_DC, levels=None, attack=None):
    acts = []
    for spell, cost in spell_pairs(name):
        base = spell.split(" (")[0]
        lvl = (levels or {}).get(spell)
        n = int(cost) if cost.isdigit() else {"var": "spell_level"}
        acts.append(act(cast(base, level=lvl, dc=dc, attack=attack), uses=n, requires=HOLD))
    return acts


def regain(amount, on_1=None, on_20=None):
    fx = [trig({"event": "dawn", "which": "each"}, {"op": "restore", "resource": "charges", "amount": amount})]
    if on_1:
        fx.append(last_charge(on_1))
    if on_20:
        fx.append(trig("expends_last_charge", {"op": "choice", "id": "d20_20", "choose": 1, "note": "On a 20:", "options": [
            {"id": "twenty", "label": "20", "effects": on_20 if isinstance(on_20, list) else [on_20]},
            {"id": "other", "label": "1–19", "effects": [ref("dnd5e/rule/magic-items", note="No further effect.")]}]}))
    return fx


def retributive(per):
    return act([{"op": "choice", "id": "escape", "choose": 1, "note": "50 percent chance to travel to a random plane, avoiding the explosion.", "options": [
        {"id": "escape", "label": "Escape (50%)", "effects": [{"op": "move", "mode": "teleport", "note": "To a random plane of existence."}]},
        {"id": "caught", "label": "Caught (50%)", "effects": [dmg({"op": "mul", "args": [16, {"var": "resource.charges"}]}, "force", target=SELF)]}]},
                save("dex", 17, on_fail=dmg({"op": "mul", "args": [per, {"var": "resource.charges"}]}, "force"), half=True,
                     target={"kind": "area", "area": {"shape": "emanation", "size_feet": 30, "origin": "object"}, "filter": {"include_self": False}}),
                DESTROYED], requires=HOLD, name="Retributive Strike")


def entries():
    E = []
    E.append(MI("Rod of Alertness", [
        ("^", "desc", None),
        ("***Alertness.***", "fx", adv(["initiative", "ability_check"], {"all": [HOLD, {"any": [{"pred": "roll_is", "args": {"roll": "initiative"}},
                                                                                                {"pred": "check_uses_skill", "args": {"skill": "perception"}}]}]})),
        ("***Spells.***", "fx", [act(cast(s), requires=HOLD) for s in ("Detect Evil and Good", "Detect Magic", "Detect Poison and Disease", "See Invisibility")]),
        ("- *Detect Evil and Good*", "sys", ["/effects/1"]),
        ("- *Detect Magic*", "sys", ["/effects/2"]),
        ("- *Detect Poison and Disease*", "sys", ["/effects/3"]),
        ("- *See Invisibility*", "sys", ["/effects/4"]),
        ("***Protective Aura.***", "fx", act([mod("ac", 1, {"pred": "in_item_light", "args": THIS}), mod("saving_throw", 1, {"pred": "in_item_light", "args": THIS}),
                                              ref("dnd5e/condition/invisible", note="Sense the location of Invisible creatures in the Bright Light.")],
                                             freq=DAWN, duration=mins(10), note="You and your allies in the Bright Light (60 feet)."),),
        ("***Protective Aura.***", "rule", {"id": "aura_light", "bright_feet": 60, "dim_feet": 60}),
        ("The rod’s head stops glowing", "rule", {"id": "aura_end", "minutes": 10, "ends_on": "a creature pulls the rod out (Magic action)"})]))
    fire_blade = {"all": [{"pred": "item_form_in", "args": {"forms": ["button_1"]}}, {"pred": "attack_uses_weapon", "args": THIS}]}
    E.append(MI("Rod of Lordly Might", [
        ("^", "fx", plus_weapon(3, HOLD)),
        ("^", "rule", {"id": "mace", "functions_as": "dnd5e/weapon/mace", "buttons": 6}),
        ("***Buttons.***", "rule", {"id": "buttons", "cost": "bonus_action", "lasts": "until another button or the same again (normal form)"}),
        ("**Button 1.**", "fx", trig("hits_with_attack_roll", dmg("2d6", "fire", target=INHERIT), condition=fire_blade)),
        ("**Button 1.**", "rule", {"id": "button_1", "as": ["dnd5e/weapon/longsword", "dnd5e/weapon/shortsword"], "bright_feet": 40, "dim_feet": 40}),
        ("**Button 2.**", "rule", {"id": "button_2", "as": "dnd5e/weapon/battleaxe", "bonus": 3}),
        ("**Button 3.**", "rule", {"id": "button_3", "as": "dnd5e/weapon/spear", "bonus": 3, "haft_feet": 6}),
        ("**Button 4.**", "rule", {"id": "button_4", "pole_feet_max": 50, "rungs_inches": 3, "rung_spacing_feet": 1, "max_lb": 4000}),
        ("**Button 5.**", "fx", mod("ability_check", 10, {"all": [{"pred": "item_form_in", "args": {"forms": ["button_5"]}},
                                                                 {"pred": "check_uses_skill", "args": {"skill": "athletics"}}, {"pred": "breaking_down_door"}]},
                                    note="Doors, barricades and other barriers.")),
        ("**Button 6.**", "rule", {"id": "button_6", "indicates": "magnetic_north", "depth_or_height": True}),
        ("***Drain Life.***", "fx", trig("hits_with_attack_roll", save("con", 17, on_fail=[dmg("4d6", "necrotic"),
                                                                                           {"op": "heal", "target": SELF, "amount": {"op": "div", "args": [{"var": "damage_amount"}, 2]}}],
                                                                       target=INHERIT), optional=True, frequency=DAWN, condition=MELEE_HIT)),
        ("***Paralyze.***", "fx", trig("hits_with_attack_roll", save("con", 17, on_fail=cond("paralyzed", mins(1)), repeat=EACH_END, target=INHERIT),
                                       optional=True, frequency=DAWN, condition=MELEE_HIT)),
        ("***Terrify.***", "fx", act(save("wis", 17, on_fail=cond("frightened", mins(1)), repeat=EACH_END,
                                          target={"kind": "area", "area": {"shape": "emanation", "size_feet": 30, "origin": "self"},
                                                  "filter": {"predicate": {"pred": "can_see"}}}), freq=DAWN, requires=HOLD))]))
    E.append(MI("Rod of Resurrection", [
        ("^", "fx", [charges(5), act(cast("Heal"), uses=1, requires=HOLD), act(cast("Resurrection"), uses=5, requires=HOLD)]),
        ("The rod regains", "fx", regain(1, {"op": "end_effect", "scope": "this_entry", "note": "The rod disappears in a harmless burst of radiance."}))]))
    E.append(MI("Rod of Rulership", [
        ("^", "fx", act(save("wis", 15, on_fail=cond("charmed", hours(8)),
                             target={"kind": "creature", "range": {"kind": "distance", "feet": 120}, "must_see": True, "count": {"var": "chosen"},
                                     "filter": {"predicate": {"pred": "chosen_by_source"}}},
                             note="Regards you as its trusted leader; ends if harmed by you or allies or commanded against its nature."), freq=DAWN))]))
    E.append(MI("Rod of Security", [
        ("^", "fx", act({"op": "move", "mode": "teleport", "note": "You and up to 199 willing creatures you can see go to a demiplane of your design."},
                        requires=HOLD, note="Can't be used again until 10 days have passed.")),
        ("^", "rule", {"id": "demiplane", "max_creatures": 200, "food_and_water": True, "harmless_environment": True, "objects_cannot_leave": True}),
        ("For each hour spent", "fx", trig({"event": "hour_elapsed", "which": "each"}, {"op": "heal", "amount": {"var": "hit_point_die"},
                                                                                         "note": "As if it spent 1 Hit Point Die."})),
        ("For each hour spent", "rule", {"id": "stay", "no_aging": True, "max_days": {"op": "div", "args": [200, {"var": "creatures_present"}]}}),
        ("When the time runs out", "rule", {"id": "return", "to": "original location or nearest unoccupied", "recharge_days": 10})]))
    rope_stats = {"id": "durability", "ac": 20, "hp": 20, "immunities": ["poison", "psychic"], "regains_hp": {"amount": 1, "every_minutes": 5}, "destroyed_at_0": True}
    E.append(MI("Rope of Climbing", [
        ("^", "rule", {"id": "rope", "length_feet": 60, "max_lb": 3000}),
        ("^", "fx", act(ref("dnd5e/magic-item/rope-of-climbing", note="The other end moves 10 feet a turn toward a destination; it can fasten, unfasten, knot, unknot or coil."),
                        requires=HOLD)),
        ("If you tell the rope to knot", "fx", adv("ability_check", {"pred": "check_for_movement", "args": {"modes": ["climb"]}}, note="Knotted rope (50 feet).")),
        ("The rope has AC 20", "rule", rope_stats)]))
    E.append(MI("Rope of Entanglement", [
        ("^", "fx", act(save("dex", 15, on_fail=cond("restrained"), target=creature(20, must_see=True)), requires=HOLD)),
        ("^", "rule", {"id": "rope", "length_feet": 30, "release": ["let go", "repeat command (bonus action)"]}),
        ("A target Restrained by the rope", "fx", {"op": "choice", "id": "escape", "choose": 1, "chooser": "target", "note": "Takes an action.", "options": [
            {"id": "athletics", "label": "Strength (Athletics)", "effects": [check("str", 15, skill="athletics", on_success={"op": "remove_condition", "conditions": ["dnd5e/condition/restrained"]})]},
            {"id": "acrobatics", "label": "Dexterity (Acrobatics)", "effects": [check("dex", 15, skill="acrobatics", on_success={"op": "remove_condition", "conditions": ["dnd5e/condition/restrained"]})]}]}),
        ("A target Restrained by the rope", "rule", {"id": "coil", "reaction_to_your_hand": True}),
        ("The rope has AC 20", "rule", rope_stats)]))
    E.append(MI("Scarab of Protection", [
        ("^", "desc", None),
        ("***Defense.***", "fx", mod("ac", 1, POSSESS)),
        ("***Preservation.***", "fx", [charges(12), trig("fails_saving_throw", {"op": "auto_result", "rolls": ["saving_throw"], "result": "success"},
                                                         cost="reaction", optional=True,
                                                         condition={"all": [POSSESS, {"any": [{"pred": "spell_school", "args": {"school": "necromancy"}},
                                                                                              {"pred": "source_creature_type_in", "args": {"types": ["undead"]}}]}]},
                                                         note="Expend 1 charge; the scarab is destroyed when the last is expended.")]),
        ("***Spell Resistance.***", "fx", adv("saving_throw", {"all": [POSSESS, {"pred": "save_against_spell"}]}))]))
    E.append(MI("Scimitar of Speed", [
        ("^", "fx", plus_weapon(2) + [act({"op": "attack", "attack_type": "melee_weapon", "note": "One attack with this weapon."},
                                          cost="bonus_action", requires=WIELD, freq={"count": 1, "per": "turn"})])]))
    E.append(MI("Sending Stones", [
        ("^", "fx", act(cast("Sending", note="The target is the bearer of the other stone; if none, you know it and don't cast."),
                        requires={"pred": "touching_item", "args": THIS}, freq=DAWN)),
        ("Once *Sending* is cast", "rule", {"id": "pair", "shared_daily_use": True, "one_destroyed": "other becomes nonmagical"})]))
    E.append(MI("Sentinel Shield", [
        ("^", "fx", adv(["initiative", "ability_check"], {"all": [HOLD, {"any": [{"pred": "roll_is", "args": {"roll": "initiative"}},
                                                                               {"pred": "check_uses_skill", "args": {"skill": "perception"}}]}]})),
        ("^", "desc", None)]))
    E.append(MI("Shield, +1, +2, or +3", [("^", "fx", mod("ac", {"var": "item_bonus"}, HOLD, note="In addition to the Shield's normal bonus."))]))
    E.append(MI("Shield of Missile Attraction", [
        ("^", "fx", resist(["bludgeoning", "piercing", "slashing", "acid", "cold", "fire", "force", "lightning", "necrotic", "poison", "psychic", "radiant", "thunder"],
                           {"all": [HOLD, {"pred": "attack_with_ranged_weapon"}]}, note="Damage from attacks made with Ranged weapons.")),
        ("***Curse.***", "ref", ["dnd5e/rule/cursed-items"]),
        ("***Curse.***", "rule", {"id": "curse", "ends_by": [SP("Remove Curse")], "removing_item_ends": False}),
        ("***Curse.***", "fx", trig({"event": "ranged_attack_against_creature_within_feet", "whose": "any", "which": "each"},
                                    ref("dnd5e/magic-item/shield-of-missile-attraction", note="You become the target instead (within 10 feet)."),
                                    condition=ATTUNED))]))
    E.append(MI("Shield of the Cavalier", [
        ("^", "fx", mod("ac", 2, HOLD, note="In addition to the Shield's normal bonus.")),
        ("The Shield has the following", "desc", None),
        ("***Forceful Bash", "fx", trig("attack_action_attack", {"op": "attack", "attack_type": "melee",
                                                                 "bonus": {"op": "add", "args": [{"var": "proficiency_bonus"}, {"var": "ability_mod.str"}]},
                                                                 "on_hit": [dmg({"op": "add", "args": ["2d6", 2, {"var": "ability_mod.str"}]}, "force"),
                                                                            {"op": "move", "mode": "push", "distance_feet": 10},
                                                                            cond("prone", note="If the creature is your size or smaller (optional).")]},
                                        optional=True, condition=HOLD, note="One attack roll of the Attack action, against a target within 5 feet.")),
        ("***Protective Field.***", "fx", trig({"event": "targeted_by_attack_or_area", "whose": "any", "which": "each"},
                                               ref("dnd5e/magic-item/shield-of-the-cavalier",
                                                   duration={"kind": "minutes", "amount": 1, "up_to": True, "concentration": True},
                                                   note="Immobile 5-foot Emanation; creatures outside pushed out; the triggering attack or area has no effect inside; nothing passes in or out."),
                                               cost="reaction", optional=True, frequency=DAWN,
                                               condition={"all": [HOLD, {"pred": "within_feet", "args": {"feet": 5}}]}))]))
    E.append(MI("Slippers of Spider Climbing", [
        ("^", "fx", [{"op": "modifier", "stat": "spider_climb", "mode": "set", "value": 1, "when": {"all": [WEAR, {"not": {"pred": "on_slippery_surface"}}]}},
                     speed("climb", 0, mode="equal_to_walk", when=WEAR)])]))
    E.append(MI("Sovereign Glue", [
        ("^", "rule", {"id": "storage", "container_coated_with": "dnd5e/magic-item/oil-of-slipperiness", "found_ounces": "1d6 + 1"}),
        ("One ounce of the glue", "rule", {"id": "bond", "coverage_sq_feet_per_ounce": 1, "apply": "dnd5e/action/utilize", "set_minutes": 1,
                                           "broken_by": ["dnd5e/magic-item/universal-solvent", "dnd5e/magic-item/oil-of-etherealness", SP("Wish")]})]))
    E.append(MI("Spellguard Shield", [
        ("^", "fx", [adv("saving_throw", {"all": [HOLD, {"pred": "save_against_spell_or_magic"}]}),
                     adv("attack_roll", {"all": [HOLD, {"pred": "attack_is_spell"}]}, mode="disadvantage", direction="against")])]))
    sphere = item_nodes("Sphere of Annihilation")
    E.append(MI("Sphere of Annihilation", [
        ("^", "rule", {"id": "sphere", "diameter_feet": 2}),
        ("The sphere obliterates", "fx", trig({"event": "touches_effect", "whose": "any", "which": "each"}, dmg("8d10", "force"),
                                              note="Obliterates matter that passes through it; Artifacts pass unscathed unless susceptible.")),
        ("***Controlling the Sphere.***", "fx", act(check("int", 25, skill="arcana",
                                                          on_success=ref("dnd5e/magic-item/sphere-of-annihilation", note="You control it until the start of your next turn."),
                                                          on_fail={"op": "move", "mode": "pull", "distance_feet": 10, "note": "The sphere moves 10 feet toward you."}),
                                                    requires={"pred": "within_feet_of_item", "args": {"feet": 60, "item": "this"}})),
        ("While in control of the sphere", "fx", act(save("dex", 19, on_fail=[dmg("8d10", "force"),
                                                                              ref("dnd5e/magic-item/sphere-of-annihilation", note="Reduced to 0 HP: obliterated, possessions left behind.")],
                                                          note="Moves up to 5 × Intelligence modifier feet (min 5); each creature whose space it enters."),
                                                     cost="bonus_action", requires={"pred": "controls_item", "args": THIS})),
        ("***Sphere Interactions.***", "md", md("sphere_interaction", "Roll 1d100 when the sphere contacts a portal or extradimensional space.",
                                                "the GM determines randomly what happens using the following table", reason="not_automatable")),
        ("| **1d100**", "table", tab("Sphere of Annihilation", ["1d100", "Result"], rows_of(sphere)))]))
    E.append(MI("Staff of Charming", [
        ("^", "fx", charges(10)),
        ("**Cast Spell.**", "fx", [act(cast(s, dc=YOUR_DC), uses=1, requires=HOLD) for s in ("Charm Person", "Command", "Comprehend Languages")]),
        ("**Reflect Enchantment.**", "fx", trig("succeeds_saving_throw", ref("dnd5e/magic-item/staff-of-charming", note="Turn the spell back on its caster as if you cast it."),
                                                cost="reaction", optional=True,
                                                condition={"all": [HOLD, {"pred": "spell_school", "args": {"school": "enchantment"}}, {"pred": "spell_targeted_only_you"}]},
                                                note="Expend 1 charge.")),
        ("**Resist Enchantment.**", "fx", trig("fails_saving_throw", {"op": "auto_result", "rolls": ["saving_throw"], "result": "success"}, optional=True,
                                               frequency=DAWN,
                                               condition={"all": [HOLD, {"pred": "spell_school", "args": {"school": "enchantment"}}, {"pred": "spell_targeted_only_you"}]})),
        ("***Regaining Charges.***", "fx", regain("1d8 + 2", DESTROYED))]))
    for nm, dtype, death in (("Staff of Fire", "fire", "crumbles into cinders"), ("Staff of Frost", "cold", "turns to water")):
        E.append(MI(nm, [
            ("^", "fx", resist(dtype, HOLD)),
            ("***Spells.***", "fx", [charges(10)] + staff_spells(nm)),
            ("| *", "table", tab(nm, ["Spell", "Charge Cost"], [list(p) for p in spell_pairs(nm)])),
            ("***Regaining Charges.***", "fx", regain("1d6 + 4", DESTROYED | {"note": f"The staff {death} and is destroyed."}))]))
    E.append(MI("Staff of Healing", [
        ("^", "fx", [charges(10),
                     act(cast("Cure Wounds", level={"var": "charges_spent"}, note="1 charge per spell level, maximum 4.", ability={"var": "spellcasting_mod"}),
                         uses={"var": "charges_spent"}, requires=HOLD),
                     act(cast("Lesser Restoration"), uses=2, requires=HOLD),
                     act(cast("Mass Cure Wounds"), uses=5, requires=HOLD)]),
        ("| **Spell**", "table", tab("Staff of Healing", ["Spell", "Charge Cost"], [["Cure Wounds", "1 charge per spell level (maximum 4 for a level 4 spell)"],
                                                                                 ["Lesser Restoration", "2"], ["Mass Cure Wounds", "5"]])),
        ("***Regaining Charges.***", "fx", regain("1d6 + 4", DESTROYED | {"note": "The staff vanishes in a flash of light, lost forever."}))]))
    E.append(MI("Staff of Power", [
        ("^", "fx", [charges(20)] + plus_weapon(2, HOLD) + [mod("ac", 2, HOLD), mod("saving_throw", 2, HOLD), mod("spell_attack_bonus", 2, HOLD)]),
        ("^", "rule", {"id": "quarterstaff", "functions_as": "dnd5e/weapon/quarterstaff"}),
        ("***Spells.***", "fx", staff_spells("Staff of Power", levels={"Fireball (level 5 version)": 5, "Lightning Bolt (level 5 version)": 5})),
        ("| **Spell**", "table", tab("Staff of Power", ["Spell", "Charge Cost"], [list(p) for p in spell_pairs("Staff of Power")])),
        ("***Regaining Charges.***", "fx", regain("2d8 + 4", ref("dnd5e/magic-item/staff-of-power", note="Keeps its +2 to attack and damage rolls but loses all other properties."),
                                                  {"op": "restore", "resource": "charges", "amount": {"op": "add", "args": ["1d8", 2]}})),
        ("***Retributive Strike.***", "fx", retributive(4))]))
    E.append(MI("Staff of Striking", [
        ("^", "fx", plus_weapon(3, HOLD)),
        ("^", "rule", {"id": "quarterstaff", "functions_as": "dnd5e/weapon/quarterstaff"}),
        ("The staff has 10 charges", "fx", [charges(10), trig("hits_with_attack_roll",
                                                             [{"op": "spend", "resource": "charges", "amount": {"var": "charges_spent"}},
                                                              dmg({"dice": {"count": {"var": "charges_spent"}, "faces": 6}}, "force", target=INHERIT)],
                                                             optional=True, condition=MELEE_HIT, note="Up to 3 charges.")]),
        ("***Regaining Charges.***", "fx", regain("1d6 + 4", ref("dnd5e/weapon/quarterstaff", note="Becomes a nonmagical Quarterstaff.")))]))
    E.append(MI("Staff of Swarming Insects", [
        ("^", "fx", charges(10)),
        ("***Insect Cloud.***", "fx", act(ref("dnd5e/rule/heavily-obscured", target=area("emanation", 30, origin="self"), duration=mins(10),
                                              note="For creatures other than you; a strong wind (Gust of Wind) disperses it."), uses=1, requires=HOLD)),
        ("***Spells.***", "fx", staff_spells("Staff of Swarming Insects", attack={"var": "spell_attack_bonus"})),
        ("| **Spell**", "table", tab("Staff of Swarming Insects", ["Spell", "Charge Cost"], [list(p) for p in spell_pairs("Staff of Swarming Insects")])),
        ("***Regaining Charges.***", "fx", regain("1d6 + 4", DESTROYED | {"note": "A swarm of insects consumes and destroys the staff."}))]))
    E.append(MI("Staff of the Magi", [
        ("^", "fx", [charges(50)] + plus_weapon(2, HOLD) + [mod("spell_attack_bonus", 2, HOLD)]),
        ("^", "rule", {"id": "quarterstaff", "functions_as": "dnd5e/weapon/quarterstaff"}),
        ("***Spell Absorption.***", "fx", [adv("saving_throw", {"all": [HOLD, {"pred": "save_against_spell"}]}),
                                           trig("targeted_by_spell", {"op": "restore", "resource": "charges", "amount": {"var": "spell_level"},
                                                                      "note": "The spell is canceled; above 50 charges the staff explodes as Retributive Strike."},
                                                cost="reaction", optional=True, condition={"all": [HOLD, {"pred": "spell_targeted_only_you"}]})]),
        ("***Spells.***", "fx", staff_spells("Staff of the Magi", levels={"Fireball (level 7 version)": 7, "Lightning Bolt (level 7 version)": 7})),
        ("| **Spell**", "table", tab("Staff of the Magi", ["Spell", "Charge Cost"], [list(p) for p in spell_pairs("Staff of the Magi")])),
        ("***Regaining Charges.***", "fx", regain("4d6 + 2", on_20={"op": "restore", "resource": "charges", "amount": {"op": "add", "args": ["1d12", 1]}})),
        ("***Retributive Strike.***", "fx", retributive(6))]))
    E.append(MI("Staff of the Python", [
        ("^", "fx", act({"op": "summon", "creature": "dnd5e/creature/giant-constrictor-snake", "controller": "summoner", "initiative": "after_summoner",
                         "note": "Lands within 10 feet."}, freq={"count": 1, "per": "hour"})),
        ("On your turn, you can mentally command", "rule", {"id": "command", "cost": "none", "range_feet": 60, "not_incapacitated": True,
                                                            "general_orders": True, "no_orders": "defends_itself"}),
        ("As a Bonus Action, you can command the snake", "rule", {"id": "revert", "cost": "bonus_action", "recharge_hours": 1,
                                                                 "at_0_hp": "dies, reverts and the staff is destroyed", "early_revert_restores_hp": True})]))
    E.append(MI("Staff of the Woodlands", [
        ("^", "fx", [charges(6)] + plus_weapon(2, HOLD) + [mod("spell_attack_bonus", 2, HOLD)]),
        ("***Spells.***", "fx", staff_spells("Staff of the Woodlands")),
        ("| **Spell**", "table", tab("Staff of the Woodlands", ["Spell", "Charge Cost"], [list(p) for p in spell_pairs("Staff of the Woodlands")])),
        ("***Tree Form.***", "fx", act(ref("dnd5e/magic-item/staff-of-the-woodlands", note="A 60-foot tree (5-foot trunk, 20-foot crown); faint Transmutation aura; touch + Magic action reverts it; creatures in it fall."),
                                       uses=1)),
        ("***Regaining Charges.***", "fx", regain("1d6", ref("dnd5e/weapon/quarterstaff", note="Loses its properties; a nonmagical Quarterstaff.")))]))
    E.append(MI("Staff of Thunder and Lightning", [
        ("^", "fx", plus_weapon(2, HOLD)),
        ("^", "rule", {"id": "daily", "each_property": "once per dawn"}),
        ("***Lightning.***", "fx", trig("hits_with_attack_roll", dmg("2d6", "lightning", target=INHERIT), optional=True, frequency=DAWN, condition=MELEE_HIT)),
        ("***Thunder.***", "fx", trig("hits_with_attack_roll", save("con", 17, on_fail=cond("stunned", until_turn("turn_end")), target=INHERIT),
                                      optional=True, frequency=DAWN, condition=MELEE_HIT)),
        ("***Thunder and Lightning.***", "fx", trig("hits_with_attack_roll", ref("dnd5e/magic-item/staff-of-thunder-and-lightning",
                                                                                 note="Use Lightning and Thunder together without expending their daily uses."),
                                                    cost="bonus_action", optional=True, frequency=DAWN, condition=MELEE_HIT)),
        ("***Lightning Strike.***", "fx", act(save("dex", 17, on_fail=dmg("9d6", "lightning"), half=True,
                                                   target={"kind": "area", "area": {"shape": "line", "size_feet": 120, "width_feet": 5, "origin": "self"}}),
                                              freq=DAWN)),
        ("***Thunderclap.***", "fx", act(save("con", 17, on_fail=[dmg("2d6", "thunder"), cond("deafened", mins(1))], half=True,
                                              target=area("emanation", 60, origin="self"), note="Audible to 600 feet; success: half damage only."),
                                         freq=DAWN))]))
    E.append(MI("Staff of Withering", [
        ("^", "fx", charges(3, "1d3")),
        ("The staff can be wielded", "fx", trig("hits_with_attack_roll", [{"op": "spend", "resource": "charges", "amount": 1},
                                                                          dmg("2d10", "necrotic", target=INHERIT),
                                                                          save("con", 15, target=INHERIT, on_fail=adv(["ability_check", "saving_throw"],
                                                                                                                      {"any": [{"pred": "roll_uses_ability", "args": {"ability": "str"}},
                                                                                                                               {"pred": "roll_uses_ability", "args": {"ability": "con"}}]},
                                                                                                                      mode="disadvantage", duration=hours(1)))],
                                                optional=True, condition={"pred": "attack_uses_weapon", "args": THIS})),
        ("The staff can be wielded", "rule", {"id": "quarterstaff", "functions_as": "dnd5e/weapon/quarterstaff"})]))
    E.append(MI("Stone of Controlling Earth Elementals", [
        ("^", "fx", act({"op": "summon", "creature": "dnd5e/creature/earth-elemental", "controller": "summoner", "initiative": "after_summoner",
                         "duration": hours(1), "note": "Within 30 feet; dismiss as a Bonus Action."}, freq=DAWN,
                        requires={"pred": "touching_item", "args": THIS})),
        ("^", "rule", {"id": "stone", "weight_lb": 5, "touching_ground": True})]))
    E.append(MI("Stone of Good Luck (Luckstone)", [("^", "fx", [mod("ability_check", 1, POSSESS), mod("saving_throw", 1, POSSESS)])]))
    E.append(MI("Sun Blade", [
        ("^", "desc", None),
        ("***Blade of Radiance.***", "rule", {"id": "blade", "toggle": "bonus_action", "functions_as": "dnd5e/weapon/longsword",
                                              "properties": ["dnd5e/weapon-property/finesse"],
                                              "proficient_if": ["dnd5e/weapon/longsword", "dnd5e/weapon/shortsword"]}),
        ("You gain a +2 bonus", "fx", plus_weapon(2) + [trig("hits_with_attack_roll", dmg("1d8", "radiant", target=INHERIT),
                                                             condition={"all": [{"pred": "attack_uses_weapon", "args": THIS},
                                                                                {"pred": "creature_type_in", "args": {"types": ["undead"]}}]})]),
        ("You gain a +2 bonus", "rule", {"id": "radiant", "damage_type": "radiant", "replaces": "slashing"}),
        ("***Sunlight.***", "rule", {"id": "sunlight", "bright_feet": 15, "dim_feet": 15, "is_sunlight": True,
                                     "adjust": {"cost": "dnd5e/action/magic", "step_feet": 5, "min_feet": 10, "max_feet": 30}})]))
    E.append(MI("Sword of Life Stealing", [
        ("^", "fx", trig("rolls_natural_20_attack", [dmg(15, "necrotic", target=INHERIT), {"op": "temp_hp", "amount": {"var": "damage_amount"}, "target": SELF}],
                         condition={"all": [{"pred": "attack_uses_weapon", "args": THIS},
                                            {"not": {"pred": "creature_type_in", "args": {"types": ["construct", "undead"]}}}]}))]))
    E.append(MI("Sword of Sharpness", [
        ("^", "fx", {"op": "modifier", "stat": "damage_roll", "mode": "set", "value": {"var": "weapon_damage_max"},
                     "when": {"all": [{"pred": "attack_uses_weapon", "args": THIS}, {"pred": "target_is_object"}]},
                     "note": "Maximize the weapon damage dice against objects."}),
        ("When you attack a creature", "fx", trig("rolls_natural_20_attack", [dmg(14, "slashing", target=INHERIT),
                                                                              cond("exhaustion", target=INHERIT, params={"levels": 1})],
                                                  condition={"pred": "attack_uses_weapon", "args": THIS}))]))
    E.append(MI("Sword of Wounding", [
        ("^", "fx", trig("hits_with_attack_roll", [dmg("2d6", "necrotic", target=INHERIT),
                                                   save("con", 15, on_fail={"op": "restrict", "restrictions": ["regain_hit_points"], "duration": hours(1)},
                                                        repeat=EACH_END, target=INHERIT)],
                         condition={"pred": "attack_uses_weapon", "args": THIS}))]))
    return E


if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
