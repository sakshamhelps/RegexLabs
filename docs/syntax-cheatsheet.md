# Python regex quick reference

| Syntax | Meaning |
|---|---|
| `.` | any character (not newline unless `s`) |
| `\d \w \s` | digit, word char, whitespace |
| `^ $` | start/end of string (of line with `m`) |
| `* + ? {n,m}` | repetition; add `?` for non-greedy |
| `(...)` / `(?:...)` | capturing / non-capturing group |
| `(?P<name>...)` | named group |
| `(?=...)` `(?!...)` | lookahead |
| `(?<=...)` `(?<!...)` | lookbehind (fixed width) |
