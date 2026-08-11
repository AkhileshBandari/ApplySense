import React from 'react';
import { X, MapPin, Briefcase, DollarSign, Bookmark, ExternalLink } from 'lucide-react';

interface JobDetailsModalProps {
    job: any;
    onClose: () => void;
    onToggleSave: (e: React.MouseEvent) => void;
}

export default function JobDetailsModal({ job, onClose, onToggleSave }: JobDetailsModalProps) {
    const matchInfo = job.match_info || {};
    const score = matchInfo.overall_score ?? 0;
    const scoreColor = score >= 80 ? 'text-emerald-400' : score >= 50 ? 'text-amber-400' : 'text-red-400';

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
            <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col relative" onClick={e => e.stopPropagation()}>
                
                {/* Header */}
                <div className="p-6 border-b border-slate-700 flex justify-between items-start sticky top-0 bg-slate-900/95 backdrop-blur z-10 rounded-t-xl">
                    <div className="pr-12">
                        <h2 className="text-2xl font-bold text-white mb-2">{job.title}</h2>
                        <div className="flex flex-wrap items-center gap-4 text-sm text-slate-300">
                            <span className="font-semibold text-slate-200">{job.company}</span>
                            {job.location && (
                                <span className="flex items-center gap-1"><MapPin className="h-4 w-4" /> {job.location}</span>
                            )}
                            {job.work_mode && (
                                <span className="flex items-center gap-1"><Briefcase className="h-4 w-4" /> {job.work_mode}</span>
                            )}
                            {job.salary_min && (
                                <span className="flex items-center gap-1"><DollarSign className="h-4 w-4" /> {job.salary_min} - {job.salary_max} {job.salary_currency}</span>
                            )}
                        </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                        <button 
                            onClick={onToggleSave}
                            className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition text-slate-300"
                        >
                            <Bookmark className={`h-5 w-5 ${job.is_saved ? 'fill-indigo-500 text-indigo-500' : ''}`} />
                        </button>
                        {job.source_url && (
                            <a href={job.source_url} target="_blank" rel="noopener noreferrer" className="p-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition text-white">
                                <ExternalLink className="h-5 w-5" />
                            </a>
                        )}
                        <button onClick={onClose} className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition text-slate-300 ml-2">
                            <X className="h-5 w-5" />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto flex-1 flex flex-col md:flex-row gap-8">
                    
                    {/* Left Col: Description */}
                    <div className="flex-1 space-y-6">
                        <section>
                            <h3 className="text-lg font-bold text-white mb-3">Job Description</h3>
                            <div className="prose prose-invert max-w-none text-slate-300 whitespace-pre-wrap text-sm leading-relaxed">
                                {job.description || "No description provided."}
                            </div>
                        </section>
                    </div>

                    {/* Right Col: Match Analysis */}
                    <div className="w-full md:w-80 space-y-6">
                        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-5">
                            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Match Analysis</h3>
                            
                            <div className="flex items-center gap-4 mb-6 pb-6 border-b border-slate-700">
                                <div className={`text-4xl font-bold ${scoreColor}`}>
                                    {score}%
                                </div>
                                <div>
                                    <div className="text-white font-medium">Overall Match</div>
                                    <div className="text-sm text-slate-400">Based on your verified profile</div>
                                </div>
                            </div>

                            {/* Missing Requirements */}
                            {matchInfo.missing_required?.length > 0 && (
                                <div className="mb-4">
                                    <h4 className="text-sm font-medium text-red-400 mb-2 flex items-center gap-2">
                                        <X className="h-4 w-4" /> Missing Required
                                    </h4>
                                    <ul className="space-y-1">
                                        {matchInfo.missing_required.map((req: string, i: number) => (
                                            <li key={i} className="text-sm text-slate-300 pl-6 relative before:content-[''] before:w-1.5 before:h-1.5 before:bg-red-500/50 before:rounded-full before:absolute before:left-2 before:top-2">
                                                {req}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Missing Preferred */}
                            {matchInfo.missing_preferred?.length > 0 && (
                                <div className="mb-4">
                                    <h4 className="text-sm font-medium text-amber-400 mb-2">Missing Preferred</h4>
                                    <ul className="space-y-1">
                                        {matchInfo.missing_preferred.map((req: string, i: number) => (
                                            <li key={i} className="text-sm text-slate-300 pl-6 relative before:content-[''] before:w-1.5 before:h-1.5 before:bg-amber-500/50 before:rounded-full before:absolute before:left-2 before:top-2">
                                                {req}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Preference Conflicts */}
                            {matchInfo.candidate_preference_conflicts?.length > 0 && (
                                <div className="mb-4">
                                    <h4 className="text-sm font-medium text-rose-400 mb-2">Preference Conflicts</h4>
                                    <ul className="space-y-1">
                                        {matchInfo.candidate_preference_conflicts.map((req: string, i: number) => (
                                            <li key={i} className="text-sm text-slate-300 pl-6 relative before:content-[''] before:w-1.5 before:h-1.5 before:bg-rose-500/50 before:rounded-full before:absolute before:left-2 before:top-2">
                                                {req}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Call to action */}
                            <div className="mt-6 pt-6 border-t border-slate-700">
                                <button className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition">
                                    Tailor Resume for Job
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
