# The parapet

A low wall that accepts a merlon only on the open beat and only opposite the last accepted side.

A merlon is L or R. It is accepted only on the open beat, and only on the side that did not take the previous accepted merlon. The first accepted merlon may be either side. The beat advances on every line, accepted or rejected. The parapet draws when each side has taken two merlons. An off-beat merlon, a same-side repeat, or a word that is not L or R is kept and marked rejected.

`python3 made/the-parapet.py check` prints PASS.

Nothing is deleted from the record.
