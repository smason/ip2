from __future__ import absolute_import, division, print_function

import numpy as np
import scipy as sp
import shared as ip2
import matplotlib.pyplot as plt

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
        """Returns a matrix with the data, latent function and derivative.

        Columns are as follows:
         0. the requested time points,
         1. the mean of the GP's latent function,
         2. the variance of the latent function,
         3. the mean of the derivative of the latent function,
         4. the variance of the derivative of the latent function,
         5. the t-score of the estimated derivative.
        """
        if Xstar is None:
            Xstar = np.unique(np.array(self.m.X))
        mu,var = self.m._raw_predict(Xstar[:,None])
        mud,vard = ip2.predict_derivatives(self.m, Xstar[:,None])
        mu,mud = mu.flatten(),mud.flatten()
        var,vard = var.flatten(),vard.flatten()
        return np.hstack((
            Xstar[:,None],
            mu[:,None],var[:,None],
            mud[:,None],vard[:,None],
            (mud/np.sqrt(vard))[:,None]))

    def plot(self,title=None,figure=None,ylim=(-6,6),Xstar=None):
        if figure is None:
            figure = plt.figure()
        # create space for our plots
        ax1 = figure.add_subplot(211)
        ax2 = figure.add_subplot(212, sharex=ax1)
        if title is not None:
            ax1.set_title(title)
        # extract estimates of derivative and tscores
        res  = self.getResults(Xstar)
        res2 = self.getResults(np.linspace(-0.04,1.04,101))
        # plot the data and GP
        self.m.plot(ax=ax1,plot_limits=(-0.04,1.04))
        # overlay the latent function
        ax1.fill_between(res2[:,0],
                         res2[:,1]+np.sqrt(res2[:,2])*sp.stats.norm.ppf(0.025),
                         res2[:,1]+np.sqrt(res2[:,2])*sp.stats.norm.ppf(0.975),
                         alpha=0.5,facecolor=Tango.colorsHex["mediumPurple"])
        # plot the t-scores
        ax2.plot(res2[:,0],res2[:,5])
        # set the axes up so we can see the area of interest
        if ylim is not None:
            ax2.set_ylim(ylim)
        # draw 95% CI
        for y in sp.stats.norm.ppf([0.025,0.975]):
            ax2.axhline(y,lw=1,ls='--',c='black')
        ax2.vlines(res[:,0], [0], res[:,5]);
        # figure.tight_layout()
