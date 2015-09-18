import sys

import numpy as np
import h5py as h5

import csi.gp as gp

class csi_res(object):
    def __init__(mod, res, cutoff):
        self.res = mod.fd[res]

        self.item   = self.res.attrs['item']
        self.psets  = self.res['parents']
        self.weight = self.res['weight'][:]

        for i in np.nonzero(weight >= cutoff)[0]:
            pi = pars[i]
            wi = weight[i]

            pd,id = getPsetData(item, pi)

            model = gp.rbf(pd,id,hypers)

            model.predict()

class csi_mod(object):
    def __init__(hdf5file):
        self.fd = h5.File("dream-trunc3.h5")

        self.data  = [d for _,d self.fd['data'].items()]
        self.items = self.fd['items']

    def get_pset_data(item, pset):
        pa = []
        da = []
        for d in self.data:
            pa.append(d[pset,:-1])
            da.append(d[[item],1:])
        pa = np.hstack(pa)
        da = np.hstack(da)
        return (da.T,pa.T)

    def get_res(n):
        return csi_res(self, res, cutoff)
