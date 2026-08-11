import React, { useEffect, useState } from 'react';
import { Target, Flag, AlertTriangle, ArrowRight, Play, CheckCircle } from 'lucide-react';
import api from '../services/api';

export const CareerDecisionPage: React.FC = () => {
    const [decisions, setDecisions] = useState<any[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchDecisions = async () => {
            try {
                const response = await api.get('/api/career-decisions/decisions/');
                setDecisions(response.data);
            } catch (err: any) {
                setError(err.message || 'Failed to fetch decisions');
            } finally {
                setLoading(false);
            }
        };
        fetchDecisions();
    }, []);

    const markActive = async (id: number) => {
        try {
            await api.post(`/api/career-decisions/decisions/${id}/make_active/`);
            const response = await api.get('/api/career-decisions/decisions/');
            setDecisions(response.data);
        } catch (err: any) {
            alert('Failed to update decision');
        }
    };

    if (loading) return <div className="p-8 text-center text-gray-500">Loading Intelligence...</div>;
    if (error) return <div className="p-8"><div className="bg-red-50 text-red-600 p-4 rounded">{error}</div></div>;

    return (
        <div className="space-y-6 max-w-7xl mx-auto pb-12">
            <div>
                <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                    <Target className="mr-2 h-6 w-6 text-indigo-600" />
                    Career Decision Planner
                </h1>
                <p className="mt-1 text-sm text-gray-500">
                    Your evidence-backed career strategy and highest-impact next actions.
                </p>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-200">
                {decisions.length === 0 ? (
                    <div className="p-8 text-center text-gray-500 border-b border-gray-200">
                        No active career decisions. Start by simulating a career pathway.
                    </div>
                ) : (
                    <ul className="divide-y divide-gray-200">
                        {decisions.map((decision) => (
                            <li key={decision.id} className="p-6 hover:bg-gray-50 transition-colors">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <h3 className="text-lg font-bold text-gray-900">{decision.primary_goal}</h3>
                                            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${decision.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                                                {decision.is_active ? 'ACTIVE PLAN' : 'DRAFT'}
                                            </span>
                                        </div>
                                        
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                                            <div className="bg-red-50 rounded p-3 border border-red-100">
                                                <h4 className="text-sm font-semibold text-red-800 flex items-center mb-1"><AlertTriangle className="w-4 h-4 mr-1"/> Top Blocker</h4>
                                                <p className="text-sm text-red-700">{decision.top_blocker || 'None identified'}</p>
                                            </div>
                                            <div className="bg-blue-50 rounded p-3 border border-blue-100">
                                                <h4 className="text-sm font-semibold text-blue-800 flex items-center mb-1"><Flag className="w-4 h-4 mr-1"/> Recommended Strategy</h4>
                                                <p className="text-sm text-blue-700">{decision.recommended_strategy}</p>
                                            </div>
                                        </div>

                                        <div className="mt-6">
                                            <h4 className="text-sm font-semibold text-gray-900 mb-3 border-b pb-2">Next Best Actions</h4>
                                            <ul className="space-y-2">
                                                {decision.next_best_actions.map((action: any, idx: number) => (
                                                    <li key={idx} className="flex items-start text-sm">
                                                        <ArrowRight className="w-4 h-4 text-gray-400 mr-2 mt-0.5 flex-shrink-0"/>
                                                        <div>
                                                            <span className="font-medium text-gray-900">{action.action_type}</span>: <span className="text-gray-600">{action.description}</span>
                                                        </div>
                                                    </li>
                                                ))}
                                                {decision.next_best_actions.length === 0 && <span className="text-gray-500 text-sm">No actions defined.</span>}
                                            </ul>
                                        </div>
                                    </div>
                                    <div className="ml-6 flex flex-col items-end">
                                        <div className="text-right mb-4">
                                            <span className="text-3xl font-bold text-gray-900">{decision.confidence_score}</span>
                                            <span className="text-gray-500 text-sm block">Confidence Score</span>
                                        </div>
                                        {!decision.is_active && (
                                            <button 
                                                onClick={() => markActive(decision.id)}
                                                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                                            >
                                                <Play className="w-4 h-4 mr-2" /> Make Active Plan
                                            </button>
                                        )}
                                        {decision.is_active && (
                                            <span className="inline-flex items-center text-sm font-medium text-green-600">
                                                <CheckCircle className="w-4 h-4 mr-1"/> Executing
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
};
