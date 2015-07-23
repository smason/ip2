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

class CsiError(Exception):
    pass

class CsiEmFailed(CsiError):
    def __init__(self, res):
        super(CsiEmFailed, self).__init__("Failed to optimise parameters (%s)" % [repr(res.message)])
        self.res = res

class CsiEm(object):
    def __init__(self, csi):
        self.csi = csi
        self.X = csi.X
        self.Y = csi.Y
        self.hypers = sp.exp(sp.randn(3))

    def setup(self, item, pset):
        M = []
        Y = self.Y.iloc[:,item]
        for i in itX:
            M.append(GPy.models.GPRegression(self.X.iloc[:,list(i)],Y))
        self.models  = M
        self.weights = np.ones(len(M)) / len(M)

    def optimiseHypers(self):
        def fn(x):
            ll = 0.
            grad = np.zeros(len(x))

            weights = self.weights
            wmx = max(weights)
            for i in np.argsort(-weights):
                # weights are expected to be highly correlated with
                # expected likelihood, therefore no point evaluating
                # these
                if weights[i] < wmx * 1e-6:
                    continue
                m = M[i]
                m[''] = x
                ll   += weights[i] * m.log_likelihood()
                grad += weights[i] * m.gradient
            return -ll, -grad
        opt = sp.optimize.minimize(fn, self.hypers, jac=True,
                                   bounds=[(1e-8,None)]*len(self.hypers))
        if not opt.success:
            raise CsiEmFailed(res)
        self.hypers = opt.x
        return res

    def reweight(self):
        ll = np.zeros(len(self.M))
        for i,m in enumerate(self.M):
            m[''] = self.hypers
            ll[i] = m.log_likelihood()
        w = np.exp(ll - max(ll))
        self.weights = w / np.sum(w)
        return ll

class Csi(object):
    def __init__(self, data):
        self.data = data

        ix = np.array(list(getIndicies([a for a,b in iter(data.columns)])))
        self.X = data.T.iloc[slice(None),ix-1]
        self.Y = data.T.iloc[slice(None),ix]

    def allParents(self, item, depth):
        return list(parentalSets(range(inp.shape[0]), item, depth))

    def runEm(self, psets):
        pass

if __name__ == "__main__":
    import time
    import sys
    import csv

    import shared.filehandling as sfh

    with open("csi/testdata/Demo_DREAM.csv") as fd:
        data = sfh.readCsvNamedMatrix(fd)

    print(data)
