# Pre-registration: Round-number bunching in takeover premia

> **This is the original research plan, written before any data was collected, and
> kept here unedited as a pre-registration. It is not a description of what was
> delivered.** The study that was actually run is smaller than this plan in every
> dimension, and the deviations are listed immediately below. Read `docs/paper.md`
> for the delivered work and `docs/research_log.md` for how it got there.
>
> **Deviations from this plan, in full:**
>
> | Planned | Delivered | Why |
> |---|---|---|
> | 8,000 to 15,000 deals | 316 | The LSEG deal screen quota-locked at a few hundred deals, forcing a pivot to a hand-built SEC EDGAR sample |
> | US, Canada, Europe | US only | EDGAR covers US filers only |
> | Completed and withdrawn | Completed only | The Item 3.01 delisting 8-K, which is what makes the target identifiable, only exists for deals that closed |
> | `P0` = close 1 day before announcement (primary) | Close about 22 trading days before | A one-day price is contaminated by pre-bid run-up and leakage; changed after inspecting the pilot, so this is a post-hoc choice and is flagged as such in the paper |
> | 4-week VWAP, premium-to-consensus-target as robustness | Not run | Requires vendor pulls that were not completed |
> | Stage 2, outcome RDD at the focal threshold | Not run | Needs withdrawn deals |
> | Stage 3, who-bunches probit | Not run | Premium roundness does not exist in the data, so the outcome would be noise. The version worth running uses offer-price roundness as the outcome instead |
> | Stage 4, wealth-transfer magnitude | Not run | Excess mass is zero, so the magnitude is zero. Retired |
>
> The plan also names its own kill condition in section 6: if premium roundness
> is only mechanical inheritance from round prices, "the headline is a null and
> the paper becomes a measurement note." The delivered paper reports a null. It
> also shows the mechanical explanation itself is wrong, which is the part the
> plan did not anticipate.

Working title: "Focal Points in Takeover Pricing: Bunching in Acquisition Premia and What It Costs Targets"
Candidate repo name: `ma-premium-bunching`

## 1. The question and the gap

Do takeover **premia** (the percent paid over the target's unaffected price) bunch at round focal points (20, 25, 30, 50 percent), and does a premium struck just below a round threshold change deal outcomes and the split of gains between target and acquirer?

The open gap, confirmed by the literature pass:

1. Existing M&A clustering work (Huang et al. 2023; Du et al. 2020) bunches the **price level**, which is partly mechanical because the target stock already trades near round numbers. The **premium** is the clean behavioral object and has not been formally bunched.
2. That work stops at deal duration and competition using regressions and logits. Nobody has run the housing-style threshold design (Pope et al. 2015; Li 2023) on the round-premium boundary to ask, causally, whether a deal just below a focal premium completes more often, gets revised less, draws fewer rival bids, and leaves the target with worse announcement returns.

Contribution: a formal excess-mass bunching estimate on the premium distribution, plus a regression-discontinuity outcome design that quantifies the wealth transfer ("money left on the table") at focal premia.

## 2. Sample

- Targets: public companies in North America (US, Canada) and Europe.
- Announcement dates: 2000-01-01 to 2025-12-31.
- Deal types: control transactions (acquirer ends with majority or 100 percent). Keep both **completed and withdrawn** deals. Completion is an outcome, so conditioning on it would bias the RDD.
- Exclude: minority-stake creep, buybacks, recaps, deals with no per-share offer price, and deals where the target lacks a usable pre-announcement price history.
- Expected N: order of 8,000 to 15,000 deals with a usable premium after filters, smaller for the outcome RDD where clean public-target prices are needed.

## 3. Data pull

### 3a. LSEG M&A deals (Workspace / Eikon Excel add-in, Deals / M&A screener)

Pull one row per deal with:

- Identifiers: Deal ID, target name, target PermID and RIC, acquirer name and PermID.
- Dates and status: announcement date, effective/withdrawn date, status (completed, withdrawn, pending).
- Geography and listing: target nation, acquirer nation, target public status, acquirer public status, cross-border flag.
- Pricing: initial offer price per share, final offer price per share, deal value, equity value, enterprise value, target currency.
- LSEG premium fields (validation against own calc): premium to 1-day, 1-week, and 4-weeks prior price.
- Consideration: payment method (cash, stock, mixed), percent cash, percent stock.
- Process: attitude (friendly, hostile, neutral), tender offer flag, challenged-deal flag, number of bidders / competing-bid flag, toehold percent, termination fee, percent sought, percent acquired.
- Advisory (for the cross-section of who bunches): target financial advisor(s), acquirer financial advisor(s).
- Industry: target TRBC sector, target SIC.

### 3b. Prices and returns (Datastream / `datastream_data` / `historical_pricing_summaries`)

For each target (and each public acquirer):

- Daily total return index (RI) and unadjusted price (P) over [-300, +60] trading days around announcement. Used for the unaffected price, runup window, and CARs.
- Region market index returns for the market model: S&P 500 (US), S&P/TSX (Canada), STOXX Europe 600 (Europe).

### 3c. Fundamentals and controls (`qa_company_fundamentals`, ORBIS)

Target, most recent pre-announcement fiscal period: market cap, total assets, book-to-market, leverage, EBITDA margin or ROA, cash/assets, EV/EBITDA.

### 3d. Analyst fair-value benchmark (`qa_ibes_consensus`)

Target consensus price target and mean recommendation in the month before announcement. Lets you scale the premium against analyst fair value and test whether bunching is in the raw premium or the premium-to-target-price.

### 3e. Public files (free)

- Fama-French factors: US (3/5-factor plus momentum) and Developed-ex-US / European regional factors, Ken French data library. For abnormal returns.
- SEC EDGAR: on a US subsample, pull DEFM14A / SC 14D9 / 8-K to cross-check final offer price and premium. Data-quality validation only.
- FX (ECB or LSEG) to keep round-number tests within currency.

## 4. Constructed variables

- Unaffected price P0: target close 1 trading day before announcement (primary); 4-week pre-announcement VWAP (robustness). Runup diagnostic over [-42, -1].
- Premium: final offer / P0 - 1. Also initial-offer premium and premium-to-consensus-target.
- Focal indicators: premium within a narrow band of {10, 15, 20, 25, 30, 33.3, 40, 50, ...}; price-level focal points (whole currency unit, multiples of 5 and 10).
- Currency bucket: USD, CAD, EUR, GBP, etc. Round-number tests run within bucket, never pooled across currencies.

## 5. Analysis

### Stage 0, first-stage validation (price-level clustering)
Replicate and extend Huang/Du: test uniformity of the final digit of the offer price (chi-square, Kuiper). Establishes data quality and links to prior work. Expected: strong clustering, as documented.

### Stage 1, main result (premium bunching)
Excess-mass estimator on the premium histogram (1 pp bins). Counterfactual density from a flexible polynomial fitted outside the bunching window (Chetty et al. 2011), with the data-driven window of Bosch et al. (2020) and the Bertanha et al. (2021) estimator as robustness. Bootstrap standard errors. Report excess mass b at each focal premium and the implied count of deals "pulled in" from neighboring premia.

Key robustness that separates this from price-level work: show the premium bunches **conditional on P0 not being a round number** (decompose premium roundness from price roundness). If premium roundness is only mechanical inheritance from round prices, the result collapses, so this test is the spine of the paper.

### Stage 2, causal outcome design (RDD at the round-premium threshold)
Local-linear / local-randomization RDD around each focal premium. Compare deals with premia just below vs just above the focal point. Outcomes:

- Deal completion probability.
- Number and size of bid revisions (bid jumps).
- Probability of a competing bid.
- Target announcement CAR; acquirer announcement CAR.
- Time to completion.

Covariate balance tests (size, book-to-market, industry, runup, payment method) across the threshold. A McCrary density test is descriptive here, since manipulation at the focal point is the phenomenon, not a violation.

### Stage 3, who bunches (cross-section)
Probit of round-premium on: advisor tier (bulge-bracket vs boutique vs none), serial vs one-time acquirer, public vs private acquirer, cross-border, hostile, competitive, deal size, cash vs stock. Huang found serial acquirers still bunch, so the test is whether sophistication removes it.

### Stage 4, wealth-transfer magnitude
Combine excess mass with the average premium gap between focal points to estimate aggregate target value foregone or captured at focal premia. This is the "so what" number.

## 6. Honest null risks and threats

- Unaffected-price noise from leakage and runup makes the premium noisy. Mitigation: 4-week pre-price and explicit runup controls; report both.
- Mechanical inheritance: premium roundness could just track price roundness. The conditional-on-non-round-price test (Stage 1) is the decisive check. If it fails, the headline is a null and the paper becomes a measurement note.
- RDD power: outcome effects may be small. The bunching existence result is robust; the causal outcome link is the higher-variance part. Be prepared to report a precise null on outcomes, which is still publishable in the house style.
- Cross-currency contamination: never pool USD and EUR focal points.
- Selection: include withdrawn deals; do not condition on completion.

## 7. Repo and reproducibility

- Python, minimal deps: numpy, pandas, scipy, statsmodels. Bunching estimator implemented from scratch (Chetty polynomial), local-linear RDD, market-model CARs.
- Synthetic demo dataset shipped so the code runs without LSEG. `.gitignore` blocks `*.xlsx`, `LSEG*`, and derived CSVs, since LSEG and ORBIS forbid redistribution.
- Writing: no em-dashes or en-dashes, humanizer conventions, honest-result framing.

## 8. Key references

- Huang, Y. et al. (2023). Round offer prices in M&A transactions. Managerial Finance. https://consensus.app/papers/details/41ed8ab9333c59828e963dcbcd6668e8/
- Du, T. et al. (2020). Round-Number Bidding as an M&A Strategy. https://consensus.app/papers/details/98b244b4036757418e1f48aeaa3386fe/
- Backus, M. et al. (2019). On the Empirical Content of Cheap-Talk Signaling. JPE. https://consensus.app/papers/details/8a91f75d139056ebaed6609a99ceba68/
- Pope, D. et al. (2015). Focal points and bargaining in housing markets. GEB. https://consensus.app/papers/details/4e101f80b11d5d259578a382835bb451/
- Li, H. (2023). Anchoring on listing round-number focal points (RDD, China housing). Applied Economics Letters. https://consensus.app/papers/details/1ee3667cba785ad69f30de134b4b4403/
- Chetty, R. et al. (2011), via Song (2024), General Bunching Designs. https://consensus.app/papers/details/9823034a1b6051c19d81487b1a090652/
- Bosch, N. et al. (2020). Data-driven bunching window. ITAX. https://consensus.app/papers/details/c5caaa550fc25d5e9e890084603bdb41/
- Bertanha, M. et al. (2021). Bunching estimation of elasticities (Stata). https://consensus.app/papers/details/c98dfcc7d6d355bfae1294ffd9114d81/
- Dharmapala, D. (2018). Compliance costs via bunching (SOX float threshold). https://consensus.app/papers/details/ced3b17797175a56bc54afc6b007d3b3/
- Masulis, R. et al. (2018). Deal Initiation in M&A (premium determinants). JFQA. https://consensus.app/papers/details/9fa85a60b5a95583b3bbc53b1e5aaefb/
