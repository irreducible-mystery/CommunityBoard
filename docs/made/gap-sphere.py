#!/usr/bin/env python3
"""The gap equation on integer quaternions, and where the sphere actually is.

x * x = x + G.

Over the integers, G an integer and x = a + bi + cj + dk with a,b,c,d
integers: the imaginary part of the equation is (2a - 1) * t = 0 for each
imaginary component t. No integer a has 2a = 1, so every integral solution
is real, and then G = a * (a - 1). i itself squares to -1 and solves nothing.

Over the reals the collision is allowed. Set a = 1/2. Then every imaginary
part satisfies the equation, and G = -1/4 - (b² + c² + d²). That set is a
point when G = -1/4, a 2-sphere when G < -1/4, and empty when G > -1/4.
Same cut the gap notes already use for the two roots being real.

A rational point on that sphere is a further question. 7 is not a sum of
three integer squares, so G = -2 has real solutions and no solution whose
doubled coordinates are integers. This file does not claim one.

Standard library only. The box is a check. The factor (2a - 1) * t = 0 is
what the box is checking, and it does not depend on the box. Not a Lean proof.
"""

from __future__ import annotations

from fractions import Fraction


def mul(x, y):
    a, b, c, d = x
    e, f, g, h = y
    return (
        a * e - b * f - c * g - d * h,
        a * f + b * e + c * h - d * g,
        a * g - b * h + c * e + d * f,
        a * h + b * g - c * f + d * e,
    )


def integer_box(limit: int = 6):
    hits = 0
    nonreal = 0
    for a in range(-limit, limit + 1):
        for b in range(-limit, limit + 1):
            for c in range(-limit, limit + 1):
                for d in range(-limit, limit + 1):
                    square = mul((a, b, c, d), (a, b, c, d))
                    if square[1] == b and square[2] == c and square[3] == d:
                        hits += 1
                        g = square[0] - a
                        if (2 * a - 1) * b or (2 * a - 1) * c or (2 * a - 1) * d:
                            raise SystemExit("factor failed on a hit")
                        if (b, c, d) != (0, 0, 0):
                            nonreal += 1
                        elif g != a * (a - 1):
                            raise SystemExit(f"real solution G={g} != a(a-1) at a={a}")
    return hits, nonreal


def half_line(b, c, d):
    """a = 1/2. Returns G, and checks the imaginary part matches on its own."""
    a = Fraction(1, 2)
    x = (a, Fraction(b), Fraction(c), Fraction(d))
    square = mul(x, x)
    if square[1:] != x[1:]:
        raise SystemExit(f"half-line imaginaries moved: {square[1:]} != {x[1:]}")
    g = square[0] - a
    norm = x[1] * x[1] + x[2] * x[2] + x[3] * x[3]
    if g != -Fraction(1, 4) - norm:
        raise SystemExit(f"G={g} != -1/4 - norm ({norm})")
    return g, norm


def main():
    hits, nonreal = integer_box()
    print(f"integer box |coord|<=6: solutions {hits}, non-real {nonreal}")
    if hits != 13 or nonreal != 0:
        raise SystemExit("expected 13 real solutions (a from -6 to 6) and no others")
    i_squared = mul((0, 1, 0, 0), (0, 1, 0, 0))
    print(f"i*i = {i_squared}; i + G always has imaginary part 1, so i solves nothing")
    if i_squared != (-1, 0, 0, 0):
        raise SystemExit("quaternion multiplication disagrees on i")

    print("reals, a = 1/2. G = -1/4 - (b²+c²+d²):")
    samples = [(0, 0, 0), (Fraction(1, 2), 0, 0), (1, 0, 0), (1, 1, 1), (Fraction(1, 3), Fraction(1, 5), 2)]
    for b, c, d in samples:
        g, norm = half_line(b, c, d)
        if norm == 0:
            kind = "point"
        else:
            kind = "sphere"
        print(f"  b,c,d = ({b}, {c}, {d})  norm={norm}  G={g}  {kind}")
        if norm == 0 and g != -Fraction(1, 4):
            raise SystemExit("zero norm should be the branch point")
        if norm > 0 and not g < -Fraction(1, 4):
            raise SystemExit("positive norm should sit strictly below -1/4")

    # G = -2 asks for doubled-norm 7, which is 8*0+7, not a sum of three integer squares.
    print("G=-2: real sphere of squared-radius 7/4; 7 is not a sum of three integer squares")
    if any(p * p + q * q + r * r == 7 for p in range(3) for q in range(3) for r in range(3)):
        raise SystemExit("7 became a sum of three squares")
    print("PASS")


if __name__ == "__main__":
    main()
