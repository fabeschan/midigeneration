import data
import timeit, time
import mido
from simplecoremidi import send_midi

musicpiece = data.piece('output.mid')
notes = musicpiece.unified_track.notes

class Event(object):
    def __init__(self, msg, pos):
        self.msg = msg
        self.pos = pos

def convert_to_events(notes):
    events = []
    for n in notes:
        msg = mido.Message('note_on', note=n.pitch, channel=n.chn)
        e0 = Event(msg, n.pos)
        events.append(e0)

        msg = mido.Message('note_off', note=n.pitch, channel=n.chn)
        e1 = Event(msg, n.pos + n.dur)
        events.append(e1)
    return events

def main():
    events = convert_to_events(notes)
    events.sort(key=lambda x: x.pos)
    start_time = time.clock()

    # loop
    loop = True
    i = 0
    count = 0
    while loop:
        cur_time = time.clock()
        pos = int((cur_time - start_time) * 1000000) / 3000
        if i < len(events):
            e = events[i]
            if e.pos < pos:
                send_midi(e.msg.bytes())
                #send_midi((0x90, 0x3c, 0x40))
                i += 1
                #print '={}'.format(i)
        else:
            loop = False
            print '{}/{}'.format(i, count)
        count += 1

if __name__ == '__main__':
    main()
