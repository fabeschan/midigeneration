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
    playback.init_midi_channel()

    note_offs = {}
    unended = set()
    events_mp = [ playback.convert_to_events(n, note_offs) for n in notes ]

    event_idx = 0
    events = events_mp[event_idx]
    start_time = time.clock()

    # loop
    loop = True
    pos = 0
    i = [0] * len(events)
    while loop:
        text = playback.read_trigger_file('trigger_file')
        if text:
            print 'read triggerfile:', text
            event_idx = (event_idx + 1) % 2
            events = events_mp[event_idx]
            playback.apply_unended(unended, pos, now=True)

        cur_time = time.clock()
        pos = int((cur_time - start_time) * 1000000) / tempo_reciprocal
        if i[event_idx] < len(events):
            e = events[i[event_idx]]
            if e.pos < pos:
                send_midi(e.msg.bytes())
                unended.add(note_offs[e])
                i[event_idx] += 1
            playback.apply_unended(unended, pos)
        else:
            loop = False

if __name__ == '__main__':
    main()
