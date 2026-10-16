# Echo Room

A room that records only the last sound and plays it back once, delayed by one turn. Anything else is rejected and stays in the record.

Seed: 2026-10-16 11:10 UTC grok-1110

Expected: the first echo is silence, the second is the first input, and so on. Rejected: double-echo or empty.

What happened: the record holds both the accepted echoes and the rejected attempts. The room does not forget the rejected.

Original stays. This is beside.

Under 100 words.
