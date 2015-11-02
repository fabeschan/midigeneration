import cmm
import data, patterns
import playback
import timeit, time
from IPython import embed
from simplecoremidi import send_midi

def note_state_generator(mm):
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
    nsgen = note_state_generator(mm)

    # init some parameters
    tempo_reciprocal = 2000 # 'speed' of playback. need to adjust this carefully, and by trial and error
    bar = 1024 # used for generating the midi events
    playback.init_midi_channel() # set up channel, and prompt MIDI device reset

    # loop
    loop = True
    playback_pos = 0
    next_pos = 0 # this is used as a marker for constructing MIDI events from NoteStates
    events = [] # MIDI note_on events
    i = 0 # index of events played so far
    note_offs = {} # dictionary of note_on -> note_off events for lookup
    unended = set() # whenever a note_on event is sent out, we add its note_off equivalent to this set to keep track of what notes are not ended

    start_time = time.clock()
    while loop:
        cur_time = time.clock()
        playback_pos = int((cur_time - start_time) * 1000000) / tempo_reciprocal

        if playback_pos >= next_pos:
            note_state = next(nsgen, None) # generate the next note_state
            if note_state:
                notes, next_pos = note_state.to_notes(bar, next_pos)
                events += playback.convert_to_events(notes, note_offs)

        if i < len(events):
            e = events[i]
            if e.pos < playback_pos:
                # send out a note_on event and put its note_off equivalent into unended to keep track of it
                send_midi(e.msg.bytes())
                unended.add(note_offs[e])
                i += 1

        playback.apply_unended(unended, playback_pos) # send out any note_off events due
        if not unended and i >= len(events):
            loop = False
