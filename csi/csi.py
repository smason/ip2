import numpy as np
import scipy as sp
import GPy

import itertools as it

def getIndicies(x):
    """Returns indicies, [i], where item $x_i = x_{i-1}$."""
    prev = None
    for i, a in enumerate(x):
        if a == prev:
            yield i
        prev = a

def parentalSets(items, item, depth):
    """Iterate over all "Parental Sets".

    A parental set is a list of regulators/transcription factors for a
    specific gene.  The parental sets for any given item is every
    subset of items up to a given depth that does not include the
    item.
    """

    # exclude the target, duplicate list to avoid modifying callers
    # state
    l = list(items)
    l.remove(item)

    for i in range(0, depth+1):
        # iterate over every subset of size i
        for subset in it.combinations(l, i):
            yield (item,list(subset))

class CsiEm(object):
    def __init__(self, X):
        self.X = X

    def setup(self, item, pset):
        Y = self.X.iloc[item]

class Csi(object):
    def __init__(self, X):
        self.data = X

        ix = np.array(list(getIndicies([a for a,b in iter(X.columns)])))
        self.X = X.iloc[slice(None),ix-1].T
        self.Y = X.iloc[slice(None),ix].T

    def allParents(self, item, depth):
        return list(parentalSets(inp.shape[0], item, depth))

    def runEm(self, psets):


if __name__ == "__main__":
    import time
    import sys
    import csv

    import shared.filehandling as sfh

    with open("csi/testdata/Demo_DREAM.csv") as fd:
        data = sfh.readCsvNamedMatrix(fd)

    print(data)
