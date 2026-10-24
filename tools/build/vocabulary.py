"""Canonical vocabulary of the catalog: one name per concept, parameters instead of variants.

Lot builders may still write the older, specific names (e.g. `wearing_item`); every entry and
the system file are normalized on write (entrylib.write_entry, entrylib.extend_registries),
so the published catalog only contains the canonical names below. An engine therefore
implements one predicate per concept, e.g. `item_state {item, state}` instead of eleven
"wearing / wielding / holding / attuned ..." predicates.

ALIASES:  old name -> (canonical name, function(args) -> canonical args)
CANONICAL: canonical predicates and events with their parameters (registry definitions)
"""
import copy

# ---------------------------------------------------------------- canonical definitions

CANONICAL_PREDICATES = {
    "attack_is": ("The attack roll matches every given criterion: range (melee|ranged), via (weapon|spell|unarmed_strike), "
                  "item (weapon or item slug, list of weapon slugs, or 'this'), property (weapon properties), weapon_kind "
                  "(monk|pact|mastered|chosen), attack_kind (opportunity|light_property_extra|wild_shape_form|feature), "
                  "feature (granting feature slug), ability (attack ability).",
                  ["range", "via", "item", "property", "weapon_kind", "attack_kind", "feature", "ability"]),
    "hp_is": ("The creature's Hit Points satisfy every given criterion: at_most N, below N, zero (0 HP), bloodied "
              "(half or fewer), missing_any (below maximum).", ["at_most", "below", "zero", "bloodied", "missing_any"]),
    "save_against": ("The saving throw is against: source (spell|magic|spell_or_magic|contagion), spell (slug), condition "
                     "(slug), hazard (slug), types (creature types causing the effect), effect (kind of effect, e.g. "
                     "breath_weapon, possession), kind (concentration), modified_by (e.g. extended_spell).",
                     ["source", "spell", "condition", "hazard", "types", "effect", "kind", "modified_by"]),
    "check_uses": ("The ability check uses: skill (id or 'any'), ability (id), tool, proficient (skill|tool|any, or false "
                   "for a skill the creature lacks), adds_proficiency_bonus (true when it already adds it).",
                   ["skill", "ability", "tool", "proficient", "adds_proficiency_bonus"]),
    "creature_is": ("The creature (who: target by default, or attacker|source) has one of these types, tags or species; "
                    "chosen = the type fixed by an earlier choice (choice id or true).",
                    ["types", "tags", "species", "who", "chosen"]),
    "spell_level_in": ("The spell, as cast, is of a level within [min, max] (either bound optional).", ["min", "max"]),
    "item_state": ("The item (slug, kind or 'this') is in this state for the creature: worn|wielded|held|possessed|attuned|"
                   "touching|gripping|ridden|played|controlled|orbiting.", ["item", "state"]),
    "within_feet": ("A creature (who: self by default, or attacker|ally|enemy|...) is within 'feet' of the reference "
                    "(of: self by default, or target|item|effect); not_incapacitated / sees qualify that creature; "
                    "farther inverts the test (more than 'feet').", ["who", "of", "feet", "item", "not_incapacitated", "sees", "farther"]),
    "level_at_least": ("The character has at least 'level' levels in 'class' (a class slug, a list of slugs = any of them), "
                       "or in total when 'class' is omitted.", ["class", "level"]),
    "in_light": ("The creature is in light of this level: bright|dim|darkness|sunlight.", ["level"]),
    "obscured": ("The creature or thing looked at is in an area obscured to this degree: light|heavy.", ["degree"]),
    "can_see": ("The observer (who: the effect's owner by default, or attacker|source|target|...) can see the observed "
                "(target: the effect's target by default, or self|attacker|effect|...).", ["who", "target"]),
    "has_condition": ("The creature has the condition (slug), optionally from a given source.", ["condition", "source"]),
    "spell_of_class": ("The spell is a spell of this class for the creature; cantrip limits it to cantrips.", ["class", "cantrip"]),
    "is_critical_hit": ("The attack roll is a Critical Hit.", []),
}

CANONICAL_EVENTS = {}

# ---------------------------------------------------------------- aliases


def _set(**fixed):
    return lambda a: {**fixed, **a}


def _ren(old, new, **fixed):
    def f(a):
        a = dict(a)
        if old in a:
            a[new] = a.pop(old)
        return {**fixed, **a}
    return f


def _weapon(a):
    a = dict(a)
    out = {"via": "weapon"}
    if "weapon" in a:
        out["item"] = a.pop("weapon")
    out.update(a)
    return out


def _hp(key):
    return lambda a: {key: a["hp"]}


def _level_is(a):
    return {"min": a["level"], "max": a["level"]}


def _class_is(a):
    return {"class": a["classes"], "level": 1}


def _creature_type(a):
    return {"types": [a["creature_type"]] if "creature_type" in a else [a["type"]]}


def _forced(a):
    return {"types": [a["type"]]}


def _chosen(a):
    return {"chosen": a.get("choice", True)}


ALIASES = {
    # attack family
    "attack_is_melee": ("attack_is", _set(range="melee")),
    "attack_is_ranged": ("attack_is", _set(range="ranged")),
    "attack_is_spell": ("attack_is", _set(via="spell")),
    "attack_is_unarmed_strike": ("attack_is", _set(via="unarmed_strike")),
    "attack_with_melee_weapon": ("attack_is", _set(range="melee", via="weapon")),
    "attack_with_ranged_weapon": ("attack_is", _set(range="ranged", via="weapon")),
    "attack_uses_weapon": ("attack_is", _weapon),
    "attack_with_weapon_property": ("attack_is", _set(via="weapon")),
    "attack_with_light_weapon": ("attack_is", _set(via="weapon", property=["light"])),
    "attack_with_monk_weapon": ("attack_is", _set(via="weapon", weapon_kind="monk")),
    "attack_with_pact_weapon": ("attack_is", _set(via="weapon", weapon_kind="pact")),
    "attack_with_mastered_weapon": ("attack_is", _set(via="weapon", weapon_kind="mastered")),
    "attack_with_chosen_weapon": ("attack_is", _set(via="weapon", weapon_kind="chosen")),
    "attack_is_opportunity_attack": ("attack_is", _set(attack_kind="opportunity")),
    "extra_attack_from_light_property": ("attack_is", _set(attack_kind="light_property_extra")),
    "wild_shape_form_attack": ("attack_is", _set(attack_kind="wild_shape_form")),
    "attack_from_feature": ("attack_is", _set(attack_kind="feature")),
    "attack_uses_ability": ("attack_is", _set()),
    # hit points
    "hp_at_most": ("hp_is", _hp("at_most")),
    "hp_below": ("hp_is", _hp("below")),
    "at_zero_hp": ("hp_is", _set(zero=True)),
    "bloodied": ("hp_is", _set(bloodied=True)),
    "target_missing_hit_points": ("hp_is", _set(missing_any=True)),
    # saving throws
    "save_against_spell": ("save_against", _set(source="spell")),
    "save_against_spell_or_magic": ("save_against", _set(source="spell_or_magic")),
    "save_against_condition": ("save_against", _set()),
    "save_against_hazard": ("save_against", _set()),
    "save_against_contagion": ("save_against", _set(source="contagion")),
    "save_against_effect_of_types": ("save_against", _set()),
    "concentration_save": ("save_against", _set(kind="concentration")),
    "concentration_save_for_extended_spell": ("save_against", _set(kind="concentration", modified_by="extended_spell")),
    "forced_by_creature_type": ("save_against", _forced),
    # ability checks
    "check_uses_skill": ("check_uses", _set()),
    "check_uses_ability": ("check_uses", _set()),
    "check_uses_proficient_skill": ("check_uses", _set(proficient="skill")),
    "check_uses_proficient_tool": ("check_uses", _set(proficient="tool")),
    "check_uses_unproficient_skill": ("check_uses", _set(skill="any", proficient=False)),
    "check_uses_own_proficiency": ("check_uses", _set(proficient="any")),
    "check_adds_proficiency_bonus": ("check_uses", _set(adds_proficiency_bonus=True)),
    # creature type, tags and species
    "creature_type": ("creature_is", _creature_type),
    "creature_type_in": ("creature_is", _set()),
    "attacker_creature_type_in": ("creature_is", _set(who="attacker")),
    "source_creature_type_in": ("creature_is", _set(who="source")),
    "creature_type_chosen": ("creature_is", _chosen),
    "creature_has_tag": ("creature_is", _set()),
    "source_has_tag": ("creature_is", _set(who="source")),
    "is_species": ("creature_is", _set()),
    # spell level
    "spell_level_is": ("spell_level_in", _level_is),
    "spell_level_at_most": ("spell_level_in", _ren("level", "max")),
    "spell_slot_level_between": ("spell_level_in", _set()),
    # item state
    "wearing_item": ("item_state", _set(state="worn")),
    "wielding_item": ("item_state", _set(state="wielded")),
    "holds_item": ("item_state", _set(state="held")),
    "possesses_item": ("item_state", _set(state="possessed")),
    "attuned_to_item": ("item_state", _set(state="attuned")),
    "touching_item": ("item_state", _set(state="touching")),
    "gripping_item": ("item_state", _set(state="gripping")),
    "riding_item": ("item_state", _set(state="ridden")),
    "playing_item": ("item_state", _set(state="played")),
    "controls_item": ("item_state", _set(state="controlled")),
    "item_orbiting": ("item_state", _set(state="orbiting")),
    # distance
    "within_feet_of_item": ("within_feet", _set(of="item")),
    "within_feet_of_effect": ("within_feet", _set(of="effect")),
    "ally_within_feet_of_target": ("within_feet", _set(who="ally", of="target")),
    "enemy_within_feet_sees": ("within_feet", _set(who="enemy", sees=True, not_incapacitated=True)),
    "farther_than_feet_from_target": ("within_feet", _set(of="target", farther=True)),
    # levels
    "class_level_at_least": ("level_at_least", _set()),
    "character_level_at_least": ("level_at_least", _set()),
    "class_is": ("level_at_least", _class_is),
    # light and obscurement
    "in_dim_light": ("in_light", _set(level="dim")),
    "in_darkness": ("in_light", _set(level="darkness")),
    "in_sunlight": ("in_light", _set(level="sunlight")),
    "heavily_obscured": ("obscured", _set(degree="heavy")),
    "in_lightly_obscured_area": ("obscured", _set(degree="light")),
    # sight
    "can_be_seen_by": ("can_see", _set(target="self")),
    "attacker_can_see_target": ("can_see", _set(who="attacker", target="target")),
    "can_see_effect": ("can_see", _set(target="effect")),
    # conditions
    "has_condition_from": ("has_condition", _set()),
    # spells of a class
    "cantrip_of_class": ("spell_of_class", _set(cantrip=True)),
}

# argument names fixed inside predicates that keep their name
ARG_RENAMES = {
    "deals_damage_type": {"type": "damage_type"},
    "behind_cover": {"cover": "degree"},
    "has_speed": {"mode": "movement_mode"},
}

EVENT_ALIASES = {
    "damaged_by_creature_within": "damaged_by_creature_within_feet",
    "reduced_to_0_hp_not_killed": "drops_to_0_hp_not_killed",
}


# ---------------------------------------------------------------- normalization

def _norm_pred(d):
    name, args = d["pred"], dict(d.get("args") or {})
    if name == "roll_is" and "result" in args:          # "any Critical Hit against you"
        return {"pred": "is_critical_hit"}
    if name == "roll_succeeded" and "value" in args:     # {"value": false} = the D20 Test failed
        inner = {"pred": "roll_succeeded", "args": {"roll": "d20_test"}}
        return inner if args["value"] else {"not": inner}
    if name in ARG_RENAMES:
        args = {ARG_RENAMES[name].get(k, k): v for k, v in args.items()}
    if name in ALIASES:
        name, fn = ALIASES[name]
        args = fn(args)
    out = {"pred": name}
    if args:
        out["args"] = args
    return out


def normalize(obj):
    """Return a copy of an entry (or any JSON value) with canonical predicate and event names."""
    if isinstance(obj, list):
        return [normalize(x) for x in obj]
    if not isinstance(obj, dict):
        return obj
    if isinstance(obj.get("pred"), str):
        n = _norm_pred(obj)
        if "pred" in n:
            n = {**{k: v for k, v in obj.items() if k not in ("pred", "args")}, **n}
        return {k: normalize(v) for k, v in n.items()}
    out = {}
    for k, v in obj.items():
        if k == "event" and isinstance(v, str):
            base, dot, rest = v.partition(".")
            out[k] = EVENT_ALIASES.get(base, base) + dot + rest
        else:
            out[k] = normalize(v)
    return out


def link_formulas(system):
    """Registry names whose value a rule states as a formula carry it (D-005).

    The engine then has one lookup path: registries.<name>.formula. The rule in
    levels.rules stays the source (formula_source points to it).
    """
    for i, r in enumerate(system.get("levels", {}).get("rules", [])):
        f = (r.get("data") or {}).get("formula")
        if not f:
            continue
        for name in ("variables", "stats"):
            for v in system["registries"].get(name, []):
                if v["id"] == r["id"]:
                    v["formula"], v["formula_source"] = f, f"#/levels/rules/{i}"
    return system


def normalize_registries(registries):
    """Drop alias names from the registries and declare the canonical ones (pages merged)."""
    reg = copy.deepcopy(registries)
    preds = reg.get("predicates", [])
    pages = {}
    for p in preds:
        if p["id"] in ALIASES:
            pages.setdefault(ALIASES[p["id"]][0], set()).update(p.get("pages", []))
    keep = [p for p in preds if p["id"] not in ALIASES]
    ids = {p["id"] for p in keep}
    for p in keep:
        if p["id"] in ARG_RENAMES:
            p["params"] = [ARG_RENAMES[p["id"]].get(x, x) for x in p.get("params", [])]
    for name, (desc, params) in CANONICAL_PREDICATES.items():
        if name in ids:
            d = next(p for p in keep if p["id"] == name)
            d["description"], d["params"] = desc, params
            d["pages"] = sorted(set(d.get("pages", [])) | pages.get(name, set()))
        else:
            keep.append({"id": name, "description": desc, "params": params, "type": "predicate",
                         "pages": sorted(pages.get(name, set())) or [9]})
    reg["predicates"] = sorted(keep, key=lambda p: p["id"])
    if "events" in reg:
        reg["events"] = [e for e in reg["events"] if e["id"] not in EVENT_ALIASES]
    return reg
