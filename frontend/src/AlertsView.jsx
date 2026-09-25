import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { alerts } from './services/api';

const badgeTone = value => ({ CRITICAL: 'bg-red-100 text-red-800', HIGH: 'bg-orange-100 text-orange-800', MEDIUM: 'bg-amber-100 text-amber-800', LOW: 'bg-slate-100 text-slate-700', OPEN: 'bg-blue-100 text-blue-800', RESOLVED: 'bg-green-100 text-green-800', BLOCKED: 'bg-red-100 text-red-800' }[String(value).toUpperCase()] || 'bg-slate-100 text-slate-700');
const Badge = ({ children }) => <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${badgeTone(children)}`}>{String(children).toUpperCase()}</span>;

export default function AlertsView() {
  const [query, setQuery] = useState({ user: '', search: '', severity: '', channel: '', status: '', start: '', end: '', sort_by: 'created_at', descending: true, page: 1, size: 50 });
  const [data, setData] = useState(null), [loading, setLoading] = useState(true), [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    setLoading(true);
    const params = { ...query, start: query.start ? new Date(`${query.start}T00:00:00Z`).toISOString() : undefined,
      end: query.end ? new Date(new Date(`${query.end}T00:00:00Z`).getTime() + 86400000).toISOString() : undefined };
    alerts(params).then(response => { if (active) { setData(response.data); setError(''); setLoading(false); } })
      .catch(failure => { if (active) { setError(failure.response?.data?.detail || failure.message); setLoading(false); } });
    return () => { active = false; };
  }, [query]);
  const change = (name, value) => setQuery(current => ({ ...current, [name]: value, page: 1 }));
  const sort = name => setQuery(current => ({ ...current, sort_by: name, descending: current.sort_by === name ? !current.descending : true, page: 1 }));
  const rows = data?.items || [];
  const sortButton = (name, label) => <button type="button" className="underline underline-offset-2 focus-visible:outline focus-visible:outline-2" aria-label={`Sort by ${label.toLowerCase()}`} onClick={() => sort(name)}>{label}{query.sort_by === name ? (query.descending ? ' ↓' : ' ↑') : ''}</button>;
  return <div className="space-y-5"><header><h1 className="text-3xl font-bold">Alerts</h1><p className="text-slate-600">Filter and investigate database-backed risk alerts.</p></header>
    <section aria-label="Alert filters" className="bg-white border rounded-xl p-5 flex flex-wrap items-end gap-3">
      <label className="text-sm">Activity or resource<input aria-label="Search activity or resource" className="border rounded p-2 block w-full" placeholder="Activity or resource" value={query.search} onChange={event => change('search', event.target.value)}/></label>
      <label className="text-sm">User<input aria-label="Search user" className="border rounded p-2 block w-full" placeholder="Search user" value={query.user} onChange={event => change('user', event.target.value)}/></label>
      {[['severity', ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']], ['channel', ['FILE', 'USB', 'CLOUD', 'UPLOAD', 'NETWORK']], ['status', ['OPEN', 'INVESTIGATING', 'ALLOWED', 'BLOCKED', 'DISMISSED', 'RESOLVED']]].map(([key, options]) => <label key={key} className="text-sm capitalize">{key}<select aria-label={key} className="border rounded p-2 block w-full" value={query[key]} onChange={event => change(key, event.target.value)}><option value="">All {key}</option>{options.map(option => <option key={option} value={option}>{option}</option>)}</select></label>)}
      <label className="text-sm">From<input aria-label="From date" type="date" className="border rounded p-2 block" value={query.start} onChange={event => change('start', event.target.value)}/></label>
      <label className="text-sm">Until<input aria-label="Until date" type="date" className="border rounded p-2 block" value={query.end} onChange={event => change('end', event.target.value)}/></label>
    </section>
    {error && <p role="alert" className="bg-red-50 text-red-700 p-3 rounded">{String(error)}</p>}
    <section className="bg-white border rounded-xl p-5"><h2 className="font-bold mb-3">{data?.total ?? 0} alerts</h2>
      {loading ? <p role="status">Loading alerts…</p> : rows.length ? <div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="border-b text-left"><th scope="col" className="p-2">{sortButton('created_at', 'Time')}</th><th scope="col" className="p-2">{sortButton('user', 'User')}</th><th scope="col" className="p-2">Activity</th><th scope="col" className="p-2">Channel</th><th scope="col" className="p-2">{sortButton('risk_score', 'Risk')}</th><th scope="col" className="p-2">{sortButton('severity', 'Severity')}</th><th scope="col" className="p-2">Status</th><th scope="col" className="p-2">Action</th></tr></thead>
        <tbody>{rows.map(alert => <tr className="border-b" key={alert.id}><td className="p-2 whitespace-nowrap">{new Date(alert.timestamp).toLocaleString()}</td><td className="p-2">{alert.user}</td><td className="p-2">{alert.activity}</td><td className="p-2">{alert.channel.toUpperCase()}</td><td className="p-2 tabular-nums">{Number(alert.riskScore).toFixed(0)}/100</td><td className="p-2"><Badge>{alert.severity}</Badge></td><td className="p-2"><Badge>{alert.status}</Badge></td><td className="p-2"><Link className="text-cyan-800 underline" to={`/alerts/${alert.id}`}>Investigate</Link></td></tr>)}</tbody></table></div> : <p className="text-slate-500 py-6" role="status">No alerts match these filters</p>}
      <nav aria-label="Alert pages" className="flex gap-4 items-center mt-4"><button className="underline disabled:no-underline disabled:opacity-50" disabled={query.page === 1 || loading} onClick={() => setQuery(current => ({ ...current, page: current.page - 1 }))}>Previous</button><span>Page {query.page}</span><button className="underline disabled:no-underline disabled:opacity-50" disabled={query.page * query.size >= (data?.total || 0) || loading} onClick={() => setQuery(current => ({ ...current, page: current.page + 1 }))}>Next</button></nav>
    </section></div>;
}
