import sys

import numpy as np
import h5py as h5

import csi.gp as gp

class csi_mod(object):
    def __init__(self, hdf5path):
        self.fd = h5.File(hdf5path)

        self.data  = [d[:] for _,d in self.fd['data'].items()]
        self.items = [s.decode('utf8') for s in self.fd['items']]
        self.time  = [d.attrs["time"] for _,d in self.fd['data'].items()]

class csi_res(object):
    def __init__(self, mod, res):
        self.mod = mod
        self.res = mod.fd["{0}".format(res+1)]

        self.hypers = self.res.attrs['hyperparams']
        self.target = self.res.attrs['item'][0]

        self.ll      = self.res["loglik"][:]
        self.psets   = self.res['parents'][:]
        self.weights = self.res['weight'][:]

    def sort_psets(self):
        ii = np.argsort(-self.ll)

        self.ll      = self.ll[ii]
        self.psets   = self.psets[ii]
        self.weights = self.weights[ii]

class csi_pred(object):
    def __init__(self, res, pset, datasets=None):
        self.target = res.target
        self.hypers = res.hypers
        self.pset   = pset
        self.ix     = [self.target]+self.pset
        self.iy     = [self.target]

        if datasets is None:
            datasets = res.mod.data

        X = [] # parent array
        Y = [] # target array
        for d in datasets:
            X.append(d[self.ix,:-1])
            Y.append(d[self.iy,1:])
        X = np.hstack(X).T
        Y = np.hstack(Y).T
        self.gp = gp.rbf(X,Y,self.hypers)

    def predict1(self, expr):
        return self.gp.predict(expr[None,self.ix])


def __main__():
    pass
