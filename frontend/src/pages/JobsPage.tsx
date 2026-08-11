import React, { useState, useEffect } from 'react';
import { MapPin, Briefcase, Bookmark } from 'lucide-react';
import api from '../services/api';
import JobDetailsModal from '../components/jobs/JobDetailsModal';

export default function JobsPage() {
    const [jobs, setJobs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedJob, setSelectedJob] = useState<any | null>(null);
    const [filterCategory, setFilterCategory] = useState('ALL');
    const [searchLocation, setSearchLocation] = useState('');
    const [targetCountry, setTargetCountry] = useState('');
    const [remoteWorldwide, setRemoteWorldwide] = useState(false);
    const [sponsorshipAvailable, setSponsorshipAvailable] = useState(false);

    const fetchJobs = async () => {
        setLoading(true);
        try {
            let url = '/api/jobs/feed/?';
            if (filterCategory !== 'ALL') {
                url += `category=${filterCategory}&`;
            }
            if (searchLocation) {
                url += `location=${searchLocation}&`;
            }
            if (targetCountry) {
                url += `country=${targetCountry}&`;
            }
            if (remoteWorldwide) {
                url += `is_remote_worldwide=true&`;
            }
            if (sponsorshipAvailable) {
                url += `sponsorship_available=true&`;
            }
            const res = await api.get(url);
            setJobs(res.data.results || []);
        } catch (e) {
            console.error("Failed to fetch jobs", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchJobs();
    }, [filterCategory, targetCountry, remoteWorldwide, sponsorshipAvailable]);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        fetchJobs();
    };

    const toggleSaveJob = async (jobId: number, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            const res = await api.post(`/api/jobs/${jobId}/save/`);
            const isSaved = res.data.status === 'saved';
            setJobs(jobs.map(j => j.id === jobId ? { ...j, is_saved: isSaved } : j));
        } catch (e) {
            console.error("Failed to save job", e);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header & Search */}
            <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold">Smart Job Feed</h1>
                    <p className="text-slate-400">Discover roles matching your verified career profile.</p>
                </div>
                <form onSubmit={handleSearch} className="flex gap-2 w-full md:w-auto">
                    <div className="relative flex-1 md:w-64">
                        <MapPin className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                        <input
                            type="text"
                            placeholder="Location..."
                            className="w-full pl-10 pr-4 py-2 bg-cardBorder rounded-lg border border-slate-700 focus:outline-none focus:border-indigo-500"
                            value={searchLocation}
                            onChange={(e) => setSearchLocation(e.target.value)}
                        />
                    </div>
                    <button type="submit" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-white font-medium transition">
                        Search
                    </button>
                </form>
            </div>

            {/* Global Filters */}
            <div className="flex flex-wrap gap-4 items-center bg-cardBorder p-4 rounded-lg border border-slate-700">
                <div className="flex items-center gap-2">
                    <label className="text-sm text-slate-400">Target Country:</label>
                    <input 
                        type="text" 
                        placeholder="e.g. United States" 
                        className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm focus:outline-none focus:border-indigo-500"
                        value={targetCountry}
                        onChange={(e) => setTargetCountry(e.target.value)}
                    />
                </div>
                <div className="flex items-center gap-2">
                    <input 
                        type="checkbox" 
                        id="remoteWorldwide"
                        checked={remoteWorldwide}
                        onChange={(e) => setRemoteWorldwide(e.target.checked)}
                        className="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500 bg-slate-800"
                    />
                    <label htmlFor="remoteWorldwide" className="text-sm text-slate-300">Remote Worldwide</label>
                </div>
                <div className="flex items-center gap-2">
                    <input 
                        type="checkbox" 
                        id="sponsorship"
                        checked={sponsorshipAvailable}
                        onChange={(e) => setSponsorshipAvailable(e.target.checked)}
                        className="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500 bg-slate-800"
                    />
                    <label htmlFor="sponsorship" className="text-sm text-slate-300">Sponsorship Available</label>
                </div>
            </div>

            {/* Filters */}
            <div className="flex gap-2 overflow-x-auto pb-2">
                {['ALL', 'SAVED', 'REMOTE'].map(cat => (
                    <button
                        key={cat}
                        onClick={() => setFilterCategory(cat)}
                        className={`px-4 py-1.5 rounded-full text-sm font-medium transition whitespace-nowrap ${
                            filterCategory === cat 
                            ? 'bg-indigo-600 text-white' 
                            : 'bg-cardBorder text-slate-300 hover:bg-cardHover'
                        }`}
                    >
                        {cat.charAt(0) + cat.slice(1).toLowerCase()}
                    </button>
                ))}
            </div>

            {/* Feed */}
            {loading ? (
                <div className="text-center py-12 text-slate-400">Loading your feed...</div>
            ) : jobs.length === 0 ? (
                <div className="text-center py-12 bg-cardBorder rounded-lg">
                    <p className="text-slate-400 mb-2">No jobs found.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {jobs.map(job => {
                        const matchInfo = job.match_info || {};
                        const score = matchInfo.overall_score ?? 0;
                        const isEligible = matchInfo.eligibility === 'ELIGIBLE' || matchInfo.eligibility === 'POSSIBLY_ELIGIBLE';
                        const scoreColor = score >= 80 ? 'text-emerald-400' : score >= 50 ? 'text-amber-400' : 'text-red-400';

                        return (
                            <div 
                                key={job.id} 
                                onClick={() => setSelectedJob(job)}
                                className="bg-cardBorder border border-slate-700 rounded-lg p-5 hover:border-indigo-500 transition cursor-pointer flex flex-col h-full relative group"
                            >
                                <button 
                                    onClick={(e) => toggleSaveJob(job.id, e)}
                                    className="absolute top-4 right-4 p-2 rounded-full hover:bg-slate-700 transition"
                                >
                                    <Bookmark className={`h-5 w-5 ${job.is_saved ? 'fill-indigo-500 text-indigo-500' : 'text-slate-400'}`} />
                                </button>

                                <div className="mb-4 pr-8">
                                    <h3 className="font-bold text-lg leading-tight line-clamp-2">{job.title}</h3>
                                    <p className="text-slate-400">{job.company}</p>
                                </div>

                                <div className="flex flex-wrap gap-2 mb-4">
                                    {job.location && (
                                        <span className="flex items-center gap-1 text-xs bg-slate-800 px-2 py-1 rounded text-slate-300">
                                            <MapPin className="h-3 w-3" /> {job.location}
                                        </span>
                                    )}
                                    {job.country && (
                                        <span className="flex items-center gap-1 text-xs bg-slate-800 px-2 py-1 rounded text-slate-300">
                                            {job.country} {job.is_remote_worldwide && '(Remote Worldwide)'}
                                        </span>
                                    )}
                                    {job.work_mode && (
                                        <span className="flex items-center gap-1 text-xs bg-slate-800 px-2 py-1 rounded text-slate-300">
                                            <Briefcase className="h-3 w-3" /> {job.work_mode}
                                        </span>
                                    )}
                                    <span className="flex items-center gap-1 text-xs bg-indigo-900/30 text-indigo-300 px-2 py-1 rounded border border-indigo-500/30">
                                        Source: {job.source || 'Custom'} {job.application_provider ? `→ ${job.application_provider}` : ''}
                                    </span>
                                </div>

                                <div className="mt-auto pt-4 border-t border-slate-700 flex items-center justify-between">
                                    <div className="flex flex-col">
                                        <span className="text-xs text-slate-400 uppercase tracking-wider">Match Score</span>
                                        <span className={`text-xl font-bold ${scoreColor}`}>{score}%</span>
                                    </div>
                                    <div className="text-right">
                                        {isEligible ? (
                                            <span className="text-xs font-medium text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded-full">Eligible</span>
                                        ) : (
                                            <span className="text-xs font-medium text-amber-400 bg-amber-400/10 px-2 py-1 rounded-full">{matchInfo.eligibility === 'STRETCH' ? 'Stretch' : 'Mismatch'}</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {selectedJob && (
                <JobDetailsModal 
                    job={selectedJob} 
                    onClose={() => setSelectedJob(null)} 
                    onToggleSave={(e) => toggleSaveJob(selectedJob.id, e)}
                />
            )}
        </div>
    );
}
