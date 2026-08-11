import React from 'react';

interface FunnelStage {
    stage: string;
    count: number;
    conversion_from_previous: number;
}

export const ApplicationFunnel: React.FC<{ data: FunnelStage[] }> = ({ data }) => {
    
    const maxCount = Math.max(...data.map(d => d.count), 1);

    return (
        <div style={{ background: 'var(--surface-color, #1e1e1e)', padding: '1.5rem', borderRadius: '12px', marginBottom: '2rem' }}>
            <h2 style={{ fontSize: '1.2rem', marginBottom: '1.5rem', borderBottom: '1px solid #333', paddingBottom: '0.5rem' }}>Application Funnel</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {data.map((stage, i) => {
                    const widthPercent = (stage.count / maxCount) * 100;
                    return (
                        <div key={stage.stage} style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                            <div style={{ width: '120px', textAlign: 'right', fontSize: '0.9rem', color: '#aaa' }}>
                                {stage.stage}
                            </div>
                            <div style={{ flex: '1', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                <div style={{ 
                                    width: `${Math.max(widthPercent, 1)}%`, 
                                    height: '30px', 
                                    background: `rgba(33, 150, 243, ${1 - (i * 0.1)})`,
                                    borderRadius: '4px',
                                    transition: 'width 0.3s ease'
                                }} />
                                <div style={{ fontWeight: 'bold', width: '40px' }}>{stage.count}</div>
                                {i > 0 && <div style={{ fontSize: '0.8rem', color: '#666' }}>{stage.conversion_from_previous}% conversion</div>}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
