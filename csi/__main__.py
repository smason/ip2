from __future__ import absolute_import, division, print_function

import sys
import optparse
import csv
import re

import numpy as np
import scipy as sp
import pandas as pd

import csi

def cmdparser(args):
    op = optparse.OptionParser()
    op.set_usage("usage: %prog [options] FILE.csv")
    op.set_defaults(verbose=False,normalise=True)
    op.add_option('-v','--verbose',dest='verbose',action='store_true',
                  help="display verbose output")
    op.add_option('-o','--csvoutput',dest='csvoutput',
                  help="write CSV output to FILE", metavar='FILE')
    op.add_option('-p','--pdfoutput',dest='pdfoutput',
                  help="write PDF output to FILE", metavar='FILE')
    return op.parse_args(args)

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    (op,fname) = cmdparser(args)

    if len(fname) == 0:
        sys.stderr.write("Error: Please specify the filename to process, or run with '-h' for more options\n")
        sys.exit(1)

    if len(fname) != 1:
        sys.stderr.write("Error: Only one input filename currently supported\n")
        sys.exit(1)

    inp = pd.read_csv(open(fname[0]),dtype=str,index_col=0,header=[0,1])
    inp.columns = pd.MultiIndex.from_tuples([(a,float(b)) for a,b in inp.columns],
                                            names=inp.columns.names)
    # convert to floating point values
    inp = inp.astype(float)

    # check whether we have two column headers and they are sorted
    assert (isinstance(inp.columns,pd.MultiIndex) and
            len(inp.columns.levels) == 2 and
            inp.columns.is_monotonic_increasing)
    # not sure whether I can do anything similar for the rows

    # from the command line?
    depth = 2

    if op.verbose:
        print("Genes:",
              ", ".join([repr(x) for x in inp.index]))
        print("Treatments:",
              ", ".join([repr(x) for x in inp.columns.levels[0]]))
        print("Time:",
              ", ".join([repr(x) for x in inp.columns.levels[1]]))

    cc = csi.Csi(inp)
    em = cc.getEm()

    for gene in inp.index:
        if op.verbose: print("Processing: ", repr(gene))

        em.setup(cc.allParents(gene,depth))

        ittr = 1
        while True:
            em.optimiseHypers()
            kl = em.reweight()
            if op.verbose: print("+ %2i: kl=%g,hypers=%s" % (ittr,kl,str(em.hypers)))
            if kl < 1e-5 or ittr > 20:
                break
            ittr += 1

        if op.verbose: print("+ finished")

if __name__ == '__main__':
    main()
