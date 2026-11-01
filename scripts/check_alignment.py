import pandas as pd
a = pd.read_csv("data/actual.csv", parse_dates=["startTime"])
f = pd.read_csv("data/forecast.csv", parse_dates=["startTime", "publishTime"])
f["h"] = (f.startTime - f.publishTime).dt.total_seconds() / 3600
near = f[(f.h >= 0) & (f.h < 3)]  # newest forecasts only

for shift in [-2, -1, -0.5, 0, 0.5, 1, 2]:
    g = near.copy()
    g["startTime"] = g.startTime + pd.Timedelta(hours=shift)
    m = g.merge(a, on="startTime", suffixes=("_f", "_a"))
    e = m.generation_f - m.generation_a
    print(f"shift {shift:+}h  n={len(m)}  MAE={e.abs().mean():.0f}  bias={e.mean():.0f}  corr={m.generation_f.corr(m.generation_a):.3f}")

m = near.merge(a, on="startTime", suffixes=("_f", "_a"))
print("sum forecast / sum actual:", round(m.generation_f.sum() / m.generation_a.sum(), 3))