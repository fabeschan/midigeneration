'''
analyze.py

This file sets up infrastructure for the similarity measure using a classifier
that compares two music segments and gives a score between 0 and 1

'''

from sklearn import datasets, neighbors, linear_model, svm
from sklearn.metrics import confusion_matrix
import numpy as np
import random
from similar_sections import ss
import sys

class train_set(object):
    def  __init__(self, data, target):
        self.data = data
        self.target = target

def generate():
    gen = ss.generate_targets_subset()
    random.shuffle(gen)
    target = np.array([ v[2] for v in gen ])
    data = np.array([ f[0].compare_with(f[1]) for f in gen ])
    return train_set(data, target)

def train_classifier(sdata, classifier=None):
    digits = sdata

    X_digits = digits.data
    y_digits = digits.target

    n_samples = len(X_digits)

    # data
    X_train = X_digits[:]
    y_train = y_digits[:]

    if not classifier:
        #classifier = svm.NuSVC(nu=0.01, probability=True)
        #classifier = linear_model.RidgeClassifierCV()
        classifier = linear_model.LogisticRegression(C=3.0)

    classifier_fit = classifier.fit(X_train, y_train)
    return classifier_fit


def test(sdata, classifier=None, verbose=True, verboseverbose=False):
    digits = sdata

    X_digits = digits.data
    y_digits = digits.target

    n_samples = len(X_digits)

    # data
    X_train = X_digits[:.85 * n_samples]
    y_train = y_digits[:.85 * n_samples]

    # truths/target
    X_test = X_digits[.85 * n_samples:]
    y_test = y_digits[.85 * n_samples:]

    if not classifier:
        classifier = linear_model.RidgeClassifierCV()

    classifier_fit = classifier.fit(X_train, y_train)

    pred = classifier_fit.predict(X_test)
    score = classifier_fit.score(X_test, y_test)

    if verboseverbose:
        # print the matrix of feature scores
        big_matrix = np.array([ np.hstack((X_test[i], y_test[i])) for i in xrange(len(X_test)) ])
        print ['Tr0Rhyt','Tr0TopL','Tr1Rhyt','Tr1TopL','Truth']
        print big_matrix
    if verbose:
        print 'TRUTH:', y_test
        print 'PREDN:', pred
        print ('Classifier score: %f' % score)

    return score, pred, y_test

def evaluate_n(n, sdata, classifier):
    avg_score = 0.0
    pred_overall, y_test_overall = np.array([]), np.array([])
    for i in xrange(n):
        score, pred, y_test = test(sdata, classifier, verbose=False if n > 1 else True)
        avg_score += score / n
        pred_overall = np.hstack((pred_overall, pred))
        y_test_overall = np.hstack((y_test_overall, y_test))

        sys.stdout.write("\r(Progress: %d/%d)" % (i, n))
        sys.stdout.flush()
    else:
        sys.stdout.write("\r")
        sys.stdout.flush()

    print "---- Num of Repetitions:", n
    print "---- Average Score:", avg_score
    np.set_printoptions(linewidth=999999)
    print confusion_matrix(y_test_overall, pred_overall)

if __name__ == '__main__':

    # three classifiers to choose from omgz
    svm = svm.NuSVC(nu=0.02)
    ridge = linear_model.RidgeClassifierCV()
    knn = neighbors.KNeighborsClassifier()
    lr = linear_model.LogisticRegression(C=10.0)

    n = 40

    if len(sys.argv) == 2:
        n = int(sys.argv[1])

    evaluate_n(n, generate(), lr)
