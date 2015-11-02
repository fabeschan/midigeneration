import data
import timeit, time
import mido
from pprint import pprint
import simplecoremidi
import random

musicpieces = [data.piece('mid/owl.mid'), data.piece('mid/lost.mid')]
notes = [mp.unified_track.notes for mp in musicpieces]

class Event(object):
    '''
    wrapper around a MIDI event message, adding position for playback purposes

    msg: a mido MIDI message
    pos: int

    note: if not on OSX, please replace simplecoremidi.send_midi() with a function compatible
    with your OS.

    '''

    def __init__(self, msg, pos):
        self.msg = msg
        self.pos = pos

    def __repr__(self):
        return str((self.pos, self.msg))

    def send_midi(self):
        # this is a simple wrapper function to send a MIDI event out immediately
        # note: has nothing to do with pos
        simplecoremidi.send_midi(self.msg.bytes())

def convert_to_events(notes, note_offs):
    '''
    convert notes to note_on events and note_off events
    add note_on and note_off pair to note_offs
    note_offs: dictionary(key=note_on event, value=note_off event)
    return a list of note_on events

    '''

    events = []
    for n in notes:
        msg = mido.Message('note_on', note=n.pitch, channel=n.chn)
        e0 = Event(msg, n.pos)
        events.append(e0)

        msg = mido.Message('note_off', note=n.pitch, channel=n.chn)
        e1 = Event(msg, n.pos + n.dur)

        note_offs[e0] = e1
    return events

def read_trigger_file(filename):
    # read file, then clear and return its contents

    text = ''
    try:
        with open(filename, 'r+') as f:
            text = f.read().strip()
            f.seek(0)
            f.truncate()
    except:
        raise # replace with pass if this is causing you problems
    return text

def apply_unended(unended, pos, now=False):
    '''
    scan and check for note_off events in unended that are overdue, and send them out
    '''

    things_to_delete = []
    for k in unended:
        if now or k.pos < pos:
            k.send_midi()
            things_to_delete.append(k)
    for k in things_to_delete:
        unended.remove(k)

def init_midi_channel():
    '''
    Initializes the midi channel, and prompts for a MIDI device reset for your DAW
    Need to reset so that DAW can pick up the MIDI events from the new channel

    '''

    msg = mido.Message('note_on', note=60, channel=0)
    on_event = Event(msg, 0)
    on_event.send_midi()
    raw_input('MIDI channel is now set up. Please reset MIDI devices before continuing. Press [Enter]')
    msg = mido.Message('note_off', note=60, channel=0)
    off_event = Event(msg, 0)
    off_event.send_midi()

