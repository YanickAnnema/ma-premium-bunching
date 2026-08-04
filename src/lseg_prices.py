"""
Phase B: price join and contract columns (Python, desktop-session mode).

Reads data/deals_real.csv, resolves each target PermID to a tradable RIC, pulls
prices, and writes data/deals_enriched.csv with the analysis contract. Price and
reference pulls are NOT subject to the deal-screen quota, so this runs even while
the deals screen is locked. Resumable: rows already priced are skipped.

Data-quality handling learned from the pilot:
  - PermID identifies the company, not a quote, so resolve PermID -> primary RIC
    first (get_data, the same mechanism Excel =TR uses), then price the RIC.
  - The UNAFFECTED price is taken about one month (22 trading days) before the
    announcement, not one day before. The one-day price leaks: pre-bid run-up
    collapses the premium toward zero. One month before is standard practice.
  - UK quotes (.L) are in pence (GBp) while the offer is in pounds, a 100x unit
    mismatch, so .L prices are divided by 100.
  - Only clean primary US/UK listings are kept; OTC and mis-resolved foreign
    quotes are dropped.

Output: deal_key, premium, p0, p0_is_round, completed, target_car, currency,
year, plus descriptive carry-throughs.

Requirements: LSEG Workspace running, pip install lseg-data pandas.
"""

import os
import re
import time
from datetime import timedelta

import pandas as pd

try:
    import lseg.data as ld
except ImportError:                   # pragma: no cover
    import refinitiv.data as ld

_HERE   = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(_HERE, "..", "data")
# prefer the EDGAR deal list if present, else the LSEG-screen list
_EDGAR  = os.path.join(OUT_DIR, "deals_edgar.csv")
IN_CSV  = _EDGAR if os.path.exists(_EDGAR) else os.path.join(OUT_DIR, "deals_real.csv")
OUT_CSV = os.path.join(OUT_DIR, "deals_enriched.csv")

UNAFFECTED_TD = 22          # trading days before announcement for the unaffected price
KEEP_MARKET = re.compile(r"\.(OQ|N|A|L)(\^|$)")   # clean US/UK primary listings
IS_UK = re.compile(r"\.L(\^|$)")

IDX_MAP = {"US": ".SPX", "USA": ".SPX", "United States": ".SPX",
           "GB": ".FTSE", "UK": ".FTSE", "United Kingdom": ".FTSE"}


def index_for(nation):
    n = str(nation).strip()
    if "united kingdom" in n.lower() or n.upper() in ("GB", "UK"):
        return ".FTSE"
    return ".SPX"


def _norm_id(x):
    """Normalize an identifier: integer-valued PermIDs to clean ints, else str."""
    try:
        f = float(x)
        if f.is_integer():
            return str(int(f))
    except (ValueError, TypeError):
        pass
    return str(x).strip()


def _get_data(universe, fields, tries=3):
    """get_data with retries; the desktop API often times out on a cold first call."""
    for k in range(tries):
        try:
            return ld.get_data(universe=universe, fields=fields)
        except Exception:
            time.sleep(3 * (k + 1))
    return None


def _warmup():
    for _ in range(5):
        try:
            h = ld.get_history("IBM.N", "TR.PriceClose", start="2023-01-03", end="2023-01-10")
            if h is not None and not h.empty:
                return True
        except Exception:
            pass
        time.sleep(3)
    return False


def resolve_rics(ids):
    """Identifier (OrgPermID or ticker) -> primary-quote RIC, batched, defensive."""
    uniq = sorted({_norm_id(p) for p in ids if pd.notna(p) and str(p).strip()})
    out = {}
    for i in range(0, len(uniq), 25):
        chunk = uniq[i:i + 25]
        df = None
        for fld in ("TR.PrimaryQuote", "TR.RIC"):
            df = _get_data(chunk, [fld])
            if df is not None and not df.empty:
                break
        if df is None or df.empty:
            continue
        for _, row in df.iterrows():
            pid = str(row.iloc[0]).split(".")[0].strip()
            ric = row.iloc[-1]
            if isinstance(ric, str) and ric.strip():
                out[pid] = ric.strip()
    return out


def _closes(instrument, ann, tries=3):
    """Daily closes from ~2 months before to a week after the announcement."""
    if not instrument:
        return None
    start = (ann - timedelta(days=60)).strftime("%Y-%m-%d")
    end = (ann + timedelta(days=8)).strftime("%Y-%m-%d")
    h = None
    for k in range(tries):
        try:
            h = ld.get_history(universe=instrument, fields="TR.PriceClose",
                               start=start, end=end)
            break
        except Exception:
            time.sleep(2 * (k + 1))
    if h is None or h.empty:
        return None
    s = h.iloc[:, 0]
    s.index = pd.to_datetime(s.index)
    return s.sort_index().dropna()


# US exchange RIC suffixes, tried in order; covers delisted targets via the
# historical date window. get_history (RDP) resolves these even when a bare
# ticker does not map through get_data.
US_SUFFIXES = [".O", ".N", ".OQ", ".A", ".K", ".PK", ".OB"]


def closes_for_ticker(ticker, ann):
    """Try ticker + each US suffix via get_history; return (series, ric) or (None, None)."""
    ticker = str(ticker).strip().upper()
    if not ticker:
        return None, None
    for sfx in US_SUFFIXES:
        s = _closes(ticker + sfx, ann, tries=1)   # fast probe; do not retry-loop each suffix
        if s is not None and len(s) >= 5:
            return s, ticker + sfx
    return None, None


def _event_points(s, ann):
    """(p_unaffected ~1m before, p_pre1 day before, p_post ~1-2d after)."""
    before = s[s.index < pd.Timestamp(ann)]
    after = s[s.index >= pd.Timestamp(ann)]
    if len(before) < 5 or len(after) < 2:
        return None
    p_unaff = before.iloc[-UNAFFECTED_TD] if len(before) >= UNAFFECTED_TD else before.iloc[0]
    return p_unaff, before.iloc[-1], after.iloc[1]


def enrich():
    df = pd.read_csv(IN_CSV)
    print(f"input: {os.path.basename(IN_CSV)}  rows: {len(df)}")
    if "consideration" in df.columns:                      # premium study uses cash deals
        df = df[df["consideration"].fillna("cash") == "cash"]
    df["ann_date"] = pd.to_datetime(df["ann_date"], errors="coerce")
    df["offer_price"] = pd.to_numeric(df["offer_price"], errors="coerce")
    # resolution id: PermID (LSEG screen), else ticker, else CIK (EDGAR)
    if "target_permid" in df.columns:
        df["resolve_id"] = df["target_permid"].map(_norm_id)
    else:
        # ticker only: a bare CIK does not resolve in LSEG and can hang a batch
        df["resolve_id"] = df.get("target_ticker", pd.Series("", index=df.index)).fillna("").astype(str).str.strip()
    df = df.dropna(subset=["ann_date", "offer_price"])
    df = df[df["resolve_id"].astype(str).str.len() > 0]
    df = df.drop_duplicates(subset=["resolve_id", "ann_date"]).reset_index(drop=True)

    done = set()
    if os.path.exists(OUT_CSV):
        prev = pd.read_csv(OUT_CSV)
        done = set(prev["deal_key"]) if "deal_key" in prev else set()

    ld.open_session()
    try:
        ld.get_config().set_param("http.request-timeout", 60)
    except Exception:
        pass
    if not _warmup():
        print("WARNING: LSEG desktop API not responding. Confirm Workspace is open "
              "and signed in, then re-run.")
    try:
        n = len(df)
        print(f"pricing {n} deals via get_history (ticker + US exchange suffix) ...")
        rows, skipped, resolved, priced_total = [], 0, 0, 0
        for j, (_, d) in enumerate(df.iterrows(), 1):
            tkr = str(d["resolve_id"]).strip()
            key = d["deal_key"] if "deal_key" in df.columns and pd.notna(d.get("deal_key")) \
                else f"{tkr}_{d.ann_date:%Y%m%d}"
            if key in done:
                continue
            ann = d.ann_date.to_pydatetime()
            tgt, ric = closes_for_ticker(tkr, ann)
            if tgt is None:
                skipped += 1
                continue
            resolved += 1
            idx = _closes(index_for(d.get("target_nation", "")), ann)
            if idx is None:
                skipped += 1
                continue
            tp = _event_points(tgt, ann)
            ip = _event_points(idx, ann)
            if tp is None or ip is None:
                skipped += 1
                continue
            p0, pre1, post = tp
            _iu, idx_pre1, idx_post = ip
            if p0 <= 0 or pre1 <= 0:
                skipped += 1
                continue
            rows.append({
                "deal_key": key,
                "premium": d.offer_price / p0 - 1.0,
                "p0": p0,
                "p0_is_round": abs(p0 - round(p0)) < 0.005,
                "completed": int(str(d.get("status", "")).strip().lower() == "completed"),
                "target_car": (post / pre1 - 1.0) - (idx_post / idx_pre1 - 1.0),
                "year": ann.year,
                "ric": ric,
                "offer_price": d.offer_price,
            })
            if len(rows) >= 50:
                pd.DataFrame(rows).to_csv(OUT_CSV, mode="a",
                    header=not os.path.exists(OUT_CSV), index=False)
                done.update(r["deal_key"] for r in rows)
                priced_total += len(rows)
                rows = []
                print(f"  {j}/{n}: priced {priced_total}, resolved {resolved}, skipped {skipped}")
        if rows:
            pd.DataFrame(rows).to_csv(OUT_CSV, mode="a",
                header=not os.path.exists(OUT_CSV), index=False)
            priced_total += len(rows)
    finally:
        try:
            ld.close_session()
        except Exception:
            pass

    print(f"priced {priced_total} deals -> {os.path.basename(OUT_CSV)} "
          f"(resolved {resolved} of {n} attempted, skipped {skipped})")


if __name__ == "__main__":
    enrich()
