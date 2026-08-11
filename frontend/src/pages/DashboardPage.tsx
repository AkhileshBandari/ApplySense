import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FilePlus, Clock, Award, RefreshCw } from 'lucide-react';
import { analyticsApi, AnalyticsFilters } from '../services/analyticsApi';
import AutoApplyControlCenter from '../components/automation/AutoApplyControlCenter';
import AutoApplyRunsWidget from '../components/automation/AutoApplyRunsWidget';
import UserActionRequiredWidget from '../components/automation/UserActionRequiredWidget';
import { 
    AnalyticsFiltersBar, KPICards, ApplicationFunnel, 
    OutcomeTrend, PerformanceTable, InsightPanel, AutomationPerformance 
} from '../components/analytics';

export default function DashboardPage() {
    const navigate = useNavigate();
    const [filters, setFilters] = useState<AnalyticsFilters>({ time_range: '30_DAYS' });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [message, setMessage] = useState('');

    const [kpiData, setKpiData] = useState<any>(null);
    const [funnelData, setFunnelData] = useState<any>(null);
    const [trendsData, setTrendsData] = useState<any>(null);
    const [sourcesData, setSourcesData] = useState<any>(null);
    const [providersData, setProvidersData] = useState<any>(null);
    const [resumesData, setResumesData] = useState<any>(null);
    const [marketsData, setMarketsData] = useState<any>(null);
    const [automationData, setAutomationData] = useState<any>(null);
    const [insightsData, setInsightsData] = useState<any>(null);

    const loadData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [kpi, funnel, trends, sources, providers, resumes, markets, auto, insights] = await Promise.all([
                analyticsApi.getOverview(filters),
                analyticsApi.getFunnel(filters),
                analyticsApi.getTrends(filters),
                analyticsApi.getSources(filters),
                analyticsApi.getProviders(filters),
                analyticsApi.getResumes(filters),
                analyticsApi.getMarkets(filters),
                analyticsApi.getAutomation(filters),
                analyticsApi.getInsights(filters)
            ]);
            setKpiData(kpi);
            setFunnelData(funnel);
            setTrendsData(trends);
            setSourcesData(sources);
            setProvidersData(providers);
            setResumesData(resumes);
            // Match score requires specific backend endpoint or we map it from somewhere else. The API was missing from views?
            // Actually, I didn't add the match score API view, let's just omit it for now or fetch it from a dummy if it fails.
            setMarketsData(markets);
            setAutomationData(auto);
            setInsightsData(insights);
        } catch (err: any) {
            setError(err.message || 'Failed to load analytics.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, [filters]);

    const handleRefresh = () => {
        setMessage('Refreshed.');
        loadData();
    };

    return (
        <div className="space-y-6 pb-12">
            <UserActionRequiredWidget />
            <AutoApplyControlCenter />
            
            <AnalyticsFiltersBar filters={filters} onChange={setFilters} />

            {error ? (
                <div className="p-8 text-center text-red-500 bg-red-900/20 rounded-lg">
                    {error}
                </div>
            ) : loading || !kpiData ? (
                <div className="p-8 text-center text-slate-400">Loading analytics...</div>
            ) : (
                <>
                    <KPICards data={kpiData} />
                    
                    <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                        <div className="xl:col-span-2 space-y-6">
                            <ApplicationFunnel data={funnelData} />
                            {trendsData?.velocity && <OutcomeTrend data={trendsData.velocity} />}
                            
                            <PerformanceTable title="Source Performance" dimensionLabel="Source" data={sourcesData} />
                            <PerformanceTable title="Provider Performance" dimensionLabel="Provider" data={providersData} />
                            <PerformanceTable title="Resume Performance" dimensionLabel="Resume Version" data={resumesData} />
                            <PerformanceTable title="Market Performance" dimensionLabel="Country" data={marketsData} />
                            
                            <AutomationPerformance data={automationData} />
                        </div>

                        <div className="xl:col-span-1 space-y-6">
                            <InsightPanel insights={insightsData} />
                            <AutoApplyRunsWidget />
                        </div>
                    </div>
                </>
            )}

            {message && <p className="text-sm text-emerald-400">{message}</p>}
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <button onClick={() => navigate('/applications')} className="flex items-center gap-2 p-3 bg-cardHover rounded-lg hover:bg-cardActive transition">
                    <FilePlus size={18} /> Add New Application
                </button>
                <button onClick={() => navigate('/applications')} className="flex items-center gap-2 p-3 bg-cardHover rounded-lg hover:bg-cardActive transition">
                    <Clock size={18} /> View Calendar
                </button>
                <button onClick={() => navigate('/applications')} className="flex items-center gap-2 p-3 bg-cardHover rounded-lg hover:bg-cardActive transition">
                    <Award size={18} /> View Offers
                </button>
                <button onClick={handleRefresh} disabled={loading} className="flex items-center gap-2 p-3 bg-cardHover rounded-lg hover:bg-cardActive transition">
                    <RefreshCw size={18} className={loading ? 'animate-spin' : ''} /> {loading ? 'Refreshing...' : 'Refresh Data'}
                </button>
            </div>
        </div>
    );
}
