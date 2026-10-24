"""Expression evaluation (urn:drpg:schema:expression) with real dice."""
import re

DICE = re.compile(r"^\s*(\d*)d(\d+)\s*(?:([+-])\s*(\d+))?\s*$")


def parse_cell(text):
    """A features-table cell as a value: '+2' -> 2, '1d6' -> '1d6', '+10 ft.' -> 10, '—' -> 0."""
    t = str(text).strip()
    if re.fullmatch(r"D\d+", t):
        t = "1" + t.lower()
    if t in ("—", "-", ""):
        return 0
    if DICE.match(t):
        return t
    m = re.match(r"^[+]?(-?\d+)", t)
    if m:
        return int(m.group(1))
    raise ValueError(text)


class Evaluator:
    """Evaluate expressions; `resolve(name)` supplies {var} values; dice are rolled with `rng`."""

    def __init__(self, rng, log, catalog):
        self.rng, self.log, self.cat = rng, log, catalog

    die_min = 0       # Great Weapon Fighting: a 1 or 2 on a damage die counts as 3

    def roll(self, n, faces, crit=False, best_of=1):
        n = n * 2 if crit else n
        best = None
        for _ in range(best_of):
            tot = sum(max(self.die_min, self.rng.randint(1, faces)) for _ in range(n))
            best = tot if best is None else max(best, tot)
        return best

    def ev(self, x, resolve, crit=False, best_of=1, ref=None):
        if x is None:
            return 0
        if isinstance(x, bool):
            return int(x)
        if isinstance(x, (int, float)):
            return x
        if isinstance(x, str):
            m = DICE.match(x)
            if not m:
                self.log.call("expr", x, "DATA_GAP", ref, "string is not a dice expression")
                return 0
            n = int(m.group(1) or 1)
            v = self.roll(n, int(m.group(2)), crit, best_of)
            if m.group(3):
                v += int(m.group(4)) * (1 if m.group(3) == "+" else -1)
            return v
        if "var" in x:
            return resolve(x["var"])
        if "dice" in x:
            n = self.ev(x["dice"]["count"], resolve, ref=ref)
            return self.roll(int(n), x["dice"]["faces"], crit, best_of)
        if "op" in x:
            a = [self.ev(y, resolve, crit, best_of, ref) for y in x["args"]]
            op = x["op"]
            if op == "add":
                return sum(a)
            if op == "sub":
                return a[0] - sum(a[1:])
            if op == "mul":
                r = 1
                for v in a:
                    r *= v
                return r
            if op == "div":
                q = a[0] / a[1]
                return -(-a[0] // a[1]) if x.get("round") == "up" else int(q // 1)
            if op == "min":
                return min(a)
            if op == "max":
                return max(a)
            if op == "neg":
                return -a[0]
            self.log.call("expr_op", op, "ENGINE_GAP", ref)
            return 0
        if "table" in x:
            cell = self.table_cell(x, resolve, ref)
            v = parse_cell(cell)
            return self.ev(v, resolve, crit, best_of, ref) if isinstance(v, str) else v
        if "scale" in x:
            v = resolve(x["scale"]["by"])
            out = 0
            for st in x["scale"]["steps"]:
                if v >= st["from"]:
                    out = st["value"]
            return self.ev(out, resolve, crit, best_of, ref) if isinstance(out, (str, dict)) else out
        if "choose_from" in x:
            self.log.call("expr", "choose_from", "OK", ref)
            return x["choose_from"][0]
        self.log.call("expr", str(sorted(x)), "ENGINE_GAP", ref)
        return 0

    def table_cell(self, x, resolve, ref=None):
        e = self.cat.get(x["table"])
        key = str(int(self.ev(x["key"], resolve, ref=ref)))
        if "levels" in (e.get("data") or {}):
            cell = e["data"]["levels"][key]["columns"][x["column"]]
        else:   # a data.tables table: the row whose first cell is the key
            t = next(t for t in e["data"].get("tables", []) if t["id"] == x.get("table_id"))
            row = next(r for r in t["rows"] if str(r[0]) == key)
            cell = row[t["columns"].index(x["column"])]
        self.log.call("table", f'{x.get("table_id")}[{x["column"]}]', "OK", x["table"])
        return cell

    def dice_of(self, x, resolve, ref=None):
        """The dice string a table/expression stands for, without rolling it (Martial Arts die)."""
        if isinstance(x, str):
            return x
        if isinstance(x, dict) and "table" in x:
            return str(parse_cell(self.table_cell(x, resolve, ref)))
        return None
