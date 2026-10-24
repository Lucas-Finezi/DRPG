"""Simulation: four level-2 adventurers against six Goblin Warriors, then advancement to level 3.

Party: Wizard (Elf, Sage), Cleric (Dwarf, Acolyte), Barbarian (Goliath, Soldier), Monk (Human,
Criminal), built only from catalog entries (standard array, background increases, class and
species features). After the fight: XP, Short Rest, level 3 (subclasses, spells, features),
Long Rest, and a second fight against six more goblins that exercises the level 3 calls.

Usage:
  python3 -I -m tools.engine.simulate_goblins            # narrated seed + 200-seed batch
  python3 -I -m tools.engine.simulate_goblins --seed 7 --runs 50
Writes reports/simulation/goblins.json and docs/simulacao-goblins.md (tables only; prose is
written by hand around them).
"""
import argparse
import json
import random
from pathlib import Path

from .builder import Builder
from .calllog import STATUSES, CallLog
from .catalog import ROOT, Catalog
from .engine import Ctx, Engine, slug

S = "dnd5e/spell/"
W = "dnd5e/weapon/"
F = "dnd5e/feature/"

# Notes audited (on the paths this simulation executes) as carrying a mechanic: (ref, op) ->
# (field that structures it, what the note says). Field None = the note itself is the gap.
NOTE_MECHANICS = {
    ("dnd5e/weapon-mastery/cleave", "attack"): (
        "ability_modifier_to_damage", "the extra attack adds no ability modifier unless negative"),
    ("dnd5e/feature/wizard-arcane-recovery", "restore"): ("max_level", "no slot of level 6 or higher"),
    ("dnd5e/spell/guiding-bolt", "roll_mode"): ("duration.ends_on", "only the next attack roll against the target"),
    ("dnd5e/weapon-mastery/vex", "roll_mode"): ("when", "only the attacker's next roll, only against that creature"),
    ("dnd5e/spell/sleep", "save"): (None, "the second save happens at the end of the target's next turn"),
}

PARTY = {
    "Wizard": dict(
        cls="wizard", species="elf", background="sage", x=-10,
        picks={
            "background_increase": ("int", "con"),
            "skills": {"dnd5e/class/wizard": ["investigation", "insight"], F + "elf-keen-senses": ["perception"],
                       F + "wizard-scholar": ["arcana"]},
            "choice": {(F + "elf-elven-lineage", "lineage"): "high_elf",
                       (F + "elf-elven-lineage", "spellcasting_ability"): "int",
                       ("dnd5e/feat/magic-initiate", "spell_list"): "wizard",
                       ("dnd5e/feat/magic-initiate", "spellcasting_ability"): "int"},
            "origin_spells": {"dnd5e/feat/magic-initiate": [S + "light", S + "minor-illusion", S + "false-life"]},
            "cantrips": [S + "fire-bolt", S + "ray-of-frost", S + "mage-hand"],
            "spellbook": [S + "magic-missile", S + "shield", S + "sleep", S + "thunderwave", S + "mage-armor",
                          S + "detect-magic", S + "feather-fall", S + "burning-hands",
                          S + "shatter", S + "misty-step"],
            "prepared": [S + "magic-missile", S + "shield", S + "sleep", S + "mage-armor", S + "thunderwave",
                         S + "scorching-ray"],
            "free_spells": {F + "evoker-evocation-savant": [S + "scorching-ray", S + "flaming-sphere"]},
            "grant": {F + "wizard-wizard-subclass": "dnd5e/subclass/evoker"},
            "equip": {W + "quarterstaff": "wielded"},
        }),
    "Cleric": dict(
        cls="cleric", species="dwarf", background="acolyte", x=-10,
        picks={
            "background_increase": ("wis", "cha"),
            "skills": {"dnd5e/class/cleric": ["medicine", "persuasion"]},
            "choice": {(F + "cleric-divine-order", "divine_order"): "thaumaturge",
                       ("dnd5e/feat/magic-initiate", "spell_list"): "cleric",
                       ("dnd5e/feat/magic-initiate", "spellcasting_ability"): "wis"},
            "origin_spells": {"dnd5e/feat/magic-initiate": [S + "light", S + "resistance", S + "sanctuary"]},
            "cantrips": [S + "sacred-flame", S + "guidance", S + "thaumaturgy", S + "spare-the-dying"],
            "prepared": [S + "bless", S + "healing-word", S + "guiding-bolt", S + "cure-wounds", S + "shield-of-faith",
                         S + "spiritual-weapon", S + "command", S + "bane"],
            "grant": {F + "cleric-cleric-subclass": "dnd5e/subclass/life-domain"},
            "equip": {"dnd5e/armor/chain-shirt": "worn", "dnd5e/armor/shield": "wielded", W + "mace": "wielded",
                      "dnd5e/gear/holy-symbol": "held"},
        }),
    "Barbarian": dict(
        cls="barbarian", species="goliath", background="soldier", x=0,
        picks={
            "background_increase": ("str", "con"),
            "skills": {"dnd5e/class/barbarian": ["perception", "survival"], F + "barbarian-primal-knowledge": ["nature"]},
            "choice": {(F + "goliath-giant-ancestry", 1): "fires_burn"},
            "masteries": ["greataxe", "handaxe"],
            "grant": {F + "barbarian-barbarian-subclass": "dnd5e/subclass/path-of-the-berserker"},
            "equip": {W + "greataxe": "wielded"},
        }),
    "Monk": dict(
        cls="monk", species="human", background="criminal", x=0,
        picks={
            "background_increase": ("dex", "con"),
            "skills": {"dnd5e/class/monk": ["acrobatics", "athletics"], F + "human-skillful": ["perception"],
                       "dnd5e/feat/skilled": ["insight", "history", "religion"]},
            "choice": {("dnd5e/feat/skilled", "skilled"): ["skill", "skill", "skill"]},
            "grant": {F + "human-versatile": "dnd5e/feat/skilled",
                      F + "monk-monk-subclass": "dnd5e/subclass/warrior-of-the-open-hand"},
            "equip": {W + "spear": "wielded"},
        }),
}


class Policy:
    """Tactical decisions. Only decisions: every rule outcome comes from the engine."""

    def __init__(self, rng):
        self.rng = rng

    # -- hooks the engine calls ------------------------------------------------------------------
    def choose(self, eng, c, fx, ctx):
        cid = fx.get("id")
        ids = [o["id"] for o in fx["options"]]
        prefs = {"unarmed_strike": "damage", "technique": "topple", "divine_spark_mode": "heal",
                 "finesse_ability": max(("str", "dex"), key=c.mod)}
        if cid in prefs and prefs[cid] in ids:
            return prefs[cid]
        if ctx.flags.get("nimble") and "disengage" in ids:
            return "disengage"
        return ids[0]

    def use_trigger(self, eng, c, ref, fx, ctx):
        name = slug(ref)
        if name == "cleave":
            first = ctx.target
            others = [o for o in eng.creatures if o.up and o.side != c.side and o is not first
                      and abs(o.x - first.x) <= 5 and abs(o.x - c.x) <= 5]
            if not others:
                return False
            ctx.target = others[0]
            ctx.attack = dict(ctx.attack)
            return True
        if name in ("wizard-arcane-recovery",):
            return any(s[0] < s[1] for s in c.slots.values())
        if name == "monk-uncanny-metabolism":
            return c.hp < eng.hp_max(c) // 2 or c.resources["focus_points"]["cur"] == 0
        if name == "alert":
            return False
        if name == "goliath-giant-ancestry":
            return c.resources["giant_ancestry"]["cur"] > 0
        return True

    def react_to_hit(self, eng, t, attacker, ctx, total):
        if S + "shield" in t.prepared and t.economy.get("reaction") and t.slots.get("1", [0])[0] > 0:
            if total < eng.ac(t, ctx) + 5:
                eng.cast(t, S + "shield", 1, [t])

    def damage_type(self, eng, c, options, t):
        return options[0]

    def area_targets(self, eng, c, fx, ctx):
        area = fx["target"]["area"]
        foes = [o for o in eng.creatures if o.alive and o.side != c.side]
        if area["origin"] == "self":
            size = area["size_feet"]
            return [o for o in foes if abs(o.x - c.x) <= size] + (
                [o for o in eng.creatures if o.side == c.side and o is not c and abs(o.x - c.x) <= size]
                if area["shape"] == "emanation" else [])
        point = ctx.flags.get("point", foes[0].x if foes else c.x)
        return [o for o in eng.creatures if o.alive and abs(o.x - point) <= area["size_feet"]
                and (o.side != c.side or area["shape"] != "sphere" or True)]

    # -- turns -----------------------------------------------------------------------------------
    def foes(self, eng, c):
        return [o for o in eng.creatures if o.up and o.side != c.side]

    def nearest(self, eng, c, pool=None):
        pool = pool if pool is not None else self.foes(eng, c)
        return min(pool, key=lambda o: (abs(o.x - c.x), o.hp)) if pool else None

    def approach(self, eng, c, target, stop=5):
        d = abs(target.x - c.x)
        step = min(c.economy.get("movement", 0), max(0, d - stop))
        c.x += step if target.x > c.x else -step
        c.economy["movement"] -= step
        if step:
            eng.log.call("action_economy", "movement", "OK", "system.json#action_economy")

    def use_action(self, eng, c, aref):
        fx = next(x for x in eng.cat.get(aref)["effects"] if x["op"] == "activation")
        if not c.economy.get(fx["cost"]):
            return False
        c.economy[fx["cost"]] = 0
        eng.log.call("op", "activation", "OK", aref, fx.get("name"))
        return True

    def activation(self, eng, c, ref, name=None, ident=None):
        for r, fx in eng.activations(c):
            if r == ref and (name is None or fx.get("name") == name) and (ident is None or fx.get("id") == ident):
                return fx
        return None

    def turn(self, eng, c):
        if not eng.can_act(c):
            eng.log.say(f"{c} cannot act")
            return
        prone = "dnd5e/condition/prone"
        if prone in c.conditions:
            stand = self.activation(eng, c, prone, name="Right yourself")
            cost = int(eng.ev(stand["movement_cost"], c, Ctx(c, ref=prone))) if stand else None
            if stand and c.economy.get("movement", 0) >= cost and eng.activate(c, prone, stand, c):
                c.economy["movement"] -= cost
        getattr(self, "turn_" + (c.name.lower() if c.kind == "pc" else "goblin"))(eng, c)

    def turn_barbarian(self, eng, c):
        rage = self.activation(eng, c, F + "barbarian-rage", ident="enter_rage")
        if rage and not eng.has_rage(c) and self.foes(eng, c):
            eng.activate(c, F + "barbarian-rage", rage, c)
        t = self.nearest(eng, c)
        if not t:
            return
        self.approach(eng, c, t)
        if abs(t.x - c.x) <= 5 and self.use_action(eng, c, "dnd5e/action/attack"):
            eng.weapon_attack(c, W + "greataxe", t)
        elif self.use_action(eng, c, "dnd5e/action/attack"):
            eng.weapon_attack(c, W + "handaxe", t, Ctx(c, flags={"thrown": True}))

    def turn_monk(self, eng, c):
        t = self.nearest(eng, c)
        if not t:
            return
        self.approach(eng, c, t)
        if abs(t.x - c.x) > 5:
            return
        if self.use_action(eng, c, "dnd5e/action/attack"):
            eng.weapon_attack(c, W + "spear", t)
        t = self.nearest(eng, c)
        if not t or abs(t.x - c.x) > 5:
            return
        flurry = self.activation(eng, c, F + "monk-monks-focus", name="Flurry of Blows")
        if flurry and eng.activate(c, F + "monk-monks-focus", flurry, t):
            return
        ma = self.activation(eng, c, F + "monk-martial-arts", name="Bonus Unarmed Strike")
        if ma:
            eng.activate(c, F + "monk-martial-arts", ma, t)

    def turn_wizard(self, eng, c):
        foes = self.foes(eng, c)
        if not foes:
            return
        near = self.nearest(eng, c)
        # Keep 20+ feet from the nearest foe, but stay within 60 feet of the farthest group.
        far = max(foes, key=lambda o: o.x)
        if abs(far.x - c.x) > 60 and abs(near.x - c.x) > 25:
            self.approach(eng, c, far, stop=max(60, abs(near.x - c.x) - 20 if False else 60))
        cluster = max(foes, key=lambda o: sum(1 for p in foes if abs(p.x - o.x) <= 5 and not p.conditions))
        n_cluster = sum(1 for p in foes if abs(p.x - cluster.x) <= 5 and not p.conditions)
        slots = c.slots
        if n_cluster >= 3 and abs(cluster.x - c.x) <= 60 and S + "sleep" in c.prepared and slots["1"][0] > 1:
            if eng.cast(c, S + "sleep", 1, [], Ctx(c, flags={"point": cluster.x})):
                return
        if "2" in slots and slots["2"][0] and S + "scorching-ray" in c.prepared:
            targets = sorted(foes, key=lambda o: o.hp)[:3]
            if eng.cast(c, S + "scorching-ray", 2, (targets * 3)[:3]):
                return
        close = [o for o in foes if abs(o.x - c.x) <= 15]
        if len(close) >= 2 and slots["1"][0] > 1 and S + "thunderwave" in c.prepared:
            if eng.cast(c, S + "thunderwave", 1, close):
                return
        wounded = [o for o in foes if o.hp <= 7]
        if wounded and slots["1"][0] > 1:
            if eng.cast(c, S + "magic-missile", 1, (sorted(wounded, key=lambda o: o.hp) * 3)[:3]):
                return
        t = min(foes, key=lambda o: o.hp)
        eng.cast(c, S + "fire-bolt", 0, [t])

    def turn_cleric(self, eng, c):
        party = [o for o in eng.creatures if o.side == c.side and not o.dead]
        down = [o for o in party if o.hp == 0]
        hurt = sorted([o for o in party if o.hp <= eng.hp_max(o) // 3], key=lambda o: o.hp)
        if (down or hurt) and c.economy.get("bonus_action") and c.slots.get("1", [0])[0]:
            eng.cast(c, S + "healing-word", 1, [(down or hurt)[0]])
        foes = self.foes(eng, c)
        if not foes:
            return
        if self.round_of(eng) == 1 and c.concentration is None and S + "bless" in c.prepared + c.always:
            allies = sorted([o for o in party if o is not c], key=lambda o: abs(o.x))[:3]
            if eng.cast(c, S + "bless", 1, allies):
                return
        spark = self.activation(eng, c, F + "cleric-channel-divinity", name="Divine Spark")
        if hurt and spark and eng.activate(c, F + "cleric-channel-divinity", spark, hurt[0]):
            return
        if "2" in c.slots and c.slots["2"][0] and S + "spiritual-weapon" in c.prepared and c.concentration is None:
            if eng.cast(c, S + "spiritual-weapon", 2, [self.nearest(eng, c)]):
                return
        t = max(foes, key=lambda o: o.hp)
        if c.slots.get("1", [0])[0] > 1 and abs(t.x - c.x) <= 120:
            if eng.cast(c, S + "guiding-bolt", 1, [t]):
                return
        t = min([o for o in foes if abs(o.x - c.x) <= 60] or foes, key=lambda o: o.hp)
        eng.cast(c, S + "sacred-flame", 0, [t])

    def turn_goblin(self, eng, c):
        foes = self.foes(eng, c)
        if not foes:
            return
        acts = {fx.get("name"): fx for r, fx in eng.activations(c) if r == c.monster["ref"]}
        if c.role == "melee":
            t = self.nearest(eng, c)
            self.approach(eng, c, t)
            if abs(t.x - c.x) <= 5:
                eng.activate(c, c.monster["ref"], acts["Scimitar"], t)
            return
        adjacent = [o for o in foes if abs(o.x - c.x) <= 5]
        if adjacent:
            nimble = next((fx for r, fx in eng.activations(c) if fx.get("cost") == "bonus_action"), None)
            if nimble:
                eng.activate(c, c.monster["ref"], nimble, c, Ctx(c, flags={"nimble": True}))
                c.x += min(c.economy.get("movement", 0), 30) * (1 if c.x >= adjacent[0].x else -1)
        back = [o for o in foes if o.name in ("Wizard", "Cleric")] or foes
        t = min(back, key=lambda o: abs(o.x - c.x))
        eng.activate(c, c.monster["ref"], acts["Shortbow"], t)

    def round_of(self, eng):
        return eng.round


def build_party(eng, b):
    party = []
    for name, spec in PARTY.items():
        c = b.character(name, spec["cls"], spec["species"], spec["background"], spec["picks"])
        c.masteries = spec["picks"].get("masteries", [])
        c.x = spec["x"]
        b.level_up(c, spec["cls"])        # level 1 -> 2 through the same advancement procedure
        c.hp = eng.hp_max(c)
        c.xp = eng.cat.system["levels"]["advancement"][1]["xp"]
        party.append(c)
    return party


def goblins(eng, b, prefix, x_melee=50, x_ranged=65):
    out = []
    for i in range(6):
        g = b.monster("dnd5e/creature/goblin-warrior", f"{prefix}{i + 1}", x_melee if i < 3 else x_ranged)
        g.role = "melee" if i < 3 else "ranged"
        out.append(g)
    return out


def encounter(eng, policy, party, foes, max_rounds=20):
    eng.creatures = party + foes
    eng.round = 0
    for c in eng.creatures:
        c.economy = {"reaction": 1}
        c.drops = 0
    # Initiative: each PC rolls; identical monsters share one roll (system initiative.groups).
    groups = eng.cat.system["initiative"]["rules"]
    single = next(r for r in groups if r["id"] == "initiative.groups")["data"]["identical_creatures"] == "single_roll"
    eng.log.call("rule", "initiative.groups", "OK", "system.json#initiative")
    order = []
    shared = eng.initiative(foes[0]) if single else None
    for c in eng.creatures:
        order.append((shared if c.kind == "monster" and single else eng.initiative(c), c.mod("dex"), c))
    order.sort(key=lambda r: (-r[0], -r[1]))
    eng.log.say("initiative: " + ", ".join(f"{c}({i})" for i, _, c in order))
    for c in eng.creatures:
        eng.emit("initiative_rolled", c, Ctx(c))
    while eng.round < max_rounds:
        eng.round += 1
        eng.log.say(f"--- round {eng.round}")
        for _, _, c in order:
            if c.dead:
                continue
            eng.start_turn(c)
            if c.up:
                policy.turn(eng, c)
            eng.end_turn(c)
            if not any(o.up for o in foes) or not any(o.up for o in party):
                return outcome(eng, party, foes)
        eng.emit("round_end", order[0][2], Ctx(order[0][2]))
    return outcome(eng, party, foes)


def outcome(eng, party, foes):
    return {"rounds": eng.round, "party_won": any(o.up for o in party) and not any(o.up for o in foes),
            "party": {c.name: {"hp": c.hp, "hp_max": eng.hp_max(c), "dead": c.dead, "drops": c.drops,
                               "slots": {k: v[0] for k, v in c.slots.items()},
                               "resources": {k: v["cur"] for k, v in c.resources.items()}} for c in party},
            "foes_down": sum(1 for f in foes if not f.up)}


def short_rest(eng, party):
    sr = eng.cat.get("dnd5e/rule/short-rest")
    spend = next(fx for fx in sr["effects"] if fx["op"] == "activation")
    for c in party:
        if c.dead:
            continue
        if c.hp == 0:
            c.hp = 1     # Stable creatures regain 1 HP after 1d4 hours (rule/dropping-to-0-hit-points)
        cls = next(iter(c.hit_dice))
        hd = c.hit_dice[cls]
        while c.hp < eng.hp_max(c) * 0.6 and hd[0] > 0:
            hd[0] -= 1
            ctx = Ctx(c, ref="dnd5e/rule/short-rest")
            die = int(hd[2][1:])
            ctx_roll = eng.rng.randint(1, die)
            amt = int(eng.ex.ev(spend["then"][0]["amount"], lambda n: ctx_roll if n == "hit_point_die" else eng.var(c, n, ctx)))
            eng.log.call("op", "activation", "OK", "dnd5e/rule/short-rest", "Spend a Hit Point Die")
            eng.heal(c, amt, ctx)
        eng.recover(c, "short_rest_finished")
        eng.emit("short_rest_finished", c, Ctx(c))
        eng.reset_uses(c, "short_rest")


def long_rest(eng, party):
    for c in party:
        if c.dead:
            continue
        c.temps = []
        c.conditions = {}
        c.concentration = None
        eng.emit("long_rest_finished", c, Ctx(c))
        eng.recover(c, "long_rest_finished")
        eng.reset_uses(c, "long_rest")
        eng.reset_uses(c, "day")
        c.hp = eng.hp_max(c)


def run(seed, narrate=True, log=None, catalog=None):
    rng = random.Random(seed)
    log = log or CallLog()
    eng = Engine(rng, catalog or Catalog(), log)
    pol = Policy(rng)
    eng.policy = pol
    eng.note_mechanics = NOTE_MECHANICS
    b = Builder(eng)
    result = {"seed": seed}

    log.phase = "1-build-level-2"
    party = build_party(eng, b)
    eng.creatures = party
    wiz = party[0]
    wiz.economy = {"action": 1}
    eng.cast(wiz, S + "mage-armor", 1, [wiz])   # before the adventure: 8 hours
    wiz.economy = {}
    wiz.slots["1"][0] = wiz.slots["1"][1]       # the slot is regained on the Long Rest before setting out
    result["party_level_2"] = sheet(eng, party)

    log.phase = "2-combat-level-2"
    foes = goblins(eng, b, "Goblin ")
    result["combat_1"] = encounter(eng, pol, party, foes)

    log.phase = "3-xp-rest"
    xp = sum(f.xp for f in foes if not f.up)
    share = xp // len(party)
    for c in party:
        c.xp += share
    need = next(a["xp"] for a in eng.cat.system["levels"]["advancement"] if a["level"] == 3)
    log.call("data", "levels.advancement", "OK", "system.json#levels")
    log.call("procedure", "level_3_by_xp", "GM", "system.json#levels",
             f"{party[0].xp} XP < {need}: level 3 granted by GM decision (exercise premise)")
    result["xp"] = {"encounter_xp": xp, "each": share, "total_each": party[0].xp, "needed_for_3": need}
    short_rest(eng, party)

    log.phase = "4-level-3"
    for c in party:
        if not c.dead:
            b.level_up(c, PARTY[c.name]["cls"])
    long_rest(eng, party)
    wiz.economy = {"action": 1}
    eng.cast(wiz, S + "mage-armor", 1, [wiz])   # recast after the Long Rest (8 hours)
    result["party_level_3"] = sheet(eng, party)

    log.phase = "5-combat-level-3"
    for c, spec in zip(party, PARTY.values()):
        c.x = spec["x"]
    foes2 = goblins(eng, b, "Goblin B")
    result["combat_2"] = encounter(eng, pol, party, foes2)
    if narrate:
        result["narrative"] = log.events
    return result


def sheet(eng, party):
    out = {}
    for c in party:
        ctx = Ctx(c)
        out[c.name] = {
            "level": c.level, "classes": dict(c.class_levels), "subclasses": {k: slug(v) for k, v in c.subclasses.items()},
            "scores": dict(c.scores), "hp_max": eng.hp_max(c), "ac": eng.ac(c, ctx), "speed": eng.speed(c, "walk", ctx),
            "proficiency_bonus": c.pb, "slots": {k: v[1] for k, v in c.slots.items()},
            "resources": {k: v["max"] for k, v in c.resources.items()},
            "cantrips": [slug(s) for s in c.cantrips], "prepared": [slug(s) for s in c.prepared],
            "always_prepared": [slug(s) for s in c.always], "spellbook": [slug(s) for s in c.spellbook],
            "features": [slug(f) for f in c.features if "/feature/" in f or "/feat/" in f],
            "skills": sorted(c.prof["skill"]), "expertise": sorted(c.prof["expertise"]),
        }
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--runs", type=int, default=200)
    ap.add_argument("--out", default=str(ROOT / "reports" / "simulation" / "goblins.json"))
    ap.add_argument("--catalog", default=None, help="knowledge/dnd5e directory to read (default: this checkout)")
    a = ap.parse_args(argv)
    cat = Catalog(a.catalog) if a.catalog else Catalog()
    log = CallLog()
    story = run(a.seed, True, log, cat)
    batch_log = CallLog()
    stats = {"runs": a.runs, "combat_1_wins": 0, "combat_2_wins": 0, "rounds_1": 0, "rounds_2": 0,
             "deaths": 0, "pc_dropped_1": 0, "pc_dropped_2": 0}
    for s in range(a.runs):
        r = run(1000 + s, False, batch_log, cat)
        stats["combat_1_wins"] += r["combat_1"]["party_won"]
        stats["combat_2_wins"] += r["combat_2"]["party_won"]
        stats["rounds_1"] += r["combat_1"]["rounds"]
        stats["rounds_2"] += r["combat_2"]["rounds"]
        stats["deaths"] += sum(p["dead"] for p in r["combat_1"]["party"].values())
        stats["deaths"] += sum(p["dead"] for p in r["combat_2"]["party"].values())
        stats["pc_dropped_1"] += sum(p["drops"] for p in r["combat_1"]["party"].values())
        stats["pc_dropped_2"] += sum(p["drops"] for p in r["combat_2"]["party"].values())
    for k in ("rounds_1", "rounds_2"):
        stats[k] = round(stats[k] / max(1, a.runs), 2)
    calls = merge(log, batch_log)
    totals = {s: sum(r["count"] for r in calls if r["status"] == s) for s in STATUSES}
    out = {"seed_story": story, "batch": stats, "totals": totals, "calls": calls,
           "per_phase": log.summary()}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"batch": stats, "totals": totals}, indent=1))
    for r in calls:
        if r["status"] != "OK":
            print(f'{r["status"]:10} {r["kind"]:12} {r["name"]:40} {r["ref"] or "":50} {r["detail"] or ""}')
    return out


def merge(*logs):
    seen = {}
    for lg in logs:
        for r in lg.distinct():
            k = (r["kind"], r["name"], r["ref"], r["status"], r["detail"])
            if k in seen:
                seen[k]["count"] += r["count"]
                seen[k]["phases"] = sorted(set(seen[k]["phases"]) | set(r["phases"]))
            else:
                seen[k] = dict(r)
                seen[k].pop("phase", None)
    return sorted(seen.values(), key=lambda r: (STATUSES.index(r["status"]), r["kind"], r["name"]))


if __name__ == "__main__":
    main()
