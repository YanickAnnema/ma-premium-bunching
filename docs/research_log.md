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

> **Superseded.** The numbers in this section and the next are the first draft's,
> kept as a record. Several are wrong. See "Corrections to the first draft" below
> for what changed and why; `docs/paper.md` carries the current figures.

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

## Corrections to the first draft

The first published version of this paper had errors. They are listed here in
full rather than quietly overwritten, because the numbers above are what that
draft reported and a reader comparing versions deserves to know what moved.

**1. The spine test's round-price cell was wrong, and it was the only significant
result in the paper.** `p0_is_round` used a one-cent tolerance
(`abs(p0 - round(p0)) < 0.01`), which admits 4.99, 5.99, 7.01 and 63.99 as "whole
dollars". That inflated the cell from 7 deals to 11. The tolerance is now 0.005,
matching what `src/lseg_prices.py` already used.

**2. The p-value for that cell was computed with an invalid approximation.**
`binom_z` used a normal approximation where `n * p0 = 1.4`. The draft reported
p = 0.02 for 5 successes in 11 trials; the exact binomial is 0.050. On the
corrected 7-deal cell it is 3 successes, 42.9 percent, exact p = 0.148. The cell
is not significant under any defensible accounting, and it is one of several
tested without correction. All binomial tails in `clustering_tests.py` are now
exact, computed by a stable pmf recurrence with no scipy dependency.

**3. The mechanism the paper claimed was wrong.** The draft argued that a
non-round pre-bid price "scrambles" the percentage, so a round premium is
effectively unreachable. That is false. A one-dollar step in the offer moves the
premium by a median of 7.6 percentage points, so the whole-dollar menu does not
skip the 5 percent multiples. Enumerating the menu deal by deal: in 85.1 percent
of deals some whole-dollar offer implies a premium on a 5 percent multiple, and
in 50.3 percent one sits within 8 percent of the price actually named. Round
price and round premium were jointly attainable and bidders did not take both.
That is a revealed preference and a better result than the one originally
claimed. It is now the paper's central test (the menu test), and the spine test
is demoted to a completeness check.

Related: the claimed mechanism does not even hold inside its own cell. Two of the
three hits come from non-round offer prices, and of the two deals with both a
whole-dollar pre-bid price and a whole-dollar offer, one lands on a 5 percent
multiple and one does not.

**4. Mixed-consideration deals were not actually dropped.** The paper said they
were. The text-based detector missed four, which survived into the sample of 320.
A mixed filing states only the cash leg, so those premia were understated. The
filter is now applied explicitly on the `consideration` column at analysis time
and N is 316.

**5. The null was overstated as zero.** "The excess-mass estimator is
statistically indistinguishable from zero at every focal premium" is true but
uninformative, because the intervals are wide: at the 30 percent focal the 95
percent interval runs to +2.17, so a density three times the counterfactual is
not excluded. The paper now prints the intervals and states the bound. On the
share test the minimum detectable excess at 80 percent power is 5.8 percentage
points. What is ruled out is an effect comparable to the price-level clustering,
not a small one.

**6. Sample-size and date-range misstatements.** The draft said "across all 320
deals, 21.4 percent", but `pct_at_5mult` silently drops premia outside 2 to 120
percent, so the actual denominator was 309. This log had the right figure and the
paper did not. The draft also said "2010 to 2025"; one deal was announced
2009-07-26 and completed in 2010. Both are corrected, and the analysis N is now
printed alongside every share.

**7. A gitignore pattern silently removed three files from the published repo.**
`.gitignore` carried `LSEG*` and `Lseg*` to block vendor data exports. Git on a
case-insensitive filesystem (`core.ignorecase = true`) matched those patterns
against `src/lseg_prices.py`, `src/lseg_extract.py` and
`docs/lseg_excel_extraction.md`, so none of them were ever committed, while the
README told readers to run `python lseg_prices.py`. The price-join step, which is
the contract the whole analysis depends on, was missing from the public repo. The
patterns are now scoped to data extensions and the three files are committed.

**8. Documentation and reproducibility defects.** `data_provenance.md` described
the extractor as filtering Item 1.01 when the code filters Item 3.01. The README
linked a deleted file. `clustering_tests.py` crashed with a raw traceback on a
fresh clone, because `data/deals_enriched.csv` is correctly gitignored and the
script had no fallback, while `run_pipeline.py` right beside it did. All fixed;
both scripts now fall back to the synthetic set and label the output as
synthetic.

**Not a defect, checked and cleared.** The raw EDGAR extract
(`data/deals_edgar.csv`, 644 rows) contains 15 rows parsed at exactly $1.00
(Warnaco, Jefferies and others) where the regex hit a thousands separator or a
one-decimal price. None of them reach the analysis sample: the price join and the
premium sanity band remove all 15. The three rows above $300 that do survive
(Panera $315, Karuna $330, Atrion $460) are correct prices. The headline numbers
are not contaminated. The parser should still be fixed before `deals_edgar.csv`
is published as a standalone dataset.

## What the corrections did to the headline

The direction of the result did not change; its basis did. Offer prices still
cluster (36.4 percent at a whole dollar, 69.3 percent on a quarter, on N = 316),
premia still do not (21.3 percent on a 5 percent multiple, exact p = 0.30). What
changed is that the paper no longer rests on an 11-deal cell with a wrong
p-value and a wrong mechanism. It rests on the menu test, which uses all 305
deals with a usable premium and asks the question the spine test was trying to
ask.

## Open follow-ups

In rough order of value per hour:

1. Fix the `parse_price` regexes (thousands separators, one-decimal prices), then
   commit `data/deals_edgar.csv` as a standalone public-domain dataset. SEC
   filings are public domain and the file is currently blocked only by the blanket
   `data/*` rule, so the one genuinely shareable artifact in the repo is not
   being shared.
2. Extend the extractor from Item 3.01 completion 8-Ks to DEFM14A and SC 14D9.
   Both are target-filed by the same logic that makes Item 3.01 work, and both are
   far more numerous, which is the route from N = 316 to something in the low
   thousands. A merger proxy also states the unaffected price in text, which
   would remove the LSEG dependency entirely and make the enriched sample
   publishable.
3. Run the who-bunches cross-section with **offer-price** roundness as the
   outcome rather than premium roundness. Premium roundness does not exist in
   the data so it would predict noise, but price roundness is 36.4 percent and
   the covariates (deal size, tender-offer structure, cash versus mixed) come
   free from the filings. This adds a positive result to a paper whose only
   current finding is an absence.
4. Recover the ~120 successor-name drops by whitelist and confirm the null holds.
5. Report the attrition balance test: compare the dropped EDGAR deals to the kept
   ones on offer-price roundness. A first pass gives 39.0 percent versus 36.6
   percent, z = -0.64, p = 0.52, so attrition is not detectably non-random. It is
   cheap and it closes an obvious referee question.
6. The completion-outcome RDD needs withdrawn deals. The flag is obtainable free
   (a target files DEFM14A or SC 14D9 at announcement; no Item 3.01 or Form 25
   within 24 months means the deal failed), but at realistic US public-deal
   failure rates the design stays underpowered even at N in the thousands. Treat
   it as unlikely rather than pending.
7. Retired: the wealth-transfer magnitude calculation. Excess mass is zero, so
   the magnitude is zero. There is no number to compute.
