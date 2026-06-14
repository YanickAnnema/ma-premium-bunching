# Claude-in-Excel prompt: price the EDGAR deal list (reliable channel)

Use this when the Python lseg-data desktop API keeps timing out. The Excel LSEG
add-in (=TR) is the proven-reliable channel and is not deal-quota limited.
Paste the box into Claude in Excel with Workspace open and signed in.

```
You are operating the LSEG Workspace Excel add-in (=TR works; the add-in is
reliable, unlike the Python desktop API). Compute takeover premia for a list of
completed US M&A deals and export the result. Price pulls are not quota-limited.

Setup
- Import the CSV at ..\data\deals_edgar.csv (relative to the ma-premium-bunching
  repo; ask me for the full path if needed) into a sheet named "deals". It has
  columns including: ann_date, target_ticker, offer_price, status, deal_key.
- Work only on rows where target_ticker is non-empty. Leave a notes column for
  rows you cannot price.

Per-deal columns to build (one row per deal)
1. unaff_date = ann_date minus 35 calendar days, formatted yyyy-mm-dd. This is
   about one trading month before announcement (the unaffected price date).
2. p0 (unaffected close). The historical ticker may be NYSE, Nasdaq, or other,
   so try exchange suffixes in order and take the first that returns a number.
   In one cell, with A=ticker and U=unaff_date:
     =IFERROR(@TR(A2&".O","TR.PriceClose","SDate="&U2&" CH=Fd"),
      IFERROR(@TR(A2&".N","TR.PriceClose","SDate="&U2&" CH=Fd"),
      IFERROR(@TR(A2&".OQ","TR.PriceClose","SDate="&U2&" CH=Fd"),
      IFERROR(@TR(A2&".A","TR.PriceClose","SDate="&U2&" CH=Fd"),
      IFERROR(@TR(A2&".K","TR.PriceClose","SDate="&U2&" CH=Fd"), NA())))))
   CH=Fd carries forward to the last close on or before that date. Because the
   date is historical, this resolves delisted targets too. Record which suffix
   worked in a "ric" column (repeat the IFERROR chain returning A2&".O" etc.).
3. premium = offer_price / p0 - 1.
4. p0_is_round = (ABS(p0 - ROUND(p0,0)) < 0.005).
5. completed = 1 (the list is completed deals; set IF(status="Completed",1,0)).
6. year = YEAR(ann_date).
7. target_car (market-adjusted [-1,+1], optional but include if time allows):
     tpre  = @TR(ric,"TR.PriceClose","SDate="&TEXT(ann-1,"yyyy-mm-dd")&" CH=Fd")
     tpost = @TR(ric,"TR.PriceClose","SDate="&TEXT(ann+2,"yyyy-mm-dd")&" CH=Fd")
     ipre  = @TR(".SPX","TR.PriceClose","SDate="&TEXT(ann-1,"yyyy-mm-dd")&" CH=Fd")
     ipost = @TR(".SPX","TR.PriceClose","SDate="&TEXT(ann+2,"yyyy-mm-dd")&" CH=Fd")
     target_car = (tpost/tpre - 1) - (ipost/ipre - 1)

Process and stability
- Do the p0 column first for all rows; let the add-in finish resolving (it may
  show "Requesting..." briefly). Then convert p0, premium, and the other formula
  columns to VALUES (paste-special values) so they do not re-query. Then add the
  CAR columns and value them too.
- Report how many rows got a numeric p0 versus NA (the resolution rate).

Export
- Save a sheet with exactly these columns as ..\data\deals_enriched.csv:
  deal_key, premium, p0, p0_is_round, completed, target_car, year, ric, offer_price
- Confirm the row count and that premium/p0 are numbers, not formulas.

Report: rows priced, rows that failed to resolve (NA p0), and the median premium.
```

After it writes `deals_enriched.csv`, run `python run_pipeline.py` to get the
bunching result on the real sample.
```
