import React from 'react';

interface TrendPoint {
    period: string;
    submissions: number;
}

export const OutcomeTrend: React.FC<{ data: TrendPoint[] }> = ({ data }) => {
    
    // Very simple SVG sparkline for trend
    const maxSubmissions = Math.max(...data.map(d => d.submissions), 1);
    
    return (
        <div style={{ background: 'var(--surface-color, #1e1e1e)', padding: '1.5rem', borderRadius: '12px', marginBottom: '2rem' }}>
            <h2 style={{ fontSize: '1.2rem', marginBottom: '1.5rem', borderBottom: '1px solid #333', paddingBottom: '0.5rem' }}>Application Velocity</h2>
            {data.length === 0 ? (
                <div style={{ color: '#aaa' }}>Not enough data yet.</div>
            ) : (
                <div style={{ display: 'flex', height: '150px', alignItems: 'flex-end', gap: '4px', overflowX: 'auto' }}>
                    {data.map(point => {
                        const height = (point.submissions / maxSubmissions) * 100;
                        return (
                            <div key={point.period} style={{ flex: '1', minWidth: '30px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                <div style={{ fontSize: '0.7rem', color: '#888', marginBottom: '4px' }}>{point.submissions}</div>
                                <div style={{ width: '100%', height: `${Math.max(height, 5)}%`, background: '#2196f3', borderRadius: '4px 4px 0 0' }} title={point.period} />
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};
