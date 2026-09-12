import React, { useState } from 'react';
import {
  Users,
  Zap,
} from 'lucide-react';
import {
  PageHeader,
  AlertBadge,
  FilterBar,
  EmptyState,
  LoadingSpinner,
} from '../components/UIComponents';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { usersAPI } from '../services/api';
import { useFetch } from '../services/useAPI';
import { getErrorMessage } from '../services/errorUtils';

const UserActivity = () => {
  const [selectedUser, setSelectedUser] = useState(null);
  const [filters, setFilters] = useState({
    search: '',
    riskLevel: 'all',
  });

  // Fetch user activity data from backend
  const { data: userActivityData = null, loading, error, refetch } = useFetch(
    () => usersAPI.getActivity().then(res => res.data || res)
  );

  const users = userActivityData?.users || [];
  const userRiskTrendData = userActivityData?.userRiskTrend || [];
  const anomalies = userActivityData?.anomalies || [];

  const filterOptions = [
    {
      id: 'search',
      label: 'Search User',
      type: 'text',
      placeholder: 'Enter email or name...',
      value: filters.search,
    },
    {
      id: 'riskLevel',
      label: 'Risk Level',
      type: 'select',
      options: [
        { value: 'all', label: 'All Users' },
        { value: 'high', label: 'High Risk (80+)' },
        { value: 'medium', label: 'Medium Risk (40-79)' },
        { value: 'low', label: 'Low Risk (<40)' },
      ],
      value: filters.riskLevel,
    },
  ];

  const handleFilterChange = (filterId, value) => {
    setFilters(prev => ({ ...prev, [filterId]: value }));
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.email.toLowerCase().includes(filters.search.toLowerCase());
    let matchesRisk = filters.riskLevel === 'all';

    if (filters.riskLevel === 'high') matchesRisk = user.riskScore >= 80;
    if (filters.riskLevel === 'medium')
      matchesRisk = user.riskScore >= 40 && user.riskScore < 80;
    if (filters.riskLevel === 'low') matchesRisk = user.riskScore < 40;

    return matchesSearch && matchesRisk;
  });

  const currentUser = selectedUser
    ? users.find(u => u.id === selectedUser)
    : null;

  if (loading) {
    return (
      <div className="p-8">
        <PageHeader
          title="User Activity"
          subtitle="Monitor user behavior and detect anomalies"
        />
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <PageHeader
          title="User Activity"
          subtitle="Monitor user behavior and detect anomalies"
        />
        <div className="card mb-6">
          <div className="card-body">
            <div className="bg-red-50 border-l-4 border-red-600 p-4">
              <p className="text-red-800 font-semibold">Error loading data</p>
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
      </div>
    );
  }

  return (
    <div className="p-8">
      <PageHeader
        title="User Activity"
        subtitle="Monitor user behavior and detect anomalies"
      />

      {/* Filters */}
      <FilterBar filters={filterOptions} onFilterChange={handleFilterChange} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* User List */}
        <div className="lg:col-span-1">
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold">Users</h3>
            </div>
            <div className="card-body p-0">
              <div className="divide-y max-h-96 overflow-y-auto">
                {filteredUsers.length > 0 ? (
                  filteredUsers.map(user => (
                    <div
                      key={user.id}
                      onClick={() => setSelectedUser(user.id)}
                      className={`p-4 cursor-pointer transition-colors ${
                        selectedUser === user.id
                          ? 'bg-blue-50 border-l-4 border-blue-600'
                          : 'hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex-between mb-2">
                        <p className="font-medium text-gray-900 truncate">
                          {user.email}
                        </p>
                        <span className="badge badge-danger text-xs">
                          {user.alertCount}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                user.riskScore >= 80
                                  ? 'bg-red-600'
                                  : user.riskScore >= 40
                                  ? 'bg-yellow-600'
                                  : 'bg-green-600'
                              }`}
                              style={{ width: `${user.riskScore}%` }}
                            ></div>
                          </div>
                        </div>
                        <span className="ml-2 font-bold text-gray-900">
                          {user.riskScore}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        Active {user.lastActivity}
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="p-8 text-center text-gray-500">
                    No users found
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* User Details */}
        <div className="lg:col-span-2">
          {currentUser ? (
            <>
              {/* User Header */}
              <div className="card mb-6">
                <div className="card-header">
                  <h3 className="text-lg font-semibold">{currentUser.email}</h3>
                </div>
                <div className="card-body">
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-gray-500 mb-1">Risk Score</p>
                      <p className="text-2xl font-bold text-red-600">
                        {currentUser.riskScore}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 mb-1">Active Alerts</p>
                      <p className="text-2xl font-bold text-orange-600">
                        {currentUser.alertCount}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 mb-1">Status</p>
                      <div className="mt-1">
                        <AlertBadge severity={currentUser.status.includes('high') ? 'critical' : 'high'} />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Activity Timeline */}
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-semibold">Weekly Activity</h3>
                </div>
                <div className="card-body">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={currentUser.activities}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="time" stroke="#9ca3af" />
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
                      <Bar dataKey="normal" fill="#10b981" name="Normal Activity" />
                      <Bar dataKey="suspicious" fill="#ef4444" name="Suspicious Activity" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          ) : (
            <div className="card">
              <div className="card-body">
                <EmptyState
                  icon={Users}
                  title="Select a user"
                  description="Choose a user from the list to view detailed activity"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Behavioral Anomalies */}
      <div className="card mt-8">
        <div className="card-header">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Zap size={20} className="text-yellow-600" />
            Detected Behavioral Anomalies
          </h3>
        </div>
        <div className="card-body">
          <div className="space-y-3">
            {anomalies.map(anomaly => (
              <div
                key={anomaly.id}
                className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-yellow-300 transition-colors"
              >
                <div className="flex-between">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{anomaly.user}</p>
                    <p className="text-sm text-gray-600 mt-1">{anomaly.anomaly}</p>
                  </div>
                  <div className="text-right">
                    <AlertBadge severity={anomaly.severity} />
                    <p className="text-xs text-gray-500 mt-2">{anomaly.timestamp}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Risk Trend Chart */}
      <div className="card mt-8">
        <div className="card-header">
          <h3 className="text-lg font-semibold">Risk Score Trends (5 Weeks)</h3>
        </div>
        <div className="card-body">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={userRiskTrendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="week" stroke="#9ca3af" />
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
                dataKey="john"
                stroke="#ef4444"
                name="John Doe"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="jane"
                stroke="#f59e0b"
                name="Jane Smith"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="bob"
                stroke="#10b981"
                name="Bob Wilson"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default UserActivity;
