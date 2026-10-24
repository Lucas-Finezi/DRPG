"""Two six-adventurer groups play the Lost Mine of Phandelver; together they use all 12 classes.

SIMULATION ONLY (see scenario.py). Usage:
  python3 -I -m simulations.phandelver.run [--seed 2026] [--batch 20]
Writes reports/simulation/phandelver.json.
"""
import argparse
import json
from pathlib import Path

from tools.engine.calllog import STATUSES, CallLog
from tools.engine.campaign import Campaign
from tools.engine.catalog import ROOT
from tools.engine.simulate_goblins import merge

from .scenario import SUBSTITUTES, scenes

# Classes split between the groups; the 9 species and 4 backgrounds all appear.
GROUPS = {
    "A": [dict(name="Fighter", cls="fighter", species="human", background="soldier"),
          dict(name="Cleric", cls="cleric", species="dwarf", background="acolyte"),
          dict(name="Rogue", cls="rogue", species="halfling", background="criminal"),
          dict(name="Wizard", cls="wizard", species="elf", background="sage"),
          dict(name="Ranger", cls="ranger", species="orc", background="soldier"),
          dict(name="Bard", cls="bard", species="tiefling", background="criminal")],
    "B": [dict(name="Paladin", cls="paladin", species="dragonborn", background="soldier"),
          dict(name="Druid", cls="druid", species="gnome", background="sage"),
          dict(name="Barbarian", cls="barbarian", species="goliath", background="soldier"),
          dict(name="Monk", cls="monk", species="human", background="criminal"),
          dict(name="Sorcerer", cls="sorcerer", species="elf", background="sage"),
          dict(name="Warlock", cls="warlock", species="tiefling", background="acolyte")],
}


def play(group, seed, log=None):
    camp = Campaign(seed, GROUPS[group], log=log)
    created = [camp.sheet(c) for c in camp.party]
    out = camp.run(scenes())
    out["created"] = created
    out["narrative"] = camp.log.events
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--batch", type=int, default=0)
    ap.add_argument("--out", default=str(ROOT / "reports" / "simulation" / "phandelver.json"))
    a = ap.parse_args(argv)
    result = {"substitutes": SUBSTITUTES, "groups": {}}
    logs = []
    for g in GROUPS:
        log = CallLog()
        run = play(g, a.seed, log)
        logs.append(log)
        batch = []
        blog = CallLog()
        for s in range(a.batch):
            r = play(g, 5000 + s, blog)
            deaths = [d for d in r["deaths"] if "revived_by" in d]
            batch.append({"seed": 5000 + s, "deaths": len(deaths),
                          "permanent_deaths": sum(1 for d in deaths if not d["revived_by"]),
                          "defeats": len(r.get("defeats", [])),
                          "finished": not any(sc.get("skipped") for sc in r["scenes"]),
                          "levels": [p["level"] for p in r["party"]]})
        logs.append(blog)
        result["groups"][g] = {"story": run, "batch": batch,
                               "calls": merge(log, blog),
                               "totals": {s: sum(x["count"] for x in merge(log, blog) if x["status"] == s) for s in STATUSES}}
        print(g, result["groups"][g]["totals"])
    result["calls"] = merge(*logs)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(result, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    main()
