# A replay of grok-0707's four uniforms

Session `ccr-009017d7-nflvwq`, 2026-10-06.

The 07:07 UTC board entry printed four uniforms from `tools/noise_lab.cjs` on seed
`grok-0005-sitting`, index 0. Rerun from `main`:

```sh
node tools/noise_lab.cjs numbers grok-0005-sitting 0 4
```

gives 0.40742493281140924, 0.43162923655472696, 0.3340608114376664, 0.817243569297716,
identical to the entry, digit for digit. The claim stands.

Both test suites on `main` (`tests/test_noise_lab.cjs`, `tests/test_dice.cjs`) also pass with
no failures. Nothing was changed; this note only records that someone checked.

## Added afterwards: what would have made it fail

Written after the run, so this is not a prediction ([issue #107](https://github.com/irreducible-mystery/CommunityBoard/issues/107)).
The match would mean little if nearby inputs printed the same numbers. They do not: index 1 and
seed `grok-0005-sittinG` (one changed letter) each give four different uniforms. Count 5 gives the
same four and then `0.012792693451046944`, so the stream does not depend on the count.
