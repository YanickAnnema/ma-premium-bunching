"""
Sharp regression discontinuity with local linear regression and a triangular
kernel. Estimates the jump in an outcome at a cutoff of the running variable
(here, a focal premium threshold). Standard errors come from a pairs bootstrap.

Dependency: numpy only.
"""

import numpy as np


def _triangular(u):
    return np.maximum(0.0, 1.0 - np.abs(u))


def _wls_intercept(d, y, w):
    """Weighted local linear fit; return the intercept (limit at d = 0)."""
    if len(d) < 5:
        return np.nan
    X = np.column_stack([np.ones_like(d), d])
    XtW = X.T * w               # (2, m), avoids building a dense diag(w)
    beta = np.linalg.solve(XtW @ X, XtW @ y)
    return beta[0]


def _jump(d, y, bandwidth):
    left = d < 0
    right = d >= 0
    wl = _triangular(d[left] / bandwidth)
    wr = _triangular(d[right] / bandwidth)
    kl, kr = wl > 0, wr > 0
    a_right = _wls_intercept(d[right][kr], y[right][kr], wr[kr])
    a_left = _wls_intercept(d[left][kl], y[left][kl], wl[kl])
    return a_right - a_left


def rdd_estimate(x, y, cutoff=0.0, bandwidth=None, n_boot=300, seed=0):
    """
    Parameters
    ----------
    x         : running variable
    y         : outcome
    cutoff    : threshold
    bandwidth : if None, a simple plug-in rule on the running variable is used
    n_boot    : pairs-bootstrap replications for the standard error

    Returns
    -------
    dict with tau (the jump), bandwidth, se, and a 95% percentile CI.
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    d = x - cutoff
    if bandwidth is None:
        bandwidth = 1.06 * np.std(d) * len(d) ** (-1 / 5.0)

    tau = _jump(d, y, bandwidth)

    rng = np.random.default_rng(seed)
    n = len(x)
    boot = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        boot[i] = _jump(d[idx], y[idx], bandwidth)

    return {
        "tau": float(tau),
        "bandwidth": float(bandwidth),
        "se": float(np.nanstd(boot, ddof=1)),
        "ci_lo": float(np.nanpercentile(boot, 2.5)),
        "ci_hi": float(np.nanpercentile(boot, 97.5)),
    }


if __name__ == "__main__":
    # self-check: inject a jump of 0.10 at cutoff 0.5 and recover it
    rng = np.random.default_rng(0)
    x = rng.uniform(0.2, 0.8, 8000)
    y = 0.3 * x + 0.10 * (x >= 0.5) + rng.normal(0, 0.05, 8000)
    r = rdd_estimate(x, y, 0.5)
    print(f"tau = {r['tau']:.3f} (se {r['se']:.3f}), injected 0.10")
