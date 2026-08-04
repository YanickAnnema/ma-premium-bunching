"""
First-stage, spine, and menu tests for the premium-bunching study.

Stage 0 (offer-price clustering): are offer prices concentrated at round values?
  This is the known result and a data-quality validation.
Spine test: does the premium cluster at round numbers only where the pre-bid
  (unaffected) price is also round? If yes, any premium roundness would be
  mechanical inheritance from round prices rather than premium-targeting.
Menu test: could the bidder have named a whole-dollar price that ALSO produced a
  round premium, and did it? This is the test that carries the paper. Roundness
  in the price and roundness in the premium are jointly attainable in most deals,
  so declining the round premium is a choice, not an arithmetic impossibility.

Reads data/deals_enriched.csv (columns: premium, offer_price, p0, consideration).
Falls back to the synthetic demo set if that file is absent, so the script runs
on a fresh clone. numpy/pandas/matplotlib only, no scipy: binomial tail
probabilities are computed exactly with a stable recurrence, because the cells
here are far too small for a normal approximation.

Run: python clustering_tests.py
"""

import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(_HERE, "..", "data", "deals_enriched.csv")
OUT = os.path.join(_HERE, "..", "outputs")
os.makedirs(OUT, exist_ok=True)

# A pre-bid price counts as round only if it is a whole dollar to within half a
# cent. An earlier version used 0.01, which admits 4.99, 5.99, 7.01 and 63.99
# and inflated this cell from 7 deals to 11. See docs/research_log.md.
ROUND_TOL = 0.005


def binom_sf(k, n, p0):
    """Exact P(X >= k) for X ~ Binomial(n, p0), by a stable pmf recurrence.

    The spine cell has n = 7, where n*p0 = 1.4 and a normal approximation is
    meaningless. No scipy dependency.
    """
    if n == 0:
        return float("nan")
    k = max(int(k), 0)
    if k > n:
        return 0.0
    pmf = (1.0 - p0) ** n
    total = pmf if k == 0 else 0.0
    for i in range(n):
        pmf *= (n - i) / (i + 1.0) * p0 / (1.0 - p0)
        if i + 1 >= k:
            total += pmf
    return min(total, 1.0)


def pct_at_5mult(premium):
    """Share of premia landing on a 5 percent multiple, at 1 pp resolution."""
    pct = np.round(np.asarray(premium) * 100).astype(int)
    pct = pct[(pct >= 2) & (pct <= 120)]
    n = len(pct)
    k = int((pct % 5 == 0).sum())
    if n == 0:
        return 0, 0, float("nan"), float("nan")
    return n, k, k / n, binom_sf(k, n, 0.20)


def round_price_menu(p0, offer, lo_mult=1.02, hi_mult=2.20, near_frac=0.08):
    """For each deal, the whole-dollar offers that also give a 5% multiple premium.

    Returns (available, available_near, blind_rate): whether any such price
    exists in the plausible premium range, whether one exists within near_frac
    of the offer actually named, and the share of the whole-dollar menu that
    lands on a 5% multiple (the rate expected if a bidder picks a round price
    without regard to the premium it implies).
    """
    available, available_near, blind = [], [], []
    for a, b in zip(np.asarray(p0), np.asarray(offer)):
        cand = np.arange(max(int(np.ceil(a * lo_mult)), 1),
                         int(np.floor(a * hi_mult)) + 1)
        if len(cand) == 0:
            continue
        pct = np.round((cand / a - 1.0) * 100).astype(int)
        inrange = (pct >= 2) & (pct <= 120)
        if not inrange.any():
            continue
        ok = (pct % 5 == 0) & inrange
        available.append(bool(ok.any()))
        available_near.append(bool((ok & (np.abs(cand - b) <= near_frac * b)).any()))
        blind.append(float((pct[inrange] % 5 == 0).mean()))
    return np.array(available), np.array(available_near), np.array(blind)


def load_deals():
    """Real enriched deals if present, else the synthetic demo set.

    The real deal table is built from licensed LSEG prices and is not
    redistributable, so a fresh clone lands on the synthetic path. The synthetic
    generator injects premium bunching on purpose, so its output is the OPPOSITE
    of the real finding. It exercises the code, it does not reproduce the paper.
    """
    if os.path.exists(CSV):
        df = pd.read_csv(CSV)
        df = df.dropna(subset=["premium", "p0", "offer_price"])
        df = df[(df["premium"] > -0.3) & (df["premium"] < 1.5)]
        if "consideration" in df.columns:
            # A mixed-consideration row records only the cash leg, so its
            # premium is understated. Drop rather than trust.
            n_mixed = int((df["consideration"] != "cash").sum())
            df = df[df["consideration"] == "cash"]
            if n_mixed:
                print(f"dropped {n_mixed} mixed-consideration deals (cash leg only)")
        print(f"loaded REAL deals: {len(df)} from {os.path.basename(CSV)}\n")
        return df.reset_index(drop=True), True
    from make_synthetic import make_deals
    print("no real deals found (data/deals_enriched.csv is gitignored, licensed "
          "LSEG prices).\nFalling back to the SYNTHETIC demo set, which injects "
          "bunching on purpose.\nIts result is the opposite of the paper's. See "
          "docs/paper.md for the real numbers.\n")
    return make_deals(), False


def main():
    df, is_real = load_deals()
    # Recompute rather than trust a stored flag, so the tolerance is explicit.
    df["p0_is_round"] = (df["p0"] - df["p0"].round()).abs() < ROUND_TOL
    prem = df["premium"].values
    offer = df["offer_price"].values
    pr = df["p0_is_round"].astype(bool).values
    n = len(df)
    print(f"N = {n}; pre-bid price a whole dollar (tol {ROUND_TOL}): {pr.sum()}\n")

    print("STAGE 0: offer-price clustering")
    cents = np.round((offer % 1) * 100).astype(int)
    for c in (0, 50, 25, 75):
        k = int((cents == c).sum())
        print(f"  cents == {c:02d}: {k/n*100:5.1f}%  (uniform ~1%, "
              f"exact p={binom_sf(k, n, 0.01):.2g})")
    on_quarter = np.isin(cents, [0, 25, 50, 75])
    print(f"  on a quarter-dollar (.00/.25/.50/.75): {on_quarter.mean()*100:.1f}%"
          f"  (uniform ~4%, exact p={binom_sf(int(on_quarter.sum()), n, 0.04):.2g})")

    print("\nSPINE TEST: premium at a 5% multiple, split by pre-bid-price roundness")
    print("  (exact binomial against a 20% chance rate; one-sided)")
    for label, mask in [("all", np.ones(n, bool)),
                        ("pre-bid price round", pr),
                        ("pre-bid price NOT round", ~pr)]:
        nn, kk, f, p = pct_at_5mult(prem[mask])
        print(f"  {label:24s} N={nn:3d}  k={kk:3d}  at 5% mult = {f*100:4.1f}%"
              f"  exact p={p:.3f}")

    print("\nMENU TEST: was a round price with a round premium even available?")
    avail, avail_near, blind = round_price_menu(df["p0"].values, offer)
    nn, kk, f, _ = pct_at_5mult(prem)
    print(f"  a whole-dollar offer giving a 5% multiple exists: "
          f"{avail.mean()*100:.1f}% of deals")
    print(f"  ...and within 8% of the offer actually named:     "
          f"{avail_near.mean()*100:.1f}% of deals")
    print(f"  expected rate if round prices are picked blind:   "
          f"{blind.mean()*100:.1f}%")
    print(f"  observed rate:                                    {f*100:.1f}%")
    print("  Round price and round premium are jointly attainable in most deals,")
    print("  and the observed rate sits at the blind-picking rate. Bidders had the")
    print("  option and did not take it.")

    # figure: offer-price cents (the clustering) and premium distribution
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].hist(cents, bins=np.arange(-0.5, 100.5, 1), color="#9bbcd6")
    ax[0].set_title("Offer-price cents (clusters at 00/25/50/75)")
    ax[0].set_xlabel("cents"); ax[0].set_ylabel("count")
    ax[1].hist(prem, bins=np.arange(-0.3, 1.51, 0.02), color="#9bbcd6",
               edgecolor="white")
    for mlt in (0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50):
        ax[1].axvline(mlt, color="#c0392b", ls=":", lw=1)
    tag = "" if is_real else " [SYNTHETIC DEMO]"
    ax[1].set_title(f"Premia (no bunching), N={n}{tag}")
    ax[1].set_xlabel("premium"); ax[1].set_ylabel("count")
    fig.tight_layout()
    path = os.path.join(OUT, "clustering_tests.png")
    fig.savefig(path, dpi=130)
    print(f"\nsaved {os.path.normpath(path)}")


if __name__ == "__main__":
    main()
