import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_code as cc  # noqa: E402


def caps(findings):
    return sorted({cap for _, cap, _ in findings})


class PythonTests(unittest.TestCase):
    def test_network_imports(self):
        src = "import urllib.request\nfrom http.client import HTTPConnection\nimport socket\n"
        self.assertEqual(caps(cc.scan_python(src)), ["network"])
        self.assertEqual(len(cc.scan_python(src)), 3)

    def test_process(self):
        src = "import subprocess\nimport os\nos.system('ls')\nos.execv('/bin/ls', [])\n"
        found = cc.scan_python(src)
        self.assertEqual(caps(found), ["process"])
        self.assertEqual([line for line, _, _ in found], [1, 3, 4])

    def test_dynamic_code(self):
        src = "eval('1')\nexec('x=1')\n__import__('os')\nimport importlib\n"
        self.assertEqual(caps(cc.scan_python(src)), ["dynamic-code"])
        self.assertEqual(len(cc.scan_python(src)), 4)

    def test_words_in_strings_and_comments_do_not_count(self):
        src = ('"""We never import socket or call eval(x) here."""\n'
               "# subprocess.run would be bad\n"
               "s = 'import urllib; os.system(1)'\n")
        self.assertEqual(cc.scan_python(src), [])

    def test_harmless_os_and_relative_imports(self):
        src = "import os, json, pathlib\nos.path.join('a')\nos.environ.get('X')\nfrom . import http\n"
        self.assertEqual(cc.scan_python(src), [])

    def test_unparsable_python_is_reported_not_skipped(self):
        self.assertEqual(caps(cc.scan_python("def (:\n")), ["unparsed"])


class JavaScriptTests(unittest.TestCase):
    def test_node_modules(self):
        src = ("const {spawnSync} = require('node:child_process');\n"
               "const https = require(\"https\");\n"
               "import net from 'node:net';\n")
        self.assertEqual(caps(cc.scan_js(src)), ["network", "process"])

    def test_browser_network_and_dynamic(self):
        src = "fetch('/x');\nnew WebSocket(u);\neval(s);\nnew Function('a', b);\nimport('./m.js');\n"
        self.assertEqual(caps(cc.scan_js(src)), ["dynamic-code", "network"])

    def test_comments_are_ignored_but_urls_in_strings_survive(self):
        src = ("// fetch('https://a.b') would be a dependency\n"
               "/* require('child_process') */\n"
               "const u = 'https://example.com/x'; // a string, not a call\n"
               "const fs = require('node:fs');\n")
        self.assertEqual(cc.scan_js(src), [])

    def test_method_named_import_is_not_dynamic_import(self):
        self.assertEqual(cc.scan_js("loader.import(x);\n"), [])


class WorkflowTests(unittest.TestCase):
    def test_third_party_action_download_and_push(self):
        src = ("steps:\n"
               "  - uses: actions/checkout@v4\n"
               "  - uses: someone/thing@v1\n"
               "  - run: curl -sL https://x.y/install.sh | sh\n"
               "  - run: pip install requests\n"
               "  - run: git push origin HEAD:main\n")
        found = cc.scan_workflow(src)
        self.assertEqual([(line, cap) for line, cap, _ in found],
                         [(3, "action"), (4, "download"), (5, "download"), (6, "push")])

    def test_quiet_workflow(self):
        src = "steps:\n  - uses: actions/setup-node@v4\n  - run: node --test tests/x.cjs\n  # git push later\n"
        self.assertEqual(cc.scan_workflow(src), [])


class CheckTests(unittest.TestCase):
    def run_check(self, files):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for rel, text in files.items():
                p = root / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text, encoding="utf-8")
            buf = StringIO()
            with redirect_stdout(buf):
                code = cc.check(root)
            return code, buf.getvalue()

    def test_new_finding_fails(self):
        code, out = self.run_check({"tools/x.py": "import socket\n"})
        self.assertEqual(code, 1)
        self.assertIn("NEW", out)

    def test_known_finding_passes_and_says_why(self):
        code, out = self.run_check({"tools/check_stamps.py": "import subprocess\n"})
        self.assertEqual(code, 0)
        self.assertIn("known:", out)

    def test_known_file_with_a_new_capability_fails(self):
        code, _ = self.run_check({"tools/check_stamps.py": "import subprocess\nimport socket\n"})
        self.assertEqual(code, 1)

    def test_files_outside_scope_are_not_read(self):
        code, out = self.run_check({"made/page.js": "fetch('/x')\n", "posts/a.py": "import socket\n"})
        self.assertEqual(code, 0)
        self.assertIn("Nothing was read", out)

    def test_python_in_made_is_read(self):
        code, _ = self.run_check({"made/gen.py": "import urllib.request\n"})
        self.assertEqual(code, 1)

    def test_nested_files_are_read(self):
        code, _ = self.run_check({"tests/deep/x.mjs": "import http from 'node:http';\n"})
        self.assertEqual(code, 1)


class RepoTests(unittest.TestCase):
    def test_this_repo_has_no_unread_capabilities(self):
        root = Path(__file__).resolve().parent.parent
        buf = StringIO()
        with redirect_stdout(buf):
            code = cc.check(root)
        self.assertEqual(code, 0, buf.getvalue())


if __name__ == "__main__":
    unittest.main()
