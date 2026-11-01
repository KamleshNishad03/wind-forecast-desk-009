# Video script (max 10 min). Read it, then say it in your own words.

## Part 1: Client pitch (about 4 min). Talk about money and risk, not code.
1. (30s) Problem: "You buy day-ahead power one day early. Wind is uncertain. If wind is lower than forecast, you buy too little and pay expensive balancing prices."
2. (60s) Show the main chart: pick a day, show the forecast you had at decision time vs what happened. Say: "This uses only what you could have known at the time."
3. (60s) Show the four numbers: typical miss, lean (bias), 90% shortfall, RMSE. Say what each means in MW.
4. (45s) Show "Older forecasts are less accurate": "Forecasts get worse the further ahead they are made. Use the newest one you can."
5. (30s) Show the daily bar chart: "Some days are much harder than others."
6. (15s) Close: "Use the 90% shortfall number as a starting point for your safety buffer. This is a pilot: wind only, January only."

## Part 2: Tech lead review (about 5 min)
1. (45s) Architecture: React (Vite, Recharts) -> FastAPI -> CSV files made by `scripts/fetch_data.py`. One Docker image. Vercel runs the same FastAPI app as a function.
2. (90s) The key idea, in `backend/app/analysis.py` -> `select_latest`: many forecasts exist per target time. Keep only those published before the cutoff, then take the newest. Show test `test_no_forecast_published_after_cutoff_is_used`.
3. (60s) Metrics and sign convention (error = forecast - actual). Why bias and P90 matter more than MAE for a buyer.
4. (45s) Data: downloaded once, not live. Reason: speed, API limits, repeatable demo. Mention UTC and inner-join on startTime.
5. (30s) Limits, said honestly: fixed GB-wide wind only, cutoff is an assumption, past errors do not guarantee future errors, AI tools were used to build it.
6. (30s) How to run: `docker compose up --build`, tests with `pytest`.
