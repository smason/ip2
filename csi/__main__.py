from __future__ import absolute_import, division, print_function

import sys
import optparse
import csv
import re

import logging

import numpy as np
import scipy as sp
import pandas as pd

import csi

logger = logging.getLogger('CSI')

def cmdparser(args):
    op = optparse.OptionParser()
    op.set_usage("usage: %prog [options] FILE.csv")
    op.set_defaults(verbose=False,normalise=True)
    op.add_option('-v','--verbose',dest='verbose',action='count',
                  help="Increase verbosity (specify twice for more detail)")
    op.add_option('-o','--csvoutput',dest='csvoutput',
                  help="write CSV output to FILE", metavar='FILE')
    op.add_option('-p','--pdfoutput',dest='pdfoutput',
                  help="write PDF output to FILE", metavar='FILE')
    return op.parse_args(args)

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    (op,fname) = cmdparser(args)

    log_level = logging.WARNING
    if op.verbose == 1:
        log_level = logging.INFO
    elif op.verbose >= 2:
        log_level = logging.DEBUG

    logging.basicConfig(level=log_level)
    logging.getLogger('GP').setLevel(logging.WARNING)
    logging.getLogger('parameters changed meta').setLevel(logging.WARNING)

    if len(fname) == 0:
        sys.stderr.write("Error: Please specify the filename to process, or run with '-h' for more options\n")
        sys.exit(1)

    if len(fname) != 1:
        sys.stderr.write("Error: Only one input filename currently supported\n")
        sys.exit(1)

    if op.csvoutput is None:
        csvout = csv.writer(sys.stdout)
    else:
        csvout = csv.writer(open(op.csvoutput,'w'))

    inp = pd.read_csv(open(fname[0]),dtype=str,index_col=0,header=[0,1])
    inp.columns = pd.MultiIndex.from_tuples([(a,float(b)) for a,b in inp.columns],
                                            names=inp.columns.names)
    # convert to floating point values
    inp = inp.astype(float)

    # check whether we have two column headers and that the second
    # level is sorted (currently check whether all levels are sorted,
    # need to fix!)
    assert (isinstance(inp.columns,pd.MultiIndex) and
            len(inp.columns.levels) == 2 and
            inp.columns.is_monotonic_increasing)
    # not sure whether I can do anything similar for the rows

    # TODO: get this from the command line
    depth = 2

    if op.verbose:
        logger.info("Genes: %s",
                    ", ".join([repr(x) for x in inp.index]))
        logger.info("Treatments: %s",
                    ", ".join([repr(x) for x in inp.columns.levels[0]]))
        logger.info("Time: %s",
                    ", ".join([repr(x) for x in inp.columns.levels[1]]))

    # start the CSI analysis
    cc = csi.Csi(inp)
    # we only know how to do expectation-maximisation at the moment
    em = cc.getEm()

    for gene in inp.index:
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

        csvout.writerow([
            ])


if __name__ == '__main__':
    main()
