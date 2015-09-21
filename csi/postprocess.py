import sys

import numpy as np
import h5py as h5

import csi.gp as gp

class csi_res(object):
    def __init__(mod, res, cutoff):
        self.res = res

        self.target = res.attrs['item']
        self.psets  = res['parents'][:]
        self.weight = res['weight'][:]

        self.models = []

        for i in np.nonzero(weight >= cutoff)[0]:
            pi = pars[i]
            wi = weight[i]

            # data for (parent,target)
            dp,dt = getPsetData(self.target, pi)

            self.models.append(gp.rbf(dp,dt,hypers))

    def

class csi_mod(object):
    def __init__(hdf5file):
        self.fd = h5.File("dream-trunc3.h5")

        self.data  = [d for _,d self.fd['data'].items()]
        self.items = self.fd['items']

    def get_pset_data(target, pset):
        pa = [] # parent array
        ta = [] # target array
        for d in self.data:
            pa.append(d[pset,:-1])
            ta.append(d[[target],1:])
        pa = np.hstack(pa)
        ta = np.hstack(da)
        return (pa.T,ta.T)

    def get_res(n):
        return csi_res(self, self.fd[str(res)], cutoff)
