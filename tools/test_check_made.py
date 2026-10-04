"""Tests for tools/check_made.py. Run with: python3 -m unittest discover -s tools"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_made as cm  # noqa: E402


def write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


class ScanTests(unittest.TestCase):
    def scan(self, html: str) -> list[str]:
        root = Path(tempfile.mkdtemp())
        write(root, "page.html", html)
        return [kind for _, kind, _ in cm.scan_html(root / "page.html")]

    def test_clean_page_has_no_problems(self):
        self.assertEqual(self.scan("<script>var x = 1; // fetch the next frame\n</script>"), [])

    def test_prose_mentioning_fetch_is_not_flagged(self):
        self.assertEqual(self.scan("<p>We fetch nothing. XMLHttpRequest is a word.</p>"), [])

    def test_remote_src_and_link(self):
        kinds = self.scan('<link rel="stylesheet" href="https://a.b/x.css">'
                          '<script src="//cdn.a.b/l.js"></script>')
        self.assertEqual(sorted(kinds), ["<link href>", "src"])

    def test_local_src_and_data_uri_are_fine(self):
        self.assertEqual(self.scan('<img src="data:image/png;base64,AAAA"><script src="./l.js"></script>'), [])

    def test_srcset_object_poster(self):
        kinds = self.scan('<img srcset="a.png 1x, https://a.b/c.png 2x">'
                          '<object data="https://a.b/o.svg"></object>'
                          '<video poster="//a.b/p.jpg"></video>')
        self.assertEqual(sorted(kinds), ["data", "poster", "srcset"])

    def test_css_import_and_url(self):
        kinds = self.scan('<style>@import url("https://f.a/x.css"); body{background:url(//i.a/b.png)}</style>')
        self.assertEqual(sorted(kinds), ["@import", "url()"])

    def test_network_calls(self):
        kinds = self.scan("<script>fetch('/x'); new WebSocket('wss://a.b'); new EventSource('/e');"
                          " navigator.sendBeacon('/b'); import('https://a.b/m.js');</script>")
        self.assertEqual(kinds.count("network call"), 5)
        self.assertIn("url in script string", kinds)

    def test_url_in_script_string(self):
        kinds = self.scan("<script>var api = 'https://api.example.com/v1';</script>")
        self.assertEqual(kinds, ["url in script string"])

    def test_outbound_anchor_links_are_allowed(self):
        self.assertEqual(self.scan('<a href="https://example.com">Reading</a>'), [])

    def test_unquoted_and_entity_encoded_src(self):
        self.assertEqual(self.scan("<script src=https://example.com/x.js></script>"), ["src"])
        self.assertEqual(self.scan('<script src="https&#58;//example.com/x.js"></script>'), ["src"])

    def test_inline_style_attribute(self):
        self.assertEqual(self.scan('<div style="background:url(https://a.b/x.png)"></div>'), ["url()"])


class IndexTests(unittest.TestCase):
    def test_hidden_ancestor_does_not_skip_everything(self):
        base = Path(tempfile.mkdtemp())
        root = base / ".checkout"
        write(root, "made/README.md", "")
        write(root, "made/bad.html", '<script src="https://example.com/x.js"></script>')
        self.assertEqual(cm.list_items(root / "made"), ["bad.html"])
        import contextlib, io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cm.check(root), 1)
        self.assertIn("1 page(s) checked, 2 problem(s)", out.getvalue())

    def test_hidden_files_inside_made_are_skipped(self):
        root = Path(tempfile.mkdtemp())
        write(root, "made/.draft/x.html", "<p>x</p>")
        write(root, "made/ok.html", "<p>x</p>")
        self.assertEqual(cm.list_items(root / "made"), ["ok.html"])

    def test_exact_name_match_not_substring(self):
        names = cm.index_names("- `data.py` does things; see [notes](docs/notes.md)")
        self.assertEqual(names, {"data.py", "docs/notes.md"})
        self.assertNotIn("a.py", names)

    def test_check_reports_missing_and_stale(self):
        root = Path(tempfile.mkdtemp())
        write(root, "made/README.md", "- `one.html` here\n- `gone.html` was here\n- [two](sub/two.html)\n")
        write(root, "made/one.html", "<p>ok</p>")
        write(root, "made/sub/two.html", "<p>ok</p>")
        write(root, "made/three.py", "print(1)\n")
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = cm.check(root)
        text = out.getvalue()
        self.assertEqual(status, 1)
        self.assertIn("sub/two.html", text)
        self.assertIn("missing from made/README.md: three.py", text)
        self.assertIn("named in made/README.md but absent: gone.html", text)
        self.assertIn("2 problem(s)", text)


if __name__ == "__main__":
    unittest.main()
