from __future__ import absolute_import, division, print_function

import numpy as np
import scipy as sp
import shared as ip2
import matplotlib.pyplot as plt

import pandas as pd

import GPy
import GPy.plotting.matplot_dep.Tango as Tango

def zerosLinearInterpolate(xy):
    """Linearly interpolate to find all zeros from an evaluated function"""
    ii = np.where((np.diff(xy[:,1] < 0)))[0]
    out = np.empty(len(ii),dtype=xy.dtype)
    for j,i in enumerate(ii):
        x0,y0 = xy[i+0,[0,1]]
        x1,y1 = xy[i+1,[0,1]]

        m = (y0 - y1) / (x0 - x1)
        c = y1 - m*x1
        out[j] = -c/m
    return out

def transformResults(res, xtrans, ytrans):
    """Linearly transform results"""
    out = res.set_index(res.index * xtrans[1] + xtrans[0])

    out["mu"]   = out["mu"] * ytrans[1] + ytrans[0]
    out["var"]  = out["var"] * ytrans[1] ** 2
    out["mud"]  = out["mud"] * (ytrans[1]/xtrans[1])
    out["vard"] = out["vard"] * (ytrans[1]/xtrans[1])**2

    return out

def _test():
    assert np.allclose(0.5,zerosLinearInterpolate(np.array([[0,-0.5],
                                                            [1, 0.5]])))

class GradientTool:
    """Code for running WSBC's Gradient-Tool analysis

    :param X: time points
    :param Y: the readings values
    """

    def __init__(self, X, Y):
        assert len(X.shape) == 1
        assert X.shape == Y.shape
        self.X = X
        self.Y = Y
        self.m = GPy.models.GPRegression(X[:,None], Y[:,None])

    @property
    def rbfLengthscale(self): return float(self.m.rbf.lengthscale)
    @property
    def rbfVariance   (self): return float(self.m.rbf.variance)
    @property
    def noiseVariance (self): return float(self.m.Gaussian_noise.variance)

    def setPriorRbfLengthscale(self, shape, rate):
        self.m.rbf.lengthscale.set_prior(GPy.priors.Gamma(shape, rate), warning=False)
    def setPriorRbfVariance(self, shape, rate):
        self.m.rbf.variance.set_prior(GPy.priors.Gamma(shape, rate), warning=False)
    def setPriorNoiseVariance(self, shape, rate):
        self.m.Gaussian_noise.variance.set_prior(GPy.priors.Gamma(shape, rate), warning=False)

    def optimize(self):
        self.m.optimize()

    def getResults(self, Xstar=None):
        """Returns a Pandas DataFrame of the latent function, its derivative and variances.

        The `index` is time"""

        # get the points we're evaluating the function at
        if Xstar is None:
            Xstar = np.unique(self.X)

        # get predictions of our function and its derivative
        mu,var = self.m._raw_predict(Xstar[:,None])
        mud,vard = ip2.predict_derivatives(self.m, Xstar[:,None])

        # put into a matrix
        out = np.empty((len(Xstar),5),dtype=self.Y.dtype)
        out[:,0] = mu[:,0]
        out[:,1] = var[:,0]
        out[:,2] = mud[:,0]
        out[:,3] = vard[:,0,0]
        out[:,4] = out[:,2]/np.sqrt(out[:,3])

        # convert to a DataFrame and return
        return pd.DataFrame(out, index=Xstar, columns=
                            ["mu","var","mud","vard","tscore"])
