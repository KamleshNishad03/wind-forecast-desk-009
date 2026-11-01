# Wind forecast desk

Web app for a UK utility's day-ahead power buyers. It shows (1) the latest wind forecast available at decision time and (2) how accurate these forecasts have been in January 2026. Data: Elexon BMRS, national wind only (`FUELHH` actuals, `WINDFOR` forecasts).

**Live app:** _add your Vercel link here_

**AI use:** This project was built with help from an AI assistant (Claude). All code was reviewed by the author.

## Files
- `backend/app/analysis.py`: forecast selection and error metrics (the important file)
- `backend/app/main.py`: FastAPI routes (`/api/meta`, `/api/day`, `/api/summary`, `/api/horizon`)
- `frontend/`: React app (Vite + Recharts)
- `scripts/fetch_data.py`: downloads real Elexon data into `data/`
- `scripts/make_sample_data.py`: makes FAKE data in `data/sample/` for offline testing
- `data/`: `actual.csv`, `forecast.csv` (real data once fetched)
- `tests/`: unit tests for the selection and metric logic
- `api/index.py`, `vercel.json`: Vercel deployment
- `Dockerfile`, `docker-compose.yml`: container setup
- `docs/VIDEO_SCRIPT.md`: talking points for the demo video

## Run it
1. Get real data (needs internet, once): `pip install -r requirements.txt && python scripts/fetch_data.py`
2. Start with Docker: `docker compose up --build`, then open http://localhost:8000
3. Or without Docker: `uvicorn backend.app.main:app --reload` and in `frontend/`: `npm install && npm run dev` (http://localhost:5173)
4. Tests: `pytest`

If `data/actual.csv` is missing, the app shows fake sample data with a yellow banner.

## Method and assumptions
- **Delivery days:** 2 Jan to 1 Feb 2026. Decisions are made on 1 to 31 Jan, one day before delivery.
- **Decision time:** default 09:00 UTC on the day before delivery. This is an assumption; it can be changed in the app.
- **Forecast used:** for each half-hour, the newest forecast with `publishTime` at or before the decision time.
- **Error:** forecast minus actual, in MW. Metrics: MAE, RMSE, bias, 90th percentile shortfall.
- **Horizon chart:** uses all forecasts for January targets, grouped by hours between publish and target.
- Only times that exist in both datasets are compared. All times are UTC.
- Limits: wind only, one month, no demand data, past error is not a guarantee.
