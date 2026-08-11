import { useState, useEffect } from 'react';
import { ShieldAlert, ExternalLink, Clock } from 'lucide-react';
import { getUserActionRequired } from '../../services/api';

export default function UserActionRequiredWidget() {
  const [actions, setActions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchActions();
    const interval = setInterval(fetchActions, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchActions = async () => {
    try {
      const data = await getUserActionRequired();
      setActions(data.results || data);
    } catch (err) {
      console.error('Failed to fetch user actions required', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return null; // Fade in silently
  if (actions.length === 0) return null; // Only show if there's action required

  return (
    <div className="bg-amber-500/10 border border-amber-500/50 rounded-lg p-6 shadow-lg relative overflow-hidden">
      <div className="absolute top-0 right-0 p-4 opacity-10">
        <ShieldAlert className="w-24 h-24 text-amber-500" />
      </div>
      
      <h2 className="text-lg font-bold flex items-center gap-2 text-amber-400 mb-4 relative z-10">
        <ShieldAlert className="w-5 h-5" />
        Action Required
      </h2>
      
      <p className="text-sm text-gray-300 mb-4 relative z-10">
        The Auto Apply engine encountered security checks (e.g. CAPTCHAs, OTPs) that require your manual input.
      </p>

      <div className="space-y-3 relative z-10 max-h-64 overflow-y-auto custom-scrollbar pr-2">
        {actions.map((action) => (
          <div key={action.id} className="bg-black/30 rounded-md p-4 border border-amber-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="bg-amber-500/20 text-amber-300 text-xs px-2 py-0.5 rounded font-mono uppercase tracking-wider">
                  {action.action_type.replace('_', ' ')}
                </span>
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {new Date(action.created_at).toLocaleString()}
                </span>
              </div>
              <p className="text-sm text-gray-200 mt-2 font-medium">
                {action.job_title || 'Unknown Job'} @ {action.job_company || 'Unknown Company'}
              </p>
            </div>
            
            <a
              href={action.job_url || '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 flex items-center justify-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-black font-semibold rounded-md transition-colors text-sm"
            >
              Complete Manually <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}
