import numpy as np
import h5py as h5

import csi.gp as gp

class csi_rep(object):
    def __init__(self, h5data):
        self.name = h5data.attrs["replicate"]
        self.time = h5data.attrs["time"]
        self.data = h5data[:]

class csi_mod(object):
    def __init__(self, fd):
        self.fd = fd

        self.items = [s.decode('utf-8') for s in fd['items']]
        self.reps  = [csi_rep(d) for d in fd['data'].values()]

    def get_res(self, res):
        return csi_res(self, self.fd["result/{0}".format(res+1)])

    def iter_res(self):
        for res in self.fd["result"].values():
            yield csi_res(self, res)

class csi_res(object):
    def __init__(self, mod, res):
        self.mod = mod
        self.res = res

        self.hypers = self.res.attrs['hyperparams']
        self.target = self.res.attrs['item'][0]

        self.ll      = self.res["loglik"][:]
        self.psets   = self.res['parents'][:]
        self.weights = self.res['weight'][:]

    def filter_by_weight(self, min_weight):
        keep = np.nonzero(self.weights >= min_weight)
        self.ll      = self.ll[keep]
        self.psets   = self.psets[keep]
        self.weights = self.weights[keep]

    def sort_psets(self):
        ii = np.argsort(-self.ll)

        self.ll      = self.ll[ii]
        self.psets   = self.psets[ii]
        self.weights = self.weights[ii]

class csi_pred(object):
    def __init__(self, res, pset, datasets=None):
        self.target = res.target
        self.hypers = res.hypers
        self.pset   = list(pset)
        self.ix     = [self.target]+self.pset
        self.iy     = [self.target]

        if datasets is None:
            datasets = (r.data for r in res.mod.reps)

        X = [] # parent array
        Y = [] # target array
        for d in datasets:
            X.append(d[self.ix,:-1])
            Y.append(d[self.iy,1:])
        X = np.hstack(X).T
        Y = np.hstack(Y).T
        self.gp = gp.rbf(X,Y,self.hypers)

    def predict_dataset(self, data):
        return self.gp.predict(data[self.ix,:].T)

    def predict1(self, expr):
        return self.gp.predict(expr[None,self.ix])

def get_dom(mod, min_weight=1e-5, min_predict=1e-2):
    items = mod.items

    reps = []
    for r in mod.reps:
        reps.append(dict(
            name=r.name,
            time=r.time.tolist(),
            data=r.data.tolist()))

    results = []
    for res in mod.iter_res():
        res.filter_by_weight(min_weight)
        res.sort_psets()

        models = []
        for w,ps in zip(res.weights,res.psets):
            mi = dict(weight=w,pset=ps.tolist())
            if w >= min_predict:
                pred = csi_pred(res, ps)
                predict = []
                for r in mod.reps:
                    mu,var = pred.predict_dataset(r.data[:,:-1])
                    predict.append(dict(
                        mu=mu.flatten().tolist(),
                        var=var.flatten().tolist()))
                mi["predict"] = predict
            models.append(mi)

        out = dict(
            target=int(res.target),
            hyperparams=res.hypers.tolist(),
            models=models)
        results.append(out)

    return dict(
        items=items,
        reps=reps,
        results=results)

def main():
    import json
    import sys

    fd = h5.File("dream-trunc3.h5")
    mod = csi_mod(fd)
    json.dump(get_dom(mod),sys.stdout)

if __name__ == '__main__':
    main()
