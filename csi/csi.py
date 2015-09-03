import numpy as np
import scipy as sp
import scipy.optimize as spo
import scipy.stats as sps
import pandas as pd

import itertools as it

import csi

import logging
logger = logging.getLogger('CSI')

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

def logexp_optimise(fn, x):
    """Our 'LogExp' transform is taken from GPy and ensures that
    parameters are always greater than zero.
    """
    def transform(x):
        theta = logexp_to_natural(x)
        y,grad = fn(theta)
        # get gradients back to our space
        grad *= logexp_gradientfactor(theta)
        return (y,grad)
    res = spo.minimize(transform, natural_to_logexp(x), jac=True)
    res.x = logexp_to_natural(res.x)
    return res

def logexp_to_natural(x):
    return np.logaddexp(0., x)

def natural_to_logexp(f):
    # wrap in np.where to stop exp() of large values overflowing and
    # hence log giving back non-sensible values
    return np.where(f > 36., f, np.log(np.expm1(f)))

def logexp_gradientfactor(f):
    # no point wrapping in np.where as only small values will overflow
    # and they'll do that anyway
    return -np.expm1(-f)

class CsiError(Exception):
    pass

class CsiEmFailed(CsiError):
    def __init__(self, res):
        super(CsiEmFailed, self).__init__("Failed to optimise parameters (%s)" % [repr(res.message)])
        self.res = res

class CsiResult(object):
    def to_json_dom(self):
        raise NotImplementedError

class EmRes(CsiResult):
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

    def to_json_dom(self):
        return dict(restype="EM",
                    item=self.pset[0][1],
                    hyperparams=self.hypers.tolist(),
                    weights=self.weights.tolist(),
                    loglik=self.ll.tolist(),
                    parents=[a for (a,_) in self.pset])

class CsiEm(object):
    "Find MAP estimate via Expectation-Maximisation."
    def __init__(self, csi):
        self.csi = csi
        self.X = csi.X.T
        self.Y = csi.Y.T
        self.pset = []
        self.weighttrunc = 1e-5
        self.sampleinitweights = True

    @property
    def hypers(self):
        return self._hypers

    @hypers.setter
    def hypers(self, value):
        self._hypers   = value
        self._updatell = True

    def setup(self, pset):
        "Configure model for EM using the specified parent set."

        if self.sampleinitweights:
            # want to start with mostly singleton parental sets, so start
            # by calculating parental set sizes
            pl = np.array([len(a) for a,b in pset])
            # down-weight higher order parental sets
            w = sps.gamma.rvs(np.where(pl > 1, 1e-2, 0.5))
            # normalise weights to sum to one
            w /= np.sum(w)
        else:
            # all weights are equal
            w = np.ones(len(pset)) / len(pset)

        self.pset = pset
        self.hypers = sp.exp(sp.randn(3))
        self.weights = w

    def _loglik_pset(self, pset, theta):
        i,j = pset
        X = self.X.loc[:,[j]+i].values
        Y = self.Y.loc[:,[j]].values

        return csi.rbf_likelihod_gradient(X, Y, theta)

    def _optfn(self, x):
        """Return negated-loglik and gradient in a form suitable for use with
        SciPy's numeric optimisation."""

        logger.debug("     optfn(theta=%s)", str(x))

        ll = 0.
        grad = np.zeros(len(x))

        wmx = max(self.weights) * self.weighttrunc
        for w,pset in zip(self.weights,self.pset):
            # weights are expected to be highly correlated with
            # expected likelihood, therefore no point evaluating
            # these
            if w < wmx:
                continue

            m = self._loglik_pset(pset, x)

            ll   += w * m.loglik
            grad += w * m.gradient

        logger.debug("       optfn=%g", ll)

        return -ll, -grad

    def optimiseHypers(self):
        """Re-optimise hyper-parameters of the given model, throwing exception
        on failure.
        """
        res = logexp_optimise(self._optfn, self.hypers)
        if not res.success:
            raise CsiEmFailed(res)
        self.hypers = res.x
        return res

    def logliks(self):
        "Return the log-likelihood of each GP given the current hyperparameters"
        if not self._updatell:
            return self._ll
        ll = np.zeros(len(self.pset))
        for i,pset in enumerate(self.pset):
            ll[i] = self._loglik_pset(pset, self._hypers).loglik
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
        return kl.sum()

    def getResults(self):
        return EmRes(self)

class Csi(object):
    "Perform CSI analysis on the provided data"
    def __init__(self, data):
        self.data = data

        n = [a for a,b in data.columns.values]
        ix = np.flatnonzero(np.array([a==b for a,b in zip(n, n[1:])]))
        self.X = data.iloc[:,ix]
        self.Y = data.iloc[:,ix+1]

    def allParents(self, item, depth):
        "Utility function to calculate the parental set of the given item"
        return list(parentalSets(self.data.index, item, depth))

    def getEm(self):
        "For getting at a MAP estimate via expectation-maximisation."
        return CsiEm(self)

    def to_json_dom(self, res):
        "@res is a list of objects derived from CsiResult's"
        def c1(tup):
            a,(b,c) = tup
            return b
        def mkpair(a,l):
            l = list(l)
            i = [i for i,_ in l]
            v = [v for _,(_,v) in l]
            return (a,i,v)

        reps = [mkpair(a,b) for a,b in it.groupby(enumerate(self.data.columns),c1)]
        data = [[self.data.iloc[i,b].values.tolist() for a,b,c in reps]
                for i in range(self.data.shape[0])]

        return dict(replicates=[dict(id=a,time=c) for a,b,c in reps],
                    items=[dict(id=name) for name in self.data.index],
                    data=data,
                    results=[r.to_json_dom() for r in res])

def loadData(path):
    with open(path) as fd:
        # read in data and make sure headers are correct
        inp = pd.read_csv(fd,dtype=str,index_col=0,header=[0,1])
        inp.columns = pd.MultiIndex.from_tuples([(a,float(b)) for a,b in inp.columns],
                                                names=inp.columns.names)
        # convert to floating point values
        return inp.astype(float)

def runCsiEm(em, genes, fnpset):
    for gene in genes:
        logger.info("Processing: %s", repr(gene))

        em.setup(fnpset(gene))

        for ittr in range(1, 20):
            logger.debug("%2i: optimising hyperparameters",
                         ittr)
            em.optimiseHypers()
            logger.debug("%2i: recalculating weights",
                         ittr)
            kl = em.reweight()
            logger.debug("%2i: kl=%10.4g, hypers=%s",
                         ittr,kl,str(em.hypers))
            if kl < 1e-5:
                break

        logger.debug("finished after %i iterations", ittr)

        yield em.getResults()
