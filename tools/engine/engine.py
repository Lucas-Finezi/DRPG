"""DRPG rules-engine prototype.

Executes catalog effects (the closed op vocabulary) for creatures in an encounter. It is not
the production engine: it exists to prove that the catalog carries every call a real engine
needs. Each call is logged with an outcome (see calllog.py). When the catalog lacks something
the engine falls back to an explicit FALLBACK and logs DATA_GAP, so gaps are never silent.

Space is one-dimensional (a position in feet along a line): distances, reach, areas and
movement are computed on it. Lighting and obscurement are a scene assumption (bright, open).
"""
import copy
import json
import re

from .calllog import CallLog
from .catalog import Catalog
from .expr import DICE, Evaluator, parse_cell

# Effects that shape a creature while they are present (as opposed to effects run once).
PASSIVE = {"modifier", "roll_mode", "defense", "restrict", "auto_result", "speed", "sense", "trigger",
           "proficiency", "resource"}
# Rules that apply to every creature.
GLOBAL_RULES = ["dnd5e/rule/concentration", "dnd5e/rule/dropping-to-0-hit-points", "dnd5e/rule/ranged-attacks"]
# Events whose subject acts on someone else: 'inherit' targets keep pointing at that creature.
OUTWARD_EVENTS = {"hits_with_attack_roll", "attack_roll_made", "spell_restores_hp", "cantrip_misses_or_saved",
                  "misses_with_attack_roll", "deals_damage", "casts_spell"}
D20_ROLLS = ("attack_roll", "saving_throw", "ability_check", "initiative")

# Rules that apply to every player character.
PC_RULES = ["dnd5e/rule/heroic-inspiration"]
# Values the engine needs and must find in the catalog; used only when the catalog lacks them.
FALLBACK = {
    "spell_save_dc": {"op": "add", "args": [8, {"var": "spellcasting_mod"}, {"var": "proficiency_bonus"}]},
    "spell_attack_bonus": {"op": "add", "args": [{"var": "spellcasting_mod"}, {"var": "proficiency_bonus"}]},
}


def slug(ref):
    return ref.split("/")[-1]


def snake(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def roll_matches(pattern, name):
    """'saving_throw' covers 'saving_throw.dex'; 'd20_test' covers every d20 roll."""
    if pattern == name or name.startswith(pattern + "."):
        return True
    if pattern == "d20_test":
        return name.split(".")[0] in D20_ROLLS
    return False


class Ctx:
    """What a single call is about: who acts, on whom, with what attack/spell/roll."""

    def __init__(self, actor, target=None, ref=None, **kw):
        self.actor, self.target, self.ref = actor, target, ref
        self.attack = None      # dict: type, via, range, ability, weapon, feature, damage_type, explicit
        self.spell = None       # dict: ref, slot, level, ability, cantrip
        self.roll = None        # roll being made: 'attack_roll', 'saving_throw.dex', ...
        self.crit = False
        self.chosen = {}
        self.scoped = []        # (owner, effect, ref) applying to this call only
        self.damage_amount = 0
        self.item = None
        self.flags = {}
        self.__dict__.update(kw)

    def sub(self, **kw):
        c = copy.copy(self)
        c.chosen = dict(self.chosen)
        c.flags = dict(self.flags)
        c.__dict__.update(kw)
        return c


class Creature:
    def __init__(self, eng, name, side, kind):
        self.eng, self.name, self.side, self.kind = eng, name, side, kind
        self.scores = {}
        self.class_levels = {}
        self.subclasses = {}
        self.level = 0
        self.hp = self.hp_base = 0
        self.temp_hp = 0
        self.features = []          # granted entry refs (class, species, background, feat, subclass)
        self.choices = {}           # (ref, choice key) -> option id
        self.items = []             # {"ref", "state"} (worn / wielded / held / carried)
        self.conditions = {}        # condition ref -> {"source", "duration", "implied_by"}
        self.temps = []             # temporary effects applied to this creature
        self.resources = {}         # id -> {"cur", "max", "ref", "fx"}
        self.slots = {}             # spell level -> [current, max]
        self.prof = {k: set() for k in ("saving_throw", "skill", "weapon", "armor", "tool", "expertise")}
        self.cantrips, self.prepared, self.always, self.spellbook = [], [], [], []
        self.spell_ability = None
        self.masteries = []
        self.hit_dice = {}          # class -> [current, max, die]
        self.x = 0
        self.dead = self.stable = False
        self.death = [0, 0]
        self.concentration = None   # {"ref", "temps"}
        self.turn = {}
        self.economy = {}
        self.uses = {}              # frequency counters
        self.monster = None         # creature entry for monsters
        self.xp = 0
        self.drops = 0
        self.speed_base = 30
        self.ac_fixed = None
        self.save_bonus = {}
        self.cr_pb = None

    # -- basics -------------------------------------------------------------------------------
    def __repr__(self):
        return self.name

    def mod(self, ab):
        return self.eng.cat.ability_mod(self.scores[ab])

    @property
    def pb(self):
        if self.cr_pb is not None:
            return self.cr_pb
        return self.eng.cat.proficiency_bonus(max(1, self.level))

    @property
    def alive(self):
        return not self.dead

    @property
    def up(self):
        return not self.dead and self.hp > 0

    def has_item(self, ref_or_slug, state=None):
        for it in self.items:
            if slug(it["ref"]) == slug(ref_or_slug) and (state is None or it["state"] == state
                                                          or (state == "held" and it["state"] == "wielded")):
                return True
        return False

    # -- effect sources ------------------------------------------------------------------------
    def sources(self):
        """(ref, effect, owner_temp) for every effect currently shaping this creature."""
        cat = self.eng.cat
        refs = list(self.features) + GLOBAL_RULES + (PC_RULES if self.kind == "pc" else []) + list(self.conditions)
        if self.monster:
            refs.append(self.monster["ref"])
        for ref in refs:
            e = cat.get(ref)
            for i, fx in enumerate(e.get("effects") or []):
                yield from self._expand(ref, fx, i)
        for it in self.items:
            e = cat.get(it["ref"])
            for i, fx in enumerate(e.get("effects") or []):
                if fx["op"] in PASSIVE:
                    yield it["ref"], fx, {"item": it}
        for t in self.temps:
            yield t["ref"], t["fx"], t

    def _expand(self, ref, fx, i):
        if fx["op"] == "choice":
            pick = self.choices.get((ref, fx.get("id") or i))
            for o in fx["options"]:
                if o["id"] == pick:
                    for j, sub in enumerate(o["effects"]):
                        yield from self._expand(ref, sub, f"{i}.{j}")
        elif fx["op"] in PASSIVE:
            yield ref, fx, None

    def passives(self, op):
        for ref, fx, t in self.sources():
            if fx["op"] == op:
                yield ref, fx, t


class Engine:
    def __init__(self, rng, catalog=None, log=None):
        self.cat = catalog or Catalog()
        self.log = log or CallLog()
        self.rng = rng
        self.ex = Evaluator(rng, self.log, self.cat)
        self.creatures = []
        self.round = 0
        self.current = None
        self.policy = None          # object with decision hooks (see simulate_goblins.Policy)
        self.note_mechanics = {}    # (ref, op) -> (structured field, why): notes audited as mechanics
        reg = self.cat.system["registries"]
        self.var_formulas = {v["id"]: v.get("formula") for v in reg["variables"]}
        self.stat_formulas = {v["id"]: v.get("formula") for v in reg["stats"]}
        self.level_rules = {r["id"]: r for r in self.cat.system["levels"]["rules"]}
        self.preds = {p["id"] for p in reg["predicates"]}
        self.events = {e["id"] for e in reg["events"]}

    # =========================================================================================
    # values
    # =========================================================================================
    def resolver(self, c, ctx):
        return lambda name: self.var(c, name, ctx)

    def ev(self, x, c, ctx, **kw):
        return self.ex.ev(x, self.resolver(c, ctx), ref=ctx.ref if ctx else None, **kw)

    def var(self, c, name, ctx):
        log = self.log
        ref = ctx.ref if ctx else None
        head, _, tail = name.partition(".")
        if head == "ability_mod":
            return c.mod(tail)
        if head == "ability_score":
            return c.scores[tail]
        if head == "class_level":
            return c.class_levels.get(tail, 0)
        if head == "chosen":
            if tail in ctx.chosen:
                return ctx.chosen[tail]
            if tail in ("weapon_damage_type", "attack_damage_type", "cantrip_damage_type") and ctx.attack:
                return ctx.attack.get("damage_type")
            log.call("var", name, "ENGINE_GAP", ref, "choice not recorded in context")
            return 0
        if head == "speed":
            return self.speed(c, tail or "walk", ctx)
        if head == "condition_level":
            return 0
        simple = {
            "proficiency_bonus": lambda: c.pb,
            "level": lambda: c.level if c.kind == "pc" else 1,
            "hp_max": lambda: self.hp_max(c),
            "spell_slot_level": lambda: (ctx.spell or {}).get("slot", 0),
            "damage_amount": lambda: ctx.damage_amount,
            "attack_ability_mod": lambda: self.attack_ability_mod(c, ctx),
            "spellcasting_mod": lambda: c.mod(self.spell_ability(c, ctx)),
        }
        if name in simple:
            log.call("var", name, "OK", ref)
            return simple[name]()
        if name in ("spell_save_dc", "spell_attack_bonus"):
            f = self.var_formulas.get(name)
            if f is None:
                log.call("var", name, "DATA_GAP", "system.json#registries.variables",
                         "formula only in prose (description / rule text); engine FALLBACK used")
                f = FALLBACK[name]
            else:
                log.call("var", name, "OK", "system.json#registries.variables")
            return self.ev(f, c, ctx)
        log.call("var", name, "ENGINE_GAP", ref)
        return 0

    def spell_ability(self, c, ctx):
        if ctx and ctx.spell and ctx.spell.get("ability"):
            return ctx.spell["ability"]
        return c.spell_ability or "int"

    # =========================================================================================
    # predicates
    # =========================================================================================
    def holds(self, p, c, ctx):
        if p is None:
            return True
        if "all" in p:
            return all(self.holds(q, c, ctx) for q in p["all"])
        if "any" in p:
            return any(self.holds(q, c, ctx) for q in p["any"])
        if "not" in p:
            return not self.holds(p["not"], c, ctx)
        name, a = p["pred"], p.get("args", {})
        fn = getattr(self, "p_" + name, None)
        ref = ctx.ref if ctx else None
        if fn is None:
            self.log.call("pred", name, "ENGINE_GAP", ref, "predicate not implemented; treated as false")
            return False
        r = fn(c, ctx, **a)
        if r is None:   # predicate answered by the GM / scene
            return False
        return r

    def gm_pred(self, name, ctx, value, why):
        self.log.call("pred", name, "GM", ctx.ref if ctx else None, why)
        return value

    def ok(self, name, ctx):
        self.log.call("pred", name, "OK", ctx.ref if ctx else None)

    def p_effect_active(self, c, ctx, effect):
        self.ok("effect_active", ctx)
        return any(slug(t["ref"]) == effect for t in c.temps)

    def p_attack_is(self, c, ctx, **a):
        self.ok("attack_is", ctx)
        at = (ctx.attack or {}) if ctx else {}
        if not at:
            return False
        for k, v in a.items():
            if k == "weapon_kind":
                if v == "monk" and not self.is_monk_weapon(at.get("weapon")):
                    return False
            elif k == "attack_kind":
                if v == "feature" and not at.get("feature"):
                    return False
            elif at.get(k) != v:
                return False
        return True

    def is_monk_weapon(self, wref):
        if not wref:
            return False
        rule = self.cat.rule("dnd5e/feature/monk-martial-arts", "monk_weapons")
        w = self.cat.get(wref)["data"]
        light = any(slug(p["ref"]) == "light" for p in w.get("properties", []))
        kinds = {"simple_melee": w["category"] == "simple" and w["melee_or_ranged"] == "melee",
                 "martial_melee_with_light_property": w["category"] == "martial" and w["melee_or_ranged"] == "melee" and light}
        return any(kinds.get(k) for k in rule["weapons"])

    def p_only_monk_weapons_or_unarmed(self, c, ctx):
        self.ok("only_monk_weapons_or_unarmed", ctx)
        return all(self.is_monk_weapon(it["ref"]) for it in c.items
                   if it["state"] == "wielded" and "/weapon/" in it["ref"])

    def p_wearing_armor(self, c, ctx, category):
        self.ok("wearing_armor", ctx)
        return any(it["state"] == "worn" and self.cat.get(it["ref"])["data"]["category"] == category
                   for it in c.items if "/armor/" in it["ref"])

    def p_wearing_armor_any(self, c, ctx):
        self.ok("wearing_armor_any", ctx)
        return any(it["state"] == "worn" and self.cat.get(it["ref"])["data"]["category"] != "shield"
                   for it in c.items if "/armor/" in it["ref"])

    def p_using_shield(self, c, ctx):
        self.ok("using_shield", ctx)
        return c.has_item("dnd5e/armor/shield", "wielded")

    def p_item_state(self, c, ctx, item, state):
        self.ok("item_state", ctx)
        if item == "this":
            return ctx.item is not None and ctx.item["state"] == state
        if not self.cat.exists(f"dnd5e/armor/{item}") and not any(
                self.cat.exists(f"dnd5e/{k}/{item}") for k in ("gear", "weapon", "magic-item")):
            self.log.call("pred_arg", f"item_state.item={item}", "DATA_GAP", ctx.ref,
                          "item argument is not a catalog slug")
            item = item.replace("_", "-")
        return c.has_item(item, state)

    def p_has_condition(self, c, ctx, condition):
        self.ok("has_condition", ctx)
        return f"dnd5e/condition/{condition}" in c.conditions

    def p_within_feet(self, c, ctx, feet, who=None, **a):
        self.ok("within_feet", ctx)
        if who == "enemy":
            return any(o.up and o.side != c.side and abs(o.x - c.x) <= feet
                       and not (a.get("not_incapacitated") and self.p_has_condition(o, ctx, "incapacitated"))
                       for o in self.creatures)
        other = ctx.actor if who == "attacker" else ctx.target
        if other is None or other is c:
            other = ctx.actor if ctx.actor is not c else ctx.target
        return other is not None and abs(other.x - c.x) <= feet

    def p_beyond_normal_range(self, c, ctx):
        self.ok("beyond_normal_range", ctx)
        at = ctx.attack or {}
        return bool(at.get("normal_feet")) and ctx.target is not None and abs(ctx.target.x - c.x) > at["normal_feet"]

    def p_beyond_long_range(self, c, ctx):
        self.ok("beyond_long_range", ctx)
        at = ctx.attack or {}
        return bool(at.get("long_feet")) and ctx.target is not None and abs(ctx.target.x - c.x) > at["long_feet"]

    def p_roller_is_source(self, c, ctx):
        self.ok("roller_is_source", ctx)
        return ctx.flags.get("effect_source") is not None and ctx.flags.get("effect_source") is ctx.actor

    def p_first_attack_this_turn(self, c, ctx):
        self.ok("first_attack_this_turn", ctx)
        return c.turn.get("attacks", 0) == 0

    def p_roll_is(self, c, ctx, roll):
        self.ok("roll_is", ctx)
        return bool(ctx.roll) and roll_matches(roll, ctx.roll)

    def p_roll_succeeded(self, c, ctx, roll=None):
        return self.gm_pred("roll_succeeded", ctx, False, "outcome of a roll not tracked by the prototype")

    def p_is_monster(self, c, ctx):
        self.ok("is_monster", ctx)
        return c.kind == "monster"

    def p_hp_is(self, c, ctx, **a):
        self.ok("hp_is", ctx)
        if a.get("zero"):
            return c.hp == 0
        if a.get("bloodied"):
            return c.hp <= self.hp_max(c) // 2
        if "at_most" in a:
            return c.hp <= a["at_most"]
        return False

    def p_can_see(self, c, ctx, **a):
        return self.gm_pred("can_see", ctx, True, "scene assumption: bright light, no obscurement")

    def p_obscured(self, c, ctx, **a):
        return self.gm_pred("obscured", ctx, False, "scene assumption: open field")

    def p_behind_cover(self, c, ctx, **a):
        return self.gm_pred("behind_cover", ctx, False, "scene assumption: no cover")

    def p_in_enemy_line_of_sight(self, c, ctx):
        return self.gm_pred("in_enemy_line_of_sight", ctx, True, "scene assumption: open field")

    def p_speed_is_zero(self, c, ctx):
        self.ok("speed_is_zero", ctx)
        return self.speed(c, "walk", ctx) == 0

    def p_concentrating(self, c, ctx):
        self.ok("concentrating", ctx)
        return c.concentration is not None

    def p_deals_damage_type(self, c, ctx, damage_type):
        self.ok("deals_damage_type", ctx)
        return bool(ctx.attack) and ctx.attack.get("damage_type") == damage_type

    def p_damage_from_spell(self, c, ctx, spell):
        self.ok("damage_from_spell", ctx)
        return bool(ctx.spell) and slug(ctx.spell["ref"]) == spell

    def p_spell_cast_with_slot(self, c, ctx):
        self.ok("spell_cast_with_slot", ctx)
        return bool(ctx.spell) and ctx.spell.get("slot", 0) > 0

    def p_target_is_source(self, c, ctx):
        self.ok("target_is_source", ctx)
        return c is ctx.actor

    def p_chosen_by_source(self, c, ctx):
        self.ok("chosen_by_source", ctx)
        return c.side == ctx.actor.side

    def p_level_at_least(self, c, ctx, level, **a):
        self.ok("level_at_least", ctx)
        if "class" in a:
            return c.class_levels.get(a["class"], 0) >= level
        return c.level >= level

    def p_doesnt_sleep(self, c, ctx):
        self.ok("doesnt_sleep", ctx)
        return any("magical_sleep" in fx["restrictions"] for _, fx, _ in c.passives("restrict"))

    def p_immune_to_condition(self, c, ctx, condition):
        self.ok("immune_to_condition", ctx)
        if c.monster:
            imm = c.monster["data"].get("condition_immunities") or {}
            return condition in str(imm).lower()
        return False

    def p_save_against(self, c, ctx, **a):
        self.ok("save_against", ctx)
        return bool(a.get("condition")) and ctx.flags.get("save_against") == a.get("condition")

    def p_check_uses(self, c, ctx, **a):
        self.ok("check_uses", ctx)
        return ctx.flags.get("skill") == a.get("skill")

    def p_damage_reduced_to_zero(self, c, ctx):
        self.ok("damage_reduced_to_zero", ctx)
        return ctx.flags.get("damage_after_reduction", 1) <= 0

    # =========================================================================================
    # derived stats
    # =========================================================================================
    def modifiers(self, c, stat, ctx):
        out = []
        for ref, fx, t in list(c.passives("modifier")) + [(r, f, None) for (o, f, r) in ctx.scoped
                                                           if o is c and f["op"] == "modifier"]:
            if not roll_matches(fx["stat"], stat):
                continue
            sub = ctx.sub(ref=ref, item=t.get("item") if t else None)
            if t and t.get("source"):
                sub = sub.sub(target=c)
            if self.holds(fx.get("when"), c, sub):
                self.log.call("op", "modifier", "OK", ref, fx["stat"])
                out.append((ref, fx, t, sub))
        return out

    def stat(self, c, stat, ctx, base=0):
        sets, val = [], base
        mods = self.modifiers(c, stat, ctx)
        for ref, fx, t, sub in mods:
            if fx["mode"] == "set":
                owner = t["source"] if t and t.get("source") else c
                sets.append(self.ev(fx["value"], c if owner is c else owner, sub))
        if sets:
            val = max(sets)   # rule/armor-class: one base calculation, the bearer picks the best
        for ref, fx, t, sub in mods:
            owner = t["source"] if t and t.get("source") else c
            if fx["mode"] == "add":
                val += self.ev(fx["value"], owner, sub)
            elif fx["mode"] == "max":
                val = max(val, self.ev(fx["value"], owner, sub))
            elif fx["mode"] == "min":
                val = min(val, self.ev(fx["value"], owner, sub))
        return val

    def ac(self, c, ctx):
        if c.ac_fixed is not None:
            base = c.ac_fixed
            self.log.call("stat", "ac", "OK", c.monster["ref"], "stat block AC")
            return base + sum(self.ev(fx["value"], c, sub) for ref, fx, t, sub in self.modifiers(c, "ac", ctx)
                              if fx["mode"] == "add")
        formula = self.stat_formulas.get("base_ac")
        if formula:
            self.log.call("stat", "base_ac", "OK", "system.json#registries.stats", "default formula")
            default = self.ev(formula, c, ctx)
        else:
            self.log.call("rule", "armor-class#base_ac", "DATA_GAP", "dnd5e/rule/armor-class",
                          "'10 plus your Dexterity modifier' only in prose; engine FALLBACK used")
            default = 10 + c.mod("dex")
        base = self.stat(c, "base_ac", ctx, default)
        return self.stat(c, "ac", ctx, base)

    def hp_max(self, c):
        ctx = Ctx(c, ref="hp_max")
        return self.stat(c, "hp_max", ctx, c.hp_base)

    def speed(self, c, mode, ctx):
        ctx = ctx or Ctx(c)
        v, zero = c.speed_base, False
        for ref, fx, t in c.passives("speed"):
            if fx.get("movement", "walk") != mode:
                continue
            sub = ctx.sub(ref=ref)
            if not self.holds(fx.get("when"), c, sub):
                continue
            val = self.ev(fx["value"], c, sub)
            if fx["mode"] == "set":
                zero = zero or val == 0
                v = max(v, val)
            elif fx["mode"] == "add":
                v += val
            self.log.call("op", "speed", "OK", ref)
        return 0 if zero else max(0, v)

    def restricted(self, c, what, ctx=None):
        ctx = ctx or Ctx(c)
        for ref, fx, t in c.passives("restrict"):
            if what in fx["restrictions"] and self.holds(fx.get("when"), c, ctx.sub(ref=ref)):
                self.log.call("op", "restrict", "OK", ref, what)
                return True
        return False

    def can_act(self, c):
        return c.up and not self.restricted(c, "take_actions")

    def attack_ability_mod(self, c, ctx):
        at = ctx.attack or {}
        return c.mod(at.get("ability", "str"))

    # =========================================================================================
    # d20 tests
    # =========================================================================================
    def roll_mode(self, roller, roll, ctx, against=None):
        adv = dis = 0
        pools = [(roller, "own")]
        if against is not None:
            pools.append((against, "against"))
        for who, direction in pools:
            for ref, fx, t in who.passives("roll_mode"):
                if fx.get("direction", "own") != direction:
                    continue
                if not any(roll_matches(r, roll) for r in fx["rolls"]):
                    continue
                sub = ctx.sub(ref=ref, roll=roll, flags=dict(ctx.flags, effect_source=t.get("source") if t else None))
                if not self.holds(fx.get("when"), who, sub):
                    continue
                if t is not None:
                    ctx.flags.setdefault("used_temps", []).append(t)
                self.log.call("op", "roll_mode", "OK", ref, f'{fx["mode"]} on {roll}')
                if fx["mode"] == "advantage":
                    adv += 1
                else:
                    dis += 1
        for o, fx, ref in ctx.scoped:
            if fx["op"] == "roll_mode" and o is roller and any(roll_matches(r, roll) for r in fx["rolls"]):
                adv += fx["mode"] == "advantage"
                dis += fx["mode"] != "advantage"
        return "advantage" if adv and not dis else "disadvantage" if dis and not adv else "normal"

    def d20(self, mode):
        a, b = self.rng.randint(1, 20), self.rng.randint(1, 20)
        return max(a, b) if mode == "advantage" else min(a, b) if mode == "disadvantage" else a

    def auto_result(self, c, roll, ctx, against=None):
        pools = [(c, "own")] + ([(against, "against")] if against else [])
        for who, direction in pools:
            for ref, fx, t in who.passives("auto_result"):
                if fx.get("direction", "own") != direction or not any(roll_matches(r, roll) for r in fx["rolls"]):
                    continue
                if self.holds(fx.get("when"), who, ctx.sub(ref=ref, roll=roll)):
                    self.log.call("op", "auto_result", "OK", ref, f'{roll} -> {fx["result"]}')
                    return fx["result"]
        for o, fx, ref in ctx.scoped:
            if fx["op"] == "auto_result" and o is None and any(roll_matches(r, roll) for r in fx["rolls"]):
                if self.holds(fx.get("when"), c, ctx.sub(ref=ref, roll=roll)):
                    self.log.call("op", "auto_result", "OK", ref, f'{roll} -> {fx["result"]}')
                    return fx["result"]
        return None

    def saving_throw(self, c, ability, dc, ctx):
        roll = f"saving_throw.{ability}"
        sub = ctx.sub(roll=roll)
        forced = self.auto_result(c, roll, sub)
        if forced:
            return forced == "success"
        mode = self.roll_mode(c, roll, sub)
        nat = self.d20(mode)
        if c.monster:
            bonus = c.save_bonus[ability]
        else:
            bonus = c.mod(ability) + (c.pb if ability in c.prof["saving_throw"] else 0)
        total = nat + self.stat(c, roll, sub, bonus)
        okay = total >= dc
        self.log.say(f"{c} save {ability.upper()} {total} vs DC {dc}: {'success' if okay else 'fail'}")
        self.emit("succeeds_saving_throw" if okay else "fails_saving_throw", c, sub)
        return okay

    # =========================================================================================
    # effects
    # =========================================================================================
    def run(self, effects, ctx):
        for fx in effects or []:
            self.run_one(fx, ctx)
            if ctx.flags.pop("spend_failed", False):
                return

    def run_one(self, fx, ctx):
        op = fx["op"]
        fn = getattr(self, "op_" + op, None)
        if fn is None:
            self.log.call("op", op, "ENGINE_GAP", ctx.ref)
            return
        if fx.get("when") and op not in PASSIVE and not self.holds(fx["when"], ctx.target or ctx.actor, ctx):
            return
        if fx.get("note"):
            self.check_note(fx, ctx)
        fn(fx, ctx)

    def check_note(self, fx, ctx):
        """Notes audited as carrying a mechanic: a gap while the structured field is missing."""
        audit = self.note_mechanics.get((ctx.ref, fx["op"]))
        if audit is None:
            self.log.call("note", fx["op"], "OK", ctx.ref, fx["note"])
            return
        field, why = audit
        value = fx
        for part in (field or "").split("."):
            value = value.get(part) if isinstance(value, dict) and part else (value if not part else None)
        if field is None or value is None:
            self.log.call("note", fx["op"], "DATA_GAP", ctx.ref, why)
        else:
            self.log.call("note", fx["op"], "OK", ctx.ref, f"structured as '{field}'")

    def targets_of(self, fx, ctx):
        """Resolve an effect's target spec to creatures (policy chooses among candidates)."""
        t = fx.get("target") or {}
        kind = t.get("kind")
        if kind == "self":
            return [ctx.actor]
        if kind in (None, "inherit"):
            return [ctx.target] if ctx.target else [ctx.actor]
        if kind == "area":
            return self.policy.area_targets(self, ctx.actor, fx, ctx)
        if kind in ("creature", "creature_or_object"):
            n = int(self.ev(t.get("count", 1), ctx.actor, ctx))
            if ctx.flags.get("targets"):
                return ctx.flags["targets"][:n]
            return [ctx.target] if ctx.target else []
        self.log.call("target", str(kind), "ENGINE_GAP", ctx.ref)
        return [ctx.target] if ctx.target else []

    def op_reference(self, fx, ctx):
        rule = fx["rule"]
        if rule == ctx.ref:
            self.log.call("op", "reference", "DATA_GAP", ctx.ref, "refers to its own entry: the mechanic is only in a note")
            return
        e = self.cat.get(rule)
        if e is None:
            self.log.call("op", "reference", "DATA_GAP", ctx.ref, f"missing entry {rule}")
            return
        effects = e.get("effects") or []
        if not effects:
            self.log.call("op", "reference", "DATA_GAP", ctx.ref, f"{rule} has no effects")
            return
        acts = [x for x in effects if x["op"] in ("attack", "save", "check")]
        if len(acts) > 1:
            self.log.call("op", "reference", "DATA_GAP", rule,
                          "alternative options listed side by side without a 'choice'; engine runs the first")
            effects = [acts[0]]
        self.log.call("op", "reference", "OK", ctx.ref, rule)
        if len(effects) == 1 and effects[0]["op"] == "activation":
            self.run(effects[0]["then"], ctx.sub(ref=rule))
        else:
            self.run(effects, ctx.sub(ref=rule))

    def op_choice(self, fx, ctx):
        pick = self.policy.choose(self, ctx.actor, fx, ctx)
        self.log.call("op", "choice", "OK", ctx.ref, fx.get("id"))
        for o in fx["options"]:
            if o["id"] == pick:
                if "value" in o and fx.get("id"):
                    ctx.chosen[fx["id"]] = o["value"]
                self.run(o["effects"], ctx)

    def op_repeat(self, fx, ctx):
        n = int(self.ev(fx["times"], ctx.actor, ctx))
        self.log.call("op", "repeat", "OK", ctx.ref)
        for i in range(n):
            self.run(fx["then"], ctx.sub(flags=dict(ctx.flags, repeat_index=i)))

    def op_attack(self, fx, ctx):
        targets = self.targets_of(fx, ctx) if fx.get("target") else [ctx.target]
        for t in targets:
            if t is None or not t.alive:
                continue
            self.resolve_attack(ctx.actor, t, fx, ctx)

    def op_damage(self, fx, ctx):
        for t in self.targets_of(fx, ctx):
            if t is not None and t.alive:
                self.deal_damage(ctx.actor, t, fx, ctx)

    def op_heal(self, fx, ctx):
        for t in self.targets_of(fx, ctx):
            if t is None or t.dead:
                continue
            amt = max(0, int(self.ev(fx["amount"], ctx.actor, ctx.sub(target=t))))
            self.log.call("op", "heal", "OK", ctx.ref)
            self.heal(t, amt, ctx)

    def heal(self, t, amt, ctx):
        before = t.hp
        t.hp = min(self.hp_max(t), t.hp + amt)
        if before == 0 and t.hp > 0:
            t.death = [0, 0]
            t.stable = False
        self.end_while(t)
        self.log.say(f"{t} regains {t.hp - before} HP ({t.hp}/{self.hp_max(t)})")
        self.emit("regains_hit_points", t, ctx.sub(target=t))
        if ctx.spell and not ctx.flags.get("bonus_heal"):
            self.emit("spell_restores_hp", ctx.actor, ctx.sub(target=t, flags=dict(ctx.flags, bonus_heal=True)))

    def op_temp_hp(self, fx, ctx):
        for t in self.targets_of(fx, ctx):
            t.temp_hp = max(t.temp_hp, int(self.ev(fx["amount"], ctx.actor, ctx)))
            self.log.call("op", "temp_hp", "OK", ctx.ref)

    def op_save(self, fx, ctx):
        targets = self.targets_of(fx, ctx)
        ability = fx["ability"]
        for t in targets:
            if t is None or not t.alive:
                continue
            ab = ability
            if isinstance(ab, dict):
                ab = max(ab["choose_from"], key=lambda a: t.save_bonus.get(a, t.mod(a)) if t.monster else t.mod(a))
                self.log.call("op", "save.choose_from", "OK", ctx.ref, "the target picks its better ability")
            dc = int(self.ev(fx["dc"], ctx.actor, ctx.sub(target=t)))
            self.log.call("op", "save", "OK", ctx.ref)
            sub = ctx.sub(target=t)
            okay = self.saving_throw(t, ab, dc, sub)
            if okay:
                if fx.get("half_on_success"):
                    self.run([dict(d, _half=True) for d in fx.get("on_fail", []) if d["op"] == "damage"], sub)
                self.run(fx.get("on_success"), sub)
                if ctx.spell and ctx.spell.get("cantrip"):
                    self.emit("cantrip_misses_or_saved", ctx.actor, sub.sub(damage_amount=self.preview_damage(fx.get("on_fail"), sub)))
            else:
                self.run(fx.get("on_fail"), sub)

    def op_check(self, fx, ctx):
        self.log.call("op", "check", "OK", ctx.ref)
        c = ctx.actor
        roll = f'ability_check.{fx["ability"]}'
        nat = self.d20(self.roll_mode(c, roll, ctx.sub(roll=roll)))
        bonus = c.mod(fx["ability"]) + (c.pb if fx.get("skill") in c.prof["skill"] else 0)
        if c.monster and fx.get("skill"):
            bonus = (c.monster["data"].get("skills") or {}).get(fx["skill"], bonus)
        okay = nat + bonus >= int(self.ev(fx["dc"], c, ctx))
        self.run(fx.get("on_success") if okay else fx.get("on_fail"), ctx)

    def op_apply_condition(self, fx, ctx):
        if not fx.get("duration") and fx.get("note"):
            self.log.call("duration", "apply_condition", "DATA_GAP", ctx.ref,
                          "how long it lasts is only in a note: " + fx["note"])
        for t in self.targets_of(fx, ctx):
            if t is not None and t.alive:
                self.apply_condition(t, fx["condition"], fx.get("duration"), ctx)

    def op_remove_condition(self, fx, ctx):
        for t in self.targets_of(fx, ctx) if fx.get("target") else [ctx.target or ctx.actor]:
            for cond in fx.get("conditions", []):
                if t.conditions.pop(cond, None) is not None:
                    self.log.call("op", "remove_condition", "OK", ctx.ref, cond)

    def op_move(self, fx, ctx):
        self.log.call("op", "move", "OK", ctx.ref, fx.get("mode"))
        dist = fx.get("distance_feet", 0)
        for t in [ctx.target] if fx.get("mode") == "push" else [ctx.actor]:
            if t is None:
                continue
            away = 1 if t.x >= ctx.actor.x else -1
            t.x += away * dist if fx.get("mode") == "push" else 0

    def op_restore(self, fx, ctx):
        c = ctx.actor
        res = fx["resource"]
        if res == "spell_slot":
            if fx["amount"] == "all":
                for lv in c.slots:
                    c.slots[lv][0] = c.slots[lv][1]
            else:
                budget = int(self.ev(fx["amount"], c, ctx))
                for lv in sorted(c.slots, reverse=True):
                    while budget >= int(lv) and c.slots[lv][0] < c.slots[lv][1] and int(lv) <= fx.get("max_level", 9):
                        c.slots[lv][0] += 1
                        budget -= int(lv)
            self.log.call("op", "restore", "OK", ctx.ref, res)
            return
        if res == "hit_point_dice":
            for cls, hd in c.hit_dice.items():
                hd[0] = hd[1] if fx["amount"] == "all" else min(hd[1], hd[0] + int(self.ev(fx["amount"], c, ctx)))
            self.log.call("op", "restore", "OK", ctx.ref, res)
            return
        r = c.resources.get(res)
        if r is None:
            self.log.call("op", "restore", "ENGINE_GAP", ctx.ref, f"unknown resource {res}")
            return
        mx = self.resource_max(c, res)
        r["cur"] = mx if fx["amount"] == "all" else min(mx, r["cur"] + int(self.ev(fx["amount"], c, ctx)))
        self.log.call("op", "restore", "OK", ctx.ref, res)

    def op_spend(self, fx, ctx):
        r = ctx.actor.resources.get(fx["resource"])
        if r and r["cur"] >= fx.get("amount", 1):
            r["cur"] -= fx.get("amount", 1)
            self.log.call("op", "spend", "OK", ctx.ref, fx["resource"])
        else:
            ctx.flags["spend_failed"] = True

    def op_end_effect(self, fx, ctx):
        if fx.get("scope") == "concentration":
            self.end_concentration(ctx.actor, ctx)
        self.log.call("op", "end_effect", "OK", ctx.ref, fx.get("scope"))

    def op_master_decision(self, fx, ctx):
        self.log.call("op", "master_decision", "GM", ctx.ref, fx.get("decision"))

    def op_reroll(self, fx, ctx):
        self.log.call("op", "reroll", "OK", ctx.ref, ",".join(fx["rolls"]))
        if "damage_roll" in fx["rolls"]:
            ctx.flags["damage_best_of"] = 2

    def op_trigger(self, fx, ctx):
        """A trigger run as part of a spell/feature: it waits on its target for the event."""
        for t in self.targets_of(fx, ctx) if fx.get("target") else [ctx.target or ctx.actor]:
            self.add_temp(t, fx, ctx, once=True)
            self.log.call("op", "trigger", "OK", ctx.ref, f'installed: {fx["event"]["event"]}')

    def op_grant(self, fx, ctx):
        self.log.call("op", "grant", "OK", ctx.ref)
        for r in fx["refs"]:
            if "/spell/" in r and r not in ctx.actor.always:
                ctx.actor.always.append(r)

    # Effects that create a lasting state when run (not passive here).
    def lasting(self, fx, ctx):
        for t in self.targets_of(fx, ctx):
            if t is not None and t.alive:
                self.add_temp(t, fx, ctx)
                self.log.call("op", fx["op"], "OK", ctx.ref, "temporary")

    op_modifier = op_roll_mode = op_defense = op_restrict = op_auto_result = op_speed = lasting

    def op_activation(self, fx, ctx):
        self.activate(ctx.actor, ctx.ref, fx, ctx.target, ctx)

    # =========================================================================================
    # temporary effects, conditions, concentration
    # =========================================================================================
    def add_temp(self, t, fx, ctx, once=False):
        dur = fx.get("duration") or {}
        temp = {"ref": ctx.ref, "fx": fx, "source": ctx.actor, "bearer": t, "duration": dur,
                "created_round": self.round, "created_turn_of": self.current, "once": once,
                "spell": ctx.spell, "chosen": dict(ctx.chosen)}
        if not dur and not once:
            # Contract: an effect without a duration lasts for the call that runs it (the triggering
            # attack, damage or roll), e.g. Deflect Attacks reducing the damage of that one attack.
            self.log.call("duration", "scoped_to_call", "OK", ctx.ref, fx["op"])
            ctx.scoped.append((t, fx, ctx.ref))
            return None
        t.temps.append(temp)
        if dur.get("concentration") and ctx.actor.concentration is not None:
            ctx.actor.concentration["temps"].append(temp)
        return temp

    def apply_condition(self, t, cond, duration, ctx, implied_by=None):
        if cond in t.conditions:
            return
        e = self.cat.get(cond)
        t.conditions[cond] = {"source": ctx.actor, "duration": duration or {}, "implied_by": implied_by,
                              "created_turn_of": self.current, "created_round": self.round}
        if duration and duration.get("concentration") and ctx.actor.concentration is not None:
            ctx.actor.concentration["temps"].append({"condition": cond, "bearer": t})
        self.log.call("op", "apply_condition", "OK", ctx.ref, slug(cond))
        self.log.say(f"{t} gains {e['name']}")
        self.emit("condition_gained", t, ctx.sub(target=t))
        # A condition's own apply_condition effects (Unconscious -> Incapacitated, Prone) run now.
        for fx in e.get("effects") or []:
            if fx["op"] == "apply_condition":
                # Contract: without a duration an implied condition lasts until something removes it
                # (Prone after Unconscious); one that ends with its parent says so with 'while'.
                if not fx.get("duration") and "parent" in fx.get("note", ""):
                    self.log.call("duration", f"{slug(cond)}->{slug(fx['condition'])}", "DATA_GAP", cond,
                                  "how long the implied condition lasts is only in a note")
                self.apply_condition(t, fx["condition"], fx.get("duration"), ctx.sub(ref=cond), implied_by=cond)

    def end_concentration(self, c, ctx=None):
        if not c.concentration:
            return
        for tmp in c.concentration["temps"]:
            b = tmp["bearer"]
            if "condition" in tmp:
                b.conditions.pop(tmp["condition"], None)
            elif tmp in b.temps:
                b.temps.remove(tmp)
        self.log.say(f"{c} loses concentration on {self.cat.get(c.concentration['ref'])['name']}")
        c.concentration = None

    def end_while(self, c):
        """Drop durations of kind 'while' whose predicate stopped holding."""
        for cond, info in list(c.conditions.items()):
            d = info["duration"]
            if d.get("kind") == "while" and not self.holds(d["while"], c, Ctx(c, ref=cond)):
                c.conditions.pop(cond, None)
                self.log.call("duration", "while", "OK", cond)
                self.log.say(f"{c} is no longer {self.cat.get(cond)['name']}")

    def expire(self, event, who):
        """End temps and conditions whose duration ends at this event of creature `who`."""
        for c in self.creatures:
            items = [(t, t["duration"]) for t in c.temps] + [((cond, info), info["duration"]) for cond, info in c.conditions.items()]
            for obj, dur in items:
                ends = dur.get("ends_on") or []
                until = dur.get("until") if dur.get("kind") == "until_event" else None
                hit = False
                for ev in ([until] if until else []):
                    hit |= self.event_matches(ev, event, who, c, obj)
                if not hit:
                    continue
                if isinstance(obj, tuple):
                    c.conditions.pop(obj[0], None)
                    self.log.say(f"{c}: {self.cat.get(obj[0])['name']} ends")
                elif obj in c.temps:
                    c.temps.remove(obj)

    def event_matches(self, ev, event, who, bearer, obj):
        if ev.get("event") != event:
            return False
        info = obj if isinstance(obj, dict) else obj[1]
        whose = ev.get("whose", "self")
        owner = {"self": info.get("source") if isinstance(obj, dict) else bearer, "source": info.get("source"),
                 "target": bearer, "any": who}.get(whose, bearer)
        if owner is not who:
            return False
        # 'next' turn end: skip the end of the turn during which the effect was created.
        if event == "turn_end" and info.get("created_turn_of") is who and info.get("created_round") == self.round:
            return False
        return True

    def used_up(self, t, event, used):
        """Temps on `t` that end on `event` (whose: target): with a 'when', only if they applied to this roll."""
        for tmp in list(t.temps):
            ends = [e for e in (tmp["duration"] or {}).get("ends_on") or [] if e.get("event") == event]
            if ends and (not tmp["fx"].get("when") or any(u is tmp for u in used)):
                t.temps.remove(tmp)
                self.log.call("duration", f"ends_on.{event}", "OK", tmp["ref"])

    def damage_events(self, t, ctx):
        """ends_on events of durations (e.g. Sleep ends when the target takes damage)."""
        self.used_up(t, "damage_taken", [])
        for cond, info in list(t.conditions.items()):
            for ev in info["duration"].get("ends_on") or []:
                if ev.get("event") == "damage_taken":
                    t.conditions.pop(cond, None)
                    self.log.call("duration", "ends_on.damage_taken", "OK", cond)
                    self.log.say(f"{t}: {self.cat.get(cond)['name']} ends (took damage)")

    # =========================================================================================
    # events and triggers
    # =========================================================================================
    def emit(self, event, c, ctx):
        if event not in self.events:
            self.log.call("event", event, "DATA_GAP", None, "event not in the registry")
        for ref, fx, t in list(c.passives("trigger")) + self.mastery_triggers(c, ctx):
            if fx["event"]["event"] != event:
                continue
            if t and t.get("once"):
                if not self.event_matches(fx["event"], event, c, c, t):
                    continue
                c.temps.remove(t)
            if t and t.get("source"):
                # A trigger installed by someone else's spell/feature acts for its source, on its bearer.
                sub = ctx.sub(ref=ref, actor=t["source"], target=c, spell=t.get("spell"),
                              chosen=dict(t.get("chosen") or {}))
            elif event in OUTWARD_EVENTS:
                sub = ctx.sub(ref=ref, actor=c)
            else:
                sub = ctx.sub(ref=ref, actor=c, target=c, flags=dict(ctx.flags, other=ctx.actor))
            if not self.holds(fx.get("condition"), c, sub):
                continue
            freq = fx.get("frequency")
            key = (ref, fx["event"]["event"])
            if freq and not self.freq_ok(c, key, freq):
                continue
            if fx.get("cost") == "reaction" and not c.economy.get("reaction"):
                continue
            if fx.get("optional") and not self.policy.use_trigger(self, c, ref, fx, sub):
                continue
            if fx.get("cost") == "reaction":
                c.economy["reaction"] = 0
            if freq:
                self.freq_use(c, key, freq)
            self.log.call("event", event, "OK", ref)
            if t is None and fx.get("optional"):
                self.mark_active(c, ref, fx, sub)
            self.run(fx["then"], sub)

    def mark_active(self, c, ref, fx, ctx):
        """An optional trigger whose effects last makes its entry active (effect_active)."""
        durs = [x.get("duration") for x in fx["then"] if x.get("duration")]
        if durs:
            c.temps.append({"ref": ref, "fx": {"op": "marker"}, "source": c, "bearer": c, "duration": durs[0],
                            "created_round": self.round, "created_turn_of": self.current})

    def mastery_triggers(self, c, ctx):
        at = ctx.attack if ctx else None
        if not at or not at.get("weapon"):
            return []
        w = self.cat.get(at["weapon"])["data"]
        m = w.get("mastery")
        if not m or slug(at["weapon"]) not in c.masteries:
            return []
        return [(m, fx, None) for fx in self.cat.get(m).get("effects") or [] if fx["op"] == "trigger"]

    def freq_ok(self, c, key, freq):
        return c.uses.get((key, freq["per"]), 0) < freq.get("count", 1)

    def freq_use(self, c, key, freq):
        c.uses[(key, freq["per"])] = c.uses.get((key, freq["per"]), 0) + 1
        self.log.call("frequency", freq["per"], "OK", key[0])

    def reset_uses(self, c, per):
        for k in [k for k in c.uses if k[1] == per]:
            del c.uses[k]

    # =========================================================================================
    # resources and activations
    # =========================================================================================
    def resource_max(self, c, res):
        r = c.resources[res]
        return int(self.ev(r["fx"]["max"], c, Ctx(c, ref=r["ref"])))

    def init_resources(self, c):
        for ref, fx, t in c.passives("resource"):
            rid = fx["resource"]
            old = c.resources.get(rid)
            c.resources[rid] = {"ref": ref, "fx": fx, "cur": 0}
            mx = self.resource_max(c, rid)
            c.resources[rid]["cur"] = mx if old is None else min(mx, old["cur"] + max(0, mx - old.get("max", mx)))
            c.resources[rid]["max"] = mx
            self.log.call("op", "resource", "OK", ref, rid)

    def recover(self, c, event):
        for rid, r in c.resources.items():
            for rec in r["fx"].get("recovery", []):
                if rec["on"]["event"] == event:
                    mx = self.resource_max(c, rid)
                    r["cur"] = mx if rec["amount"] == "all" else min(mx, r["cur"] + rec["amount"])
                    self.log.call("resource.recovery", rid, "OK", r["ref"], event)

    def activations(self, c):
        """Every activation the creature can use: (ref, effect)."""
        out = []
        for ref in list(c.features) + ([c.monster["ref"]] if c.monster else []) + list(c.conditions):
            for i, fx in enumerate(self.cat.get(ref).get("effects") or []):
                for r, f, _ in self.expand_all(c, ref, fx, i):
                    if f["op"] == "activation":
                        out.append((r, f))
        return out

    def expand_all(self, c, ref, fx, i):
        if fx["op"] == "choice":
            pick = c.choices.get((ref, fx.get("id") or i))
            for o in fx["options"]:
                if o["id"] == pick:
                    for j, sub in enumerate(o["effects"]):
                        yield from self.expand_all(c, ref, sub, f"{i}.{j}")
        else:
            yield ref, fx, None

    def can_pay(self, c, fx, ctx):
        cost = fx.get("cost")
        if cost in ("action", "bonus_action", "reaction") and not c.economy.get(cost):
            return False
        if cost in ("action", "bonus_action") and self.restricted(c, "take_" + cost + "s"):
            return False
        u = fx.get("uses")
        if u and c.resources.get(u["resource"], {}).get("cur", 0) < int(self.ev(u.get("amount", 1), c, ctx)):
            return False
        if fx.get("requires") and not self.holds(fx["requires"], c, ctx):
            return False
        return True

    def activate(self, c, ref, fx, target, ctx=None, label=None):
        ctx = (ctx or Ctx(c)).sub(actor=c, target=target, ref=ref)
        if not self.can_pay(c, fx, ctx):
            return False
        cost = fx.get("cost")
        if cost in ("action", "bonus_action", "reaction"):
            c.economy[cost] = 0
            if cost == "bonus_action":
                self.extend_rage(c)
        u = fx.get("uses")
        if u:
            c.resources[u["resource"]]["cur"] -= int(self.ev(u.get("amount", 1), c, ctx))
        self.log.call("op", "activation", "OK", ref, fx.get("name") or label)
        self.log.say(f"{c} uses {fx.get('name') or label or self.cat.get(ref)['name']}")
        if fx.get("name"):
            ctx.flags["feature"] = snake(fx["name"])
        then = fx["then"]
        actions = [x for x in then if x["op"] == "reference" and "/action/" in x["rule"]]
        if len(actions) > 1 and len(actions) == len(then) and " or " in fx.get("note", ""):
            self.log.call("op", "activation", "DATA_GAP", ref,
                          "one activation takes several actions listed without a 'choice' (" + fx.get("note", "") + ")")
            then = then[:1]
        if fx.get("duration"):
            c.temps.append({"ref": ref, "fx": {"op": "marker"}, "source": c, "bearer": c, "duration": fx["duration"],
                            "created_round": self.round, "created_turn_of": self.current})
            self.log.call("duration", "activation", "OK", ref, "entry becomes active")
        self.run(then, ctx)
        return True

    def extend_rage(self, c):
        for t in c.temps:
            if slug(t["ref"]) == "barbarian-rage":
                t["extended"] = True

    # =========================================================================================
    # attacks and damage
    # =========================================================================================
    def weapon_attack(self, c, wref, target, ctx=None, feature=None):
        w = self.cat.get(wref)
        fx = next(x for x in w["effects"] if x["op"] == "attack")
        ctx = (ctx or Ctx(c)).sub(ref=wref)
        rng = "ranged" if fx["attack_type"] == "ranged_weapon" else "melee"
        ability = self.default_ability(rng)
        at = {"type": fx["attack_type"], "via": "weapon", "range": rng, "weapon": wref, "feature": feature,
              "damage_type": w["data"]["damage"]["type"], "ability": ability}
        for p in w["data"].get("properties", []):
            if p.get("range") and (rng == "ranged" or ctx.flags.get("thrown")):
                at["normal_feet"], at["long_feet"] = p["range"]["normal_feet"], p["range"]["long_feet"]
        ctx.attack = at
        # attack_ability modifiers (Finesse choice, Martial Arts) pick the ability.
        self.choose_attack_ability(c, ctx, w)
        self.resolve_attack(c, target, fx, ctx)

    def default_ability(self, rng):
        """Melee attacks use Str, ranged Dex: read from the attack bonus formulas of system levels.rules."""
        r = self.level_rules.get(f"{rng}_attack_bonus")
        if r:
            self.log.call("rule", f"levels.rules#{rng}_attack_bonus", "OK", "system.json#levels.rules")
            m = re.search(r"ability_mod\.(\w+)", json.dumps(r["data"]["formula"]))
            return m.group(1)
        self.log.call("rule", "attack-rolls#attack_ability", "DATA_GAP", "dnd5e/rule/attack-rolls",
                      "Attack Roll Abilities table is text; engine FALLBACK (melee Str, ranged Dex)")
        return "str" if rng == "melee" else "dex"

    def choose_attack_ability(self, c, ctx, w=None):
        best = ctx.attack["ability"]
        if w:
            for p in w["data"].get("properties", []):
                if slug(p["ref"]) == "finesse":
                    self.log.call("op", "choice", "OK", p["ref"], "finesse_ability")
                    best = max(("str", "dex"), key=c.mod)
        for ref, fx, t, sub in self.modifiers(c, "attack_ability", ctx):
            cand = [ab for ab in ("str", "dex", "con", "int", "wis", "cha")
                    if fx["value"] == {"var": f"ability_mod.{ab}"}]
            if cand and c.mod(cand[0]) > c.mod(best):
                best = cand[0]
        ctx.attack["ability"] = best

    def unarmed_strike(self, c, target, ctx=None, feature=None):
        ref = "dnd5e/rule/unarmed-strike"
        ctx = (ctx or Ctx(c)).sub(ref=ref)
        ctx.attack = {"type": "melee", "via": "unarmed_strike", "range": "melee", "weapon": None,
                      "feature": feature, "damage_type": "bludgeoning", "ability": self.default_ability("melee")}
        self.choose_attack_ability(c, ctx)
        e = self.cat.get(ref)
        fx = e["effects"][0]
        if fx["op"] == "choice":
            opt = next(o for o in fx["options"] if o["id"] == self.policy.choose(self, c, fx, ctx))
            self.log.call("op", "choice", "OK", ref, "unarmed_strike")
            fx = opt["effects"][0]
        else:
            self.log.call("op", "reference", "DATA_GAP", ref,
                          "Damage/Grapple/Shove listed side by side without a 'choice'; engine runs the first")
        if fx["op"] == "attack":
            self.resolve_attack(c, target, fx, ctx)
        else:
            self.run([fx], ctx.sub(target=target))

    def attack_bonus(self, c, fx, ctx):
        at = ctx.attack
        if "bonus" in fx:
            b = fx["bonus"]
            if isinstance(b, dict) and "ability_mod.str" in str(b) and at.get("ability") != "str":
                self.log.call("expr", "attack.bonus", "DATA_GAP", ctx.ref,
                              "bonus hard-codes Str; attack_ability modifiers (Martial Arts, Finesse) cannot apply")
            return int(self.ev(b, c, ctx))
        if at["type"].endswith("spell"):
            return int(self.var(c, "spell_attack_bonus", ctx))
        prof = 0
        if at.get("weapon"):
            w = self.cat.get(at["weapon"])["data"]
            if w["category"] in c.prof["weapon"] or slug(at["weapon"]) in c.prof["weapon"]:
                prof = c.pb
        elif at.get("via") == "unarmed_strike":
            prof = c.pb
        return c.mod(at["ability"]) + prof

    def resolve_attack(self, c, t, fx, ctx):
        ctx = ctx.sub(target=t)
        if ctx.attack is not None and "ability_modifier_to_damage" in fx:
            ctx.attack = dict(ctx.attack, ability_modifier_to_damage=fx["ability_modifier_to_damage"])
            self.log.call("op", "attack.ability_modifier_to_damage", "OK", ctx.ref, fx["ability_modifier_to_damage"])
        if ctx.attack is None:
            spell = fx["attack_type"].endswith("spell")
            ctx.attack = {"type": fx["attack_type"], "via": "spell" if spell else "natural",
                          "range": "ranged" if "ranged" in fx["attack_type"] else "melee",
                          "explicit": "bonus" in fx,
                          "damage_type": next((d.get("damage_type") for d in fx.get("on_hit", []) if d["op"] == "damage"), None),
                          "ability": self.spell_ability(c, ctx) if spell else "str"}
            if ctx.flags.get("feature"):
                ctx.attack["feature"] = ctx.flags["feature"]
            feet = ((fx.get("target") or {}).get("range") or {}).get("feet")
            if feet:
                ctx.attack["normal_feet"] = ctx.attack["long_feet"] = feet
        self.log.call("op", "attack", "OK", ctx.ref, fx["attack_type"])
        self.emit("attack_roll_made", c, ctx)
        if self.has_rage(c) and t.side != c.side:
            self.extend_rage(c)
        c.turn["attacks"] = c.turn.get("attacks", 0) + 1
        roll = f'attack_roll.{ctx.attack["range"]}'
        sub = ctx.sub(roll=roll)
        if self.auto_result(c, roll, sub) == "miss":
            self.log.say(f"{c} cannot attack {t}: out of range")
            return False
        mode = self.roll_mode(c, roll, sub, against=t)
        nat = self.d20(mode)
        self.used_up(t, "targeted_by_attack_roll", sub.flags.get("used_temps", []))
        bonus = self.attack_bonus(c, fx, ctx)
        total = nat + self.stat(c, roll, sub, bonus)
        crit_min = self.stat(c, "critical_hit_min_d20", sub, 20)
        ac = self.ac(t, ctx.sub(actor=c, target=t))
        hit = nat != 1 and (nat >= crit_min or total >= ac)
        crit = nat >= crit_min
        if hit and not crit:
            # The target may react to being hit (Shield spell, Deflect Attacks).
            self.emit("hit_by_attack_roll", t, ctx)
            self.policy.react_to_hit(self, t, c, ctx, total)
            ac = self.ac(t, ctx.sub(actor=c, target=t))
            hit = total >= ac
        if hit and self.auto_result(c, roll, sub.sub(actor=c, target=t), against=t) == "critical_hit":
            crit = True
        self.log.say(f"{c} attacks {t} ({mode}): {nat}+{total - nat}={total} vs AC {ac} -> "
                     f"{'CRIT' if hit and crit else 'hit' if hit else 'miss'}")
        if not hit:
            self.run(fx.get("on_miss"), ctx)
            if ctx.spell and ctx.spell.get("cantrip"):
                self.emit("cantrip_misses_or_saved", c, ctx.sub(damage_amount=self.preview_damage(fx.get("on_hit"), ctx)))
            return False
        if crit:
            self.log.call("rule", "critical-hits#critical_damage", "OK", "dnd5e/rule/critical-hits")
        hctx = ctx.sub(crit=crit and hit)
        self.emit("hits_with_attack_roll", c, hctx)
        self.run(fx.get("on_hit"), hctx)
        if crit:
            self.run(fx.get("on_critical"), hctx)
        return True

    def has_rage(self, c):
        return any(slug(t["ref"]) == "barbarian-rage" for t in c.temps)

    def preview_damage(self, effects, ctx):
        for d in effects or []:
            if d["op"] == "damage":
                return int(self.ev(d["amount"], ctx.actor, ctx))
        return 0

    def damage_amount(self, c, fx, ctx):
        amount = fx["amount"]
        at = ctx.attack or {}
        best_of = ctx.flags.get("damage_best_of", 1) if at.get("via") == "weapon" else 1
        # Martial Arts die: replaces a smaller weapon/unarmed die.
        for ref, m, t, sub in self.modifiers(c, "weapon_damage_die", ctx):
            die = self.ex.dice_of(m["value"], self.resolver(c, sub), ref)
            amount = self.bigger_die(amount, die, ctx)
        val = self.ev(amount, c, ctx, crit=ctx.crit and fx.get("critical", True), best_of=best_of)
        weaponish = at.get("via") in ("weapon",) and not at.get("explicit")
        if weaponish:
            rule = self.cat.rule("dnd5e/rule/damage-rolls", "ability_modifier")
            mode = at.get("ability_modifier_to_damage", "add")
            if rule and rule.get("weapon_attack") == "add_attack_ability_modifier":
                self.log.call("rule", "damage-rolls#ability_modifier", "OK", "dnd5e/rule/damage-rolls", mode)
                m = c.mod(at["ability"])
                val += m if mode == "add" or (mode == "negative_only" and m < 0) else 0
        if at and fx is not None and not fx.get("_extra"):
            val = self.stat(c, "damage_roll", ctx.sub(roll="damage_roll"), val)
        if fx.get("_half"):
            val //= 2
        return max(0, int(val))

    def bigger_die(self, amount, die, ctx):
        """Swap the leading die of a damage expression for `die` when that is larger."""
        def avg(d):
            m = DICE.match(d)
            return int(m.group(1) or 1) * (int(m.group(2)) + 1) / 2
        if not die:
            return amount
        if isinstance(amount, str) and DICE.match(amount):
            return die if avg(die) > avg(amount) else amount
        if isinstance(amount, dict) and amount.get("op") == "add":
            head = amount["args"][0]
            if isinstance(head, (int, str)) and (isinstance(head, int) or DICE.match(head)):
                cur = head if isinstance(head, str) else f"{head}d1"
                if avg(die) > avg(cur):
                    self.log.call("stat", "weapon_damage_die", "OK", ctx.ref)
                    return dict(amount, args=[die] + amount["args"][1:])
        return amount

    def deal_damage(self, c, t, fx, ctx):
        dtype = fx["damage_type"]
        if isinstance(dtype, dict):
            if "var" in dtype:
                dtype = self.var(c, dtype["var"], ctx)
            else:
                dtype = self.policy.damage_type(self, c, dtype["choose_from"], t)
        amt = self.damage_amount(c, fx, ctx)
        self.log.call("op", "damage", "OK", ctx.ref, dtype)
        self.apply_damage(t, amt, dtype, ctx.sub(target=t), source=c)

    def apply_damage(self, t, amt, dtype, ctx, source=None):
        for ref, fx, tmp in t.passives("defense"):
            if dtype not in fx.get("damage_types", []):
                continue
            if not self.holds(fx.get("when"), t, ctx.sub(ref=ref)):
                continue
            self.log.call("op", "defense", "OK", ref, f'{fx["kind"]} {dtype}')
            if fx["kind"] == "immunity":
                amt = 0
            elif fx["kind"] == "resistance":
                amt //= 2
            elif fx["kind"] == "vulnerability":
                amt *= 2
        for o, fx, ref in list(ctx.scoped):
            if o is t and fx["op"] == "modifier" and fx["stat"] == "damage_taken":
                amt = max(0, amt + int(self.ev(fx["value"], t, ctx)))
                self.log.call("op", "modifier", "OK", ref, "damage_taken")
        ctx.flags["damage_after_reduction"] = amt
        if amt <= 0:
            self.log.say(f"{t} takes no damage")
            return
        if t.temp_hp:
            soak = min(t.temp_hp, amt)
            t.temp_hp -= soak
            amt -= soak
        was = t.hp
        t.hp = max(0, t.hp - amt)
        self.log.say(f"{t} takes {amt} {dtype} ({t.hp}/{self.hp_max(t)})")
        self.damage_events(t, ctx)
        self.emit("damage_taken", t, ctx.sub(damage_amount=amt))
        if was == 0 and t.kind == "pc" and not t.dead:
            self.death_save_failure(t, 2 if ctx.crit else 1, amt, ctx)
            return
        if t.hp == 0 and was > 0:
            self.drop_to_zero(t, amt - was, ctx)

    def drop_to_zero(self, t, overflow, ctx):
        rules = {r["id"]: r for r in self.cat.get("dnd5e/rule/dropping-to-0-hit-points")["data"]["rules"]}
        self.log.call("rule", "dropping-to-0-hit-points", "OK", "dnd5e/rule/dropping-to-0-hit-points")
        if self.holds(rules["monster_death"]["when"], t, ctx):
            t.dead = True
            self.log.say(f"{t} dies")
            self.emit("dies", t, ctx)
            return
        if overflow >= self.hp_max(t):
            t.dead = True
            self.log.say(f"{t} dies (massive damage)")
            return
        t.drops += 1
        self.emit("drops_to_0_hp", t, ctx)
        self.end_concentration(t, ctx)

    def death_save_failure(self, t, n, amt, ctx):
        if amt >= self.hp_max(t):
            t.dead = True
        t.death[1] += n
        t.stable = False
        if t.death[1] >= 3:
            t.dead = True
        self.log.say(f"{t} death save failures {t.death[1]}" + (" - dies" if t.dead else ""))

    def death_save(self, t):
        r = self.cat.rule("dnd5e/rule/dropping-to-0-hit-points", "death_saves")
        self.log.call("rule", "dropping-to-0-hit-points#death_saves", "OK", "dnd5e/rule/dropping-to-0-hit-points")
        nat = self.rng.randint(1, 20)
        if nat == 20:
            self.heal(t, 1, Ctx(t, ref="death_save"))
            return
        if nat == 1:
            t.death[1] += 2
        elif nat >= r["success_at_least"]:
            t.death[0] += 1
        else:
            t.death[1] += 1
        if t.death[1] >= 3:
            t.dead = True
        elif t.death[0] >= 3:
            t.stable = True
        self.log.say(f"{t} death save {nat}: {t.death[0]} ok / {t.death[1]} fail" + (" - dies" if t.dead else ""))

    # =========================================================================================
    # spells
    # =========================================================================================
    def cast(self, c, sref, slot, targets, ctx=None, ability=None):
        sp = self.cat.get(sref)
        lvl = sp["facets"]["level"]
        known = c.cantrips if lvl == 0 else c.prepared + c.always
        if sref not in known:
            self.log.call("spell", "not_prepared", "OK", sref, f"{c} cannot cast it (not known/prepared)")
            return False
        cost = sp["data"]["casting_time"].get("cost", "action")
        if cost in ("action", "bonus_action") and not c.economy.get(cost):
            return False
        if cost == "reaction" and not c.economy.get("reaction"):
            return False
        if self.restricted(c, "cast_spells"):
            return False
        if sp["data"]["components"].get("verbal") and self.restricted(c, "speak"):
            return False
        if lvl > 0:
            s = c.slots.get(str(slot))
            if not s or s[0] <= 0:
                return False
            s[0] -= 1
            self.log.call("resource", "spell_slot", "OK", sref, f"level {slot}")
        if cost in c.economy:
            c.economy[cost] = 0
        self.log.call("op", "cast", "OK", sref)
        self.log.say(f"{c} casts {sp['name']}" + (f" (slot {slot})" if lvl else ""))
        ctx = (ctx or Ctx(c)).sub(actor=c, ref=sref, target=targets[0] if targets else None,
                                  spell={"ref": sref, "slot": slot if lvl else 0, "level": lvl,
                                         "ability": ability or c.spell_ability, "cantrip": lvl == 0},
                                  flags={"targets": targets})
        dur = sp["data"].get("duration", {})
        if dur.get("concentration"):
            self.emit("concentration_effect_started", c, ctx)
            c.concentration = {"ref": sref, "temps": []}
        # Spell-wide rules: auto results that apply to the spell's own saves (Sleep vs elves).
        for fx in sp["effects"]:
            if fx["op"] == "auto_result" and not fx.get("target"):
                ctx.scoped.append((None, fx, sref))
        for fx in sp["effects"]:
            if fx["op"] == "auto_result" and not fx.get("target"):
                continue
            if fx["op"] == "activation":
                continue
            self.run_one(fx, ctx)
        if lvl > 0:
            self.emit("casts_spell", c, ctx)
        return True

    # =========================================================================================
    # turns
    # =========================================================================================
    def start_turn(self, c):
        self.current = c
        c.turn = {"attacks": 0}
        for e in self.cat.system["action_economy"]:
            if e["id"] in ("action", "bonus_action", "reaction"):
                c.economy[e["id"]] = e.get("count", 1)
        c.economy["movement"] = self.speed(c, "walk", Ctx(c))
        self.reset_uses(c, "turn")
        self.expire("turn_start", c)
        self.emit("turn_start", c, Ctx(c))
        if not c.dead and c.hp == 0 and c.kind == "pc" and not c.stable:
            self.death_save(c)

    def end_turn(self, c):
        self.emit("turn_end", c, Ctx(c))
        rage = next((t for t in c.temps if slug(t["ref"]) == "barbarian-rage"), None)
        if rage is not None:
            r = self.cat.rule("dnd5e/feature/barbarian-rage", "duration")
            if r and not rage.get("extended") and rage.get("created_round") != self.round:
                c.temps.remove(rage)
                self.log.say(f"{c}'s Rage ends")
            rage["extended"] = False
            self.log.call("rule", "barbarian-rage#duration", "OK", "dnd5e/feature/barbarian-rage")
        self.expire("turn_end", c)
        self.current = None

    def initiative(self, c):
        ctx = Ctx(c, ref="initiative", roll="initiative")
        mode = self.roll_mode(c, "initiative", ctx)
        bonus = c.monster["data"]["initiative"]["modifier"] if c.monster else c.mod("dex")
        if c.monster:
            self.log.call("stat", "initiative", "OK", c.monster["ref"], "stat block modifier")
        return self.d20(mode) + self.stat(c, "initiative", ctx, bonus)
