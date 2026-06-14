"""
First-stage and spine tests for the premium-bunching study.

Stage 0 (offer-price clustering): are offer prices concentrated at round values?
  This is the known result and a data-quality validation.
Spine test: does the premium cluster at round numbers only where the pre-bid
  (unaffected) price is also round? If yes, any premium roundness is mechanical
  inheritance from round prices, not genuine premium-targeting.

Reads data/deals_enriched.csv (columns: premium, offer_price, p0; p0_is_round is
computed if absent). numpy/pandas/matplotlib only, no scipy: tail probabilities
use a normal approximation, which is fine at these effect sizes.

Run: python clustering_tests.py
"""

import os
import math

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(_HERE, "..", "data", "deals_enriched.csv")
OUT = os.path.join(_HERE, "..", "outputs")
os.makedirs(OUT, exist_ok=True)


def binom_z(k, n, p0):
    """One-sided upper-tail z and p for k successes in n vs rate p0 (normal approx)."""
    if n == 0:
        return float("nan"), float("nan")
    z = (k - n * p0) / math.sqrt(n * p0 * (1 - p0))
    p = 0.5 * math.erfc(z / math.sqrt(2))
    return z, p


def pct_at_5mult(premium):
    pct = np.round(premium * 100).astype(int)
    pct = pct[(pct >= 2) & (pct <= 120)]
    k = int((pct % 5 == 0).sum())
    n = len(pct)
    z, p = binom_z(k, n, 0.20)
    return n, k / n if n else float("nan"), z, p


def main():
    df = pd.read_csv(CSV)
    df = df[(df["premium"] > -0.3) & (df["premium"] < 1.5)].copy()
    if "p0_is_round" not in df.columns:
        df["p0_is_round"] = (df["p0"] - df["p0"].round()).abs() < 0.01
    prem = df["premium"].values
    offer = df["offer_price"].values
    pr = df["p0_is_round"].astype(bool).values
    n = len(df)
    print(f"N = {n}; pre-bid price round (whole dollar): {pr.sum()}\n")

    print("STAGE 0: offer-price clustering")
    cents = np.round((offer % 1) * 100).astype(int)
    for c in (0, 50, 25, 75):
        frac = (cents == c).mean()
        z, p = binom_z(int((cents == c).sum()), n, 0.01)
        print(f"  cents == {c:02d}: {frac*100:5.1f}%  (uniform ~1%, z={z:.0f})")
    on_quarter = np.isin(cents, [0, 25, 50, 75]).mean()
    print(f"  on a quarter-dollar (.00/.25/.50/.75): {on_quarter*100:.1f}%  (uniform ~4%)")

    print("\nSPINE TEST: premium at a 5% multiple, split by pre-bid-price roundness")
    for label, mask in [("all", np.ones(n, bool)),
                        ("pre-bid price round", pr),
                        ("pre-bid price NOT round", ~pr)]:
        nn, f, z, p = pct_at_5mult(prem[mask])
        print(f"  {label:24s} N={nn:3d}  at 5% mult = {f*100:4.1f}% (chance 20%)  z={z:4.1f}  p={p:.2f}")

    # figure: offer-price cents (the clustering) and premium distribution (no bunching)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].hist(cents, bins=np.arange(-0.5, 100.5, 1), color="#9bbcd6")
    ax[0].set_title("Offer-price cents (clusters at 00/25/50/75)")
    ax[0].set_xlabel("cents"); ax[0].set_ylabel("count")
    ax[1].hist(prem, bins=np.arange(-0.3, 1.51, 0.02), color="#9bbcd6", edgecolor="white")
    for mlt in (0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50):
        ax[1].axvline(mlt, color="#c0392b", ls=":", lw=1)
    ax[1].set_title(f"Premia (no bunching), N={n}")
    ax[1].set_xlabel("premium"); ax[1].set_ylabel("count")
    fig.tight_layout()
    path = os.path.join(OUT, "clustering_tests.png")
    fig.savefig(path, dpi=130)
    print(f"\nsaved {os.path.normpath(path)}")


if __name__ == "__main__":
    main()
