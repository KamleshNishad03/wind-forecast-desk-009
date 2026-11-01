"""Make FAKE data in the same shape as the Elexon data, for offline testing only."""
import numpy as np, pandas as pd
from pathlib import Path

rng = np.random.default_rng(7)
out = Path(__file__).resolve().parents[1] / "data" / "sample"
out.mkdir(parents=True, exist_ok=True)

t = pd.date_range("2025-12-30", "2026-02-03", freq="30min", tz="UTC")
walk = np.cumsum(rng.normal(0, 120, len(t)))
walk = walk - np.convolve(walk, np.ones(96) / 96, mode="same")
truth = np.clip(5500 + walk + 1500 * np.sin(np.arange(len(t)) / 60), 200, 13000)
actual = pd.DataFrame({"startTime": t, "generation": truth.round(0)})
actual.to_csv(out / "actual.csv", index=False)

series = pd.Series(truth, index=t)
rows = []
for p in pd.date_range("2025-12-31", "2026-01-31 23:00", freq="1h", tz="UTC"):
    targets = pd.date_range(p + pd.Timedelta(hours=1), periods=96, freq="1h")
    targets = targets[targets.isin(series.index)]
    h = (targets - p).total_seconds() / 3600
    noise = rng.normal(0, 150 + 45 * h) - 20 * h  # error grows with horizon, slight over-forecast
    rows.append(pd.DataFrame({"publishTime": p, "startTime": targets,
                              "generation": np.clip(series[targets].values + noise, 0, None).round(0)}))
pd.concat(rows).to_csv(out / "forecast.csv", index=False)
print("sample data written to", out)
