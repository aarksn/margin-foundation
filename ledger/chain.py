"""
THE MARGIN FOUNDATION — chain.py
The hash chain under the public ledger. This file is the whole trust
model: every forecast entry is hash-linked to its predecessor, so any
alteration of history changes every subsequent hash and the published
head. The site serves chain.json verbatim; anyone can re-run verify().

Recreated 2026-07-05: the original was authored in an ephemeral
sandbox and never pushed. The GENESIS_HASH constant survives in the
deployed site and its tests and is kept verbatim as the chain anchor.
The anchor is fully auditable: GENESIS_HASH == SHA-256 of the ASCII
string "the-margin-genesis" — and in any case integrity derives from
the links, not from the anchor's provenance.

API (consumed by margin/bridge.py — do not change signatures):
  GENESIS_HASH: str
  append(ledger: list, entry: dict) -> dict   # links + appends, returns stored entry
  head(ledger: list) -> str                   # tip hash (GENESIS_HASH when empty)
  verify(ledger: list) -> (bool, str)         # full recompute walk
"""
import hashlib
import json

GENESIS_HASH = "2eb85a69aa3d424e3afba45f1195222527fbd36c548c46cf9d2e895d74f4808c"

# every field EXCEPT the link fields participates in the hash
LINK_FIELDS = ("prev", "hash")

def _canonical(entry: dict) -> str:
    payload = {k: v for k, v in entry.items() if k not in LINK_FIELDS}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))

def _entry_hash(prev: str, entry: dict) -> str:
    return hashlib.sha256(
        (prev + "|" + _canonical(entry)).encode("utf-8")).hexdigest()

def head(ledger: list) -> str:
    return ledger[-1]["hash"] if ledger else GENESIS_HASH

def append(ledger: list, entry: dict) -> dict:
    e = dict(entry)
    e["prev"] = head(ledger)
    e["hash"] = _entry_hash(e["prev"], e)
    ledger.append(e)
    return e

def verify(ledger: list):
    prev = GENESIS_HASH
    last_id = 0
    for i, e in enumerate(ledger):
        if e.get("prev") != prev:
            return False, f"broken link at index {i} (id {e.get('id')})"
        if e.get("hash") != _entry_hash(prev, e):
            return False, f"hash mismatch at index {i} (id {e.get('id')})"
        eid = e.get("id")
        if not isinstance(eid, int) or eid <= last_id:
            return False, f"non-monotonic id at index {i}: {eid!r}"
        last_id = eid
        prev = e["hash"]
    return True, f"verified {len(ledger)} entries · head {prev[:16]}"

# ----------------------------------------------------------------- selftest
def selftest():
    ok = True
    def check(name, cond):
        nonlocal ok
        print("  %-46s %s" % (name, "PASS" if cond else "FAIL"))
        ok = ok and cond
    led = []
    check("empty ledger verifies", verify([]) == (True,
          "verified 0 entries · head " + GENESIS_HASH[:16]))
    check("head of empty is genesis", head(led) == GENESIS_HASH)
    e1 = append(led, {"id": 1, "ts": "t1", "market": "M1",
                      "action": "open", "model_prob": 0.6})
    e2 = append(led, {"id": 2, "ts": "t2", "market": "M1",
                      "action": "resolve", "outcome": 1})
    check("links chain from genesis", e1["prev"] == GENESIS_HASH
          and e2["prev"] == e1["hash"])
    check("clean chain verifies", verify(led)[0])
    check("head is last hash", head(led) == e2["hash"])
    tampered = json.loads(json.dumps(led))
    tampered[0]["model_prob"] = 0.11
    check("value tamper detected", not verify(tampered)[0])
    reordered = [led[1], led[0]]
    check("reorder detected", not verify(reordered)[0])
    truncated_mid = [led[1]]
    check("truncation-from-front detected", not verify(truncated_mid)[0])
    dup = json.loads(json.dumps(led))
    dup[1]["id"] = 1
    check("non-monotonic id detected", not verify(dup)[0])
    check("determinism: same input same hash",
          _entry_hash(GENESIS_HASH, {"id": 1, "a": 1})
          == _entry_hash(GENESIS_HASH, {"a": 1, "id": 1}))
    print("\n%s" % ("ALL PASS" if ok else "FAILURES"))
    return ok

if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
