import data, patterns, sys, cmm, chords
import numpy as np
from skimage import io
from matplotlib.pyplot import figure, show, cm

def mixture(chord_transitions, sc2):
    sc2 = cmm.NoteState.piece_to_state_chain(piece2, use_chords=True)
    x = np.zeros((len(sc2),), dtype=np.float)
    for i in range(len(sc2)-1):
        x[i] = 0 if (sc2[i].chord, sc2[i+1].chord) in chord_transitions else 1

    fig = figure()
    x.shape = 1, len(x)
    axprops = dict(xticks=[], yticks=[])
    barprops = dict(aspect='auto', cmap=cm.binary, interpolation='bicubic')
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.1], **axprops)
    ax.imshow(x, **barprops)
    show()

if __name__ == '__main__':
    c = patterns.fetch_classifier()

    chord_transitions = set()
    for i in range(1, len(sys.argv)-1):
        piece1 = data.piece(sys.argv[i])
        sc_ = cmm.NoteState.piece_to_state_chain(piece1, use_chords=True)
        schords = [s.chord for s in sc_ ]
        schords2 = []
        for i in range(1, 6):
            schords2 += [ chords.translate(chords.untranslate(s.chord.split('m')[0])+i) + ('m' if 'm' in s.chord else '') for s in sc_ ]
        for i in range(1, 7):
            schords2 += [ chords.translate(chords.untranslate(s.chord.split('m')[0])-i) + ('m' if 'm' in s.chord else '') for s in sc_ ]
        schords += schords2

        # assume chain length is 1
        chord_transitions = chord_transitions.union({(schords[i], schords[i+1]) for i in range(len(schords)-1)})

    piece2 = data.piece(sys.argv[-1])

    mixture(chord_transitions, piece2)

