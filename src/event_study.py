"""
Market-model event study. Estimate alpha and beta over an estimation window,
then cumulate abnormal returns over an event window to get a CAR per deal.

On real data, build the input panel from LSEG total return indices (target and
region market index) over [-300, +60] trading days around the announcement.

Dependencies: numpy, pandas.
"""

import numpy as np
import pandas as pd


def market_model_car(panel, est_window=(-250, -50), event_window=(-1, 1),
                     min_obs=60):
    """
    Parameters
    ----------
    panel : long DataFrame with columns
            deal_id, rel_day (int, trading days from announcement),
            ret (target return), mkt_ret (region market return)
    est_window, event_window : (lo, hi) inclusive in trading days
    min_obs : minimum estimation-window observations to keep a deal

    Returns
    -------
    DataFrame with deal_id, car, alpha, beta, n_est.
    """
    out = []
    for did, g in panel.groupby("deal_id"):
        est = g[(g.rel_day >= est_window[0]) & (g.rel_day <= est_window[1])]
        ev = g[(g.rel_day >= event_window[0]) & (g.rel_day <= event_window[1])]
        if len(est) < min_obs or ev.empty:
            continue
        X = np.column_stack([np.ones(len(est)), est.mkt_ret.values])
        beta, *_ = np.linalg.lstsq(X, est.ret.values, rcond=None)
        ar = ev.ret.values - (beta[0] + beta[1] * ev.mkt_ret.values)
        out.append({"deal_id": did, "car": float(ar.sum()),
                    "alpha": float(beta[0]), "beta": float(beta[1]),
                    "n_est": int(len(est))})
    return pd.DataFrame(out)


if __name__ == "__main__":
    # self-check on a tiny synthetic panel
    rng = np.random.default_rng(0)
    rows = []
    for did in range(50):
        days = np.arange(-260, 6)
        mkt = rng.normal(0, 0.01, len(days))
        true_beta = rng.uniform(0.8, 1.3)
        ret = 0.0002 + true_beta * mkt + rng.normal(0, 0.012, len(days))
        ret[days == 0] += 0.15          # announcement bump on day 0
        for d, m, r in zip(days, mkt, ret):
            rows.append((did, d, r, m))
    panel = pd.DataFrame(rows, columns=["deal_id", "rel_day", "ret", "mkt_ret"])
    res = market_model_car(panel)
    print(f"mean CAR = {res.car.mean():.3f} across {len(res)} deals "
          f"(injected ~0.15)")
