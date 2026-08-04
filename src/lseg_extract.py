"""
LSEG M&A deal extractor (Python, desktop-session mode).

Why this exists: the Excel =TR add-in pulls deal-level M&A data but the deals
screen throttles after a few hundred deals, and the cap did not reset on a
Workspace restart. This script piggybacks on the SAME running Workspace via the
lseg-data library, so it uses the same entitlement as Excel but is fully
automatable: chunked by announcement-date windows, checkpointed, and resumable.

Read this honestly: a Python client cannot beat an entitlement cap. If the throttle
is daily, re-run on later days and the script continues from the last finished
window. If the throttle is a hard account limit, neither Excel nor this script can
extract the full universe, and the SEC EDGAR route (us-public targets, free) is
the real fallback.

Requirements on the user's machine (cannot run in a sandbox):
  - LSEG Workspace running and signed in, same machine.
  - pip install lseg-data pandas        (older installs: refinitiv-data, same API)

Run in Spyder (F5) or: python lseg_extract.py
Edit the CONFIG block, then run. It writes data/deals_real.csv incrementally and
data/daq_done_windows.json as the resume checkpoint.
"""

import os
import json
import time
from datetime import date, timedelta

import pandas as pd

try:
    import lseg.data as ld            # current package name
except ImportError:                   # pragma: no cover
    import refinitiv.data as ld       # older name, identical API

# ----------------------------- CONFIG -----------------------------
NATIONS     = ["US", "GB"]            # ISO codes; full country names error in SCREEN
DATE_START  = date(2010, 1, 1)
DATE_END    = date(2025, 12, 31)
MIN_VALUE   = 100_000_000            # raw USD, TR.MnARankValueIncNetDebt
WINDOW_DAYS = 7                      # small, to stay under the per-call row cap

_HERE     = os.path.dirname(os.path.abspath(__file__))
OUT_DIR   = os.path.join(_HERE, "..", "data")
DEALS_CSV = os.path.join(OUT_DIR, "deals_real.csv")
DONE_JSON = os.path.join(OUT_DIR, "daq_done_windows.json")

# Lean field set and filters validated in the Excel test. The universe/field
# syntax is identical between the Excel =TR template and get_data.
FIELDS = [
    "TR.MnAAnnDate",
    "TR.MnATargetFullName",
    "TR.MnATargetPermID",
    "TR.MnATargetNation",
    "TR.MnATargetPublicStatus",
    "TR.MnAAcquirorFullName",
    "TR.MnAStatus",
    "TR.MnAOfferPricePerShare",
    "TR.MnAOfferPricePerShareCurrency",
]

# Canonical column names in the SAME order as FIELDS. get_data returns an
# "Instrument" column first, then the requested fields in order, so we map by
# POSITION after dropping "Instrument". Positional is deterministic; matching on
# header text mis-assigned columns in an earlier version.
CANON = ["ann_date", "target_name", "target_permid", "target_nation",
         "target_public_status", "acquiror_name", "status",
         "offer_price", "currency"]


def screen(start, end):
    nat = ",".join(f'"{n}"' for n in NATIONS)
    return (
        "SCREEN(U(IN(DEALS)/*UNV:DEALSMNA*/),"
        f"BETWEEN(TR.MnAAnnDate,{start:%Y-%m-%d},{end:%Y-%m-%d}),"
        f"IN(TR.MnATargetNation,{nat}),"
        f"TR.MnARankValueIncNetDebt>={MIN_VALUE},"
        "TR.MnAOfferPricePerShare>0)"
    )


def windows():
    s = DATE_START
    while s <= DATE_END:
        e = min(s + timedelta(days=WINDOW_DAYS - 1), DATE_END)
        yield s, e
        s = e + timedelta(days=1)


def normalize(df):
    """Map columns to canonical names by position (request order, sans Instrument)."""
    data_cols = [c for c in df.columns if str(c).strip().lower() != "instrument"]
    n = min(len(data_cols), len(CANON))
    out = df[data_cols[:n]].copy()
    out.columns = CANON[:n]
    return out


def dump_columns_once(raw):
    """Write the true raw headers once, so the mapping can be verified."""
    path = os.path.join(OUT_DIR, "_raw_columns.txt")
    if os.path.exists(path) or raw is None or len(raw.columns) == 0:
        return
    with open(path, "w") as fh:
        fh.write("raw get_data columns (in order):\n")
        fh.write(repr(list(raw.columns)) + "\n\n")
        fh.write("first rows:\n")
        fh.write(raw.head(5).to_string())


def load_done():
    if os.path.exists(DONE_JSON):
        return set(json.load(open(DONE_JSON)))
    return set()


def save_done(done):
    json.dump(sorted(done), open(DONE_JSON, "w"))


def append_deals(df):
    header = not os.path.exists(DEALS_CSV)
    df.to_csv(DEALS_CSV, mode="a", header=header, index=False)


def _price_alive():
    """A plain price pull still works after the deal quota locks; use it to tell
    a real empty window apart from a quota lockout."""
    try:
        p = ld.get_data(universe="AAPL.O", fields=["TR.PriceClose"])
        return p is not None and not p.empty
    except Exception:
        return False


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    ld.open_session()                 # auto-detects the running Workspace session
    done = load_done()
    pulled = 0
    try:
        for s, e in windows():
            key = f"{s:%Y-%m-%d}"
            if key in done:
                continue
            try:
                raw = ld.get_data(universe=screen(s, e), fields=FIELDS)
            except Exception as ex:
                print(f"[stop] error at {key}: {ex}")
                break

            dump_columns_once(raw)
            # quota lock shows up as blank target-name values; probe that column
            probe = None
            if raw is not None and not raw.empty:
                data_cols = [c for c in raw.columns if str(c).strip().lower() != "instrument"]
                if data_cols:
                    probe = raw[data_cols[1 if len(data_cols) > 1 else 0]]
            empty = probe is None or probe.isna().all()

            if empty:
                if _price_alive():
                    print(f"[quota] locked at {key}. {pulled} deals appended this run. "
                          f"Re-run later to resume from here.")
                    break
                print(f"[ok] {key}: genuinely no deals, marking done")
                done.add(key)
                save_done(done)
                continue

            df = normalize(raw)
            if "target_public_status" in df.columns:
                df = df[df["target_public_status"] == "Public"].copy()
            append_deals(df)
            pulled += len(df)
            done.add(key)
            save_done(done)
            time.sleep(0.2)           # be polite to the service
    finally:
        save_done(done)
        try:
            ld.close_session()
        except Exception:
            pass

    print(f"windows done: {len(done)} | deals appended this run: {pulled}")
    if os.path.exists(DEALS_CSV):
        total = sum(1 for _ in open(DEALS_CSV)) - 1
        print(f"total rows in {os.path.basename(DEALS_CSV)}: {total}")
        print("De-duplicate on [target_permid, ann_date, acquiror_name] when loading.")


if __name__ == "__main__":
    main()
