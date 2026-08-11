import React, { useEffect, useState } from 'react';
import { AlertTriangle, TrendingUp, Filter, Activity } from 'lucide-react';
import api from '../services/api';

const CareerOutcomesPage: React.FC = () => {
    const [funnel, setFunnel] = useState<any>(null);
    const [resumePerf, setResumePerf] = useState<any>(null);
    const [matchPerf, setMatchPerf] = useState<any>(null);
    const [recommendations, setRecommendations] = useState<any>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAll = async () => {
            try {
                const [fRes, rpRes, mpRes, recRes] = await Promise.all([
                    api.get('/api/career-outcomes/events/funnel/'),
                    api.get('/api/career-outcomes/events/resume_performance/'),
                    api.get('/api/career-outcomes/events/match_performance/'),
                    api.get('/api/career-outcomes/events/recommendations/')
                ]);
                setFunnel(fRes.data);
                setResumePerf(rpRes.data);
                setMatchPerf(mpRes.data);
                setRecommendations(recRes.data.recommendations);
            } catch (err: any) {
                setError(err.message || 'Failed to fetch outcomes');
            } finally {
                setLoading(false);
            }
        };
        fetchAll();
    }, []);

    if (loading) return <div className="p-8 text-center"><Activity className="animate-spin inline mr-2"/> Loading outcome intelligence...</div>;
    if (error) return <div className="p-8"><div className="bg-red-50 text-red-600 p-4 rounded-md flex items-center"><AlertTriangle className="mr-2"/> {error}</div></div>;

    return (
        <div className="space-y-6 max-w-7xl mx-auto pb-12">
            <div>
                <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                    <TrendingUp className="mr-2 h-6 w-6 text-blue-600" />
                    Career Outcome Intelligence
                </h1>
                <p className="mt-1 text-sm text-gray-500">
                    Evidence-backed closed-loop analysis of your application outcomes.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Funnel Metrics */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden md:col-span-2">
                    <div className="px-4 py-5 border-b border-gray-200 flex justify-between items-center bg-gray-50">
                        <h3 className="text-lg font-medium text-gray-900 flex items-center">
                            <Filter className="mr-2 h-5 w-5 text-gray-500"/> Application Funnel Metrics
                        </h3>
                        {funnel?.confidence && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                Confidence: {funnel.confidence}
                            </span>
                        )}
                    </div>
                    <div className="p-6">
                        {funnel?.status === 'INSUFFICIENT_SAMPLE' ? (
                            <div className="bg-yellow-50 text-yellow-800 p-4 rounded-md text-sm">
                                {funnel.message}
                            </div>
                        ) : (
                            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center divide-x divide-gray-100">
                                <div>
                                    <p className="text-sm font-medium text-gray-500">Applications</p>
                                    <p className="mt-1 text-3xl font-semibold text-gray-900">{funnel?.total_apps}</p>
                                </div>
                                <div>
                                    <p className="text-sm font-medium text-gray-500">Screening Rate</p>
                                    <p className="mt-1 text-3xl font-semibold text-blue-600">{funnel?.screening_rate}%</p>
                                </div>
                                <div>
                                    <p className="text-sm font-medium text-gray-500">Interview Rate</p>
                                    <p className="mt-1 text-3xl font-semibold text-indigo-600">{funnel?.interview_rate}%</p>
                                </div>
                                <div>
                                    <p className="text-sm font-medium text-gray-500">Final Round Rate</p>
                                    <p className="mt-1 text-3xl font-semibold text-purple-600">{funnel?.final_round_rate}%</p>
                                </div>
                                <div>
                                    <p className="text-sm font-medium text-gray-500">Offer Rate</p>
                                    <p className="mt-1 text-3xl font-semibold text-green-600">{funnel?.offer_rate}%</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Recommendations */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden md:col-span-2">
                    <div className="px-4 py-5 border-b border-gray-200 bg-gray-50">
                        <h3 className="text-lg font-medium text-gray-900 flex items-center">
                            <Activity className="mr-2 h-5 w-5 text-gray-500"/> Closed-Loop Recommendations
                        </h3>
                    </div>
                    <div className="p-0">
                        {recommendations && recommendations.length > 0 ? (
                            <ul className="divide-y divide-gray-200">
                                {recommendations.map((rec: any, idx: number) => (
                                    <li key={idx} className="p-4 hover:bg-gray-50">
                                        <div className="flex justify-between items-start">
                                            <div className="flex-1">
                                                <h4 className="text-sm font-semibold text-gray-900">{rec.recommended_action}</h4>
                                                <p className="mt-1 text-sm text-gray-600 font-medium">Observation: {rec.observation}</p>
                                                <p className="mt-1 text-sm text-gray-500">{rec.meaning}</p>
                                                <p className="mt-2 text-xs text-gray-400 font-mono">Evidence: {rec.evidence}</p>
                                            </div>
                                            <span className="ml-4 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 border border-gray-200">
                                                {rec.confidence}
                                            </span>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <div className="p-6 text-center text-sm text-gray-500">
                                No actionable recommendations generated yet. Log more outcomes to build intelligence.
                            </div>
                        )}
                    </div>
                </div>

                {/* Resume Performance */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                    <div className="px-4 py-5 border-b border-gray-200 bg-gray-50">
                        <h3 className="text-lg font-medium text-gray-900">Resume Version Performance</h3>
                    </div>
                    <div className="p-0 overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Version ID</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Apps</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Response Rate</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {resumePerf?.resume_performance?.map((rp: any, idx: number) => (
                                    <tr key={idx}>
                                        <td className="px-4 py-3 text-sm text-gray-900">{rp.resume_version_id}</td>
                                        <td className="px-4 py-3 text-sm text-gray-500">{rp.total_apps}</td>
                                        <td className="px-4 py-3 text-sm text-gray-900">{rp.response_rate !== undefined ? `${rp.response_rate}%` : '-'}</td>
                                        <td className="px-4 py-3 text-sm">
                                            <span className={`inline-flex px-2 text-xs font-semibold leading-5 rounded-full ${rp.status === 'OBSERVED_ASSOCIATION' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                                                {rp.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Match Performance */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                    <div className="px-4 py-5 border-b border-gray-200 bg-gray-50">
                        <h3 className="text-lg font-medium text-gray-900">Match Score Performance</h3>
                    </div>
                    <div className="p-0 overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Score Band</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Response Rate</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {matchPerf?.match_score_performance && Object.entries(matchPerf.match_score_performance).map(([band, mp]: [string, any], idx: number) => (
                                    <tr key={idx}>
                                        <td className="px-4 py-3 text-sm text-gray-900">{band}</td>
                                        <td className="px-4 py-3 text-sm text-gray-900">{mp.response_rate !== undefined ? `${mp.response_rate}%` : '-'}</td>
                                        <td className="px-4 py-3 text-sm">
                                            <span className={`inline-flex px-2 text-xs font-semibold leading-5 rounded-full ${mp.status === 'OBSERVED_ASSOCIATION' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                                                {mp.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default CareerOutcomesPage;
