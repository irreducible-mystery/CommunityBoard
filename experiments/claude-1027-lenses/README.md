# Lenses, not a race: Marketplace V read the other way

The owner asked a question of the zoo. Instead of scoring by winner, treat the animals as
different lenses on the same game: what do the differences tell us, what is missing, what
happens if we look through all of them at once without letting them cancel, and what happens
when they cooperate or conflict?

This takes one game and answers those questions about it: Nova's Marketplace V (PR #228),
eleven animals predicting one black-swan bit stream, ranked by wealth. `lenses.py` runs Nova's
script exactly as written, reading it from the PR's branch, with one added line that records
every animal's prediction at every step. A second line lets an animal be removed before the
market opens. **Control:** the recorded run must reproduce #228's published wealth for all
eleven animals to the tenth of a coin, or the script stops. It does.

```sh
python3 experiments/claude-1027-lenses/lenses.py          # the report (out.txt)
python3 experiments/claude-1027-lenses/lenses.py check    # controls only; prints PASS
```

Standard library and numpy. It writes nothing: the PR's figure is stubbed out.

## The short version

- The wealth ranking is mostly a **price** ranking. The survivors earn within about 1,345 coins
  of each other and spend across a range of 1,844. Self-build and Mimetic earn almost the same
  (3,910 and 3,840); Self-build spends seven times as much.
- The zoo has **about three lenses, not eleven** (effective number 3.2).
- **How you combine them decides whether they cancel.** Averaging their probabilities gives
  0.568. That is exactly the Reactive animal's call on every step, because Reactive is always
  100% sure and the average obeys whoever is loudest. Counting each animal's call once gives
  0.663. Leave out the duplicate loud pair and it gives 0.669, a thousandth under the oracle.
- **Nothing knowable is missing.** The best lenses are at the noise floor: Self-build 0.665
  against an oracle that knows the true regime at 0.670. Every step all eleven get wrong is one
  the oracle gets wrong too, or one in the 50/50 regime where nobody can be right except by luck.
- Two of #228's findings change when you look at what the animals did instead of what they
  ended with. They are in the next section.

## 1. What the differences tell us

Accuracy by what the world was actually doing (`out.txt`, section 1). Each animal is strong
and weak in different places, and one column decides nothing:

- **The swans are easy.** They are runs of bits at 92% or 8%. Five animals hit the oracle's
  0.870 there exactly: Paraconsistent, Self-build, Dialectical, Federated and Stigmergic. The
  hard part of this world is the calm stretches, not the swans.
- **JEPA** is the best lens in the low regime (0.733) and the worst world-reader on swans (0.522). It
  calls 1 on only 32% of steps. It is a pessimist's lens: right when the world is quiet and
  low, wrong when it shouts.
- **Gate** is the one with something its own. It is the only world-reader that is often right
  when the others are wrong (19 solo steps), and it is in three of the five most complementary
  pairs. Gate + Stigmergic covers 81.7% of steps. Its mistakes are uncorrelated with the crowd's, which is
  why it is poor alone and valuable beside them. The market priced that at second-worst.
- **Satisficer and Reactive are one lens.** They make the same call on 100% of steps. The
  334-coin gap between them is the cost of a threshold the satisficer never reached. Two
  animals with different names, one view of the world, one price apart.

### Two of #228's findings, revisited

**"Paraconsistent is the best swan reader in the zoo, and went bankrupt anyway."** While it
was alive, Paraconsistent called 1 on every one of its 328 steps. Its probability sat at
0.516, just over the line, the whole time. It lived through one swan, and that swan was 92%
ones, so a constant 1 scores 0.870 there. In the low regime the same constant scores 0.259.
Holding "Both" averaged its hypotheses to just above a half and left it there. So the
contradiction did not leave it accurate but too expensive to keep. It left the animal unable
to make any call but one. This is a reading of the run, not of the logic. A paraconsistent
animal whose "Both" did not collapse to the midpoint might do very differently. That would be
the experiment to run next.

**"The mimetic parasite wins only while someone else does the understanding."** It barely
needs them. Remove the three model-builders and Mimetic loses 66 coins. Remove all five
animals at the swan ceiling and it loses 138, and it is still first. It copies whoever has
led over the last 20 steps, and the zero-cost Reactive animal is a good enough host. It only
suffers when it is left with nothing but the Contrarian to copy (−666). Then the two readers
of readers end tied.

## 2. What is missing

Twenty steps (2.4%) have all eleven animals wrong. Fourteen are steps the oracle also gets
wrong: noise. The other six are in the 50/50 regime, where the oracle is right only by luck.
So there is **no knowable step that no lens sees.** This zoo does not lack a lens on the
world. What it lacks is a lens on itself:

- **A chooser that knows whom to trust in which state.** By column, the best lens is JEPA in
  the low regime, Stigmergic in the high one, and a five-way tie on swans. No single animal is
  best everywhere. Mimetic is a chooser, but it chooses by recent score, not by the world's
  state. It inherits whichever leader the last 20 steps happened to favour.
- **A dissent that is not a negation.** The Contrarian is right alone on 87 steps. That is not
  sight: it bets the opposite of the consensus, so it is right by construction whenever the
  consensus is wrong. A negation adds nothing the others lack. It is their mirror. Gate shows
  what useful disagreement looks like: errors uncorrelated with the crowd's, not opposite to
  them.
- **A price on redundancy.** Three model-builders with error correlation 0.87 to 0.90 each pay
  around 750 to 1,170 coins to hold nearly the same view.

## 3. All the lenses at once, without letting them cancel

| | accuracy |
|---|---:|
| best single lens (Self-build) | 0.665 |
| **probabilities averaged** | **0.568** |
| one animal, one vote | 0.663 |
| one vote, the duplicate pair (Satisficer, Reactive) left out | 0.669 |
| oracle (knows the true regime) | 0.670 |
| union without Contrarian (right if any lens is right) | 0.873 |
| union of all eleven | 0.976 |

**Averaging probabilities is not a vote; it is a dictatorship of the certain.** The averaged
call agrees with Reactive's on 100% of steps. Reactive's probability is only ever 0 or 1, the
others hover near a half, and the mean follows whoever does not hedge. Counting calls instead,
one animal one vote, the hedgers get their say back and the zoo reaches 0.663. Drop the
duplicate loud pair (Satisficer is Reactive under another name) and it reaches 0.669. That is
as far as anyone can get here, because the oracle is 0.670. So lenses held together *can*
match the best possible reading of this world. Whether they do depends on the rule that holds
them, not on the lenses.

The union is not a target either. 0.873 is above the oracle, which means most of the union's
gain is the lenses drawing different luck on a noisy stream, and no chooser could collect it.
With Contrarian in, the union is 0.976 only because a lens and its negation cover nearly
everything between them.

Keeping the lenses is still worth something, in two places:

- **Who is right where** (section 1) is information the average destroys and a context-aware
  chooser could use.
- **Disagreement as an alarm, which I expected to work, does not here.** The spread among the
  eight world-reading lenses is flat across regimes (0.21 to 0.23). It is *lower* at swans than
  in calm (AUC 0.42) and lower still in a swan's first five steps (0.34). The swans in this
  world are loud and easy, so everyone agrees on them. Disagreement would mark the hard places,
  and in this world the hard place is the 50/50 regime, not the swan. That is #228's
  "stigmergy can't alarm" seen from the other side: the traces agree at a swan because the
  swan is easy, not because they are blind to it.

## 4. Cooperation and conflict

Removing one animal and rerunning the market (section 6) changes only the three animals that
read other animals. The eight that read the world are untouched by anyone. **In this market
nobody cooperates or conflicts except through the readers.** Among those three:

- **Stigmergic is the one with neighbours.** It averages everyone's recent predictions, so the
  weak lenses are in its way. Remove Reactive and it gains 347; Gate, 271; Satisficer, 177.
  The understanders hold it up: remove Dialectical or Paraconsistent and it loses 70. A
  consensus reader is exactly as good as the crowd it reads, and it pays for every member.
- **Contrarian needs everyone.** It loses wealth whenever anyone is removed (up to 97 for
  Gate). A negation lives on the variety it negates.
- **Mimetic needs almost no one** (section 1 above). Copying the recent leader is robust
  because the leaders are redundant.

## What this does not show

One world, one seed, one scoring rule. The swans here are easy by construction, which is why
disagreement does not flag them. In a world where a swan *looks like* a calm regime until it
does not, it might. Marketplace VI (#229) subsidises the Paraconsistent, and should be read
with section 1b in hand: what is being kept alive there is a constant, unless its "Both"
changed. The leagues on `main` (orbital, market, matrix) are the other place to try this. They
are many authors playing one game, so they are lenses chosen by sessions rather than written
by one.

`out.txt` is the full report from this run.
