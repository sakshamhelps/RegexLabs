# RegexLab

Test regular expressions against text, stdin and files from the command line: see every match with line/column, capture groups, named groups, and optional replacement previews. Offline, standard library only.

> RegexLab uses **Python `re` syntax**. Patterns that work here may behave differently in JavaScript, PCRE, Go or other engines.

## Install

Python 3.10+.

```
pip install .
# or: PYTHONPATH=src python -m regexlab --help
```

## Usage

```
regexlab test PATTERN [-t TEXT] [--stdin] [-f FILE]... [--flags imsxa] [-r REPLACEMENT] [--limit N] [--format text|json]
regexlab examples     # run built-in example patterns
regexlab flags        # list flags
```

```
$ regexlab test '(?P<y>\d{4})-(?P<m>\d{2})' -t 'built 2026-11 and 2027-01'
$ regexlab test '^TODO' -f src/app.py --flags m
$ regexlab test '(\w+)@(\w+)' -t 'me@site' -r '\2 at \1'
```

Flags: `i` IGNORECASE, `m` MULTILINE, `s` DOTALL, `x` VERBOSE, `a` ASCII.

Exit codes: `0` at least one match, `1` no match, `2` error (bad pattern, bad flag, missing/unreadable file, no input).

## Limitations

- Files must be UTF-8 text and at most 10 MB.
- Python's `re` can suffer **catastrophic backtracking** on pathological patterns (e.g. `(a+)+$` on long inputs). RegexLab does not impose a timeout; press Ctrl+C to abort.
- Output lists at most `--limit` matches (default 1000) per input.

## Tests

```
python -m unittest discover -s tests -v
```

## Licence

MIT, Copyright (c) 2026 BYREX. No third-party dependencies.

The MIT licence covers the code only. The BYREX name and branding are not licensed for use by forks: see [TRADEMARK.md](TRADEMARK.md).
