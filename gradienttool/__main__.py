from __future__ import absolute_import, division, print_function

import csv
import re

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import seaborn as sbs

from gradienttool import GradientTool

def normaliseArray(x):
    "linearly scale a NumPy array @x such that the minimum is zero and the maximum is one."
    mn = np.nanmin(x)
    mx = np.nanmax(x)
    return (x - mn) / (mx - mn)

def main():
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

if __name__ == "__main__":
    main()
