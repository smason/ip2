import numpy as np
import scipy as sp
import GPy

import shared.filehandling as sfh

# The whole of CSI_Engine should basically move into GPy.  It's going
# to be a bit of a fiddle figuring out how to set everything up, but
# looks like a magic set of invocations of @link_parameter will be
# able to

if __name__ == "__main__":
    import time
    import sys
    import csv

    with open("csi/testdata/Demo_DREAM.csv") as fd:
        data = sfh.readCsvNamedMatrix(fd)

    print data
