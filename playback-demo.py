import data
import timeit, time
import mido
from pprint import pprint
from simplecoremidi import send_midi
import random
import playback

def main():
    # init
    musicpieces = [data.piece('mid/owl.mid'), data.piece('mid/lost.mid')]
    notes = [mp.unified_track.notes for mp in musicpieces]

    tempo_reciprocal = 3000 # 'speed' of playback. need to adjust this carefully
    playback.init_midi_channel() # set up channel, and prompt MIDI device reset

    note_offs = {} # dictionary of note_on -> note_off Events for lookup
    unended = set() # whenever a note_on Event is sent out, we add its note_off equivalent to this set to keep track of what notes are not ended
    events_mp = [ playback.convert_to_events(n, note_offs) for n in notes ]

    event_idx = 0
    events = events_mp[event_idx]
    start_time = time.clock()

    # loop
    loop = True
    pos = 0
    i = [0] * len(events) # for each music piece, keep track of which events are sent out
    while loop:

        # read/poll the trigger file
        text = playback.read_trigger_file('trigger_file')
        if text:
            print 'read triggerfile:', text
            event_idx = (event_idx + 1) % 2 # switch pieces
            events = events_mp[event_idx] # switch pieces
            playback.apply_unended(unended, pos, now=True) # send out any note_off Events due

        cur_time = time.clock()
        pos = int((cur_time - start_time) * 1000000) / tempo_reciprocal
        if i[event_idx] < len(events):
            e = events[i[event_idx]]
            if e.pos < pos:
                # send out a note_on Event and put its note_off equivalent into unended to keep track of it
                e.send_midi()
                unended.add(note_offs[e])
                i[event_idx] += 1
            playback.apply_unended(unended, pos) # send out any note_off Events due
        else:
            loop = False

if __name__ == '__main__':
    main()
