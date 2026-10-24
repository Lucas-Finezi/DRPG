"""Read-only access to the generated catalog, as the engine sees it."""
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KNOW = ROOT / "knowledge" / "dnd5e"
ENT = KNOW / "entries"


class Catalog:
    def __init__(self, root=KNOW):
        self.root = Path(root)
        self.system = json.loads((self.root / "system.json").read_text(encoding="utf-8"))

    @lru_cache(maxsize=None)
    def get(self, ref):
        kind, slug = ref.split("/")[-2:]
        p = self.root / "entries" / kind / f"{slug}.json"
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def exists(self, ref):
        return self.get(ref) is not None

    @lru_cache(maxsize=None)
    def kind(self, kind):
        return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((self.root / "entries" / kind).glob("*.json"))]

    def spells(self, cls=None, level=None, school=None):
        out = []
        for e in self.kind("spell"):
            f = e["facets"]
            if cls and cls not in f.get("classes", []):
                continue
            if level is not None and f.get("level") != level:
                continue
            if school and f.get("school") != school:
                continue
            out.append(e)
        return out

    def ability_mod(self, score):
        for row in self.system["ability_scores"]["modifier_table"]:
            if row["min"] <= score <= row["max"]:
                return row["modifier"]
        raise ValueError(score)

    def proficiency_bonus(self, level):
        return self.system["proficiency_bonus"]["by_level"][str(level)]

    def table_rows(self, ref, table_id):
        e = self.get(ref)
        for t in (e.get("data") or {}).get("tables", []):
            if t["id"] == table_id:
                return t
        return None

    def rule(self, ref, rule_id):
        e = self.get(ref)
        for r in (e.get("data") or {}).get("rules", []):
            if r.get("id") == rule_id:
                return r
        return None
