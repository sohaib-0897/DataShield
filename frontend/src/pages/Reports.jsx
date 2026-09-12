import React, { useState, } from 'react';
import {
  FileText,
  Download,
  TrendingUp,
  Users,
  AlertTriangle,
  Share2,
  Clock,
} from 'lucide-react';
import { PageHeader, EmptyIntegrationState, DisabledActionButton, LoadingSpinner } from '../components/UIComponents';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { reportsAPI } from '../services/api';
import { useFetch } from '../services/useAPI';
import { getErrorMessage } from '../services/errorUtils';

const Reports = () => {
  const [selectedReport, setSelectedReport] = useState('summary');
  const [dateRange, setDateRange] = useState('7days');

  // Fetch all report data
  const { data: reportData = null, loading, error, refetch } = useFetch(async () => {
    const [summary, alerts, threats, users] = await Promise.all([
      reportsAPI.getSummary().then(res => res.data || res),
      reportsAPI.getAlertTrends().then(res => res.data || res),
      reportsAPI.getThreatAnalysis().then(res => res.data || res),
      reportsAPI.getUserReports().then(res => res.data || res),
    ]);
    return { summary, alerts, threats, users };
  });

  // Extract alert trends data with null safety
  const alertTrendsData = reportData && Array.isArray(reportData.alerts) ? reportData.alerts : [];

  // Extract threat data for pie chart with null safety
  const topThreatsData = reportData && Array.isArray(reportData.threats)
    ? reportData.threats.slice(0, 4).map((threat, idx) => ({
        name: threat.name,
        value: threat.count,
        fill: ['#3b82f6', '#8b5cf6', '#06b6d4', '#14b8a6'][idx],
      }))
    : [];

  // Extract department risk data with null safety
  const departmentRiskData = reportData?.users?.departmentRisk || [];

  const reports = [
    {
      id: 'summary',
      name: 'Executive Summary',
      description: 'High-level overview of security incidents and trends',
      icon: FileText,
    },
    {
      id: 'alerts',
      name: 'Alert Report',
      description: 'Detailed alert trends and statistics',
      icon: AlertTriangle,
    },
    {
      id: 'users',
      name: 'User Risk Report',
      description: 'User risk scores and behavioral analysis',
      icon: Users,
    },
    {
      id: 'threats',
      name: 'Threat Analysis',
      description: 'Classification and analysis of detected threats',
      icon: TrendingUp,
    },
  ];

  const renderReport = () => {
    // Show loading state during data fetch
    if (loading || !reportData) {
      return (
        <div className="card">
          <div className="card-body text-center text-gray-500">
            <p>Loading report data...</p>
          </div>
        </div>
      );
    }

    switch (selectedReport) {
      case 'summary':
        const summaryMetrics = reportData.summary || {};
        return (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="card">
                <div className="card-body">
                  <p className="text-sm text-gray-500 mb-2">Total Incidents</p>
                  <p className="text-4xl font-bold text-gray-900">{summaryMetrics.totalIncidents || 0}</p>
                  <p className="text-xs text-red-600 mt-2">{summaryMetrics.totalIncidentsChange || '↑ 0%'}</p>
                </div>
              </div>
              <div className="card">
                <div className="card-body">
                  <p className="text-sm text-gray-500 mb-2">Incidents Blocked</p>
                  <p className="text-4xl font-bold text-green-600">{summaryMetrics.incidentsBlocked || 0}</p>
                  <p className="text-xs text-gray-600 mt-2">{summaryMetrics.incidentsBlockedPercentage?.toFixed(1) || 0}% of total</p>
                </div>
              </div>
              <div className="card">
                <div className="card-body">
                  <p className="text-sm text-gray-500 mb-2">Investigated</p>
                  <p className="text-4xl font-bold text-blue-600">{summaryMetrics.investigated || 0}</p>
                  <p className="text-xs text-gray-600 mt-2">{summaryMetrics.investigatedPercentage?.toFixed(1) || 0}% of total</p>
                </div>
              </div>
              <div className="card">
                <div className="card-body">
                  <p className="text-sm text-gray-500 mb-2">Avg Response Time</p>
                  <p className="text-4xl font-bold text-purple-600">{summaryMetrics.avgResponseTime || '0h'}</p>
                  <p className="text-xs text-gray-600 mt-2">per incident</p>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold">Alert Trends</h3>
              </div>
              <div className="card-body">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={alertTrendsData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="date" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1f2937',
                        border: 'none',
                        borderRadius: '0.5rem',
                        color: '#fff',
                      }}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="alerts"
                      stroke="#3b82f6"
                      name="Total Alerts"
                      strokeWidth={2}
                    />
                    <Line
                      type="monotone"
                      dataKey="blocked"
                      stroke="#10b981"
                      name="Blocked"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        );

      case 'alerts':
        return (
          <div className="space-y-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-semibold">Threat Types</h3>
                </div>
                <div className="card-body flex items-center justify-center">
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={topThreatsData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value }) => `${name}: ${value}`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {topThreatsData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-semibold">Alert Summary</h3>
                </div>
                <div className="card-body space-y-4">
                  {reportData.threats && reportData.threats.slice(0, 4).map((threat, idx) => (
                    <div key={threat.name} className="flex justify-between items-center pb-3 border-b">
                      <span className="text-gray-700">{threat.name}</span>
                      <span className={`text-2xl font-bold ${['text-red-600', 'text-orange-600', 'text-yellow-600', 'text-green-600'][idx]}`}>
                        {threat.count}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold">Most Common Alert Types</h3>
              </div>
              <div className="card-body">
                <div className="space-y-4">
                  {reportData.threats && reportData.threats.map((threat, idx) => (
                    <div key={threat.name}>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm font-medium text-gray-700">
                          {threat.name}
                        </span>
                        <span className="text-sm font-bold text-gray-900">
                          {threat.count} ({threat.percentage}%)
                        </span>
                      </div>
                      <div className="bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${threat.percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        );

      case 'users':
        return (
          <div className="space-y-8">
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold">Risk by Department</h3>
              </div>
              <div className="card-body">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={departmentRiskData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="department" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1f2937',
                        border: 'none',
                        borderRadius: '0.5rem',
                        color: '#fff',
                      }}
                    />
                    <Legend />
                    <Bar dataKey="risk" fill="#ef4444" name="Avg Risk Score" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold">Top At-Risk Users</h3>
              </div>
              <div className="card-body">
                <div className="divide-y">
                  {reportData.users?.topUsers?.map((user, idx) => (
                    <div key={user.id} className="py-3">
                      <div className="flex justify-between items-center mb-2">
                        <p className="font-medium text-gray-900">{user.email}</p>
                        <span className="text-sm font-bold text-red-600">
                          {user.riskScore}/100
                        </span>
                      </div>
                      <div className="flex justify-between items-center mb-2">
                        <div className="flex-1 mr-4">
                          <div className="bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-red-600 h-2 rounded-full"
                              style={{ width: `${user.riskScore}%` }}
                            ></div>
                          </div>
                        </div>
                        <span className="text-xs text-gray-500">
                          {user.incidents} active alerts
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        );

      case 'threats':
        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold">Threat Categories</h3>
              </div>
              <div className="card-body flex items-center justify-center">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={topThreatsData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${value}%`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {topThreatsData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold">Threat Severity Matrix</h3>
              </div>
              <div className="card-body">
                <div className="space-y-3">
                  {reportData.threats && reportData.threats.map((threat, idx) => (
                    <div key={threat.name} className="pb-3 border-b">
                      <p className="font-medium text-gray-900 mb-2">{threat.name}</p>
                      <div className="flex items-center">
                        <div
                          className={`flex-1 h-4 rounded flex items-center justify-center text-xs text-white font-bold ${
                            threat.severity === 'critical' ? 'bg-red-600' :
                            threat.severity === 'high' ? 'bg-orange-500' :
                            threat.severity === 'medium' ? 'bg-yellow-500' :
                            'bg-green-500'
                          }`}
                          style={{ minWidth: `${Math.max(30, threat.percentage)}%` }}
                        >
                          {threat.percentage}%
                        </div>
                        <span className="ml-2 text-sm text-gray-600">
                          {threat.count} incidents
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="p-8">
      <PageHeader
        title="Reports"
        subtitle="Generate and export security reports"
      />

      <EmptyIntegrationState
        feature="Report Generation & Export"
        endpoint="GET /api/reports/summary, GET /api/reports/alerts, GET /api/reports/users, GET /api/reports/threats, POST /api/reports/export"
        description="Report generation, statistical aggregation, time-series analysis, and PDF/CSV export functionality"
        isMocked={true}
      />

      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <div className="card mb-6">
          <div className="card-body">
            <div className="bg-red-50 border-l-4 border-red-600 p-4">
              <p className="text-red-800 font-semibold">Error loading reports</p>
              <p className="text-red-700 text-sm mt-1">{getErrorMessage(error)}</p>
              <button
                onClick={refetch}
                className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      ) : (
        <>
          {/* Report Type Selection */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Select Report Type</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {reports.map(report => {
                const Icon = report.icon;
                return (
                  <button
                    key={report.id}
                    onClick={() => setSelectedReport(report.id)}
                    className={`card p-4 text-left transition-all border-l-4 ${
                      selectedReport === report.id
                        ? 'border-l-blue-600 bg-blue-50'
                        : 'border-l-gray-200 hover:border-l-blue-400'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <Icon
                        size={24}
                        className={
                          selectedReport === report.id
                            ? 'text-blue-600'
                            : 'text-gray-400'
                        }
                      />
                      <div>
                        <h4 className="font-semibold text-gray-900">{report.name}</h4>
                        <p className="text-xs text-gray-500 mt-1">
                          {report.description}
                        </p>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Date Range Selection */}
          <div className="card mb-8">
            <div className="card-body">
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    Date Range
                  </label>
                  <select
                    value={dateRange}
                    onChange={(e) => setDateRange(e.target.value)}
                    className="form-select"
                  >
                    <option value="7days">Last 7 Days</option>
                    <option value="30days">Last 30 Days</option>
                    <option value="90days">Last 90 Days</option>
                    <option value="1year">Last Year</option>
                  </select>
                </div>
                <div className="flex gap-2 items-end">
                  <DisabledActionButton
                    label="Export PDF"
                    reason="Backend endpoint needed: POST /api/reports/export"
                icon={Download}
              />
              <DisabledActionButton
                label="Share Report"
                reason="Backend sharing service not implemented"
                icon={Share2}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Report Content */}
      {renderReport()}

      {/* Report Footer */}
      <div className="mt-12 text-center text-gray-500 text-sm">
        <p className="flex items-center justify-center gap-2">
          <Clock size={16} />
          Report generated on {new Date().toLocaleString()}
        </p>
      </div>
        </>
      )}
    </div>
  );
};

export default Reports;
