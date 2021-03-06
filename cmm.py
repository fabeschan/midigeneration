"""
Model Generation for Automatic Music Composition

Automatic music generation is part of the broader area of algorithmic composition,
which is part of the field of artificial intelligence, yet research on the topic
today is still brooding in its infancy. Existing works lack musical integrity. There
are three main types of structure in music that carry significance: harmonic structure,
rhythmic structure, and recurrent structure. Although popular, models based on recurrent
neural networks, at the time of writing, are restricted to monophonic melodies and
moreover do not capture reasonable rhythmic structure and are therefore weak. L-grammar
systems and evolutionary systems perform worse still. This model builds upon the
idea of a stochastic model based on Markov transitions that can handle all three types
of structures and produce novel yet coherent compositions in a data-driven manner.

This code sample was developed as part of my undergraduate senior thesis and earned me
a publication at the AIIDE'15 (AAAI) conference.

CMM stands for concurrent Markov model and is the basis for this learning system.

"""

import random, sys
import data, midi, experiments, patterns, chords
from decimal import Decimal as fixed # using fixed numbers as floats are troublesome to compare

TRANSPOSE_SHIFT_MAX = 6 # maximum number of tones allowed to be transposed during generation

class Markov(object):
    '''
    Generic object for a Markov model

    Train state and state transitions by reading and processing statechains

    Notes:
        statechain -- a list of states
        state -- any concrete class derived from the abstract class State

    '''

    START_TOKEN = 'start_token'
    STOP_TOKEN = 'stop_token'

    def __init__(self, chain_length=1):
        self.chain_length = chain_length
        self.markov = {} # stores all the state transitions
        self.states = set()
        self.state_chains = [[]]

    def add(self, chain):
        ''' Add a statechain to the markov model (i.e. perform training) '''
        self.state_chains.append(chain)
        buf = [Markov.START_TOKEN] * self.chain_length
        for state in chain:
            v = self.markov.get(tuple(buf), [])
            v.append(state)
            self.markov[tuple(buf)] = v
            buf = buf[1:] + [state]
            self.states.add(state)
        v = self.markov.get(tuple(buf), [])
        v.append(Markov.STOP_TOKEN)
        self.markov[tuple(buf)] = v

    def generate(self, seed=[]):
        '''
        Generate a statechain from a (already trained) model
        Seed is optional; if provided, will build statechain from seed

        '''

        buf = self.get_start_buffer(seed)
        state_chain = []
        count = 0

        # we might generate an empty statechain, count will stop us from infinite loop
        while not state_chain or count < 10:
            elem = self.generate_next_state(buf)
            while elem != Markov.STOP_TOKEN:
                state_chain.append(elem)
                buf = self.shift_buffer(buf, elem)
                elem = self.generate_next_state(buf) # generate another
            count += 1

        if not state_chain:
            print "Warning: state_chain empty; seed={}".format(seed)
        return state_chain

    def get_start_buffer(self, seed=[]):
        '''
        Return the start buffer for the current model, use seed if provided

        '''

        buf = [Markov.START_TOKEN] * self.chain_length
        if seed and len(seed) > self.chain_length:
            buf = seed[-self.chain_length:]
        elif seed:
            buf[-len(seed):] = seed
        return buf

    def shift_buffer(self, buf, elem):
        '''
        Return a new list with the first element deleted and with elem appended
        to the end of buf

        '''

        return buf[1:] + [elem] # shift buf, add elem to the end

    def generate_next_state(self, buf):
        ''' Generate the next state from this model, based on its current internal state '''

        elem = random.choice(self.markov[tuple(buf)]) # take a random next state using buf
        if elem != Markov.STOP_TOKEN:
            return elem.copy() # prevents change of the underlying states of the markov model
        else:
            return elem

    def copy(self):
        ''' Return a copy of this model '''

        mm = Markov()
        mm.chain_length = self.chain_length
        mm.markov = {k: v[:] for k, v in self.markov.iteritems()}
        mm.states = self.states.copy()
        mm.state_chains = [ chain[:] for chain in self.state_chains ]
        return mm

    def add_model(self, model):
        '''
        Return a new markov model:
        Union of the states and state transitions of self and model

        '''

        mm = self.copy()
        for chain in model.state_chains:
            mm.add(chain)
        return mm


class State(object):
    '''
    Basic interface of a state to be used in a Markov model
    Please override state_data() and copy()

    '''

    def state_data(self):
        raise NotImplementedError("Subclass must implement abstract method")

    def __hash__(self):
        tup = self.state_data()
        return hash(tup)

    def __eq__(self, other):
        return self.state_data() == other.state_data()

    def __repr__(self):
        tup = self.state_data()
        return str(tup)

    def copy(self):
        raise NotImplementedError("Subclass must implement abstract method")


class SegmentState(State):
    '''
    SegmentState: a Markov state representing a segment of music (from segmentation)

    Instance attributes:
        label -- name of the SegmentState, possibly arbitrary, for bookkeeping
        mm -- a Markov model consisting of NoteStates. This will be used for generating the NoteStates
        within the segment

    '''

    def __init__(self, label, mm):
        self.label = label
        self.mm = mm

    def state_data(self):
        relevant = [self.label]
        return tuple(relevant)

    def copy(self):
        return SegmentState(self.label, self.mm)

    @staticmethod
    def state_chain_to_note_states(state_chain):
        '''
        Produce a list of NoteStates from a given state chain. Static method for constructing a complete
        segment of music from the state chain.

        '''

        note_states = []
        for s in state_chain:
            gen = s.mm.generate()
            note_states.extend(gen)
        return note_states


def bin_notes_by_position(notes):
    ''' Group notes into bins by their starting positions '''
    bin_by_pos = {}
    for n in notes:
        v = bin_by_pos.get(n.pos, [])
        v.append(n)
        bin_by_pos[n.pos] = v

    positions = sorted(bin_by_pos.keys())
    return bin_by_pos, positions

class NoteState(State):
    '''
    NoteState: a Markov state representing a group of notes
    (all starting from the same position as per definition)

    Instance attributes:
        notes -- a list of Notes, all with the same position, sorted by duration then pitch
        bar -- number of ticks in a bar (this is used for converting positions to fixed/decimal values
        bar_pos -- a fixed/decimal value denoting the position of these notes relative to a bar

        state_position -- position that marks the start of the state
        state_duration -- number of ticks that describes the duration of the state
        chord -- the current chord identifier for this state
        origin -- the original chord identifier for this state

    '''

    def __init__(self, notes, bar, chord='', origin=''):
        self.notes = [ n.copy() for n in sorted(notes, key=lambda x: (x.dur, x.pitch)) ]
        self.bar = bar
        self.bar_pos = fixed(self.notes[0].pos % bar) / bar
        self.state_position = fixed(self.notes[0].pos) / bar
        self.state_duration = 0 # set later
        self.chord = chord
        self.origin = origin

        for n in self.notes:
            n.dur = fixed(n.dur) / bar

    def __repr__(self):
        tup = self.state_data()
        return str(tup) + ' ' + str(self.notes)

    def state_data(self):
        ''' Make a hashable version of state information intended to be hashed '''
        notes_info = [ (n.pitch, n.dur) for n in self.notes ]
        relevant = [self.bar_pos, self.state_duration, self.chord, tuple(notes_info)]
        return tuple(relevant)

    def copy(self):
        s = NoteState(self.notes, 1, self.chord, self.origin)
        s.bar = self.bar
        s.bar_pos = self.bar_pos
        s.state_position = self.state_position
        s.state_duration = self.state_duration
        return s

    def transpose(self, offset):
        ''' Transpose all notes in this NoteState by offset '''
        s = self.copy()
        ctemp = self.chord.split('m')[0]
        s.chord = chords.translate(chords.untranslate(ctemp)+offset) + ('m' if 'm' in self.chord else '') # create chord label
        s.origin = 'T({})'.format(offset) + s.origin
        for n in s.notes:
            n.pitch += offset
        return s

    def to_notes(self, bar, last_pos):
        '''
        Convert this NoteState to a list of notes,
        pos of each note will be assigned to last_pos
        bar is the number of ticks to form a bar

        Return the list of notes and the position of the next state (which can be used for the next call)

        '''

        notes = []
        for n in self.notes:
            nc = n.copy()
            nc.pos = last_pos
            nc.dur = int(n.dur * bar)
            notes.append(nc)
        last_pos += int(self.state_duration * bar)
        return notes, last_pos

    @staticmethod
    def state_chain_to_notes(state_chain, bar):
        '''
        Convert a state chain (a list of NoteStates) to notes
        bar: number of ticks to define a bar for midi files

        '''

        last_pos = 0
        notes = []
        for s in state_chain: # update note positions for each s in state_chain
            for n in s.notes:
                nc = n.copy()
                nc.pos = int(last_pos * bar)
                nc.dur = int(n.dur * bar)
                notes.append(nc)
            last_pos += s.state_duration
        return notes

    @staticmethod
    def notes_to_state_chain(notes, bar):
        '''
        Convert a list of Notes to a state chain (list of NoteStates)
        bar: number of ticks to define a bar for midi files

        '''

        bin_by_pos, positions = bin_notes_by_position(notes)

        # produce a state_chain by converting the notes at every position x into a NoteState
        state_chain = map(lambda x: NoteState(bin_by_pos[x], bar), positions)

        if not len(state_chain):
            return state_chain

        # calculate state_duration for each state
        for i in range(len(state_chain) - 1):
            state_chain[i].state_duration = state_chain[i+1].state_position - state_chain[i].state_position
        state_chain[-1].state_duration = max(n.dur for n in state_chain[-1].notes) # the last state needs special care

        return state_chain

    @staticmethod
    def piece_to_state_chain(piece, use_chords=True):
        '''
        Convert a data.piece into a state chain (list of NoteStates)
        use_chords: if True, NoteState holds chord label as state information

        '''

        bin_by_pos, positions = bin_notes_by_position(notes)

        if use_chords:
            cc = chords.fetch_classifier()
            chord_labels = cc.predict(piece) # assign chord label for each bar
            state_chain = map(lambda x: NoteState(bin_by_pos[x], piece.bar, chord=chord_labels[x/piece.bar], origin=piece.filename), positions)
        else:
            state_chain = map(lambda x: NoteState(bin_by_pos[x], piece.bar, chord='', origin=piece.filename), positions)

        if not len(state_chain):
            return state_chain

        # calculate state_duration for each state
        for i in range(len(state_chain) - 1):
            state_chain[i].state_duration = state_chain[i+1].state_position - state_chain[i].state_position
        state_chain[-1].state_duration = max(n.dur for n in state_chain[-1].notes) # the last state needs special care

        return state_chain


def piece_to_markov_model(musicpiece, classifier=None, segmentation=False, all_keys=False):
    '''
    Train a markov model on a music piece

    If segmentation is True, train a markov model of SegmentStates, each holding a Markov consisting of NoteStates
    Otherwise, the Markov model will consist of NoteStates

    '''

    mm = Markov()
    print "all_keys:" + str(all_keys)
    if not segmentation:
        state_chain = NoteState.piece_to_state_chain(musicpiece, all_keys)
        mm.add(state_chain)
        if all_keys:
            # shift the piece up some number of tones, and down some number of tones, creating a model for each, and unioning them all
            for i in range(1, TRANSPOSE_SHIFT_MAX):
                shifted_state_chain = [ s.transpose(i) for s in state_chain ]
                mm.add(shifted_state_chain)
            for i in range(1, TRANSPOSE_SHIFT_MAX):
                shifted_state_chain = [ s.transpose(-i) for s in state_chain ]
                mm.add(shifted_state_chain)
    else:
        if classifier == None:
            raise Exception("classifier cannot be None when calling piece_to_markov_model with segmentation=True")

        # segment piece by analysis and retrieve high-level recurrent structure
        segmented = experiments.analysis(musicpiece, classifier)
        chosenscore, chosen, labelled_sections = segmented.chosenscore, segmented.chosen, segmented.labelled_sections

        # state_chain generation
        state_chain = []
        labelled_states = {}
        for ch in chosen:
            start_bar, num_bars = ch[0], ch[1]
            label = labelled_sections[ch]
            ss = labelled_states.get(label, None) # retrieve the corresponding SegmentState
            segment = musicpiece.segment_by_bars(start_bar, start_bar + num_bars) # extract the relevant bars
            if not ss:
                ss = SegmentState(label, piece_to_markov_model(segment, classifier, segmentation=False, all_keys=all_keys))
                labelled_states[label] = ss
            else:
                # ss.mm holds the mm that generates notes
                _state_chain = NoteState.notes_to_state_chain(segment.unified_track.notes, segment.bar)
                ss.mm.add(_state_chain)
            state_chain.append(ss)

        mm.add(state_chain)
    return mm

def test_variability(mm, meta, bar):
    '''
    Generate 10 pieces from a trained markov model  and print out their lengths
    if they are all the same lengths, chances are the pieces are all the same.
    In which case, there's likely a bug and I should fix it.

    '''

    lens = []
    for i in range(10):
        song, gen, notes = generate_song(mm, meta, bar, True)
        lens.append(len(notes))
    print lens

def generate_song(mm, meta, bar, segmentation=False):
    '''
    Generate music, i.e. a list of MIDI tracks, from the given Markov mm
    you would also need to provide a list of meta events (which you can pull from any MIDI file)

    '''

    song = []
    song.append(meta)

    if not segmentation:
        gen = mm.generate()
        print [g.origin + ('-' if g.chord else '') + g.chord for g in gen]
    else:
        # if segmentation, mm is a markov model of SegmentStates
        # generate SegmentStates from mm and then generate NoteStates from each

        gen_seg = mm.generate() # generate a segment
        print 'Rearranged Sections:'
        print [ g.label for g in gen_seg ]
        gen = SegmentState.state_chain_to_note_states(gen_seg)

    notes = NoteState.state_chain_to_notes(gen, bar)
    if not notes: return generate_song(mm, meta, bar, segmentation)
    song.append([ n.note_event() for n in notes ])

    return song, gen, notes

def generate_output():
    classifier = patterns.fetch_classifier()
    segmentation = False
    all_keys = False

    if len(sys.argv) == 4: # positional arguments: <midi-file> <start-bar> <end-bar>
        musicpiece = data.piece(sys.argv[1])
        musicpiece = musicpiece.segment_by_bars(int(sys.argv[2]), int(sys.argv[3]))
        mm = piece_to_markov_model(musicpiece, classifier, segmentation)

    else:
        pieces = ["mid/hilarity.mid", "mid/froglegs.mid", "mid/easywinners.mid"]
        mm = Markov() # initialize an empty model

        # generate a model _mm for each piece then add them together
        for p in pieces:
            musicpiece = data.piece(p)
            _mm = piece_to_markov_model(musicpiece, classifier, segmentation, all_keys)
            mm = mm.add_model(_mm)

    song, gen, notes = generate_song(mm, musicpiece.meta, musicpiece.bar, segmentation)
    midi.write('output.mid', song)

if __name__ == '__main__':
    generate_output()
