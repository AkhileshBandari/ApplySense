import React from 'react';

interface PerformanceRow {
    dimension: string | null;
    bucket?: string;
    applications: number;
    submitted: number;
    responses: number;
    interviews: number;
    offers: number;
    rejections: number;
    response_rate: number;
    interview_rate: number;
    offer_rate: number;
    rejection_rate: number;
}

export const PerformanceTable: React.FC<{ title: string, data: PerformanceRow[], dimensionLabel: string }> = ({ title, data, dimensionLabel }) => {
    return (
        <div style={{ background: 'var(--surface-color, #1e1e1e)', padding: '1.5rem', borderRadius: '12px', marginBottom: '2rem', overflowX: 'auto' }}>
            <h2 style={{ fontSize: '1.2rem', marginBottom: '1.5rem', borderBottom: '1px solid #333', paddingBottom: '0.5rem' }}>{title}</h2>
            {data.length === 0 ? (
                <div style={{ color: '#aaa' }}>Not enough data yet.</div>
            ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid #333' }}>
                            <th style={{ padding: '0.5rem', color: '#aaa', fontWeight: 'normal' }}>{dimensionLabel}</th>
                            <th style={{ padding: '0.5rem', color: '#aaa', fontWeight: 'normal' }}>Submitted</th>
                            <th style={{ padding: '0.5rem', color: '#aaa', fontWeight: 'normal' }}>Responses</th>
                            <th style={{ padding: '0.5rem', color: '#aaa', fontWeight: 'normal' }}>Interviews</th>
                            <th style={{ padding: '0.5rem', color: '#aaa', fontWeight: 'normal' }}>Offers</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((row, i) => (
                            <tr key={i} style={{ borderBottom: '1px solid #222' }}>
                                <td style={{ padding: '0.5rem' }}>{row.dimension || row.bucket || 'Unknown'}</td>
                                <td style={{ padding: '0.5rem' }}>{row.submitted}</td>
                                <td style={{ padding: '0.5rem' }}>{row.response_rate}% ({row.responses})</td>
                                <td style={{ padding: '0.5rem' }}>{row.interview_rate}% ({row.interviews})</td>
                                <td style={{ padding: '0.5rem' }}>{row.offer_rate}% ({row.offers})</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
};
