from __future__ import absolute_import, division, print_function

import sys
import optparse
import csv
import re
import itertools as it

import h5py as h5
import json

import logging

import numpy as np
import scipy as sp
import pandas as pd

import csi

logger = logging.getLogger('CSI')

def cmdparser(args):
    # create parser objects
    op = optparse.OptionParser()
    out = optparse.OptionGroup(op, "Output Formats")
    compat = optparse.OptionGroup(op, "Compatibility Options")

    op.set_usage("usage: %prog [options] FILE.csv")
    op.set_defaults(
        verbose=False,
        normalise=True,
        depth=2,
        depgenes=[])

    # define general parameters
    op.add_option('-v','--verbose',dest='verbose',action='count',
                  help="Increase verbosity (specify twice for more detail)")
    op.add_option('-d', '--depth',dest='depth',type='int',metavar='D',
                  help="Truncate parental set at depth D")
    op.add_option('--gene',dest='genes',action='append',metavar='GENE',
                  help="Limit analysis to a specific gene (repeat for more than one)")
    op.add_option('--mp',dest='numprocs',type='int',
                  help="Number of CPU cores (worker processes) to use")

    # define output parameters
    op.add_option_group(out)
    out.add_option('-o','--csv',dest='csvoutput',
                   help="write CSV output to FILE", metavar='FILE')
    out.add_option('--pdf',dest='pdfoutput',
                   help="write PDF output to FILE", metavar='FILE')
    out.add_option('--json',dest='jsonoutput',
                   help="write JSON output to FILE", metavar='FILE')
    out.add_option('--hdf5',dest='hdf5output',
                   help="write HDF5 output to FILE", metavar='FILE')

    # define compatibility options
    op.add_option_group(compat)
    compat.add_option('--weighttrunc',type='float', metavar='V',
                      help="Don't evaluate likelihoods whose weight is less than V")
    compat.add_option('--initweights',type='choice',metavar='TYPE',
                      choices=['uniform','weighted'],
                      help="Initialise weights as either 'uniform' or 'weighted'")

    # parse our command line arguments
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

    numprocs = op.numprocs
    if numprocs is not None and numprocs < 1:
        sys.stderr.write("Error: must have one or more worker process")
        sys.exit(1)

    # figure out where our output is going
    if op.csvoutput is None or op.csvoutput == '-':
        csvout = csv.writer(sys.stdout)
    else:
        csvout = csv.writer(open(op.csvoutput,'w'))

    if op.jsonoutput:
        jsonoutput = open(op.jsonoutput,'w')
    else:
        jsonoutput = None

    if op.hdf5output:
        hdf5output = h5.File(op.hdf5output,'w')
    else:
        hdf5output = None

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

    if hdf5output:
        cc.write_hdf5(hdf5output)

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
    for i,res in enumerate(csi.runCsiEm(em, genes, lambda gene: cc.allParents(gene,depth), numprocs)):
        res.writeCsv(csvout)
        results.append(res)
        if hdf5output:
            res.write_hdf5(hdf5output, i)

    if jsonoutput is not None:
        json.dump(cc.to_dom(results), jsonoutput)

    # plot in pdf?  an interactive html page may be better!

if __name__ == '__main__':
    main()
