import io, json, os, tempfile, unittest, contextlib, sys
import _path  # noqa
from regexlab.cli import main, compile_pattern, find_matches, RegexLabError, line_col

def run(argv, stdin=None):
    o, e = io.StringIO(), io.StringIO(); old = sys.stdin
    if stdin is not None: sys.stdin = io.StringIO(stdin)
    try:
        with contextlib.redirect_stdout(o), contextlib.redirect_stderr(e):
            try: c = main(argv)
            except SystemExit as x: c = x.code
    finally: sys.stdin = old
    return c, o.getvalue(), e.getvalue()

class T(unittest.TestCase):
    def test_basic_match_and_exit_codes(self):
        c, o, _ = run(["test", r"\d+", "-t", "a1 b22"]); self.assertEqual(c, 0); self.assertIn("2 match", o)
        self.assertEqual(run(["test", r"\d+", "-t", "abc"])[0], 1)
    def test_groups_named_and_positions(self):
        rx = compile_pattern(r"(?P<k>\w+)=(\d+)"); m = find_matches(rx, "x\nab=12")[0]
        self.assertEqual((m["line"], m["column"]), (2, 1)); self.assertEqual(m["named"], {"k": "ab"}); self.assertEqual(m["groups"], ["ab", "12"])
    def test_flags(self):
        self.assertEqual(len(find_matches(compile_pattern("a", "i"), "aA")), 2)
        self.assertEqual(len(find_matches(compile_pattern("^x", "m"), "x\nx")), 2)
        self.assertEqual(len(find_matches(compile_pattern("a.b", "s"), "a\nb")), 1)
    def test_bad_flag_and_bad_pattern(self):
        c, _, e = run(["test", "a", "-t", "a", "--flags", "z"]); self.assertEqual(c, 2); self.assertIn("unknown flag", e)
        c, _, e = run(["test", "(unclosed", "-t", "x"]); self.assertEqual(c, 2); self.assertIn("invalid regular expression", e)
    def test_empty_pattern_and_empty_text(self):
        self.assertEqual(run(["test", "", "-t", "x"])[0], 2)
        self.assertEqual(run(["test", "a", "-t", ""])[0], 1)
    def test_no_input_given(self): self.assertEqual(run(["test", "a"])[0], 2)
    def test_file_and_missing_and_dir_and_binary(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "f.txt")
            with open(p, "w") as f: f.write("foo\nbar foo")
            c, o, _ = run(["test", "foo", "-f", p]); self.assertEqual(c, 0); self.assertIn("2 match", o)
            self.assertEqual(run(["test", "x", "-f", os.path.join(d, "no")])[0], 2)
            self.assertEqual(run(["test", "x", "-f", d])[0], 2)
            b = os.path.join(d, "b.bin")
            with open(b, "wb") as f: f.write(b"\xff\xfe\xfd")
            self.assertEqual(run(["test", "x", "-f", b])[0], 2)
    def test_replace(self):
        c, o, _ = run(["test", r"(\w+)@", "-t", "ab@x", "-r", r"<\1>@"]); self.assertIn("<ab>@x", o)
        c, _, e = run(["test", "a", "-t", "a", "-r", r"\9"]); self.assertEqual(c, 2)
    def test_json_and_stdin_and_limit(self):
        j = json.loads(run(["test", "a", "--stdin", "--format", "json", "--limit", "2"], stdin="aaaa")[1]); self.assertEqual(j[0]["count"], 2)
        self.assertEqual(run(["test", "a", "-t", "a", "--limit", "0"])[0], 2)
    def test_zero_width_match_terminates(self):
        self.assertEqual(len(find_matches(compile_pattern("x*"), "ab")), 3)
    def test_examples_and_flags_commands(self):
        c, o, _ = run(["examples"]); self.assertEqual(c, 0); self.assertIn("Email addresses", o); self.assertIn("ada@example.com", o)
        self.assertIn("IGNORECASE", run(["flags"])[1])
    def test_line_col(self): self.assertEqual(line_col("ab\ncd", 4), (2, 2))

    def test_broken_pipe_is_quiet(self):
        """Closing the reader early (like `| head`) must not print a traceback."""
        import subprocess, sys as _s
        env = {**os.environ, "PYTHONPATH": os.path.join(os.path.dirname(__file__), "..", "src")}
        pr = subprocess.Popen([_s.executable, "-m", "regexlab"] + ["examples"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        pr.stdout.close(); err = pr.stderr.read(); pr.stderr.close(); pr.wait()
        self.assertNotIn(b"Traceback", err); self.assertEqual(pr.returncode, 0)

if __name__ == "__main__": unittest.main()
