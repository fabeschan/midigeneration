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

playback-demo.py
> PROOF OF CONCEPT - real time dynamic playback

> Loops over MIDI events and sends them to a MIDI channel

> It polls a local file called triggerfile to toggle between two .mid files:

```
echo "blah" > triggerfile
```

> (only tested on OSX)

> Requires simplecoremidi package for python
```
pip install simplecoremidi
```

> And a DAW (I use REAPER which is 'free')
