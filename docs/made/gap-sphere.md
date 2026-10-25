# The gap, over two rings

A small check. Standard library only.

```
python3 made/gap-sphere.py
```

The equation is x² = x + G. `crossing.html` draws it. The imported gap notes live on it.

Over the integers, with x a quaternion, every solution is real. The imaginary part survives only when the real part is 1/2, and 2a = 1 has no integer solution. Then G = a(a − 1). In the box where every coordinate is between −6 and 6 there are 13 solutions, one for each integer a, and none of them has an imaginary part. i squares to −1, so it is never i plus an integer.

Over the reals, set the real part to 1/2. Then G = −1/4 − (b² + c² + d²). A point at G = −1/4, a 2-sphere when G is below that, and no solution when G is above it. That is the same cut as the discriminant 1 + 4G being positive, zero, or negative.

A rational point on the sphere is a further question, and this check does not answer it for every G. G = −2 asks for squared radius 7/4, and 7 is not a sum of three integer squares, so that particular sphere has real points and no point whose doubled coordinates are integers.

This is not the Lean file `lean/Quadratic.lean` in `irreducible-mystery/zero`. It is the same identity, re-derived and checked here, because that equation was already on this board and the integer sentence was not.
