#!/usr/bin/env python3
"""
One-off migration helper (migrate-python3, task 4.1).

Rewrites the Python 2 test-case files under autobahntestsuite/case/ to Python 3,
applying the bytes-discipline rules from the change design:

  * intra-package imports  ->  absolute (autobahntestsuite.case.*)
  * wire payload / message string literals  ->  bytes
      - pure-ASCII literals get a b"" prefix
      - non-ASCII (UTF-8 torture) literals become "...".encode("utf8")
  * single-byte indexing PAYLOAD[n] (int in py3) -> PAYLOAD[n:n+1] (bytes)
  * print statements / has_key / except-comma  -> py3 forms

Idempotent-ish and conservative: only rewrites lines matching the known
payload/message patterns. Files needing hand review are printed at the end.
Run from the repo root:  python3 test/port_cases_to_py3.py
"""
import os, re, sys

CASE_DIR = os.path.join(os.path.dirname(__file__), "..",
                        "autobahntestsuite", "autobahntestsuite", "case")

# assignment targets whose string value is wire data (sent or expected)
DATA_LHS = re.compile(r'^(\s*)(self\.)?(payload|PAYLOAD\d?|testData)(\s*=\s*)(.+?)(\s*)$')

def is_ascii(s):
    try:
        s.encode("ascii"); return True
    except UnicodeEncodeError:
        return False

def to_bytes_expr(expr):
    """Convert a py2 str-valued RHS expression to an equivalent bytes expression.
    Handles: "lit", 'lit', u"lit", "x"*N, concatenations of these, and already-b"" ."""
    e = expr.strip()
    # already bytes or references a bytes name / call -> leave
    if e.startswith('b"') or e.startswith("b'"):
        return expr
    # strip a leading u prefix on unicode literals
    # tokenised approach: transform each quoted literal in the expression
    def repl_literal(m):
        quote, body = m.group(1), m.group(2)
        # Decide b"" vs .encode("utf8") on the RAW SOURCE body, not the decoded
        # value: `\xfe` is ASCII source describing byte 0xFE (a deliberately
        # invalid-UTF-8 torture byte) and must stay a raw byte -> b"...".
        # A literal non-ASCII character in source (e.g. µ, ß, κ under a utf-8
        # coding cookie) was the UTF-8 bytes of that text in py2 -> .encode.
        if is_ascii(body):
            return 'b%s%s%s' % (quote, body, quote)
        else:
            return '%s%s%s.encode("utf8")' % (quote, body, quote)
    # match optional u/r prefix + quote + body (no nested same-quote)
    lit = re.compile(r'(?:u|U)?("|\')((?:\\.|(?!\1).)*)\1')
    # only rewrite if the expression is purely literals/operators/names we trust
    if re.search(r'\b(chr|bytes|bytearray|struct)\b', e):
        return None  # needs manual review
    return lit.sub(repl_literal, expr)

def port_source(src):
    notes = []
    out = []
    for line in src.split("\n"):
        orig = line

        # imports
        line = re.sub(r'^from case import ', 'from autobahntestsuite.case import ', line)
        line = re.sub(r'^from (case[0-9][0-9A-Za-z_]*) import ',
                      r'from autobahntestsuite.case.\1 import ', line)
        line = re.sub(r'^import (case[0-9][0-9A-Za-z_]*)$',
                      r'import autobahntestsuite.case.\1', line)

        # single-byte index used as payload/hex -> slice to keep bytes
        line = re.sub(r'(PAYLOAD)\[(\d+)\](?!\s*[:\]])',
                      lambda m: '%s[%s:%d]' % (m.group(1), m.group(2), int(m.group(2)) + 1),
                      line)

        # payload/PAYLOAD/testData string assignments -> bytes
        m = DATA_LHS.match(line)
        if m and ('"' in m.group(5) or "'" in m.group(5)):
            rhs = m.group(5)
            newrhs = to_bytes_expr(rhs)
            if newrhs is None:
                notes.append("manual: %s" % orig.strip())
            elif newrhs != rhs:
                line = "%s%s%s%s%s%s" % (m.group(1), m.group(2) or "", m.group(3),
                                         m.group(4), newrhs, m.group(6))

        # ("message", "literal", bool) expected tuples -> bytes message
        def msg_tuple(mm):
            body = mm.group(1)
            if is_ascii(body):
                return '("message", b"%s"' % body
            return '("message", "%s".encode("utf8")' % body
        line = re.sub(r'\("message",\s*"((?:\\.|[^"\\])*)"', msg_tuple, line)

        # inline payload = "lit" inside sendFrame(...) calls
        def inline_payload(mm):
            pre, body = mm.group(1), mm.group(2)
            if is_ascii(body):
                return '%sb"%s"' % (pre, body)
            return '%s"%s".encode("utf8")' % (pre, body)
        line = re.sub(r'(payload\s*=\s*)"((?:\\.|[^"\\])*)"', inline_payload, line)

        # py2 syntax
        line = re.sub(r'^(\s*)print (.+)$', lambda mm: '%sprint(%s)' % (mm.group(1), mm.group(2).rstrip()), line)
        line = re.sub(r'([\w\.\[\]"\']+)\.has_key\(([^()]+)\)', r'\2 in \1', line)
        line = re.sub(r'except (\w[\w\.]*), (\w+):', r'except \1 as \2:', line)

        out.append(line)
    return "\n".join(out), notes

def main():
    review = {}
    for fn in sorted(os.listdir(CASE_DIR)):
        if not fn.endswith(".py"):
            continue
        path = os.path.join(CASE_DIR, fn)
        src = open(path, encoding="utf-8").read()
        new, notes = port_source(src)
        if new != src:
            open(path, "w", encoding="utf-8").write(new)
        if notes:
            review[fn] = notes
    if review:
        print("Files needing manual review:")
        for fn, notes in review.items():
            print("  %s" % fn)
            for n in notes:
                print("     %s" % n)
    else:
        print("No files flagged for manual review.")

if __name__ == "__main__":
    main()
