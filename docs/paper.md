# Round Numbers in Takeover Pricing: The Anchor Is the Price, Not the Premium

Yanick Annema, 2026

## Abstract

In 316 completed all-cash acquisitions of US public companies (announced 2009 to 2025, completed 2010 to 2025), offer prices cluster heavily at round values: 36.4 percent end in exactly .00 and 69.3 percent fall on a quarter-dollar, against roughly 1 and 4 percent under uniformity. This reproduces the documented price-level clustering in mergers. Acquisition premia show no matching concentration. The share of premia landing on a 5 percent multiple is 21.3 percent against 20 percent expected by chance (exact binomial p = 0.30), and a polynomial excess-mass estimator is indistinguishable from zero at every focal premium from 10 to 50 percent, though with intervals wide enough that only large effects are ruled out. The natural explanation, that a non-round pre-bid price mechanically prevents a round premium, is wrong: in 85.1 percent of deals some whole-dollar offer would have produced a premium on a 5 percent multiple, and in 50.3 percent one sat within 8 percent of the price actually named. Round price and round premium were jointly available and bidders did not take both. The observed 21.3 percent matches the 20.3 percent expected when round prices are chosen without regard to the premium they imply. The focal point in takeover pricing is therefore the nominal price a bidder names, and the premium is a residual of that choice rather than a target in its own right.

## 1. Question

Round numbers act as focal points in bargaining. They have been documented in online negotiation, in housing, and in the clustering of merger offer prices at round dollar amounts. A natural next question is whether the takeover premium, the percentage paid over the target's unaffected price, also bunches at round numbers such as 20, 25, or 30 percent. The premium is the cleaner behavioral object: an offer price can be round for mechanical reasons (a stock simply trades near a round number), whereas a round premium would reflect a deliberate choice about the size of the markup.

This paper asks whether premia bunch, and if they do not, whether that is a choice or an arithmetic inevitability. A bidder naming a whole-dollar price over a non-round pre-bid price will rarely land on a round premium by accident. But it does not follow that the bidder could not have done so deliberately. Whole-dollar offers come in a menu, and different members of that menu imply different premia. If a round premium was reachable without giving up a round price, then declining it is informative about what bidders actually anchor on. Section 4.3 tests exactly that.

## 2. Data

The deal list comes from SEC EDGAR. For each completed acquisition of a US public company, the target files an 8-K reporting Item 3.01 (delisting). Only the target files a delisting notice, so the filer is unambiguously the target, which avoids the common error of recording the acquirer as the target. That filing states the per-share cash consideration in clean language ("converted into the right to receive $X.XX in cash") and names the original announcement date ("Agreement and Plan of Merger, dated as of ..."). The historical ticker is read from the target's announcement-period press release, taking the exchange symbol that sits next to the target's name rather than the acquirer's.

Unaffected prices come from LSEG. Each target is matched to its delisted RIC and its identity confirmed by matching the RIC's company name back to the target name; matches that fail are dropped rather than guessed. The unaffected price is the close about one month (roughly 22 trading days) before the announcement, which avoids the pre-bid run-up that contaminates a one-day-prior price. The premium is the final cash offer over that unaffected price, minus one.

The sample is restricted to all-cash deals, since a mixed-consideration filing records only the cash leg and its premium would be understated. After identity verification and quality filters (dropping mixed consideration, implausible parses, and unresolved delisted names), 316 deals remain, announced between July 2009 and August 2025 and completed between 2010 and 2025. The median premium is 31.0 percent, in line with the takeover-premium literature and with precedent-transaction analyses of US all-cash deals. The LSEG data are licensed and not redistributed; the repository ships the code and a synthetic demonstration dataset, and the EDGAR-derived deal terms are public.

## 3. Method

Four tests are run.

First, offer-price clustering: the distribution of the cents component of the offer price is compared to uniformity.

Second, premium bunching: the share of premia falling on a 5 percent multiple is compared to the 20 percent expected by chance, and a polynomial excess-mass estimator (Chetty, Friedman, Olsen and Pistaferri, 2011) is fitted at each focal premium with a bootstrap confidence interval.

Third, the spine test: the premium round-number share is computed separately for deals whose pre-bid price is a whole dollar and deals whose pre-bid price is not.

Fourth, the menu test. For each deal, enumerate every whole-dollar offer price in the plausible premium range (2 to 120 percent) and ask whether any of them implies a premium on a 5 percent multiple. This measures whether the two forms of roundness were jointly attainable, and it supplies the correct null: the share of the whole-dollar menu that happens to land on a 5 percent multiple is the rate expected if bidders pick round prices without regard to the premium.

All binomial tail probabilities are exact. The spine test's round-price cell holds 7 deals, where a normal approximation is invalid (an earlier draft of this work reported a normal-approximation p-value of 0.02 for that cell; see section 4.3).

## 4. Results

![Offer-price cents cluster at 00, 25, 50, 75; premia are smooth](figures/clustering_tests.png)

### 4.1 Offer prices cluster strongly

The cents distribution of offer prices is far from uniform. Offers end in .00 in 36.4 percent of deals, in .50 for 17.7 percent, in .25 for 10.4 percent, and in .75 for 4.7 percent. Taken together, 69.3 percent of offers sit on a quarter-dollar, against roughly 4 percent under uniformity. Every one of these is exact-binomial significant beyond any conventional threshold. Price-level clustering is overwhelming, confirming the prior literature and validating that the sample behaves as expected.

Two caveats on the comparison to prior work. Published figures are higher: Hukkanen and Keloharju (2019) report roughly 50 percent of US public-target cash offers at one-dollar precision, and Du and Lieberman (2023) report 58.3 percent of public cash offers rounded. Both measure the initial offer, whereas this sample measures the final completed price, and negotiated bumps de-round prices. Roundness here is also strongly increasing in price level (4.2 percent at a whole dollar for offers below $5, 58.6 percent for offers above $80), and this sample contains a larger small-price tail than the published samples. The direction of the effect replicates; the level is not directly comparable.

### 4.2 Premia do not bunch, within the power available

Across the 305 deals with a premium between 2 and 120 percent, 21.3 percent fall on a 5 percent multiple, against 20 percent expected by chance (exact one-sided p = 0.30). A placebo that jitters each premium by up to half a percentage point puts the true chance rate at 20.5 percent, so the observed excess is smaller than the nominal comparison suggests.

The excess-mass estimator contains zero at every focal premium tested. The intervals are wide and should be reported as such:

| focal | b | 95 percent CI |
|---|---|---|
| 0.10 | 0.73 | [-0.79, 2.98] |
| 0.15 | 0.27 | [-0.90, 2.31] |
| 0.20 | -0.45 | [-1.46, 1.03] |
| 0.25 | 0.12 | [-1.14, 2.72] |
| 0.30 | 0.17 | [-0.89, 2.17] |
| 0.40 | -0.28 | [-1.31, 1.78] |
| 0.50 | 0.98 | [-1.08, 7.04] |

At the 30 percent focal the data cannot rule out a density three times the counterfactual. This is a bounded null, not a zero. On the share test the minimum detectable excess at 80 percent power is 5.8 percentage points, so what is ruled out is any effect remotely comparable to the price-level clustering, which runs at 36 times its chance baseline. A small effect of a few percentage points would not be detected here, and an earlier pilot on a different sample suggested roughly that magnitude.

### 4.3 The absence is a choice, not an arithmetic constraint

The obvious explanation for section 4.2 is mechanical. A round offer divided by a non-round market price gives a non-round premium, so premia cannot be round and nothing behavioral is being measured. That explanation does not survive.

The spine test is the weaker half of the evidence and it is reported here for completeness. Among the 7 deals whose pre-bid price is a whole dollar, 3 have premia on a 5 percent multiple (42.9 percent, exact p = 0.148). Among the 298 whose pre-bid price is not, 62 do (20.8 percent, exact p = 0.39). The round-price cell is not statistically significant, it is one of several cells tested without correction, and the mechanism it is supposed to demonstrate does not hold inside it: of its three hits, two came from non-round offer prices, and of the two deals with both a whole-dollar pre-bid price and a whole-dollar offer, one lands on a 5 percent multiple and one does not. Nothing should be built on this cell.

The menu test carries the argument instead. A one-dollar step in the offer moves the premium by 100/P0 percentage points, a median of 7.6, so the whole-dollar menu steps across the premium line in strides only slightly wider than one 5 percent cycle. It does not skip the target values. Enumerating that menu deal by deal:

- In 85.1 percent of deals, at least one whole-dollar offer in the 2 to 120 percent premium range implies a premium on a 5 percent multiple.
- In 50.3 percent, such an offer sits within 8 percent of the price the bidder actually named.
- Averaged over the sample, 20.3 percent of the whole-dollar menu lands on a 5 percent multiple.

The observed rate is 21.3 percent. That is the blind-picking rate. Bidders could have had a round price and a round premium at the same time in most deals, frequently without moving far from the price they chose, and they landed on round premia at exactly the rate expected from indifference. The absence of premium bunching is therefore a revealed preference, not an arithmetic impossibility.

## 5. Discussion

The focal-point behavior in takeover pricing lives in the nominal offer price the bidder names, not in the premium that price implies. Bidders and their advisers anchor on round dollar amounts, consistent with round prices serving as low-search-cost coordination points or signals in negotiation. The premium is then whatever that choice produces.

It is worth being precise about why, because the intuitive explanation is wrong. A non-round pre-bid price does not obstruct a round premium. It only means the bidder has to select the right member of the whole-dollar menu, and in most deals such a member exists. What the data show is that bidders do not perform that selection. Given a choice between naming a round price and implying a round premium, the price wins, and it wins so consistently that the premium distribution is statistically indistinguishable from one generated by ignoring the premium entirely.

This has a direct implication for how the takeover-pricing literature reads round-number effects. Clustering documented in the price level should not be extrapolated to the premium, and a premium is not a good place to look for round-number psychology in any setting where the denominator is a market price. Du and Lieberman's finding that tender offers, which are made at a specified premium over market price, are less likely to be rounded in price is the same trade-off observed from the other side: when the premium is the named object, the price gives way.

## 6. Limitations

The sample is completed all-cash deals only. Withdrawn deals are absent, so the study cannot test whether a round premium affects deal completion, which was part of the original design (`methodology.md`) and is left for a sample that includes withdrawn bids. Completion-conditioning is a genuine threat and its direction is not signed here: if a round premium functions as a take-it-or-leave-it anchor that is more often rejected or bumped, conditioning on completion would strip round-premium mass and could contribute to the observed null.

The null is bounded rather than zero. At this sample size an effect of a few percentage points would go undetected, and section 4.2 states the bound explicitly rather than claiming an absence.

The premium is measured against one denominator, the close about 22 trading days before announcement. The pre-registration also specified a one-day-prior price, a four-week VWAP, and a premium relative to the analyst consensus target, and none of those are reported here. Baker, Pan and Wurgler (2012) show offer prices anchor on the target's 52-week peak, which is a fourth reference point not tested. A negotiator saying "we went 30 over" is not necessarily indexing to a one-month-prior close, so the result should be read as applying to this denominator, and the menu test as applying to the whole-dollar price grid.

The sample is 316 US-listed targets, which is 5 to 35 times smaller than published papers in this literature (Du and Lieberman, 11,328 offers; Hukkanen and Keloharju, roughly 2,000). Identification of delisted targets causes attrition: roughly 120 deals were dropped because the matched RIC resolves to a post-merger successor name (for example AmeriCredit to GM Financial), and these are recoverable with a manual whitelist. Prices come from a single vendor. The pre-bid price itself is not perfectly non-round: it lands on a whole dollar in about 2 percent of deals against 1 percent under uniformity, so the "market prices are never round" simplification is an approximation.

## 7. Conclusion

Offer prices in US cash takeovers cluster sharply at round numbers; acquisition premia do not, to the limits of what this sample can detect. The absence is not forced by arithmetic: in most deals a whole-dollar offer implying a round premium was available, often close to the price actually named, and bidders landed on round premia at exactly the rate expected from ignoring them. The focal point is the price a bidder names. The premium is what falls out.

## References

- Backus, Blake, Larsen, Tadelis (2019). On the empirical content of cheap-talk signaling: an application to bargaining. Journal of Political Economy.
- Baker, Pan, Wurgler (2012). The effect of reference point prices on mergers and acquisitions. Journal of Financial Economics.
- Chetty, Friedman, Olsen, Pistaferri (2011). Adjustment costs, firm responses, and micro vs macro labor supply elasticities. Quarterly Journal of Economics. (Bunching estimator.)
- Du, Lieberman (2023). Round-number bidding as an M&A strategy. UCLA Anderson working paper.
- Hukkanen, Keloharju (2019). Initial offer precision and M&A outcomes. Financial Management.
- Huang et al. (2023). Round offer prices in M&A transactions: costly negotiation and psychological preference. Managerial Finance.
- Kepler, Naiker, Stewart (2023). Stealth acquisitions and product market competition. Journal of Finance. (Bunching applied to M&A deal value.)
- Pope, Pope, Sydnor (2015). Focal points and bargaining in housing markets. Games and Economic Behavior.

## Reproducibility

Code, the synthetic demonstration dataset, and the analysis (`src/clustering_tests.py`, `src/bunching.py`) are in this repository. The EDGAR deal extractor (`src/edgar_deals.py`, `src/edgar_tickers.py`) is free to run; the LSEG price join (`src/lseg_prices.py`) requires a Workspace entitlement. Underlying LSEG prices are not redistributed under licence; the figure shows aggregate results only. `src/clustering_tests.py` falls back to the synthetic set when the licensed price join is unavailable, and labels its output accordingly. The full data-acquisition history, including the dead ends and the corrections made to an earlier draft of this paper, is documented in `docs/research_log.md`.
