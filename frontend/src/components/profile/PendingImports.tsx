import { useEffect, useState } from 'react';
import { AlertCircle, Check, X } from 'lucide-react';
import api from '../../services/api';

export default function PendingImports({ onReviewComplete }: { onReviewComplete: () => void }) {
    const [pending, setPending] = useState<any>(null);
    const loadPending = () => {
        api.get('/api/profile/pending-imports/')
            .then(res => setPending(res.data))
            .catch(err => console.error(err));
    };

    useEffect(() => {
        loadPending();
    }, []);

    if (!pending) return null;

    const hasPending = Object.values(pending).some((arr: any) => arr.length > 0);

    if (!hasPending) return null;

    const handleAction = async (action: string, factType: string, factId: number) => {
        try {
            await api.post('/api/profile/fact-review/', {
                action,
                fact_type: factType,
                fact_id: factId
            });
            loadPending();
            onReviewComplete();
        } catch (err) {
            console.error("Failed to review fact", err);
        }
    };

    const renderFactList = (title: string, factType: string, items: any[], displayKey1: string, displayKey2?: string) => {
        if (!items || items.length === 0) return null;
        return (
            <div className="mb-4">
                <h4 className="text-sm font-semibold text-slate-300 mb-2 capitalize">{title}</h4>
                <div className="space-y-2">
                    {items.map((item: any) => (
                        <div key={item.id} className="flex items-center justify-between bg-slate-900/50 p-3 rounded-xl border border-slate-700">
                            <div>
                                <p className="text-sm font-medium text-white">{item[displayKey1]}</p>
                                {displayKey2 && <p className="text-xs text-slate-400">{item[displayKey2]}</p>}
                            </div>
                            <div className="flex items-center gap-2">
                                <button onClick={() => handleAction('ACCEPT', factType, item.id)} className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 transition">
                                    <Check className="w-4 h-4" />
                                </button>
                                <button onClick={() => handleAction('REJECT', factType, item.id)} className="p-1.5 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition">
                                    <X className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    return (
        <div className="rounded-3xl border border-yellow-500/30 bg-yellow-500/5 p-6 mb-6">
            <div className="flex items-center gap-2 mb-4 text-yellow-300">
                <AlertCircle className="w-5 h-5" />
                <h3 className="text-lg font-semibold">Review Extracted Facts</h3>
            </div>
            <p className="text-sm text-slate-300 mb-4">
                We've extracted the following information from your latest resume upload. 
                Please review and confirm them to add them to your profile.
            </p>
            
            <div className="space-y-4">
                {renderFactList('Experiences', 'experience', pending.experiences, 'company', 'role')}
                {renderFactList('Education', 'education', pending.educations, 'institution', 'degree')}
                {renderFactList('Skills', 'skill', pending.skills, 'name')}
                {renderFactList('Projects', 'project', pending.projects, 'name', 'technologies')}
                {renderFactList('Certifications', 'certification', pending.certifications, 'name', 'issuer')}
                {renderFactList('Languages', 'language', pending.languages, 'name', 'proficiency')}
            </div>
        </div>
    );
}
