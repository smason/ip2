import numpy as np

import scipy.spatial.distance as dist
import scipy.linalg.lapack as lapack

_LOG_2_PI = 1.837877066409345483556

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

def rbf_likelihod_gradient(X, Y, theta):
    """Log-likelihood and gradient of parameters of a GP, optimised for
    our use case.  We use a RBF/squared-exponential kernel for our
    Gaussian Process, and return a structure for easy/quick lookup.

    The parameter definitions and naming conventions (mostly) follow
    the `GPML` library of Rasmussen and Williams, they are the
    variance (`sf2`) and lengthscale (`l2`) of the RBF Kernel, and the
    variance of the additive Gaussian noise (`return`).
    """

    [sf2, l2, sn2] = theta

    # evaluate RBF kernel for our given X
    r = dist.pdist(X) / l2
    K = dist.squareform(sf2 * np.exp(-0.5 * r**2))
    np.fill_diagonal(K, sf2)

    # add in Gaussian noise
    Ky = K.copy()
    np.fill_diagonal(Ky, sf2 + sn2 + 1e-8)

    # compute the Cholesky factorization of our covariance matrix
    LW, info = lapack.dpotrf(Ky, lower=True)
    assert info == 0

    # calculate lower half of inverse of K (assumes real symmetric positive definite)
    Wi, info = lapack.dpotri(LW, lower=True)
    assert info == 0

    # make symmetric by filling in the upper half
    Wi += np.tril(Wi,-1).T

    # and solve
    alpha, info = lapack.dpotrs(LW, Y, lower=True)
    assert info == 0

    # this lets us get at the log-determinant…
    W_logdet = 2.*np.sum(np.log(np.diag(LW)))
    #   and hence to the log of the marginal likelihood
    log_marginal = 0.5 * (-Y.size * _LOG_2_PI - Y.shape[1] * W_logdet - np.sum(alpha * Y))

    dL_dK  = 0.5 * (np.dot(alpha,alpha.T) - Y.shape[1] * Wi)

    gradient = np.zeros(3)
    # fill in gradient of sn2
    gradient[2] = np.diag(dL_dK).sum()

    # multiply to save duplication of work
    dL_dK *= K
    # gradient of sf2
    gradient[0] = np.sum(dL_dK) / sf2
    # gradient of l2
    gradient[1] = np.sum(dist.squareform(r)**2 * dL_dK) / l2

    return RbfLikelihoodGradient(X, Y, theta, log_marginal, gradient)
