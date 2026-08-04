# Claude-in-Excel prompt: full M&A DAQ via LSEG formulas (no GUI export) v2

Paste the box into Claude in Excel. Resumable across Workspace sessions. v2 folds
in the live field audit: it never re-runs Step 0 on resume (so the session deal
quota is spent only on real deals), uses the confirmed filter syntax, joins on
PermID (no RIC field exists), and pulls a lean field set to stretch the quota.

```
You are operating the LSEG Workspace Excel add-in (=TR functions, signed in,
Datastream not entitled). Continue building the M&A premium data acquisition,
formulas only, no GUI export. A prior run already built the scaffold, so read it
before doing anything.

KNOWN LIMITS (engineer around them):
  1. Per-call row cap: very wide screens error "limit for the Number of Deals".
     7-day windows for US+GB with the value filter stay under the cap.
  2. Session deal quota: after roughly 200 deals pulled, screens return blank
     (names come back empty) while a plain =TR("AAPL.O","TR.PriceClose") still
     returns a number. The quota resets only on a Workspace restart. Blank-name
     rows are degraded data: never write them.

RESUME GUARD (do this first, every run):
  - If DAQ_control!B1 contains the SCREEN template AND DAQ_control!H:J shows the
    field audit is done, SKIP Step 0 and Step 1 entirely. Do not re-probe, do not
    re-validate, do not run any test screen. Go straight to Phase A. Re-probing
    burns the whole session quota and is why a prior run collected zero deals.
  - Only if the template or ledger is missing do you build them (Step 0 / Step 1
    below), and even then do the minimum and stop before extracting.

CONFIRMED from the field audit (use exactly these):
  Filters that screen:  BETWEEN(TR.MnAAnnDate,{START},{END}),
                        IN(TR.MnATargetNation,"US","GB")   [ISO codes, not names],
                        TR.MnARankValueIncNetDebt>=100000000   [raw USD units]
  Public status does NOT screen -> post-filter returned rows on
    TR.MnATargetPublicStatus = "Public".
  Invalid fields are dropped silently and columns shift -> parse the returned
    block by its header description, never by fixed column position.
  Join key is a PermID, not a RIC: use TR.MnATargetPermID
    (TR.MnATargetRIC / TR.MnATargetPrimaryRIC do not exist).
  Currency field is TR.MnAOfferPricePerShareCurrency (TR.MnACurrency missing).
  No deal-number field (TR.MnADealNumber missing) -> dedup key is
    TR.MnATargetPermID + TR.MnAAnnDate + TR.MnAAcquirorFullName.

QUOTA EFFICIENCY (important, the quota is the binding constraint):
  - Lean Phase A field set, in this order, nothing else:
      TR.MnAAnnDate, TR.MnATargetFullName, TR.MnATargetPermID,
      TR.MnATargetNation, TR.MnATargetPublicStatus, TR.MnAAcquirorFullName,
      TR.MnAStatus, TR.MnAOfferPricePerShare, TR.MnAOfferPricePerShareCurrency
    Advisors, consideration structure, and deal value are NOT pulled in Phase A.
    They become an optional enrichment pass later, keyed on the dedup key.
  - Try to add ONE more screen condition that excludes private targets, so the
    quota is not wasted on rows you discard. Test, in a single cheap probe only
    if you have not already hit the quota: a public-deal-type token or
    TR.MnAOfferPricePerShare present/greater-than-0 as a screen condition. If one
    works, add it to the template and note it in DAQ_log. If none work, proceed
    with the post-filter and accept the waste. Do not spend more than one probe
    on this.

PHASE A, resumable extraction loop:
  Deals sheet header (13 cols, already created): deal_key, ann_date, target_name,
  target_permid, target_nation, target_public_status, acquiror_name, status,
  offer_price, currency, consideration, deal_value, advisors. Phase A fills the
  lean columns; consideration/deal_value/advisors stay blank until enrichment.
  Loop DAQ_control rows with status = pending, oldest first. For each chunk:
    a. Substitute {START}/{END} into the template into DAQ_scratch.
    b. Wait, then read:
       - "limit for the Number of Deals": split into 7 daily sub-chunks as
         pending, mark this chunk split, continue.
       - Names blank WHILE =TR("AAPL.O","TR.PriceClose") still returns a number:
         SESSION QUOTA. Do not mark the chunk done, do not write its rows. Log
         "SESSION QUOTA REACHED at {chunk_start}", STOP, print the RESUME
         MESSAGE, do not start Phase B.
       - Rows returned with non-blank names: keep only TR.MnATargetPublicStatus =
         "Public", append to Deals de-duplicated on the dedup key, mark chunk done
         with rows_returned (post-filter count) and timestamp.
    c. Clear the scratch formula before the next chunk.
  Safety: if the FIRST chunk of a fresh session locks before returning any rows,
  the quota did not reset. Stop and tell the user the Workspace restart did not
  clear the quota.

PHASE B prices (only after every chunk is done; not quota-limited):
  First confirm the PermID join works for prices: test
  =TR(<one target_permid>,"TR.PriceClose","SDate=2023-01-03 CH=Fd"). If it returns
  a number, use PermIDs directly. If not, resolve each PermID to a RIC once via
  =TR(permid,"TR.RIC") into a helper column, and use that RIC for prices.
  Build IDX_MAP (US -> .SPX, GB -> .FTSE). Coerce ann_date to a date serial. Per
  Deals row, with TR.PriceClose and CH=Fd:
    p0 = close on/before ann_date-1; tgt_pre = ann_date-2; tgt_post = ann_date+2;
    idx_pre/idx_post = index closes at ann_date-2 and ann_date+2.
  Compute: premium = offer_price/p0 - 1; p0_is_round = ABS(p0-ROUND(p0,0))<0.005;
    target_car = (tgt_post/tgt_pre - 1) - (idx_post/idx_pre - 1);
    completed = IF(status="Completed",1,0)  [keep withdrawn]; year = YEAR(ann_date).
  Resumable: skip rows that already have p0.

EXPORT: save Deals as CSV in the workbook folder as deals_real.csv; report the
row count and confirm it wrote.

RESUME MESSAGE: "Phase A paused on the session deal quota. Done N of 835 chunks,
last completed = {date}, total deals so far = K. To continue: fully close and
reopen LSEG Workspace, then run this prompt again. It skips Step 0 and finished
chunks and resumes from the first pending one."

REPORT each run: chunks done this run, total done / 835, deals appended this run
(post public-filter), total in Deals, deals-per-session observed (for planning),
median rows per chunk, row cap hits, quota hit yes/no, and the result of the
private-target exclusion probe.
```
```

## Note for planning (not part of the prompt)

The single most useful output of the next session is the throughput number:
deals-per-session and deals-per-chunk. Read those off the next run's report, and
they tell us how many restart cycles the full scope really needs, without
guessing. Decide final scope from that number, not before.
