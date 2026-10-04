import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location('maze', Path(__file__).resolve().parents[1] / 'made' / 'maze.py')
maze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(maze)


class MazeTests(unittest.TestCase):
    def test_connected_tree_and_valid_route(self):
        for width, height in ((1, 1), (1, 9), (9, 1), (20, 14), (100, 100)):
            edges = maze.generate(width, height, 42)
            seen, stack = {0}, [0]
            while stack:
                cell = stack.pop()
                for other in edges[cell]:
                    self.assertIn(cell, edges[other])
                    x, y = cell % width, cell // width
                    ox, oy = other % width, other // width
                    self.assertEqual(abs(x - ox) + abs(y - oy), 1)
                    if other not in seen:
                        seen.add(other)
                        stack.append(other)
            self.assertEqual(len(seen), width * height)
            self.assertEqual(sum(map(len, edges)), 2 * (width * height - 1))
            route = maze.solve(edges)
            self.assertEqual((route[0], route[-1]), (0, width * height - 1))
            for a, b in zip(route, route[1:]):
                self.assertIn(b, edges[a])
            ET.fromstring(maze.svg(width, height, edges, True))

    def test_seed_is_repeatable(self):
        self.assertEqual(maze.generate(20, 14, 42), maze.generate(20, 14, 42))
        self.assertNotEqual(maze.generate(20, 14, 42), maze.generate(20, 14, 43))


if __name__ == '__main__':
    unittest.main()
