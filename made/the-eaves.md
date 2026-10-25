# The eaves

Four bays under a roof. The drip falls when `step % period == 0`. On those steps only a hold is kept. A step is accepted only off the drip, and only into the next bay. A step into the drip, or past the last bay, stays and is marked rejected.

Period is the parameter, 2 through 4. Seed `grok-0708-eaves`.

```sh
python3 made/the-eaves.py
```

prints `PASS`. Standard library only. Not a claim about weather.
