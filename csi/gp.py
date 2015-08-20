import numpy as np
import scipy as sp
import scipy.linalg as lapack

# my attempt at an optimised version of the RBF kernel and gaussian
# likelihood from the GPy library.  All I care about is getting at the
# log-likelihood and gradient of parameters quickly for a given theta

class RbfLikelihoodGradient(object):
    def __init__(self, X, Y, theta, loglik, gradient):
        self.X   = X
        self.Y   = Y
        self.theta = theta
        self.loglik = loglik
        self.gradient = gradient

def rbf_likelihod_gradient(X, Y, sf2, l2, sn2):
    """Log-likelihood and gradient of parameters of a GP, optimised for
    our use case.  We use a RBF/squared-exponential kernel for our
    Gaussian Process, and return a structure for easy/quick lookup.

    The parameter definitions and naming conventions (mostly) follow
    the `GPML` library of Rasmussen and Williams, they are the
    variance (`sf2`) and lengthscale (`l2`) of the RBF Kernel, and the
    variance of the additive Gaussian noise (`return`).
    """



    return RbfLikelihoodGradient(X, Y, np.array([sf2,ln2,sn2]), loglik, gradient)
