from __future__ import absolute_import, division, print_function

import sys
import optparse
import csv
import re
import itertools as it

import logging

import numpy as np
import scipy as sp
import pandas as pd

import csi

logger = logging.getLogger('CSI')

def cmdparser(args):
    op = optparse.OptionParser()
    op.set_usage("usage: %prog [options] FILE.csv")
    op.set_defaults(
        verbose=False,
        normalise=True,
        depth=2,
        depgenes=[])
    op.add_option('-v','--verbose',dest='verbose',action='count',
                  help="Increase verbosity (specify twice for more detail)")
    op.add_option('-o','--csvoutput',dest='csvoutput',
                  help="write CSV output to FILE", metavar='FILE')
    op.add_option('-p','--pdfoutput',dest='pdfoutput',
                  help="write PDF output to FILE", metavar='FILE')
    op.add_option('-d', '--depth',dest='depth',type='int',action='store',
                  help="Truncation depth for parental set")
    op.add_option('--gene',dest='genes',action='append',
                  help="Specific gene to analyse (specify again for more than one)")
    return op.parse_args(args)

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    # parse command line arguments
    (op,fname) = cmdparser(args)

    # extract out the logging level early
    log_level = logging.WARNING
    if   op.verbose == 1: log_level = logging.INFO
    elif op.verbose >= 2: log_level = logging.DEBUG

    # configure logger
    logging.basicConfig(level=log_level)
    logging.getLogger('GP').setLevel(logging.WARNING)
    logging.getLogger('parameters changed meta').setLevel(logging.WARNING)

    # make sure we're only processing a single file
    if len(fname) != 1:
        if len(fname) == 0:
            sys.stderr.write("Error: Please specify the filename to process, or run with '-h' for more options\n")
        else:
            sys.stderr.write("Error: Only one input filename currently supported\n")
        sys.exit(1)

    # pull out the parental set trunction depth and validate
    depth = op.depth
    if depth < 1:
        sys.stderr.write("Error: truncation depth must be greater than or equal to one")
        sys.exit(1)

    # sanity check!
    if depth == 1:
        logger.info("Truncation depth of 1 may not be very useful")

    # figure out where our output is going
    if op.csvoutput is None or op.csvoutput == '-':
        csvout = csv.writer(sys.stdout)
    else:
        csvout = csv.writer(open(op.csvoutput,'w'))

    # read in data and make sure headers are correct
    inp = pd.read_csv(open(fname[0]),dtype=str,index_col=0,header=[0,1])
    inp.columns = pd.MultiIndex.from_tuples([(a,float(b)) for a,b in inp.columns],
                                            names=inp.columns.names)
    # convert to floating point values
    inp = inp.astype(float)

    # check whether the second level is sorted (currently check whether all
    # levels are sorted, need to fix!)
    assert (inp.columns.is_monotonic_increasing)
    # not sure whether I can do anything similar for the rows

    if op.verbose:
        logger.info("Genes: %s",
                    ", ".join([repr(x) for x in inp.index]))
        logger.info("Treatments: %s",
                    ", ".join([repr(x) for x in inp.columns.levels[0]]))
        logger.info("Time: %s",
                    ", ".join([repr(x) for x in inp.columns.levels[1]]))

    # figure out which genes/rows we're going to process
    genes = op.genes
    if genes is None:
        logger.debug("No genes specified, assuming all")
        genes = list(inp.index)
    else:
        missing = np.setdiff1d(genes, inp.index)
        if len(missing) > 0:
            sys.stderr.write("Error: The following genes were not found: %s\n" %
                             ", ".join(missing))
            sys.exit(1)

    # TODO: how does the user specify the parental set?

    # start the CSI analysis
    cc = csi.Csi(inp)
    # we only know how to do expectation-maximisation at the moment
    em = cc.getEm()

    results = []

    # structure to store
    graph = csi.CsiGraph()

    for gene in genes:
        logger.info("Processing: %s", repr(gene))

        em.setup(cc.allParents(gene,depth))
        logger.debug("optimising")

        for ittr in range(1, 20):
            em.optimiseHypers()
            kl = em.reweight()
            logger.debug("%2i: kl=%10.4g, hypers=%s",
                         ittr,kl,str(em.hypers))
            if kl < 1e-5:
                break

        logger.debug("finished after %i iterations", ittr)

        res = em.getResults()
        res.writeCsv(csvout)

        results.append(res)

    # truncate graph at a given level
    df = pd.DataFrame(list(it.chain(*[r.getMarginalWeights() for r in results])),
                      columns=['regulator','target','weight'])
    dfm = df.groupby(["regulator","target"]).mean()
    dfm /= dfm.groupby("target").sum()
    print(dfm.sort('weight',ascending=False))

    # plot in pdf?  an interactive html page may be better!

if __name__ == '__main__':
    main()
