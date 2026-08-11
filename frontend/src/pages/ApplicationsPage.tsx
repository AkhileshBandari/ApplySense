import { useEffect, useState } from 'react';
import {
    Plus,
    MessageSquare,
    X,
    MapPin,
    Building,
    RefreshCw,
    Play,
    AlertCircle,
    CheckCircle2,
    Settings,
} from 'lucide-react';
import api from '../services/api';

interface ApplicationItem {
    id: number;
    title: string;
    company: string;
    location: string;
    portal_type: string;
    status: string;
    preparation_status: string;
    submission_status: string;
    match_score: number;
    applied_at: string;
    notes: any[];
    interviews: any[];
    questions: any[];
    policy_decisions: any[];
}

export default function ApplicationsPage() {
    const [apps, setApps] = useState<ApplicationItem[]>([]);
    const [showAddModal, setShowAddModal] = useState(false);
    const [newUrl, setNewUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [refreshing, setRefreshing] = useState(false);

    // Selection details
    const [selectedApp, setSelectedApp] = useState<ApplicationItem | null>(null);
    const [newNote, setNewNote] = useState('');

    const loadApplications = async () => {
        setRefreshing(true);
        try {
            const { data } = await api.get('/api/applications/tracker/');
            if (data?.length) {
                setApps(data.map((item: any) => ({
                    id: item.id,
                    title: item.job_details?.title ?? item.role ?? 'Untitled',
                    company: item.job_details?.company ?? item.company ?? 'Unknown',
                    location: item.job_details?.location ?? 'Remote',
                    portal_type: item.job_details?.portal_type ?? item.application_provider ?? 'Other',
                    status: item.status,
                    preparation_status: item.preparation_status,
                    submission_status: item.submission_status,
                    match_score: item.match_score ?? 0,
                    applied_at: item.applied_at ?? new Date().toISOString(),
                    notes: (item.notes ?? []).map((note: any) => ({ id: note.id, date: note.created_at?.split('T')[0] ?? '', content: note.content })),
                    interviews: (item.interviews ?? []).map((interview: any) => ({ id: interview.id, stage: interview.stage, date: interview.scheduled_at?.split('T')[0] ?? '' })),
                    questions: item.questions ?? [],
                    policy_decisions: item.policy_decisions ?? [],
                })));
                setMessage('Applications refreshed.');
            } else {
                setApps([]);
                setMessage('No applications found.');
            }
        } catch {
            setMessage('Unable to load applications.');
        } finally {
            setRefreshing(false);
        }
    };

    useEffect(() => {
        loadApplications();
    }, []);

    // Condensed Kanban for view
    const statusGroups = [
        { label: 'Draft', statuses: ['DRAFT', 'PREPARING', 'REVIEW_REQUIRED', 'READY_TO_SUBMIT', 'Saved'] },
        { label: 'Submitted', statuses: ['SUBMITTING', 'SUBMITTED', 'APPLICATION_FAILED', 'Applied'] },
        { label: 'In Progress', statuses: ['UNDER_REVIEW', 'ASSESSMENT', 'INTERVIEW', 'FINAL_ROUND', 'Under Review', 'Interview'] },
        { label: 'Closed', statuses: ['OFFER', 'REJECTED', 'ACCEPTED', 'DECLINED', 'WITHDRAWN', 'Offer', 'Rejected'] }
    ];

    const handleScrapeJob = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newUrl) return;
        setLoading(true);
        setMessage('');

        try {
            const { data } = await api.post('/api/jobs/parse/', { url: newUrl });
            const jobId = data.job_id ?? data.id;
            const job = data.job_details ?? data.job ?? {};
            
            const applicationResponse = await api.post('/api/applications/tracker/', {
                job: jobId,
                status: 'DRAFT',
                match_score: Math.round(job.match_score ?? data.match_result?.score ?? 0),
            });

            const created = applicationResponse.data;
            const newApp: ApplicationItem = {
                id: created.id,
                title: created.job_details?.title ?? job.title ?? 'Untitled',
                company: created.job_details?.company ?? job.company ?? 'Unknown',
                location: created.job_details?.location ?? job.location ?? 'Remote',
                portal_type: created.job_details?.portal_type ?? job.portal_type ?? 'Other',
                status: created.status ?? 'DRAFT',
                preparation_status: created.preparation_status ?? '',
                submission_status: created.submission_status ?? '',
                match_score: created.match_score ?? 0,
                applied_at: created.applied_at ?? new Date().toISOString(),
                notes: [],
                interviews: [],
                questions: [],
                policy_decisions: [],
            };
            setApps(prev => [newApp, ...prev]);
            setMessage('Application added.');
        } catch (err) {
            console.error('Network error while parsing job:', err);
            setMessage('Unable to add application.');
        }
        setLoading(false);
        setNewUrl('');
        setShowAddModal(false);
    };

    const handlePrepareApplication = async (appId: number) => {
        setLoading(true);
        try {
            const { data } = await api.post(`/api/applications/tracker/${appId}/prepare/`);
            setMessage('Preparation initiated.');
            // Reload to get questions and updated status
            await loadApplications();
            if (selectedApp?.id === appId) {
                setSelectedApp(data.application);
            }
        } catch (err: any) {
            setMessage(err.response?.data?.error || 'Failed to prepare application.');
        }
        setLoading(false);
    };

    const handleTransition = async (appId: number, newStatus: string) => {
        try {
            const { data } = await api.post(`/api/applications/tracker/${appId}/transition/`, { status: newStatus });
            
            setApps(prev => prev.map(a => (a.id === appId ? { ...a, status: data.status } : a)));
            if (selectedApp?.id === appId) {
                setSelectedApp(prev => (prev ? { ...prev, status: data.status } : prev));
            }
            setMessage(`Status updated to ${data.status}.`);
        } catch (err: any) {
            setMessage(err.response?.data?.error || 'Unable to update status.');
        }
    };

    const handleAddNote = async () => {
        if (!selectedApp || !newNote.trim()) return;
        try {
            const { data } = await api.post('/api/applications/notes/', { application: selectedApp.id, content: newNote.trim() });
            const note = { id: data.id, date: data.created_at?.split('T')[0] ?? '', content: data.content };
            setApps(prev => prev.map(a => (a.id === selectedApp.id ? { ...a, notes: [...a.notes, note] } : a)));
            setSelectedApp(prev => (prev ? { ...prev, notes: [...prev.notes, note] } : prev));
            setNewNote('');
            setMessage('Note added.');
        } catch {
            setMessage('Unable to add note.');
        }
    };

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold">Applications</h2>
                <div className="flex gap-2">
                    <button
                        onClick={() => void loadApplications()}
                        className="flex items-center gap-1 px-3 py-2 bg-cardHover text-white rounded-md font-semibold hover:opacity-90 transition-opacity"
                    >
                        <RefreshCw size={18} className={refreshing ? 'animate-spin' : ''} /> Refresh
                    </button>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="flex items-center gap-1 px-3 py-2 bg-accentTeal text-darkBg rounded-md font-semibold hover:opacity-90 transition-opacity"
                    >
                        <Plus size={18} /> Add Job
                    </button>
                </div>
            </div>

            {message ? <p className="text-sm text-emerald-400">{message}</p> : null}

            {/* Add Modal */}
            {showAddModal && (
                <div className="bg-cardBorder rounded-lg p-4">
                    <form onSubmit={handleScrapeJob} className="flex space-x-2">
                        <input
                            className="flex-1 p-2 bg-darkBg text-primaryText rounded border border-gray-600"
                            placeholder="Paste job URL..."
                            value={newUrl}
                            onChange={e => setNewUrl(e.target.value)}
                            data-testid="job-url-input"
                        />
                        <button type="submit" disabled={loading} className="px-4 py-2 bg-accentTeal text-darkBg rounded font-semibold" data-testid="add-job-button">
                            {loading ? 'Adding...' : 'Add'}
                        </button>
                        <button type="button" onClick={() => setShowAddModal(false)} className="px-3 py-2 bg-gray-600 rounded">
                            Cancel
                        </button>
                    </form>
                </div>
            )}

            {/* Kanban Columns */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {statusGroups.map(group => (
                    <div key={group.label} className="bg-cardBorder rounded-lg p-3 min-h-[300px]">
                        <h3 className="font-semibold mb-3 text-sm text-gray-300">{group.label}</h3>
                        <div className="space-y-2">
                            {apps
                                .filter(app => group.statuses.includes(app.status))
                                .map(app => (
                                    <div
                                        key={app.id}
                                        data-testid={`app-card-${app.id}`}
                                        className="bg-darkBg p-3 rounded-md cursor-pointer hover:bg-cardHover transition-colors border border-transparent hover:border-accentTeal/30"
                                        onClick={() => setSelectedApp(app)}
                                    >
                                        <div className="flex justify-between items-start">
                                            <span className="font-medium text-sm leading-tight">{app.title}</span>
                                            <span className="text-xs text-accentTeal font-bold ml-1">{app.match_score}%</span>
                                        </div>
                                        <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
                                            <Building size={10} /> {app.company}
                                        </p>
                                        <div className="flex items-center justify-between mt-2">
                                            <span className="text-[10px] bg-gray-700 px-2 py-0.5 rounded">{app.status}</span>
                                            {app.status === 'REVIEW_REQUIRED' && (
                                                <AlertCircle size={14} className="text-amber-500" />
                                            )}
                                        </div>
                                    </div>
                                ))}
                        </div>
                    </div>
                ))}
            </div>

            {/* Detail Panel */}
            {selectedApp && (
                <div className="bg-cardBorder rounded-lg p-5 border border-gray-600 mt-6" data-testid="app-details">
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h3 className="text-xl font-bold">{selectedApp.title}</h3>
                            <p className="text-gray-400 flex items-center gap-2 mt-1">
                                <Building size={14} /> {selectedApp.company} <MapPin size={14} className="ml-2" /> {selectedApp.location}
                            </p>
                        </div>
                        <button onClick={() => setSelectedApp(null)} className="text-gray-400 hover:text-white" data-testid="close-details">
                            <X size={20} />
                        </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            {/* State Management */}
                            <div className="bg-darkBg rounded p-4 mb-4">
                                <h4 className="font-semibold mb-3 flex items-center gap-2 border-b border-gray-700 pb-2">
                                    <Settings size={16} /> Lifecycle Controls
                                </h4>
                                <div className="space-y-3">
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-gray-400">Current Phase:</span>
                                        <span className="text-sm font-bold text-white bg-gray-700 px-2 py-1 rounded">{selectedApp.status}</span>
                                    </div>
                                    
                                    {(selectedApp.status === 'DRAFT' || selectedApp.status === 'Saved') && (
                                        <button 
                                            onClick={() => handlePrepareApplication(selectedApp.id)}
                                            disabled={loading}
                                            className="w-full py-2 bg-accentTeal text-darkBg font-bold rounded flex items-center justify-center gap-2 hover:opacity-90 transition"
                                            data-testid="prepare-btn"
                                        >
                                            <Play size={16} /> Prepare Application
                                        </button>
                                    )}

                                    {selectedApp.status === 'REVIEW_REQUIRED' && (
                                        <div className="bg-amber-900/30 border border-amber-700 p-3 rounded">
                                            <p className="text-sm text-amber-200 flex items-center gap-2 mb-2">
                                                <AlertCircle size={16} /> Missing or unverified answers require your review.
                                            </p>
                                            
                                            {selectedApp.policy_decisions && selectedApp.policy_decisions.length > 0 && (
                                                <div className="mt-2 mb-3 p-2 bg-gray-800 rounded border border-gray-700 text-xs text-gray-300">
                                                    <strong>Policy Decision:</strong> {selectedApp.policy_decisions[selectedApp.policy_decisions.length - 1].decision}
                                                    <br/>
                                                    <strong>Reasons:</strong> {selectedApp.policy_decisions[selectedApp.policy_decisions.length - 1].reason_codes.join(', ')}
                                                </div>
                                            )}
                                            
                                            <button 
                                                onClick={() => handleTransition(selectedApp.id, 'READY_TO_SUBMIT')}
                                                className="w-full py-1.5 bg-amber-600 text-white text-sm font-bold rounded hover:bg-amber-500 transition"
                                                data-testid="mark-ready-btn"
                                            >
                                                Mark Ready
                                            </button>
                                        </div>
                                    )}

                                    {selectedApp.status === 'READY_TO_SUBMIT' && (
                                        <button 
                                            onClick={() => handleTransition(selectedApp.id, 'SUBMITTED')}
                                            className="w-full py-2 bg-emerald-600 text-white font-bold rounded flex items-center justify-center gap-2 hover:bg-emerald-500 transition"
                                        >
                                            <CheckCircle2 size={16} /> Mark as Submitted
                                        </button>
                                    )}

                                </div>
                            </div>
                            
                            {/* Questions Section */}
                            {selectedApp.questions && selectedApp.questions.length > 0 && (
                                <div className="bg-darkBg rounded p-4 mb-4">
                                    <h4 className="font-semibold mb-3 border-b border-gray-700 pb-2">Questions</h4>
                                    <div className="space-y-3 max-h-60 overflow-y-auto pr-2">
                                        {selectedApp.questions.map((q: any) => (
                                            <div key={q.id} className="border border-gray-700 p-2 rounded">
                                                <p className="text-sm font-medium">{q.question_text}</p>
                                                <p className={`text-xs mt-1 ${!q.answer ? 'text-amber-500' : 'text-emerald-400'}`}>
                                                    {q.answer ? `Ans: ${q.answer}` : 'Requires Answer'}
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                        </div>

                        <div>
                            {/* Notes */}
                            <div className="bg-darkBg rounded p-4 h-full flex flex-col">
                                <h4 className="font-semibold mb-3 flex items-center gap-2 border-b border-gray-700 pb-2">
                                    <MessageSquare size={16} /> Notes
                                </h4>
                                <div className="flex-1 overflow-y-auto mb-3 space-y-2">
                                    {selectedApp.notes.map(note => (
                                        <div key={note.id} className="bg-gray-800 p-2 rounded text-sm">
                                            <span className="text-gray-400 text-xs block mb-1">{note.date}</span>
                                            <p>{note.content}</p>
                                        </div>
                                    ))}
                                </div>
                                <div className="flex gap-2 mt-auto">
                                    <input
                                        className="flex-1 p-2 bg-gray-800 rounded border border-gray-600 text-sm"
                                        placeholder="Add a note..."
                                        value={newNote}
                                        onChange={e => setNewNote(e.target.value)}
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter') {
                                                e.preventDefault();
                                                handleAddNote();
                                            }
                                        }}
                                    />
                                    <button onClick={handleAddNote} className="px-3 py-1 bg-gray-600 rounded text-sm hover:bg-gray-500">
                                        Add
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
