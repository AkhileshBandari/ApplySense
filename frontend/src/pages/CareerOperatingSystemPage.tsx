import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, LayoutDashboard, AlertTriangle, CheckCircle, Clock, ListTodo } from 'lucide-react';
import { getOSDashboardState, getUserActionItems, OperatingState, UserActionItem } from '../api/osIntegration';
import api from '../services/api';

const CareerOperatingSystemPage: React.FC = () => {
    const navigate = useNavigate();
    const [state, setState] = useState<OperatingState | null>(null);
    const [actionItems, setActionItems] = useState<UserActionItem[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const loadData = async () => {
        try {
            const [osState, actions] = await Promise.all([
                getOSDashboardState(),
                getUserActionItems()
            ]);
            setState(osState);
            setActionItems(actions);
        } catch (err: any) {
            setError(err.message || 'Failed to fetch operating system state');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const handleResolveAction = async (id: number) => {
        try {
            await api.patch(`/career-integration/action-center/${id}/`, { is_resolved: true });
            loadData();
        } catch (err) {
            console.error("Failed to resolve action", err);
        }
    };

    if (loading) return <div className="p-8 text-center"><Activity className="animate-spin inline mr-2"/> Loading OS State...</div>;
    if (error) return <div className="p-8"><div className="bg-red-50 text-red-600 p-4 rounded-md flex items-center"><AlertTriangle className="mr-2"/> {error}</div></div>;
    if (!state) return <div className="p-8"><div className="bg-blue-50 text-blue-600 p-4 rounded-md flex items-center"><Activity className="mr-2"/> No Operating State Initialized</div></div>;

    const activeActions = actionItems.filter(a => !a.is_resolved).sort((a, b) => b.priority - a.priority);

    return (
        <div className="space-y-6 max-w-7xl mx-auto pb-12">
            <div>
                <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                    <LayoutDashboard className="mr-2 h-6 w-6 text-indigo-600" />
                    Career Operating System Command Center
                </h1>
                <p className="mt-1 text-sm text-gray-500">
                    Unified orchestration layer for your career progression.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* High-level KPIs */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Overall Health</h3>
                    <div className="mt-2">
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${state.overall_health === 'HEALTHY' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                            {state.overall_health === 'HEALTHY' ? <CheckCircle className="w-4 h-4 mr-1"/> : <AlertTriangle className="w-4 h-4 mr-1"/>}
                            {state.overall_health}
                        </span>
                    </div>
                </div>
                
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Current OS State</h3>
                    <div className="mt-2 text-xl font-bold text-gray-900">
                        {state.current_os_state.replace(/_/g, ' ')}
                    </div>
                </div>
                
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Overall Readiness</h3>
                    <div className="mt-2 text-4xl font-bold text-gray-900">
                        {state.overall_readiness_score}<span className="text-xl text-gray-400 font-normal">/100</span>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Action Center */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden md:col-span-2">
                    <div className="px-4 py-5 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
                        <h3 className="text-lg font-medium text-gray-900 flex items-center">
                            <ListTodo className="mr-2 w-5 h-5 text-indigo-500"/> Action Center
                        </h3>
                        <span className="bg-indigo-100 text-indigo-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                            {activeActions.length} Pending
                        </span>
                    </div>
                    {activeActions.length === 0 ? (
                        <div className="p-8 text-center text-gray-500 flex flex-col items-center justify-center">
                            <CheckCircle className="w-12 h-12 text-green-400 mb-3" />
                            <p>You're all caught up! No active blockers.</p>
                        </div>
                    ) : (
                        <ul className="divide-y divide-gray-200">
                            {activeActions.map((action) => (
                                <li key={action.id} className="p-5 hover:bg-gray-50 flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center mb-1">
                                            <span className="text-xs font-semibold uppercase tracking-wide text-gray-500 mr-2">
                                                [{action.source_domain}]
                                            </span>
                                            {action.priority >= 90 && (
                                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 mr-2">
                                                    Critical
                                                </span>
                                            )}
                                            <h4 className="text-sm font-bold text-gray-900">{action.title}</h4>
                                        </div>
                                        <p className="text-sm text-gray-600 mt-1">{action.description}</p>
                                    </div>
                                    <div className="ml-4 flex-shrink-0">
                                        <button 
                                            onClick={() => handleResolveAction(action.id)}
                                            className="text-indigo-600 hover:text-indigo-900 text-sm font-medium"
                                        >
                                            Resolve
                                        </button>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                {/* Sub-domains Sidebar */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden md:col-span-1">
                    <div className="px-4 py-5 border-b border-gray-200 bg-gray-50">
                        <h3 className="text-lg font-medium text-gray-900 flex items-center">
                            <Activity className="mr-2 w-5 h-5 text-gray-500"/> Subsystem Status
                        </h3>
                    </div>
                    <ul className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                        {state.domains?.map((d: any, idx: number) => (
                            <li key={idx} className="p-4 flex flex-col hover:bg-gray-50">
                                <div className="flex justify-between items-center mb-1">
                                    <span className="text-sm font-bold text-gray-900">{d.domain_name}</span>
                                    <span className={`inline-flex px-2 py-0.5 text-xs font-semibold rounded-full 
                                        ${d.status === 'HEALTHY' ? 'bg-green-100 text-green-800' : 
                                          d.status === 'STALE' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'}`}>
                                        {d.status}
                                    </span>
                                </div>
                                <p className="text-xs text-gray-500 flex items-center">
                                    <Clock className="w-3 h-3 mr-1"/> {new Date(d.last_synced_at).toLocaleString()}
                                </p>
                            </li>
                        ))}
                    </ul>
                </div>
            </div>

            {/* Quick Links */}
            <div className="pt-4 border-t border-gray-200">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">Jump to Domain</h3>
                <div className="flex flex-wrap gap-3">
                    <button onClick={() => navigate('/career-decisions')} className="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50">Decisions</button>
                    <button onClick={() => navigate('/career-execution')} className="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50">Execution</button>
                    <button onClick={() => navigate('/applications')} className="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50">Applications</button>
                    <button onClick={() => navigate('/learning')} className="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50">Skill Growth</button>
                    <button onClick={() => navigate('/evidence')} className="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50">Evidence</button>
                    <button onClick={() => navigate('/career-brand')} className="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50">Brand</button>
                </div>
            </div>
        </div>
    );
};

export default CareerOperatingSystemPage;
