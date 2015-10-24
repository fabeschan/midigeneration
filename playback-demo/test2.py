import music21

def xtestPlayOneMeasureAtATime():
    b = music21.corpus.parse('bwv66.6')
    measures = [] # store for later
    maxMeasure = len(b.parts[0].getElementsByClass('Measure'))
    for i in range(maxMeasure):
        measures.append(b.measure(i))
    sp = music21.midi.realtime.StreamPlayer(b)

    for i in range(len(measures)):
        sp.streamIn = measures[i]
        sp.play()

xtestPlayOneMeasureAtATime()
