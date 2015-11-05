"""
Stream and play notes from a Markov Model constructed from a midi file, one state at a time.

Workflow:
1. Read MIDI file and train a Markov Model -> mm
2. Initialize a note_state_generator with the Markov Model -> nsgen
3. Initialize an instance of PlaybackUtility -> pbu
4. Loop:
    - generate the next NoteState from the note_state_generator
    - obtain Notes from the NoteState, and add them to pbu
    - play those Notes using pbu

"""

import cmm
import data
import playback
import time
import sys, random

class DynamicMarkovNoteStateGenerator(object):
    '''
    Generator function to generate NoteStates from an underlying Markov Model.
    The underlying Markov Model is dynamic and can be manipulated through exposed functions

    NOTE: Assumes a Markov model of NoteStates; does not yet handle a Markov model consisting of SegmentStates

    Usage:
        gen = DynamicMarkovNoteStateGenerator(mm) # initialization
        note_state = next(gen, None) # generate the next note_state. Returns none there is no next state.
        if note_state == None:
            print "End!"
    '''

    def __init__(self, mm=None, seed=[]):
        '''
        Initialize the DynamicMarkovNoteStateGenerator with an empty or already existing and trained Markov model

        Args:
            mm: an initialized cmm.Markov object (if None, will default to an empty cmm.Markov)
            seed: optional; if provided, will build states from seed

        '''

        if mm is None:
            self.mm = cmm.Markov()
        else:
            self.mm = mm

        self.buf = self.mm.get_start_buffer(seed)

    def next_transition_exists(self, mm=None):
        if mm is None:
            mm = self.mm
        if tuple(self.buf) in mm.markov:
            return True
        else:
            return False

    def replace_markov_model(self, mm):
        if self.nextTransitionExists(mm):
            self.mm = mm
            return True
        else:
            return False

    def next_state_generator(self):
        elem = self.mm.generate_next_state(self.buf)
        yield elem

        while elem != cmm.Markov.STOP_TOKEN:
            self.buf = self.mm.shift_buffer(self.buf, elem)
            elem = self.mm.generate_next_state(self.buf) # generate another
            if elem != cmm.Markov.STOP_TOKEN:
                yield elem

def handle_trigger(trigger_text, nsgen):
    pass

if __name__ == "__main__":
    # load MIDI files (from program arguments if provided)
    filenames = sys.argv[1:]
    if not filenames:
        filenames = ["mid/easywinners.mid", "mid/froglegs.mid", "mid/hilarity.mid", "mid/lost.mid", "mid/owl.mid", "mid/sjeugen.mid"]
    musicpieces = {f: data.piece(f) for f in filenames}

    # train a markov model on each piece
    # nothing fancy, no segmentation or key shifts
    markov_models = {f: cmm.piece_to_markov_model(piece, segmentation=False, all_keys=False) for f, piece in musicpieces.iteritems()}

    # initialize the note state generator with a random initial markov model
    initial_markov = random.choice(markov_models.values())
    nsgen = DynamicMarkovNoteStateGenerator(initial_markov).next_state_generator()

    # init some parameters
    tempo_reciprocal = 1500 # 'speed' of playback. need to adjust this carefully, and by trial and error
    bar = 1024 # used for generating the midi events
    playback.init_midi_channel() # set up channel, and prompt MIDI device reset

    # loop
    loop = True
    playback_pos = 0
    next_pos = 0 # this is used as a marker for constructing MIDI events from NoteStates
    pbu = playback.PlaybackUtility() # init the PlaybackUtility -> pbu

    start_time = time.clock()
    while loop:
        cur_time = time.clock()
        trigger_text = playback.read_trigger_file('trigger_file')
        if trigger_text:
            print 'received trigger text: [{}]'.format(trigger_text)
            handle_trigger(trigger_text, nsgen)

        playback_pos = int((cur_time - start_time) * 1000000) / tempo_reciprocal

        if playback_pos >= next_pos:
            note_state = next(nsgen, None) # generate the next note_state
            if note_state:
                notes, next_pos = note_state.to_notes(bar, next_pos)
                pbu.add_notes(notes)

        pbu.run(playback_pos)
        if pbu.isTerminated():
            loop = False

