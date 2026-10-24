#!/usr/bin/env python3
"""Stat block parser and creature entry builder for the bestiary lots (L33–L40).

parse(name, page) reads one stat block into structured data: size/type/alignment, AC and
Initiative, HP, Speed, ability scores and saves, the labelled lines (Skills, Resistances,
Vulnerabilities, Immunities, Senses, Languages, CR, Gear) and the ability sections (Traits,
Actions, Bonus Actions, Reactions, Legendary Actions).

Each ability is turned into effects where its wording follows the stat block templates:
  *Melee/Ranged Attack Roll:* +N, reach/range ... *Hit:* damage [and conditions]
  *<Ability> Saving Throw:* DC N, targets. *Failure:* ... *Success:* ...
  *Trigger:* ... *Response:* ... (reactions)
  Multiattack, Spellcasting (At Will / N/Day lists), and a library of recurring traits
  (Amphibious, Magic Resistance, Pack Tactics, ...). Qualifiers in the name (Recharge X–6,
  N/Day, Costs N Actions) become data and activation frequency.
Text the templates don't cover (riders after the damage, unique traits) is not guessed: it
becomes a master decision (reason not_automatable) quoting the source, and is counted in
the lot report.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import NODES, build, find, slugify  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ENTRIES = ROOT / "knowledge" / "dnd5e" / "entries"
INV = {e["name"]: e for e in json.loads((ROOT / "inventory/dnd5e/srd-5.2.1/entries.json").read_text(encoding="utf-8"))["entries"]
       if e["kind"] == "creature"}
OUTLINE = json.loads((ROOT / "inventory/dnd5e/srd-5.2.1/outline.json").read_text(encoding="utf-8"))["sections"]
SECTIONS = ("Traits", "Actions", "Bonus Actions", "Reactions", "Legendary Actions")
ABIL = {"Str": "str", "Dex": "dex", "Con": "con", "Int": "int", "Wis": "wis", "Cha": "cha"}
ABILITY_NAMES = {"Strength": "str", "Dexterity": "dex", "Constitution": "con", "Intelligence": "int", "Wisdom": "wis", "Charisma": "cha"}
DAMAGE = ["acid", "bludgeoning", "cold", "fire", "force", "lightning", "necrotic", "piercing", "poison", "psychic", "radiant",
          "slashing", "thunder"]
CONDITIONS = ["blinded", "charmed", "deafened", "exhaustion", "frightened", "grappled", "incapacitated", "invisible", "paralyzed",
              "petrified", "poisoned", "prone", "restrained", "stunned", "unconscious"]
NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
SHAPES = {"cone": "cone", "cube": "cube", "cylinder": "cylinder", "emanation": "emanation", "line": "line", "sphere": "sphere"}
STATS = Counter()     # per run: automated / partial / manual abilities
MANUAL = []           # (creature, section, ability) left to a master decision


def C(s):
    return f"dnd5e/condition/{s}"


def _plain(s):
    s = s.replace("\xa0", " ")
    s = re.sub(r"\*+\s+\*+", " ", s)          # "*Detect* *Magic*" -> "Detect Magic"
    return re.sub(r"\s+", " ", s.replace("*", "")).strip()


def _num(s):
    return int(s.replace("−", "-").replace("+", "").replace(",", ""))


def _dice(s):
    """'2d6 + 5' -> expression."""
    s = s.replace("−", "-").strip()
    m = re.fullmatch(r"(\d+d\d+)(?: ([+-]) (\d+))?", s)
    if not m:
        return None
    if not m.group(2):
        return m.group(1)
    return {"op": "add" if m.group(2) == "+" else "sub", "args": [m.group(1), int(m.group(3))]}


def path_of(heading_index):
    heads = [n for n in NODES if n.type == "h" and n.level <= 4 and not n.sidebar]
    k = next(i for i, n in enumerate(heads) if n.index == heading_index)
    return OUTLINE[k]["path"]


# ---------------------------------------------------------------- stat block nodes and header

def block_nodes(name, page, level=3):
    i = find(name, level, page)
    j = i + 1
    while j < len(NODES) and not (NODES[j].type == "h" and NODES[j].level <= 4 and not NODES[j].sidebar):
        j += 1
    return i, [n for n in NODES[i + 1:j] if not n.sidebar]


def _parse_list(s):
    return [x.strip() for x in re.split(r",\s*|\s+and\s+", s) if x.strip()]


def parse_header_line(label, value, data):
    v = _plain(value)
    key = slugify(label).replace("-", "_")
    if label == "HP":
        m = re.match(r"(\d+) \(([^)]+)\)", v)
        data["hp"] = {"average": int(m.group(1)), "formula": _dice(m.group(2)) or m.group(2), "text": v} if m else {"average": _num(v.split()[0]), "text": v}
    elif label == "Speed":
        sp = {"text": v}
        for part in v.split(","):
            part = part.strip()
            m = re.match(r"(?:(Burrow|Climb|Fly|Swim) )?(\d+) ft\.( \(hover\))?", part)
            if m:
                sp[(m.group(1) or "walk").lower()] = int(m.group(2))
                if m.group(3):
                    sp["hover"] = True
        data["speed"] = sp
    elif label == "Skills":
        data["skills"] = {slugify(n).replace("-", "_"): _num(b) for n, b in re.findall(r"([A-Z][A-Za-z ]+?) ([+−-]\d+)", v)}
        data["skills"]["text"] = v
    elif label in ("Resistances", "Vulnerabilities"):
        data[key] = {"damage_types": [t.lower() for t in _parse_list(v) if t.lower() in DAMAGE], "text": v}
    elif label == "Immunities":
        dmg_part, _, cond_part = v.partition(";")
        items = _parse_list(dmg_part) + _parse_list(cond_part)
        data["immunities"] = {"damage_types": [t.lower() for t in items if t.lower() in DAMAGE],
                              "conditions": [C(t.lower()) for t in items if t.lower() in CONDITIONS], "text": v}
    elif label == "Senses":
        se = {"text": v}
        for n, f in re.findall(r"(Blindsight|Darkvision|Tremorsense|Truesight) (\d+) ft\.", v):
            se[n.lower()] = int(f)
        m = re.search(r"Passive Perception (\d+)", v)
        if m:
            se["passive_perception"] = int(m.group(1))
        data["senses"] = se
    elif label == "Languages":
        la = {"text": v}
        m = re.search(r"telepathy (\d+) ft\.", v)
        if m:
            la["telepathy_feet"] = int(m.group(1))
        data["languages"] = la
    elif label == "CR":
        m = re.match(r"([\d/]+) \(XP ([\d,]+)(?:, or ([\d,]+) in lair)?; PB \+(\d+)\)", v)
        if m:
            data["cr"] = {"value": m.group(1), "xp": _num(m.group(2)), "proficiency_bonus": int(m.group(4)), "text": v}
            if m.group(3):
                data["cr"]["xp_in_lair"] = _num(m.group(3))
        else:
            data["cr"] = {"text": v}
    else:
        data[key] = {"text": v}


# ---------------------------------------------------------------- abilities

QUAL = [(r"^Recharge (\d)(?:–6)?$", lambda m, d: d.__setitem__("recharge", {"min": int(m.group(1)), "die": "1d6"})),
        (r"^Recharge after a (Short or Long|Long) Rest$", lambda m, d: d.__setitem__("recharge", {"rest": m.group(1).lower().replace(" or ", "_or_")})),
        (r"^(\d+)/Day(?: Each)?$", lambda m, d: d.__setitem__("per_day", int(m.group(1)))),
        (r"^(\d+)/Day(?: Each)?, or (\d+)/Day(?: Each)? in Lair$", lambda m, d: (d.__setitem__("per_day", int(m.group(1))), d.__setitem__("per_day_in_lair", int(m.group(2))))),
        (r"^Costs (\d+) Actions$", lambda m, d: d.__setitem__("legendary_cost", int(m.group(1))))]


def split_name(raw):
    """'Legendary Resistance (3/Day, or 4/Day in Lair)' -> name, data."""
    d = {}
    m = re.match(r"^(.+?) \((.+)\)$", raw)
    if not m:
        return raw, d
    quals = []
    for q in [x.strip() for x in re.split(r";", m.group(2))]:
        hit = False
        for rx, fn in QUAL:
            mm = re.match(rx, q)
            if mm:
                fn(mm, d)
                hit = True
                break
        if not hit:
            quals.append(q)
    if quals:
        d["qualifiers"] = quals
    return m.group(1), d


def damage_terms(s):
    out = []
    # a damage term followed by a condition ("... damage if the attack roll had Advantage", "or ... while
    # Bloodied") is not unconditional: it is left to the rider decision
    for avg, dice, dtype in re.findall(r"(\d+) \((\d+d\d+(?: [+−] \d+)?)\) (\w+) damage(?![^.,]*?\b(?:if|while|when|instead)\b)(?!,? or )", s):
        if dtype.lower() in DAMAGE:
            out.append({"op": "damage", "amount": _dice(dice), "damage_type": dtype.lower(), "average": int(avg)})
    if not out:
        m = re.match(r"^(\d+) (\w+) damage", s)
        if m and m.group(2).lower() in DAMAGE:
            out.append({"op": "damage", "amount": int(m.group(1)), "damage_type": m.group(2).lower()})
    return out


SIZES = ["Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"]
COND_RX = re.compile(r"(?:(?:If|if) the target is an? (Tiny|Small|Medium|Large|Huge|Gargantuan) or smaller creature, )?"
                     r"(?:the target |it |and (?:the target )?)?has the (\w+) condition"
                     r"(?: \(escape DC (\d+)\))?(?: from [^.,]+)?"
                     r"(?: (until the end of its next turn|until the (?:start|end) of the [\w’' -]+?’s next turn|until the grapple ends|for (\d+) (minute|hour)s?))?")
PUSH_RX = re.compile(r"(?:(?:If|if) the target is an? (Tiny|Small|Medium|Large|Huge|Gargantuan) or smaller creature, )?"
                     r"(?:the target |it )?is pushed up to (\d+) feet (?:straight )?away from [\w’' -]+")
REPEAT_RX = re.compile(r"(?:The target |The \w+ target |It )?repeats the save at the end of each of its turns, ending the effect on itself on a success")


def _dur(m_until, amount, unit):
    if amount:
        return {"kind": f"{unit}s", "amount": int(amount)}
    if not m_until:
        return None
    if m_until == "until the end of its next turn":
        return {"kind": "until_event", "until": {"event": "turn_end", "whose": "target", "which": "next"}}
    if m_until == "until the grapple ends":
        return {"kind": "while", "while": {"pred": "has_condition", "args": {"condition": "grappled"}}}
    return {"kind": "until_event", "until": {"event": "turn_start" if "start" in m_until else "turn_end", "whose": "source", "which": "next"}}


def condition_terms(s):
    out = []
    for size, cname, esc, until, amount, unit in COND_RX.findall(s):
        if cname.lower() in CONDITIONS:
            d = {"op": "apply_condition", "condition": C(cname.lower())}
            if esc:
                d["params"] = {"escape_dc": int(esc)}
            du = _dur(until, amount, unit)
            if du:
                d["duration"] = du
            if size:
                d["when"] = {"pred": "target_size_at_most", "args": {"size": size.lower()}}
            out.append(d)
    for size, feet in PUSH_RX.findall(s):
        d = {"op": "move", "mode": "push", "distance_feet": int(feet)}
        if size:
            d["when"] = {"pred": "target_size_at_most", "args": {"size": size.lower()}}
        out.append(d)
    return out


def residual(hit):
    """Text of a Hit/Failure clause left after its damage terms and the rider clauses handled above."""
    s = re.sub(r"\d+ \(\d+d\d+(?: [+−] \d+)?\) \w+ damage(?![^.,]*?\b(?:if|while|when|instead)\b)(?!,? or )", "", hit)
    s = re.sub(r"^\d+ \w+ damage", "", s)
    s = COND_RX.sub("", s)
    s = PUSH_RX.sub("", s)
    s = REPEAT_RX.sub("", s)
    s = re.sub(r"\bplus\b|\band\b|[.,;]", " ", s)
    return s.strip()


def attack_fx(text):
    m = re.search(r"\*(Melee|Ranged|Melee or Ranged) Attack Roll:\* \+(\d+)(?: \(([^)]*)\))?, (.+?)\. \*Hit:\* (.+?)(?:\n\n|$)", text, re.S)
    if not m:
        return None, None
    kind, bonus, cond_bonus, reach, hit = m.groups()
    fx = {"op": "attack", "attack_type": {"Melee": "melee", "Ranged": "ranged", "Melee or Ranged": "melee"}[kind], "bonus": int(bonus)}
    rng = {}
    r = re.search(r"reach (\d+) ft\.", reach)
    if r:
        rng = {"kind": "distance", "feet": int(r.group(1))}
    r2 = re.search(r"range (\d+)(?:/(\d+))? ft\.", reach)
    if r2 and not r:
        rng = {"kind": "distance", "feet": int(r2.group(1))}
        if r2.group(2):
            rng["long_feet"] = int(r2.group(2))
    if rng:
        fx["target"] = {"kind": "creature", "range": rng}
    nested = None
    k = hit.find("Saving Throw:*")
    if k >= 0:
        start = hit.rfind("*", 0, k - 1)
        sv, sv_left = save_fx(hit[start:])
        if sv:
            nested = sv
            pre = hit[:start]
            cond_txt = re.search(r"(?:If|if) the target is (an? [^,]+), (?:it|the target) is subjected to the following effect", pre)
            if cond_txt:
                sv["note"] = f"If the target is {cond_txt.group(1)}."
            pre = re.sub(r"(?:(?:If|if) the target is [^,]+, )?(?:it|the target) is subjected to the following effect\.?", "", pre)
            hit = pre + (f" {sv_left}" if sv_left else "")
    on_hit = [{k: v for k, v in d.items() if k != "average"} for d in damage_terms(hit)] + condition_terms(hit)
    if nested:
        on_hit.append(nested)
    if on_hit:
        fx["on_hit"] = on_hit
    notes = []
    if kind == "Melee or Ranged" and r2:
        notes.append(f"Or ranged: {r2.group(0)}.")
    if cond_bonus:
        notes.append(f"Attack: {cond_bonus}.")
    rest = residual(hit)
    if notes:
        fx["note"] = " ".join(notes)
    return fx, (hit if rest and len(rest.split()) > 2 else None)


def save_fx(text):
    t = re.sub(r"\n\n", " ", text)
    m = re.search(r"\*(?:Response—)?(\w+) Saving Throw:\* DC (\d+), (.+?)\. \*Failure:\* (.+?)(?= \*Success:\*| \*Failure or Success:\*|$)"
                  r"(?: \*Success:\* (.+?)(?= \*Failure or Success:\*|$))?(?: \*Failure or Success:\* (.+))?$", t)
    if not m:
        return None, None
    ab, dc, tgt, fail, succ, both = m.groups()
    fx = {"op": "save", "ability": ABILITY_NAMES[ab], "dc": int(dc)}
    target = {"kind": "creature"}
    a = re.search(r"(\d+)-foot(?:-long)?(?:,? (\d+)-foot-wide)? (Cone|Cube|Emanation|Line|Sphere|Cylinder)", tgt)
    if a:
        target = {"kind": "area", "area": {"shape": SHAPES[a.group(3).lower()], "size_feet": int(a.group(1))}}
        if a.group(2):
            target["area"]["width_feet"] = int(a.group(2))
        target["area"]["origin"] = "self" if "originating from" in tgt or a.group(3) in ("Cone", "Line", "Emanation") else "point"
    else:
        r = re.search(r"within (\d+) feet", tgt)
        if r:
            target["range"] = {"kind": "distance", "feet": int(r.group(1))}
        cnt = re.match(r"^(one|two|three|four|five|six) ", tgt)
        if cnt and NUM[cnt.group(1)] > 1:
            target["count"] = NUM[cnt.group(1)]
    target["text"] = tgt
    fx["target"] = target
    on_fail = [{k: v for k, v in d.items() if k != "average"} for d in damage_terms(fail)] + condition_terms(fail)
    if on_fail:
        fx["on_fail"] = on_fail
    if REPEAT_RX.search(fail) or (both and REPEAT_RX.search(both)):
        fx["repeat"] = {"on": {"event": "turn_end", "whose": "target", "which": "each"}, "ends": "effect_on_self"}
    leftover = []
    rest = residual(fail)
    if rest and len(rest.split()) > 2:
        leftover.append(fail)
    if succ:
        if re.match(r"^Half damage(?: only)?\.?$", succ.strip()):
            fx["half_on_success"] = True
        elif succ.strip() not in ("",):
            leftover.append(f"Success: {succ}")
    if both and residual(both) and len(residual(both).split()) > 2:
        leftover.append(f"Failure or Success: {both}")
    return fx, (" ".join(leftover) if leftover else None)


def reaction_fx(text):
    m = re.search(r"\*Trigger:\* (.+?) \*Response(?:—\w+ Saving Throw)?:\*", re.sub(r"\n\n", " ", text))
    if not m:
        return None, None
    trig = m.group(1)
    sv, left = save_fx(text)
    if sv:
        return {"op": "trigger", "event": {"event": "reaction_trigger"}, "cost": "reaction", "optional": True, "then": [sv],
                "note": f"Trigger: {trig}"}, left
    r = re.search(r"\*Response:\* .+? adds (\d+) to its AC against that attack", text)
    if r:
        return {"op": "trigger", "event": {"event": "reaction_trigger"}, "cost": "reaction", "optional": True,
                "then": [{"op": "modifier", "stat": "ac", "mode": "add", "value": int(r.group(1)), "note": "Against the triggering attack."}],
                "note": f"Trigger: {trig}"}, None
    return {"op": "trigger", "event": {"event": "reaction_trigger"}, "cost": "reaction", "optional": True,
            "then": [{"op": "reference", "rule": "dnd5e/rule/reaction", "note": "Response in the text."}], "note": f"Trigger: {trig}"}, \
        _plain(text.split("*Response")[1]) if "*Response" in text else text


def multiattack(text, names):
    t = _plain(text)
    attacks = []
    for cnt, nm in re.findall(r"\b(one|two|three|four|five|six)(?: times)? (?:with )?(?:its |their )?([A-Z][\w’' -]+?)(?: attacks?\b| \(| or |, |\.| and )", t):
        nm = nm.strip()
        if nm in names:
            attacks.append({"name": nm, "count": NUM[cnt]})
    return {"id": "multiattack", "attacks": attacks, "text": t}


def spellcasting(text, creature):
    t = _plain(text)
    m = re.search(r"using (\w+) as the spellcasting ability \((?:spell save DC (\d+))?(?:, )?(?:\+(\d+) to hit with spell attacks)?\)", t)
    rule = {"id": "spellcasting", "text": t}
    if m:
        rule["ability"] = ABILITY_NAMES[m.group(1)]
        if m.group(2):
            rule["save_dc"] = int(m.group(2))
        if m.group(3):
            rule["attack_bonus"] = int(m.group(3))
    rule["no_material_components"] = "requiring no Material components" in t
    fx, lists = [], []
    for freq, spells in re.findall(r"(At Will|\d+/Day(?: Each)?):\s*(.+?)(?=(?:At Will|\d+/Day(?: Each)?):|$)", t):
        names = [s.strip() for s in re.split(r",(?![^()]*\))", spells) if s.strip()]
        for s in names:
            base = re.sub(r" \(.*\)$", "", s).strip(" .")
            lvl = re.search(r"level (\d) version", s)
            ref = f"dnd5e/spell/{slugify(base)}"
            d = {"op": "cast_spell", "spell": ref, "slot": "none"}
            if rule.get("no_material_components"):
                d["components"] = ["V", "S"]
            if lvl:
                d["level"] = int(lvl.group(1))
            if m and m.group(2):
                d["save_dc"] = int(m.group(2))
            if m and m.group(3):
                d["attack_bonus"] = int(m.group(3))
            if "(" in s and not lvl:
                d["note"] = s[s.index("("):]
            act = {"op": "activation", "cost": "action", "action": "dnd5e/action/magic", "then": [d], "name": base}
            if freq != "At Will":
                act["frequency"] = {"count": int(freq.split("/")[0]), "per": "day"}
            fx.append(act)
            lists.append({"spell": ref, "frequency": freq})
    rule["spells"] = lists
    return rule, fx


# recurring traits: name -> fn(text, creature) -> (effects, rules)
def _speed_mode(mode, val):
    return {"op": "speed", "movement": mode, "mode": "set", "value": val}


def _fixed(fx=None, rule=None):
    return lambda text, cr: ([] if fx is None else (fx if isinstance(fx, list) else [fx]), [] if rule is None else [rule])


def one_of_actions(*actions, name=None, note=None):
    """A Bonus Action that takes one of several actions: a choice, not a sequence (D-005)."""
    fx = {"op": "activation", "name": name, "cost": "bonus_action", "then": [{"op": "choice", "id": "action", "choose": 1, "options": [
        {"id": a, "label": a.title(), "effects": [{"op": "reference", "rule": f"dnd5e/action/{a}"}]} for a in actions]}]}
    if note:
        fx["note"] = note
    return fx


TRAITS = {
    "Amphibious": _fixed({"op": "modifier", "stat": "breathe_underwater", "mode": "set", "value": 1, "note": "Breathes air and water."}),
    "Water Breathing": _fixed({"op": "modifier", "stat": "breathe_underwater", "mode": "set", "value": 1}),
    "Magic Resistance": _fixed({"op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw"], "when": {"pred": "save_against_spell_or_magic"}}),
    "Pack Tactics": _fixed({"op": "roll_mode", "mode": "advantage", "rolls": ["attack_roll"],
                            "when": {"pred": "ally_within_feet_of_target", "args": {"feet": 5, "not_incapacitated": True}}}),
    "Spider Climb": _fixed({"op": "modifier", "stat": "spider_climb", "mode": "set", "value": 1, "note": "Climbs difficult surfaces, including ceilings, without an ability check."}),
    "Sunlight Sensitivity": _fixed({"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll", "ability_check"],
                                    "when": {"all": [{"pred": "in_sunlight"}, {"any": [{"pred": "roll_is", "args": {"roll": "attack_roll"}},
                                                                                         {"pred": "check_uses_skill", "args": {"skill": "perception"}}]}]},
                                    "note": "Attack rolls and Wisdom (Perception) checks while in sunlight."}),
    "Legendary Resistance": _fixed({"op": "trigger", "event": {"event": "fails_saving_throw"}, "optional": True,
                                    "then": [{"op": "auto_result", "rolls": ["saving_throw"], "result": "success"}]}),
    "Flyby": _fixed({"op": "restrict", "restrictions": ["provoke_opportunity_attack_when_flying_out_of_reach"], "target": {"kind": "self"},
                     "note": "Doesn't provoke Opportunity Attacks when it flies out of an enemy's reach."}),
    "Nimble Escape": _fixed(one_of_actions("disengage", "hide", name="Nimble Escape", note="Takes the Disengage or Hide action.")),
    "Cunning Action": _fixed(one_of_actions("dash", "disengage", "hide", name="Cunning Action", note="Takes the Dash, Disengage, or Hide action.")),
    "Immutable Form": _fixed({"op": "restrict", "restrictions": ["shape_changed"], "note": "Can't shape-shift."}),
    "Siege Monster": _fixed({"op": "modifier", "stat": "damage_roll", "mode": "multiply", "value": 2, "when": {"pred": "target_is_object"},
                             "note": "Double damage to objects and structures."}),
    "Web Walker": _fixed({"op": "restrict", "restrictions": ["web_movement_restrictions"],
                          "note": "Ignores movement restrictions caused by webs and knows the location of any creature in contact with the same web."}),
    "Amorphous": _fixed(rule={"id": "amorphous", "squeeze_inch": 1, "no_extra_movement": True}),
    "Incorporeal Movement": _fixed(rule={"id": "incorporeal_movement", "through_creatures_and_objects": True, "difficult_terrain": True,
                                         "ends_turn_inside": {"damage": "1d10", "damage_type": "force"}}),
    "Swarm": _fixed(rule={"id": "swarm", "occupies_others_space": True, "squeezes_tiny_openings": True, "no_hp_regain": True,
                          "no_temp_hp": True}),
    "Hold Breath": lambda text, cr: ([], [{"id": "hold_breath", "text": _plain(text),
                                           **({"minutes": int(m.group(1))} if (m := re.search(r"(\d+) (?:minutes|minute|hours?)", text)) else {})}]),
}


def _spells_in(text):
    out = []
    for nm in re.findall(r"\*([A-Z][^*]+?)\*", text):
        nm = _plain(nm)
        if (ENTRIES / "spell" / f"{slugify(nm)}.json").exists():
            out.append(nm)
    return out


def _generic(name, text, creature):
    """Recurring wordings outside the attack/save templates."""
    t = _plain(text)
    fx, rules = [], []
    sp = _spells_in(text)
    if sp and re.search(r"\bcasts?\b|to cast\b", t):
        lvl = re.search(r"level (\d) version", t)
        casts = []
        for nm in sp:
            d = {"op": "cast_spell", "spell": f"dnd5e/spell/{slugify(nm)}", "slot": "none"}
            if lvl and len(sp) == 1:
                d["level"] = int(lvl.group(1))
            if "requiring no spell components" in t:
                d["components"] = []
            casts.append(d)
        if len(casts) == 1:
            fx.append(casts[0])
        else:
            fx.append({"op": "choice", "id": slugify(name).replace("-", "_"), "choose": 1,
                       "options": [{"id": slugify(c["spell"].split("/")[-1]).replace("-", "_"), "label": c["spell"].split("/")[-1],
                                    "effects": [c]} for c in casts]})
        if "can’t take this action again until the start of its next turn" in t:
            rules.append({"id": "once_per_round", "until": "start of its next turn"})
        return fx, rules
    m = re.search(r"If the [\w’' -]+ dies outside (?:the )?(.+?), .*?reviving with all its Hit Points somewhere in (?:the )?(.+?)\.", t)
    if m:
        return [], [{"id": "restoration", "dies_outside": m.group(1), "revives_in": m.group(2), "hit_points": "all"}]
    m = re.search(r"regains (\d+) Hit Points at the start of each of its turns(?: if it has at least 1 Hit Point)?", t)
    if m:
        fx.append({"op": "trigger", "event": {"event": "turn_start", "whose": "self", "which": "each"},
                   "condition": {"not": {"pred": "at_zero_hp"}}, "then": [{"op": "heal", "amount": int(m.group(1))}]})
        m2 = re.search(r"If the [\w’' -]+ takes ([\w ,]+?) damage, this trait doesn’t function", t)
        if m2:
            rules.append({"id": "regeneration_suppressed_by", "damage_types": [x.lower() for x in _parse_list(m2.group(1).replace(" or ", ", "))
                                                                               if x.lower() in DAMAGE]})
        return fx, rules
    m = re.search(r"sheds Bright Light in an? (\d+)-foot radius and Dim Light for an additional (\d+) feet", t)
    if m and len(t) < 160:
        return [], [{"id": "light", "bright_feet": int(m.group(1)), "dim_feet": int(m.group(2)),
                     "rules": ["dnd5e/rule/bright-light", "dnd5e/rule/dim-light"]}]
    m = re.search(r"jumps up to (\d+) feet by spending (\d+) feet of movement", t)
    if m:
        return [{"op": "move", "mode": "jump", "distance_feet": int(m.group(1)), "note": f"Spends {m.group(2)} feet of movement."}], []
    m = re.search(r"Long Jump is up to (\d+) feet and its High Jump is up to (\d+) feet", t)
    if m:
        return [], [{"id": "standing_leap", "long_jump_feet": int(m.group(1)), "high_jump_feet": int(m.group(2)), "running_start": False}]
    m = re.search(r"teleports (.+?) up to (\d+) feet to an unoccupied space", t)
    if m:
        return [{"op": "move", "mode": "teleport", "distance_feet": int(m.group(2)), "note": f"Teleports {m.group(1)}."}], []
    m = re.search(r"^At the end of each of the [\w’' -]+’s turns, each creature (?:of the [\w’' -]+’s choice )?in an? (\d+)-foot Emanation originating from the [\w’' -]+ takes (\d+) \((\d+d\d+(?: [+−] \d+)?)\) (\w+) damage", t)
    if m and m.group(4).lower() in DAMAGE:
        return [{"op": "trigger", "event": {"event": "turn_end", "whose": "self", "which": "each"},
                 "then": [{"op": "damage", "amount": _dice(m.group(3)), "damage_type": m.group(4).lower(),
                           "target": {"kind": "area", "area": {"shape": "emanation", "size_feet": int(m.group(1)), "origin": "self"}}}],
                 "note": t[m.end():].strip() or None}], []
    m = re.match(r"^The [\w’' -]+ (?:moves up to (half )?its Speed, and it )?makes (one|two) ([A-Z][\w’' -]+?) attacks?\.?(?: The [\w’' -]+ can’t take this action again until the start of its next turn\.)?$", t)
    if m:
        r = {"id": "attack", "attacks": [{"name": m.group(3), "count": NUM[m.group(2)]}]}
        if m.group(1) is not None or "moves up to" in t:
            r["move"] = "half_speed" if m.group(1) else "speed"
        return [], [r]
    return None


def trait_from_library(name, text, creature):
    fn = TRAITS.get(name)
    if fn:
        return fn(text, creature)
    g = _generic(name, text, creature)
    if g:
        g = ([f for f in g[0] if f], g[1])
        for f in g[0]:
            if f.get("note") is None:
                f.pop("note", None)
        return g if (g[0] or g[1]) else None
    return None


# ---------------------------------------------------------------- parse a block

def parse(name, page, level=3, nodes=None):
    hi, nodes = (None, nodes) if nodes is not None else block_nodes(name, page, level)
    data = {}
    sec = None
    abilities = {}
    items = []          # coverage plan
    merged = []         # (node-like kind, text)
    for n in nodes:
        t = n.text
        if n.type == "h" and n.level == 5 and t in SECTIONS:
            merged.append(("h", t))
            continue
        if merged and n.type == "p" and merged[-1][0] == "p" and sec is None and not t.startswith(("***", "**", "*")) \
                and merged[-1][1].startswith("**") and not merged[-1][1].startswith("***"):
            merged[-1] = ("p", merged[-1][1] + " " + t)  # wrapped labelled line
            continue
        merged.append(("t" if n.type == "t" else "p", t))
    first = merged[0][1].strip("* ")
    m = re.match(r"^(.+?) (Aberration|Beast|Celestial|Construct|Dragon|Elemental|Fey|Fiend|Giant|Humanoid|Monstrosity|Ooze|Plant|Undead|"
                 r"Swarm of Tiny \w+)(?: \(([^)]+)\))?, (.+)$", _plain(first))
    if m:
        data["size"], data["type"], data["alignment"] = m.group(1), m.group(2), m.group(4)
        if m.group(3):
            data["tags"] = [x.strip() for x in m.group(3).split(",")]
    else:
        data["size"], data["type"], data["alignment"] = None, None, _plain(first)
    data["type_line"] = _plain(first)
    for kind, t in merged[1:]:
        if kind == "h":
            sec = slugify(t).replace("-", "_")
            data.setdefault(sec, [])
            continue
        if sec is None:
            if kind == "t" and "**AC**" in t:
                for label, val in re.findall(r"\*\*(AC|Initiative)\*\* ([^|]+)", t):
                    v = _plain(val)
                    if label == "AC":
                        mm = re.match(r"(\d+)(?: \((.+)\))?", v)
                        data["ac"] = {"value": int(mm.group(1)), "text": v}
                    else:
                        mm = re.match(r"([+−-]\d+) \((\d+)\)", v)
                        data["initiative"] = {"modifier": _num(mm.group(1)), "score": int(mm.group(2)), "text": v} if mm else {"text": v}
                continue
            if kind == "t":
                for a, score, md_, sv in re.findall(r"\*\*(Str|Dex|Con|Int|Wis|Cha)\*\*\s*\|?\s*(\d+)\s*\|\s*([+−-]\d+)\s*\|\s*([+−-]\d+)", t):
                    data.setdefault("abilities", {})[ABIL[a]] = {"score": int(score), "mod": _num(md_), "save": _num(sv)}
                continue
            mm = re.match(r"^\*\*([^*]+?)\*\*\s*(.*)$", t)
            if mm:
                parse_header_line(mm.group(1), mm.group(2), data)
            continue
        t = t.replace("\xa0", " ")
        mm = re.match(r"^\*\*\*(.+?)\.\*\*\*\s*(.*)$", t, re.S)
        if mm:
            nm, qd = split_name(_plain(mm.group(1)))
            data[sec].append({"name": nm, **qd, "text": mm.group(2)})
        elif data[sec]:
            data[sec][-1]["text"] += "\n\n" + t
        else:  # section intro (Legendary Action Uses ...)
            data[f"{sec}_intro"] = {"text": _plain(t)}
            mu = re.search(r"Legendary Action Uses: (\d+)(?: \((\d+) in Lair\))?", t)
            if mu:
                data[f"{sec}_intro"]["uses"] = int(mu.group(1))
                if mu.group(2):
                    data[f"{sec}_intro"]["uses_in_lair"] = int(mu.group(2))
    return hi, nodes, data


COST = {"actions": "action", "bonus_actions": "bonus_action", "reactions": "reaction", "legendary_actions": "legendary_action", "traits": None}


def wrap(fx, sec, ab):
    """Activation wrapper by section and qualifiers."""
    cost = COST[sec]
    if cost is None or fx.get("op") in ("trigger", "activation"):
        return fx
    d = {"op": "activation", "cost": cost, "name": ab["name"], "then": [fx]}
    if cost == "action" and fx.get("op") == "attack":
        d["action"] = "dnd5e/action/attack"
    if "per_day" in ab:
        d["frequency"] = {"count": ab["per_day"], "per": "day"}
    if "recharge" in ab:
        d["note"] = f"Recharge {ab['recharge'].get('min', '')}–6." if "min" in ab["recharge"] else "Recharges after a rest."
    if "legendary_cost" in ab:
        d["uses"] = {"resource": "legendary_actions", "amount": ab["legendary_cost"]}
    elif cost == "legendary_action":
        d["uses"] = {"resource": "legendary_actions", "amount": 1}
    return d


def creature(name, lot, page=None, overrides=None, extra_fx=None, nodes=None, slug=None, level=3, path=None):
    """Catalog entry for a stat block. `overrides`: {ability name: [(tag, payload), ...]} replacing the
    automatic analysis of that ability; `extra_fx`: {ability name: [(tag, payload)]} added to it."""
    inv = INV.get(name)
    page = page or inv["page"]
    hi, nodes, data = parse(name, page, level, nodes)
    path = path or (path_of(NODES[hi].index) if hi is not None else name)
    items = [(None, "sys", ["/data/type_line"] + [p for p in ("/data/size", "/data/type", "/data/alignment") if data.get(p.split("/")[-1])]
              + (["/data/tags"] if "tags" in data else []))]
    labels = {"ac": "| **AC**", "hp": "**HP**", "speed": "**Speed**"}
    for k, a in labels.items():
        if k in data:
            items.append((a, "sys", [f"/data/{k}"] + (["/data/initiative"] if k == "ac" and "initiative" in data else [])))
    if "abilities" in data:
        items.append(("| MOD SAVE", "sys", ["/data/abilities"]))
    for n in nodes:
        mm = re.match(r"^\*\*([^*]+?)\*\*", n.text)
        if mm and mm.group(1) not in ("AC", "HP", "Speed") and not n.text.startswith("***") and n.type == "p":
            key = slugify(mm.group(1)).replace("-", "_")
            if key in data and isinstance(data[key], dict) and items[-1][0] != n.text[:len(mm.group(0))]:
                items.append((n.text[:len(mm.group(0))], "sys", [f"/data/{key}"]))
    overrides = overrides or {}
    extra_fx = extra_fx or {}
    mds = []
    for sec_title in SECTIONS:
        sec = slugify(sec_title).replace("-", "_")
        if sec not in data:
            continue
        items.append((f"##### {sec_title}", "sys", [f"/data/{sec}"] + ([f"/data/{sec}_intro"] if f"{sec}_intro" in data else [])))
        names = {a["name"] for s in SECTIONS for a in data.get(slugify(s).replace("-", "_"), [])}
        for i, ab in enumerate(data[sec]):
            anchor = "***" + _anchor_name(ab, nodes)
            items.append((anchor, "sys", [f"/data/{sec}/{i}"]))
            if ab["name"] in overrides:
                for tag, payload in overrides[ab["name"]]:
                    items.append((anchor, tag, payload))
                STATS["override"] += 1
                continue
            auto = analyze(name, sec, ab, names)
            for tag, payload in auto + extra_fx.get(ab["name"], []):
                items.append((anchor, tag, payload))
    facets = {"group": inv["facets"].get("group") if inv else "embedded", "size": data.get("size"), "type": data.get("type"),
              "alignment": data.get("alignment")}
    if "cr" in data and "value" in data["cr"]:
        facets["cr"] = data["cr"]["value"]
    facets = {k: v for k, v in facets.items() if v is not None}
    return build("creature", slug or (inv["ref"].split("/")[-1] if inv else slugify(name)), name, nodes, lot, path, items,
                 facets=facets, data=data)


def _anchor_name(ab, nodes):
    for n in nodes:
        m = re.match(r"^\*\*\*(.+?)\.\*\*\*", n.text)
        if m and (_plain(m.group(1)) == ab["name"] or _plain(m.group(1)).startswith(ab["name"] + " (")):
            return m.group(1)[: len(m.group(1))].split("(")[0].rstrip() if "(" in m.group(1) else m.group(1)
    return ab["name"]


def analyze(creature_name, sec, ab, names):
    """Automatic effects for one ability: list of (tag, payload)."""
    out = []
    text = ab["text"]
    nm = ab["name"]
    left = None
    if nm == "Multiattack":
        STATS["auto"] += 1
        return [("rule", multiattack(text, names))]
    if nm == "Spellcasting":
        rule, fx = spellcasting(text, creature_name)
        STATS["auto"] += 1
        return [("rule", rule)] + [("fx", f) for f in fx]
    if "*Trigger:*" in text:
        fx, left = reaction_fx(text)
        if fx:
            out.append(("fx", fx))
    elif "Attack Roll:*" in text:
        fx, left = attack_fx(text)
        if fx:
            out.append(("fx", wrap(fx, sec, ab)))
    elif "Saving Throw:*" in text:
        fx, left = save_fx(text)
        if fx:
            out.append(("fx", wrap(fx, sec, ab)))
    else:
        lib = trait_from_library(nm, text, creature_name)
        if lib:
            fxs, rules = lib
            fxs = [wrap(f, sec, ab) for f in fxs]
            if "per_day" in ab:
                for f in fxs:
                    if f.get("op") in ("trigger", "activation") and "frequency" not in f:
                        f["frequency"] = {"count": ab["per_day"], "per": "day"}
            out += [("fx", f) for f in fxs] + [("rule", r) for r in rules]
    if not out:
        STATS["manual"] += 1
        MANUAL.append((creature_name, sec, nm))
        out.append(("md", {"id": slugify(f"{sec}-{nm}").replace("-", "_"), "reason": "not_automatable",
                           "prompt": f"Adjudicate {nm} as written.", "source_text": _plain(text)[:400]}))
    elif left:
        STATS["partial"] += 1
        MANUAL.append((creature_name, sec, nm + " (rider)"))
        out.append(("md", {"id": slugify(f"{sec}-{nm}-rider").replace("-", "_"), "reason": "not_automatable",
                           "prompt": f"Apply the rest of {nm} as written.", "source_text": _plain(left)[:400]}))
    else:
        STATS["auto"] += 1
    return out


# ---------------------------------------------------------------- lots

REGISTRY = {
    "events": [
        {"id": "reaction_trigger", "description": "The trigger stated in a stat block Reaction (its text is in the effect's note).", "type": "event", "pages": [257]},
    ],
    "predicates": [
        {"id": "target_size_at_most", "description": "The target is of this size or smaller (param: size).", "params": ["size"], "type": "predicate", "pages": [254]},
        {"id": "in_sunlight", "description": "The creature is in sunlight.", "type": "predicate", "pages": [256]},
    ],
    "restrictions": [
        {"id": "provoke_opportunity_attack_when_flying_out_of_reach", "description": "Provoke Opportunity Attacks when flying out of an enemy's reach.", "pages": [256]},
        {"id": "shape_changed", "description": "Have its shape changed (shape-shifting effects).", "pages": [256]},
        {"id": "web_movement_restrictions", "description": "Be subject to movement restrictions caused by webs.", "pages": [256]},
    ],
}


def build_lot(lot, overrides=None, extra_fx=None):
    """Entries for every stat block the inventory assigns to `lot`."""
    out = []
    for name, e in INV.items():
        if e["lot"] == lot:
            out.append(creature(name, lot, overrides=(overrides or {}).get(name), extra_fx=(extra_fx or {}).get(name)))
    return out


def report(lot):
    mine = [m for m in MANUAL]
    return {"automated": STATS["auto"], "partial": STATS["partial"], "manual": STATS["manual"], "items": mine}


def add_legendary_action_economy(lot):
    """Legendary Actions are a part of the action economy of monsters (stat block rules, p. 257)."""
    from entrylib import KNOWLEDGE, quote
    path = KNOWLEDGE / "dnd5e" / "system.json"
    system = json.loads(path.read_text(encoding="utf-8"))
    if not any(a["id"] == "legendary_action" for a in system["action_economy"]):
        system["action_economy"].append({
            "id": "legendary_action", "name": "Legendary Action", "per": "round", "refreshes_on": "turn_start",
            "rules": [quote("A Legendary Action is an action that a monster can take immediately after another creature’s turn.", "legendary_action.timing"),
                      quote("The monster expends one use whenever it takes a Legendary Action, and it regains all expended uses at the start of each of its turns.",
                            "legendary_action.uses")],
            "pages": [257]})
        path.write_text(json.dumps(system, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_lot(lot, entries):
    from entrylib import extend_registries, write_entry
    extend_registries(REGISTRY, lot)
    add_legendary_action_economy(lot)
    for e in entries:
        write_entry(e)
    rep = ROOT / "inventory" / "dnd5e" / "srd-5.2.1" / "reports"
    rep.mkdir(exist_ok=True)
    (rep / f"{lot}_master_decisions.json").write_text(json.dumps(
        {"lot": lot, "automated": STATS["auto"], "partial_riders": STATS["partial"], "not_automated": STATS["manual"],
         "abilities": [{"creature": c, "section": s, "ability": a} for c, s, a in MANUAL]}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {len(entries)} entries; abilities automated {STATS['auto']}, with rider decision {STATS['partial']}, "
          f"master decision {STATS['manual']}")
