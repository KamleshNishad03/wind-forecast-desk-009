"""Core logic: pick the forecast that was available at decision time, then measure its error.

Terms used everywhere in this file:
- delivery day: the day the power is delivered (UTC).
- decision time (cutoff): `cutoff_hour` UTC on the day BEFORE the delivery day.
- error = forecast - actual (MW). Positive = forecast was too high (buyer under-buys).
"""
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

# Decisions are made in January 2026, so delivery days are 2 Jan .. 1 Feb 2026.
DELIVERY_START = pd.Timestamp("2026-01-02", tz="UTC")
DELIVERY_END = pd.Timestamp("2026-02-02", tz="UTC")  # exclusive
DEFAULT_CUTOFF_HOUR = 9


def data_dir():
    """Use real data if present, otherwise the fake sample data (and say so)."""
    if (DATA / "actual.csv").exists() and (DATA / "forecast.csv").exists():
        return DATA, False
    return DATA / "sample", True


@lru_cache(maxsize=1)
def load():
    d, is_sample = data_dir()
    actual = pd.read_csv(d / "actual.csv", parse_dates=["startTime"])
    fc = pd.read_csv(d / "forecast.csv", parse_dates=["startTime", "publishTime"])
    for df in (actual, fc):
        df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    fc["publishTime"] = pd.to_datetime(fc["publishTime"], utc=True)
    actual = actual.rename(columns={"generation": "actual"})[["startTime", "actual"]]
    actual = actual.drop_duplicates("startTime", keep="last")
    fc = fc.rename(columns={"generation": "forecast"})[["publishTime", "startTime", "forecast"]]
    return actual, fc, is_sample


def select_latest(fc: pd.DataFrame, cutoff_hour: int) -> pd.DataFrame:
    """For every target half-hour, keep the newest forecast published at or before the cutoff.

    Forecasts published after the cutoff are ignored: the buyer could not have seen them.
    """
    fc = fc[(fc.startTime >= DELIVERY_START) & (fc.startTime < DELIVERY_END)].copy()
    delivery_day = fc["startTime"].dt.floor("D")
    cutoff = delivery_day - pd.Timedelta(days=1) + pd.Timedelta(hours=cutoff_hour)
    fc = fc[fc["publishTime"] <= cutoff]
    return fc.sort_values("publishTime").groupby("startTime", as_index=False).last()


def with_actuals(fc: pd.DataFrame, actual: pd.DataFrame) -> pd.DataFrame:
    """Join forecast to actual on target time. Only times present in both are kept."""
    df = fc.merge(actual, on="startTime", how="inner")
    df["error"] = df["forecast"] - df["actual"]
    df["horizon_h"] = (df["startTime"] - df["publishTime"]).dt.total_seconds() / 3600
    return df


def selected(cutoff_hour: int) -> pd.DataFrame:
    actual, fc, _ = load()
    return with_actuals(select_latest(fc, cutoff_hour), actual)


def metrics(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"n": 0}
    e = df["error"]
    mean_actual = df["actual"].mean()
    return {
        "n": int(len(df)),
        "mae": float(e.abs().mean()),
        "rmse": float(np.sqrt((e**2).mean())),
        "bias": float(e.mean()),
        # In 9 out of 10 half-hours, wind fell short of the forecast by no more than this.
        "p90_shortfall": float(e.quantile(0.9)),
        "p90_abs_error": float(e.abs().quantile(0.9)),
        # Miss that is left after removing the average lean (the steady gap).
        "spread": float((e - e.mean()).abs().mean()),
        "bias_pct": float(e.mean() / mean_actual * 100) if mean_actual else None,
        "mean_actual": float(mean_actual),
        "mae_pct": float(e.abs().mean() / mean_actual * 100) if mean_actual else None,
    }


def horizon_errors() -> list:
    """Error by how far ahead the forecast was made (uses ALL January-target forecasts)."""
    actual, fc, _ = load()
    fc = fc[(fc.startTime >= DELIVERY_START - pd.Timedelta(days=1)) & (fc.startTime < DELIVERY_END)]
    df = with_actuals(fc, actual)
    df = df[df["horizon_h"] >= 0]
    bins = [0, 3, 6, 12, 24, 36, 48, 72, 120, np.inf]
    labels = ["0-3h", "3-6h", "6-12h", "12-24h", "24-36h", "36-48h", "2-3d", "3-5d", "5d+"]
    df["bucket"] = pd.cut(df["horizon_h"], bins=bins, labels=labels, right=False)
    out = []
    for b, g in df.groupby("bucket", observed=True):
        out.append({"bucket": str(b), "n": int(len(g)),
                    "mae": float(g["error"].abs().mean()), "bias": float(g["error"].mean()),
                    "spread": float((g["error"] - g["error"].mean()).abs().mean())})
    return out


def clean(obj):
    """Make pandas/numpy values JSON-safe (NaN -> None, Timestamp -> ISO text)."""
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean(v) for v in obj]
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, (float, np.floating)):
        return None if np.isnan(obj) or np.isinf(obj) else float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    return obj