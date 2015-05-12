'''
recurrence_plot.py

Produces a recurrence plot from two input pieces
(most of the time piece1 = piece2 for self-similarity analysis)

'''


import data, patterns, sys
import numpy as np
from skimage import io
import matplotlib.pyplot as plt

def recurrence(c, piece1, piece2):
    plot = np.zeros((piece1.num_bars, piece2.num_bars), dtype=np.float)
    segment1 = [ piece1.segment_by_bars(i, i+1) for i in range(piece1.num_bars) ]
    segment2 = [ piece2.segment_by_bars(j, j+1) for j in range(piece2.num_bars) ]
    print "done 1/2"

    for i in range(piece1.num_bars):
        for j in range(piece2.num_bars):
            features = [segment1[i].compare_with(segment2[j])]
            score = c.predict_proba(features)[0][1]
            plot[i][j] = 0 if score >= 0.5 else 1 - score
            #plot[i][j] = 1 - score
    print "done 2/2"

    return np.fliplr(plot)


if __name__ == '__main__':
    c = patterns.fetch_classifier()

    if len(sys.argv) == 3:
        piece1 = data.piece(sys.argv[1])
        piece2 = data.piece(sys.argv[2])

    if len(sys.argv) == 2:
        piece1 = data.piece(sys.argv[1])
        piece2 = data.piece(sys.argv[1])

    plot = recurrence(c, piece1, piece2)
    io.imshow(plot)
    io.show()
