from __future__ import absolute_import, division, print_function

import csv
import re

import numpy as np
import scipy as sp

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import seaborn as sbs

import shared as ip2
import gradienttool as gt

def normaliseArray(x):
    """linearly scale a NumPy array @x such that the minimum is zero and the maximum is one."""
    mn = np.nanmin(x)
    mx = np.nanmax(x)
    return (x - mn) / (mx - mn)

def doReportPlot(fig, g, xtrans, ytrans, title=None,
                 CI=sp.stats.norm.ppf([0.025,0.975])):
    """Generate a pair of plots for the report"""
    res1 = g.getResults()
    ar = ip2.niceAxisRange(res1.index)
    res2 = g.getResults(np.linspace(ar[0],ar[1],101))

    # transform back to unnormalised space
    res1 = gt.transformResults(res1, xtrans, ytrans)
    res2 = gt.transformResults(res2, xtrans, ytrans)

    # extract for ease of access
    mu     = res2['mu']
    var    = res2['var']
    mud    = res2['mud']
    tscore = res1['tscore']

    # set up plots
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212, sharex=ax1)

    ax1.margins(0.04)
    ax2.set_ylim([-6,6])

    fig.tight_layout()

    if title is not None: ax1.set_title(title)

    # draw data, function and error bars
    ax1.fill_between(mu.index,
                     mu + CI[0]*np.sqrt(var + g.noiseVariance),
                     mu + CI[1]*np.sqrt(var + g.noiseVariance),
                     facecolor='black', edgecolor='none', alpha=0.05)
    ax1.fill_between(mu.index,
                     mu + CI[0]*np.sqrt(var),
                     mu + CI[1]*np.sqrt(var),
                     facecolor='royalblue', edgecolor='none', alpha=0.2)
    mu.plot(ax=ax1)
    # data goes at the end so it doesn't get hidden by everything else
    ax1.scatter(g.X * xtrans[1] + xtrans[0],
                g.Y * ytrans[1] + ytrans[0],
                marker='x', c='black', s=40, lw=1.2);

    # draw t-scores
    ax2.vlines(tscore.index, 0, tscore)
    ax2.plot(res2.index, res2['tscore'])
    for y in CI:
        ax2.axhline(y, lw=1, ls='--', color='black')

    return res1

def main():
    plt.switch_backend('pdf')

    import shared.filehandling as sfh

    inp = sfh.readCsvNamedMatrix(open('gradienttool/testdata/demData.csv'))

    # assume column headers are time, so remove anything that isn't
    # part of a number and convert into a NumPy matrix
    time = np.asarray([re.sub('[^0-9.]','',x) for x in inp.colnames],
                      dtype=np.float64)

    xtrans = (min(time), max(time)-min(time))
    ytrans = (np.mean(inp.data), np.std(inp.data))

    time = (time - xtrans[0]) / xtrans[1]

    gl = []
    with open('output.csv','w') as csvfd:
        csvout = csv.writer(csvfd)
        csvout.writerow(['item','X','f_mean','f_variance','df_mean','df_variance','tscore'])

        for i in range(inp.nrows()):
            # run the gradient tool
            g = gt.GradientTool(time, (inp.data[i,:] - ytrans[0]) / ytrans[1])
            g.setPriorRbfLengthscale(2.0, 0.2)
            g.setPriorRbfVariance(2.0, 0.5)
            g.setPriorNoiseVariance(1.5, 0.1)
            g.optimize()

            # save results for plotting
            gl.append(g)

            # write out to CSV file
            name = inp.rownames[i]
            res = gt.transformResults(g.getResults(), xtrans, ytrans)
            for i,k in res.iterrows():
                csvout.writerow([name,i]+k.tolist())

    # write out a nicely ordered PDF file
    with PdfPages('output.pdf') as pdf:
        for i in np.argsort([-g.rbfLengthscale for g in gl]):
            g = gl[i]

            fig = plt.figure(figsize=(8,7))
            res = doReportPlot(fig, g, xtrans, ytrans, title=inp.rownames[i])
            pdf.savefig()
            plt.close(fig)

if __name__ == '__main__':
    main()
