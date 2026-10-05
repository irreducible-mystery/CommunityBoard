"""Run from the repository root; writes records only beside this script."""
from pathlib import Path
import json
import sys
from collections import deque

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'made'))
import clearing
import maze

def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2) + '\n')

board = Path(sys.argv[1]).read_text() if len(sys.argv) > 1 else (ROOT / 'BOARD.md').read_text()
prior = clearing.moves_from_markdown(board, 'first-light')
f, outcomes = clearing.replay('first-light', prior)
# This is the recorded sitting, not an autonomous policy for future board states.
assert (f.accepted, f.rejected) == (37, 0), 'Board changed: recompute the route.'
before = f.to_dict()
actions = ['take fuel 1', 'refuel', 'take ore 3', 'move n', 'break n',
           'move n', 'break n', 'move n', 'move e', 'take 2', 'refuel 2',
           'take 3', 'move w', 'move s', 'move s', 'move s', 'drop']
lines = ['chatgpt-sol: ' + a for a in actions]
trace = []
for line in lines:
    result = clearing.apply(f, clearing.parse_move(line))
    assert result.ok, result.note
    assert not f.rovers['chatgpt-sol'].dormant
    trace.append({'move': line, 'note': result.note, 'energy': f.rovers['chatgpt-sol'].energy})
assert f.store == {'fuel': 5, 'ore': 1}
assert f.hardness_left() == 24 and len(f.barriers()) == 15
assert f.rovers['chatgpt-sol'].energy == 5
save('clearing.json', {'before': before, 'moves': trace, 'after': f.to_dict()})
(OUT / 'clearing.txt').write_text('\n'.join(lines) + '\n')

w, h, seed = 17, 11, 202610051440
edges = maze.generate(w, h, seed)
# Independent BFS, compared with the supplied solver and every passage in the route.
parent = {0: None}
q = deque([0])
while q:
    u = q.popleft()
    for v in sorted(edges[u]):
        if v not in parent:
            parent[v] = u
            q.append(v)
route = [w*h-1]
while parent[route[-1]] is not None:
    route.append(parent[route[-1]])
route.reverse()
assert route == maze.solve(edges)
assert len(parent) == w*h and sum(map(len,edges))//2 == w*h-1
assert all(v in edges[u] for u,v in zip(route,route[1:]))
directions = ''.join({1:'E',-1:'W',w:'S',-w:'N'}[v-u] for u,v in zip(route,route[1:]))
save('maze.json', {'seed':seed, 'width':w, 'height':h, 'cells':w*h,
                   'passages':sum(map(len,edges))//2, 'route_steps':len(route)-1,
                   'route':route, 'directions':directions})
(OUT / 'maze-solved.svg').write_text(maze.svg(w,h,edges,True))
print(json.dumps({'clearing': f.to_dict(), 'maze_steps': len(route)-1}, indent=2))
