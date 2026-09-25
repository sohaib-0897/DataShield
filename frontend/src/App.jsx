import React, { useEffect, useState } from 'react';
import { BrowserRouter, Link, Navigate, Route, Routes, useNavigate, useParams } from 'react-router-dom';
import * as api from './services/api';
import PolicyManager from './PolicyManager';
import UserActivityView from './UserActivityView';
import ReportsView from './ReportsView';
import AlertsView from './AlertsView';
import './styles/index.css';

const Card = ({ title, children }) => <section className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm min-w-0"><h2 className="font-bold text-slate-600 text-sm uppercase tracking-wide mb-4">{title}</h2>{children}</section>;
const Empty = ({ children = 'No data recorded' }) => <p className="text-slate-500 py-6" role="status">{children}</p>;
const ErrorBox = ({ error }) => error ? <p role="alert" className="p-3 rounded bg-red-50 text-red-700">{String(error.response?.data?.detail || error.message || error)}</p> : null;
const shownTime = value => value ? new Date(value).toLocaleString() : 'Not recorded';

function useLoad(loader, deps = []) {
  const [state, setState] = useState({ loading: true, data: null, error: null });
  useEffect(() => {
    let live = true;
    const run = () => loader().then(r => live && setState({ loading: false, data: r.data, error: null }))
      .catch(error => live && setState({ loading: false, data: null, error }));
    run();
    const timer = setInterval(run, 15000);
    return () => { live = false; clearInterval(timer); };
    // Loader identity is intentionally controlled by the caller's dependency list.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return state;
}

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const submit = async event => {
    event.preventDefault(); setError(null); setBusy(true);
    try {
      const response = await api.login(username, password);
      sessionStorage.setItem('datashield_token', response.data.access_token);
      onLogin(response.data); navigate('/');
    } catch (failure) { setError(failure); }
    finally { setBusy(false); }
  };
  return <main className="min-h-screen bg-slate-950 grid place-items-center p-4"><form onSubmit={submit} aria-labelledby="login-title" className="bg-white p-8 rounded-xl w-full max-w-sm space-y-4 shadow-xl">
    <h1 id="login-title" className="text-3xl font-bold">DataShield</h1><p className="text-slate-600">Analyst sign in</p><ErrorBox error={error}/>
    <label className="block text-sm font-medium" htmlFor="username">Username</label><input id="username" name="username" placeholder="Username" autoComplete="username" required className="border rounded p-3 w-full" value={username} onChange={event => setUsername(event.target.value)}/>
    <label className="block text-sm font-medium" htmlFor="password">Password</label><input id="password" name="password" placeholder="Password" autoComplete="current-password" type="password" required className="border rounded p-3 w-full" value={password} onChange={event => setPassword(event.target.value)}/>
    <button disabled={busy} className="bg-slate-900 text-white rounded p-3 w-full disabled:opacity-60">{busy ? 'Signing in…' : 'Sign in'}</button>
  </form></main>;
}

function Shell({ user, onLogout, children }) {
  const links = [['/', 'Overview'], ['/alerts', 'Alerts'], ['/users', 'User activity'], ['/reports', 'Reports'], ['/system', 'System status'], ['/policies', 'Policies'], ['/audit', 'Audit log']];
  return <div className="min-h-screen bg-slate-100 flex"><aside className="w-56 shrink-0 bg-slate-950 text-white p-5">
    <Link to="/" className="text-xl font-bold mb-7 block">DataShield</Link><nav aria-label="Main navigation" className="space-y-1">
      {links.filter(([path]) => !['/policies', '/audit'].includes(path) || user.role === 'ADMIN').map(([path, title]) => <Link key={path} to={path} className="block p-2 rounded hover:bg-slate-800 focus-visible:outline focus-visible:outline-2">{title}</Link>)}
    </nav><p className="text-xs mt-8">{user.username} · {user.role}</p><button className="text-sm mt-4 underline" onClick={onLogout}>Sign out</button>
  </aside><main className="flex-1 p-4 sm:p-6 lg:p-8 min-w-0 space-y-5">{children}</main></div>;
}

function Overview() {
  const x = useLoad(api.summary), s = useLoad(api.status), f = useLoad(() => api.alerts({ size: 5 }));
  const loading = x.loading || s.loading || f.loading;
  const stats = x.data ? [['Open alerts', x.data.by_status?.OPEN || 0], ['High and critical', (x.data.by_severity?.HIGH || 0) + (x.data.by_severity?.CRITICAL || 0)], ['Events today', x.data.events_today ?? 0], ['Risky users', x.data.risky_users?.length || 0]] : [['Open alerts', null], ['High and critical', null], ['Events today', null], ['Risky users', null]];
  return <>
    <header><h1 className="text-3xl font-bold">Security overview</h1><p className="text-slate-600">Database-backed recent activity (30 days) · refreshes every 15 seconds</p></header>
    <ErrorBox error={x.error || s.error || f.error}/>{loading && <p role="status">Loading overview…</p>}
    <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4">{stats.map(([title, value]) => <Card key={title} title={title}><b className="text-3xl tabular-nums">{value ?? '—'}</b></Card>)}</div>
    <div className="grid xl:grid-cols-2 gap-4"><Card title="Alert severity distribution">{Object.entries(x.data?.by_severity || {}).length ? Object.entries(x.data.by_severity).map(([key, value]) => <p key={key} className="flex justify-between border-b py-2"><span>{key}</span><b>{value}</b></p>) : <Empty/>}</Card>
      <Card title="Event volume · daily">{x.data?.event_daily?.length ? x.data.event_daily.slice(-10).map(row => <p key={row.date} className="flex justify-between border-b py-2"><span>{row.date}</span><b>{row.events} events</b></p>) : <Empty/>}</Card></div>
    <Card title="Recent alerts">{f.data?.items?.length ? <ul>{f.data.items.map(alert => <li key={alert.id} className="border-b py-3"><Link className="text-cyan-800 underline" to={`/alerts/${alert.id}`}>{alert.activity} · {alert.user}</Link><span className="block text-sm text-slate-600">{alert.severity.toUpperCase()} · {alert.riskScore}/100 · {shownTime(alert.timestamp)}</span></li>)}</ul> : <Empty>{f.loading ? 'Loading recent alerts…' : 'No alerts recorded'}</Empty>}</Card>
    <div className="grid xl:grid-cols-2 gap-4"><Card title="Highest observed user risk">{x.data?.risky_users?.length ? x.data.risky_users.slice(0, 5).map(user => <p key={user.user} className="flex justify-between border-b py-2">{user.user}<b>{user.risk}/100</b></p>) : <Empty/>}</Card>
      <Card title="System and behavior status"><p>System health: <b>{s.data?.database || (s.error ? 'Unavailable' : 'Loading')}</b></p><p>Behavior analysis source: <b>{s.data?.behavior_source || 'Unknown'}</b></p><p>Production trained model: <b>{s.data ? (s.data.production_model_available ? 'Available' : 'Not available') : 'Loading'}</b></p><p>Feature schema: {s.data?.feature_schema_version || '—'}</p><p>Endpoints online: {s.data?.endpoints?.filter(endpoint => endpoint.status === 'ONLINE').length ?? '—'} / {s.data?.endpoints?.length ?? '—'}</p>{s.data?.endpoints?.slice(0, 3).map(endpoint => <p className="text-sm text-slate-600" key={endpoint.machine_id}>{endpoint.hostname} · {endpoint.status}</p>)}</Card></div>
  </>;
}

function Investigation({ user }) {
  const { id } = useParams(), x = useLoad(() => api.alert(id), [id]);
  const [notes, setNotes] = useState(''), [error, setError] = useState(null), [result, setResult] = useState(null), [busy, setBusy] = useState(false);
  const action = async choice => {
    if (['ALLOW', 'BLOCK', 'DISMISS', 'RESOLVE'].includes(choice) && !window.confirm(`Confirm ${choice.toLowerCase()} decision for this alert?`)) return;
    setBusy(true);
    try { const response = await api.decide(id, choice, notes); setResult(response.data); setError(null); }
    catch (failure) { setError(failure); }
    finally { setBusy(false); }
  };
  const alert = x.data;
  return <><Link to="/alerts" className="text-cyan-800 underline">← Back to alerts</Link><header><h1 className="text-3xl font-bold">Alert investigation</h1><p className="text-slate-600">What happened, why it was flagged, and the recorded response.</p></header>
    <ErrorBox error={x.error || error}/>{x.loading && <p role="status">Loading investigation…</p>}{!x.loading && !alert && !x.error && <Empty>Alert not found</Empty>}
    {alert && <>
      <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-4"><Card title="Alert"><p className="font-semibold">{alert.title || alert.activity}</p><p>ID: <span className="break-all">{alert.id}</span></p><p>Severity: <b>{alert.severity.toUpperCase()}</b></p><p>Status: <b role="status">{(result?.status || alert.status).toUpperCase()}</b></p><p>Created: {shownTime(alert.timestamp)}</p></Card>
        <Card title="Identity"><p>User: <b>{alert.user}</b></p><p>Endpoint: {alert.endpoint || 'Unknown endpoint'}</p><p>Hostname: {alert.endpoint || 'Not reported'}</p><p>Machine ID: {alert.machine_id || 'Not reported'}</p></Card>
        <Card title="Event"><p>Channel: {alert.channel.toUpperCase()}</p><p>Type: {alert.event?.event_type || alert.activity}</p><p>Resource: <span className="break-all">{alert.resource || 'Not reported'}</span></p><p>Occurred: {shownTime(alert.event?.timestamp || alert.timestamp)}</p></Card>
        <Card title="Risk assessment"><b className="text-4xl tabular-nums">{Number(alert.riskScore).toFixed(0)}<span className="text-xl">/100</span></b><p>Severity: {alert.severity.toUpperCase()}</p><p>Scoring version: {alert.riskBreakdown.scoring_version}</p><p>Policy threshold: {alert.riskBreakdown.policy_threshold}</p></Card></div>
      <div className="grid xl:grid-cols-2 gap-4"><Card title="Why DataShield flagged this"><h3 className="font-semibold">Risk factor contributions</h3>{Object.entries(alert.riskBreakdown.contributions || {}).length ? Object.entries(alert.riskBreakdown.contributions).map(([name, value]) => <p key={name} className="flex justify-between border-b py-2"><span>{name.replaceAll('_', ' ')}</span><b>{Number(value).toFixed(1)}</b></p>) : <Empty/>}<p className="text-sm text-slate-600 mt-3">{alert.riskBreakdown.anomaly_reason}</p></Card>
        <Card title="Analysis sources"><h3 className="font-semibold">Sensitivity</h3><p>Classification: {alert.sensitivity?.label || 'Unclassified'} · score {Number(alert.sensitivity?.score || 0).toFixed(1)}/100</p><p>Source: <b>{alert.sensitivity?.source || alert.classifierSource}</b> · version {alert.sensitivity?.model_version || alert.riskBreakdown.rule_version || 'Not applicable'}</p><h3 className="font-semibold mt-4">Behavior</h3><p>Source: <b>{alert.anomalySource}</b>{alert.anomalySource === 'HEURISTIC' ? ' (deterministic history rule; not a trained model)' : ''}</p><p>Score: {Number(alert.riskBreakdown.components?.anomaly || 0).toFixed(1)}/100 · model version {alert.riskBreakdown.anomaly_model_version || 'Not applicable'}</p><p>Feature schema: {alert.riskBreakdown.feature_schema_version}</p></Card></div>
      <div className="grid xl:grid-cols-2 gap-4"><Card title="Evidence and sensitive detections">{alert.evidence?.length ? alert.evidence.map((evidence, index) => <pre key={index} className="text-xs whitespace-pre-wrap break-all bg-slate-50 p-3 mb-2 rounded">{evidence.type}: {JSON.stringify(evidence.value, null, 2)}</pre>) : <Empty>No supporting evidence was attached</Empty>}</Card>
        <Card title="Supporting event timeline">{alert.supporting_events?.length ? <ol className="border-l-2 border-slate-200 pl-4">{alert.supporting_events.map(event => <li key={event.id} className="relative border-b py-2"><b>{event.event_type}</b> · {event.channel} · {event.resource || 'No resource'}<span className="block text-sm text-slate-600">{shownTime(event.timestamp)}</span></li>)}</ol> : <Empty>No supporting events in the surrounding hour</Empty>}</Card></div>
      <Card title="Analyst response">{user.role === 'VIEWER' ? <p>Read only. An analyst or admin can record a decision.</p> : <><label htmlFor="decision-notes" className="block font-medium mb-1">Decision notes</label><textarea id="decision-notes" className="w-full border rounded p-2" rows="3" placeholder="Record investigation context" value={notes} onChange={event => setNotes(event.target.value)}/><div className="flex gap-2 flex-wrap mt-3">{['INVESTIGATE', 'ALLOW', 'BLOCK', 'DISMISS', 'RESOLVE'].map(choice => <button disabled={busy} className="bg-slate-900 text-white px-3 py-2 rounded disabled:opacity-50" key={choice} onClick={() => action(choice)}>{choice}</button>)}</div><p className="text-xs text-slate-600 mt-3">Block applies to cooperating upload clients; it cannot reverse completed file operations.</p></>}</Card>
      <Card title="Decision and audit history">{alert.decision_history?.length ? alert.decision_history.map((row, index) => <p key={index} className="border-b py-2">{shownTime(row.timestamp)} · {row.action} · {JSON.stringify(row.details)}</p>) : <Empty>No analyst action recorded yet</Empty>}</Card>
    </>}
  </>;
}

function System() {
  const x = useLoad(api.status);
  return <><header><h1 className="text-3xl font-bold">System status</h1><p className="text-slate-600">Service health and model availability are reported separately.</p></header><ErrorBox error={x.error}/>
    <div className="grid md:grid-cols-2 gap-4"><Card title="System health"><p>Release: {x.data?.version || '—'}</p><p>Database: <b>{x.data?.database || 'Unknown'}</b></p><p>Last event received: {shownTime(x.data?.last_event)}</p></Card>
      <Card title="Behavior analysis"><p>Active source: <b>{x.data?.behavior_source || 'Unknown'}</b></p><p>Production trained model: <b>{x.data?.production_model_available ? 'Available' : 'Not available'}</b></p><p>Artifact state: {x.data?.anomaly_model || 'Unknown'}</p><p>Feature schema: {x.data?.feature_schema_version || '—'}</p><p>{x.data?.model_error || 'When no production model is available, behavior uses the documented heuristic or insufficient-history state.'}</p></Card>
      <Card title="Sensitivity analysis"><p>Active source: <b>{x.data?.sensitivity?.source || 'RULE'}</b></p><p>Model version: {x.data?.sensitivity?.model_version || 'Not applicable'}</p><p>Configured model state: {x.data?.sensitivity?.configured_model || 'Not configured'}</p>{x.data?.sensitivity?.fallback_reason && <p role="status">Configured classifier unavailable ({x.data.sensitivity.fallback_reason}); rule classification remains active.</p>}<p>Rule source is reported per detection as RULE or DECLARED.</p></Card><Card title="Endpoints">{x.data?.endpoints?.length ? x.data.endpoints.map(endpoint => <p className="border-b py-2" key={endpoint.machine_id}>{endpoint.hostname} · {endpoint.status} · {shownTime(endpoint.last_seen)}</p>) : <Empty>No endpoints have checked in</Empty>}</Card></div></>;
}

function Audit() {
  const x = useLoad(api.audit);
  return <><h1 className="text-3xl font-bold">Audit log</h1><ErrorBox error={x.error}/><Card title="Recent actions">{x.loading ? <Empty>Loading audit records…</Empty> : x.data?.length ? <div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="border-b text-left"><th scope="col" className="p-2">Time</th><th scope="col" className="p-2">Action</th><th scope="col" className="p-2">Entity</th><th scope="col" className="p-2">Details</th></tr></thead><tbody>{x.data.map(row => <tr className="border-b" key={row.id}><td className="p-2 whitespace-nowrap">{shownTime(row.timestamp)}</td><td className="p-2">{row.action}</td><td className="p-2">{row.entity_type} {row.entity_id}</td><td className="p-2 break-all">{JSON.stringify(row.details)}</td></tr>)}</tbody></table></div> : <Empty>No audit records</Empty>}</Card></>;
}

export default function App() {
  const [user, setUser] = useState(null), [loading, setLoading] = useState(!!sessionStorage.getItem('datashield_token'));
  useEffect(() => {
    if (loading) api.me().then(response => setUser(response.data)).catch(() => { sessionStorage.removeItem('datashield_token'); setUser(null); }).finally(() => setLoading(false));
  }, [loading]);
  if (loading) return <p className="p-6" role="status">Loading session…</p>;
  return <BrowserRouter><Routes><Route path="/login" element={user ? <Navigate to="/" replace/> : <Login onLogin={setUser}/>}/><Route path="*" element={!user ? <Navigate to="/login" replace/> : <Shell user={user} onLogout={() => { sessionStorage.removeItem('datashield_token'); setUser(null); }}><Routes>
    <Route path="/" element={<Overview/>}/><Route path="/alerts" element={<AlertsView/>}/><Route path="/alerts/:id" element={<Investigation user={user}/>}/><Route path="/users" element={<UserActivityView/>}/><Route path="/reports" element={<ReportsView role={user.role}/>}/><Route path="/system" element={<System/>}/><Route path="/policies" element={user.role === 'ADMIN' ? <PolicyManager/> : <Navigate to="/" replace/>}/><Route path="/audit" element={user.role === 'ADMIN' ? <Audit/> : <Navigate to="/" replace/>}/><Route path="*" element={<Navigate to="/" replace/>}/>
  </Routes></Shell>}/></Routes></BrowserRouter>;
}
