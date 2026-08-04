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

# Focal premia reported in docs/paper.md section 4.2. FOCALS is the set the
# synthetic generator injects; this is the set the paper reports on real data,
# and it adds 0.10. Bootstrap draws are seeded, so this table is reproducible.
REPORT_FOCALS = [0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]
N_BOOT = 500


# A pre-bid price counts as round only if it is a whole dollar to within half a
# cent. Must match ROUND_TOL in clustering_tests.py.
ROUND_TOL = 0.005


def load_deals():
    """Use real enriched deals if present, else the synthetic demo set.

    The synthetic set injects bunching on purpose, so on a fresh clone this
    pipeline reports a POSITIVE excess mass. That exercises the estimators; it
    is not the paper's result, which is a null. See docs/paper.md.
    """
    if os.path.exists(REAL):
        df = pd.read_csv(REAL)
        df = df.dropna(subset=["premium", "p0"])
        df = df[(df["premium"] > -0.3) & (df["premium"] < 1.5)]   # drop bad joins
        if "consideration" in df.columns:
            # A mixed-consideration row records only the cash leg, so its
            # premium is understated. Drop rather than trust.
            df = df[df["consideration"] == "cash"]
        df["p0_is_round"] = (df["p0"] - df["p0"].round()).abs() < ROUND_TOL
        print(f"loaded REAL deals: {len(df)} from {os.path.basename(REAL)}")
        return df.reset_index(drop=True)
    print("no real deals found, using the SYNTHETIC demo set.\n"
          "It injects bunching on purpose, so the b values below are positive "
          "by construction.\nThe real-data result is a null: see docs/paper.md.")
    return make_deals()


def main():
    df = load_deals()
    z = df["premium"].values
    print(f"N deals: {len(df)}\n")

    print("Stage 1: premium bunching (normalized excess mass b)")
    for f in REPORT_FOCALS:
        bs = bootstrap_bunching(z, f, n_boot=N_BOOT, **BUNCH_KW)
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
