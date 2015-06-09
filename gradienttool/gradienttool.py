from __future__ import absolute_import, division, print_function

import numpy       as np
import scipy.stats as sps

def squaredDistance(x):
    "Calculate squared-distance between every pair of elements in the given vector"
    return (x - x[:,None]) ** 2

def covSquaredExponential(x, ell, sf2):
    "Squared Exponential covariance function, as per covSEiso from GPML."
    return sf2 * np.exp(-squaredDistance(x / ell) / 2)

def covNoise(x, s2):
    "Independent covariance function, as per covNoise from GPML."
    return s2 * np.eye(len(x))

class GaussianProcess:
    def __init__(self, cov):
        self.cov = cov

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

def calcGradients(x, y):
    def opt(theta):
        # parameters are constrained to be > 0
        theta = np.exp(theta)
        cov = (
            covSquaredExponential(x, theta[0], theta[1]) +
            covNoise(x, theta[2]))
        ll = (
            sps.multivariate_normal.logpdf(y, mean=None, cov=cov) +
            sps.gamma.logpdf(theta, 2))

if __name__ == "__main__":
    import sys
    import csv
    import re

    mat = readNamedMatrix(csv.reader(sys.stdin))

    # remove the "TP" that has been prepended to the times
    time = [re.sub("^TP","",x) for x in mat.colnames]

    # convert colnames into a NumPy matrix
    time = np.asarray(time, dtype=np.float64)

    print(mat.data.shape)
    print(time.shape)
