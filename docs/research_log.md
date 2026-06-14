# Research log

A running record of decisions, dead ends, and data-quality findings. Kept so the
final paper can be honest about how the sample was built and what was learned
along the way.

## Question

Do takeover premia bunch at round focal points (20, 25, 30, 50 percent), and does
a premium set at a round threshold change deal outcomes? The premium, not the
offer-price level, is the object: the price level clusters partly for mechanical
reasons, so the premium is the cleaner test. See `docs/methodology.md`.

## Data acquisition

The first plan pulled the deal list from the LSEG Deals screen through the Excel
add-in, then through the LSEG Python library. Both hit the same wall: the deal
screen returns only a few hundred deals (about 663 in one clean run) before a
quota locks all further deal pulls, and the lock did not clear on a Workspace
restart. The cap is at the entitlement level, not per session, so neither the
Excel add-in nor the Python client can extract the full universe. Price, IBES,
fundamentals, and ESG pulls are not affected by this cap.

Decision: keep LSEG for prices, which work, and move the deal list to SEC EDGAR,
which is free and unlimited for US public targets. `src/edgar_deals.py` searches
merger 8-Ks and parses the per-share cash price from the filing text. The LSEG
extraction scripts are retained for reference and for any future run on a higher
entitlement.

## Pilot on the 663 LSEG deals

The 663-deal LSEG pilot (US and UK public targets, 2010 to 2011) validated the
full pipeline end to end and surfaced the data-quality hazards, all of which are
the standard joins of this kind of study:

- A column-mapping bug wrote the offer price under the wrong header. Fixed by
  mapping returned columns positionally rather than by header text.
- PermID identifies the company, not a quote, so it cannot be priced directly.
  Resolve PermID to a primary RIC first.
- The unaffected price taken one day before the announcement produced a large
  spike of near-zero premia (leakage). Moving it to one month before removes the
  artifact.
- UK quotes are in pence while the offer is in pounds, a 100x mismatch that made
  every UK premium negative. Fixed by dividing .L prices by 100.
- Some PermIDs resolved to the wrong listing (foreign or OTC quotes, or the
  acquirer). Filtered to clean US and UK primary listings.

After cleaning, the pilot premia had a sensible median near 0.22 and about 8
percent negative. The round-number signal was weak (roughly 1.16x more mass at
5 percent multiples than between them) with noisy bunching estimates. This is not
a null result, it is an underpowered one: 464 usable deals give only 10 to 16
deals at each focal premium against bootstrap standard errors near 0.3 to 0.8.
The conclusion was that the method and cleaning are sound but the sample must be
much larger, which is the motivation for the EDGAR pivot.

## EDGAR pivot and the identification problem

The EDGAR route delivered the deal list but identification of delisted targets was
hard. Lessons, in order: announcement 8-Ks are filed by both sides, so the filer
is not reliably the target (acquirers were recorded as targets); the target's
completion 8-K (Item 3.01, delisting) is unambiguously the target and carries a
clean merger-consideration price and the announcement date in text; pre-2019
filings carry no ticker, so the historical ticker comes from the announcement
press release; the press release names both companies, so the ticker must be tied
to the target's name, not the first exchange mention (which is usually the
acquirer); a bare delisted ticker does not resolve in LSEG, but ticker plus
exchange suffix over the announcement-date window does; and the resolved RIC must
be confirmed by matching its name back to the target, which drops successor-name
cases (AmeriCredit/GM, PAETEC/Windstream) that are recoverable later by whitelist.
The Python desktop API (UDF) was unreliable for bulk pulls; the Excel add-in was
the dependable channel.

## Result: clean 320-deal sample (US cash takeovers, 2010-2025)

Headline: offer prices cluster at round numbers, premia do not.

- Offer prices: 36.6% sit at a whole dollar. Strong price-level clustering,
  consistent with the prior literature.
- Premia: 21.4% land on a 5% multiple versus 20% expected by chance (z = 0.60,
  p = 0.28). The bunching estimator at every focal premium (10 to 50%) is
  statistically zero (all 95% CIs include zero). The premium histogram is smooth
  and right-skewed, median 30.8%, with no spikes at round numbers.

Interpretation: the round-number focal-point behavior lives in the nominal offer
price the bidder names, not in the percentage premium it implies. A round price
over a noisy unaffected price de-rounds the premium. The documented price
clustering does not propagate to premia.

## First-stage and spine tests (src/clustering_tests.py)

Stage 0, offer-price clustering: the cents distribution is far from uniform
(chi-square p ~ 0). 36.6% of offers end in .00 (z=64 vs a 1% null), 17.8% in .50,
10.3% in .25, 5.0% in .75; 69.7% sit on a quarter-dollar against ~4% under
uniformity. Price-level clustering is overwhelming, as the literature reports.

Spine test, premia at a 5% multiple split by whether the pre-bid price is round:
- all deals: 21.4% (N=309), z=0.6, p=0.28, no bunching;
- pre-bid price round: 45.5% (N=11), z=2.1, p=0.02, premia cluster here;
- pre-bid price not round: 20.5% (N=298), z=0.2, p=0.42, flat.

So the faint premium roundness appears only where the pre-bid price is also round
(round offer over round pre-bid price gives a round premium), and disappears in
the 298 deals with a non-round pre-bid price. Premium roundness is mechanical
inheritance from round prices, not negotiators targeting round premia. The N=11
round-price cell is tiny, so treat the 45.5% as suggestive; the well-powered
non-round cell (N=298) is the clean null. Headline figure:
outputs/clustering_tests.png (offer-price cents spikes next to a smooth premium
distribution).

## Open follow-ups

Recover the ~120 successor-name drops and ~21 mixed-consideration deals to push N
toward ~450 and confirm robustness; the proper market-model CAR; and the
completion-outcome RDD, which needs withdrawn deals (absent from this
completed-only sample).
