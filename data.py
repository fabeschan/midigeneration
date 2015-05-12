import midi, sys, getopt
from decimal import Decimal as fixed

def edit_distance(s1, s2):
    m=len(s1)+1
    n=len(s2)+1

    tbl = {}
    for i in xrange(m): tbl[i,0]=i
    for j in xrange(n): tbl[0,j]=j
    for i in xrange(1, m):
        for j in xrange(1, n):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            tbl[i,j] = min(tbl[i, j-1]+1, tbl[i-1, j]+1, tbl[i-1, j-1]+cost)

    return tbl[i,j]

def edit_distance_norm(s1, s2):
    if len(s1) + len(s2) == 0: return 0.0
    return min(edit_distance(s1, s2) / float(len(s1) + len(s2)), 0.5)

class note(object):
    def __init__(self, note_event, pos_offset=0):
        self.pos = note_event[1] + pos_offset
        self.dur = note_event[2]
        self.chn = note_event[3]
        self.pitch = note_event[4]

    def note_event(self):
        return ['note', self.pos, self.dur, self.chn, self.pitch]

    def note_event_with_pos_offset(self, pos_offset):
        return ['note', self.pos + pos_offset, self.dur, self.chn, self.pitch]

    def copy(self):
        return note(self.note_event())

    def __repr__(self):
        return str([self.pos, self.dur, self.chn, self.pitch])

class track(object):
    def pitches(self): # augment to show better info
        return [ n.pitch for n in self.notes ]

    def get_notes(self, tr, pos_offset=0):
        notes = [note(n, pos_offset) for n in tr]
        return notes

    def get_durations(self):
        # notes: a list of note's
        positions = sorted(list(set([n.pos for n in self.notes])))
        l = []
        if not positions: return l
        prev_pos = positions[0]
        for p in positions:
            l.append(fixed(p) / self.ticks)
            prev_pos = p
        return l

    def get_positions(self):
        # notes: a list of note's
        positions = sorted(list(set([n.pos for n in self.notes])))
        l = []
        if not positions: return l
        for p in positions:
            l.append(fixed(p) / self.ticks)
        return l

    def get_bar_positions(self):
        l = []
        if not self.positions: return l
        for p in self.positions:
            l.append(p % self.bar)
        #print l
        return l

    def get_intervals(self):
        # return a list of integers which are the pitch differences
        # between one note and the next, based on topline

        l = []
        if not self.topline: return l
        prev_pitch = self.topline[0].pitch
        for n in self.topline:
            l.append(n.pitch - prev_pitch)
            prev_pitch = n.pitch
        return l

    def get_directions(self):
        r = []
        for v in self.intervals:
            if v < 0: r.append(-1)
            elif v > 0: r.append(1)
            else: r.append(0)
        return r

    def get_topline(self):
        # extract the list of highest, longest, non-overlapping notes
        # TODO: get chords too
        # for now assume notes are sorted by position

        notes, l = self.notes, []
        if not len(notes): return l

        i = 0
        while i < len(notes):
            common_starts = []
            cur_note = notes[i]
            for j in xrange(i, len(notes)):
                if not common_starts or notes[j].pos == cur_note.pos:
                    common_starts.append(notes[j])
                else:
                    i = j
                    break
            top_note = max(common_starts, key=lambda x: x.pitch)
            l.append(top_note)

            for j in notes[i:]:
                if j.pos < top_note.pos + top_note.dur:
                    i += 1
                else: break
        return l

    def get_botline(self):
        # extract the list of lowest, longest, non-overlapping notes
        # TODO: get chords too
        # for now assume notes are sorted by position

        notes, l = self.notes, []
        if not len(notes): return l

        i = 0
        while i < len(notes):
            common_starts = []
            cur_note = notes[i]
            for j in xrange(i, len(notes)):
                if not common_starts or notes[j].pos == cur_note.pos:
                    common_starts.append(notes[j])
                else:
                    i = j
                    break
            bot_note = max(common_starts, key=lambda x: x.pitch)
            l.append(bot_note)

            for j in notes[i:]:
                if j.pos < bot_note.pos + bot_note.dur:
                    i += 1
                else: break
        return l

    def get_absolute_pitches(self):
        # extract the list of pitches % 12 from topline
        if not self.topline: return []
        return [ n.pitch % 12 for n in self.topline ]

    def __init__(self, tr, meta, pos_offset=0):
        self.time_top = 4
        self.time_bottom = 4
        for event in meta:
            if event[0] == 'ticks': self.ticks = event[2]
            elif event[0] == 'time': #TODO: time sig could change
                self.time_top = event[2]
                self.time_bottom = event[3]

        self.bar = 4 * self.time_top / self.time_bottom
        self.notes = self.get_notes(tr)
        self.process()

    def process(self):
        self.topline = self.get_topline()
        self.botline = self.get_botline()
        self.positions = self.get_positions()
        self.bar_positions = self.get_bar_positions()
        self.intervals = self.get_intervals()
        self.directions = self.get_directions()
        self.absolute_pitches = self.get_absolute_pitches()
        return self

class piece(object):
    def __init__(self, filename_or_midi, filename=None, pos_offset=0):
        if isinstance(filename_or_midi, str):
            self.filename = filename_or_midi
            self.midi = midi.read(filename_or_midi)

            if self.midi == -1:
                raise Exception("ERROR: Failed reading {}".format(filename_or_midi))
        elif isinstance(filename_or_midi, list):
            self.filename = "NO_FILENAME"
            self.midi = filename_or_midi
        else:
            raise Exception("ERROR: invalid input to constructor of piece")

        if filename: self.filename = filename
        self.meta = self.midi[0] # meta track
        self.tracks = []
        self.unified_track = None
        self.pos_offset = pos_offset
        self.unified_midi = [self.midi[0]]

        self.unified_midi.append(self.midi[1][:])
        # add other tracks on top of track 1
        for i in range(2, len(self.midi)):
            tr = self.midi[i]
            self.unified_midi[1].extend(tr)

        self.unified_midi[1].sort(key = lambda v: (v[1], v[2]))
        track1 = track(self.unified_midi[1], self.meta, self.pos_offset)
        self.unified_track = track1
        self.bar = self.unified_track.bar * self.unified_track.ticks
        if self.unified_track.notes:
            total_length = self.unified_track.notes[-1].pos + self.unified_track.notes[-1].dur
        else:
            total_length = 0
        self.num_bars = (total_length + self.bar - 1) / self.bar

        for tr in self.midi[1:]:
            newtrack = track(tr, self.meta, self.pos_offset)
            self.tracks.append(newtrack)

    def transpose(self, offset=0):
        newmidi = []
        newmidi.append(self.midi[0])
        for tr in self.tracks:
            temp = [ n.copy() for n in tr.notes ]
            for n in temp:
                n.pitch += offset
            newmidi.append([ n.note_event() for n in temp ])
        p = piece(newmidi, self.filename)
        return p

    def segment(self, div_tick, only=''):
        div_tick = self.pos_offset + div_tick
        piece1midi, piece2midi = [], []
        piece1midi.append(self.midi[0])
        piece2midi.append(self.midi[0])

        for tr in self.tracks:
            # mark 'tied' notes
            notes_to_split = [ i for i in xrange(len(tr.notes)) if tr.notes[i].pos < div_tick and div_tick < tr.notes[i].pos + tr.notes[i].dur ]
            left = [ n for n in tr.notes if n.pos + n.dur <= div_tick ]
            right = [ n for n in tr.notes if div_tick <= n.pos ]

            center = [ tr.notes[i].copy() for i in notes_to_split ]
            for n in center:
                temp_dur = n.dur
                n.dur = div_tick - n.pos
                left.append(n.copy())

                n.dur = temp_dur - (div_tick - n.pos)
                n.pos = div_tick
                right.insert(0, n)

            if only != 'right':
                piece1midi.append([ n.note_event() for n in left ])
            if only != 'left':
                piece2midi.append([ n.note_event_with_pos_offset(-div_tick) for n in right ])

        if only == 'left':
            return piece(piece1midi, self.filename), None
        elif only == 'right':
            return None, piece(piece2midi, self.filename)
        else:
            return piece(piece1midi, self.filename), piece(piece2midi, self.filename)

    def split_by_bars(self, bar_0, bar_1=-1):
        # return only the specified bars from index bar_0 to bar_1 (end point exclusive)
        # return only bar_0 if bar_1 is -1
        # 0-based index
        if bar_1 == -1:
            offset = 1
        else:
            offset = bar_1 - bar_0
        left, right = self.segment((bar_0 + offset) * self.bar)
        left, center = left.segment(bar_0 * self.bar)
        return left, center, right

    def segment_by_bars(self, bar_0, bar_1=-1):
        if bar_1 == -1:
            offset = 1
        else:
            offset = bar_1 - bar_0
        left, right = self.segment((bar_0 + offset) * self.bar, only='left')
        left, center = left.segment(bar_0 * self.bar, only='right')
        return center

    def compare_with(self, other):
        edit_dists = []
        self_tr = self.unified_track
        other_tr = other.unified_track
        if True:
            ed0 = edit_distance_norm(self_tr.absolute_pitches, other_tr.absolute_pitches)
            ed1 = edit_distance_norm(self_tr.intervals, other_tr.intervals)
            ed2 = edit_distance_norm(self_tr.bar_positions, other_tr.positions)
            ed3 = edit_distance_norm(self_tr.directions, other_tr.directions)
            edit_dists += [ed0, ed1, ed2, ed3]
        return edit_dists

if __name__ == '__main__':

    try:
        opts, args = getopt.getopt(sys.argv[1:], "", [])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        sys.exit(2)
    output = None
    verbose = False
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", "--help"):
            sys.exit()
        elif o in ("-o", "--output"):
            output = a
        else:
            pass
    else:
        def compare_two_pieces():
            if len(sys.argv) >= 3:
                piece1, piece2 = piece(sys.argv[1]), piece(sys.argv[2])
                print piece1.compare_with(piece2)
            else:
                from similar_sections import ss
                for k,v in ss.pair_dict.keys():
                    piece1, piece2 = piece(k), piece(v)
                    print (k, v), piece1.compare_with(piece2)
        compare_two_pieces()


