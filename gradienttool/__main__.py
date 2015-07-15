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

    gl = []
    zeros = {}
    with open('output.csv','w') as csvfd:
        csvout = csv.writer(csvfd)
        csvout.writerow(['item','X','f_mean','f_variance','df_mean','df_variance','tscore'])

        for i in range(inp.nrows()):
            # run the gradient tool
            g = gt.GradientToolNormalised(time, inp.data[i,:], xtrans, ytrans)
            g.setPriorRbfLengthscale(2.0, 0.2)
            g.setPriorRbfVariance(2.0, 0.5)
            g.setPriorNoiseVariance(1.5, 0.1)
            g.optimize()

            # save results for plotting
            gl.append(g)

            # get the "results" out
            res = g.getResults()

            zt = gt.zerosLinearInterpolate(np.vstack([res.index,res["mud"]]).T)
            if len(zt) in zeros:
                zeros[len(zt)] = np.concatenate([zeros[len(zt)], zt])
            else:
                zeros[len(zt)] = zt

            # write out to CSV file
            name = inp.rownames[i]
            for i,k in res.iterrows():
                csvout.writerow([name,i]+k.tolist())

    # write out a nicely ordered PDF file
    with PdfPages('output.pdf') as pdf:
        for a,b in zeros.items():
            fig = plt.figure(figsize=(6,4))
            ax1 = fig.add_subplot(111)
            ax1.margins(0.04)
            ax1.hist(b, edgecolor='none')
            ax1.set_title("%i Gradient Inflections" % (a,))
            pdf.savefig()
            plt.close(fig)

        for i in np.argsort([-g.rbfLengthscale for g in gl]):
            g = gl[i]

            fig = plt.figure(figsize=(8,7))
            gt.doReportPlot(fig, g, title=inp.rownames[i])
            fig.tight_layout()
            pdf.savefig()
            plt.close(fig)

if __name__ == '__main__':
    main()
