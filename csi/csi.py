import numpy as np
import scipy as sp
import GPy

import itertools as it

class MetaModel(GPy.core.Model):
    def __init__(self, models):
        #models is a  list of GPy models.
        GPy.core.Model.__init__(self, name='metamodel')
        self.models = models
        self.link_parameters(*self.models)

    def log_likelihood(self):
        return sum([m.log_likelihood() for m in self.models])

def parentalSets(items, item, depth):
    """Iterate over all "Parental Sets".

    A parental set is a list of regulators/transcription factors for a
    specific gene.  The parental sets for any given item is every
    subset of items up to a given depth that does not include the
    item.
    """

    # exclude the target, duplicate list to avoid modifying callers
    # state
    l = list(items)
    l.remove(item)

    for i in range(0, depth+1):
        # iterate over every subset of size i
        for subset in it.combinations(l, i):
            yield (item,list(subset))


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
