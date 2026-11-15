"""RegexLab: test regular expressions (Python `re` syntax) against text and files."""
from __future__ import annotations
import argparse, json, os, re, sys
from . import __version__

FLAGS = {"i": re.IGNORECASE, "m": re.MULTILINE, "s": re.DOTALL, "x": re.VERBOSE, "a": re.ASCII}
MAX_FILE_BYTES = 10 * 1024 * 1024

class RegexLabError(Exception):
    pass

def parse_flags(spec: str) -> int:
    value = 0
    for ch in spec or "":
        if ch not in FLAGS:
            raise RegexLabError(f"unknown flag '{ch}' (valid: {''.join(FLAGS)})")
        value |= FLAGS[ch]
    return value

def compile_pattern(pattern: str, flags: str = ""):
    if pattern == "":
        raise RegexLabError("pattern is empty")
    try:
        return re.compile(pattern, parse_flags(flags))
    except re.error as e:
        pos = f" at position {e.pos}" if e.pos is not None else ""
        raise RegexLabError(f"invalid regular expression: {e.msg}{pos}")

def line_col(text: str, index: int):
    line = text.count("\n", 0, index) + 1
    col = index - (text.rfind("\n", 0, index) + 1) + 1
    return line, col

def find_matches(rx, text: str, limit: int = 1000):
    out = []
    for m in rx.finditer(text):
        ln, col = line_col(text, m.start())
        out.append({"match": m.group(0), "start": m.start(), "end": m.end(), "line": ln, "column": col,
                    "groups": list(m.groups()), "named": m.groupdict()})
        if len(out) >= limit:
            break
    return out

def do_replace(rx, text, repl):
    try:
        return rx.subn(repl, text)
    except (re.error, IndexError) as e:
        raise RegexLabError(f"invalid replacement: {e}")

def read_file(path):
    if not os.path.exists(path): raise RegexLabError(f"file not found: {path}")
    if os.path.isdir(path): raise RegexLabError(f"is a directory: {path}")
    try:
        if os.path.getsize(path) > MAX_FILE_BYTES: raise RegexLabError(f"file too large (> {MAX_FILE_BYTES // 1024 // 1024} MB): {path}")
        with open(path, "r", encoding="utf-8") as f: return f.read()
    except PermissionError: raise RegexLabError(f"permission denied: {path}")
    except UnicodeDecodeError: raise RegexLabError(f"not valid UTF-8 text: {path}")

EXAMPLES = [
    ("Email addresses", r"[\w.+-]+@[\w-]+\.[\w.-]+", "", "Contact: ada@example.com, bob.smith+tag@mail.example.org"),
    ("ISO dates with named groups", r"(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})", "", "Released 2026-01-31, patched 2026-02-14."),
    ("IPv4-like addresses", r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "", "server 192.168.0.1 and 10.0.0.255"),
    ("Lines starting with TODO (multiline flag)", r"^TODO:.*$", "m", "TODO: fix\nok\nTODO: test"),
    ("Hex colours (case-insensitive)", r"#(?:[0-9a-f]{3}){1,2}\b", "i", "colors #FFF #1a2B3c #12"),
]

def build_parser():
    p = argparse.ArgumentParser(prog="regexlab", description="Test Python-syntax regular expressions against text or files.")
    p.add_argument("--version", action="version", version=f"regexlab {__version__}")
    sub = p.add_subparsers(dest="command", required=True)
    t = sub.add_parser("test", help="find matches of PATTERN in text")
    t.add_argument("pattern"); t.add_argument("-t", "--text", help="text to search")
    t.add_argument("-f", "--file", action="append", default=[], help="file to search (repeatable)")
    t.add_argument("--flags", default="", help="any of: i m s x a (e.g. im)")
    t.add_argument("-r", "--replace", help="also show result of substituting matches with this replacement")
    t.add_argument("--limit", type=int, default=1000, help="max matches per input")
    t.add_argument("--format", choices=["text", "json"], default="text")
    t.add_argument("--stdin", action="store_true", help="read text from stdin")
    sub.add_parser("examples", help="run built-in example patterns")
    sub.add_parser("flags", help="describe supported flags")
    return p

def show(label, text, rx, args):
    ms = find_matches(rx, text, args.limit)
    result = {"source": label, "count": len(ms), "matches": ms}
    if args.replace is not None:
        result["replaced"], result["replacements"] = do_replace(rx, text, args.replace)
    return result

def print_text(r):
    print(f"[{r['source']}] {r['count']} match(es)")
    for i, m in enumerate(r["matches"], 1):
        shown = m["match"] if len(m["match"]) <= 80 else m["match"][:77] + "..."
        print(f"  {i}. line {m['line']}, col {m['column']}: {shown!r}")
        for j, g in enumerate(m["groups"], 1): print(f"       group {j}: {g!r}")
        for k, v in m["named"].items(): print(f"       <{k}>: {v!r}")
    if "replaced" in r:
        print(f"  --- replaced ({r['replacements']}) ---"); print(r["replaced"])

def _main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    try:
        if a.command == "flags":
            for k, v in FLAGS.items(): print(f"{k}  re.{re.RegexFlag(v).name}")
            return 0
        if a.command == "examples":
            for title, pat, fl, text in EXAMPLES:
                print(f"## {title}\npattern: {pat}  flags: {fl or '-'}")
                print_text(show("example", text, compile_pattern(pat, fl), argparse.Namespace(limit=100, replace=None))); print()
            return 0
        rx = compile_pattern(a.pattern, a.flags)
        if a.limit < 1: raise RegexLabError("--limit must be >= 1")
        sources = []
        if a.text is not None: sources.append(("text", a.text))
        if a.stdin: sources.append(("stdin", sys.stdin.read()))
        for f in a.file: sources.append((f, read_file(f)))
        if not sources: raise RegexLabError("provide --text, --stdin or --file")
        results = [show(l, t, rx, a) for l, t in sources]
        if a.format == "json": print(json.dumps(results, indent=2))
        else:
            for r in results: print_text(r)
        return 0 if any(r["count"] for r in results) else 1
    except RegexLabError as e:
        print(f"regexlab: error: {e}", file=sys.stderr); return 2


def main(argv=None) -> int:
    """Entry point. Exits quietly if the output pipe is closed (e.g. `| head`)."""
    try:
        return _main(argv)
    except BrokenPipeError:
        try:
            sys.stdout = open(os.devnull, "w")
        except OSError:
            pass
        return 0
