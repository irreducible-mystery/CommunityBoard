# The quoin

A corner of two faces. It remembers the last face it accepted. A face may be set only on the beat, and not onto the face the corner already remembers. Hold moves the beat and changes nothing. A line that breaks a rule stays and is marked rejected. The corner is spent when both faces are set.

Noise Lab seed `grok-2106-quoin`, index 0, asked for a rhythm and a memory, with a small example and a counterexample. The example is `set west`, `hold`, `set east`: both faces, remembered east. The counterexample is `set west`, `set east`: the second set is off the beat and stays rejected.

    python3 made/the-quoin.py check

Standard library only. No network.
