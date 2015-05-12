import numpy as np
import random as rd
from similar_sections import ss
import data, analyze, sys, time

class SegmentationTree(object):
    def __init__(self):
        self.label = label

def fetch_classifier():
    try:
        from sklearn.externals import joblib
        c = joblib.load('cached/classifier.pkl')
    except Exception, e:
        print e
        print "Retraining classifier..."
        from sklearn.externals import joblib
        c = analyze.train_classifier(analyze.generate())
        joblib.dump(c, 'cached/classifier.pkl')
    return c

class timer:
    def __init__(self, print_string):
        self.print_string = print_string

    def __enter__(self):
        self.start_time = time.time()

    def __exit__(self, type, value, traceback):
        self.end_time = time.time()
        elapsed = int(self.end_time - self.start_time)
        print self.print_string, '<time taken: {}m {}s>'.format(elapsed / 60, elapsed % 60)

def preprocess_segments(Piece, c):
    segs = {}
    d = {}

    with timer("Preprocess_segments: 1/2"):
        for k in range(1, Piece.num_bars + 1):
            print "Preprocess Segments: Part 1/2; Part {}/{}".format(k, Piece.num_bars)

            segs = {}
            for i in range(Piece.num_bars - k + 1):
                segment = Piece.segment_by_bars(i, i+k)
                segs[(i, i+k)] = segment

            for i in range(Piece.num_bars - k + 1):
                segment_i = segs[(i, i+k)]

                for j in range(Piece.num_bars - k + 1):
                    key = (i, j, k)
                    if i == j:
                        d[key] = 1.0
                        continue
                    same = d.get((j, i, k), [])
                    if same:
                        d[key] = same
                        continue

                    # get rid of overlapping intervals
                    if i <= j and j < i + k: continue
                    if j <= i and i < j + k: continue

                    if k > 4 and d[(i, j, k-1)] < 0.5:
                        d[key] = d[(i, j, k-1)]
                        continue

                    segment_j = segs[(j, j+k)]
                    features = [segment_i.compare_with(segment_j)]
                    score = c.predict_proba(features)[0][1]
                    d[key] = score

    with timer("Preprocess_segments: 2/2"):
        match = {}
        def is_overlap(j, k, l=[]):
            for i in l:
                if i <= j and j < i+k:
                    return True
                if j <= i and i < j+k:
                    return True
            return False

        bin_by_i_k = {}
        for key in d.keys():
            i, j, k = key
            l = bin_by_i_k.get((i, k), [])
            l.append(key)
            bin_by_i_k[(i, k)] = l

        # extract non-overlapping matches
        for k in range(1, Piece.num_bars + 1):
            for i in range(Piece.num_bars - k + 1):
                keys_same_k = bin_by_i_k[(i, k)]
                result = [x[1] for x in keys_same_k if d[x] >= 0.5]
                result.sort(key=lambda j: (-d[(i, j, k)], j))
                non_overlap = []
                for j in result:
                    if not is_overlap(j, k, non_overlap): non_overlap.append(j)

                match[(i, k)] = non_overlap

    segs = {} #TODO
    return segs, d, match

def default_scoring_fn(key, Piece, d, match):
    i, k = key
    freq_w = sum([ d[(i, j, k)] for j in match[key] ]) - 1 # a 'weighted' frequency
    k = k-1
    #sum_ = -freq_w**2 + (freq_w + k) * Piece.num_bars / 2 + -k**2 if match[key] else 0
    #return freq_w * k * k + k
    sum_ = -freq_w**2 + (freq_w + k) * Piece.num_bars / 2 + -k**2 if match[key] else 0
    return (sum_ * k * k * freq_w + k) / Piece.num_bars

def _default_scoring_fn(key, Piece, d, match):
    i, k = key
    #freq_w = sum([ d[(i, j, k)] for j in match[key] ]) - 1 # a 'weighted' frequency
    #k = k-1
    #sum_ = -(freq_w - 0)**2 + (freq_w + k) * Piece.num_bars + -k**2 if match[key] else 0
    #return (sum_ * (k-0) * freq_w * k + k) / Piece.num_bars
    sum_ = (sum([ d[(i, j, k)] for j in match[key] ]) - 1) * k * k
    return sum_

def segmentation(Piece, d, match, scoring_fn=default_scoring_fn, start=0, dur=-1, section_prefix='', depth=0):

    if dur == -1:
        dur = Piece.num_bars

    with timer("Segmentation: 1/3 done"):
        score = {k: scoring_fn(k, Piece, d, match) for k in match.keys() if (k[0] >= start and k[0]+k[1] <= start+dur) }
        best = sorted(score.keys(), key=lambda x: -score[x]) # order the keys by their score

    with timer("Segmentation: 2/3 done"):
        # Find set of non-overlapping intervals with maximum total score (weighted interval scheduling)
        bin_by_end = {}
        for key in score.keys():
            i, k = key
            l = bin_by_end.get(i+k, [])
            l.append(key)
            bin_by_end[i+k] = l

        M = [0]
        intervals = []
        for n in range(1, dur + 1):
            key = max([k for k in bin_by_end.get(n, [])], key=lambda x: score[x] + M[x[0]])
            intervals.append(key)
            M.append(score[key] + M[key[0]])

        chosen = []
        n = 0
        while n < len(intervals):
            i, k = intervals[-n-1]
            chosen.append((i, k))
            n += k
        chosen = chosen[::-1]

        bestscore = [(b, score[b]) for b in best]
        chosenscore = [(b, score[b]) for b in chosen]

    with timer("Segmentation: 3/3 done"):
        labelled_sections = {}
        alphabet = 'ABCDEFGHIJKLMNOPQRSTOPWXYZ'
        alpha_i = 0
        for c1 in chosen:
            i, k = c1

            if c1 not in labelled_sections:
                mkeys = [ (j, k) for j in match[c1] ]
                for mk in mkeys:
                    labelled_sections[mk] = alphabet[alpha_i]
                alpha_i += 1

        labelled_chosen = [(b, labelled_sections[b]) for b in chosen]

        '''
        for c1 in chosen:
            label = labelled_sections[c1]
            start, dur = c1


            segmentation(Piece, d, match, default_scoring_fn, start, dur, section_prefix=label, depth+1)
        '''

    return chosenscore, chosen, score, labelled_sections, bestscore

if __name__ == '__main__':
    c = fetch_classifier()
    musicpiece = data.piece(sys.argv[1])

    if len(sys.argv) == 5: # midi-file, min_bars, start_bar_index, end_bar_index
        musicpiece = musicpiece.segment_by_bars(int(sys.argv[3]), int(sys.argv[4]))
        d = preprocess_segments(musicpiece, c)

    if len(sys.argv) == 6: # midi-file, b00, b01, b10, b11
        b00, b01, b10, b11 = [ int(n) for n in sys.argv[2:6] ]
        def compare_bars(musicpiece, c, b00, b01, b10, b11):
            one = musicpiece.segment_by_bars(b00, b01)
            two = musicpiece.segment_by_bars(b10, b11)
            features = [one.compare_with(two)]
            similarity_score = c.predict_proba(features)[0][1] # get similarity_score
            print "SIMPROB:", similarity_score
            headers = [ 'Feature' + str(i) for i in range(len(features[0])) ]
            features.insert(0, headers)
            from tabulate import tabulate
            print "FEATURES:\n", tabulate(features)

        compare_bars(musicpiece, c, b00, b01, b10, b11)
