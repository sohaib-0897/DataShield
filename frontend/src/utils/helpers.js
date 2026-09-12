import { formatDistanceToNow, format } from 'date-fns';

export const dateUtils = {
  // Format timestamp to relative time (e.g., "2 hours ago")
  getRelativeTime: (timestamp) => {
    if (!timestamp) return 'Unknown';
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
    } catch {
      return 'Unknown';
    }
  },

  // Format timestamp to full date string
  getFullDate: (timestamp, formatStr = 'PPpp') => {
    if (!timestamp) return 'Unknown';
    try {
      return format(new Date(timestamp), formatStr);
    } catch {
      return 'Unknown';
    }
  },

  // Format timestamp to time only
  getTimeOnly: (timestamp) => {
    if (!timestamp) return 'Unknown';
    try {
      return format(new Date(timestamp), 'HH:mm:ss');
    } catch {
      return 'Unknown';
    }
  },

  // Format timestamp to date only
  getDateOnly: (timestamp) => {
    if (!timestamp) return 'Unknown';
    try {
      return format(new Date(timestamp), 'PP');
    } catch {
      return 'Unknown';
    }
  },
};

export const dataUtils = {
  // Format file size
  formatFileSize: (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  },

  // Truncate text with ellipsis
  truncateText: (text, maxLength = 50) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  },

  // Highlight search term in text
  highlightText: (text, searchTerm) => {
    if (!text || !searchTerm) return text;
    const regex = new RegExp(`(${searchTerm})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  },

  // Extract domain from email
  getDomainFromEmail: (email) => {
    if (!email) return '';
    return email.split('@')[1] || '';
  },

  // Extract username from email
  getUsernameFromEmail: (email) => {
    if (!email) return '';
    return email.split('@')[0] || '';
  },

  // Sort array by property
  sortBy: (array, property, ascending = true) => {
    return [...array].sort((a, b) => {
      if (a[property] < b[property]) return ascending ? -1 : 1;
      if (a[property] > b[property]) return ascending ? 1 : -1;
      return 0;
    });
  },
};

export const riskUtils = {
  // Get risk level label
  getRiskLevel: (score) => {
    if (score >= 80) return 'Critical';
    if (score >= 60) return 'High';
    if (score >= 40) return 'Medium';
    if (score >= 20) return 'Low';
    return 'Minimal';
  },

  // Get severity level
  getSeverity: (score) => {
    if (score >= 80) return 'critical';
    if (score >= 60) return 'high';
    if (score >= 40) return 'medium';
    return 'low';
  },

  // Get risk color
  getRiskColor: (score) => {
    if (score >= 80) return '#dc3545'; // Red
    if (score >= 60) return '#fd7e14'; // Orange
    if (score >= 40) return '#ffc107'; // Yellow
    return '#28a745'; // Green
  },

  // Get risk background color
  getRiskBgColor: (score) => {
    if (score >= 80) return '#ffe5e5'; // Red
    if (score >= 60) return '#fff3e0'; // Orange
    if (score >= 40) return '#fffbf0'; // Yellow
    return '#e8f5e9'; // Green
  },

  // Calculate risk trend
  calculateTrend: (currentScore, previousScore) => {
    const diff = currentScore - previousScore;
    return {
      value: Math.abs(diff),
      direction: diff > 0 ? 'up' : diff < 0 ? 'down' : 'stable',
      percentage: ((diff / previousScore) * 100).toFixed(1),
    };
  },
};

export const alertUtils = {
  // Determine alert priority based on multiple factors
  getPriority: (severity, riskScore, age) => {
    const severityScore = {
      critical: 100,
      high: 75,
      medium: 50,
      low: 25,
    }[severity] || 0;

    const riskFactor = riskScore || 0;
    const ageFactor = age < 60 ? 100 : age < 3600 ? 70 : 40; // Minutes

    const priority = (severityScore + riskFactor + ageFactor) / 3;
    return Math.round(priority);
  },

  // Get status badge configuration
  getStatusConfig: (status) => {
    const configs = {
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Pending' },
      investigating: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Investigating' },
      blocked: { bg: 'bg-red-100', text: 'text-red-800', label: 'Blocked' },
      allowed: { bg: 'bg-green-100', text: 'text-green-800', label: 'Allowed' },
      resolved: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Resolved' },
    };
    return configs[status] || configs.pending;
  },

  // Get channel icon and label
  getChannelInfo: (channel) => {
    const channels = {
      file: { icon: '📁', label: 'File System', color: '#7c3aed' }, // Purple
      usb: { icon: '🔌', label: 'USB Device', color: '#6366f1' }, // Indigo
      cloud: { icon: '☁️', label: 'Cloud Upload', color: '#06b6d4' }, // Cyan
      http: { icon: '🌐', label: 'HTTP Request', color: '#0ea5e9' }, // Sky blue
      email: { icon: '📧', label: 'Email', color: '#f97316' }, // Orange
    };
    return channels[channel] || channels.file;
  },
};

export const chartUtils = {
  // Format data for charts
  formatChartData: (data) => {
    return data.map(item => ({
      ...item,
      name: item.name || item.label,
      value: item.value || item.count,
    }));
  },

  // Generate color palette
  getColorPalette: (count = 5) => {
    const palette = [
      '#3b82f6', // Blue
      '#ef4444', // Red
      '#10b981', // Green
      '#f59e0b', // Amber
      '#8b5cf6', // Purple
      '#06b6d4', // Cyan
      '#ec4899', // Pink
      '#14b8a6', // Teal
    ];
    return palette.slice(0, count);
  },
};

export default {
  dateUtils,
  dataUtils,
  riskUtils,
  alertUtils,
  chartUtils,
};
