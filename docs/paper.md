# Round Numbers in Takeover Pricing: Offer Prices Cluster, Premia Do Not

Yanick Annema, 2026

## Abstract

In 320 completed cash acquisitions of US public companies between 2010 and 2025, offer prices cluster heavily at round values: 36.6 percent end in exactly .00 and 69.7 percent fall on a quarter-dollar, far above the roughly 4 percent expected under a uniform distribution. This reproduces the well-documented price-level clustering in mergers. Acquisition premia, by contrast, show no round-number bunching. The share of premia landing on a 5 percent multiple is 21.4 percent against 20 percent expected by chance (p = 0.28), and an excess-mass bunching estimator is statistically indistinguishable from zero at every focal premium from 10 to 50 percent. The faint roundness that does appear in premia is confined to the small subset of deals where the pre-bid price is itself round, and it disappears once the pre-bid price is not round. Premium roundness is therefore mechanical inheritance from round prices rather than evidence that negotiators target round premia. The behavioral focal point in takeover pricing is the nominal price a bidder names, not the percentage premium it implies.

## 1. Question

Round numbers act as focal points in bargaining. They have been documented in online negotiation, in housing, and in the clustering of merger offer prices at round dollar amounts. A natural next question is whether the takeover premium, the percentage paid over the target's unaffected price, also bunches at round numbers such as 20, 25, or 30 percent. The premium is the cleaner behavioral object: an offer price can be round for mechanical reasons (a stock simply trades near a round number), whereas a round premium would reflect a deliberate choice about the size of the markup.

This paper separates the two. It asks whether premia bunch at round numbers, and whether any roundness in premia is genuine premium-targeting or merely a mechanical consequence of round offer prices divided by the pre-bid price. The test that distinguishes these, here called the spine test, is whether premium roundness survives once the pre-bid price is not itself round.

## 2. Data

The deal list comes from SEC EDGAR. For each completed acquisition of a US public company, the target files an 8-K reporting Item 3.01 (delisting). Only the target files a delisting notice, so the filer is unambiguously the target, which avoids the common error of recording the acquirer as the target. That filing states the per-share cash consideration in clean language ("converted into the right to receive $X.XX in cash") and names the original announcement date ("Agreement and Plan of Merger, dated as of ..."). The historical ticker is read from the target's announcement-period press release, taking the exchange symbol that sits next to the target's name rather than the acquirer's.

Unaffected prices come from LSEG. Each target is matched to its delisted RIC and its identity confirmed by matching the RIC's company name back to the target name; matches that fail are dropped rather than guessed. The unaffected price is the close about one month (roughly 22 trading days) before the announcement, which avoids the pre-bid run-up that contaminates a one-day-prior price. The premium is the final cash offer over that unaffected price, minus one.

The sample is restricted to completed cash deals, since the study concerns the premium offered in cash transactions. After identity verification and quality filters (dropping mixed-consideration rows whose recorded price is only the cash leg, implausible parses, and unresolved delisted names), 320 deals remain. The median premium is 30.8 percent, in line with the takeover-premium literature. The LSEG and ORBIS data are licensed and are not redistributed; the repository ships the code and a synthetic demonstration dataset, and the EDGAR-derived deal terms are public.

## 3. Method

Three tests are run. First, offer-price clustering: the distribution of the cents component of the offer price is compared to uniformity. Second, premium bunching: the share of premia falling on a 5 percent multiple is compared to the 20 percent expected by chance, and a polynomial excess-mass estimator (Chetty, Friedman, Olsen and Pistaferri, 2011) is fitted at each focal premium with a bootstrap confidence interval. Third, the spine test: the premium round-number share is computed separately for deals whose pre-bid price is round (a whole dollar) and deals whose pre-bid price is not. If premium roundness is genuine, it should be present among non-round-price deals; if it is mechanical, it should appear only when the pre-bid price is also round.

## 4. Results

![Offer-price cents cluster at 00, 25, 50, 75; premia are smooth](figures/clustering_tests.png)

### 4.1 Offer prices cluster strongly

The cents distribution of offer prices is far from uniform (chi-square p effectively zero). Offers end in .00 in 36.6 percent of deals (a z-statistic of 64 against a 1 percent null), in .50 for 17.8 percent, in .25 for 10.3 percent, and in .75 for 5.0 percent. Taken together, 69.7 percent of offers sit on a quarter-dollar, against roughly 4 percent under uniformity. Price-level clustering is overwhelming, confirming the prior literature and validating that the sample behaves as expected.

### 4.2 Premia do not bunch

Across all 320 deals, 21.4 percent of premia fall on a 5 percent multiple, against 20 percent expected by chance (z = 0.6, p = 0.28). The excess-mass bunching estimator is statistically zero at every focal premium tested (10, 15, 20, 25, 30, 40, 50 percent); each bootstrap confidence interval contains zero. The premium distribution is a smooth, right-skewed curve centered near 30 percent with no spikes at round numbers.

### 4.3 Premium roundness is mechanical

Splitting by whether the pre-bid price is round sharpens the result. Among the 11 deals whose pre-bid price is a whole dollar, 45.5 percent of premia fall on a 5 percent multiple (p = 0.02), the only place round premia concentrate. Among the 298 deals whose pre-bid price is not round, the figure is 20.5 percent, indistinguishable from chance (p = 0.42). A round premium requires a round offer divided by a round pre-bid price; when the pre-bid price is not round, the premium is de-rounded and no clustering remains. The round-price cell is small, so its point estimate is only suggestive, but the well-powered non-round cell is a clean null.

## 5. Discussion

The focal-point behavior in takeover pricing lives in the nominal offer price the bidder names, not in the premium that price implies. Bidders and their advisers anchor on round dollar amounts, consistent with round prices serving as low-search-cost coordination points or signals in negotiation. That behavior does not translate into round premia, because the unaffected price in the denominator is a market price that is almost never round, so it scrambles the percentage. The premium is the wrong place to look for round-number psychology; the offer price is the right one.

This reframes the natural hypothesis. One might expect, given strong price clustering, that premia bunch at salient percentages. They do not, and the spine test explains why: the only premium roundness is the mechanical residue of round prices meeting round pre-bid prices, which is rare and which the data isolate and dismiss.

## 6. Limitations

The sample is completed cash deals only. Withdrawn deals are absent, so the study cannot test whether a round premium affects deal completion, which was part of the original design and is left for a sample that includes withdrawn bids. Mixed cash-and-stock deals are excluded because the recorded per-share figure captures only the cash leg. The sample is US-listed targets and 320 deals, which gives clear power for the offer-price clustering and the main premium null, but the round-pre-bid-price cell (N = 11) is too small to be conclusive on its own. Identification of delisted targets causes attrition: roughly 120 deals were dropped because the matched RIC now resolves to a post-merger successor name (for example AmeriCredit to GM Financial), and these are recoverable later with a manual whitelist. Prices come from a single vendor. None of these threatens the central contrast, which is that strong price clustering coexists with a premium null.

## 7. Conclusion

Offer prices in US cash takeovers cluster sharply at round numbers; acquisition premia do not. Whatever roundness premia exhibit is mechanical inheritance from round prices, not negotiators choosing round percentage markups. The result is a clean separation between where round-number focal points operate (the nominal price) and where they do not (the implied premium).

## References

- Backus, Blake, Larsen, Tadelis (2019). On the empirical content of cheap-talk signaling: an application to bargaining. Journal of Political Economy.
- Chetty, Friedman, Olsen, Pistaferri (2011). Adjustment costs, firm responses, and micro vs macro labor supply elasticities. Quarterly Journal of Economics. (Bunching estimator.)
- Du et al. (2020). Round-number bidding as an M&A strategy.
- Huang et al. (2023). Round offer prices in M&A transactions: costly negotiation and psychological preference. Managerial Finance.
- Pope, Pope, Sydnor (2015). Focal points and bargaining in housing markets. Games and Economic Behavior.

## Reproducibility

Code, the synthetic demonstration dataset, and the analysis (`src/clustering_tests.py`, `src/bunching.py`) are in this repository. The EDGAR deal extractor (`src/edgar_deals.py`, `src/edgar_tickers.py`) is free to run; the LSEG price join (`src/lseg_prices.py`) requires a Workspace entitlement. Underlying LSEG prices are not redistributed under licence; the figure shows aggregate results only. The full data-acquisition history, including the dead ends, is documented in `docs/research_log.md`.
