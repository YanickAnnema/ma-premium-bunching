"""
Fill missing target tickers in data/deals_edgar.csv.

Completion 8-Ks often omit the ticker, but the target's announcement-period
filing (8-K / 425 / DEFA14A press release) reliably carries "(NYSE: TICKER)".
This pass locates that filing via the SEC submissions API (by CIK and the parsed
announcement date) and parses the ticker from its press release.

Runs as a separate pass over the finished deal list, so it does not disturb a
running edgar_deals.py crawl. Resumable: only blank tickers are attempted, and
the CSV is checkpointed periodically. Run after edgar_deals.py, before
lseg_prices.py.

Requirements: pip install requests pandas. Set EDGAR_UA.
"""

import os
import re
import time

import requests
import pandas as pd

EDGAR_UA = "Yanick Annema yftannema@gmail.com"   # REQUIRED by SEC
SLEEP = 0.15

_HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(_HERE, "..", "data", "deals_edgar.csv")
SUB = "https://data.sec.gov/submissions/CIK{:010d}.json"
ARCH = "https://www.sec.gov/Archives/edgar/data"
HEADERS = {"User-Agent": EDGAR_UA, "Accept-Encoding": "gzip, deflate"}

EXCOLON_RE = re.compile(r"\(\s*(?:nasdaq|nyse|amex)[^):]*:\s*([A-Z]{1,5})\s*\)", re.I)
TAG_RE = re.compile(r"<[^>]+>")
STOP = {"inc", "corp", "corporation", "company", "co", "holdings", "group", "ltd",
        "llc", "plc", "the", "and", "of", "international", "technologies", "technology",
        "systems", "pharmaceuticals", "pharma", "financial", "bancorp", "industries",
        "solutions", "resources", "energy", "capital", "partners", "global", "health",
        "networks", "media", "communications", "services", "products", "enterprises",
        "laboratories", "management", "trust", "therapeutics", "biosciences"}


def _target_words(name):
    ws = [w.lower() for w in re.findall(r"[A-Za-z]{3,}", str(name)) if w.lower() not in STOP]
    ws.sort(key=len, reverse=True)
    return ws[:2]   # the two most distinctive words, to avoid acquirer cross-matches


def ticker_near_target(text, target_name):
    """Pick the (EXCHANGE: TICKER) whose preceding text names the target, so we
    get the target ticker, not the acquirer's (which usually appears first)."""
    words = _target_words(target_name)
    if not words:
        return None
    for m in EXCOLON_RE.finditer(text):
        ctx = text[max(0, m.start() - 90):m.start()].lower()
        if any(w in ctx for w in words):
            return m.group(1)
    return None
ANN_FORMS = {"8-K", "8-K/A", "425", "DEFA14A", "SC 14D9", "SC TO-T"}


def _get(url):
    for i in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                return r
            if r.status_code in (429, 503):
                time.sleep(1.5 * (i + 1))
                continue
            return None
        except requests.RequestException:
            time.sleep(1.0 * (i + 1))
    return None


def _exhibit99_urls(base):
    r = _get(f"{base}/index.json")
    time.sleep(SLEEP)
    if r is None:
        return []
    try:
        items = r.json()["directory"]["item"]
    except Exception:
        return []
    return [f"{base}/{it['name']}" for it in items
            if it.get("name", "").lower().endswith((".htm", ".html"))
            and "99" in it.get("name", "").lower()]


def announcement_ticker(cik, ann_date, target_name):
    """Find an announcement-period filing near ann_date and parse the TARGET's ticker."""
    r = _get(SUB.format(int(cik)))
    time.sleep(SLEEP)
    if r is None:
        return None
    try:
        rec = r.json()["filings"]["recent"]
    except Exception:
        return None
    forms = rec.get("form", [])
    dates = rec.get("filingDate", [])
    accs = rec.get("accessionNumber", [])
    docs = rec.get("primaryDocument", [])
    ann = pd.to_datetime(ann_date, errors="coerce")
    if pd.isna(ann):
        return None

    cands = []
    for f, d, a, doc in zip(forms, dates, accs, docs):
        if f not in ANN_FORMS:
            continue
        fd = pd.to_datetime(d, errors="coerce")
        if pd.notna(fd) and abs((fd - ann).days) <= 10:
            cands.append((abs((fd - ann).days), a, doc))
    cands.sort()

    for _, a, doc in cands[:4]:
        base = f"{ARCH}/{int(cik)}/{a.replace('-', '')}"
        urls = ([f"{base}/{doc}"] if doc else []) + _exhibit99_urls(base)
        for url in urls:
            rr = _get(url)
            time.sleep(SLEEP)
            if rr is None:
                continue
            t = ticker_near_target(TAG_RE.sub(" ", rr.text), target_name)
            if t:
                return t
    return None


def main():
    df = pd.read_csv(CSV, dtype={"target_ticker": str})
    if "target_ticker" not in df.columns:
        df["target_ticker"] = ""
    df["target_ticker"] = df["target_ticker"].fillna("").astype(str)
    # re-resolve EVERY row by target-name match, overwriting acquirer-contaminated
    # tickers. Resumable via tkr_checked.
    if "tkr_checked" not in df.columns:
        df["tkr_checked"] = False
    df["tkr_checked"] = df["tkr_checked"].fillna(False).astype(bool)
    todo = df.index[~df["tkr_checked"]].tolist()
    print(f"re-resolving target tickers (name-matched) for {len(todo)} of {len(df)} rows")

    found = 0
    for n, i in enumerate(todo, 1):
        t = announcement_ticker(df.at[i, "target_cik"], df.at[i, "ann_date"], df.at[i, "target_name"])
        df.at[i, "target_ticker"] = t or ""
        df.at[i, "tkr_checked"] = True
        if t:
            found += 1
        if n % 25 == 0:
            df.to_csv(CSV, index=False)
            print(f"  {n}/{len(todo)} processed, {found} target tickers found this run")
    df.to_csv(CSV, index=False)
    total = int((df["target_ticker"].str.strip() != "").sum())
    print(f"done. {total} of {len(df)} rows now have a name-verified target ticker")


if __name__ == "__main__":
    main()
