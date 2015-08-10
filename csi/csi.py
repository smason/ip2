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

    # exclude the target if needed
    if item in items:
        # duplicate list to avoid modifying callers state
        items = list(items)
        items.remove(item)

    for i in range(0, depth+1):
        # iterate over every subset of size i
        for subset in it.combinations(items, i):
            yield (list(subset),item)

class CsiError(Exception):
    pass

class CsiEmFailed(CsiError):
    def __init__(self, res):
        super(CsiEmFailed, self).__init__("Failed to optimise parameters (%s)" % [repr(res.message)])
        self.res = res

class EmRes(object):
    def __init__(self, em):
        self.hypers  = np.copy(em.hypers)
        self.weights = np.copy(em.weights)
        self.pset    = em.pset
        self.ll      = np.copy(em.logliks())

    def writeCsv(self, csvout):
        for i in np.argsort(-self.ll):
            pset    = self.pset[i]
            weights = self.weights[i]
            csvout.writerow(
                [pset[1],
                 ":".join(pset[0]),
                 weights]+
                self.hypers.tolist())

    def getMarginalWeights(self):
        # add all genes to our (directed) graph
        for pset,weight in zip(self.pset,self.weights):
            target = pset[1]
            for regulator in pset[0]:
                yield (regulator,target,weight)

class CsiEm(object):
    "Find MAP estimate via Expectation-Maximisation."
    def __init__(self, csi):
        self.csi = csi
        self.X = csi.X.T
        self.Y = csi.Y.T
        self.hypers = sp.exp(sp.randn(3))
        self.pset = []

    @property
    def hypers(self):
        return self._hypers

    @hypers.setter
    def hypers(self, value):
        self._hypers   = value
        self._updatell = True

    def setup(self, pset):
        "Configure model for EM using the specified parent set."
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
        """Return negated-loglik and gradient in a form suitable for use with
        SciPy's numeric optimisation."""
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
        """Re-optimise hyper-parameters of the given model, throwing exception
        on failure.
        """
        res = sp.optimize.minimize(self._optfn, self.hypers, jac=True,
                                   bounds=[(1e-8,None)]*len(self.hypers))
        if not res.success:
            raise CsiEmFailed(res)
        self.hypers = res.x
        return res

    def logliks(self):
        "Return the log-likelihood of each GP given the current hyperparameters"
        if not self._updatell:
            return self._ll
        ll = np.zeros(len(self.models))
        for i,m in enumerate(self.models):
            m[''] = self._hypers
            ll[i] = m.log_likelihood()
        self._ll       = ll
        self._updatell = False
        return ll

    def reweight(self):
        "Recalculate the weights and return the KL divergence."
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

    def getResults(self):
        return EmRes(self)

class Csi(object):
    "Perform CSI analysis on the provided data"
    def __init__(self, data):
        self.data = data

        ix = np.array(list(getIndicies([a for a,b in iter(data.columns)])))
        self.X = data.iloc[:,ix-1]
        self.Y = data.iloc[:,ix]

    def allParents(self, item, depth):
        "Utility function to calculate the parental set of the given item"
        return list(parentalSets(self.data.index, item, depth))

    def getEm(self):
        "For getting at a MAP estimate via expectation-maximisation."
        return CsiEm(self)
