import React, { useState, useMemo, } from 'react';
import { Link } from 'react-router-dom';
import {
  ChevronDown,
  AlertTriangle,
  FileText,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import {
  PageHeader,
  AlertBadge,
  StatusBadge,
  ChannelBadge,
  FilterBar,
  EmptyState,
  LoadingSpinner,
} from '../components/UIComponents';
import { alertsAPI } from '../services/api';
import { useFetch } from '../services/useAPI';
import { getErrorMessage } from '../services/errorUtils';

const Alerts = () => {
  // Fetch alerts from real backend API
  const { data: fetchedAlerts = null, loading, error, refetch } = useFetch(
    () => alertsAPI.getAll().then(res => res.data || res)
  );

  const [filters, setFilters] = useState({
    search: '',
    severity: 'all',
    channel: 'all',
    status: 'all',
  });

  const [sortConfig, setSortConfig] = useState({
    key: 'timestamp',
    direction: 'desc',
  });

  const handleFilterChange = (filterId, value) => {
    setFilters(prev => ({ ...prev, [filterId]: value }));
  };

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  // Filter and sort alerts from backend data
  const filteredAlerts = useMemo(() => {
    if (!fetchedAlerts || !Array.isArray(fetchedAlerts)) return [];

    let result = [...fetchedAlerts].filter(alert => {
      const matchesSearch =
        alert.user.toLowerCase().includes(filters.search.toLowerCase()) ||
        alert.activity.toLowerCase().includes(filters.search.toLowerCase()) ||
        alert.file.toLowerCase().includes(filters.search.toLowerCase());

      const matchesSeverity = filters.severity === 'all' || alert.severity === filters.severity;
      const matchesChannel = filters.channel === 'all' || alert.channel === filters.channel;
      const matchesStatus = filters.status === 'all' || alert.status === filters.status;

      return matchesSearch && matchesSeverity && matchesChannel && matchesStatus;
    });

    // Sort
    result.sort((a, b) => {
      const aValue = a[sortConfig.key];
      const bValue = b[sortConfig.key];

      if (typeof aValue === 'string') {
        return sortConfig.direction === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
    });

    return result;
  }, [fetchedAlerts, filters, sortConfig]);

  const filterOptions = [
    {
      id: 'search',
      label: 'Search',
      type: 'text',
      placeholder: 'User, activity, or file name...',
      value: filters.search,
    },
    {
      id: 'severity',
      label: 'Severity',
      type: 'select',
      options: [
        { value: 'all', label: 'All Severities' },
        { value: 'critical', label: 'Critical' },
        { value: 'high', label: 'High' },
        { value: 'medium', label: 'Medium' },
        { value: 'low', label: 'Low' },
      ],
      value: filters.severity,
    },
    {
      id: 'channel',
      label: 'Channel',
      type: 'select',
      options: [
        { value: 'all', label: 'All Channels' },
        { value: 'file', label: 'File System' },
        { value: 'usb', label: 'USB Device' },
        { value: 'cloud', label: 'Cloud Upload' },
        { value: 'http', label: 'HTTP' },
      ],
      value: filters.channel,
    },
    {
      id: 'status',
      label: 'Status',
      type: 'select',
      options: [
        { value: 'all', label: 'All Status' },
        { value: 'pending', label: 'Pending' },
        { value: 'investigating', label: 'Investigating' },
        { value: 'blocked', label: 'Blocked' },
        { value: 'allowed', label: 'Allowed' },
      ],
      value: filters.status,
    },
  ];

  const SortableHeader = ({ label, sortKey }) => (
    <th
      className="cursor-pointer hover:bg-gray-200 transition-colors"
      onClick={() => handleSort(sortKey)}
    >
      <div className="flex items-center gap-1">
        {label}
        {sortConfig.key === sortKey && (
          <ChevronDown
            size={16}
            className={`transform transition-transform ${
              sortConfig.direction === 'desc' ? '' : 'rotate-180'
            }`}
          />
        )}
      </div>
    </th>
  );

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <PageHeader
          title="Alerts"
          subtitle="Monitor and investigate security incidents"
        />
        <button
          onClick={refetch}
          className="btn btn-secondary"
          disabled={loading}
          title="Refresh alerts from backend"
        >
          <RefreshCw size={16} className={`mr-2 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* Show loading state */}
      {loading && <LoadingSpinner />}

      {/* Show error state */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 font-medium">Failed to load alerts</p>
          <p className="text-red-700 text-sm mt-1">{getErrorMessage(error)}</p>
          <button
            onClick={refetch}
            className="mt-2 btn btn-sm bg-red-600 text-white hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      )}

      {/* Show real data notice */}
      {!loading && !error && fetchedAlerts?.length > 0 && (
        <div className="mb-6 p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-green-800 text-sm font-medium">
            ✓ Connected to real backend • Showing {fetchedAlerts.length} alert{fetchedAlerts.length !== 1 ? 's' : ''}
          </p>
        </div>
      )}

      {/* Filters */}
      {!loading && <FilterBar filters={filterOptions} onFilterChange={handleFilterChange} />}

      {/* Alerts Table */}
      {!loading && (
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold">
              {filteredAlerts.length} Alert{filteredAlerts.length !== 1 ? 's' : ''}
            </h3>
          </div>

          {filteredAlerts.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="table w-full">
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Activity</th>
                    <th>File</th>
                    <SortableHeader label="Risk Score" sortKey="riskScore" />
                    <th>Severity</th>
                    <th>Channel</th>
                    <th>Status</th>
                    <SortableHeader label="Time" sortKey="timestamp" />
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAlerts.map(alert => (
                    <tr key={alert.id} className="hover:bg-blue-50">
                      <td className="font-medium text-gray-900">{alert.user}</td>
                      <td className="text-gray-700">{alert.activity}</td>
                      <td className="text-gray-600 truncate max-w-xs">{alert.file}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-full bg-gray-200 rounded-full h-2 max-w-xs">
                            <div
                              className={`h-2 rounded-full ${
                                alert.riskScore >= 80
                                  ? 'bg-red-600'
                                  : alert.riskScore >= 50
                                  ? 'bg-yellow-600'
                                  : 'bg-green-600'
                              }`}
                              style={{ width: `${alert.riskScore}%` }}
                            ></div>
                          </div>
                          <span className="font-semibold text-gray-900">{alert.riskScore}</span>
                        </div>
                      </td>
                      <td>
                        <AlertBadge severity={alert.severity} />
                      </td>
                      <td>
                        <ChannelBadge channel={alert.channel} />
                      </td>
                      <td>
                        <StatusBadge status={alert.status} />
                      </td>
                      <td className="text-gray-600 text-sm">
                        {new Date(alert.timestamp).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </td>
                      <td>
                        <Link
                          to={`/investigation/${alert.id}`}
                          className="inline-flex items-center gap-1 px-3 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
                        >
                          <FileText size={14} />
                          Investigate
                          <ArrowRight size={14} />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="card-body">
              <EmptyState
                icon={AlertTriangle}
                title="No alerts found"
                description={fetchedAlerts.length === 0 && !loading ? 'No alerts in the system' : 'Try adjusting your filters or search criteria'}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Alerts;
