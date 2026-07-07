import { useState } from 'react';
import { initialApplications, MockApplication } from '../utils/mockData';
import {
    Plus,
    MessageSquare,
    Calendar,
    X,
    MapPin,
    Building,
} from 'lucide-react';

interface ApplicationsPageProps {
    apiMode: 'mock' | 'live';
}

export default function ApplicationsPage({ apiMode }: ApplicationsPageProps) {
    const [apps, setApps] = useState<MockApplication[]>(initialApplications);
    const [showAddModal, setShowAddModal] = useState(false);
    const [newUrl, setNewUrl] = useState('');
    const [loading, setLoading] = useState(false);

    // Selection details
    const [selectedApp, setSelectedApp] = useState<MockApplication | null>(null);
    const [newNote, setNewNote] = useState('');

    // Kanban status categories
    const statuses = ['Saved', 'Applied', 'Under Review', 'Interview', 'Offer', 'Rejected'];

    const handleScrapeJob = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newUrl) return;
        setLoading(true);

        if (apiMode === 'live') {
            try {
                const response = await fetch('http://localhost:8000/api/jobs/parse/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${localStorage.getItem('applysense_token')}`,
                    },
                    body: JSON.stringify({ url: newUrl }),
                });
                const data = await response.json();
                if (response.ok) {
                    const newApp: MockApplication = {
                        id: Date.now(),
                        title: data.job?.title || 'Untitled',
                        company: data.job?.company || 'Unknown',
                        location: data.job?.location || 'Remote',
                        portal_type: data.job?.portal_type || 'Other',
                        status: 'Saved',
                        match_score: data.job?.match_score ?? 0,
                        applied_at: new Date().toISOString(),
                        notes: [],
                        interviews: [],
                    };
                    setApps(prev => [newApp, ...prev]);
                } else {
                    console.error('Job parse failed:', data);
                }
            } catch (err) {
                console.error('Network error while parsing job:', err);
                // Fallback to mock
                addMockApp();
            }
        } else {
            addMockApp();
        }
        setLoading(false);
        setNewUrl('');
        setShowAddModal(false);
    };

    const addMockApp = () => {
        const mockApp: MockApplication = {
            id: Date.now(),
            title: 'Mock Job Title',
            company: 'Mock Company',
            location: 'Remote',
            portal_type: 'LinkedIn',
            status: 'Saved',
            match_score: 75,
            applied_at: new Date().toISOString(),
            notes: [],
            interviews: [],
        };
        setApps(prev => [mockApp, ...prev]);
    };

    const handleAddNote = () => {
        if (!selectedApp || !newNote.trim()) return;
        const note = { id: Date.now(), date: new Date().toISOString().split('T')[0], content: newNote.trim() };
        setApps(prev =>
            prev.map(a => (a.id === selectedApp.id ? { ...a, notes: [...a.notes, note] } : a))
        );
        setSelectedApp(prev => (prev ? { ...prev, notes: [...prev.notes, note] } : prev));
        setNewNote('');
    };

    const handleStatusChange = (appId: number, newStatus: string) => {
        setApps(prev => prev.map(a => (a.id === appId ? { ...a, status: newStatus } : a)));
        if (selectedApp?.id === appId) {
            setSelectedApp(prev => (prev ? { ...prev, status: newStatus } : prev));
        }
    };

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold">Applications</h2>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="flex items-center gap-1 px-3 py-2 bg-accentTeal text-darkBg rounded-md font-semibold hover:opacity-90 transition-opacity"
                >
                    <Plus size={18} /> Add Job
                </button>
            </div>

            {/* Add Modal */}
            {showAddModal && (
                <div className="bg-cardBorder rounded-lg p-4">
                    <form onSubmit={handleScrapeJob} className="flex space-x-2">
                        <input
                            className="flex-1 p-2 bg-darkBg text-primaryText rounded border border-gray-600"
                            placeholder="Paste job URL or leave empty for mock"
                            value={newUrl}
                            onChange={e => setNewUrl(e.target.value)}
                        />
                        <button type="submit" disabled={loading} className="px-4 py-2 bg-accentTeal text-darkBg rounded font-semibold">
                            {loading ? 'Adding...' : 'Add'}
                        </button>
                        <button type="button" onClick={() => setShowAddModal(false)} className="px-3 py-2 bg-gray-600 rounded">
                            Cancel
                        </button>
                    </form>
                </div>
            )}

            {/* Kanban Columns */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                {statuses.map(status => (
                    <div key={status} className="bg-cardBorder rounded-lg p-3 min-h-[200px]">
                        <h3 className="font-semibold mb-3 text-sm text-gray-300">{status}</h3>
                        <div className="space-y-2">
                            {apps
                                .filter(app => app.status === status)
                                .map(app => (
                                    <div
                                        key={app.id}
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
                                        <p className="text-xs text-gray-500 flex items-center gap-1">
                                            <MapPin size={10} /> {app.location}
                                        </p>
                                    </div>
                                ))}
                        </div>
                    </div>
                ))}
            </div>

            {/* Detail Panel */}
            {selectedApp && (
                <div className="bg-cardBorder rounded-lg p-4 border border-gray-600">
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h3 className="text-xl font-bold">{selectedApp.title}</h3>
                            <p className="text-gray-400">
                                {selectedApp.company} · {selectedApp.location}
                            </p>
                        </div>
                        <button onClick={() => setSelectedApp(null)} className="text-gray-400 hover:text-white">
                            <X size={20} />
                        </button>
                    </div>

                    {/* Status Changer */}
                    <div className="flex flex-wrap gap-2 mb-4">
                        {statuses.map(s => (
                            <button
                                key={s}
                                onClick={() => handleStatusChange(selectedApp.id, s)}
                                className={`px-2 py-1 rounded text-xs font-medium ${selectedApp.status === s ? 'bg-accentTeal text-darkBg' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                    }`}
                            >
                                {s}
                            </button>
                        ))}
                    </div>

                    {/* Notes */}
                    <div>
                        <h4 className="font-semibold mb-2 flex items-center gap-1">
                            <MessageSquare size={16} /> Notes
                        </h4>
                        {selectedApp.notes.map(note => (
                            <div key={note.id} className="bg-darkBg p-2 rounded mb-1 text-sm">
                                <span className="text-gray-500 text-xs">{note.date}</span>
                                <p>{note.content}</p>
                            </div>
                        ))}
                        <div className="flex gap-2 mt-2">
                            <input
                                className="flex-1 p-2 bg-darkBg rounded border border-gray-600 text-sm"
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
                            <button onClick={handleAddNote} className="px-3 py-1 bg-gray-600 rounded text-sm">
                                Add
                            </button>
                        </div>
                    </div>

                    {/* Interviews */}
                    {selectedApp.interviews.length > 0 && (
                        <div className="mt-4">
                            <h4 className="font-semibold mb-2 flex items-center gap-1">
                                <Calendar size={16} /> Interviews
                            </h4>
                            {selectedApp.interviews.map(iv => (
                                <div key={iv.id} className="bg-darkBg p-2 rounded mb-1 text-sm flex justify-between">
                                    <span>{iv.stage}</span>
                                    <span className="text-gray-400">{iv.date}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
