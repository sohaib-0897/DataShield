import React from 'react';
import {fireEvent, render, screen, waitFor} from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';
import * as api from './services/api';

jest.mock('./services/api', () => ({
  login: jest.fn(), me: jest.fn(), summary: jest.fn(), status: jest.fn(), alerts: jest.fn(),
}));

beforeEach(() => { sessionStorage.clear(); window.history.pushState({}, '', '/login'); });

test('login failure remains visible and does not expose a dashboard', async () => {
  api.login.mockRejectedValueOnce({response: {data: {detail: 'Invalid credentials'}}});
  render(<App/>);
  fireEvent.change(screen.getByPlaceholderText('Username'), {target: {value: 'analyst'}});
  fireEvent.change(screen.getByPlaceholderText('Password'), {target: {value: 'wrong'}});
  fireEvent.click(screen.getByText('Sign in'));
  expect(await screen.findByText('Invalid credentials')).toBeInTheDocument();
  expect(screen.queryByText('Security overview')).not.toBeInTheDocument();
});

test('successful login opens persisted analytics without sample numbers', async () => {
  api.login.mockResolvedValueOnce({data: {access_token: 'test-token', username: 'viewer', role: 'VIEWER'}});
  api.summary.mockResolvedValue({data: {alerts: 0, events: 0, by_severity: {}, by_status: {}, by_channel: {}}});
  api.status.mockResolvedValue({data: {anomaly_model: 'UNAVAILABLE', behavior_source: 'HEURISTIC', production_model_available: false, feature_schema_version: 'event-window-v2'}});
  api.alerts.mockResolvedValue({data: {items: [], total: 0}});
  render(<App/>);
  fireEvent.change(screen.getByPlaceholderText('Username'), {target: {value: 'viewer'}});
  fireEvent.change(screen.getByPlaceholderText('Password'), {target: {value: 'test-password'}});
  fireEvent.click(screen.getByText('Sign in'));
  await waitFor(() => expect(screen.getByText('Security overview')).toBeInTheDocument());
  expect(await screen.findByText(/Production trained model:/)).toHaveTextContent('Not available');
  expect(screen.getByText(/Behavior analysis source:/)).toHaveTextContent('HEURISTIC');
  expect(screen.queryByText('Policies')).not.toBeInTheDocument();
});

test('sign out removes the browser session and returns to sign in', async () => {
  api.login.mockResolvedValueOnce({data: {access_token: 'logout-token', username: 'viewer', role: 'VIEWER'}});
  api.summary.mockResolvedValue({data: {alerts: 0, events: 0, by_severity: {}, by_status: {}, by_channel: {}}});
  api.status.mockResolvedValue({data: {anomaly_model: 'UNAVAILABLE', behavior_source: 'HEURISTIC', feature_schema_version: 'event-window-v2'}});
  api.alerts.mockResolvedValue({data: {items: [], total: 0}});
  render(<App/>);
  fireEvent.change(screen.getByLabelText('Username'), {target: {value: 'viewer'}});
  fireEvent.change(screen.getByLabelText('Password'), {target: {value: 'test-password'}});
  fireEvent.click(screen.getByRole('button', {name: 'Sign in'}));
  await screen.findByRole('heading', {name: 'Security overview'});
  expect(sessionStorage.getItem('datashield_token')).toBe('logout-token');
  fireEvent.click(screen.getByRole('button', {name: 'Sign out'}));
  expect(await screen.findByRole('heading', {name: 'DataShield'})).toBeInTheDocument();
  expect(sessionStorage.getItem('datashield_token')).toBeNull();
});

test('alert filters request real server results and show empty state', async () => {
  sessionStorage.setItem('datashield_token', 'test-token');
  window.history.pushState({}, '', '/alerts');
  api.me.mockResolvedValue({data: {username: 'viewer', role: 'VIEWER'}});
  api.alerts.mockResolvedValue({data: {items: [], total: 0}});
  render(<App/>);
  await screen.findByText('No alerts match these filters');
  fireEvent.change(screen.getByLabelText('severity'), {target: {value: 'HIGH'}});
  await waitFor(() => expect(api.alerts).toHaveBeenLastCalledWith(expect.objectContaining({severity: 'HIGH'})));
  expect(screen.getByText('No alerts match these filters')).toBeInTheDocument();
});

test('risk column sorting requests the server order', async () => {
  sessionStorage.setItem('datashield_token', 'test-token');
  window.history.pushState({}, '', '/alerts');
  api.me.mockResolvedValue({data: {username: 'viewer', role: 'VIEWER'}});
  api.alerts.mockResolvedValue({data: {items: [{id: 'synthetic-1', timestamp: '2026-01-01T00:00:00Z', user: 'synthetic.user', activity: 'UPLOAD_ATTEMPT', channel: 'upload', riskScore: 70, severity: 'high', status: 'open'}], total: 1}});
  render(<App/>);
  fireEvent.click(await screen.findByRole('button', {name: 'Sort by risk'}));
  await waitFor(() => expect(api.alerts).toHaveBeenLastCalledWith(expect.objectContaining({sort_by: 'risk_score'})));
});

test('alert API errors are visible to the analyst', async () => {
  sessionStorage.setItem('datashield_token', 'test-token');
  window.history.pushState({}, '', '/alerts');
  api.me.mockResolvedValue({data: {username: 'analyst', role: 'ANALYST'}});
  api.alerts.mockRejectedValueOnce(new Error('Synthetic backend failure'));
  render(<App/>);
  expect(await screen.findByRole('alert')).toHaveTextContent('Synthetic backend failure');
});

test('viewer sees real report empty state without export control', async () => {
  sessionStorage.setItem('datashield_token', 'test-token');
  window.history.pushState({}, '', '/reports');
  api.me.mockResolvedValue({data: {username: 'viewer', role: 'VIEWER'}});
  api.summary.mockResolvedValue({data: {daily: [], event_daily: [], risk_daily: [], by_severity: {}, by_channel: {}, by_status: {}, decisions: {}, risky_users: [], alerts_with_sensitive_detections: 0}});
  render(<App/>);
  expect(await screen.findByText('Event volume')).toBeInTheDocument();
  expect(screen.queryByText('Export CSV')).not.toBeInTheDocument();
  expect(screen.getAllByText('No data').length).toBeGreaterThan(0);
});
