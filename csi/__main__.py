from __future__ import absolute_import, division, print_function

import sys
import optparse
import csv
import re
import itertools as it
import json

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
    op.add_option('-p','--pdf',dest='pdfoutput',
                  help="write PDF output to FILE", metavar='FILE')
    op.add_option('--json',dest='jsonoutput',
                  help="write JSON output to FILE", metavar='FILE')
    op.add_option('-d', '--depth',dest='depth',type='int',action='store',
                  help="Truncation depth for parental set")
    op.add_option('--gene',dest='genes',action='append',
                  help="Specific gene to analyse (specify again for more than one)")
    compat = optparse.OptionGroup(op, "Compatibility Options")
    compat.add_option('--weighttrunc',type='float', metavar='TRUNC',
                      help="Don't evaluate likelihoods whose weight is less than TRUNC")
    compat.add_option('--initweights',type='choice',metavar='TYPE',
                      choices=['uniform','weighted'],
                      help="Initialise weights as either 'uniform' or 'weighted'")
    op.add_option_group(compat)
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

    if op.jsonoutput:
        jsonoutput = open(op.jsonoutput,'w')
    else:
        jsonoutput = None

    # load the data from disk
    inp = csi.loadData(fname[0])

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
                             ', '.join(missing))
            sys.exit(1)

    # TODO: how does the user specify the parental set?

    cc = csi.Csi(inp)
    em = cc.getEm()

    if op.weighttrunc:
        val = float(op.weightrunc)
        if 0 < val < 1:
            sys.stderr.write("Error: The weight truncation must be between zero and one\n")
            sys.exit(1)

        if val > 0.01:
            logger.warning("weight truncation should probably be less than 0.01")

        em.weightrunc = val

    if op.initweights:
        if op.initweights == 'uniform':
            em.sampleinitweights = False
        elif op.initweights == 'weighted':
            em.sampleinitweights = True
        else:
            sys.stderr.write("Error: Unrecognised initial weight mode: %s\n" %
                             op.initweights)
            sys.exit(1)

    results = []
    for res in csi.runCsiEm(em, genes, lambda gene: cc.allParents(gene,depth)):
        res.writeCsv(csvout)
        results.append(res)

    if jsonoutput is not None:
        json.dump(cc.to_json_dom(results), jsonoutput)

    # truncate graph at a given level
    df = pd.DataFrame(list(it.chain(*[r.getMarginalWeights() for r in results])),
                      columns=['regulator','target','weight'])
    dfm = df.groupby(['regulator','target']).sum()
    print(dfm.sort('weight',ascending=False))

    # plot in pdf?  an interactive html page may be better!

if __name__ == '__main__':
    main()
