import { useState, useEffect } from 'react';
import {
    Save,
    Mail,
    Phone,
    MapPin,
    Globe,
    Linkedin,
    Github,
    User,
    Briefcase,
    GraduationCap
} from 'lucide-react';
import api from '../services/api';
import CompletenessBar from '../components/profile/CompletenessBar';
import PendingImports from '../components/profile/PendingImports';

interface ProfileState {
    name: string;
    email: string;
    phone: string;
    location: string;
    linkedin: string;
    github: string;
    portfolio: string;
    bio: string;
    professional_headline: string;
    career_goals: string;
    skills: any[];
    experience: any[];
    education: any[];
    projects: any[];
    certifications: any[];
    languages: any[];
}

const initialProfile: ProfileState = {
    name: '', email: '', phone: '', location: '',
    linkedin: '', github: '', portfolio: '', bio: '',
    professional_headline: '', career_goals: '',
    skills: [], experience: [], education: [], projects: [], certifications: [], languages: []
};

export default function ProfilePage() {
    const [profile, setProfile] = useState<ProfileState>(initialProfile);
    const [message, setMessage] = useState('');
    const [saving, setSaving] = useState(false);
    const [loading, setLoading] = useState(false);
    const [refreshTrigger, setRefreshTrigger] = useState(0);

    const loadProfile = () => {
        setLoading(true);
        api.get('/api/profile/')
            .then(({ data }: { data: any }) => {
                if (!data.id) return;
                setProfile({
                    name: data.name || '',
                    email: data.user_email || '',
                    phone: data.phone || '',
                    location: data.location || '',
                    linkedin: data.linkedin_url || '',
                    github: data.github_url || '',
                    portfolio: data.portfolio_url || '',
                    bio: data.bio || '',
                    professional_headline: data.professional_headline || '',
                    career_goals: data.career_goals || '',
                    skills: data.skills || [],
                    experience: data.experiences || [],
                    education: data.educations || [],
                    projects: data.projects || [],
                    certifications: data.certifications || [],
                    languages: data.languages || [],
                });
            })
            .catch((err: unknown) => {
                console.error('Failed to fetch profile:', err);
                setMessage('Unable to load profile from the server.');
            })
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        loadProfile();
    }, [refreshTrigger]);

    const handleSave = async () => {
        const payload = {
            name: profile.name,
            phone: profile.phone,
            location: profile.location,
            linkedin_url: profile.linkedin,
            github_url: profile.github,
            portfolio_url: profile.portfolio,
            bio: profile.bio,
            professional_headline: profile.professional_headline,
            career_goals: profile.career_goals,
        };

        setSaving(true);
        setMessage('');
        try {
            await api.patch('/api/profile/', payload);
            setMessage('Profile updated.');
            setRefreshTrigger(prev => prev + 1);
        } catch (err) {
            console.error(err);
            setMessage('Unable to update profile.');
        } finally {
            setSaving(false);
        }
    };

    const triggerRefresh = () => setRefreshTrigger(prev => prev + 1);

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                    <div className="inline-flex items-center gap-2 rounded-full bg-cardHover px-3 py-1 text-sm font-semibold text-white">
                        <User className="h-4 w-4" /> Career Profile
                    </div>
                    <h1 className="mt-4 text-3xl font-semibold text-white">Your Professional Identity</h1>
                    <p className="mt-2 max-w-2xl text-sm text-slate-300">
                        Manage your verified career facts. 
                    </p>
                </div>
            </div>

            <CompletenessBar refreshTrigger={refreshTrigger} />
            <PendingImports onReviewComplete={triggerRefresh} />

            <div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
                {/* Main Content */}
                <div className="space-y-6">
                    <section className="glass-panel rounded-3xl p-6">
                        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                            <User className="w-5 h-5 text-accentTeal" /> Core Identity
                        </h2>
                        {loading && <p className="text-sm text-slate-400">Loading...</p>}
                        
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">Full Name</label>
                                <input
                                    className="w-full rounded-xl border border-cardBorder bg-slate-900/50 p-3 text-sm text-slate-200 outline-none transition focus:border-cyan-500"
                                    value={profile.name}
                                    onChange={e => setProfile({ ...profile, name: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">Professional Headline</label>
                                <input
                                    className="w-full rounded-xl border border-cardBorder bg-slate-900/50 p-3 text-sm text-slate-200 outline-none transition focus:border-cyan-500"
                                    placeholder="e.g. Senior Frontend Engineer"
                                    value={profile.professional_headline}
                                    onChange={e => setProfile({ ...profile, professional_headline: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1">Bio / Summary</label>
                                <textarea
                                    className="w-full rounded-xl border border-cardBorder bg-slate-900/50 p-3 text-sm text-slate-200 outline-none transition focus:border-cyan-500 min-h-[100px]"
                                    value={profile.bio}
                                    onChange={e => setProfile({ ...profile, bio: e.target.value })}
                                />
                            </div>
                        </div>
                    </section>

                    {/* Verified Facts Read-Only View */}
                    <section className="glass-panel rounded-3xl p-6">
                        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                            <Briefcase className="w-5 h-5 text-accentTeal" /> Verified Experience
                        </h2>
                        {profile.experience.length === 0 ? (
                            <p className="text-sm text-slate-400">No verified experience. Upload a resume to add some.</p>
                        ) : (
                            <div className="space-y-4">
                                {profile.experience.map(exp => (
                                    <div key={exp.id} className="border-l-2 border-slate-700 pl-4 py-1">
                                        <h3 className="font-semibold text-white">{exp.role}</h3>
                                        <p className="text-sm text-slate-300">{exp.company} • {exp.location}</p>
                                        <p className="text-xs text-slate-400 mt-1">{exp.start_date} to {exp.is_current ? 'Present' : exp.end_date}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </section>

                    <section className="glass-panel rounded-3xl p-6">
                        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                            <GraduationCap className="w-5 h-5 text-accentTeal" /> Verified Education
                        </h2>
                        {profile.education.length === 0 ? (
                            <p className="text-sm text-slate-400">No verified education.</p>
                        ) : (
                            <div className="space-y-4">
                                {profile.education.map(edu => (
                                    <div key={edu.id} className="border-l-2 border-slate-700 pl-4 py-1">
                                        <h3 className="font-semibold text-white">{edu.degree} in {edu.field_of_study}</h3>
                                        <p className="text-sm text-slate-300">{edu.institution}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </section>
                </div>

                {/* Sidebar */}
                <aside className="space-y-6">
                    <section className="glass-panel rounded-3xl p-6">
                        <h2 className="text-lg font-semibold text-white mb-4">Contact Info</h2>
                        <div className="space-y-3">
                            <div>
                                <label className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-1">
                                    <Mail size={14} /> Email (Read Only)
                                </label>
                                <input
                                    className="w-full rounded-lg border border-cardBorder bg-slate-900/50 p-2 text-sm text-slate-400"
                                    value={profile.email}
                                    disabled
                                />
                            </div>
                            <div>
                                <label className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-1">
                                    <Phone size={14} /> Phone
                                </label>
                                <input
                                    className="w-full rounded-lg border border-cardBorder bg-slate-900/50 p-2 text-sm text-slate-200 outline-none transition focus:border-cyan-500"
                                    value={profile.phone}
                                    onChange={e => setProfile({ ...profile, phone: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-1">
                                    <MapPin size={14} /> Location
                                </label>
                                <input
                                    className="w-full rounded-lg border border-cardBorder bg-slate-900/50 p-2 text-sm text-slate-200 outline-none transition focus:border-cyan-500"
                                    value={profile.location}
                                    onChange={e => setProfile({ ...profile, location: e.target.value })}
                                />
                            </div>
                        </div>
                    </section>

                    <section className="glass-panel rounded-3xl p-6">
                        <h2 className="text-lg font-semibold text-white mb-4">Links</h2>
                        <div className="space-y-3">
                            <div>
                                <label className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-1">
                                    <Linkedin size={14} /> LinkedIn
                                </label>
                                <input
                                    className="w-full rounded-lg border border-cardBorder bg-slate-900/50 p-2 text-sm text-slate-200 outline-none transition focus:border-cyan-500"
                                    value={profile.linkedin}
                                    onChange={e => setProfile({ ...profile, linkedin: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-1">
                                    <Github size={14} /> GitHub
                                </label>
                                <input
                                    className="w-full rounded-lg border border-cardBorder bg-slate-900/50 p-2 text-sm text-slate-200 outline-none transition focus:border-cyan-500"
                                    value={profile.github}
                                    onChange={e => setProfile({ ...profile, github: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-1">
                                    <Globe size={14} /> Portfolio
                                </label>
                                <input
                                    className="w-full rounded-lg border border-cardBorder bg-slate-900/50 p-2 text-sm text-slate-200 outline-none transition focus:border-cyan-500"
                                    value={profile.portfolio}
                                    onChange={e => setProfile({ ...profile, portfolio: e.target.value })}
                                />
                            </div>
                        </div>
                    </section>

                    <div className="flex flex-col gap-3 pt-4">
                        <button
                            className="w-full p-3 bg-accentTeal text-darkBg font-semibold rounded-xl flex items-center justify-center transition hover:bg-cyan-500"
                            onClick={handleSave}
                            disabled={saving}
                        >
                            <Save size={18} className="mr-2" /> {saving ? 'Saving…' : 'Save Changes'}
                        </button>
                        {message && <p className="text-center text-sm text-emerald-400">{message}</p>}
                    </div>
                </aside>
            </div>
        </div>
    );
}
