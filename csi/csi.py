import numpy as np
import scipy as sp
# import GPy

import itertools as it

def parentalSets(items, item, depth):
    """Iterate over all "Parental Sets".

    A parental set is a list of potential regulators/transcription
    factors of a gene.
    """

    l = list(items)
    l.remove(item)

    yield (item,)
    for i in range(depth):
        for m in it.combinations(l, 1+i):
            yield (item,)+m

# The whole of CSI_Engine should basically move into GPy.  It's going
# to be a bit of a fiddle figuring out how to set everything up, but
# looks like a magic set of invocations of @link_parameter will be
# able to

if __name__ == "__main__":
    import time
    import sys
    import csv

    import shared.filehandling as sfh

    with open("csi/testdata/Demo_DREAM.csv") as fd:
        data = sfh.readCsvNamedMatrix(fd)

    print(data)
