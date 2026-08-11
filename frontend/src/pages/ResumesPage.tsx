import { ChangeEvent, useEffect, useState } from 'react';
import {
    UploadCloud,
    FileText,
    ArrowRight,
    ShieldCheck,
    Check,
    Sparkles,
    Trash2,
    RefreshCw,
    Download,
    AlertCircle,
    Activity
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function ResumesPage() {
    const navigate = useNavigate();
    const [resumes, setResumes] = useState<any[]>([]);
    const [uploading, setUploading] = useState(false);
    const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null);
    const [jobDesc, setJobDesc] = useState('');
    const [tailoredVersion, setTailoredVersion] = useState<any>(null);
    const [tailorLoading, setTailorLoading] = useState(false);
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');
    const [refreshing, setRefreshing] = useState(false);

    const loadResumes = async () => {
        setRefreshing(true);
        try {
            const { data } = await api.get('/api/resumes/');
            if (data?.length) {
                setResumes(data);
                setMessage('Resumes refreshed.');
            } else {
                setResumes([]);
                setMessage('No resumes found.');
            }
        } catch {
            setError('Unable to load resumes.');
        } finally {
            setRefreshing(false);
        }
    };

    useEffect(() => {
        loadResumes();
    }, []);

    const handleFileUpload = (e: ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files || e.target.files.length === 0) return;
        const file = e.target.files[0];
        setUploading(true);
        setError('');
        setMessage('');

        const formData = new FormData();
        formData.append('file', file);
        api.post('/api/resumes/upload/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        })
            .then(({ data }: { data: any }) => {
                const resume = data.resume ?? data;
                if (resume?.id) {
                    setResumes(prev => [resume, ...prev]);
                    setMessage('Upload complete. Parsing started.');
                }
            })
            .catch(() => setError('Upload failed. Please try again.'))
            .finally(() => setUploading(false));
    };

    const handleDeleteResume = async (resumeId: number) => {
        if (!window.confirm('Are you sure you want to delete this resume?')) return;
        try {
            await api.delete(`/api/resumes/${resumeId}/`);
            setResumes(prev => prev.filter(r => r.id !== resumeId));
            setMessage('Resume deleted.');
        } catch {
            setError('Failed to delete resume.');
        }
    };

    const handleDownloadResume = async (resumeId: number) => {
        try {
            const { data } = await api.get(`/api/resumes/${resumeId}/`, { responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `resume-${resumeId}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            setMessage('Resume downloaded.');
        } catch {
            setError('Failed to download resume.');
        }
    };

    const handleTailor = (resumeId: number) => {
        setSelectedResumeId(resumeId);
        setTailorLoading(true);
        setTailoredVersion(null);
        setError('');

        api.post(`/api/resumes/${resumeId}/tailor/`, {
            job_description: jobDesc,
            job_title: 'Custom Job Title', // Users could input this later
            job_company: 'Custom Company'
        })
            .then(({ data }: { data: any }) => {
                setTailoredVersion(data);
                setMessage('Tailoring completed.');
            })
            .catch(() => setError('Tailoring failed. Please try again.'))
            .finally(() => setTailorLoading(false));
    };

    const handleDownloadTailored = async (versionId: number) => {
        try {
            const { data } = await api.get(`/api/resumes/versions/${versionId}/download/`, { responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `tailored-resume-${versionId}.docx`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            setMessage('Tailored Resume downloaded.');
        } catch {
            setError('Failed to download tailored resume.');
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'REVIEW_REQUIRED': return 'text-yellow-400 border-yellow-400/50 bg-yellow-400/10';
            case 'CONFIRMED': return 'text-emerald-400 border-emerald-400/50 bg-emerald-400/10';
            case 'FAILED': return 'text-red-400 border-red-400/50 bg-red-400/10';
            default: return 'text-cyan-400 border-cyan-400/50 bg-cyan-400/10'; // UPLOADED, EXTRACTING, PARSING
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                    <div className="inline-flex items-center gap-2 rounded-full bg-cardHover px-3 py-1 text-sm font-semibold text-white">
                        <UploadCloud className="h-4 w-4" /> Resume Intelligence
                    </div>
                    <h1 className="mt-4 text-3xl font-semibold text-white">Resume Manager</h1>
                    <p className="mt-2 max-w-2xl text-sm text-slate-300">
                        Upload your resume for AI parsing. Review extracted facts before they enter your profile.
                    </p>
                </div>

                <div className="flex flex-col gap-2 sm:flex-row">
                    <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-cardBorder bg-card p-3 text-sm text-slate-200 transition hover:border-slate-400">
                        <UploadCloud />
                        <span>{uploading ? 'Uploading...' : 'Upload Resume'}</span>
                        <input type="file" className="hidden" onChange={handleFileUpload} />
                    </label>
                </div>
            </div>

            {/* Main layout */}
            <div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
                {/* Uploaded Resumes */}
                <section className="glass-panel rounded-3xl p-6">
                    <div className="mb-6 flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-semibold text-white">Uploaded Resumes</h2>
                            <p className="text-sm text-slate-400">View your current resume collection and processing status.</p>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-cardBorder bg-slate-800 text-slate-100 transition hover:border-slate-400 disabled:opacity-60"
                                onClick={loadResumes}
                                disabled={refreshing}
                                title="Refresh resumes"
                            >
                                <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                            </button>
                            <div className="inline-flex items-center gap-2 rounded-full bg-slate-700/70 px-3 py-2 text-sm text-slate-100">
                                <ShieldCheck className="h-4 w-4" /> {resumes.length} resumes
                            </div>
                        </div>
                    </div>

                    {error ? <p className="mb-4 text-sm text-red-400">{error}</p> : null}
                    {message ? <p className="mb-4 text-sm text-emerald-400">{message}</p> : null}
                    <div className="space-y-4">
                        {resumes.map(resume => (
                            <div key={resume.id} className="rounded-3xl border border-cardBorder bg-card p-5">
                                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <p className="text-sm text-slate-400">{new Date(resume.uploaded_at).toLocaleString()}</p>
                                            <span className={`px-2 py-0.5 rounded-full text-xs border ${getStatusColor(resume.status)}`}>
                                                {resume.status.replace('_', ' ')}
                                            </span>
                                        </div>
                                        <h3 className="mt-2 text-lg font-semibold text-white">{resume.file_name}</h3>
                                        {resume.status === 'FAILED' && resume.parsing_error && (
                                            <p className="mt-1 text-sm text-red-400 flex items-center gap-1">
                                                <AlertCircle className="w-4 h-4"/> {resume.parsing_error}
                                            </p>
                                        )}
                                        {resume.status === 'REVIEW_REQUIRED' && (
                                            <p className="mt-1 text-sm text-yellow-300 flex items-center gap-1">
                                                <Activity className="w-4 h-4"/> Requires review of extracted facts.
                                            </p>
                                        )}
                                    </div>

                                    <div className="flex flex-wrap items-center gap-2">
                                        {resume.status === 'REVIEW_REQUIRED' && (
                                            <button
                                                className="inline-flex items-center gap-2 rounded-full bg-yellow-500/20 text-yellow-300 border border-yellow-500/50 px-4 py-2 text-sm font-semibold transition hover:bg-yellow-500/30"
                                                onClick={() => navigate('/profile')} // They go to profile to review facts
                                            >
                                                Review Facts
                                            </button>
                                        )}
                                        <button
                                            className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-cardBorder bg-slate-800 text-slate-100 transition hover:border-slate-400"
                                            onClick={() => handleDownloadResume(resume.id)}
                                            title="Download resume"
                                        >
                                            <Download className="h-4 w-4" />
                                        </button>
                                        <button
                                            className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-red-500/40 bg-red-950/40 text-red-200 transition hover:border-red-400"
                                            onClick={() => handleDeleteResume(resume.id)}
                                            title="Delete resume"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                        {resume.status === 'CONFIRMED' && (
                                            <button
                                                className="inline-flex items-center gap-2 rounded-full bg-accentTeal px-4 py-2 text-sm font-semibold text-darkBg transition hover:bg-cyan-500"
                                                onClick={() => handleTailor(resume.id)}
                                            >
                                                Tailor Resume
                                                <Sparkles className="h-4 w-4" />
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Resume Tailoring */}
                <aside className="glass-panel rounded-3xl p-6 h-fit sticky top-6">
                    <div className="mb-4 flex items-center gap-3 text-white">
                        <FileText className="h-5 w-5" />
                        <h2 className="text-lg font-semibold">Resume Tailoring</h2>
                    </div>

                    <div className="space-y-4">
                        <textarea
                            className="w-full rounded-3xl border border-cardBorder bg-slate-950/80 p-4 text-sm text-slate-200 outline-none transition focus:border-cyan-500"
                            placeholder="Paste a job description to tailor your resume..."
                            value={jobDesc}
                            onChange={e => setJobDesc(e.target.value)}
                            rows={5}
                        />

                        <button
                            className="inline-flex w-full items-center justify-center gap-2 rounded-3xl bg-accentTeal px-4 py-3 text-sm font-semibold text-darkBg transition hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed"
                            disabled={tailorLoading || selectedResumeId === null}
                            onClick={() => selectedResumeId !== null && handleTailor(selectedResumeId)}
                        >
                            {tailorLoading ? 'Generating feedback...' : 'Generate Tailored Feedback'}
                            <ArrowRight className="h-4 w-4" />
                        </button>

                        {tailoredVersion ? (
                            <div className="rounded-3xl border border-cardBorder bg-slate-950/80 p-4 max-h-[400px] overflow-y-auto space-y-4">
                                <div className="mb-3 flex items-center justify-between text-slate-200">
                                    <div className="flex items-center gap-2">
                                        <Check className="h-4 w-4 text-emerald-400" /> <span>Tailoring complete</span>
                                    </div>
                                    <button 
                                        onClick={() => handleDownloadTailored(tailoredVersion.id)}
                                        className="text-xs bg-cyan-600 hover:bg-cyan-500 text-white px-2 py-1 rounded-full flex items-center gap-1"
                                    >
                                        <Download className="w-3 h-3" /> DOCX
                                    </button>
                                </div>
                                <div className="space-y-3">
                                    {tailoredVersion.changes && tailoredVersion.changes.length > 0 ? (
                                        tailoredVersion.changes.map((change: any) => (
                                            <div key={change.id} className="border border-slate-700 p-3 rounded-xl bg-slate-900/50">
                                                <div className="flex justify-between items-start mb-2">
                                                    <span className="text-xs font-semibold uppercase text-cyan-400">{change.section}</span>
                                                    <span className={`text-xs px-2 py-0.5 rounded-full ${change.validation_status === 'SUPPORTED' ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-500/30' : 'bg-yellow-900/50 text-yellow-400 border border-yellow-500/30'}`}>
                                                        {change.validation_status}
                                                    </span>
                                                </div>
                                                <div className="text-xs text-red-300 line-through mb-1">{change.original_text}</div>
                                                <div className="text-sm text-emerald-300 font-medium mb-2">{change.proposed_text}</div>
                                                <div className="text-xs text-slate-400 italic">Reason: {change.reason}</div>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="text-sm text-slate-300">No changes proposed. Your resume already matches well!</div>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className="rounded-3xl border border-dashed border-slate-700 bg-slate-950/70 p-4 text-sm text-slate-400">
                                Select a confirmed resume and paste a job description to receive guidance.
                            </div>
                        )}
                    </div>
                </aside>
            </div>
        </div>
    );
}
