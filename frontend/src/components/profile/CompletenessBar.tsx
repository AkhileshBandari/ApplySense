import { useEffect, useState } from 'react';
import { Target, CheckCircle2 } from 'lucide-react';
import api from '../../services/api';

interface CompletenessData {
    overall: number;
    missing: string[];
    next_action: string;
}

export default function CompletenessBar({ refreshTrigger }: { refreshTrigger: number }) {
    const [data, setData] = useState<CompletenessData | null>(null);

    useEffect(() => {
        api.get('/api/profile/completeness/')
            .then(res => setData(res.data))
            .catch(err => console.error("Failed to fetch completeness", err));
    }, [refreshTrigger]);

    if (!data) return null;

    const isComplete = data.overall >= 100;

    return (
        <div className="rounded-3xl border border-cardBorder bg-card p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Target className="w-5 h-5 text-accentTeal" />
                    <h3 className="text-lg font-semibold text-white">Profile Completeness</h3>
                </div>
                <span className="text-lg font-bold text-accentTeal">{data.overall}%</span>
            </div>
            
            <div className="w-full bg-slate-800 rounded-full h-2.5 mb-4 overflow-hidden">
                <div 
                    className="bg-accentTeal h-2.5 rounded-full transition-all duration-500 ease-in-out" 
                    style={{ width: `${Math.min(data.overall, 100)}%` }}
                ></div>
            </div>

            {isComplete ? (
                <div className="flex items-center gap-2 text-emerald-400 text-sm">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Your profile is complete! You are ready to apply.</span>
                </div>
            ) : (
                <div className="text-sm text-slate-300">
                    <p className="mb-2"><strong>Next up:</strong> {data.next_action}</p>
                    {data.missing.length > 0 && (
                        <p className="text-slate-500 text-xs">Missing: {data.missing.join(', ')}</p>
                    )}
                </div>
            )}
        </div>
    );
}
