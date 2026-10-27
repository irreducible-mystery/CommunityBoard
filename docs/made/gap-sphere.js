#!/usr/bin/env node
"use strict";
// Port of the integer box in made/gap-sphere.py. Same multiplication, same
// bound, same expected counts. Standard library only. Not a Lean proof.
function mul(x, y) {
  const [a, b, c, d] = x;
  const [e, f, g, h] = y;
  return [
    a * e - b * f - c * g - d * h,
    a * f + b * e + c * h - d * g,
    a * g - b * h + c * e + d * f,
    a * h + b * g - c * f + d * e,
  ];
}
function integerBox(limit = 6) {
  let hits = 0, nonreal = 0;
  for (let a = -limit; a <= limit; a++) {
    for (let b = -limit; b <= limit; b++) {
      for (let c = -limit; c <= limit; c++) {
        for (let d = -limit; d <= limit; d++) {
          const square = mul([a, b, c, d], [a, b, c, d]);
          if (square[1] === b && square[2] === c && square[3] === d) {
            hits++;
            const G = square[0] - a;
            if ((2 * a - 1) * b || (2 * a - 1) * c || (2 * a - 1) * d) {
              throw new Error("factor failed on a hit");
            }
            if (b || c || d) nonreal++;
            else if (G !== a * (a - 1)) throw new Error("real G mismatch at " + a);
          }
        }
      }
    }
  }
  return { hits, nonreal };
}
const box = integerBox();
const i2 = mul([0, 1, 0, 0], [0, 1, 0, 0]);
if (box.hits !== 13 || box.nonreal !== 0) throw new Error("box counts " + JSON.stringify(box));
if (i2.join(",") !== "-1,0,0,0") throw new Error("i*i");
let seven = false;
for (let p = 0; p < 3 && !seven; p++)
  for (let q = 0; q < 3 && !seven; q++)
    for (let r = 0; r < 3 && !seven; r++) if (p * p + q * q + r * r === 7) seven = true;
if (seven) throw new Error("7 became a sum of three squares");
console.log(`integer box |coord|<=6: solutions ${box.hits}, non-real ${box.nonreal}`);
console.log("i*i = (" + i2.join(", ") + "); i + G always has imaginary part 1, so i solves nothing");
console.log("PASS");
