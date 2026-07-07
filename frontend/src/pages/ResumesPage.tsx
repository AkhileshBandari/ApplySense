import { ChangeEvent, useState } from 'react';
import { initialResumes } from '../utils/mockData';
import {
    UploadCloud,
    FileText,
    ArrowRight,
    ShieldCheck,
    HeartPulse,
    Check,
    Sparkles,
} from 'lucide-react';

interface ResumesPageProps {
    apiMode: 'mock' | 'live';
}

export default function ResumesPage({ apiMode }: ResumesPageProps) {
    const [resumes, setResumes] = useState(initialResumes);
    const [uploading, setUploading] = useState(false);
    const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null);
    const [jobDesc, setJobDesc] = useState('');
    const [tailoredResult, setTailoredResult] = useState('');
    const [tailorLoading, setTailorLoading] = useState(false);

    const handleFileUpload = (e: ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files || e.target.files.length === 0) return;
        const file = e.target.files[0];
        setUploading(true);

        if (apiMode === 'live') {
            const formData = new FormData();
            formData.append('file', file);
            fetch('http://localhost:8000/api/resumes/upload/', {
                method: 'POST',
                headers: { Authorization: `Bearer ${localStorage.getItem('applysense_token')}` },
                body: formData,
            })
                .then(res => res.json())
                .then(data => {
                    if (data.id) {
                        setResumes(prev => [data, ...prev]);
                    }
                    setUploading(false);
                })
                .catch(() => _emulateMockUpload(file.name));
        } else {
            _emulateMockUpload(file.name);
        }
    };

    const _emulateMockUpload = (fileName: string) => {
        setTimeout(() => {
            const newResume = {
                id: Date.now(),
                file_name: fileName,
                uploaded_at: new Date().toISOString(),
                health_score: 84,
                ats_score: 82,
                parsed_data: {
                    skills: ['React', 'Python', 'SQL'],
                    experience_years: 5,
                },
            };
            setResumes(prev => [newResume, ...prev]);
            setUploading(false);
        }, 1200);
    };

    const handleTailor = (resumeId: number) => {
        setSelectedResumeId(resumeId);
        setTailorLoading(true);
        setTailoredResult('');

        // Mocked tailoring – replace with actual API call when live
        setTimeout(() => {
            setTailoredResult(
                `Tailored resume feedback for Resume #${resumeId}. Match this resume to the job description and highlight strengths clearly.`
            );
            setTailorLoading(false);
        }, 1000);
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
                        Upload and review your resume health score, ATS readiness, and get fast AI‑tailored feedback.
                    </p>
                </div>

                <div className="flex flex-col gap-2 sm:flex-row">
                    <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-cardBorder bg-card p-3 text-sm text-slate-200 transition hover:border-slate-400">
                        <UploadCloud />
                        <span>{uploading ? 'Uploading...' : 'Upload Resume'}</span>
                        <input type="file" className="hidden" onChange={handleFileUpload} />
                    </label>
                    <button
                        className="inline-flex items-center gap-2 rounded-lg bg-accentTeal px-4 py-3 text-sm font-semibold text-darkBg transition hover:bg-cyan-500"
                        onClick={() => setJobDesc('')}
                    >
                        <ArrowRight /> Reset Job Description
                    </button>
                </div>
            </div>

            {/* Main layout */}
            <div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
                {/* Uploaded Resumes */}
                <section className="glass-panel rounded-3xl p-6">
                    <div className="mb-6 flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-semibold text-white">Uploaded Resumes</h2>
                            <p className="text-sm text-slate-400">View your current resume collection and choose one to tailor.</p>
                        </div>
                        <div className="inline-flex items-center gap-2 rounded-full bg-slate-700/70 px-3 py-2 text-sm text-slate-100">
                            <ShieldCheck className="h-4 w-4" /> {resumes.length} resumes
                        </div>
                    </div>

                    <div className="space-y-4">
                        {resumes.map(resume => (
                            <div key={resume.id} className="rounded-3xl border border-cardBorder bg-card p-5">
                                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                                    <div>
                                        <p className="text-sm text-slate-400">{resume.uploaded_at}</p>
                                        <h3 className="mt-2 text-lg font-semibold text-white">{resume.file_name}</h3>
                                        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-400">
                                            {resume.parsed_data.skills.slice(0, 4).map(skill => (
                                                <span key={skill} className="rounded-full border border-slate-600 bg-slate-800 px-2 py-1">
                                                    {skill}
                                                </span>
                                            ))}
                                        </div>
                                    </div>

                                    <button
                                        className="inline-flex items-center gap-2 rounded-full bg-accentTeal px-4 py-2 text-sm font-semibold text-darkBg transition hover:bg-cyan-500"
                                        onClick={() => handleTailor(resume.id)}
                                    >
                                        Tailor Resume
                                        <Sparkles className="h-4 w-4" />
                                    </button>
                                </div>

                                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                                    <div className="rounded-3xl bg-slate-900/70 p-4 text-center">
                                        <p className="text-sm text-slate-400">Health</p>
                                        <p className="mt-2 text-2xl font-semibold text-white">{resume.health_score}%</p>
                                    </div>
                                    <div className="rounded-3xl bg-slate-900/70 p-4 text-center">
                                        <p className="text-sm text-slate-400">ATS Score</p>
                                        <p className="mt-2 text-2xl font-semibold text-white">{resume.ats_score}%</p>
                                    </div>
                                    <div className="rounded-3xl bg-slate-900/70 p-4 text-center">
                                        <p className="text-sm text-slate-400">Experience</p>
                                        <p className="mt-2 text-2xl font-semibold text-white">{resume.parsed_data.experience_years} yrs</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Resume Tailoring */}
                <aside className="glass-panel rounded-3xl p-6">
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
                            className="inline-flex w-full items-center justify-center gap-2 rounded-3xl bg-accentTeal px-4 py-3 text-sm font-semibold text-darkBg transition hover:bg-cyan-500"
                            disabled={tailorLoading || selectedResumeId === null}
                            onClick={() => selectedResumeId !== null && handleTailor(selectedResumeId)}
                        >
                            {tailorLoading ? 'Generating feedback...' : 'Generate Tailored Feedback'}
                            <ArrowRight className="h-4 w-4" />
                        </button>

                        {tailoredResult ? (
                            <div className="rounded-3xl border border-cardBorder bg-slate-950/80 p-4">
                                <div className="mb-3 flex items-center gap-2 text-slate-200">
                                    <Check className="h-4 w-4 text-emerald-400" /> <span>Tailoring complete</span>
                                </div>
                                <p className="text-sm leading-6 text-slate-300">{tailoredResult}</p>
                            </div>
                        ) : (
                            <div className="rounded-3xl border border-dashed border-slate-700 bg-slate-950/70 p-4 text-sm text-slate-400">
                                Select a resume and paste a job description to receive guidance.
                            </div>
                        )}
                    </div>
                </aside>
            </div>
        </div>
    );
}
