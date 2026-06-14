"""
SEC EDGAR M&A deal extractor (free, no quota, US public targets).

Design: search the TARGET's completion filing, not the announcement. When a
public company is acquired it files an 8-K reporting Item 3.01 (delisting). Only
the target files a delisting notice, so the filer is unambiguously the target.
That filing states the merger consideration as clean language ("converted into
the right to receive $X.XX in cash") and names the original announcement date
("Agreement and Plan of Merger, dated as of <DATE>"), and its cover page carries
the target's then-current trading symbol.

Why not the announcement 8-K: both the acquirer and the target file announcement
8-Ks, so the filer is ambiguous (acquirers get recorded as targets), and a
generic per-share regex there picks up par value and dividends. The completion
filing avoids all three problems. The cost is that this captures COMPLETED deals
only, which is a clean sample for a premium-bunching study; withdrawn deals and
the completion-outcome test are a separate later pass.

Outputs data/deals_edgar.csv: ann_date, completion_date, target_name,
target_cik, target_ticker, offer_price, status, url, deal_key.

SEC fair-access: keep requests modest, send a real User-Agent with a contact
email (set EDGAR_UA). Run: `python edgar_deals.py`. Resumable by date chunk.
Requirements: pip install requests pandas
"""

import os
import re
import json
import time
from datetime import date, timedelta

import requests
import pandas as pd

# ----------------------------- CONFIG -----------------------------
EDGAR_UA   = "Yanick Annema yftannema@gmail.com"   # REQUIRED by SEC fair-access
DATE_START = date(2010, 1, 1)
DATE_END   = date(2025, 12, 31)
CHUNK_DAYS = 14
SLEEP      = 0.15

_HERE   = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(_HERE, "..", "data")
OUT_CSV = os.path.join(OUT_DIR, "deals_edgar.csv")
DONE_JSON = os.path.join(OUT_DIR, "edgar_done_chunks.json")

EFTS = "https://efts.sec.gov/LATEST/search-index"
ARCH = "https://www.sec.gov/Archives/edgar/data"
HEADERS = {"User-Agent": EDGAR_UA, "Accept-Encoding": "gzip, deflate"}

# merger-consideration phrasing only, so par value and dividends are not matched
PRICE_PATTERNS = [
    re.compile(r"right to receive[^$]{0,90}\$\s?(\d{1,4}(?:\.\d{2})?)", re.I),
    re.compile(r"converted into[^$]{0,140}\$\s?(\d{1,4}(?:\.\d{2})?)", re.I),
    re.compile(r"merger consideration[^$]{0,90}\$\s?(\d{1,4}(?:\.\d{2})?)", re.I),
    re.compile(r"\$\s?(\d{1,4}(?:\.\d{2})?)\s+in cash,?\s+(?:without interest|per share|for each)", re.I),
    re.compile(r"for\s+\$\s?(\d{1,4}(?:\.\d{2})?)\s+(?:in cash\s+)?per share", re.I),
    re.compile(r"\$\s?(\d{1,4}(?:\.\d{2})?)\s+per share\s+in cash", re.I),
]
ANNDATE_RE = re.compile(
    r"Agreement and Plan of Merger[^.]{0,90}?dated\s+(?:as of\s+)?"
    r"([A-Z][a-z]+\.?\s+\d{1,2},\s+\d{4})")
PAREN_RE = re.compile(r"\(([^)]+)\)")
TICKER_OK = re.compile(r"[A-Z]{1,5}(?:-[A-Z]{1,3})?$")
# "(NASDAQ: IGOI)" / "(NYSE: ABC)" / "(NASDAQ Global Select Market: XYZ)"
EXCOLON_RE = re.compile(r"\(\s*(?:nasdaq|nyse|amex)[^):]*:\s*([A-Z]{1,5})\s*\)", re.I)
# 2019+ cover page: symbol immediately before the exchange name
EXCH_RE = re.compile(r"\b([A-Z]{1,5})\s+(?:The\s+)?(?:Nasdaq|New York Stock Exchange|NYSE American|NYSE)")
SKIP_DOC = re.compile(r"(index|header|metalink|filingsummary|financial_report|^r\d+\.htm|^show|report\.css)", re.I)
TAG_RE = re.compile(r"<[^>]+>")
SPAC_RE = re.compile(r"acquisition corp|blank check", re.I)


def _get(url, params=None, tries=4):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                return r
            if r.status_code in (429, 503):
                time.sleep(1.5 * (i + 1))
                continue
            return None
        except requests.RequestException:
            time.sleep(1.0 * (i + 1))
    return None


def fetch_text(url):
    r = _get(url)
    time.sleep(SLEEP)
    return TAG_RE.sub(" ", r.text) if r is not None else None


def ticker_from_display(names):
    for nm in names:
        if "CIK" in nm:
            nm = nm.split("(CIK")[0]
        for grp in PAREN_RE.findall(nm):
            tok = grp.split(",")[0].strip()
            if TICKER_OK.match(tok):
                return tok
    return None


def parse_ticker(text):
    m = EXCOLON_RE.search(text) or EXCH_RE.search(text)
    return m.group(1) if m else None


def exhibit_urls(cik, adsh, skip=None, limit=4):
    """Likely price/ticker-bearing exhibits (press release first), from the index.
    Used when the main 8-K lacks the price or the ticker (pre-2019 filings)."""
    base = f"{ARCH}/{cik}/{adsh.replace('-', '')}"
    idx = _get(f"{base}/index.json")
    time.sleep(SLEEP)
    if idx is None:
        return []
    try:
        items = idx.json()["directory"]["item"]
    except Exception:
        return []

    def rank(name):
        s = name.lower()
        if "press" in s or "99" in s:                 # EX-99.x = press release (covers exv99w1, ex991, ...)
            return 0
        if "merger" in s or re.search(r"ex.{0,3}2", s):  # EX-2.x merger agreement
            return 1
        return 2

    docs = []
    for it in items:
        nm = it.get("name", "")
        if nm.lower().endswith((".htm", ".html")) and not SKIP_DOC.search(nm):
            docs.append((rank(nm), nm))
    docs.sort()
    return [f"{base}/{nm}" for _, nm in docs if f"{base}/{nm}" != skip][:limit]


def parse_price(text):
    from collections import Counter
    vals = []
    for pat in PRICE_PATTERNS:
        for m in pat.findall(text):
            try:
                v = float(m)
            except ValueError:
                continue
            if 1.0 <= v <= 100000:
                vals.append(round(v, 2))
    return Counter(vals).most_common(1)[0][0] if vals else None


def parse_ann_date(text):
    m = ANNDATE_RE.search(text)
    if not m:
        return None
    d = pd.to_datetime(m.group(1), errors="coerce")
    return d.date().isoformat() if pd.notna(d) else None


def search_chunk(start, end):
    """Target completion filings: main 8-K, Item 3.01 (delisting), not SPAC."""
    out, frm = {}, 0
    while frm < 10000:
        params = {"q": '"Agreement and Plan of Merger"', "forms": "8-K",
                  "startdt": start.isoformat(), "enddt": end.isoformat(), "from": frm}
        r = _get(EFTS, params)
        time.sleep(SLEEP)
        if r is None:
            break
        hits = r.json().get("hits", {}).get("hits", [])
        if not hits:
            break
        for h in hits:
            s = h["_source"]
            if s.get("file_type") != "8-K":
                continue
            if "3.01" not in (s.get("items") or []):     # delisting = the target
                continue
            names = s.get("display_names", [])
            if any(SPAC_RE.search(n) for n in names):
                continue
            adsh = s["adsh"]
            if adsh in out:
                continue
            cik = s["ciks"][0].lstrip("0")
            fname = h["_id"].split(":", 1)[1]
            out[adsh] = {
                "completion_date": s["file_date"],
                "target_name": names[0].split("(")[0].strip(),
                "target_cik": cik,
                "target_ticker": ticker_from_display(names),
                "adsh": adsh,
                "url": f"{ARCH}/{cik}/{adsh.replace('-', '')}/{fname}",
            }
        frm += len(hits)
        if len(hits) < 100:
            break
    return list(out.values())


def load_done():
    return set(json.load(open(DONE_JSON))) if os.path.exists(DONE_JSON) else set()


def save_done(d):
    json.dump(sorted(d), open(DONE_JSON, "w"))


def append(rows):
    pd.DataFrame(rows).to_csv(OUT_CSV, mode="a", header=not os.path.exists(OUT_CSV), index=False)


def chunks():
    s = DATE_START
    while s <= DATE_END:
        e = min(s + timedelta(days=CHUNK_DAYS - 1), DATE_END)
        yield s, e
        s = e + timedelta(days=1)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    if "@" not in EDGAR_UA:
        print("Set EDGAR_UA to 'Your Name your@email' first (SEC requires it).")
        return
    done = load_done()
    total = 0
    for s, e in chunks():
        key = s.isoformat()
        if key in done:
            continue
        cands = search_chunk(s, e)
        rows = []
        for c in cands:
            text = fetch_text(c["url"])
            if text is None:
                continue
            price = parse_price(text)
            ann = parse_ann_date(text)
            tic = c["target_ticker"] or parse_ticker(text)
            if price is None or ann is None or not tic:
                # price/date usually in the main 8-K; the ticker often only in the
                # press release. Scan exhibits to fill whatever is missing.
                for ex in exhibit_urls(c["target_cik"], c["adsh"], skip=c["url"]):
                    ext = fetch_text(ex)
                    if not ext:
                        continue
                    if price is None:
                        price = parse_price(ext)
                    if not tic:
                        tic = parse_ticker(ext)
                    if ann is None:
                        ann = parse_ann_date(ext)
                    if price is not None and ann is not None and tic:
                        break
            # ticker is optional: CIK is always present and is resolved downstream
            if price is None or ann is None:
                continue
            c["offer_price"] = price
            c["ann_date"] = ann
            c["target_ticker"] = tic or ""
            # cash vs cash-and-stock; a premium study uses the cash deals
            c["consideration"] = "mixed" if re.search(r"in cash and.{0,80}?shares?\b", text, re.I | re.S) else "cash"
            c["status"] = "Completed"
            c["deal_key"] = f"{c['target_cik']}_{ann.replace('-', '')}"
            c.pop("adsh", None)
            rows.append(c)
        if rows:
            append(rows)
            total += len(rows)
        done.add(key)
        save_done(done)
        print(f"{key}: {len(cands)} delisting filings, {len(rows)} priced "
              f"(running total {total})")
    print(f"done. new deals this run: {total}")
    if os.path.exists(OUT_CSV):
        print(f"total rows: {sum(1 for _ in open(OUT_CSV)) - 1} in {os.path.basename(OUT_CSV)}")


if __name__ == "__main__":
    main()
