import { useEffect, useState } from 'react';
import api from '../services/api';
import { Activity, Database, Server, Settings, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

export default function OpsDashboardPage() {
    const [liveness, setLiveness] = useState<any>(null);
    const [readiness, setReadiness] = useState<any>(null);
    const [automation, setAutomation] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchHealth = async () => {
            try {
                // Ensure API handles public access correctly or attach dummy tokens if needed
                const [liveRes, readyRes, autoRes] = await Promise.all([
                    api.get('/health/liveness/'),
                    api.get('/health/readiness/'),
                    api.get('/health/automation/')
                ]);
                setLiveness(liveRes.data);
                setReadiness(readyRes.data);
                setAutomation(autoRes.data);
            } catch (err) {
                setError('Failed to fetch health endpoints. Backend might be completely offline or Rate-limited.');
            } finally {
                setLoading(false);
            }
        };

        fetchHealth();
        
        const interval = setInterval(fetchHealth, 10000); // Polling every 10s
        return () => clearInterval(interval);
    }, []);

    const StatusIcon = ({ status }: { status: string }) => {
        if (status === 'HEALTHY') return <CheckCircle className="w-5 h-5 text-emerald-500" />;
        if (status === 'DEGRADED') return <AlertTriangle className="w-5 h-5 text-amber-500" />;
        return <XCircle className="w-5 h-5 text-rose-500" />;
    };

    if (loading) {
        return <div className="p-8 text-center text-slate-400">Loading System Telemetry...</div>;
    }

    return (
        <div className="p-8 max-w-5xl mx-auto text-slate-100">
            <h1 className="text-3xl font-bold mb-8 flex items-center gap-3">
                <Activity className="text-blue-400 w-8 h-8" />
                Production Ops Dashboard
            </h1>

            {error && (
                <div className="bg-rose-900/30 border border-rose-500/50 text-rose-200 p-4 rounded-lg mb-8">
                    {error}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                {/* Core API */}
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-xl">
                    <h2 className="text-lg font-semibold flex items-center gap-2 mb-4 border-b border-slate-700 pb-2">
                        <Server className="w-5 h-5 text-indigo-400" />
                        API Liveness
                    </h2>
                    <div className="flex items-center justify-between">
                        <span className="text-slate-400">Status</span>
                        <div className="flex items-center gap-2">
                            <span className="font-mono">{liveness?.status || 'UNAVAILABLE'}</span>
                            <StatusIcon status={liveness?.status} />
                        </div>
                    </div>
                </div>

                {/* Databases */}
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-xl">
                    <h2 className="text-lg font-semibold flex items-center gap-2 mb-4 border-b border-slate-700 pb-2">
                        <Database className="w-5 h-5 text-emerald-400" />
                        Data Infrastructure
                    </h2>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <span className="text-slate-400">PostgreSQL</span>
                            <div className="flex items-center gap-2">
                                <span className="font-mono">{readiness?.details?.db || 'UNAVAILABLE'}</span>
                                <StatusIcon status={readiness?.details?.db} />
                            </div>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-slate-400">Redis (Broker)</span>
                            <div className="flex items-center gap-2">
                                <span className="font-mono">{readiness?.details?.redis || 'UNAVAILABLE'}</span>
                                <StatusIcon status={readiness?.details?.redis} />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Automation Workers */}
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-xl">
                    <h2 className="text-lg font-semibold flex items-center gap-2 mb-4 border-b border-slate-700 pb-2">
                        <Settings className="w-5 h-5 text-amber-400" />
                        Automation Nodes
                    </h2>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <span className="text-slate-400">General Workers</span>
                            <div className="flex items-center gap-2">
                                <span className="font-mono">{automation?.details?.automation_worker || 'UNAVAILABLE'}</span>
                                <StatusIcon status={automation?.details?.automation_worker} />
                            </div>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-slate-400">Browser Workers</span>
                            <div className="flex items-center gap-2">
                                <span className="font-mono">{automation?.details?.browser_worker || 'UNAVAILABLE'}</span>
                                <StatusIcon status={automation?.details?.browser_worker} />
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}
