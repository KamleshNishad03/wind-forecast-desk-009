import { useEffect, useState } from "react";
import {
  ResponsiveContainer, ComposedChart, BarChart, Bar, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ReferenceLine,
} from "recharts";

const C = { forecast: "#138a8a", actual: "#0d2433", short: "#c8425a" };
const mw = (v) => (v == null ? "-" : `${Math.round(v).toLocaleString("en-GB")} MW`);
const hhmm = (iso) => iso.slice(11, 16);
const when = (iso) => `${iso.slice(8, 10)} Jan, ${hhmm(iso)} UTC`;

async function api(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `Request failed (${r.status})`);
  return r.json();
}

function Stat({ value, label }) {
  return <div className="stat"><b>{value}</b><span>{label}</span></div>;
}

export default function App() {
  const [meta, setMeta] = useState(null);
  const [day, setDay] = useState("2026-01-15");
  const [cutoff, setCutoff] = useState(9);
  const [dayData, setDayData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [horizon, setHorizon] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/meta").then((m) => { setMeta(m); setCutoff(m.default_cutoff_hour); }).catch((e) => setError(e.message));
    api("/api/horizon").then(setHorizon).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    setError("");
    api(`/api/day?date=${day}&cutoff_hour=${cutoff}`).then(setDayData).catch((e) => { setDayData(null); setError(e.message); });
    api(`/api/summary?cutoff_hour=${cutoff}`).then(setSummary).catch((e) => setError(e.message));
  }, [day, cutoff]);

  const m = dayData?.metrics;
  const all = summary?.overall;
  const points = (dayData?.points || []).map((p) => ({ ...p, label: hhmm(p.t) }));

  return (
    <div className="wrap">
      <h1>Wind forecast desk</h1>
      <p className="sub">
        See the wind forecast you actually had when you had to buy day-ahead power,
        and how far off these forecasts have been in January 2026. National GB wind, Elexon data.
      </p>

      {meta?.is_sample && (
        <div className="banner"><b>Sample data.</b> This is fake data for testing. Run <code>scripts/fetch_data.py</code> to load real Elexon data.</div>
      )}
      {error && <div className="banner err">{error}</div>}

      <div className="controls">
        <label>Delivery day
          <select value={day} onChange={(e) => setDay(e.target.value)}>
            {(meta?.delivery_days || [day]).map((d) => <option key={d}>{d}</option>)}
          </select>
        </label>
        <label>Buying decision made at (UTC, day before)
          <select value={cutoff} onChange={(e) => setCutoff(+e.target.value)}>
            {Array.from({ length: 24 }, (_, h) => <option key={h} value={h}>{String(h).padStart(2, "0")}:00</option>)}
          </select>
        </label>
      </div>

      {dayData && (
        <p className="brief">
          For delivery on <b>{day}</b>, the buyer decides at <b>{String(cutoff).padStart(2, "0")}:00 UTC the day before</b>.
          The latest forecast available then was published at <b>{when(dayData.latest_publish)}</b>.
          Expected wind that day averages <b>{mw(points.reduce((s, p) => s + p.forecast, 0) / points.length)}</b>.
        </p>
      )}

      <div className="stats">
        <Stat value={mw(m?.mae)} label={`This day: typical miss (${m?.mae_pct != null ? m.mae_pct.toFixed(0) : "-"}% of wind)`} />
        <Stat value={mw(m?.bias)} label="This day: average lean (positive = forecast too high)" />
        <Stat value={mw(all?.bias)} label={`January: average lean (${all?.bias_pct != null ? all.bias_pct.toFixed(0) : "-"}% of wind)`} />
        <Stat value={mw(all?.spread)} label="January: typical miss after removing the average lean" />
        <Stat value={mw(all?.p90_shortfall)} label="January: wind fell short of forecast by up to this in 9 of 10 half-hours" />
      </div>

      <div className="panel">
        <h2>Forecast vs what actually happened</h2>
        <p className="note">The forecast line uses only data published before the decision time.</p>
        <ResponsiveContainer width="100%" height={340}>
          <ComposedChart data={points}>
            <CartesianGrid stroke="#e3eaee" vertical={false} />
            <XAxis dataKey="label" interval={3} />
            <YAxis tickFormatter={(v) => `${v / 1000}k`} label={{ value: "MW", angle: -90, position: "insideLeft" }} />
            <Tooltip formatter={(v) => mw(v)} />
            <Legend />
            <Line dataKey="forecast" name="Forecast" stroke={C.forecast} strokeWidth={2.5} dot={false} />
            <Line dataKey="actual" name="Actual" stroke={C.actual} strokeWidth={2.5} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="grid2">
        <div className="panel">
          <h2>Typical miss by delivery day</h2>
          <p className="note">Mean absolute error (MW) for each day in January, at the chosen decision time.</p>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={summary?.daily || []}>
              <CartesianGrid stroke="#e3eaee" vertical={false} />
              <XAxis dataKey="date" tickFormatter={(d) => d.slice(8)} interval={1} />
              <YAxis />
              <Tooltip formatter={(v) => mw(v)} />
              <Bar dataKey="mae" name="MAE" fill={C.forecast} />
              {all && <ReferenceLine y={all.mae} stroke={C.short} strokeDasharray="4 4" />}
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="panel">
          <h2>Error by how far ahead the forecast was made</h2>
          <p className="note">All January forecasts. Bias is the steady gap. Spread is what is left after removing it.</p>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={horizon}>
              <CartesianGrid stroke="#e3eaee" vertical={false} />
              <XAxis dataKey="bucket" />
              <YAxis />
              <Tooltip formatter={(v) => mw(v)} />
              <Legend />
              <Bar dataKey="mae" name="MAE" fill={C.forecast} />
              <Bar dataKey="bias" name="Bias" fill={C.short} />
              <Bar dataKey="spread" name="Spread" fill="#8aa1b1" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="panel method">
        <h2>How this is calculated</h2>
        <ul>
          <li>Error = forecast minus actual. Positive means the forecast was too high, so you would have bought too little.</li>
          <li>For each half-hour, we use the newest forecast published at or before the decision time. Later forecasts are ignored.</li>
          <li>The buffer figure is the 90th percentile of the error. It is a measured past value, not a promise about the future.</li>
          <li>The forecast runs about {all?.bias_pct != null ? all.bias_pct.toFixed(0) : "-"}% above the actual series in January, all month. We have not shown whether this is a real forecast bias or a difference in what the two Elexon datasets measure.</li>
          <li>Forecasts are hourly and actuals are half-hourly, so only on-the-hour times are compared.</li>
          <li>Only times that have both a forecast and an actual are counted. All times are UTC.</li>
        </ul>
      </div>
    </div>
  );
}