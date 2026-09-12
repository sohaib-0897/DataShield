import React, { useState, } from 'react';
import {
  AlertTriangle,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import { StatCard, PageHeader, LoadingSpinner, NotImplementedBadge, IntegrationPlaceholder } from '../components/UIComponents';
import { Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { alertsAPI } from '../services/api';
import { useFetch } from '../services/useAPI';
import { getErrorMessage } from '../services/errorUtils';

const Dashboard = () => {
  const [refreshing, setRefreshing] = useState(false);

  // Fetch real alerts from backend
  const { data: allAlerts = [], loading, error: alertsError, refetch } = useFetch(
    () => alertsAPI.getAll().then(res => res.data || res)
  );

  // Calculate metrics from real data
  const calculateMetrics = () => {
    if (!allAlerts || allAlerts.length === 0) {
      return {
        totalAlerts: 0,
        severityDistribution: [],
        recentAlerts: [],
      };
    }

    // Total alerts
    const totalAlerts = allAlerts.length;

    // Severity distribution
    const severityCounts = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
    };

    allAlerts.forEach(alert => {
      const severity = (alert.severity || 'medium').toLowerCase();
      if (severity in severityCounts) {
        severityCounts[severity]++;
      }
    });

    const severityDistribution = [
      { name: 'Critical', value: severityCounts.critical, fill: '#dc3545' },
      { name: 'High', value: severityCounts.high, fill: '#fd7e14' },
      { name: 'Medium', value: severityCounts.medium, fill: '#ffc107' },
      { name: 'Low', value: severityCounts.low, fill: '#28a745' },
    ].filter(item => item.value > 0);

    // Recent alerts (first 3)
    const recentAlerts = allAlerts.slice(0, 3);

    return {
      totalAlerts,
      severityDistribution,
      recentAlerts,
    };
  };

  const metrics = calculateMetrics();

  const handleRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <PageHeader
          title="Dashboard"
          subtitle="Real-time monitoring and alert overview"
        />
        <button
          onClick={handleRefresh}
          className={`btn btn-secondary ${refreshing ? 'opacity-50 cursor-not-allowed' : ''}`}
          disabled={refreshing}
        >
          <RefreshCw size={16} className={`mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Connection Status Banner */}
      {alertsError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <AlertCircle size={20} className="text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-900">Backend Connection Error</h3>
              <p className="text-red-700 text-sm mt-1">{getErrorMessage(alertsError)}</p>
              <button
                onClick={handleRefresh}
                className="mt-2 px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Success Connection Banner */}
      {!alertsError && allAlerts.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-6">
          <p className="text-sm text-green-700">
            ✓ <span className="font-semibold">Connected to real backend</span> • {metrics.totalAlerts} alerts loaded
          </p>
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid-responsive mb-8">
        <StatCard
          icon={AlertTriangle}
          title="Total Alerts"
          value={metrics.totalAlerts}
          subtitle="All severity levels"
          color="red"
          isReal={true}
        />
        <div className="card">
          <div className="card-body">
            <IntegrationPlaceholder
              feature="High Risk Users"
              endpoint="GET /dashboard/users/high-risk"
              description="Requires user-level risk aggregation and time-series tracking"
              showBanner={true}
            >
              <div className="text-center py-4">
                <div className="text-2xl font-bold text-gray-400">N/A</div>
                <p className="text-xs text-gray-500 mt-1">Not Implemented</p>
              </div>
            </IntegrationPlaceholder>
          </div>
        </div>
        <div className="card">
          <div className="card-body">
            <IntegrationPlaceholder
              feature="Recent Activities"
              endpoint="GET /dashboard/analytics/activity-count"
              description="Requires hourly/daily activity aggregation and event tracking"
              showBanner={true}
            >
              <div className="text-center py-4">
                <div className="text-2xl font-bold text-gray-400">N/A</div>
                <p className="text-xs text-gray-500 mt-1">Not Implemented</p>
              </div>
            </IntegrationPlaceholder>
          </div>
        </div>
        <div className="card">
          <div className="card-body">
            <IntegrationPlaceholder
              feature="Blocked Attempts"
              endpoint="GET /dashboard/analytics/blocked-count"
              description="Requires decision tracking and historical audit log"
              showBanner={true}
            >
              <div className="text-center py-4">
                <div className="text-2xl font-bold text-gray-400">N/A</div>
                <p className="text-xs text-gray-500 mt-1">Not Implemented</p>
              </div>
            </IntegrationPlaceholder>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Activity Timeline - NOT IMPLEMENTED */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              Activity Timeline
              <NotImplementedBadge />
            </h3>
            <p className="text-sm text-gray-500 mt-1">Events and blocked attempts over 24 hours</p>
          </div>
          <div className="card-body">
            <IntegrationPlaceholder
              feature="Activity Timeline"
              endpoint="GET /dashboard/analytics/timeline"
              description="Requires hourly event aggregation with breakdown by event type and status"
              showBanner={true}
            >
              <div className="flex items-center justify-center h-72 bg-gray-50 rounded border border-dashed border-gray-300">
                <p className="text-gray-500 text-center">
                  <AlertCircle size={20} className="mx-auto mb-2 opacity-50" />
                  Timeline data not available from backend
                </p>
              </div>
            </IntegrationPlaceholder>
          </div>
        </div>

        {/* Alert Severity Distribution - REAL DATA */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Alert Severity</h3>
            <p className="text-sm text-gray-500 mt-1">Distribution across severity levels</p>
          </div>
          <div className="card-body flex items-center justify-center">
            {metrics.severityDistribution && metrics.severityDistribution.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={metrics.severityDistribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {metrics.severityDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1f2937',
                      border: 'none',
                      borderRadius: '0.5rem',
                      color: '#fff',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <p>No alerts to display</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* User Risk Score Distribution - NOT IMPLEMENTED */}
      <div className="card mb-8">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            User Risk Score Distribution
            <NotImplementedBadge />
          </h3>
          <p className="text-sm text-gray-500 mt-1">Number of users by risk score range</p>
        </div>
        <div className="card-body">
          <IntegrationPlaceholder
            feature="User Risk Distribution"
            endpoint="GET /dashboard/analytics/risk-distribution"
            description="Requires user-level risk score aggregation and bucketing by score ranges"
            showBanner={true}
          >
            <div className="flex items-center justify-center h-80 bg-gray-50 rounded border border-dashed border-gray-300">
              <p className="text-gray-500 text-center">
                <AlertCircle size={20} className="mx-auto mb-2 opacity-50" />
                Risk distribution data not available from backend
              </p>
            </div>
          </IntegrationPlaceholder>
        </div>
      </div>

      {/* Recent Alerts Preview - REAL DATA */}
      <div className="card">
        <div className="card-header flex-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Recent Alerts</h3>
            <p className="text-sm text-gray-500 mt-1">Latest suspicious activities detected</p>
          </div>
          <a href="/alerts" className="text-blue-600 hover:text-blue-700 font-medium text-sm">
            View All →
          </a>
        </div>
        <div className="card-body">
          {metrics.recentAlerts && metrics.recentAlerts.length > 0 ? (
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {metrics.recentAlerts.map((alert, idx) => (
                <div
                  key={idx}
                  className="flex-between p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all cursor-pointer"
                  onClick={() => window.location.href = `/investigation/${alert.id}`}
                >
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{alert.activity || 'Alert Activity'}</p>
                    <p className="text-sm text-gray-500 mt-1">User: {alert.user || 'Unknown'}</p>
                    <p className="text-xs text-gray-400 mt-1">File: {alert.file || 'N/A'}</p>
                  </div>
                  <div className="text-right">
                    <span
                      className={`badge ${
                        alert.severity === 'critical'
                          ? 'badge-danger'
                          : alert.severity === 'high'
                          ? 'badge-warning'
                          : 'badge-info'
                      }`}
                    >
                      {alert.severity || 'unknown'}
                    </span>
                    <p className="text-xs text-gray-500 mt-2">
                      {alert.timestamp
                        ? new Date(alert.timestamp).toLocaleString()
                        : 'N/A'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <AlertCircle size={32} className="mx-auto mb-2 opacity-50" />
              <p>No alerts currently in the system</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
