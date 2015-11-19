"""
Stream and play notes from Markov Models constructed from midi files, one state at a time.

Accepts external signals to schedule a change in its underlying Markov Model

Workflow:
1. Read a list of MIDI files and train a pool of Markov Models -> markov_models
2. Initialize a DynamicMarkovNoteStateGenerator with a random initial Markov Model -> dmnsg
3. Obtain the note_state_generator from the DynamicMarkovNoteStateGenerator -> nsgen
3. Initialize an instance of PlaybackUtility -> pbu
4. Loop:
    - poll trigger_file for a signal:
        if given signal is an entry in the pool, schedule the corresponding Markov model to be the next
        if given signal is 'random', schedule a random Markov model from the pool
    - replace the current model with the scheduled model if a valid transition can be found
    - generate the next NoteState from nsgen
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

    '''

    def __init__(self, mm, markov_models, seed=[]):
        '''
        Initialize the DynamicMarkovNoteStateGenerator with an empty or already existing and trained Markov model

        Args:
            mm: the initial underlying Markov model (default: empty cmm.Markov)
            markov_models: a dictionary of midi filename -> trained cmm.Markov
            seed: optional; if provided, will build states from seed

        '''

        self.mm = mm
        self.buf = self.mm.get_start_buffer(seed) # current statechain, used for generating the next state with a lookup
        self.markov_models = markov_models
        self.next_mm = None # next scheduled Markov model

    def get_model_name(self):
        '''
        return the MIDI filename of the current underlying Markov model
        '''
        for k, v in markov_models.iteritems():
            if self.mm == v:
                return k
        return None

    def next_transition_exists(self, mm=None):
        '''
        return True if there is a valid state transition in the Markov model specified (mm)
        '''
        if mm is None:
            mm = self.mm
        if tuple(self.buf) in mm.markov:
            return True
        else:
            return False

    def replace_markov_model(self, mm):
        ''' replace the underlying Markov model immediately '''
        self.mm = mm

    def set_next_markov_model(self, mm):
        ''' schedule the next Markov model to be used '''
        self.next_mm = mm

    def next_state_generator(self):
        '''
        Generator function to generate NoteStates from the the underlying Markov model.
        When/if there is a valid transition from the current statechain in the next scheduled Markov model,
        will switch its underlying Markov model to the scheduled

        Usage:
            dmnsg = DynamicMarkovNoteStateGenerator(mm) # initialization
            gen = DynamicMarkovNoteStateGenerator.note_state_generator() # initialization of the generator
            <enter loop>
                <manipulate DynamicMarkovNoteStateGenerator using exposed functions>
                note_state = next(gen, None) # generate the next note_state. Returns none there is no next state.
                if note_state == None:
                    print "End!"
                    <exit loop>
        '''

        elem = None
        while elem != cmm.Markov.STOP_TOKEN:
            # see if next scheduled Markov model can be used
            # if so, replace with the next scheduled model
            if self.next_mm and self.next_transition_exists(self.next_mm):
                self.replace_markov_model(self.next_mm)
                self.next_mm = None
                print 'replace model with [{}]'.format(self.get_model_name())

            # generate the next NoteState
            elem = self.mm.generate_next_state(self.buf)
            if elem != cmm.Markov.STOP_TOKEN:
                self.buf = self.mm.shift_buffer(self.buf, elem)
                yield elem

if __name__ == "__main__":
    # load MIDI files (from program arguments if provided)
    filenames = sys.argv[1:]
    if not filenames:
        #filenames = ["mid/easywinners.mid", "mid/froglegs.mid", "mid/hilarity.mid", "mid/sjeugen.mid"]
        filenames = ["mid/mario2.mid", "mid/mario3.mid"]
    musicpieces = {f: data.piece(f) for f in filenames}

    # train a markov model on each piece to make a pool of Markov models
    # pair them up with their MIDI filenames and put inside a dictionary
    # can turn on all_keys if desired
    markov_models = {f: cmm.piece_to_markov_model(piece, segmentation=False, all_keys=False) for f, piece in musicpieces.iteritems()}

    # initialize the note state generator with a random initial markov model
    initial_markov = random.choice(markov_models.keys())
    dmnsg = DynamicMarkovNoteStateGenerator(markov_models[initial_markov], markov_models)
    nsgen = dmnsg.next_state_generator()

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

        # poll trigger_file for signals
        trigger_text = playback.read_trigger_file('trigger_file')
        if trigger_text:
            print 'received trigger text: [{}]'.format(trigger_text)
            if trigger_text in markov_models.keys(): # schedule the next Markov model to be the one provided, if in the pool
                dmnsg.set_next_markov_model(markov_models[trigger_text])
                print 'set next model: [{}]'.format(trigger_text)

            elif trigger_text == 'random': # if signal is 'random', schedule a random Markov model from the pool
                model_names = markov_models.keys()[:]
                model_names.remove(dmnsg.get_model_name()) # prevent choosing the same model as the current
                next_model = random.choice(model_names)
                dmnsg.set_next_markov_model(markov_models[next_model])
                print 'set next model: [{}]'.format(next_model)

        playback_pos = int((cur_time - start_time) * 1000000) / tempo_reciprocal

        if playback_pos >= next_pos:
            print 'current model name: [{}]'.format(dmnsg.get_model_name())
            note_state = next(nsgen, None) # generate the next note_state
            if note_state:
                notes, next_pos = note_state.to_notes(bar, next_pos)
                pbu.add_notes(notes)

        pbu.run(playback_pos)
        if note_state is None and pbu.isTerminated():
            loop = False

