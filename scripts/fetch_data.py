"""Download real data from Elexon (BMRS) once and save it to data/*.csv.

Run on your own machine:   python scripts/fetch_data.py
Needs internet. No API key needed.
"""
import sys, time
from pathlib import Path
import pandas as pd
import requests

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
OUT = Path(__file__).resolve().parents[1] / "data"


def get(url, params):
    for attempt in range(4):
        r = requests.get(url, params={**params, "format": "json"}, timeout=120)
        if r.status_code == 200:
            return r.json()
        print(f"  HTTP {r.status_code}: {r.text[:300]}")
        time.sleep(2 * (attempt + 1))
    sys.exit("Giving up. Check the URL and parameter names against the Elexon API docs.")


def chunks(start, end, days):
    s = pd.Timestamp(start)
    while s < pd.Timestamp(end):
        e = min(s + pd.Timedelta(days=days), pd.Timestamp(end))
        yield s, e
        s = e


def fetch_actual():
    rows = []
    for s, e in chunks("2026-01-01", "2026-02-03", 7):
        print("FUELHH", s.date(), e.date())
        rows += get(f"{BASE}/FUELHH/stream", {
            "settlementDateFrom": s.strftime("%Y-%m-%d"),
            "settlementDateTo": e.strftime("%Y-%m-%d"),
            "fuelType": "WIND"})
    df = pd.DataFrame(rows)
    df = df[df["fuelType"] == "WIND"][["startTime", "generation"]]
    return df.drop_duplicates("startTime").sort_values("startTime")


def fetch_forecast():
    rows = []
    for s, e in chunks("2025-12-31", "2026-02-01", 2):
        print("WINDFOR", s.date(), e.date())
        rows += get(f"{BASE}/WINDFOR/stream", {
            "publishDateTimeFrom": s.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "publishDateTimeTo": e.strftime("%Y-%m-%dT%H:%M:%SZ")})
    df = pd.DataFrame(rows)[["publishTime", "startTime", "generation"]]
    return df.drop_duplicates(["publishTime", "startTime"]).sort_values(["publishTime", "startTime"])


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    a, f = fetch_actual(), fetch_forecast()
    a.to_csv(OUT / "actual.csv", index=False)
    f.to_csv(OUT / "forecast.csv", index=False)
    print(f"actual rows: {len(a)}, forecast rows: {len(f)}")
    print("actual  :", a.startTime.min(), "->", a.startTime.max())
    print("forecast:", f.publishTime.min(), "->", f.publishTime.max())
