import { useState, useEffect } from 'react';
import {
    Chart as ChartJS,
    ArcElement,
    Tooltip,
    Legend,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
} from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';
import {
    TrendingUp,
    Award,
    Clock,
    FilePlus,
    ArrowUpRight,
} from 'lucide-react';
import { mockRecommendations } from '../utils/mockData';

ChartJS.register(
    ArcElement,
    Tooltip,
    Legend,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
);

interface DashboardPageProps {
    apiMode: 'mock' | 'live';
}

export default function DashboardPage({ apiMode }: DashboardPageProps) {
    const [recommendations] = useState(mockRecommendations);
    const [stats, setStats] = useState({
        total: 5,
        applied: 4,
        interviews: 2,
        offers: 1,
        avgMatch: 88,
    });

    /* ------------------------------------------------------------------ */
    /* Live‑mode fallback – keep mock stats if backend not reachable */
    /* ------------------------------------------------------------------ */
    useEffect(() => {
        if (apiMode === 'live') {
            fetch('http://localhost:8000/api/applications/analytics/', {
                headers: {
                    Authorization: `Bearer ${localStorage.getItem('applysense_token')}`,
                },
            })
                .then(res => res.json())
                .then(data => {
                    if (data.total_applications !== undefined) {
                        setStats({
                            total: data.total_applications,
                            applied:
                                data.total_applications -
                                (data.status_breakdown?.Saved ?? 0),
                            interviews: data.status_breakdown?.Interview ?? 0,
                            offers: data.status_breakdown?.Offer ?? 0,
                            avgMatch: data.average_match_score ?? 85,
                        });
                    }
                })
                .catch(() =>
                    console.log('Live backend not running, falling back to mock data.'),
                );
        }
    }, [apiMode]);

    /* ------------------------------------------------------------------ */
    /* Charts data */
    /* ------------------------------------------------------------------ */
    const doughnutData = {
        labels: ['Saved', 'Applied', 'Under Review', 'Interview', 'Offer', 'Rejected'],
        datasets: [
            {
                data: [
                    // Mock numbers – replace with real API data when available
                    2,
                    stats.applied,
                    1,
                    stats.interviews,
                    stats.offers,
                    0,
                ],
                backgroundColor: [
                    '#4b9cdb',
                    '#56ccf2',
                    '#f6c90e',
                    '#ff9f43',
                    '#2ecc71',
                    '#e74c3c',
                ],
                hoverOffset: 4,
            },
        ],
    };

    const barData = {
        labels: recommendations.map(r => r.title),
        datasets: [
            {
                label: 'Match Score',
                data: recommendations.map(r => r.match_score),
                backgroundColor: '#56ccf2',
            },
        ],
    };

    return (
        <div className="space-y-6">
            {/* ----------- Stats ----------- */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="p-4 bg-cardBorder rounded-lg text-center">
                    <h3 className="text-sm text-gray-400">Total Submitted</h3>
                    <p className="text-2xl font-bold">{stats.total}</p>
                </div>
                <div className="p-4 bg-cardBorder rounded-lg text-center">
                    <h3 className="text-sm text-gray-400">Applied</h3>
                    <p className="text-2xl font-bold">{stats.applied}</p>
                </div>
                <div className="p-4 bg-cardBorder rounded-lg text-center">
                    <h3 className="text-sm text-gray-400">Interviews</h3>
                    <p className="text-2xl font-bold">{stats.interviews}</p>
                </div>
                <div className="p-4 bg-cardBorder rounded-lg text-center">
                    <h3 className="text-sm text-gray-400">Offers</h3>
                    <p className="text-2xl font-bold">{stats.offers}</p>
                </div>
                <div className="p-4 bg-cardBorder rounded-lg text-center">
                    <h3 className="text-sm text-gray-400">Avg. Match %</h3>
                    <p className="text-2xl font-bold">{stats.avgMatch}%</p>
                </div>
            </div>

            {/* ----------- Charts ----------- */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Doughnut */}
                <div className="bg-cardBorder rounded-lg p-4">
                    <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                        <TrendingUp className="h-5 w-5" />
                        Application Status
                    </h3>
                    <Doughnut data={doughnutData} />
                </div>

                {/* Bar */}
                <div className="bg-cardBorder rounded-lg p-4">
                    <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                        <Award className="h-5 w-5" />
                        Top Recommendations
                    </h3>
                    <Bar
                        data={barData}
                        options={{
                            responsive: true,
                            plugins: { legend: { display: false } },
                        }}
                    />
                </div>
            </div>

            {/* ----------- Quick actions ----------- */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <button className="flex items-center gap-2 p-3 bg-cardHover rounded-lg hover:bg-cardActive transition">
                    <FilePlus size={18} /> Add New Application
                </button>
                <button className="flex items-center gap-2 p-3 bg-cardHover rounded-lg hover:bg-cardActive transition">
                    <Clock size={18} /> View Calendar
                </button>
                <button className="flex items-center gap-2 p-3 bg-cardHover rounded-lg hover:bg-cardActive transition">
                    <Award size={18} /> View Offers
                </button>
                <button className="flex items-center gap-2 p-3 bg-cardHover rounded-lg hover:bg-cardActive transition">
                    <ArrowUpRight size={18} /> Export Report
                </button>
            </div>
        </div>
    );
}
