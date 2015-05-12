'''
similar_sections.py

This file sets up training data for the similarity measure
that compares two music segments and gives a score between 0 and 1
(used by analysis.py)

'''

import random as rd
import data

class similar_sections:

    def __init__(self):
        self.pair_dict = {}
        self.pieces_dict = {}
        self.targets = []
        self.prefix = "__SSPREFIX-"
        self.uid = 1

    def get_prefix_uid(self):
        self.uid += 1
        return self.prefix + str(self.uid)

    def add_pair_mid(self, mid1, mid2):
        #self.pair_dict[(data.piece(mid1), data.piece(mid2))] = 1
        self.pair_dict[(mid1, mid2)] = 1

    def add_pair(self, piece1, piece2):
        u1 = self.get_prefix_uid()
        u2 = self.get_prefix_uid()
        self.pieces_dict[u1] = piece1
        self.pieces_dict[u2] = piece2
        self.pair_dict[(u1, u2)] = 1

    def add_pair_by_bars(self, filename, b00, b01, b10, b11):
        p = data.piece(filename)
        p1 = p.segment_by_bars(b00, b01)
        p2 = p.segment_by_bars(b10, b11)
        self.add_pair(p1, p2)

    def is_similar(self, mid1, mid2):
        if self.pair_dict.get((mid1, mid2), 0) == 1:
            return 1
        else:
            return pair_dict.get((mid2, mid1), 0)

    def generate_targets(self):
        if self.targets: return self.targets
        l = []

        # gather all file names into one list
        for k in self.pair_dict.keys():
            l.append(k[0])
            l.append(k[1])
        l = list(set(l))

        out_dict = self.pair_dict.copy()
        # loop through every combination
        for mid1 in l:
            for mid2 in l:
                if mid1 == mid2: pass
                elif (mid1, mid2) in out_dict.keys(): pass
                elif (mid2, mid1) in out_dict.keys(): pass
                else:
                    out_dict[(mid1, mid2)] = 0

        s = []
        for k, v in out_dict.iteritems():
            if self.prefix in k[0]: k0 = self.pieces_dict[k[0]]
            else: k0 = data.piece(k[0])
            if self.prefix in k[1]: k1 = self.pieces_dict[k[1]]
            else: k1 = data.piece(k[1])
            s.append((k0, k1, v))
        self.targets = s
        return s

    def generate_targets_subset(self):
        # produces the same list as generate_target() but limits the number of
        # elements which have target=0 to be (linearly) proportional to the number
        # elements which have target=1
        if self.targets: return self.targets
        l = []

        # gather all file names into one list
        for k in self.pair_dict.keys():
            l.append(k[0])
            l.append(k[1])
        l = list(set(l))

        out_dict = self.pair_dict.copy()
        # loop through every combination
        counter = 0
        for mid1 in l:
            for mid2 in l:
                if mid1 == mid2: pass
                elif (mid1, mid2) in out_dict.keys(): pass
                elif (mid2, mid1) in out_dict.keys(): pass
                else:
                    if counter > 4 * len(self.pair_dict.keys()) ** 1.5:
                        pass
                    else:
                        counter += 1
                        out_dict[(mid1, mid2)] = 0
        s = []
        for k, v in out_dict.iteritems():
            if self.prefix in k[0]: k0 = self.pieces_dict[k[0]]
            else: k0 = data.piece(k[0])
            if self.prefix in k[1]: k1 = self.pieces_dict[k[1]]
            else: k1 = data.piece(k[1])
            s.append((k0, k1, v))
        self.targets = s
        return s


ss = similar_sections()

# Scott Joplin, Easy Winners
ss.add_pair_mid("mid/easywinners_1.mid", "mid/easywinners_2.mid")

# Bach Inventions 1, 3, 4, 13
ss.add_pair_mid("mid/invention1_1.mid", "mid/invention1_2.mid")
ss.add_pair_mid("mid/invention1_3.mid", "mid/invention1_4.mid")
ss.add_pair_mid("mid/invention3_1.mid", "mid/invention3_2.mid")
ss.add_pair_mid("mid/invention3_3.mid", "mid/invention3_4.mid")
ss.add_pair_mid("mid/invention4_1.mid", "mid/invention4_2.mid")
ss.add_pair_mid("mid/invention4_2.mid", "mid/invention4_3.mid")
ss.add_pair_mid("mid/invention4_3.mid", "mid/invention4_1.mid")
ss.add_pair_mid("mid/invention4_4.mid", "mid/invention4_5.mid")
ss.add_pair_mid("mid/invention4_6.mid", "mid/invention4_7.mid")
ss.add_pair_mid("mid/invention13_1.mid", "mid/invention13_2.mid")
ss.add_pair_mid("mid/invention13_3.mid", "mid/invention13_4.mid")
ss.add_pair_mid("mid/invention13_5.mid", "mid/invention13_6.mid")

# Chopin, The Minute Waltz
#ss.add_pair_mid("mid/minutewaltz_1.mid", "mid/minutewaltz_2.mid")
#ss.add_pair_mid("mid/minutewaltz_3.mid", "mid/minutewaltz_4.mid")
ss.add_pair_by_bars("mid/minute_waltz_chopin.mid", 0, 4, 0, 4)
ss.add_pair_by_bars("mid/minute_waltz_chopin.mid", 4, 12, 12, 20)
ss.add_pair_by_bars("mid/minute_waltz_chopin.mid", 8, 12, 16, 20)
ss.add_pair_by_bars("mid/minute_waltz_chopin.mid", 20, 22, 22, 24)
ss.add_pair_by_bars("mid/minute_waltz_chopin.mid", 24, 26, 32, 34)

# Beethoven, Minuit in G Major
ss.add_pair_mid("mid/minuitGmajor_1.mid", "mid/minuitGmajor_2.mid")

# Twinkle Twinkle
ss.add_pair_by_bars("mid/twinkle_twinkle.mid", 0, 2, 8, 10)
ss.add_pair_by_bars("mid/twinkle_twinkle.mid", 2, 4, 6, 8)

# Carol of the Bells
ss.add_pair_by_bars("mid/caroltest.mid", 0, 2, 2, 4)
ss.add_pair_by_bars("mid/caroltest.mid", 24, 26, 26, 28)

# Owl
ss.add_pair_by_bars("mid/owl.mid", 0, 4, 4, 8)
ss.add_pair_by_bars("mid/owl.mid", 16, 20, 20, 24)
