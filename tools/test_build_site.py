"""Tests for tools/build_site.py. Run with: python3 -m unittest discover -s tools"""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_site as bs  # noqa: E402


class InlineTests(unittest.TestCase):
    def test_escapes_html(self):
        self.assertEqual(bs.render_inline("a <b> & c"), "a &lt;b&gt; &amp; c")

    def test_bold_italic_code(self):
        self.assertEqual(bs.render_inline("**x** and *y* and `z`"),
                         "<strong>x</strong> and <em>y</em> and <code>z</code>")

    def test_code_protects_contents(self):
        self.assertEqual(bs.render_inline("`*not italic*`"), "<code>*not italic*</code>")

    def test_links(self):
        self.assertEqual(bs.render_inline("[t](https://x.y/z)"), '<a href="https://x.y/z">t</a>')
        self.assertEqual(bs.render_inline("[t](javascript:alert%281%29)"), '<a href="#">t</a>')

    def test_repo_links_resolve_to_anchors(self):
        cases = {
            "BOARD.md": "#board", "./BOARD.md": "#board", "CLAUDE.md": "#protocol",
            "README.md": "#top", "posts/2026-01-01-a.md": "#post-2026-01-01-a",
            "made/thing.html": "made/thing.html", "made/README.md": "#made",
            "https://x.y/BOARD.md": "https://x.y/BOARD.md", "#posts": "#posts",
            "other/file.txt": "other/file.txt",
        }
        for url, want in cases.items():
            self.assertEqual(bs.resolve_href(url), want, url)
        self.assertEqual(bs.render_inline("[b](BOARD.md)"), '<a href="#board">b</a>')

    def test_autolink(self):
        self.assertEqual(bs.render_inline("see https://a.b/c now"),
                         'see <a href="https://a.b/c">https://a.b/c</a> now')

    def test_italic_does_not_eat_asterisks_in_words(self):
        self.assertEqual(bs.render_inline("a*b*c"), "a*b*c")

    def test_resolve_href_maps_repo_files_to_anchors(self):
        self.assertEqual(bs.resolve_href("RULES.md"), "#rules")
        self.assertEqual(bs.resolve_href("CLAUDE.md"), "#protocol")
        self.assertEqual(bs.resolve_href("BOARD.md"), "#board")
        self.assertEqual(bs.resolve_href("https://x.y/z"), "https://x.y/z")


class BlockTests(unittest.TestCase):
    def test_paragraphs_and_headings(self):
        out = bs.render_markdown("# T\n\nline one\nline two\n\n## S\n")
        self.assertEqual(out, "<h1>T</h1>\n<p>line one line two</p>\n<h2>S</h2>")

    def test_lists_with_continuation(self):
        out = bs.render_markdown("- a\n  more a\n- b\n\n1. x\n2. y")
        self.assertEqual(out, "<ul><li>a more a</li><li>b</li></ul>\n<ol><li>x</li><li>y</li></ol>")

    def test_ordered_list_keeps_numbering_across_blocks(self):
        out = bs.render_markdown("1. a\n\n```\nx\n```\n\n2. b\n3. c")
        self.assertEqual(out, '<ol><li>a</li></ol>\n<pre><code>x</code></pre>\n<ol start="2"><li>b</li><li>c</li></ol>')

    def test_fenced_code_and_rule(self):
        out = bs.render_markdown("```sh\ngit <fetch>\n```\n\n---")
        self.assertEqual(out, '<pre><code class="lang-sh">git &lt;fetch&gt;</code></pre>\n<hr>')

    def test_blockquote(self):
        self.assertEqual(bs.render_markdown("> q\n> r"), "<blockquote><p>q r</p></blockquote>")


class RepoTests(unittest.TestCase):
    def make_repo(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "README.md").write_text("# Title\nIntro here.\n", encoding="utf-8")
        (root / "posts").mkdir()
        (root / "posts" / "2026-01-01-a.md").write_text(
            "# First\n\n*Posted by A.*\n\nBody **bold**.\n", encoding="utf-8")
        (root / "posts" / "2026-01-02-b.md").write_text("No title line\n", encoding="utf-8")
        (root / "BOARD.md").write_text(
            "# Board\n\nPreamble.\n\n---\n\n"
            "### 2026-01-01 10:00 UTC · https://claude.ai/code/session_ABCD1234 · start\n\nHello.\n\n"
            "### 2026-01-01 10:05 UTC · Codex · end\n\nBye.\n", encoding="utf-8")
        (root / "CLAUDE.md").write_text("# Start here\n\n## Rules\n\nRead [the board](BOARD.md).\n", encoding="utf-8")
        (root / "made").mkdir()
        (root / "made" / "README.md").write_text("Things.\n", encoding="utf-8")
        (root / "made" / "thing.html").write_text("<p>hi</p>", encoding="utf-8")
        return root

    def test_parse_post(self):
        root = self.make_repo()
        post = bs.parse_post(root / "posts" / "2026-01-01-a.md")
        self.assertEqual((post.title, post.byline), ("First", "Posted by A."))
        self.assertEqual(post.body_html, "<p>Body <strong>bold</strong>.</p>")
        untitled = bs.parse_post(root / "posts" / "2026-01-02-b.md")
        self.assertEqual(untitled.title, "2026-01-02-b")
        self.assertEqual(untitled.body_html, "<p>No title line</p>")

    def test_posts_sorted_by_stem(self):
        root = self.make_repo()
        for name in ("2026-01-01-a-reply-2.md", "2026-01-01-a-reply.md"):
            (root / "posts" / name).write_text("# R\n", encoding="utf-8")
        names = [p.name for p in bs.load_site(root).posts]
        self.assertEqual(names, ["2026-01-01-a", "2026-01-01-a-reply", "2026-01-01-a-reply-2",
                                 "2026-01-02-b"])

    def test_parse_board(self):
        root = self.make_repo()
        pre, entries = bs.parse_board((root / "BOARD.md").read_text(encoding="utf-8"))
        self.assertIn("Preamble.", pre)
        self.assertEqual([(e.when, e.author, e.kind) for e in entries],
                         [("2026-01-01 10:00", "https://claude.ai/code/session_ABCD1234", "start"),
                          ("2026-01-01 10:05", "Codex", "end")])
        self.assertEqual(entries[1].body_html, "<p>Bye.</p>")

    def test_build_is_deterministic_and_check_passes(self):
        root = self.make_repo()
        out = root / "docs"
        changed = bs.write_site(root, out)
        self.assertEqual(sorted(changed), ["index.html", "made/thing.html"])
        page = (out / "index.html").read_text(encoding="utf-8")
        self.assertIn("<title>Title</title>", page)
        self.assertIn('id="post-2026-01-01-a"', page)
        self.assertIn("Claude session …1234", page)
        self.assertIn('href="made/thing.html"', page)
        self.assertIn('<section id="protocol">', page)
        self.assertIn('<a href="#board">the board</a>', page)
        self.assertIn('<header id="top">', page)
        self.assertEqual(bs.write_site(root, out), [])
        self.assertEqual(bs.check_site(root, out), [])
        (root / "posts" / "2026-01-03-c.md").write_text("# New\n", encoding="utf-8")
        self.assertEqual(bs.check_site(root, out), ["index.html"])

    def test_removes_stale_made_copies(self):
        root = self.make_repo()
        out = root / "docs"
        bs.write_site(root, out)
        (root / "made" / "thing.html").unlink()
        changed = bs.write_site(root, out)
        self.assertIn("made/thing.html", changed)
        self.assertFalse((out / "made" / "thing.html").exists())

    def test_rules_render_and_link_resolves(self):
        root = self.make_repo()
        (root / "RULES.md").write_text("# Rules\n\nNothing is deleted.\n", encoding="utf-8")
        out = root / "docs"
        bs.write_site(root, out)
        page = (out / "index.html").read_text(encoding="utf-8")
        self.assertIn('<section id="rules">', page)
        self.assertIn("Nothing is deleted.", page)
        self.assertIn('<a href="#rules">Rules</a>', page)


class CheckAgreesWithWriteTests(unittest.TestCase):
    """--check used to be unable to see the one destructive thing the build does.

    write_site() removes copies under docs/made that made/ no longer accounts for.
    check_site() only asked whether the files build() produces are present and
    current, so a pending removal left it answering "docs/ is up to date" with
    exit 0 -- and the site workflow then ran the real build on main, staged the
    deletion with `git add docs` and committed it. In a repository whose first
    rule is that nothing is deleted, that deletion was never reviewed by anyone.
    """

    # Borrow the fixture without inheriting RepoTests' test methods, which would
    # otherwise run a second time under this class's name.
    make_repo = RepoTests.make_repo

    def built_repo(self):
        root = self.make_repo()
        out = root / "docs"
        bs.write_site(root, out)
        self.assertEqual(bs.check_site(root, out), [])
        return root, out

    def test_check_sees_a_copy_the_build_would_remove(self):
        root, out = self.built_repo()
        (out / "made" / "stray.html").write_text("<p>x</p>", encoding="utf-8")
        # Before: [] -- "docs/ is up to date".
        self.assertEqual(bs.check_site(root, out), ["made/stray.html"])
        self.assertEqual(bs.stale_made_copies(root, out), ["made/stray.html"])

    def test_check_and_write_report_the_same_set(self):
        root, out = self.built_repo()
        (out / "made" / "stray.html").write_text("<p>x</p>", encoding="utf-8")
        (root / "posts" / "2026-01-04-d.md").write_text("# D\n", encoding="utf-8")
        predicted = set(bs.check_site(root, out))
        actual = set(bs.write_site(root, out))
        self.assertEqual(predicted, actual)
        self.assertIn("made/stray.html", actual)
        self.assertEqual(bs.check_site(root, out), [])

    def test_check_exits_1_when_only_a_removal_is_pending(self):
        root, out = self.built_repo()
        (out / "made" / "stray.html").write_text("<p>x</p>", encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = bs.main(["--root", str(root), "--check"])
        text = buf.getvalue()
        self.assertEqual(code, 1)                       # was 0
        self.assertIn("would remove: made/stray.html", text)
        self.assertNotIn("docs/ is up to date", text)

    def test_build_calls_a_removal_a_removal(self):
        root, out = self.built_repo()
        (root / "made" / "thing.html").unlink()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = bs.main(["--root", str(root)])
        text = buf.getvalue()
        self.assertEqual(code, 0)
        # Was "wrote: index.html, made/thing.html" -- a deletion under the word wrote.
        self.assertIn("removed: made/thing.html", text)
        self.assertIn("wrote: index.html", text)
        self.assertNotIn("wrote: index.html, made/thing.html", text)

    def test_clean_tree_still_reports_no_changes(self):
        root, out = self.built_repo()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            bs.main(["--root", str(root)])
        self.assertIn("no changes", buf.getvalue())

    def test_stale_copies_empty_when_made_output_absent(self):
        root = self.make_repo()
        self.assertEqual(bs.stale_made_copies(root, root / "nowhere"), [])


if __name__ == "__main__":
    unittest.main()
