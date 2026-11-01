from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from . import analysis as a

app = FastAPI(title="Wind forecast accuracy")


@app.get("/api/meta")
def meta():
    _, _, is_sample = a.load()
    days = [d.strftime("%Y-%m-%d") for d in
            a.pd.date_range(a.DELIVERY_START, a.DELIVERY_END - a.pd.Timedelta(days=1), freq="D")]
    return {"is_sample": is_sample, "delivery_days": days,
            "default_cutoff_hour": a.DEFAULT_CUTOFF_HOUR}


@app.get("/api/day")
def day(date: str, cutoff_hour: int = Query(a.DEFAULT_CUTOFF_HOUR, ge=0, le=23)):
    df = a.selected(cutoff_hour)
    d = df[df["startTime"].dt.strftime("%Y-%m-%d") == date].sort_values("startTime")
    if d.empty:
        raise HTTPException(404, "No data for this delivery day with this cutoff.")
    points = [{"t": r.startTime, "forecast": r.forecast, "actual": r.actual,
               "publishTime": r.publishTime} for r in d.itertuples()]
    return a.clean({"points": points, "metrics": a.metrics(d),
                    "latest_publish": d["publishTime"].max(),
                    "oldest_publish": d["publishTime"].min()})


@app.get("/api/summary")
def summary(cutoff_hour: int = Query(a.DEFAULT_CUTOFF_HOUR, ge=0, le=23)):
    df = a.selected(cutoff_hour)
    daily = []
    for date, g in df.groupby(df["startTime"].dt.strftime("%Y-%m-%d")):
        daily.append({"date": date, **a.metrics(g)})
    return a.clean({"overall": a.metrics(df), "daily": daily})


@app.get("/api/horizon")
def horizon():
    return a.clean(a.horizon_errors())


# Serve the built React app when present (Docker). Must stay AFTER the API routes.
_dist = a.ROOT / "frontend" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="ui")
