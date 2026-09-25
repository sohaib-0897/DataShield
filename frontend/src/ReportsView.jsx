import React, {useEffect, useState} from 'react';
import {Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis} from 'recharts';
import {summary, exportReport} from './services/api';

function Trend({title, rows, field, color}) {
  return <section className="bg-white border rounded-xl p-5">
    <h2 className="font-bold mb-3">{title}</h2>
    {rows?.length ? <ResponsiveContainer width="100%" height={260}>
      <BarChart data={rows}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="date"/><YAxis/><Tooltip/><Bar dataKey={field} fill={color}/></BarChart>
    </ResponsiveContainer> : <p className="text-slate-500 py-8">No data</p>}
  </section>;
}

function Breakdown({title, values}) {
  return <section className="bg-white border rounded-xl p-5">
    <h2 className="font-bold mb-3">{title}</h2>
    {Object.entries(values || {}).length ? Object.entries(values).map(([name, count]) =>
      <p key={name} className="flex justify-between border-b py-2">{name}<b>{count}</b></p>
    ) : <p className="text-slate-500">No data</p>}
  </section>;
}

export default function ReportsView({role}) {
  const [days, setDays] = useState(30);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    setLoading(true);
    summary(days).then(response => { if (active) { setData(response.data); setError(''); } })
      .catch(err => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [days]);

  const download = async () => {
    try {
      const response = await exportReport(days);
      const url = URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'datashield-alerts.csv';
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) { setError(err.response?.data?.detail || err.message); }
  };

  return <div className="space-y-5">
    <h1 className="text-3xl font-bold">Reports</h1>
    <div className="flex gap-3 items-center">
      <label>Time range <select className="border p-2 rounded ml-2" value={days} onChange={event => setDays(Number(event.target.value))}>
        <option value={7}>7 days</option><option value={30}>30 days</option><option value={90}>90 days</option><option value={365}>365 days</option>
      </select></label>
      {role !== 'VIEWER' && <button className="bg-slate-900 text-white rounded px-3 py-2" onClick={download}>Export CSV</button>}
    </div>
    {error && <p role="alert" className="text-red-700 bg-red-50 p-3">{error}</p>}
    {loading && <p className="text-slate-500" role="status">Loading report…</p>}
    <div className="grid lg:grid-cols-2 gap-4">
      <Trend title="Alerts over time" rows={data?.daily} field="alerts" color="#0891b2"/>
      <Trend title="Event volume" rows={data?.event_daily} field="events" color="#334155"/>
      <Trend title="Average assessed risk" rows={data?.risk_daily} field="average_risk" color="#b45309"/>
      <Breakdown title="Severity distribution" values={data?.by_severity}/>
      <Breakdown title="Channel breakdown" values={data?.by_channel}/>
      <Breakdown title="Alert status" values={data?.by_status}/>
      <Breakdown title="Analyst decisions" values={data?.decisions}/>
      <section className="bg-white border rounded-xl p-5">
        <h2 className="font-bold mb-3">Sensitive detections</h2>
        <p className="text-2xl font-bold">{data?.alerts_with_sensitive_detections ?? '—'}</p>
        <p className="text-sm text-slate-500">Alerts with at least one rule detection</p>
      </section>
    </div>
    <section className="bg-white border rounded-xl p-5">
      <h2 className="font-bold mb-3">Highest observed user risk</h2>
      {data?.risky_users?.length ? data.risky_users.map(user =>
        <p key={user.user} className="flex justify-between border-b py-2">{user.user}<b>{user.risk}/100</b></p>
      ) : <p className="text-slate-500">No data</p>}
    </section>
  </div>;
}
