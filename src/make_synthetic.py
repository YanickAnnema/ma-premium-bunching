"""
Synthetic deal generator for the premium-bunching project.

It injects three things the estimators must recover:
  1. Round-number bunching in the premium at focal points (a two-sided magnet).
  2. Independent price-level rounding on a separate fraction of deals, so the
     "premium bunches even when the pre-bid price is not round" test is
     meaningful (this is the spine of the real paper).
  3. A known discontinuity in deal outcomes (completion and target CAR) at the
     0.50 premium threshold, for the RDD to recover.

No proprietary data is used or shipped. On real data, replace make_deals()
with the loaded LSEG deal table carrying the same columns.

Dependencies: numpy, pandas.
"""

import numpy as np
import pandas as pd

FOCALS = [0.15, 0.20, 0.25, 0.30, 0.40, 0.50]


def make_deals(n=12000, seed=42):
    rng = np.random.default_rng(seed)

    # Unaffected pre-bid price: lognormal, with a fraction snapped to whole units
    p0 = np.round(np.exp(rng.normal(3.2, 0.6, n)), 2)         # median ~ 25
    make_round = rng.random(n) < 0.18
    p0[make_round] = np.round(p0[make_round])
    p0_is_round = np.isclose(p0, np.round(p0))

    # Latent smooth premium centered near 0.34
    latent = np.clip(rng.gamma(4.0, 0.085, n), 0.0, 1.3)

    # Round-number magnet: pull latent within a band of a focal to the focal
    prem = latent.copy()
    band, p_attract = 0.025, 0.45
    for f in FOCALS:
        pull = (np.abs(latent - f) <= band) & (rng.random(n) < p_attract)
        prem[pull] = f + rng.normal(0, 0.0015, int(np.sum(pull)))

    # Offer price, then independent price-level rounding on a separate fraction
    offer_price = p0 * (1 + prem)
    snap = rng.random(n) < 0.25
    offer_price[snap] = np.round(offer_price[snap])
    offer_price = np.round(offer_price, 2)
    prem_realized = offer_price / p0 - 1.0

    at_focal = np.zeros(n, bool)
    for f in FOCALS:
        at_focal |= np.abs(prem_realized - f) <= 0.004

    # Outcomes with a known jump at the 0.50 threshold
    logit = -0.2 + 2.5 * prem_realized + 0.6 * (prem_realized >= 0.50)
    completed = rng.random(n) < 1.0 / (1.0 + np.exp(-logit))
    target_car = (0.40 * prem_realized + 0.05 * (prem_realized >= 0.50)
                  + rng.normal(0, 0.06, n))

    return pd.DataFrame({
        "deal_id": np.arange(n),
        "p0": p0,
        "p0_is_round": p0_is_round,
        "offer_price": offer_price,
        "premium": prem_realized,
        "at_focal": at_focal,
        "completed": completed.astype(int),
        "target_car": target_car,
        "year": rng.integers(2000, 2026, n),
        "currency": rng.choice(["USD", "EUR", "CAD", "GBP"], n,
                               p=[0.50, 0.30, 0.12, 0.08]),
    })


if __name__ == "__main__":
    df = make_deals()
    print(df.head())
    print(f"\nN = {len(df)}, share at a focal premium = {df.at_focal.mean():.3f}, "
          f"share completed = {df.completed.mean():.3f}")
