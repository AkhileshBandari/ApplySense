import { useState, useEffect } from 'react';
import { Activity, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { getAutoApplyRuns } from '../../services/api';

export default function AutoApplyRunsWidget() {
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchRuns();
    // Poll every 10 seconds for updates
    const interval = setInterval(fetchRuns, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchRuns = async () => {
    try {
      const data = await getAutoApplyRuns();
      setRuns(data.results || data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load runs');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return <CheckCircle className="w-5 h-5 text-emerald-500" />;
      case 'FAILED':
        return <XCircle className="w-5 h-5 text-rose-500" />;
      case 'USER_ACTION_REQUIRED':
        return <AlertTriangle className="w-5 h-5 text-amber-500" />;
      default:
        return <Activity className="w-5 h-5 text-blue-500" />;
    }
  };

  if (loading) return <div className="text-gray-400 p-4">Loading runs...</div>;

  return (
    <div className="bg-cardBorder rounded-lg p-6 flex flex-col h-full shadow-lg border border-gray-700/50">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold flex items-center gap-2 text-white">
          <Activity className="w-5 h-5 text-blue-400" />
          Recent Auto Apply Runs
        </h2>
      </div>

      {error && <p className="text-rose-400 text-sm mb-4">{error}</p>}

      {runs.length === 0 ? (
        <p className="text-gray-400 text-sm italic flex-1 flex items-center justify-center">
          No automated runs yet.
        </p>
      ) : (
        <div className="overflow-y-auto max-h-64 space-y-3 pr-2 custom-scrollbar">
          {runs.map((run) => (
            <div
              key={run.id}
              className="bg-black/20 p-3 rounded-md border border-gray-800 flex items-start gap-3"
            >
              <div className="mt-0.5">{getStatusIcon(run.status)}</div>
              <div className="flex-1">
                <div className="flex justify-between items-start">
                  <h4 className="text-sm font-semibold text-gray-200">
                    {run.job_title || 'Unknown Job'}
                  </h4>
                  <span className="text-xs text-gray-500 whitespace-nowrap ml-2">
                    {new Date(run.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-1">{run.job_company || 'Unknown Company'}</p>
                {run.failure_reason && (
                  <p className="text-xs text-rose-400 mt-1.5 bg-rose-500/10 px-2 py-1 rounded inline-block">
                    {run.failure_reason}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
