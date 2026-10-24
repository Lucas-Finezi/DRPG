"""Campaign runner: a party plays a sequence of scenes (fights, traps, checks, rewards, rests,
travel with random encounters, milestones), gaining XP, treasure and levels.

The scenes come from a scenario module outside the knowledge base (simulations/<name>/).
Levels are gained when XP reaches the Character Advancement threshold (system.json), with the
Hit Die rolled; a scenario milestone can grant a level the XP did not reach (a GM decision,
logged as such).
"""
import random

from .builder import Builder
from .calllog import CallLog
from .catalog import Catalog
from .engine import Ctx, Engine, slug
from .party import auto_equip, picks_for, share_out, wealth
from .tactics import Tactics, cls_of


ROMAN = {2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X"}


class Campaign:
    def __init__(self, seed, roster, catalog=None, log=None):
        self.rng = random.Random(seed)
        self.log = log or CallLog()
        self.eng = Engine(self.rng, catalog or Catalog(), self.log)
        self.tactics = Tactics(self.rng)
        self.eng.policy = self.tactics
        self.b = Builder(self.eng)
        self.party = [self.make(spec) for spec in roster]
        self.record = {"scenes": [], "levels": [], "deaths": [], "loot": [], "rests": 0, "fights": 0,
                       "milestones": []}
        self.short_rests = 0
        self.graveyard = []
        self.scene_name = "start"

    # ==========================================================================================
    # characters
    # ==========================================================================================
    def make(self, spec):
        eng, b = self.eng, self.b
        self.log.phase = "build"
        picks = picks_for(eng, spec["cls"], spec["background"])
        c = b.character(spec["name"], spec["cls"], spec["species"], spec["background"], picks)
        c.spec = spec
        c.x = 0 if spec["cls"] in ("barbarian", "fighter", "paladin", "monk") else -10
        c.xp = 0
        self.after_level(c)
        c.hp = eng.hp_max(c)
        return c

    def after_level(self, c):
        """Weapon masteries, gear and resources after creation or a level."""
        eng = self.eng
        n = int(eng.stat(c, "weapon_mastery_kinds", Ctx(c), 0))
        if n:
            c.masteries = c.picks["chooser"].masteries(c, n)
            self.log.call("stat", "weapon_mastery_kinds", "OK", None, f"{n} masteries")
        auto_equip(eng, c, cls_of(c))
        eng.init_resources(c)

    def check_levels(self, reason="xp"):
        adv = self.eng.cat.system["levels"]["advancement"]
        for c in self.party:
            if c.dead:
                continue
            while c.level < 20:
                nxt = next(a for a in adv if a["level"] == c.level + 1)
                if c.xp < nxt["xp"]:
                    break
                self.level_up(c, f"{c.xp} XP >= {nxt['xp']}")

    def level_up(self, c, why):
        phase = self.log.phase
        self.log.phase = f"level-{c.level + 1}"
        gain = self.b.level_up(c, cls_of(c), roll=True)
        self.after_level(c)
        self.log.phase = phase
        self.record["levels"].append({"who": c.name, "level": c.level, "hp_gain": gain, "hp_max": self.eng.hp_max(c),
                                      "why": why, "scene": self.scene_name})
        self.log.say(f"*** {c} reaches level {c.level} ({why}); HP max {self.eng.hp_max(c)}")

    def milestone(self, level, why):
        for c in self.party:
            if c.dead:
                continue
            while c.level < level:
                self.log.call("procedure", "milestone_level", "GM", None, why)
                self.record["milestones"].append({"who": c.name, "to": c.level + 1, "xp": c.xp, "why": why})
                self.level_up(c, f"milestone: {why}")

    # ==========================================================================================
    # scenes
    # ==========================================================================================
    def run(self, scenes):
        for sc in scenes:
            if self.wiped():
                self.record["scenes"].append({"name": sc.get("name"), "skipped": "party defeated"})
                continue
            self.scene_name = sc.get("name", sc["type"])
            self.log.phase = sc.get("part", "campaign")
            getattr(self, "scene_" + sc["type"])(sc)
        return self.summary()

    def wiped(self):
        return not any(c.up for c in self.party) or all(c.dead for c in self.party)

    def award(self, sc, defeated=()):
        alive = [c for c in self.party if not c.dead]
        if not alive:
            return 0
        each = sc.get("xp_each", 0)
        split = sc.get("xp", 0)
        if sc.get("xp") == "monsters":
            split = sum(m.xp for m in defeated)
            self.log.call("data", "creature.cr.xp", "OK", None, "XP from the stat blocks")
        share = each + (split // len(alive) if split else 0)
        for c in alive:
            c.xp += share
        if share:
            self.log.say(f"XP: +{share} each ({self.scene_name})")
        self.check_levels()
        return share

    def scene_combat(self, sc):
        eng, t = self.eng, self.tactics
        foes = []
        x0 = sc.get("distance", 40)
        for g in sc["foes"]:
            for i in range(g.get("count", 1)):
                name = g.get("name") or eng.cat.get(g["ref"])["name"]
                if g.get("count", 1) > 1:
                    name = f"{name} {i + 1}"
                m = self.b.monster(g["ref"], name, x0 + g.get("x", 0) + (10 if g.get("role") == "ranged" else 0))
                m.behaviour = dict(g.get("behaviour") or {}, role=g.get("role", "melee"))
                if g.get("conditions"):
                    for cond in g["conditions"]:
                        m.conditions[cond] = {"source": m, "duration": {}, "implied_by": None,
                                              "created_turn_of": None, "created_round": 0}
                foes.append(m)
        for c in self.party:
            c.x = 0 if cls_of(c) in ("barbarian", "fighter", "paladin", "monk") else -10
            c.economy = {"reaction": 1}
            c.drops = 0
        t.encounter = {"boss": sc.get("boss", False), "round": 0}
        t.used_recharge = set()
        self.record["fights"] += 1
        res = self.encounter(foes, sc)
        tries = 1
        while not all(not f.up or f.behaviour.get("fled") for f in foes) and any(not c.dead for c in self.party) \
                and tries < 3:
            # Defeat: the book's consequence (knocked out, robbed, back after a rest) and a second attempt.
            self.log.call("procedure", "defeat_retry", "GM", None,
                          "party defeated: wakes up robbed of coins, long rest, tries again")
            self.record.setdefault("defeats", []).append({"scene": sc["name"], "attempt": tries})
            for c in self.party:
                if not c.dead:
                    c.coins = {k: 0 for k in c.coins}
            self.long_rest()
            for f in foes:
                if not f.dead:
                    f.hp = f.hp_base
                    f.conditions, f.temps = {}, []
                    f.x = x0 + (10 if f.behaviour.get("role") == "ranged" else 0)
            for c in self.party:
                c.x = 0 if cls_of(c) in ("barbarian", "fighter", "paladin", "monk") else -10
                c.economy = {"reaction": 1}
            t.encounter = {"boss": sc.get("boss", False), "round": 0}
            res = self.encounter(foes, sc)
            tries += 1
        defeated = [f for f in foes if not f.up or f.behaviour.get("fled")]
        won = all(not f.up or f.behaviour.get("fled") for f in foes)
        xp = self.award(sc, defeated) if won else 0
        if won:
            self.after_fight(sc)
            self.loot(sc)
        self.record["scenes"].append({"name": sc["name"], "type": "combat", "won": won, "rounds": res["rounds"],
                                      "foes": [f"{g.get('count', 1)}x {slug(g['ref'])}" for g in sc["foes"]],
                                      "xp_each": xp, "party_hp": {c.name: f"{c.hp}/{eng.hp_max(c)}" for c in self.party},
                                      "dropped": {c.name: c.drops for c in self.party if c.drops},
                                      "dead": [c.name for c in self.party if c.dead]})

    def encounter(self, foes, sc, max_rounds=30):
        eng = self.eng
        party = [c for c in self.party if not c.dead]
        eng.creatures = party + foes
        eng.round = 0
        groups = {}
        for f in foes:
            groups.setdefault(f.monster["ref"], f)
        rolls = {ref: eng.initiative(m) for ref, m in groups.items()}
        eng.log.call("rule", "initiative.groups", "OK", "system.json#initiative")
        order = []
        for c in eng.creatures:
            ini = rolls[c.monster["ref"]] if c.monster else (eng.initiative(c) if c.up else -99)
            order.append((ini, c.mod("dex"), c))
        order.sort(key=lambda r: (-r[0], -r[1]))
        eng.log.say(f"=== {sc['name']}: " + ", ".join(f"{c}({i})" for i, _, c in order))
        for c in eng.creatures:
            if c.up:
                eng.emit("initiative_rolled", c, Ctx(c))
        while eng.round < max_rounds:
            eng.round += 1
            self.tactics.encounter["round"] = eng.round
            for _, _, c in order:
                if c.dead or c.behaviour.get("fled"):
                    continue
                eng.start_turn(c)
                if c.up:
                    self.tactics.turn(eng, c)
                eng.end_turn(c)
                if all(not f.up or f.behaviour.get("fled") for f in foes) or not any(p.up for p in party):
                    return {"rounds": eng.round}
        return {"rounds": eng.round}

    def after_fight(self, sc):
        """Stabilize the fallen, revive the dead if anyone can, end combat-long effects."""
        eng = self.eng
        for c in self.party:
            c.temps = [t for t in c.temps if (t.get("duration") or {}).get("kind") in ("hours", "days", "permanent")
                       or t.get("grant")]
            c.concentration = None if c.concentration and eng.cat.get(c.concentration["ref"])["data"]["duration"].get(
                "kind") in ("minutes", "rounds") else c.concentration
            if c.form is not None:
                eng.end_form(c)
            for k in [k for k, v in c.conditions.items() if k != "dnd5e/condition/unconscious"]:
                c.conditions.pop(k, None)
        for c in self.party:
            if c.dead and not getattr(c, "death_recorded", False):
                c.death_recorded = True
                self.try_revive(c)
            elif c.hp == 0:
                healer = next((h for h in self.party if h.up and h is not c), None)
                if healer is not None:
                    ok = eng.ability_check(healer, "wis", "medicine", 10, Ctx(healer, target=c, ref="dnd5e/rule/dropping-to-0-hit-points"))
                    eng.log.call("op", "check", "OK", "dnd5e/rule/dropping-to-0-hit-points", "Stabilize (Medicine DC 10)")
                    c.stable = c.stable or ok
                c.hp = 1 if c.stable or healer is None else 1
                c.conditions.pop("dnd5e/condition/unconscious", None)
                c.conditions.pop("dnd5e/condition/incapacitated", None)
                eng.log.say(f"{c} is stabilized and regains 1 HP after the fight (GM: rest)")
                eng.log.call("rule", "stable.regain_1_hp", "GM", "dnd5e/rule/dropping-to-0-hit-points",
                             "1d4 hours later a Stable creature regains 1 HP; the party waits")
        if any(c.hp < self.eng.hp_max(c) // 2 for c in self.party if c.up) and sc.get("rest", "short") == "short" \
                and self.short_rests < 2:
            self.short_rest()

    def try_revive(self, c):
        eng = self.eng
        rev = "dnd5e/spell/revivify"
        diamond = None
        for h in self.party:
            for v in h.inventory:
                if "diamond" in v.get("name", "").lower() and v.get("gp", 0) * v.get("quantity", 1) >= 300:
                    diamond = (h, v)
        for h in self.party:
            if not h.up:
                continue
            scroll = next((it for it in h.items if "spell-scroll" in it["ref"] and it.get("spell") == rev), None)
            if scroll and eng.holds({"pred": "spell_on_your_list"}, h, Ctx(h, item=scroll)):
                h.economy = {"action": 1, "bonus_action": 1, "reaction": 1}
                if eng.use_item(h, scroll, c):
                    self.record["deaths"].append({"who": c.name, "revived_by": f"{h.name} (scroll)", "scene": self.scene_name})
                    return
            slot = self.tactics.lowest_slot(eng, h, rev) if rev in h.prepared + h.always else None
            if slot and diamond:
                h.economy = {"action": 1, "bonus_action": 1, "reaction": 1}
                if eng.cast(h, rev, slot, [c]):
                    diamond[1]["quantity"] = diamond[1].get("quantity", 1) - 1
                    self.record["deaths"].append({"who": c.name, "revived_by": h.name, "scene": self.scene_name})
                    return
        self.record["deaths"].append({"who": c.name, "revived_by": None, "scene": self.scene_name, "level": c.level})

    def loot(self, sc):
        if not sc.get("loot"):
            return
        notes = share_out(self.eng, self.party, sc["loot"], self.log)
        self.record["loot"].append({"scene": self.scene_name, "coins": sc["loot"].get("coins"), "notes": notes})
        for n in notes:
            self.log.say(f"loot: {n}")

    def scene_reward(self, sc):
        self.loot(sc)
        self.award(sc)
        self.record["scenes"].append({"name": sc["name"], "type": "reward", "coins": (sc.get("loot") or {}).get("coins"),
                                      "xp_each": sc.get("xp_each", 0)})

    def scene_trap(self, sc):
        """A hazard: a save (or a check to notice it first) and its damage/condition."""
        eng = self.eng
        alive = [c for c in self.party if c.up]
        if not alive:
            return
        victims = alive if sc.get("who") == "all" else [alive[0]]
        noticed = False
        if sc.get("notice"):
            spotter = max(alive, key=lambda c: c.mod("wis") + (c.pb if "perception" in c.prof["skill"] else 0))
            passive = 10 + spotter.mod("wis") + (spotter.pb if "perception" in spotter.prof["skill"] else 0)
            noticed = passive >= sc["notice"]
            eng.log.call("stat", "passive_perception", "OK", "system.json#registries.stats")
            eng.log.say(f"{spotter} passive Perception {passive} vs {sc['notice']}: {'noticed' if noticed else 'missed'}")
        hurt = []
        if not noticed:
            for v in victims:
                ctx = Ctx(v, ref=sc.get("ref", "dnd5e/rule/hazards"))
                ok = eng.saving_throw(v, sc["save"], sc["dc"], ctx)
                if not ok or sc.get("half"):
                    amt = int(eng.ex.ev(sc["damage"], eng.resolver(v, ctx)))
                    if ok:
                        amt //= 2
                    eng.apply_damage(v, amt, sc.get("damage_type", "bludgeoning"), ctx)
                    hurt.append(v.name)
                    for cond in sc.get("conditions", []) if not ok else []:
                        eng.apply_condition(v, cond, sc.get("duration"), ctx)
        for v in victims:
            if v.hp == 0 and not v.dead:
                v.hp = 1
                v.conditions.clear()
        self.award(sc)
        self.record["scenes"].append({"name": sc["name"], "type": "trap", "noticed": noticed, "hurt": hurt})

    def scene_check(self, sc):
        eng = self.eng
        alive = [c for c in self.party if c.up]
        who = max(alive, key=lambda c: c.mod(sc["ability"]) + (c.pb if sc.get("skill") in c.prof["skill"] else 0)
                  + (c.pb if sc.get("tool") in c.prof["tool"] else 0) + (c.pb if sc.get("skill") in c.prof["expertise"] else 0))
        ok = sc.get("auto") or eng.ability_check(who, sc["ability"], sc.get("skill"), sc["dc"],
                                                 Ctx(who, ref=sc.get("ref", "dnd5e/rule/ability-checks")), tool=sc.get("tool"))
        if sc.get("auto"):
            eng.log.say(f"{sc['name']}: automatic success ({sc['auto']})")
        branch = sc.get("on_success" if ok else "on_fail") or {}
        if branch:
            self.loot(branch)
            self.award(branch)
        self.record["scenes"].append({"name": sc["name"], "type": "check", "by": who.name, "success": bool(ok)})

    def scene_rest(self, sc):
        if sc["kind"] == "long":
            self.long_rest()
        else:
            self.short_rest()

    def scene_milestone(self, sc):
        self.milestone(sc["level"], sc["why"])

    def scene_travel(self, sc):
        """Days of travel: a d20 each day and night; 17-20 rolls on the scenario's table."""
        for day in range(sc["days"]):
            for when in ("day", "night"):
                roll = 20 if sc.get("force") else self.rng.randint(1, 20)
                self.log.call("procedure", "random_encounter_check", "OK", None, f"{when} d20={roll}")
                if roll < 17:
                    continue
                d = self.rng.randint(1, 12)
                for lo, hi, ref, count in sc["table"][when]:
                    if lo <= d <= hi:
                        n = count(self.rng) if callable(count) else count
                        self.scene_combat({"name": f"{sc['name']}: {slug(ref)} x{n} ({when} {day + 1})",
                                           "foes": [{"ref": ref, "count": n}], "xp": "monsters", "distance": 40})
                        break
            self.long_rest(quiet=True)

    # ==========================================================================================
    # rests
    # ==========================================================================================
    def short_rest(self):
        eng = self.eng
        sr = eng.cat.get("dnd5e/rule/short-rest")
        spend = next(fx for fx in sr["effects"] if fx["op"] == "activation")
        for c in self.party:
            if c.dead:
                continue
            cls = next(iter(c.hit_dice))
            hd = c.hit_dice[cls]
            while c.hp < eng.hp_max(c) * 0.7 and hd[0] > 0:
                hd[0] -= 1
                die = int(hd[2][1:])
                ctx = Ctx(c, ref="dnd5e/rule/short-rest", flags={"hit_point_die": self.rng.randint(1, die)})
                eng.log.call("op", "activation", "OK", "dnd5e/rule/short-rest", "Spend a Hit Point Die")
                eng.heal(c, int(eng.ev(spend["then"][0]["amount"], c, ctx)), ctx)
            eng.recover(c, "short_rest_finished")
            eng.emit("short_rest_finished", c, Ctx(c))
            eng.reset_uses(c, "short_rest")
        self.short_rests += 1
        self.record["rests"] += 1
        eng.log.say("--- short rest")

    def replace_dead(self):
        """SRD Character Demise: a dead character who can't be revived is replaced by a new one
        (same class) at the party's level, with the XP of that level (GM decision)."""
        for i, c in enumerate(self.party):
            if not c.dead or getattr(c, "replaced", False):
                continue
            c.replaced = True
            living = [p for p in self.party if not p.dead]
            level = min((p.level for p in living), default=c.level)
            base = c.spec["name"].split(" ")[0]
            n = 2 + sum(1 for d in self.record["deaths"] if d.get("replaced_by", "").startswith(base + " "))
            spec = dict(c.spec, name=f"{base} {ROMAN[n]}")
            new = self.make(spec)
            while new.level < level:
                self.level_up(new, "replacement joins at the party's level")
            new.xp = next(a["xp"] for a in self.eng.cat.system["levels"]["advancement"] if a["level"] == new.level)
            self.party[i] = new
            self.graveyard.append(c)
            self.log.call("procedure", "replacement_character", "GM", "dnd5e/rule/dropping-to-0-hit-points",
                          "Character Demise: a new character joins the group")
            self.record["deaths"].append({"who": c.name, "replaced_by": new.name, "scene": self.scene_name})
            self.log.say(f"{new} joins the party (level {new.level}) in place of {c}")

    def morning(self, c):
        """After a Long Rest: Mage Armor (8 hours) from a slot or Armor of Shadows."""
        eng = self.eng
        if any(it["state"] == "worn" and "/armor/" in (it.get("base") or it["ref"]) and slug(it["ref"]) != "shield"
               for it in c.items):
            return
        ma = "dnd5e/spell/mage-armor"
        c.economy = {"action": 1, "bonus_action": 1, "reaction": 1}
        r, inv = self.tactics.activation(eng, c, ref="dnd5e/feature/warlock-invocation-armor-of-shadows")
        if inv:
            eng.activate(c, r, inv, c, Ctx(c, target=c, flags={"targets": [c]}))
            return
        if ma in c.prepared + c.always:
            slot = self.tactics.lowest_slot(eng, c, ma)
            if slot:
                eng.cast(c, ma, slot, [c])

    def long_rest(self, quiet=False):
        eng = self.eng
        self.replace_dead()
        for c in self.party:
            if c.dead:
                continue
            c.temps, c.conditions, c.concentration = [], {}, None
            eng.end_form(c)
            eng.emit("long_rest_finished", c, Ctx(c))
            eng.recover(c, "long_rest_finished")
            for k in ("long_rest", "day"):
                eng.reset_uses(c, k)
            c.hp = eng.hp_max(c)
            for it in c.items:
                if it.get("charges") is not None and slug(it["ref"]) == "wand-of-magic-missiles":
                    it["charges"] = min(7, it["charges"] + self.rng.randint(1, 6) + 1)
            self.morning(c)
        self.short_rests = 0
        self.record["rests"] += 1
        if not quiet:
            eng.log.say("--- long rest")

    # ==========================================================================================
    # report
    # ==========================================================================================
    def sheet(self, c):
        eng = self.eng
        return {"name": c.name, "class": cls_of(c), "subclass": slug(next(iter(c.subclasses.values()))) if c.subclasses else None,
                "level": c.level, "xp": c.xp, "dead": c.dead, "hp_max": eng.hp_max(c), "ac": eng.ac(c, Ctx(c)),
                "scores": {a: eng.score(c, a) for a in c.scores},
                "features": [slug(f) for f in c.features if "/feature/" in f or "/feat/" in f],
                "slots": {k: v[1] for k, v in c.slots.items()}, "pact": c.pact_level,
                "resources": {k: v.get("max") for k, v in c.resources.items()},
                "cantrips": [slug(s) for s in c.cantrips], "prepared": [slug(s) for s in c.prepared],
                "always": [slug(s) for s in c.always], "spellbook": [slug(s) for s in c.spellbook],
                "masteries": c.masteries,
                "items": [{"name": it.get("name") or eng.cat.get(it["ref"])["name"], "state": it["state"],
                           "quantity": it.get("quantity", 1), **({"attuned": True} if it.get("attuned") else {}),
                           **({"charges": it["charges"]} if it.get("charges") is not None else {})} for it in c.items],
                "valuables": c.inventory, "coins": dict(c.coins), "wealth_gp": wealth(c)}

    def summary(self):
        return {"party": [self.sheet(c) for c in self.party], "fallen": [self.sheet(c) for c in self.graveyard],
                **self.record}
