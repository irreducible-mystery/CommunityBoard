import sys, statistics
sys.path.insert(0, "/home/user/CommunityBoard/made")
import clearing
seeds = ["first-light","room-for-chance","quiet-hour-15","tetralemma"] + [chr(c) for c in range(ord("a"), ord("z")+1)] + [str(i) for i in range(1, 11)]
print("seeds", len(seeds))
for n in (1, 2, 3, 4, 6):
    cleared, lens, rej = 0, [], 0
    for s in seeds:
        f, log, outs = clearing.play(s, bots=n, steps=600)
        if f.cleared:
            cleared += 1
            lens.append(len(log))
        rej += sum(1 for o in outs if getattr(o, "rejected", False))
    med = statistics.median(lens) if lens else None
    print(f"rovers {n}: cleared {cleared} of {len(seeds)}, median moves {med}, rejected moves {rej}")
