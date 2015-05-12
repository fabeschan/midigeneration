import numpy as np
import sys
import analyze, midi, patterns
from data import *
import pprint
import matplotlib.pyplot as plt

pp = pprint.PrettyPrinter(indent=4)

class penalty(object):
    def __init__(self):
        self.new_voice = 20.0
        self.pitch_interval = 1.0
        self.silence = 30.0 / 512 # per tick
        self.collision = 10.0

def common_starts(notes):
    ''' Return a dictionary, key=start_pos, value=list of notes '''
    d = {}
    notes = sorted(notes, key=lambda v: (v.pos, v.dur))
    i, pos = 0, 0
    c_starts = []
    d[pos] = c_starts
    for cur in notes:
        if pos != cur.pos:
            pos = cur.pos
            c_starts = []
            d[pos] = c_starts
        c_starts.append(cur)
    if not d[0]: del d[0]
    return d

def all_combinations(commons, voices):
    ''' commons: a list of (notes, voices)

        returns: a list of list of (note, voice)
     '''
    ret = []
    for c in commons:
        commons_ = commons[:]
        commons_.remove(c)
        for voice in voices:
            voices_ = voices[:]
            voices_.remove(voice)
            combos = all_combinations(commons_, voices_)
            if not combos: ret += [ [(c, voice)] ]
            else:
                for combo in combos:
                    cross = False
                    for e_n, e_v in combo:
                        if e_n and e_v and voice and c:
                            if c.pitch > e_n.pitch and voice.pitch < e_v.pitch:
                                cross = True
                                break # do not add to ret to avoid voices crossing
                            if c.pitch < e_n.pitch and voice.pitch > e_v.pitch:
                                cross = True
                                break # do not add to ret to avoid voices crossing
                    if not cross:
                        ret += [ [(c, voice)] + combo for combo in combos ]
    return ret

def calculate_penalty(combo, best_so_far, best_so_far_pen, pen):
    ''' combo is a list of (note, last_note) '''
    penalty = 0
    #for n, v in combo:
    #    if not v:
    #        penalty += pen.new_voice
    #    else:
    #        #penalty += best_so_far_pen[v]
    #        pen_t_silence = (n.pos - v.pos - v.dur) * pen.silence
    #        pen_t_pitch_interval = abs(v.pitch - n.pitch) * pen.pitch_interval
    #        penalty += pen_t_silence + pen_t_pitch_interval

    best_so_far = best_so_far.copy()
    best_so_far_pen = best_so_far_pen.copy()
    for n, v in combo:
        best_so_far[n] = v
        if v:
            pen_t_silence = (n.pos - v.pos - v.dur) * pen.silence
            pen_t_pitch_interval = abs(v.pitch - n.pitch) * pen.pitch_interval
            best_so_far_pen[n] = best_so_far_pen[v] + pen_t_silence + pen_t_pitch_interval
        else:
            best_so_far_pen[n] = pen.new_voice

    voices = extract_voices(best_so_far)
    for v in voices:
        last_note = v[-1]
        penalty += best_so_far_pen[last_note]
    return penalty

class voice(object):
    def __init__(self, l=[]):
        self.val = l
    def __repr__(self):
        return self.val.__repr__()

def identify_voices(piece, pen=None, verbose=False):
    ''' underlying assumptions:
        - each note is entirely included in a voice
        - voice only spans 1 pitch at any one moment

        alg:
        - store best-so-far voice ending at each note
    '''
    # here assume piece has exactly one track (=tracks[0])
    iter = 0
    if not pen:
        pen = penalty()
    tr = piece.tracks[0]
    track_notes = tr.notes
    cs = common_starts(track_notes)
    best_so_far = {} # stores previous note in its voice given specified note
    best_so_far_pen = {} # stores penalty score of voice ending at specified note
    final_voices = set() # will get updated with the voices that we ultimately want in the end

    cs_keys = sorted(cs.keys())
    for k in cs_keys:
        commons = cs.get(k, []) # get list of notes that start at pos k
        # find a voice for each note in commons
        # find best combination that gives minimum overall penalty

        # do not need to consider voices that are too far away
        temp_best_so_far = { n:v for n, v in best_so_far.iteritems() if (k - n.pos - n.dur) * pen.silence < pen.new_voice }
        #print temp_best_so_far
        voices = temp_best_so_far.keys()
        print "\nvoices", len(voices)
        for i in xrange(len(commons)): # add new empty voices to the mix
            voices.append(None)
        combinations_temp = all_combinations(commons, voices) # first generate all combos

        # get rid of duplicates
        combinations = set()
        for combos in combinations_temp:
            t = frozenset(combo for combo in combos)
            combinations.add(t)
        print "\ncombo", len(combinations)

        # combo is a list of (note, voice). Choose best combo
        best_combo = min(combinations, key=lambda c: calculate_penalty(c, temp_best_so_far, best_so_far_pen, pen))
        lowest_penalty = calculate_penalty(best_combo, temp_best_so_far, best_so_far_pen, pen)

        for n, v in best_combo:
            if not v:
                best_so_far_pen[n] = pen.new_voice
                best_so_far[n] = None
            else:
                best_so_far_pen[n] = calculate_penalty([(n, v)], temp_best_so_far, best_so_far_pen, pen)
                best_so_far[n] = v
        sys.stdout.write("\r(Progress: %d/%d)" % (iter, len(cs_keys)))
        iter += 1
        sys.stdout.flush()
    else:
        sys.stdout.write("\r")
        sys.stdout.flush()

    return best_so_far, best_so_far_pen
    #pp.pprint(best_so_far)

def extract_voices(best_so_far):
    '''
    Reconstruct the voices
    '''
    voices = []
    all_notes = best_so_far.keys()
    #print "all:", all_notes
    while all_notes:
        all_notes = sorted(list(all_notes), key=lambda n: -n.pos)
        n = all_notes[0]
        voice = _extract_voice(best_so_far, n)
        #print "voice:", voice
        voices.append(voice)
        for a in voice:
            all_notes.remove(a)
            del best_so_far[a]
    return voices

def _extract_voice(best_so_far, n):
    voice = []
    if n in best_so_far and best_so_far[n] and best_so_far[n] in best_so_far:
        r = _extract_voice(best_so_far, best_so_far[n])
        r.append(n)
        return r
    else:
        return [n]

def plot_voices(voices, bar=0):
    for voice_ in voices:
        if voice_:
            x = [ n.pos for n in voice_ ]
            y = [ n.pitch for n in voice_ ]
            plt.step(x, y, marker='o', where='post')
            ax = plt.axes()
            start, end = ax.get_xlim()
            if bar:
                ax.xaxis.set_ticks(np.arange(start, end, bar))
                ax.xaxis.grid(True)
        else:
            print "WARNING: voice_ has no notes"
    plt.show()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        musicpiece = piece(sys.argv[1])
        #musicpiece = a4piece
        bar = musicpiece.bar
        print "BAR:", bar

    if len(sys.argv) == 1:
        commons = [3,4,2,3, None]
        voices = [1,2,3]
        combinations = all_combinations(commons, voices) # first generate all combos
        uniques = set()
        for combos in combinations:
            t = frozenset(combo for combo in combos)
            uniques.add(t)

        pp.pprint(uniques)

    if len(sys.argv) == 2:
        best_so_far, best_so_far_pen = identify_voices(musicpiece)
        voices = extract_voices(best_so_far)
        plot_voices(voices, bar)

    if len(sys.argv) == 4: # midi-file, b0, b1
        musicpiece = musicpiece.segment_by_bars(int(sys.argv[2]), int(sys.argv[3]))
        best_so_far, best_so_far_pen = identify_voices(musicpiece)
        voices = extract_voices(best_so_far)
        plot_voices(voices, bar)
