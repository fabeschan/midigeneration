_________________________

README FOR createModel.py
_________________________


HOW TO RUN:
-----------
python createModel.py

- it will then prompt a midi file to base the model on
	- eg: Enter midi file for model (with extension): song.mid

- next, enter the output file for the model:
	- eg: Enter the name for the output model: exampleModel


OUTLINE:
--------
We first scan through the midi file with starting increments of 2 chords. If there is an 85% match in the initial 2 chords
we increase the chord length by one and scan again. We continually increase the chord size until there is less than an
85% match and at that point, we mark the last matching section as a riff (The section used to compare is marked as 
"reference" and given a number starting from 0, the subsequent matching riffs are labelled with the same number).

After all the riffs are found, we generate a probability matrix which outlines the probability of going to another section
given an initial section. The generateProbMatrix function also returns a note dictionary with the keys are the last notes
in each section and the values are the sections that appear after that note.

These are the values that comprise the model used to generate songs.


OUTPUTS:
--------
The output file (named by the user) is a model that contains the following pickled variables:
	- riff: numbered riffs (starting from 0) and the sections that they start/end on
	- master: the midi tracks combined and grouped into chords (ie: notes that are played at the same time)
	- probability matrix: the probability of going to another section given the current section
	- noteDict: a dictionary where the keys are the last notes in each section and the values are the section that appears next
	- model (from original midi generation): a generated model from the original midi generation files

__________________________

README FOR generateSong.py
__________________________

How to run:
python generateSong.py

- it will then prompt for up to 2 models in which to generate from (ie: the output of createmodel.py)
	- eg: Enter model to generate from: exampleModel
		  Enter model to generate from or DONE to generate: exampleModel2
		  
	- eg: Enter model to generate from: anotherExampleModel
		  Enter model to generate from or DONE to generate: DONE

- next, enter the output file for the midi file:
	- eg: Enter the output song name: finalmidi.mid

OUTLINE:
--------
First we unpickle all the models that are provided to have access to the variables. Then we generate subsequent sections
starting from the first section in the first model (NOTE: The generated sequence will always begin with the first section
of the FIRST provided model. If you wish to start with the other model, simply input the models in reverse order). For a
sequence generated with one model, it factors the probability of arriving to the next section and chooses from the probablity.
In a 2 model generated sequence, it combines the note dictionaries and pulls from a random sequence.


OUTPUTS:
--------
The output midi file is a generated from the models that were specified, pulling from sections appropriately

___________________________________

README FOR ORIGINAL GENERATION CODE
___________________________________

- navigate to the appropriate folder and run python in the command line
- do the following:
>>> import muse
>>> model = muse.make("midifile.mid", 1) # where midifile.mid is the name of the midi file and 1 is how far to look back
>>> muse.use(model, "outputfile.mid") # where outputfile.mid is the name of the output file