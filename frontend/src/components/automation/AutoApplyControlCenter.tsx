import { useState, useEffect } from 'react';
import { Play, Pause, Settings, AlertCircle, Save } from 'lucide-react';
import {
  getAutoApplyConfig,
  updateAutoApplyConfig,
  enableAutoApply,
  pauseAutoApply,
  getAutomationHealth,
} from '../../services/api';

export default function AutoApplyControlCenter() {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const [data, healthData] = await Promise.all([
        getAutoApplyConfig(),
        getAutomationHealth()
      ]);
      setConfig(data);
      setHealth(healthData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load config');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async () => {
    if (!config) return;
    try {
      if (config.auto_apply_enabled) {
        await pauseAutoApply();
      } else {
        await enableAutoApply();
      }
      await fetchConfig(); // Refresh state
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to toggle Auto Apply');
    }
  };

  const handleSaveLimits = async () => {
    if (!config) return;
    setSaving(true);
    try {
      await updateAutoApplyConfig({
        daily_limit: config.daily_limit,
        weekly_limit: config.weekly_limit,
      });
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save limits');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="text-gray-400 p-4">Loading Auto Apply Config...</div>;

  return (
    <div className="bg-cardBorder rounded-lg p-6 space-y-4 shadow-lg border border-gray-700/50">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2 text-white">
            <Settings className="w-6 h-6 text-emerald-400" />
            Auto Apply Engine
          </h2>
          <p className="text-sm text-gray-400">Control your automated application settings</p>
        </div>
        <button
          onClick={handleToggle}
          className={`flex items-center gap-2 px-4 py-2 rounded-md font-semibold transition-colors ${
            config?.auto_apply_enabled
              ? 'bg-rose-500/10 text-rose-500 hover:bg-rose-500/20'
              : 'bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20'
          }`}
        >
          {config?.auto_apply_enabled ? (
            <>
              <Pause className="w-5 h-5" /> Pause Auto Apply
            </>
          ) : (
            <>
              <Play className="w-5 h-5" /> Enable Auto Apply
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/50 text-rose-400 p-3 rounded-md flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {health && health.status !== 'ok' && (
        <div className="bg-amber-500/10 border border-amber-500/50 text-amber-400 p-3 rounded-md flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          Worker status is degraded. Auto apply functionality may be delayed or unavailable. ({health.message})
        </div>
      )}

      {config && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4 bg-black/20 p-4 rounded-lg">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">
              Daily Limit
            </label>
            <input
              type="number"
              min="0"
              value={config.daily_limit}
              onChange={(e) => setConfig({ ...config, daily_limit: parseInt(e.target.value) || 0 })}
              className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Used today: {config.daily_count} / {config.daily_limit}
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">
              Weekly Limit
            </label>
            <input
              type="number"
              min="0"
              value={config.weekly_limit}
              onChange={(e) => setConfig({ ...config, weekly_limit: parseInt(e.target.value) || 0 })}
              className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-white focus:outline-none focus:border-emerald-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Used this week: {config.weekly_count} / {config.weekly_limit}
            </p>
          </div>
        </div>
      )}

      <div className="flex justify-end pt-2">
        <button
          onClick={handleSaveLimits}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md transition-colors disabled:opacity-50"
        >
          <Save className="w-4 h-4" />
          {saving ? 'Saving...' : 'Save Limits'}
        </button>
      </div>
    </div>
  );
}
