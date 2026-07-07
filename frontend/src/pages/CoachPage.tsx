import { useState } from 'react';
import { mockRoadmap, mockInterviewPrep } from '../utils/mockData';
import { Sparkles, CheckSquare, GraduationCap, FileQuestion, Lightbulb, Compass, Award } from 'lucide-react';


interface CoachPageProps {
    apiMode: 'mock' | 'live';
}

export default function CoachPage({ apiMode }: CoachPageProps) {
    const [targetRole, setTargetRole] = useState('Senior DevOps & Infrastructure Engineer');
    const [loading, setLoading] = useState(false);
    const [roadmap, setRoadmap] = useState(mockRoadmap);
    const [prep, setPrep] = useState(mockInterviewPrep);
    const [gapsChecked, setGapsChecked] = useState(false);

    const handleRunCoach = () => {
        if (!targetRole) return;
        setLoading(true);

        if (apiMode === 'live') {
            fetch('http://localhost:8000/api/coach/roadmap/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('applysense_token')}`,
                },
                body: JSON.stringify({ missing_skills: ['Kubernetes', 'Next.js'] }),
            })
                .then(res => res.json())
                .then(data => {
                    setRoadmap(data.length ? data : mockRoadmap);
                })
                .catch(() => setRoadmap(mockRoadmap));

            fetch('http://localhost:8000/api/coach/interview-prep/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('applysense_token')}`,
                },
                body: JSON.stringify({ resume_text: 'Senior Full Stack', job_description: targetRole }),
            })
                .then(res => res.json())
                .then(data => {
                    setPrep(data.behavioral_questions ? data : mockInterviewPrep);
                    setLoading(false);
                    setGapsChecked(true);
                })
                .catch(() => {
                    setPrep(mockInterviewPrep);
                    setLoading(false);
                    setGapsChecked(true);
                });
        } else {
            setRoadmap(mockRoadmap);
            setPrep(mockInterviewPrep);
            setLoading(false);
            setGapsChecked(true);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                <div>
                    <div className="inline-flex items-center gap-2 rounded-full bg-cardHover px-3 py-1 text-sm font-semibold text-white">
                        <Sparkles className="h-4 w-4" /> AI Coach
                    </div>
                    <h1 className="mt-4 text-3xl font-semibold text-white">Career Growth Assistant</h1>
                    <p className="mt-2 max-w-2xl text-sm text-slate-300">
                        Get a tailored upskilling roadmap, interview prep, and career guidance for your target role.
                    </p>
                </div>
                <button
                    onClick={handleRunCoach}
                    className="inline-flex items-center gap-2 rounded-3xl bg-accentTeal px-5 py-3 text-sm font-semibold text-darkBg transition hover:bg-cyan-500"
                >
                    {loading ? 'Generating advice...' : 'Run AI Coach'}
                    <Sparkles className="h-4 w-4" />
                </button>
            </div>

            <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
                <section className="glass-panel rounded-3xl p-6">
                    <div className="flex items-center gap-3 text-white">
                        <GraduationCap className="h-5 w-5" />
                        <h2 className="text-lg font-semibold">Target Role</h2>
                    </div>
                    <input
                        className="mt-4 w-full rounded-3xl border border-cardBorder bg-slate-950/80 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-500"
                        value={targetRole}
                        onChange={e => setTargetRole(e.target.value)}
                        placeholder="Enter the role you are targeting"
                    />

                    <div className="mt-8 space-y-4">
                        <div className="rounded-3xl border border-cardBorder bg-slate-950/80 p-5">
                            <div className="flex items-center gap-2 text-slate-200">
                                <Compass className="h-4 w-4" />
                                <span className="font-semibold">Roadmap</span>
                            </div>
                            <div className="mt-4 space-y-3">
                                {roadmap.map(item => (
                                    <div key={item.skill} className="rounded-3xl bg-slate-900/80 p-4">
                                        <div className="flex items-center justify-between gap-4">
                                            <div>
                                                <p className="text-sm text-slate-400">{item.skill}</p>
                                                <p className="mt-1 text-sm text-slate-500">Priority: {item.priority}</p>
                                            </div>
                                            <span className="rounded-full bg-slate-700 px-3 py-1 text-xs text-slate-200">
                                                {item.estimated_weeks} weeks
                                            </span>
                                        </div>
                                        <div className="mt-3 text-sm text-slate-300">
                                            {item.resources.join(', ')}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="rounded-3xl border border-cardBorder bg-slate-950/80 p-5">
                            <div className="flex items-center gap-2 text-slate-200">
                                <FileQuestion className="h-4 w-4" />
                                <span className="font-semibold">Interview Prep</span>
                            </div>
                            <div className="mt-4 space-y-3 text-sm text-slate-300">
                                <div>
                                    <p className="text-slate-400">Behavioral Questions</p>
                                    <ul className="list-disc space-y-2 pl-5">
                                        {prep.behavioral_questions.map((question, index) => (
                                            <li key={index}>{question}</li>
                                        ))}
                                    </ul>
                                </div>
                                <div>
                                    <p className="text-slate-400">Technical Focus</p>
                                    <ul className="list-disc space-y-2 pl-5">
                                        {prep.technical_questions.map((question, index) => (
                                            <li key={index}>{question}</li>
                                        ))}
                                    </ul>
                                </div>
                                <div>
                                    <p className="text-slate-400">Tips</p>
                                    <ul className="list-disc space-y-2 pl-5">
                                        {prep.tips.map((tip, index) => (
                                            <li key={index}>{tip}</li>
                                        ))}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                <aside className="glass-panel rounded-3xl p-6">
                    <div className="flex items-center gap-3 text-white">
                        <CheckSquare className="h-5 w-5" />
                        <h2 className="text-lg font-semibold">Progress Tracker</h2>
                    </div>
                    <div className="mt-6 space-y-4 text-slate-300">
                        <div className="rounded-3xl border border-cardBorder bg-slate-950/80 p-5">
                            <div className="flex items-center gap-2 text-slate-200">
                                <Lightbulb className="h-4 w-4" />
                                <span>Strengths</span>
                            </div>
                            <p className="mt-3 text-sm text-slate-300">Focus on cloud-native architectures, developer experience, and automated infrastructure workflows.</p>
                        </div>

                        <div className="rounded-3xl border border-cardBorder bg-slate-950/80 p-5">
                            <div className="flex items-center gap-2 text-slate-200">
                                <Award className="h-4 w-4" />
                                <span>Outcome</span>
                            </div>
                            <p className="mt-3 text-sm text-slate-300">Use your roadmap to improve interview readiness and secure the next step toward the target role.</p>
                        </div>

                        <div className="rounded-3xl border border-cardBorder bg-slate-950/80 p-5">
                            <div className="flex items-center gap-2 text-slate-200">
                                <Sparkles className="h-4 w-4" />
                                <span>{gapsChecked ? 'Gaps reviewed' : 'Gaps review pending'}</span>
                            </div>
                            <p className="mt-3 text-sm text-slate-300">
                                {gapsChecked
                                    ? 'Your current profile has been analyzed against the desired role.'
                                    : 'Run the AI Coach to identify training and interview gaps.'}
                            </p>
                        </div>
                    </div>
                </aside>
            </div>
        </div>
    );
}

