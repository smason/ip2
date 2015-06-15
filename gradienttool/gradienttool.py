from __future__ import absolute_import, division, print_function

import numpy          as np
import scipy.stats    as sps
import scipy.optimize as spo

def normaliseArray(x):
    mn = np.nanmin(x)
    mx = np.nanmax(x)
    return (x - mn) / (mx - mn)

def squaredDistance(x):
    "Calculate squared-distance between every pair of elements in the given vector"
    return (x - x[:,None]) ** 2

def covSquaredExponential(x, ell, sf):
    "Squared Exponential covariance function, as per covSEiso from GPML."
    return sf**2 * np.exp(-squaredDistance(x / ell) / 2)

def covNoise(x, s):
    "Independent covariance function, as per covNoise from GPML."
    return s**2 * np.eye(len(x))

def gpGaussPredict(x, y, xs, covfn):
    "Draw predictions from GP, given a Gaussian likelihood."

    K = covfn(x)
    m = np.zeros() # not needed?

    return np.array([])

class NamedMatrix:
    def __init__(self, colnames, rownames, data):
        assert data.shape == (len(rownames),len(colnames))
        self.colnames = colnames
        self.rownames = rownames
        self.data     = data

def readNamedMatrix(itr, dtype=np.float64):
    "Read a matrix that has a single row&column of names."
    hdr = next(itr)
    names = hdr[1:]
    rows = []
    data = []

    for l in itr:
        rows.append(l[0])
        data.append(l[1:])

    return NamedMatrix(names, rows, np.asarray(data, dtype=dtype))

class GradientTool:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.prior = sps.gamma(np.array([2.0, 2.0, 1.5]),
                               scale=np.array([0.2, 0.5, 0.1]))

    def rvTheta(self):
        "Draw a random theta from prior"
        return self.prior.rvs()

    def cov(self, theta, withnoise=True):
        "The covariance matrix for a given theta, with an optional noise term."
        m = covSquaredExponential(self.x, theta[0], theta[1]);
        if withnoise:
            m += covNoise(self.x, 1e-8 + theta[2])
        return m

    def loglik(self, theta):
        "Calculate the log-likelihood of this model for a given theta."
        # log-likelihood is product of data given multivariate normal and gamma
        # priors on theta
        return (sps.multivariate_normal.logpdf(self.y, mean=None, cov=self.cov(theta)) +
                self.prior.logpdf(theta).sum())

    def optimise(self, theta):
        "Optimise theta to find the parameters that result in maximum likelihood."
        # optimise log(theta) so they are constrained to be > 0
        return spo.minimize(lambda theta: -self.loglik(np.exp(theta)),
                            np.log(theta), method='Nelder-Mead')

if __name__ == "__main__":
    import time
    import sys
    import csv
    import re

    import scipy.io as sio

    import GPy

    mat = sio.loadmat('testdata/demData-out-2.mat')

    inp = readNamedMatrix(csv.reader(open("testdata/demData.csv")))

    theta = np.exp(mat['loghyper'][:,0])

    # remove the "TP" that has been prepended to the times
    t = [re.sub("^TP","",x) for x in inp.colnames]

    # convert colnames into a NumPy matrix and normalise
    t = normaliseArray(np.asarray(t, dtype=np.float64))

    xs = np.unique(t)

    # np.set_printoptions(precision=4, edgeitems=4, suppress=True)

    for i in range(0,2):
        t0 = time.time()

        m = GPy.models.GPRegression(t[:,None], inp.data[i,:][:,None])
        # set priors

        m.optimize()

        mu,var = m.predict(xs[:,None])
        mug,varg = m.predictive_gradients(xs[:,None])

        # print(mug[:,0,0])
        print(varg)

        theta = np.array([m.flattened_parameters[j].values[0] for j in range(3)])

        # delta = m.cov(theta, withnoise=False) - mat['CovMatrix']
        # print(np.percentile(delta,[0,0.25,0.5,0.75,1]))

        with open("out-%i.csv" % (i+1,),"w") as fd:
            out = csv.writer(fd)
            out.writerow(["time","mu","var","mug","varg"])

            for j in range(len(xs)):
                out.writerow([xs[j],mu[j,0],var[j,0],mug[j,0,0],varg[j,0]])

        print("time taken: %g\n" % (time.time()-t0))
