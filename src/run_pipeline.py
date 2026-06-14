"""
End-to-end demo. Run in Spyder (F5) or `python run_pipeline.py`.

Uses real enriched deals (data/deals_enriched.csv) if present, otherwise the
synthetic demo set. It validates the estimators recover injected effects on
synthetic data, and runs the identical analysis on real data once it lands.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")            # headless safe; comment out to view in Spyder
import matplotlib.pyplot as plt

from make_synthetic import make_deals, FOCALS
from bunching import estimate_bunching, bootstrap_bunching
from rdd import rdd_estimate

OUT = os.path.join(os.path.dirname(__file__), "..", "outputs")
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
REAL = os.path.join(DATA, "deals_enriched.csv")
os.makedirs(OUT, exist_ok=True)

# Low polynomial degree on purpose: the fit is local (a +/- fit_window band with
# the focal region excluded), so a high degree Runge-overshoots into the gap.
BUNCH_KW = dict(bin_width=0.01, fit_window=0.12, exclude_halfwidth=0.035,
                spike_halfwidth=0.012, poly_degree=3)


def load_deals():
    """Use real enriched deals if present, else the synthetic demo set."""
    if os.path.exists(REAL):
        df = pd.read_csv(REAL)
        df = df.dropna(subset=["premium", "p0"])
        df = df[(df["premium"] > -0.5) & (df["premium"] < 2.0)]   # drop bad joins
        print(f"loaded REAL deals: {len(df)} from {os.path.basename(REAL)}")
        return df.reset_index(drop=True)
    print("no real deals found, using synthetic demo set")
    return make_deals()


def main():
    df = load_deals()
    z = df["premium"].values
    print(f"N deals: {len(df)}\n")

    print("Stage 1: premium bunching (normalized excess mass b)")
    for f in FOCALS:
        bs = bootstrap_bunching(z, f, n_boot=300, **BUNCH_KW)
        print(f"  focal {f:.2f}: b = {bs['b_normalized']:5.2f}  "
              f"(se {bs['se']:.2f}, 95% CI [{bs['ci_lo']:.2f}, {bs['ci_hi']:.2f}])")

    if "p0_is_round" in df.columns:
        print("\nSpine test: premium bunching conditional on a non-round pre-bid price")
        z_nr = df.loc[~df["p0_is_round"].astype(bool), "premium"].values
        for f in [0.25, 0.30, 0.50]:
            bs = bootstrap_bunching(z_nr, f, n_boot=300, **BUNCH_KW)
            print(f"  focal {f:.2f}: b = {bs['b_normalized']:5.2f}  (se {bs['se']:.2f})")

    if "completed" in df.columns and "target_car" in df.columns:
        print("\nStage 2: RDD at premium = 0.50")
        rc = rdd_estimate(df["premium"].values, df["completed"].values, 0.50)
        rcar = rdd_estimate(df["premium"].values, df["target_car"].values, 0.50)
        print(f"  completion jump  tau = {rc['tau']:.3f} (se {rc['se']:.3f})")
        print(f"  target CAR jump  tau = {rcar['tau']:.3f} (se {rcar['se']:.3f})")

    res = estimate_bunching(z, 0.30, **BUNCH_KW)
    plt.figure(figsize=(7, 4))
    plt.bar(res["mids"], res["counts"], width=0.009, color="#9bbcd6",
            label="observed")
    plt.plot(res["mids"], res["counterfactual"], color="#c0392b", lw=2,
             label="counterfactual")
    plt.axvline(0.30, color="k", ls=":", lw=1)
    plt.xlabel("premium"); plt.ylabel("count")
    plt.title("Premium bunching at 0.30")
    plt.legend(); plt.tight_layout()
    path = os.path.join(OUT, "bunching_premium_0p30.png")
    plt.savefig(path, dpi=130)
    print(f"\nSaved figure: {os.path.normpath(path)}")


if __name__ == "__main__":
    main()
