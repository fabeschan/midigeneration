'''
    experiments.py

    patterns.py is too big of a file, so here is a wrapper to help with segmentation
    but I suppose this file needs a better name...
'''


import data, sys, patterns
from IPython import embed
import pickle
from os.path import basename

class analysis(object):

    def __init__(self, Piece, c, b0=0, b1=-1):
        self.musicpiece = Piece
        if b1 == -1 or b1 > Piece.num_bars:
            b1 = Piece.num_bars
        self.musicpiece = Piece.segment_by_bars(b0, b1)
        self.fetch_preprocessed(c, b0, b1)
        self.segmentation()

    def fetch_preprocessed(self, c, b0, b1):
        noext = basename(self.musicpiece.filename)
        filename = 'cached/preprocessed-{}-{}-{}.pkl'.format(noext, b0, b1)
        try:
            f = open(filename, 'r')
            self.d, self.match = pickle.load(f)
            print 'Found previously preprocessed data; using that to reduce computation time'
        except Exception, e:
            print 'Previously preprocessed data not found. Computing them...'
            _, self.d, self.match = patterns.preprocess_segments(self.musicpiece, c)
            save = (self.d, self.match)
            f = open(filename, 'w')
            pickle.dump(save, f)
        return self

    def segmentation(self, scoring_fn=None):
        if scoring_fn:
            self.chosenscore, self.chosen, self.score, self.labelled_sections, self.bestscore = patterns.segmentation(self.musicpiece, self.d, self.match, scoring_fn)
        else:
            self.chosenscore, self.chosen, self.score, self.labelled_sections, self.bestscore = patterns.segmentation(self.musicpiece, self.d, self.match)
        return self

if __name__ == '__main__':
    c = patterns.fetch_classifier()

    def get_patterns(filename, b0, b1):
        musicpiece = data.piece(filename)
        a = analysis(musicpiece, c, b0, b1)
        chosenscore, chosen, labelled_sections = a.chosenscore, a.chosen, a.labelled_sections
        a.chosenlabels = [(b, labelled_sections[b]) for b in chosen]
        return a

    if len(sys.argv) == 4: # midi-file, start_bar_index, end_bar_index
        #musicpiece = data.piece(sys.argv[1])
        #chosenscore, chosen, score, labelled_sections, bestscore, chosen_labelled = get_patterns(musicpiece, int(sys.argv[2]), int(sys.argv[3]))
        a = get_patterns(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
    elif len(sys.argv) == 2: # midi-file
        a = get_patterns(sys.argv[1], 0, -1)

    #embed()
