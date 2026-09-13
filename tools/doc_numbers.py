"""Prose in a generated document must be generated too.

The defect this catches is drift. A tool writes its tables from the current run and its narrative from a
frozen string, so a rerun with more systems, a new split or a fixed bug silently leaves the paragraphs
describing a run that no longer exists. The tables are then right and the words around them are wrong,
which is worse than either alone because the reader has no way to tell which is current.

A numeric literal inside a plain string that a report-writing tool emits is a drift risk by construction:
nothing recomputes it. An f-string interpolating a variable is not, and neither is a number in a name, a
version, a URL or a column header. The check reads the tool sources, not their output, so it fails at the
place the fix belongs.

Usage: python tools/doc_numbers.py tools/*.py          # report
       python tools/doc_numbers.py --quiet tools/*.py  # exit 1 on any finding, for CI
"""
from __future__ import annotations
import argparse, ast, re, sys
from pathlib import Path

# a statistic: a decimal with two or more places, or a four-digit-plus count
STAT = re.compile(r"(?<![\w.])[-+]?\d+\.\d{2,}(?![\w.])|(?<![\w.])\d{4,}(?![\w.])")
# contexts where a number is a name or a setting rather than a claim
SKIP = re.compile(r"https?://|\.jsonl|\.json|\.md|\.py|gpt-|claude-|gemini-|llama-|qwen|grok|kimi|glm|deepseek", re.I)


def prose_strings(src: str):
    """(lineno, text) for every plain string constant in the file; f-strings and their pieces are skipped."""
    tree = ast.parse(src)
    out = []
    joined = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):                       # an f-string recomputes; its literal parts are context
            for part in ast.walk(node):
                if isinstance(part, ast.Constant):
                    joined.add(id(part))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in joined:
            out.append((node.lineno, node.value))
    return out


def check(path: Path):
    src = path.read_text()
    lines = src.splitlines()
    bad = []
    for lineno, text in prose_strings(src):
        if len(text) < 40 or SKIP.search(text):                   # short strings are keys, flags and headers
            continue
        if text.lstrip().startswith("|") or text.lstrip().startswith("#"):
            continue
        for m in STAT.finditer(text):
            tok = m.group(0)
            if tok in ("0.05", "0.95", "0.90"):                   # preregistered thresholds are fixed by the protocol
                continue
            ctx = lines[lineno - 1].strip()[:110] if lineno <= len(lines) else ""
            bad.append((lineno, tok, ctx))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    total = 0
    for p in sorted(Path(x) for x in a.paths):
        if not p.is_file() or p.suffix != ".py":
            continue
        bad = check(p)
        total += len(bad)
        if bad:
            print(f"\n{p}: {len(bad)} frozen number(s) in emitted prose")
            for lineno, tok, ctx in bad:
                print(f"  {p}:{lineno}  {tok:>9s}   {ctx}")
        elif not a.quiet:
            print(f"{p}: ok")
    if total:
        print(f"\n{total} frozen numbers; recompute them from the run instead of writing them into the string")
        sys.exit(1)
    print("\nno frozen statistics in emitted prose")


if __name__ == "__main__":
    main()
