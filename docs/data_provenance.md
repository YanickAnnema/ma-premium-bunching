# Data provenance

This study joins a deal list to security prices. The deal list can come from
either of two sources; prices come from LSEG. Nothing proprietary is committed
to the repository.

## Deal list

Primary source, SEC EDGAR (free, public, unlimited). `src/edgar_deals.py` queries
EDGAR full-text search for 8-K filings that report Item 1.01 and contain the
phrase "Agreement and Plan of Merger", downloads the main 8-K, and parses the
per-share cash offer price and the target ticker. Output: `data/deals_edgar.csv`.
Coverage is a clean subset of US public-target cash deals; all-stock deals carry
no per-share cash figure and are excluded by design.

Optional source, LSEG Deals screen. `src/lseg_extract.py` pulls the M&A universe
through the LSEG Workspace add-in. This path is entitlement-capped (the deal
screen locks after a few hundred deals and does not reset on restart), which is
why EDGAR is the primary source. See `docs/research_log.md`.

## Prices

`src/lseg_prices.py` resolves each target to a RIC and pulls daily closes from
LSEG. From those it builds the analysis contract:

- `p0`, the unaffected price, is the close about 22 trading days (one month)
  before the announcement. One day before is too close: pre-bid run-up and
  leakage collapse the premium toward zero.
- `premium = offer_price / p0 - 1`. The premium is computed here, never taken
  from a vendor premium field, so its reference date is explicit.
- `target_car` is a simple market-adjusted return over the announcement window,
  the target return minus the regional index return. The full market-model CAR
  is available in `src/event_study.py`.
- UK quotes (.L) are in pence while the offer is in pounds, so .L prices are
  divided by 100 before computing the premium.

## Licensing and what is shared

SEC filings are public domain. The EDGAR-derived deal list is therefore
shareable. LSEG and ORBIS data are licensed and may not be redistributed, so
price series and any LSEG-derived CSV are blocked by `.gitignore` and never
committed. The repository ships code plus a synthetic demo dataset, which is
enough to reproduce the method end to end without any vendor access.
