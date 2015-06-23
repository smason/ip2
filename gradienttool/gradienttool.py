from __future__ import absolute_import, division, print_function

import numpy as np
import scipy as sp
import shared.gradient as g
import GPy

def normaliseArray(x):
    mn = np.nanmin(x)
    mx = np.nanmax(x)
    return (x - mn) / (mx - mn)

class GradientTool:
    """Code for running WSBC's Gradient-Tool analysis

    :param X: time points
    :param Y: the readings values
    :param Xstar: where the gradient should be tested.
    """

    def __init__(self, X, Y, Xstar=None):
        assert len(X.shape) == 1
        assert X.shape == Y.shape
        if Xstar is None:
            # numpy.unique returns the elements already sorted
            Xstar = np.unique(X)
        self.Xstar = Xstar
        assert len(Xstar.shape) == 1
        self.m = GPy.models.GPRegression(X[:,None], Y[:,None])

    def setPriorRbfLengthscale(self, shape, rate):
        self.m.rbf.lengthscale.set_prior(GPy.priors.Gamma(shape, rate), warning=False)
    def setPriorRbfVariance(self, shape, rate):
        self.m.rbf.variance.set_prior(GPy.priors.Gamma(shape, rate), warning=False)
    def setPriorNoiseVariance(self, shape, rate):
        self.m.rbf.variance.set_prior(GPy.priors.Gamma(shape, rate), warning=False)

    def optimize(self):
        self.m.optimize()

    def getResults(self):
        """Returns a matrix with the data, latent function and derivative.

        Columns are as follows:
         0. the requested time points,
         1. the mean of the latent GP,
         2. the standard deviation of the latent GP,
         3. the mean of the derivative of the latent GP,
         4. the standard deviation of the derivative of the latent GP,
         5. the t-score of the estimated derivative.
        """
        mu,var = self.m.predict(self.Xstar[:,None])
        mud,vard = g.predict_derivatives(self.m, self.Xstar[:,None])
        mu,mud = mu.flatten(),mud.flatten()
        sd,sdd = np.sqrt(var.flatten()),np.sqrt(vard.flatten())
        return np.hstack((
            self.Xstar[:,None],
            mu[:,None],sd[:,None],
            mud[:,None],sdd[:,None],
            ((0-mud)/sdd)[:,None]))

    def plot(self,figure):
        res = self.getResults()
        self.m.plot(ax=figure.add_subplot(211),plot_limits=(-0.04,1.04))
        ax2 = figure.add_subplot(212)
        ax2.axis((-.04,1.04,-6,6))
        # draw 95% CI
        for y in sp.stats.norm.ppf([0.025,0.975]):
            ax2.axhline(y,lw=1,ls='--',c='black')
            ax2.vlines(res[:,0], [0], res[:,5]);

if __name__ == "__main__":
    import time
    import sys
    import csv
    import re

    import shared.filehandling as sfh

    import scipy.io as sio

    import GPy

    inp = sfh.readCsvNamedMatrix(open("gradienttool/testdata/demData.csv"))

    # remove the "TP" that has been prepended to the times
    t = [re.sub("^TP","",x) for x in inp.colnames]

    # convert colnames into a NumPy matrix and normalise
    t = normaliseArray(np.asarray(t, dtype=np.float64))

    np.set_printoptions(precision=4, edgeitems=4, suppress=True)

    for i in range(0,2):
        t0 = time.time()

        gt = GradientTool(t, inp.data[i,:])
        gt.setPriorRbfLengthscale(2.0, 0.2)
        gt.setPriorRbfVariance(2.0, 0.5)
        gt.setPriorNoiseVariance(1.5, 0.1)

        gt.optimise()


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
