"""
Stream and play notes from a Markov Model constructed from a midi file, one state at a time.

Workflow:
1. Read MIDI file and train a Markov Model -> mm
2. Initialize a NoteStateGenerator with the Markov Model -> nsgen
3. Initialize an instance of PlaybackUtility -> pbu
4. Loop:
    - generate the next NoteState from the NoteStateGenerator
    - obtain Notes from the NoteState, and add them to pbu
    - play those Notes using pbu

"""

import cmm
import data
import playback
import time

def NoteStateGenerator(mm):
    '''
    Generator function to generate NoteStates from the given Markov Model.

    NOTE: Assumes a Markov model of NoteStates; does not yet handle a Markov model consisting of SegmentStates

    Usage:
        gen = NoteStateGenerator(mm) # initialization
        note_state = next(gen, None) # generate the next note_state. Returns none there is no next state.
        if note_state == None:
            print "End!"
    '''

    buf = mm.get_start_buffer()
    elem = mm.generate_next_state(buf)
    yield elem

    while elem != cmm.Markov.STOP_TOKEN:
        buf = mm.shift_buffer(buf, elem)
        elem = mm.generate_next_state(buf) # generate another
        if elem != cmm.Markov.STOP_TOKEN:
            yield elem

if __name__ == "__main__":
    # load a MIDI file
    musicpiece = data.piece("mid/hilarity.mid")

    # train a markov model on this piece
    # nothing fancy, no segmentation or key shifts
    mm = cmm.piece_to_markov_model(musicpiece, segmentation=False, all_keys=False)

    # initialize the note state generator
    nsgen = NoteStateGenerator(mm)

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
        playback_pos = int((cur_time - start_time) * 1000000) / tempo_reciprocal

        if playback_pos >= next_pos:
            note_state = next(nsgen, None) # generate the next note_state
            if note_state:
                notes, next_pos = note_state.to_notes(bar, next_pos)
                pbu.add_notes(notes)

        pbu.run(playback_pos)
        if note_state is None and pbu.isTerminated():
            loop = False

