"""
Round-number bunching estimator (Chetty et al. 2011 polynomial counterfactual).

Measures excess mass at a focal value of a running variable (here the takeover
premium) relative to a smooth polynomial counterfactual fitted on the
undistorted part of the distribution. Round numbers act as a two-sided magnet,
so the estimator excludes a wide distorted window from the polynomial fit and
then sums the excess over a narrow spike window around the focal point.

Dependency: numpy only.
"""

import numpy as np


def _binned_counts(z, bin_width, lo, hi):
    edges = np.arange(lo, hi + bin_width, bin_width)
    counts, edges = np.histogram(z, bins=edges)
    mids = edges[:-1] + bin_width / 2.0
    return mids, counts.astype(float)


def estimate_bunching(z, focal, bin_width=0.01, fit_window=0.12,
                      exclude_halfwidth=0.035, spike_halfwidth=0.012,
                      poly_degree=3):
    """
    Estimate normalized excess mass at `focal` in the distribution of `z`.

    Parameters
    ----------
    z                 : array of running-variable values (e.g. premium)
    focal             : focal point to test (e.g. 0.30)
    bin_width         : histogram bin width
    fit_window        : half-width of the local region used to fit the
                        counterfactual polynomial
    exclude_halfwidth : bins within this distance of focal are excluded from
                        the polynomial fit (the distorted region)
    spike_halfwidth   : excess mass is summed over bins within this distance
                        of focal (the spike)
    poly_degree       : degree of the counterfactual polynomial

    Returns
    -------
    dict with excess_mass (count), b_normalized (excess / counterfactual
    height), counterfactual_height, and arrays for plotting.
    """
    lo, hi = focal - fit_window, focal + fit_window
    sub = z[(z >= lo) & (z < hi)]
    mids, counts = _binned_counts(sub, bin_width, lo, hi)

    in_excluded = np.abs(mids - focal) <= exclude_halfwidth
    in_spike = np.abs(mids - focal) <= spike_halfwidth

    x = mids - focal  # center for numerical stability
    fit_mask = ~in_excluded
    X_fit = np.vander(x[fit_mask], poly_degree + 1, increasing=True)
    beta, *_ = np.linalg.lstsq(X_fit, counts[fit_mask], rcond=None)
    cfact = np.vander(x, poly_degree + 1, increasing=True) @ beta

    excess = float(np.sum(counts[in_spike] - cfact[in_spike]))
    cf_height = float(np.mean(cfact[in_spike]))
    b_norm = excess / cf_height if cf_height > 0 else np.nan

    return {
        "focal": focal,
        "excess_mass": excess,
        "b_normalized": b_norm,
        "counterfactual_height": cf_height,
        "mids": mids,
        "counts": counts,
        "counterfactual": cfact,
        "spike_mask": in_spike,
    }


def bootstrap_bunching(z, focal, n_boot=300, seed=0, **kwargs):
    """Bootstrap the normalized excess mass by resampling deals."""
    z = np.asarray(z, float)
    rng = np.random.default_rng(seed)
    n = len(z)
    bs = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        bs[i] = estimate_bunching(z[idx], focal, **kwargs)["b_normalized"]
    point = estimate_bunching(z, focal, **kwargs)["b_normalized"]
    return {
        "focal": focal,
        "b_normalized": point,
        "se": float(np.nanstd(bs, ddof=1)),
        "ci_lo": float(np.nanpercentile(bs, 2.5)),
        "ci_hi": float(np.nanpercentile(bs, 97.5)),
        "boot": bs,
    }


if __name__ == "__main__":
    # quick self-check: inject a spike and confirm b > 0
    rng = np.random.default_rng(0)
    base = rng.gamma(4.0, 0.085, 20000)
    spike = np.full(3000, 0.30) + rng.normal(0, 0.0015, 3000)
    z = np.concatenate([base, spike])
    out = bootstrap_bunching(z, 0.30, n_boot=200)
    print(f"b = {out['b_normalized']:.2f} (se {out['se']:.2f})")
