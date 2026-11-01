import pandas as pd
a = pd.read_csv("data/actual.csv", parse_dates=["startTime"])
f = pd.read_csv("data/forecast.csv", parse_dates=["startTime", "publishTime"])
print("actual step :", a.startTime.diff().mode()[0])
print("forecast step:", f.sort_values(["publishTime","startTime"]).groupby("publishTime").startTime.diff().mode()[0])
print("publish times:", f.publishTime.nunique(), "| per day ~", round(f.publishTime.nunique() / 32, 1))
h = (f.startTime - f.publishTime).dt.total_seconds() / 3600
print("horizon hours: min", h.min(), "| median", h.median(), "| max", h.max())
print("wind MW: actual min/max", a.generation.min(), a.generation.max())
print("wind MW: forecast min/max", f.generation.min(), f.generation.max())