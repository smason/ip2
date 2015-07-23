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
            M.append(GPy.models.GPRegression(self.X.iloc[:,list(i)], Y))
        self.models  = M
        self.weights = np.ones(len(M)) / len(M)

    def _optfn(x):
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

    def optimiseHypers(self):
        opt = sp.optimize.minimize(_optfn, self.hypers, jac=True,
                                   bounds=[(1e-8,None)]*len(self.hypers))
        if not opt.success:
            raise CsiEmFailed(res)
        self.hypers = opt.x
        return res

    def reweight(self):
        """Recalculate the weights and return the KL divergence."""
        # calculate the loglik of each model
        ll = np.zeros(len(self.M))
        for i,m in enumerate(self.M):
            m[''] = self.hypers
            ll[i] = m.log_likelihood()
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
        self.X = data.T.iloc[slice(None),ix-1]
        self.Y = data.T.iloc[slice(None),ix]

    def allParents(self, item, depth):
        return list(parentalSets(range(self.data.shape[0]), item, depth))

    def getEm(self):
        return CsiEm(self)
