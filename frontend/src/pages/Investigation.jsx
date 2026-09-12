import React, { useState, } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Clock,
  AlertTriangle,
  Eye,
  CheckCircle,
  XCircle,
  MessageSquare,
  AlertCircle,
} from 'lucide-react';
import {
  AlertBadge,
  StatusBadge,
  ChannelBadge,
  NotImplementedBadge,
  IntegrationPlaceholder,
} from '../components/UIComponents';
import { fileActivityAPI, alertsAPI } from '../services/api';
import { getErrorMessage } from '../services/errorUtils';
import { useFetch } from '../services/useAPI';

const Investigation = () => {
  const { alertId } = useParams();
  const navigate = useNavigate();
  const [notes, setNotes] = useState('');
  const [decision, setDecision] = useState(null);
  const [submittingDecision, setSubmittingDecision] = useState(false);
  const [decisionError, setDecisionError] = useState(null);
  const [decisionSuccess, setDecisionSuccess] = useState(false);

  // Fetch all alerts from backend and find the matching one
  const { data: allAlerts = [], loading, error: alertsError } = useFetch(
    () => alertsAPI.getAll().then(res => res.data || res)
  );

  // Ensure allAlerts is always an array (defensive guard for null/undefined from API or useFetch)
  const safeAlerts = Array.isArray(allAlerts) ? allAlerts : [];

  // Find the current alert from the fetched data
  const alert = safeAlerts.find(a => String(a.id) === String(alertId));
  const alertNotFound = !loading && safeAlerts.length > 0 && !alert;

  const handleDecision = async (action) => {
    setSubmittingDecision(true);
    setDecisionError(null);
    setDecisionSuccess(false);

    try {
      await fileActivityAPI.submitDecision(alertId, action);
      setDecision(action);
      setDecisionSuccess(true);
      // Show success message for 2 seconds, then return to alerts
      setTimeout(() => {
        navigate('/alerts');
      }, 2000);
    } catch (error) {
      console.error('Error submitting decision:', error);
      setDecisionError(getErrorMessage(error) || 'Failed to submit decision. Please try again.');
    } finally {
      setSubmittingDecision(false);
    }
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <button
          onClick={() => navigate('/alerts')}
          className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
        >
          <ArrowLeft size={24} />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Alert Investigation</h1>
          <p className="text-gray-600 mt-1">Alert ID: {alertId}</p>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
          <div className="animate-spin inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mb-4"></div>
          <p className="text-blue-700 font-medium">Loading alert details...</p>
        </div>
      )}

      {/* Error State */}
      {alertsError && !loading && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-8">
          <div className="flex items-start gap-3">
            <AlertCircle size={24} className="text-red-600 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold text-red-900">Failed to Load Alert</h3>
              <p className="text-red-700 text-sm mt-1">{getErrorMessage(alertsError)}</p>
              <button
                onClick={() => window.location.reload()}
                className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Alert Not Found */}
      {alertNotFound && !loading && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-8">
          <div className="flex items-start gap-3">
            <AlertCircle size={24} className="text-yellow-600 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold text-yellow-900">Alert Not Found</h3>
              <p className="text-yellow-700 text-sm mt-1">
                Alert ID {alertId} could not be found in the system.
              </p>
              <button
                onClick={() => navigate('/alerts')}
                className="mt-3 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
              >
                Return to Alerts
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content - Show only when alert is loaded */}
      {alert && !loading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Alert Details */}
          <div className="lg:col-span-1">
          {/* Summary Card */}
          <div className="card mb-6">
            <div className="card-header">
              <h3 className="text-lg font-semibold">Alert Summary</h3>
            </div>
            <div className="card-body space-y-4">
              <div>
                <p className="text-sm text-gray-500 mb-1">Activity</p>
                <p className="font-medium text-gray-900">{alert.activity}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-1">File</p>
                <p className="font-medium text-gray-900 truncate">{alert.file}</p>
                <p className="text-xs text-gray-500">{alert.fileSize}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-2">Severity</p>
                <AlertBadge severity={alert.severity} />
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-2">Status</p>
                <StatusBadge status={alert.status} />
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-2">Channel</p>
                <ChannelBadge channel={alert.channel} />
              </div>
            </div>
          </div>

          {/* Risk Score Card - NOT IMPLEMENTED */}
          <div className="card mb-6">
            <div className="card-header">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                Risk Score Breakdown
                <NotImplementedBadge />
              </h3>
            </div>
            <div className="card-body">
              <IntegrationPlaceholder
                feature="Risk Score Analysis"
                endpoint="GET /alerts/<id>/risk-breakdown"
                description="Detailed breakdown of behavioral anomaly, sensitivity matching, and exfiltration pattern scores"
                showBanner={true}
              >
                <div className="text-center py-8">
                  <div className="text-4xl font-bold text-gray-400 mb-2">{alert.riskScore || 'N/A'}</div>
                  <p className="text-gray-500">{alert.severity || 'unknown'}</p>
                </div>
              </IntegrationPlaceholder>
            </div>
          </div>

          {/* User Info - NOT IMPLEMENTED for history */}
          <div className="card mb-6">
            <div className="card-header">
              <h3 className="text-lg font-semibold">User Information</h3>
            </div>
            <div className="card-body space-y-3">
              <div>
                <p className="text-sm text-gray-500">Email</p>
                <p className="font-medium text-gray-900">{alert.user || 'Unknown'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-2">User Risk Trend</p>
                <IntegrationPlaceholder
                  feature="User Risk History"
                  endpoint="GET /alerts/<id>/user-history"
                  description="Trend data for user's risk scores over time"
                  showBanner={false}
                >
                  <div className="flex items-center justify-center p-4 bg-gray-50 rounded border border-dashed border-gray-300">
                    <p className="text-gray-500 text-sm">Risk history not available</p>
                  </div>
                </IntegrationPlaceholder>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold">Actions</h3>
            </div>
            <div className="card-body space-y-3">
              {decisionError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-sm text-red-700">
                    <span className="font-semibold">Error:</span> {decisionError}
                  </p>
                </div>
              )}
              {decisionSuccess && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                  <p className="text-sm text-green-700">
                    <span className="font-semibold">Success!</span> Decision recorded. Returning to alerts...
                  </p>
                </div>
              )}

              {/* For Upload Alerts - Show Allow/Block */}
              {alert.type === 'upload' && (
                <>
                  <button
                    onClick={() => handleDecision('block')}
                    className={`btn w-full bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed ${
                      decision === 'block' ? '!bg-red-800' : ''
                    }`}
                    disabled={submittingDecision}
                  >
                    <XCircle size={18} className="mr-2" />
                    {submittingDecision ? 'Processing...' : 'Block Upload'}
                  </button>
                  <button
                    onClick={() => handleDecision('allow')}
                    className={`btn w-full bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed ${
                      decision === 'allow' ? '!bg-green-800' : ''
                    }`}
                    disabled={submittingDecision}
                  >
                    <CheckCircle size={18} className="mr-2" />
                    {submittingDecision ? 'Processing...' : 'Allow Upload'}
                  </button>
                </>
              )}

              {/* For File Activity Alerts - Show Flag/Approve */}
              {alert.type === 'file_activity' && (
                <>
                  <button
                    onClick={() => handleDecision('block')}
                    className={`btn w-full bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed ${
                      decision === 'block' ? '!bg-red-800' : ''
                    }`}
                    disabled={submittingDecision}
                  >
                    <AlertTriangle size={18} className="mr-2" />
                    {submittingDecision ? 'Processing...' : 'Flag as Suspicious'}
                  </button>
                  <button
                    onClick={() => handleDecision('allow')}
                    className={`btn w-full bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed ${
                      decision === 'allow' ? '!bg-green-800' : ''
                    }`}
                    disabled={submittingDecision}
                  >
                    <CheckCircle size={18} className="mr-2" />
                    {submittingDecision ? 'Processing...' : 'Approve Activity'}
                  </button>
                </>
              )}

              <button className="btn w-full btn-secondary">
                <MessageSquare size={18} className="mr-2" />
                Alert User
              </button>
            </div>
          </div>
        </div>

        {/* Right Column - Timeline and Evidence */}
        <div className="lg:col-span-2">
          {/* Timestamp and Metadata */}
          <div className="card mb-6">
            <div className="card-header">
              <h3 className="text-lg font-semibold">Incident Details</h3>
            </div>
            <div className="card-body grid grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-gray-500 mb-1">Timestamp</p>
                <div className="flex items-center gap-2">
                  <Clock size={18} className="text-blue-600" />
                  <p className="font-medium">
                    {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : 'Unknown'}
                  </p>
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-1">Alert Type</p>
                <p className="font-medium">
                  <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-lg text-sm font-semibold">
                    {alert.type === 'upload' ? 'File Upload' : 'File Activity'}
                  </span>
                </p>
              </div>
            </div>
          </div>

          {/* Sensitive Data Matches */}
          <div className="card mb-6">
            <div className="card-header">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <AlertTriangle size={20} className="text-red-600" />
                Detected Sensitive Data
              </h3>
            </div>
            <div className="card-body">
              {alert.sensitiveMatches && alert.sensitiveMatches.length > 0 ? (
                <div className="space-y-2">
                  {alert.sensitiveMatches.map((match, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm font-mono"
                    >
                      {match}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 bg-gray-50 rounded-lg text-gray-500 text-sm text-center">
                  No sensitive data patterns detected in this alert
                </div>
              )}
            </div>
          </div>

          {/* File Preview - NOT IMPLEMENTED */}
          <div className="card mb-6">
            <div className="card-header">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Eye size={20} />
                File Preview
                <NotImplementedBadge />
              </h3>
            </div>
            <div className="card-body">
              <IntegrationPlaceholder
                feature="File Content Preview"
                endpoint="GET /view_file/<id> (as JSON API)"
                description="Backend currently returns HTML only. Need JSON API endpoint for safe content preview."
                showBanner={true}
              >
                <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm whitespace-pre-wrap overflow-auto max-h-48">
                  <p className="text-gray-500">Preview not available</p>
                </div>
              </IntegrationPlaceholder>
            </div>
          </div>

          {/* Event Timeline - NOT IMPLEMENTED */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                Activity Timeline
                <NotImplementedBadge />
              </h3>
            </div>
            <div className="card-body">
              <IntegrationPlaceholder
                feature="Activity Event Timeline"
                endpoint="GET /alerts/<id>/timeline"
                description="Historical events and activities related to this alert (file access, upload attempts, file operations)"
                showBanner={true}
              >
                <div className="flex items-center justify-center p-8 bg-gray-50 rounded border border-dashed border-gray-300">
                  <p className="text-gray-500 text-center">
                    <AlertCircle size={20} className="mx-auto mb-2 opacity-50" />
                    Activity timeline data not yet available from backend
                  </p>
                </div>
              </IntegrationPlaceholder>
            </div>
          </div>

          {/* Notes Section */}
          <div className="card mt-6">
            <div className="card-header">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                Investigation Notes
                <NotImplementedBadge />
              </h3>
            </div>
            <div className="card-body">
              <IntegrationPlaceholder
                feature="Persistent Notes Storage"
                endpoint="POST /alerts/<id>/notes, GET /alerts/<id>/notes"
                description="Backend storage for analyst investigation notes and findings"
                showBanner={true}
              >
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add investigation notes, findings, or recommendations..."
                  className="form-input h-24 resize-none"
                  disabled
                />
                <button className="btn btn-primary mt-4" disabled>
                  Save Notes
                </button>
              </IntegrationPlaceholder>
            </div>
          </div>
        </div>
      </div>
      )}
    </div>
  );
};

export default Investigation;
