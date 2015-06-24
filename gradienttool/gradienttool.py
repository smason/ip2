from __future__ import absolute_import, division, print_function

import numpy as np
import scipy as sp
import shared.gradient as g
import matplotlib.pyplot as plt

import GPy

def normaliseArray(x):
    mn = np.nanmin(x)
    mx = np.nanmax(x)
    return (x - mn) / (mx - mn)

class GradientTool:
    """Code for running WSBC's Gradient-Tool analysis

    :param X: time points
    :param Y: the readings values
    """

    def __init__(self, X, Y):
        assert len(X.shape) == 1
        assert X.shape == Y.shape
        self.m = GPy.models.GPRegression(X[:,None], Y[:,None])

    def setPriorRbfLengthscale(self, shape, rate):
        self.m.rbf.lengthscale.set_prior(GPy.priors.Gamma(shape, rate), warning=False)
    def setPriorRbfVariance(self, shape, rate):
        self.m.rbf.variance.set_prior(GPy.priors.Gamma(shape, rate), warning=False)
    def setPriorNoiseVariance(self, shape, rate):
        self.m.rbf.variance.set_prior(GPy.priors.Gamma(shape, rate), warning=False)

    def optimize(self):
        self.m.optimize()

    def getResults(self, Xstar=None):
        """Returns a matrix with the data, latent function and derivative.

        Columns are as follows:
         0. the requested time points,
         1. the mean of the latent GP,
         2. the variance of the latent GP,
         3. the mean of the derivative of the latent GP,
         4. the variance of the derivative of the latent GP,
         5. the t-score of the estimated derivative.
        """
        if Xstar is None:
            Xstar = np.unique(np.array(self.m.X))
        mu,var = self.m.predict(Xstar[:,None])
        mud,vard = g.predict_derivatives(self.m, Xstar[:,None])
        mu,mud = mu.flatten(),mud.flatten()
        var,vard = var.flatten(),vard.flatten()
        return np.hstack((
            Xstar[:,None],
            mu[:,None],var[:,None],
            mud[:,None],vard[:,None],
            ((0-mud)/np.sqrt(vard))[:,None]))

    def plot(self,title=None,figure=None, ylim=(-6,6)):
        if figure is None:
            figure = plt.figure()
        # create space for our plots
        ax1 = figure.add_subplot(211)
        ax2 = figure.add_subplot(212, sharex=ax1)
        if title is not None:
            ax1.set_title(title)
        # extract estimates of derivative and tscores
        res = self.getResults()
        # plot the data and GP
        self.m.plot(ax=ax1,plot_limits=(-0.04,1.04))
        if ylim is not None:
            ax2.set_ylim(ylim)
        res2 = self.getResults(np.linspace(-0.04,1.04,101))
        ax2.plot(res2[:,0],res2[:,5])
        # draw 95% CI
        for y in sp.stats.norm.ppf([0.025,0.975]):
            ax2.axhline(y,lw=1,ls='--',c='black')
        ax2.vlines(res[:,0], [0], res[:,5]);
        # figure.tight_layout()

if __name__ == "__main__":
    import csv
    import re

    import seaborn as sbs
    from matplotlib.backends.backend_pdf import PdfPages

    plt.switch_backend("pdf")

    import shared.filehandling as sfh

    inp = sfh.readCsvNamedMatrix(open("gradienttool/testdata/demData.csv"))

    # assume column headers are time, so remove anything that isn't
    # part of a number
    t = [re.sub("[^0-9.]","",x) for x in inp.colnames]

    # convert colnames into a NumPy matrix and normalise
    t = normaliseArray(np.asarray(t, dtype=np.float64))

    with open("output.csv",'w') as csvfd:
        with PdfPages("output.pdf") as pdf:
            csvout = csv.writer(csvfd)
            csvout.writerow(["item","X","f_mean","f_variance","df_mean","df_variance","tscore"])

            for i in range(inp.nrows()):
                name = inp.rownames[i]

                gt = GradientTool(t, inp.data[i,:])
                gt.setPriorRbfLengthscale(2.0, 0.2)
                gt.setPriorRbfVariance(2.0, 0.5)
                gt.setPriorNoiseVariance(1.5, 0.1)

                gt.optimize()
                fig = plt.figure(figsize=(8,7))
                gt.plot(name,fig)
                pdf.savefig()
                plt.close(fig)

                for r in gt.getResults():
                    csvout.writerow([name]+r.tolist())
