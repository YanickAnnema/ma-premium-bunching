# ma-premium-bunching

In takeover pricing the round-number anchor is the price a bidder names, not the premium it implies.

Merger offer prices are known to cluster at round dollar amounts. This repo asks whether that carries over to the premium, the percentage paid over the target's unaffected price. It does not. The interesting part is why: not because a non-round market price makes a round premium unreachable, but because bidders who could have had both took the round price and let the premium fall where it landed.

The method runs end to end on a synthetic dataset that ships with the repo, so it reproduces with no vendor access. On real data the deal list comes from SEC EDGAR (free) and prices come from LSEG (licensed, not redistributed).

## Result

On 316 completed all-cash acquisitions of US public companies (announced 2009 to 2025, completed 2010 to 2025):

- Offer prices cluster hard. 36.4 percent end in .00 and 69.3 percent sit on a quarter-dollar, against 1 and 4 percent under uniformity.
- Premia do not. 21.3 percent fall on a 5 percent multiple against 20 percent by chance (exact p = 0.30), and the excess-mass estimator contains zero at every focal premium from 10 to 50 percent.
- That absence is a choice, not arithmetic. In 85.1 percent of deals some whole-dollar offer would have implied a premium on a 5 percent multiple, and in 50.3 percent one sat within 8 percent of the price actually named. The observed 21.3 percent is exactly the 20.3 percent expected when round prices are picked without regard to the premium.

Full write-up: [docs/paper.md](docs/paper.md).

![Offer-price cents cluster at 00/25/50/75; premia are smooth](docs/figures/clustering_tests.png)

## What the method does

1. Offer-price clustering: the cents distribution against uniformity, with exact binomial tails. The known result, and a data-quality check.
2. Bunching: a Chetty et al. (2011) polynomial excess-mass estimator on the premium distribution, with a bootstrap interval. Reported with its intervals, because at this sample size the null is bounded rather than zero.
3. Menu test: enumerate the whole-dollar offers available in each deal and ask whether one of them implied a round premium, and whether the bidder took it. This is the test that carries the paper.
4. Spine test: the premium round-number share split by whether the pre-bid price is itself a whole dollar. Reported for completeness; its round-price cell holds 7 deals and nothing rests on it.

An outcome design (local-linear RDD at the round-premium threshold) and a market-model event study are implemented and self-checking in `src/rdd.py` and `src/event_study.py`, but they are not run on real data here: they need withdrawn deals, which this completed-only sample does not have.

## Layout

```
ma-premium-bunching/
  src/
    clustering_tests.py  offer-price clustering, spine test, menu test (main result)
    bunching.py          Chetty-polynomial excess-mass estimator + bootstrap
    rdd.py               local-linear sharp RDD with triangular kernel (not run on real data)
    event_study.py       market-model CARs from a returns panel (not run on real data)
    make_synthetic.py    generator with known bunching and a known RDD jump
    run_pipeline.py      end-to-end analysis (real data if present, else synthetic)
    edgar_deals.py       SEC EDGAR deal extractor (target completion 8-Ks)
    edgar_tickers.py     fill historical target tickers from announcement filings
    lseg_extract.py      LSEG Deals-screen extractor (optional, entitlement-capped)
    lseg_prices.py       price join: deal list -> premium, p0 (the contract)
  docs/
    paper.md                   the short paper (result and method)
    figures/                   committed result figures
    methodology.md             the original pre-registration, kept unedited
    data_provenance.md         sources, licensing, how the premium is built
    research_log.md            decisions, dead ends, data-quality findings, corrections
    lseg_excel_extraction.md   LSEG Excel deal-screen notes
  data/                empty in git; deal lists and prices land here (ignored)
  outputs/             generated figures and tables (ignored)
  requirements.txt
  LICENSE
```

## Quick start (synthetic, no vendor access)

```
pip install -r requirements.txt
cd src
python run_pipeline.py
python clustering_tests.py
```

Both fall back to the synthetic demo set when the licensed price join is absent, and say so in their output. Note that the synthetic generator **injects** bunching on purpose, so on a fresh clone these scripts report a positive excess mass and a surviving spine test, which is the opposite of the real-data result above. That is the point: it proves the estimators detect bunching when bunching is there. The real numbers are in [docs/paper.md](docs/paper.md).

Each module also self-checks when run directly (`python bunching.py`, `python rdd.py`, `python event_study.py`), recovering a known injected effect.

## Real data

Three stages, all resumable.

1. Deal list (free): set your contact email in `edgar_deals.py` (`EDGAR_UA`), run `python edgar_deals.py` (target completion 8-Ks), then `python edgar_tickers.py` to fill historical target tickers from the announcement filings.
2. Price join: `python lseg_prices.py` resolves each target to its delisted RIC, confirms identity by matching the name, and computes the premium from the offer over the unaffected close about a month before announcement, writing `data/deals_enriched.csv`. Needs an LSEG entitlement. `docs/lseg_excel_extraction.md` documents the Excel route, which is the dependable channel when the Python desktop API is flaky.
3. Analyse: `python clustering_tests.py` runs the clustering, spine and menu tests (the main result), and `python run_pipeline.py` runs the bunching estimator. Both read `data/deals_enriched.csv`.

The analysis needs `premium`, `p0`, `offer_price`, and `consideration`. The premium is the offer over the unaffected close about one month before announcement. See `docs/data_provenance.md`.

## Honest limitations

The sample is 316 completed all-cash deals, 5 to 35 times smaller than published papers in this literature. Withdrawn deals are absent, so the completion-outcome test is not run, and completion-conditioning is an unsigned threat to the null rather than a neutral filter. The null is bounded, not zero: at this sample size an effect of a few percentage points would go undetected, and the paper states the bound instead of claiming an absence. The premium is measured against one denominator (the close about 22 trading days before announcement); three others were pre-registered and are not reported. Identifying delisted targets causes attrition (about 120 deals dropped for successor-name mismatches, recoverable by whitelist), and prices come from one vendor. Full limitations and the data-acquisition journey, including the LSEG quota wall and the corrections made to an earlier draft, are in [docs/paper.md](docs/paper.md) and [docs/research_log.md](docs/research_log.md).

## References

Chetty, Friedman, Olsen, Pistaferri (2011), bunching estimator. Huang et al. (2023), Du and Lieberman (2023) and Hukkanen and Keloharju (2019), price clustering in M&A. Baker, Pan and Wurgler (2012), reference prices in M&A. Pope et al. (2015), round-number focal points in bargaining. Full list in [docs/paper.md](docs/paper.md).
