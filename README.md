```
Required python 2.7 modules:
    - IPython
    - numpy
    - matplotlib
    - sklearn
    - skimage
```


HOW TO RUN:
-----------

Run cmm.py
> python cmm.py

It produces a file named output.mid once it finishes running

Configuring: (scroll towards the end of cmm.py)
Edit pieces in cmm.py to select source pieces:
```
pieces = ["mid/hilarity.mid", "mid/froglegs.mid", "mid/easywinners.mid"]
```

Toggle between two modes: mixture or segmentation (I haven't had a chance to figure out a way to combine the two):
```
segmentation = True
all_keys = False
```


NOTES:
------

- The cached folder holds cached computations. Delete them if they are causing you problems. Note that recalculating stuff will take a while.

- The software requires that all midi files in mid are properly quantized (i.e. each note type has a regular number of ticks).

Description of each file:
------

analyze.py
> This file sets up infrastructure for the similarity measure using a classifier that compares two music segments and gives a score between 0 and 1

> Defines a training model, trains it, and saves it in a pickled file in `cached/`

chords.py
> Implements some tools to help identifying chords

> 1. Chord Templates
> 2. Chord Generator
> 3. Classifier

cmm.py
> Implements the Generic Markov Model, Statechains, NotesStates, and relevant functions

data.py
> Contains data structures to facilitate working with MIDI tracks, defines edit distance and other functionality

experiments.py
> patterns.py is too big of a file, so this is a wrapper to help with segmentation

> the file probably needs a better name

midi.py
> written by Daniel Eisner, parses a raw MIDI file and returns a list

> contains bug fixes written by me

mixture-plot.py
> script to produce a mixture plot

patterns.py
> implements the segmentation algorithm

recurrence-plot.py
> script to produce a recurrence plot

similar_sections.py
> defines training data that help train a measure of similarity between two segments

> used by analyze.py

playback.py
> module that houses a few helper functions for realtime playback

playback-demo.py
> PROOF OF CONCEPT - real time dynamic playback

> Loops over MIDI events and sends them to a MIDI channel

> It polls a local file called triggerfile to toggle between two .mid files:
> To trigger a toggle, just put something in the file as follows:
```
echo "blah" > triggerfile
```

> (only tested on OSX)

> Requires simplecoremidi package for python: https://github.com/sixohsix/simplecoremidi, and mido package for python: https://mido.readthedocs.org/en/latest/
```
$ pip install simplecoremidi
$ pip install mido
```

> To receive those MIDI events and be able to play them, use a DAW (I use REAPER which is 'free') and have it receive from the "simple core midi source" input and play to a virtual instrument

stream-cmm.py
> Stream and play notes from a Markov Model constructed from a midi file, one state at a time.

stream-dynamic.py
> Stream and play notes from Markov Models constructed from midi files, one state at a time.

> Accepts external signals to schedule a change in its underlying Markov Model
