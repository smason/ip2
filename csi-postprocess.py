import json
import sys

import h5py as h5
import csi.h5reader as pp

import optparse
import logging

def get_dom(mod, min_weight=1e-5, min_predict=1e-2, maxmodels=1000, maxpredict=20):
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

        npredict = 0

        models = []
        for w,ps in zip(res.weights,res.psets):
            mi = dict(weight=w,pset=ps.tolist())
            if w >= min_predict:
                if npredict < maxpredict:
                    pred = pp.Predictor(res, ps)
                    predict = []
                    for r in mod.reps:
                        mu,var = pred.predict_dataset(r.data[:,:-1])
                        predict.append(dict(
                            mu=mu.flatten().tolist(),
                            var=var.flatten().tolist()))
                    mi["predict"] = predict
                npredict += 1
            models.append(mi)
        out = dict(
            target=int(res.target),
            hyperparams=res.hypers.tolist(),
            models=models[:maxmodels])
        results.append(out)

        logging.info("%s: %i models and %i predictions output (weights=%s)",
                     items[res.target], len(models), npredict, str(res.weights[:3]))

    return dict(
        items=items,
        reps=reps,
        results=results)

def merge_dom(mod1, mod2):
    if mod1["items"] != mod2["items"]:
        raise ValueError("Items not the same")
    if mod1["reps"] != mod2["reps"]:
        raise ValueError("Data/replicates not the same")
    return dict(
        items=mod1["items"],
        reps=mod1["reps"],
        results=mod1["results"]+mod2["results"])

def cmdparser(args):
    # create parser objects
    op = optparse.OptionParser()
    out = optparse.OptionGroup(op, "Output Formats")

    op.set_usage("usage: %prog [options] FILE1.hdf5 [FILE2.hdf5]")
    op.set_defaults(
        verbose=False,
        min_weight=1e-5)

    # define general parameters
    op.add_option('-v','--verbose',dest='verbose',action='count',
                  help="Increase verbosity (specify twice for more detail)")

    op.add_option('-w','--weight',dest='min_weight',type=float,
                  help="Only extract parental with at least this weight",
                  metavar="MIN")
    op.add_option('-p','--predict',dest='min_predict',type=float,
                  help="Only calculate model predictions from parental with least this weight",
                  metavar="MIN")

    # parse our command line arguments
    return op.parse_args(args)

def main(args = None):
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

    min_weight = op.min_weight
    if min_weight < 0 or min_weight > 1:
        logging.warn("Minimum parental-set weight should be between 0 and 1")

    if op.min_predict is None:
        min_predict = 1e-2
    else:
        min_predict = op.min_predict
        if min_predict < 0 or min_predict > 1:
            logging.warn("Minimum weight for predictions should be between 0 and 1")

        if min_predict < min_weight:
            logging.warn("Minimum prediction weight should be greater than weight filter")

    if len(fname) < 1:
        logging.error("I need at least one file to process")
        sys.exit(1)

    try:
        with h5.File(fname[0],"r") as fd:
            dom = get_dom(pp.Model(fd), min_weight, min_predict)
    except IOError as err:
        sys.stderr.write("Error opening file {path}: {err}\n".format(path=repr(fname[0]), err=str(err)))
        sys.exit(1)

    for path in fname[1:]:
        with h5.File(path,"r") as fd:
            dom = merge_dom(dom,get_dom(pp.Model(fd), min_weight, min_predict))

    sys.stdout.write("csires = ")
    json.dump(dom,sys.stdout)

if __name__ == '__main__':
    main()
