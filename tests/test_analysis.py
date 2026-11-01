import pandas as pd
from backend.app import analysis as a


def ts(s):
    return pd.Timestamp(s, tz="UTC")


def test_no_forecast_published_after_cutoff_is_used():
    # Target: 5 Jan 12:00. Cutoff (9h) = 4 Jan 09:00.
    fc = pd.DataFrame({
        "publishTime": [ts("2026-01-03 06:00"), ts("2026-01-04 08:00"), ts("2026-01-04 10:00")],
        "startTime": [ts("2026-01-05 12:00")] * 3,
        "forecast": [100, 200, 999],  # 999 was published AFTER the cutoff -> must be ignored
    })
    out = a.select_latest(fc, cutoff_hour=9)
    assert len(out) == 1 and out.iloc[0]["forecast"] == 200


def test_target_with_only_late_forecasts_is_dropped():
    fc = pd.DataFrame({"publishTime": [ts("2026-01-04 10:00")],
                       "startTime": [ts("2026-01-05 12:00")], "forecast": [1]})
    assert a.select_latest(fc, 9).empty


def test_metrics_sign_and_values():
    df = pd.DataFrame({"forecast": [110, 90], "actual": [100, 100]})
    df["error"] = df["forecast"] - df["actual"]
    m = a.metrics(df)
    assert m["mae"] == 10 and m["bias"] == 0 and m["rmse"] == 10


def test_over_forecast_gives_positive_error():
    fc = pd.DataFrame({"publishTime": [ts("2026-01-01 00:00")], "startTime": [ts("2026-01-05 12:00")],
                       "forecast": [500]})
    act = pd.DataFrame({"startTime": [ts("2026-01-05 12:00")], "actual": [400]})
    assert a.with_actuals(fc, act).iloc[0]["error"] == 100
