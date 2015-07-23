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

    # exclude the target, duplicating list to avoid modifying callers
    # state
    l = list(items)
    l.remove(item)

    for i in range(0, depth+1):
        # iterate over every subset of size i
        for subset in it.combinations(l, i):
            yield (list(subset),item)

class CsiError(Exception):
    pass

class CsiEmFailed(CsiError):
    def __init__(self, res):
        super(CsiEmFailed, self).__init__("Failed to optimise parameters (%s)" % [repr(res.message)])
        self.res = res

class CsiEm(object):
    def __init__(self, csi):
        self.csi = csi
        self.X = csi.X.T
        self.Y = csi.Y.T
        self.hypers = sp.exp(sp.randn(3))
        self.pset = []

    def setup(self, pset):
        M = []
        for (i,j) in pset:
            if len(i) == 0:
                Xi = np.zeros((len(self.X),1))
            else:
                Xi = self.X.loc[:,i]
            Y = self.Y.loc[:,[j]]
            M.append(GPy.models.GPRegression(Xi, Y))
        self.pset    = pset
        self.models  = M
        self.weights = np.ones(len(M)) / len(M)

    def _optfn(self, x):
        ll = 0.
        grad = np.zeros(len(x))

        wmx = max(self.weights) * 1e-6
        for w,m in zip(self.weights,self.models):
            # weights are expected to be highly correlated with
            # expected likelihood, therefore no point evaluating
            # these
            if w < wmx:
                continue
            m[''] = x
            ll   += w * m.log_likelihood()
            grad += w * m.gradient
        return -ll, -grad

    def optimiseHypers(self):
        print(np.sum(self.weights > max(self.weights) * 1e-6))
        res = sp.optimize.minimize(self._optfn, self.hypers, jac=True,
                                   bounds=[(1e-8,None)]*len(self.hypers))
        if not res.success:
            raise CsiEmFailed(res)
        self.hypers = res.x
        return res

    def logliks(self):
        """Calculate the log-likelihood of each model"""
        ll = np.zeros(len(self.models))
        for i,m in enumerate(self.models):
            m[''] = self.hypers
            ll[i] = m.log_likelihood()
        return ll

    def reweight(self):
        """Recalculate the weights and return the KL divergence."""
        ll = self.logliks()
        # calculate the new weights
        w = np.exp(ll - max(ll))
        w /= np.sum(w)
        # update weights, saving old so we can calculate the KL divergence
        w0 = self.weights
        self.weights = w
        # calculate the KL divergence
        kl = w * np.log(w / w0)
        return kl[np.isfinite(kl)].sum()

class Csi(object):
    def __init__(self, data):
        self.data = data

        ix = np.array(list(getIndicies([a for a,b in iter(data.columns)])))
        self.X = data.iloc[:,ix-1]
        self.Y = data.iloc[:,ix]

    def allParents(self, item, depth):
        return list(parentalSets(self.data.index, item, depth))

    def getEm(self):
        return CsiEm(self)
