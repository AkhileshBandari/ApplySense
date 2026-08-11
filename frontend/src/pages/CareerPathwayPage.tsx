import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface CareerPath {
    id: number;
    canonical_role_name: string;
}

interface Scenario {
    id: number;
    name: string;
    target_path: CareerPath;
    status: string;
    baseline_snapshot: any;
    simulated_snapshot: any;
}

const CareerPathwayPage: React.FC = () => {
    const [scenarios, setScenarios] = useState<Scenario[]>([]);
    const [recommendations, setRecommendations] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchData = async () => {
            try {
                // We're just bootstrapping the skeleton here for now
                const recRes = await axios.get('/api/career-pathways/recommendations/', {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
                });
                setRecommendations(recRes.data);

                const scRes = await axios.get('/api/career-pathways/scenarios/', {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
                });
                setScenarios(scRes.data);
            } catch (err) {
                setError('Failed to load career pathways data. INSUFFICIENT_DATA');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) return <div>Loading...</div>;
    if (error) return <div>{error}</div>;

    return (
        <div className="career-pathway-page">
            <h1>Career Pathway Simulation & Scenario Planning</h1>
            
            <section className="recommendations-section">
                <h2>Recommended Paths</h2>
                {recommendations.length === 0 ? (
                    <p>No paths available</p>
                ) : (
                    <ul>
                        {recommendations.map((r, i) => (
                            <li key={i}>
                                <strong>{r.role_name}</strong> - Readiness: {r.overall_readiness}/100 
                                <span className={`badge ${r.classification}`}>{r.classification}</span>
                                <p>Skill Score: {r.skill_score} | Interview Score: {r.interview_score}</p>
                            </li>
                        ))}
                    </ul>
                )}
            </section>
            
            <section className="scenarios-section">
                <h2>Your Scenarios</h2>
                <button>Create New Scenario</button>
                {scenarios.map((sc, i) => (
                    <div key={i} className="scenario-card">
                        <h3>{sc.name} ({sc.status})</h3>
                        <p>Target: {sc.target_path ? sc.target_path.canonical_role_name : 'Custom'}</p>
                        <button>Simulate Delta</button>
                    </div>
                ))}
            </section>
        </div>
    );
};

export default CareerPathwayPage;
