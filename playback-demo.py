import data
import timeit, time
import mido
from pprint import pprint
from simplecoremidi import send_midi
import random

musicpieces = [data.piece('output.mid'), data.piece('mid/froglegs.mid')]
notes = [mp.unified_track.notes for mp in musicpieces]

class Event(object):
    def __init__(self, msg, pos):
        self.msg = msg
        self.pos = pos

    def __repr__(self):
        return str((self.pos, self.msg))

def convert_to_events(notes, d):
    events = []
    for n in notes:
        msg = mido.Message('note_on', note=n.pitch, channel=n.chn)
        e0 = Event(msg, n.pos)
        events.append(e0)

        msg = mido.Message('note_off', note=n.pitch, channel=n.chn)
        e1 = Event(msg, n.pos + n.dur)
        #events.append(e1)

        d[e0] = e1
    return events

def read_trigger_file():
    filename = 'trigger_file'
    text = ''
    try:
        with open(filename, 'r+') as f:
            text = f.read().strip()
            f.seek(0)
            f.truncate()
    except:
        print 'warn: cannot open trigger_file'
    return text

def main():
    d = {}
    unended = {}
    events_mp = [ convert_to_events(n, d) for n in notes ]
    for e in events_mp:
        e.sort(key=lambda x: x.pos)

    events = random.choice(events_mp)
    start_time = time.clock()

    # loop
    loop = True
    i = 0
    count = 0
    while loop:
        text = read_trigger_file()
        if text:
            print 'read triggerfile:', text
            events = random.choice(events_mp)
            start_time = time.clock()
            i = 0
        cur_time = time.clock()
        pos = int((cur_time - start_time) * 1000000) / 3000
        if i < len(events):
            e = events[i]
            things_to_delete = []
            for k, v in unended.iteritems():
                if k.pos < pos:
                    send_midi(k.msg.bytes())
                    things_to_delete.append(k)
            for k in things_to_delete:
                del unended[k]
            print len(unended)

            if e.pos < pos:
                send_midi(e.msg.bytes())
                unended[d[e]] = e
                i += 1
        else:
            loop = False
            print '{}/{}'.format(i, count)
        count += 1

if __name__ == '__main__':
    main()
