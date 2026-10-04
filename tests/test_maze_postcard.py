"""Run with: python -m unittest discover -s tests"""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location(
    "maze", Path(__file__).resolve().parents[1] / "made" / "maze_postcard.py")
maze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(maze)


class MazeTests(unittest.TestCase):
    def test_perfect_maze_and_solution(self):
        for width, height in [(1, 1), (1, 9), (9, 1), (12, 16), (100, 100)]:
            for seed in [0, 42, -7]:
                graph = maze.make_maze(width, height, seed)
                seen, pending = set(), [0]
                while pending:
                    cell = pending.pop()
                    if cell in seen:
                        continue
                    seen.add(cell)
                    pending.extend(graph[cell] - seen)
                    for nxt in graph[cell]:
                        self.assertIn(cell, graph[nxt])
                        self.assertEqual(abs(cell % width - nxt % width)
                                         + abs(cell // width - nxt // width), 1)
                self.assertEqual(len(seen), width * height)
                self.assertEqual(sum(map(len, graph.values())), 2 * (len(graph) - 1))
                path = maze.solve(graph)
                self.assertEqual((path[0], path[-1]), (0, width * height - 1))
                for a, b in zip(path, path[1:]):
                    self.assertIn(b, graph[a])

    def test_svg_and_repeatability(self):
        svg = maze.render_svg(12, 16, 42)
        self.assertEqual(svg, maze.render_svg(12, 16, 42))
        self.assertNotEqual(svg, maze.render_svg(12, 16, 43))
        ns = {"s": "http://www.w3.org/2000/svg"}
        self.assertIsNone(ET.fromstring(svg).find("s:polyline", ns))
        self.assertIsNotNone(ET.fromstring(maze.render_svg(12, 16, 42, True)).find("s:polyline", ns))

    def test_invalid_dimensions(self):
        for w, h in [(0, 2), (2, -1), (101, 2)]:
            with self.assertRaises(ValueError):
                maze.make_maze(w, h, 42)

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "existing.svg"
            target.write_text("keep me", encoding="utf-8")
            with self.assertRaises(SystemExit) as error:
                maze.main(["--output", str(target)])
            self.assertEqual(error.exception.code, 2)
            self.assertEqual(target.read_text(encoding="utf-8"), "keep me")
