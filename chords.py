"""
chords.py

Implements some tools to help identifying chords

1. Chord Templates
2. Chord Generator
3. Classifier

"""

from sklearn import linear_model, svm
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
import numpy as np
import random, sys
from IPython import embed
import analyze, data

def translate(pitch):
    d = {
        0: 'C',
        1: 'C#/Db',
        2: 'D',
        3: 'D#/Eb',
        4: 'E',
        5: 'F',
        6: 'F#/Gb',
        7: 'G',
        8: 'G#/Ab',
        9: 'A',
        10: 'A#/Bb',
        11: 'B',
    }
    return d[pitch%12]

def untranslate(pitch):
    d = {
        'C': 0,
        'C#/Db': 1,
        'D': 2,
        'D#/Eb': 3,
        'E': 4,
        'F': 5,
        'F#/Gb': 6,
        'G': 7,
        'G#/Ab': 8,
        'A': 9,
        'A#/Bb': 10,
        'B': 11,
    }
    return d[pitch]

class note_frequency(object):
    def __init__(self):
        self.frequency_table = [0]*12 # 12 semitones

    def add(self, n):
        self.frequency_table[n.pitch%12] += n.dur

    def copy(self):
        nf = note_frequency()
        nf.frequency_table = self.frequency_table[:]
        return nf

    def normalize(self):
        nf = note_frequency()
        total_dur = sum(f for f in self.frequency_table)
        if total_dur == 0: return self
        nf.frequency_table = [ float(f)/total_dur for f in self.frequency_table ]
        return nf

    def __sub__(self, other):
        nf = note_frequency()
        nf.frequency_table = [ self.frequency_table[i] - other.frequency_table[i] for i in range(12) ]
        return nf

    def __str__(self):
        return str(self.frequency_table)

    def to_list(self):
        return self.frequency_table[:]

class chord_template(object):

    def __init__(self, name, prefix, template, auxiliary=[]):
        '''
        Example:
        name: Minor Triad
        prefix: m
        template: [0, 3, 7]
        auxiliary: [other semitones]
        '''
        self.name = name
        self.prefix = prefix
        self.template = template
        self.auxiliary = auxiliary


class chord_generator(object):

    def __init__(self, templates, bar, div):

        self.templates = templates
        self.bar = bar
        self.div = div

    @staticmethod
    def default_generator():
        templates = []
        templates.append(chord_template('Major Triad', '', [0, 4, 7], [2, 5, 9, 11]))
        templates.append(chord_template('Minor Triad', 'm', [0, 3, 7], [2, 5, 8, 11]))
        #templates.append(chord_template('Dom7', '7', [0, 4, 7, 10]))
        #templates.append(chord_template('Dim7', '7m', [0, 3, 6, 9]))
        return chord_generator(templates, bar=4*1024, div=16)

    def generate(self, k):
        ''' generate k bar's worth of note_frequency for each template
            total generated = k * len(templates)
        '''

        for k_ in range(k):
            for ctemplate in self.templates:
                for tonic in range(12):
                    nf = note_frequency()
                    for i in range(self.div + random.choice(range(self.div))):
                        pitch = random.choice(ctemplate.template * 1 + ctemplate.auxiliary * 0) # auxiliary * 0 means no noise
                        dur = self.bar / self.div
                        n = data.note(['note', 0, dur, 0, tonic + pitch])
                        nf.add(n)
                    yield tonic, ctemplate, nf

class chord_classifier(object):

    def __init__(self, c):
        self.classifier = c
        self.gen = chord_generator.default_generator()

    def generate_train_set(self, k=-1):
        if k == -1: k = 500

        gen = []
        for tonic, ctemplate, nf in self.gen.generate(k):
            gen.append((nf, translate(tonic) + ctemplate.prefix))
        print 'Total number of samples:', len(gen)

        random.shuffle(gen)
        target = np.array([ v[1] for v in gen ])
        data = np.array([ f[0].normalize().to_list() for f in gen ])
        return analyze.train_set(data, target)

    def test(self, k=-1, n=10):
        analyze.evaluate_n(n, self.generate_train_set(k), self.classifier)

    def train(self):
        self.classifier = analyze.train_classifier(self.generate_train_set(), self.classifier)

    def predict(self, piece):
        nf = note_frequency()
        for n in piece.unified_track.notes:
            nf.add(n)
        ta = np.array(nf.normalize().to_list())
        print 'Key Signature :', self.classifier.predict(ta)

        allbars = []
        for i in range(piece.num_bars):
            nf = note_frequency()
            p = piece.segment_by_bars(i, i+1)
            for n in p.unified_track.notes:
                nf.add(n)
            ta = np.array(nf.normalize().to_list())
            predicted = self.classifier.predict(ta)
            allbars.append(predicted[0])
        return allbars

def freq_integral(object):

    def __init__(self, piece):
        bin_by_pos = {}
        for n in piece.unified_track.notes:
            v = bin_by_pos.get(n.pos, [])
            v.append(n)
            bin_by_pos[n.pos] = v

        positions = sorted(bin_by_pos.keys())

        self.piece = piece
        self.integral = {}
        nf = note_frequency()
        for pos in positions:
            for n in bin_by_pos[pos]:
                nf.add(n)

def fetch_classifier():
    rforest = RandomForestClassifier(n_estimators=100)
    cc = chord_classifier(rforest)

    try:
        from sklearn.externals import joblib
        c = joblib.load('cached/chord-classifier.pkl')
        cc.classifier = c
    except Exception, e:
        print e
        print "Retraining classifier..."
        cc.train()
        joblib.dump(cc.classifier, 'cached/chord-classifier.pkl')
    return cc


def chord_truths():
    l = []

    d = {}
    d['piece'] = 'mid/Enya_FWIA.MID'
    d['chords'] = [
        'D', 'D', 'Bm', 'D', 'C',
        'D', 'G', 'A', 'D', 'Bm',
        'D', 'C', 'D', 'G', 'D',
        'G', 'A', 'D', 'G', 'Bm',
        'G', 'D', 'G', 'Bm', 'G',
        'A', 'D', 'Bm', 'D', 'C',
        'D', 'G', 'D', 'G', 'D',
        'G', 'A', 'D', 'D']
    l.append(d)

    d = {}
    d['piece'] = 'mid/Enya_Lothlorien.MID'
    d['chords'] = [
        'Am', 'Em', 'Am', 'Em',
        'C', 'G', 'C', 'Am',
        'C', 'G', 'C', 'Em', 'Em',
        'Am', 'Em', 'Am', 'Em',
        'C', 'G', 'C', 'Am',
        'C', 'G', 'C', 'Em', 'Em',
        'Am', 'Em', 'Am', 'Em',
        'C', 'G', 'C', 'Am',
        'C', 'G', 'C',
        'Em', 'Em', 'Em', 'Em']
    l.append(d)

    d = {}
    d['piece'] = 'mid/moonlight_sonata.mid'
    d['chords'] = [
        'C#m', 'C#m', 'Am', 'C#m', 'C#m', 'G#', 'C#m', 'Em', 'Em', 'Em', 'G', 'Cm', 'Bm', 'Bm', 'Bm', 'Em', 'B', 'Em', 'Bm', 'C#', 'Gm', 'F#m', 'F#m', 'C#m', 'F#m', 'G#', 'C#m', 'G#', 'G#', 'C#m', 'C#m', 'B#m', 'C#m', 'C#m', 'B#m', 'B#m', 'B#m', 'G#', 'G#', 'G#', 'G#', 'C#m', 'G#', 'C#m', 'Em', 'Em', 'B', 'Em', 'G#', 'Dm', 'C#m', 'F#m', 'F#m', 'C#m', 'F#m', 'C#m', 'Am', 'F#m', 'C#m', 'C#m', 'G#', 'C#m', 'B#m', 'C#m', 'B#m', 'C#m', 'C#m', 'C#m', 'C#m']
    l.append(d)

    return l

if __name__ == '__main__':
    svc = svm.SVC(kernel='rbf', C=10000)
    rforest = RandomForestClassifier(n_estimators=100)
    lr = linear_model.LogisticRegression(C=1)

    if len(sys.argv) == 1:
        max_ = 0
        count, scores = 0, []
        truth = chord_truths()[0]
        musicpiece = data.piece(truth['piece'])
        from sklearn.externals import joblib
        while count < 30:
            #cc = chord_classifier(rforest)
            #cc.train()
            cc = fetch_classifier()
            allbars = cc.predict(musicpiece)
            s = 0
            for i in range(len(truth['chords'])):
                if truth['chords'][i] == allbars[i]:
                    s += 1
            print 'Correct Score: {}/{}'.format(s, len(truth['chords']))
            count += 1
            scores.append(s)
            print 'Count =', count

            #if s > max_ and s > 38:
            #    max_ = s
            #    joblib.dump(cc.classifier, 'cached/chord-classifier.pkl')
        print 'Max =', max(scores)
        print 'Min =', min(scores)
        print 'Mean =', sum(scores) / float(count)
        print 'Stddev =', np.std(np.array(scores))

    elif len(sys.argv) == 2:
        musicpiece = data.piece(sys.argv[1])
        cc = fetch_classifier()
        allbars = cc.predict(musicpiece)
        for i, predicted in enumerate(allbars):
            print 'Bar {}:'.format(i), predicted
        embed()

