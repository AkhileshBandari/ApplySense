import { useState, useEffect } from 'react';
import { initialProfile, MockProfile } from '../utils/mockData';
import {
    Save,
    Plus,
    Trash2,
    Mail,
    Phone,
    MapPin,
    Globe,
    Linkedin,
    Github,
} from 'lucide-react';

type ProfilePageProps = {
    apiMode: 'mock' | 'live';
};

export default function ProfilePage({ apiMode }: ProfilePageProps) {
    const [profile, setProfile] = useState<MockProfile>(() => {
        const cached = localStorage.getItem('applysense_mock_profile');
        return cached ? JSON.parse(cached) : initialProfile;
    });

    const [newSkill, setNewSkill] = useState('');
    const [message, setMessage] = useState('');

    // Persist mock profile to localStorage
    useEffect(() => {
        if (apiMode === 'mock') {
            localStorage.setItem('applysense_mock_profile', JSON.stringify(profile));
        }
    }, [profile, apiMode]);

    // Live mode – fetch from backend when component mounts or apiMode changes
    useEffect(() => {
        if (apiMode === 'live') {
            fetch('http://localhost:8000/api/profile/', {
                headers: {
                    Authorization: `Bearer ${localStorage.getItem('applysense_token')}`,
                },
            })
                .then(res => res.json())
                .then(data => {
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
                        skills: data.skills?.map((s: any) => s.name) ?? [],
                        experience: data.experiences?.map((e: any) => ({
                            company: e.company,
                            role: e.role,
                            period: `${e.start_date} - ${e.is_current ? 'Present' : e.end_date}`,
                            description: e.description,
                        })) ?? [],
                        education: data.educations?.map((ed: any) => ({
                            school: ed.institution,
                            degree: ed.degree,
                            year: ed.end_date ?? '',
                        })) ?? [],
                    });
                })
                .catch(err => console.error('Failed to fetch profile:', err));
        }
    }, [apiMode]);

    // ----- UI helpers -----
    const handleAddSkill = () => {
        if (newSkill.trim()) {
            setProfile(prev => ({
                ...prev,
                skills: [...prev.skills, newSkill.trim()],
            }));
            setNewSkill('');
        }
    };

    const handleSave = () => {
        if (apiMode === 'live') {
            // TODO: POST/PATCH to backend endpoint
            console.log('Would save to backend');
        } else {
            setMessage('Mock profile saved locally');
        }
    };

    return (
        <div className="p-6 bg-darkBg text-primaryText rounded-lg shadow-lg">
            <h2 className="text-2xl font-bold mb-4">Profile</h2>
            {/* Simple display of profile fields – extend as needed */}
            <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                    <label className="block text-sm font-medium">Name</label>
                    <input
                        className="w-full p-2 bg-cardBorder text-primaryText rounded"
                        value={profile.name}
                        onChange={e => setProfile({ ...profile, name: e.target.value })}
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium">Email</label>
                    <input
                        className="w-full p-2 bg-cardBorder text-primaryText rounded"
                        value={profile.email}
                        onChange={e => setProfile({ ...profile, email: e.target.value })}
                    />
                </div>
                {/* Add more fields (phone, location, etc.) similar to above */}
            </div>

            {/* Skills section */}
            <div className="mb-4">
                <h3 className="text-lg font-semibold">Skills</h3>
                <ul className="list-disc list-inside mb-2">
                    {profile.skills.map((skill, idx) => (
                        <li key={idx}>{skill}</li>
                    ))}
                </ul>
                <div className="flex space-x-2">
                    <input
                        className="flex-1 p-2 bg-cardBorder text-primaryText rounded"
                        placeholder="New skill"
                        value={newSkill}
                        onChange={e => setNewSkill(e.target.value)}
                    />
                    <button className="p-2 bg-cardHover rounded" onClick={handleAddSkill}>
                        <Plus size={18} />
                    </button>
                </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">

                <div>
                    <label className="flex items-center gap-2 text-sm font-medium mb-1">
                        <Mail size={16} />
                        Email
                    </label>
                    <input
                        className="w-full p-2 bg-cardBorder text-primaryText rounded"
                        value={profile.email}
                        onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                    />
                </div>

                <div>
                    <label className="flex items-center gap-2 text-sm font-medium mb-1">
                        <Phone size={16} />
                        Phone
                    </label>
                    <input
                        className="w-full p-2 bg-cardBorder text-primaryText rounded"
                        value={profile.phone}
                        onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                    />
                </div>

                <div>
                    <label className="flex items-center gap-2 text-sm font-medium mb-1">
                        <MapPin size={16} />
                        Location
                    </label>
                    <input
                        className="w-full p-2 bg-cardBorder text-primaryText rounded"
                        value={profile.location}
                        onChange={(e) => setProfile({ ...profile, location: e.target.value })}
                    />
                </div>

                <div>
                    <label className="flex items-center gap-2 text-sm font-medium mb-1">
                        <Globe size={16} />
                        Portfolio
                    </label>
                    <input
                        className="w-full p-2 bg-cardBorder text-primaryText rounded"
                        value={profile.portfolio}
                        onChange={(e) => setProfile({ ...profile, portfolio: e.target.value })}
                    />
                </div>

                <div>
                    <label className="flex items-center gap-2 text-sm font-medium mb-1">
                        <Linkedin size={16} />
                        LinkedIn
                    </label>
                    <input
                        className="w-full p-2 bg-cardBorder text-primaryText rounded"
                        value={profile.linkedin}
                        onChange={(e) => setProfile({ ...profile, linkedin: e.target.value })}
                    />
                </div>

                <div>
                    <label className="flex items-center gap-2 text-sm font-medium mb-1">
                        <Github size={16} />
                        GitHub
                    </label>
                    <input
                        className="w-full p-2 bg-cardBorder text-primaryText rounded"
                        value={profile.github}
                        onChange={(e) => setProfile({ ...profile, github: e.target.value })}
                    />
                </div>

            </div>
            {/* Action buttons */}
            <div className="flex space-x-4">
                <button
                    className="p-2 bg-cardHover rounded flex items-center"
                    onClick={handleSave}
                >
                    <Save size={18} className="mr-1" /> Save
                </button>
                <button
                    className="p-2 bg-red-600 text-white rounded flex items-center"
                    onClick={() => setProfile(initialProfile)}
                >
                    <Trash2 size={18} className="mr-1" /> Reset
                </button>
            </div>

            {message && <p className="mt-2 text-green-400">{message}</p>}
        </div>
    );
}
