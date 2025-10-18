import React, { useEffect, useState, useMemo, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { MonitoringPlanEditor } from '../components/project/MonitoringPlanEditor';
import { projectsApi } from '../services/api';
import { ProjectHeader } from '../components/layout/ProjectHeader';

// Ensure timestamps are interpreted as UTC (GMT) when timezone is missing
const parseUtcMs = (isoString: string | null): number => {
  if (!isoString) return Date.now();
  const hasTimezone = /([zZ]|[+-]\d{2}:\d{2})$/.test(isoString);
  const normalized = hasTimezone ? isoString : `${isoString}Z`;
  return new Date(normalized).getTime();
};

const MonitoringPlanReview: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [status, setStatus] = useState<'loading' | 'queued' | 'running' | 'done' | 'error'>('loading');
  const [monitoringPlan, setMonitoringPlan] = useState<any | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [startedAt, setStartedAt] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const [editablePlan, setEditablePlan] = useState<any | null>(null);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');
  const saveTimer = useRef<number | null>(null);

  // Poll for status
  useEffect(() => {
    if (!projectId) return;

    const checkStatus = async () => {
      try {
        const result = await projectsApi.getMonitoringPlanStatus(projectId);

        setStatus(result.status);
        setStartedAt(((result as any).started_at) || null);

        if (result.status === 'done' && result.extracted_data) {
          setMonitoringPlan(result.extracted_data);
          setEditablePlan(result.extracted_data);
        }

        if (result.status === 'error') {
          setErrorMessage(result.error || 'Extraction failed');
        }
      } catch (error) {
        console.error('Failed to check status:', error);
        setStatus('error');
        setErrorMessage('Failed to check extraction status');
      }
    };

    checkStatus();

    // Poll every 3 seconds if not done
    const interval = setInterval(() => {
      if (status !== 'done' && status !== 'error') {
        checkStatus();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [projectId, status]);

  // Calculate fake progress based on elapsed time
  useEffect(() => {
    if (!startedAt || status === 'done' || status === 'error') return;

    const updateProgress = () => {
      const started = parseUtcMs(startedAt);
      const now = Date.now(); // UTC-based epoch ms
      const elapsed = now - started;
      const tenMinutes = 10 * 60 * 1000; // 10 minutes in ms

      // Calculate percentage (cap at 99% until actually done)
      const percentage = Math.min((elapsed / tenMinutes) * 100, 99);
      setProgress(Math.floor(percentage));
    };

    updateProgress();
    const interval = setInterval(updateProgress, 1000);

    return () => clearInterval(interval);
  }, [startedAt, status]);

  const saveMonitoringPlan = useMemo(() => {
    return async (plan: any) => {
      if (!projectId) return;
      setSaveStatus('saving');
      try {
        await projectsApi.updateMonitoringPlan(projectId, plan);
        setSaveStatus('saved');
        setTimeout(() => setSaveStatus('idle'), 2000);
      } catch (e) {
        console.error('Failed saving monitoring plan edits', e);
        setSaveStatus('idle');
      }
    };
  }, [projectId]);

  const onEditPlanField = (path: string[], value: any) => {
    setEditablePlan((prev: any) => {
      const next = JSON.parse(JSON.stringify(prev || {})); // Deep clone
      let cursor: any = next;
      for (let i = 0; i < path.length - 1; i++) {
        const key = path[i];
        if (!cursor[key]) cursor[key] = {};
        cursor = cursor[key];
      }
      cursor[path[path.length - 1]] = value;

      // Debounced save
      if (saveTimer.current) window.clearTimeout(saveTimer.current);
      saveTimer.current = window.setTimeout(() => saveMonitoringPlan(next), 600);

      return next;
    });
  };

  const handleRetry = async () => {
    if (!projectId) return;
    // Trigger re-extraction by navigating back to monitoring plan upload
    navigate(`/projects/${projectId}/upload`);
  };

  const handleNext = () => {
    if (!projectId) return;
    navigate(`/projects/${projectId}/validation`);
  };

  return (
    <div className="min-h-screen bg-gradient-radial">
      <ProjectHeader />
      <div className="container mx-auto px-4 py-8 max-w-5xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Monitoring Plan Review</h1>
          <p className="text-gray-600 mt-2">
            Review and edit the extracted monitoring plan data before generating reports
          </p>
        </div>

        {/* Loading/Processing State */}
        {(status === 'loading' || status === 'queued' || status === 'running') && (
          <div className="bg-white rounded-2xl p-8 shadow-card">
            <div className="text-center space-y-6">
              <div className="animate-pulse">
                <div className="text-6xl mb-4">📄</div>
                <h2 className="text-2xl font-semibold text-gray-700 mb-2">
                  {status === 'loading' ? 'Loading...' : 'Extracting Monitoring Plan Data'}
                </h2>
                <p className="text-gray-600">
                  {status === 'queued' && 'Your request is queued for processing...'}
                  {status === 'running' && 'AI is analyzing your document...'}
                  {status === 'loading' && 'Please wait...'}
                </p>
              </div>

              {/* Progress Bar */}
              {(status === 'queued' || status === 'running') && (
                <div className="max-w-md mx-auto">
                  <div className="relative w-full h-6 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-500 to-primary transition-all duration-1000 ease-out"
                      style={{ width: `${progress}%` }}
                    ></div>
                    <div className="absolute inset-0 flex items-center justify-center text-xs font-semibold text-gray-700">
                      {progress}% Complete
                    </div>
                  </div>
                  <p className="text-sm text-gray-500 mt-3">
                    Extraction may take up to 10 minutes. This page will update automatically.
                  </p>
                </div>
              )}

              {/* Tips */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6 max-w-md mx-auto">
                <p className="text-sm text-blue-800">
                  <strong>💡 Tip:</strong> You can navigate away from this page and come back later.
                  The extraction continues in the background.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Error State */}
        {status === 'error' && (
          <div className="bg-white rounded-2xl p-8 shadow-card">
            <div className="text-center space-y-6">
              <div className="text-6xl text-red-500">❌</div>
              <div>
                <h2 className="text-2xl font-semibold text-red-700 mb-2">Extraction Failed</h2>
                <p className="text-gray-600">{errorMessage}</p>
              </div>
              <div className="flex gap-4 justify-center">
                <button
                  onClick={handleRetry}
                  className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition"
                >
                  Upload New File
                </button>
                <button
                  onClick={() => navigate(`/projects/${projectId}/validation`)}
                  className="px-6 py-2 border-2 border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
                >
                  Back to Validation
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Success State - Show Editor */}
        {status === 'done' && editablePlan && (
          <div className="bg-white rounded-2xl p-8 shadow-card space-y-6">
            <div className="flex items-center justify-between pb-4 border-b">
              <div>
                <h2 className="text-2xl font-semibold text-gray-800">Edit Monitoring Plan Data</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Review and edit the extracted information. Changes are automatically saved.
                </p>
              </div>
              {saveStatus !== 'idle' && (
                <div className="flex items-center gap-2 bg-blue-50 px-4 py-2 rounded-lg">
                  {saveStatus === 'saving' && (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      <span className="text-sm text-blue-700">Saving...</span>
                    </>
                  )}
                  {saveStatus === 'saved' && (
                    <>
                      <span className="text-green-600">✓</span>
                      <span className="text-sm text-green-700">Saved</span>
                    </>
                  )}
                </div>
              )}
            </div>

            <MonitoringPlanEditor data={editablePlan} onEdit={onEditPlanField} />

            {/* Navigation */}
            <div className="flex justify-between pt-6 border-t">
              <button
                onClick={() => navigate(`/projects/${projectId}/validation`)}
                className="px-6 py-2 border-2 border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
              >
                ← Back to Validation
              </button>
              <button
                onClick={handleNext}
                className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition"
              >
                Continue to Reports →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MonitoringPlanReview;
