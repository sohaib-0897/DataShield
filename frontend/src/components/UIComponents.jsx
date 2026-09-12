import React from 'react';

export const StatCard = ({ icon: Icon, title, value, subtitle, color = 'blue' }) => {
  const colorClasses = {
    red: 'bg-red-50 text-red-600 border-red-200',
    orange: 'bg-orange-50 text-orange-600 border-orange-200',
    yellow: 'bg-yellow-50 text-yellow-600 border-yellow-200',
    green: 'bg-green-50 text-green-600 border-green-200',
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
  };

  const iconColors = {
    red: 'text-red-600 bg-red-100',
    orange: 'text-orange-600 bg-orange-100',
    yellow: 'text-yellow-600 bg-yellow-100',
    green: 'text-green-600 bg-green-100',
    blue: 'text-blue-600 bg-blue-100',
  };

  return (
    <div className={`card border-l-4 ${colorClasses[color]} border-l-${color}-600`}>
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
            <p className="text-3xl font-bold text-gray-900 mb-2">{value}</p>
            {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
          </div>
          <div className={`${iconColors[color]} p-3 rounded-lg`}>
            <Icon size={24} />
          </div>
        </div>
      </div>
    </div>
  );
};

export const AlertBadge = ({ severity }) => {
  const severityConfig = {
    critical: { bg: 'bg-red-100', text: 'text-red-800', label: 'Critical' },
    high: { bg: 'bg-orange-100', text: 'text-orange-800', label: 'High' },
    medium: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Medium' },
    low: { bg: 'bg-green-100', text: 'text-green-800', label: 'Low' },
  };

  const config = severityConfig[severity] || severityConfig.low;

  return (
    <span className={`badge ${config.bg} ${config.text}`}>{config.label}</span>
  );
};

export const StatusBadge = ({ status }) => {
  const statusConfig = {
    pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Pending' },
    investigating: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Investigating' },
    blocked: { bg: 'bg-red-100', text: 'text-red-800', label: 'Blocked' },
    allowed: { bg: 'bg-green-100', text: 'text-green-800', label: 'Allowed' },
    resolved: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Resolved' },
  };

  const config = statusConfig[status] || statusConfig.pending;

  return (
    <span className={`badge ${config.bg} ${config.text}`}>{config.label}</span>
  );
};

export const ChannelBadge = ({ channel }) => {
  const channelConfig = {
    file: { bg: 'bg-purple-100', text: 'text-purple-800', label: '📁 File' },
    usb: { bg: 'bg-indigo-100', text: 'text-indigo-800', label: '🔌 USB' },
    cloud: { bg: 'bg-cyan-100', text: 'text-cyan-800', label: '☁️ Cloud' },
    http: { bg: 'bg-sky-100', text: 'text-sky-800', label: '🌐 HTTP' },
  };

  const config = channelConfig[channel] || channelConfig.file;

  return (
    <span className={`badge ${config.bg} ${config.text}`}>{config.label}</span>
  );
};

export const PageHeader = ({ title, subtitle, action }) => {
  return (
    <div className="flex-between mb-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
        {subtitle && <p className="text-gray-600 mt-1">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
};

export const FilterBar = ({ filters, onFilterChange }) => {
  return (
    <div className="card mb-6">
      <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {filters.map((filter) => (
          <div key={filter.id}>
            <label className="text-sm font-medium text-gray-700 mb-1 block">
              {filter.label}
            </label>
            {filter.type === 'select' ? (
              <select
                className="form-select"
                value={filter.value}
                onChange={(e) => onFilterChange(filter.id, e.target.value)}
              >
                {filter.options?.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type={filter.type || 'text'}
                placeholder={filter.placeholder}
                className="form-input"
                value={filter.value}
                onChange={(e) => onFilterChange(filter.id, e.target.value)}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export const EmptyState = ({ icon: Icon, title, description, action }) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="bg-gray-100 p-4 rounded-full mb-4">
        <Icon size={32} className="text-gray-400" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-1">{title}</h3>
      <p className="text-gray-500 mb-6">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
};

export const LoadingSpinner = () => {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="w-8 h-8 border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin"></div>
    </div>
  );
};

export const ProgressBar = ({ value, max = 100, label, color = 'blue' }) => {
  const percentage = (value / max) * 100;
  const colorClass = `bg-${color}-600`;

  return (
    <div className="w-full">
      {label && <p className="text-sm font-medium text-gray-700 mb-1">{label}</p>}
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-300 ${colorClass}`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );
};

export const TimelineItem = ({ icon: Icon, title, description, timestamp, severity = 'info' }) => {
  const severityColors = {
    critical: 'bg-red-50 border-red-200 text-red-600',
    high: 'bg-orange-50 border-orange-200 text-orange-600',
    medium: 'bg-yellow-50 border-yellow-200 text-yellow-600',
    low: 'bg-green-50 border-green-200 text-green-600',
    info: 'bg-blue-50 border-blue-200 text-blue-600',
  };

  return (
    <div className={`card border-l-4 p-4 mb-4 ${severityColors[severity]}`}>
      <div className="flex gap-4">
        <div className="flex-shrink-0">
          <Icon size={20} />
        </div>
        <div className="flex-1">
          <h4 className="font-medium mb-1">{title}</h4>
          <p className="text-sm opacity-75 mb-2">{description}</p>
          <p className="text-xs opacity-60">{timestamp}</p>
        </div>
      </div>
    </div>
  );
};

export const NotImplementedBadge = ({ feature = 'Feature' }) => {
  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 border border-slate-300 text-slate-700">
      <div className="w-2 h-2 rounded-full bg-slate-400"></div>
      <span className="text-xs font-medium">Not Implemented: {feature}</span>
    </div>
  );
};

/**
 * EmptyIntegrationState Component
 *
 * Displays a user-friendly message for features waiting for backend support.
 * Use this to show what backend endpoints/services need to be implemented.
 *
 * @param {string} feature - Name of the missing feature (e.g., "Alert Fetching")
 * @param {string} endpoint - Backend endpoint needed (e.g., "GET /api/alerts")
 * @param {string} description - What capability is missing (e.g., "Real-time alert retrieval from backend")
 * @param {boolean} isMocked - If true, shows "Using mock data" message (default: true)
 */
export const EmptyIntegrationState = ({
  feature = 'Feature',
  endpoint = '/api/endpoint',
  description = 'Backend support not yet available',
  isMocked = true
}) => {
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-6 mb-6">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0">
          <div className="w-10 h-10 bg-slate-200 rounded-lg flex items-center justify-center">
            <span className="text-slate-500 font-semibold text-sm">⚙️</span>
          </div>
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h4 className="text-sm font-semibold text-slate-900">{feature}</h4>
            <NotImplementedBadge feature={feature} />
          </div>
          <p className="text-sm text-slate-600 mb-3">
            {description}
          </p>
          <div className="flex flex-col gap-2">
            <div className="text-xs bg-slate-100 px-3 py-2 rounded font-mono text-slate-700">
              Endpoint needed: <span className="font-semibold">{endpoint}</span>
            </div>
            {isMocked && (
              <p className="text-xs text-slate-500">
                💡 Currently using mock data for UI testing. This data will be replaced once the backend endpoint is ready.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * IntegrationPlaceholder Component
 *
 * Wraps a section to indicate it needs backend support.
 * Disables action buttons and shows clear context about what's missing.
 * Ready for future backend hookup - just remove the wrapper when connected.
 *
 * @param {string} feature - Name of the feature
 * @param {string} endpoint - Backend endpoint needed
 * @param {string} description - What's missing
 * @param {ReactNode} children - Content to display (usually disabled state of UI)
 * @param {boolean} showBanner - Show the integration state banner (default: true)
 */
export const IntegrationPlaceholder = ({
  feature,
  endpoint,
  description,
  children,
  showBanner = true
}) => {
  return (
    <div className="space-y-4">
      {showBanner && (
        <EmptyIntegrationState
          feature={feature}
          endpoint={endpoint}
          description={description}
          isMocked={true}
        />
      )}
      <div className="opacity-75 pointer-events-none select-none">
        {children}
      </div>
      <div className="text-center text-sm text-slate-500 py-4 border-2 border-dashed border-slate-200 rounded-lg">
        Content is disabled until backend support is available
      </div>
    </div>
  );
};

/**
 * DisabledActionButton Component
 *
 * A utility button component for features that require backend support.
 * Visually disabled with tooltip explaining what's missing.
 *
 * @param {string} label - Button label
 * @param {string} reason - Why it's disabled (e.g., "Backend not implemented")
 * @param {ReactNode} icon - Icon component to display
 */
export const DisabledActionButton = ({ label, reason = 'Not Implemented', icon: Icon }) => {
  return (
    <button
      disabled
      className="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed w-full group"
      title={reason}
    >
      {Icon && <Icon size={18} className="mr-2" />}
      {label}
      <span className="invisible group-hover:visible absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-900 text-white text-xs rounded whitespace-nowrap z-10">
        {reason}
      </span>
    </button>
  );
};
