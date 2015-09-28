import json
import sys

import h5py as h5
import csi.h5reader as pp

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
                pred = pp.Predictor(res, ps)
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
    fd = h5.File("dream-trunc3.h5")
    mod = pp.Model(fd)
    json.dump(get_dom(mod),sys.stdout)

if __name__ == '__main__':
    main()
