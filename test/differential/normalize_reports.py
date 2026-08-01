#!/usr/bin/env python3
"""
migrate-python3 differential validation (phase 5.2/5.4).

Normalize + diff two fuzzingserver index.json report sets. Strips only
run-specific noise (durations, report filenames); compares case identifiers,
behavior (pass/fail/non-strict/informational) and remoteCloseCode verbatim.

  python test/differential/normalize_reports.py REFERENCE/index.json PY3/index.json \
      [--triage test/differential/triage.json]

Exits non-zero if any case outcome differs and is not covered by a triage entry.
Triage file: {"<caseId>": "reason string", ...}
"""
import json, sys, argparse


def norm(path):
    d = json.load(open(path))
    out = {}
    for agent, cases in d.items():
        for cid, c in cases.items():
            # compare only the behavior-defining fields; drop duration/reportfile
            out[cid] = {"behavior": c.get("behavior"),
                        "behaviorClose": c.get("behaviorClose"),
                        "remoteCloseCode": c.get("remoteCloseCode")}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reference")
    ap.add_argument("candidate")
    ap.add_argument("--triage", default=None)
    a = ap.parse_args()

    ref, cand = norm(a.reference), norm(a.candidate)
    triage = json.load(open(a.triage)) if a.triage else {}

    all_ids = sorted(set(ref) | set(cand), key=lambda s: [int(x) for x in s.split(".")])
    diffs, accepted = [], []
    for cid in all_ids:
        r, c = ref.get(cid), cand.get(cid)
        if r != c:
            (accepted if cid in triage else diffs).append((cid, r, c))

    for cid, r, c in accepted:
        print("ACCEPTED %s (triage: %s)\n   ref=%s\n   cand=%s" % (cid, triage[cid], r, c))
    for cid, r, c in diffs:
        print("DIFF     %s\n   ref=%s\n   cand=%s" % (cid, r, c))

    print("\n%d cases compared, %d accepted diffs, %d untriaged diffs"
          % (len(all_ids), len(accepted), len(diffs)))
    sys.exit(1 if diffs else 0)


if __name__ == "__main__":
    main()
