import React from 'react';

interface Insight {
    type: string;
    severity: 'INFO' | 'WARNING' | 'SUCCESS';
    title: string;
    description: string;
    evidence: any;
}

export const InsightPanel: React.FC<{ insights: Insight[] }> = ({ insights }) => {
    
    if (insights.length === 0) {
        return (
            <div style={{ background: 'var(--surface-color, #1e1e1e)', padding: '1.5rem', borderRadius: '12px', marginBottom: '2rem' }}>
                <h2 style={{ fontSize: '1.2rem', marginBottom: '1.5rem', borderBottom: '1px solid #333', paddingBottom: '0.5rem' }}>Decision Insights</h2>
                <div style={{ color: '#aaa' }}>Keep applying! More data is needed to generate deterministic insights.</div>
            </div>
        );
    }
    
    return (
        <div style={{ background: 'var(--surface-color, #1e1e1e)', padding: '1.5rem', borderRadius: '12px', marginBottom: '2rem' }}>
            <h2 style={{ fontSize: '1.2rem', marginBottom: '1.5rem', borderBottom: '1px solid #333', paddingBottom: '0.5rem' }}>Decision Insights</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {insights.map((insight, i) => {
                    let color = '#2196f3';
                    if (insight.severity === 'WARNING') color = '#f44336';
                    if (insight.severity === 'SUCCESS') color = '#4caf50';
                    
                    return (
                        <div key={i} style={{ padding: '1rem', borderLeft: `4px solid ${color}`, background: '#252525', borderRadius: '4px' }}>
                            <div style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>{insight.title}</div>
                            <div style={{ fontSize: '0.9rem', color: '#ccc' }}>{insight.description}</div>
                            {insight.evidence && (
                                <details style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#888' }}>
                                    <summary style={{ cursor: 'pointer' }}>View Evidence</summary>
                                    <pre style={{ background: '#111', padding: '0.5rem', marginTop: '0.5rem', overflowX: 'auto', borderRadius: '4px' }}>
                                        {JSON.stringify(insight.evidence, null, 2)}
                                    </pre>
                                </details>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
