"""Every call the engine makes into the catalog, with its outcome.

Statuses:
  OK          executed from structured catalog data
  DATA_GAP    the catalog lacks what the call needs (placeholder, note-only mechanic, text-only table)
  ENGINE_GAP  the data is there but this prototype does not execute it
  GM          the rules hand the decision to the GM or player (master decision, narrative, map)
"""
from collections import OrderedDict

STATUSES = ("OK", "DATA_GAP", "ENGINE_GAP", "GM")


class CallLog:
    def __init__(self):
        self.calls = OrderedDict()   # key -> record
        self.events = []             # narrative lines
        self.phase = "setup"

    def call(self, kind, name, status="OK", ref=None, detail=None):
        assert status in STATUSES, status
        key = (self.phase, kind, name, ref, status, detail)
        rec = self.calls.get(key)
        if rec is None:
            rec = self.calls[key] = {"phase": self.phase, "kind": kind, "name": name, "ref": ref,
                                     "status": status, "detail": detail, "count": 0}
        rec["count"] += 1
        return status == "OK"

    def say(self, line):
        self.events.append(f"[{self.phase}] {line}")

    def summary(self):
        out = {}
        for r in self.calls.values():
            ph = out.setdefault(r["phase"], {s: 0 for s in STATUSES})
            ph[r["status"]] += r["count"]
        return out

    def problems(self):
        return [r for r in self.calls.values() if r["status"] != "OK"]

    def distinct(self, status=None):
        seen = OrderedDict()
        for r in self.calls.values():
            if status and r["status"] != status:
                continue
            k = (r["kind"], r["name"], r["ref"], r["status"], r["detail"])
            if k not in seen:
                seen[k] = dict(r, phases=[r["phase"]])
            else:
                seen[k]["count"] += r["count"]
                if r["phase"] not in seen[k]["phases"]:
                    seen[k]["phases"].append(r["phase"])
        return list(seen.values())
