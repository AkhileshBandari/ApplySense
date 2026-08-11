import React from 'react';

interface AutoData {
    manual_vs_auto: {
        auto: any;
        manual: any;
    };
    policy_blocks: { reason: string, count: number }[];
    user_actions: { reason: string, count: number }[];
    automation_success: {
        attempts: number;
        success: number;
        success_rate: number;
    };
}

export const AutomationPerformance: React.FC<{ data: AutoData }> = ({ data }) => {
    
    return (
        <div style={{ background: 'var(--surface-color, #1e1e1e)', padding: '1.5rem', borderRadius: '12px', marginBottom: '2rem' }}>
            <h2 style={{ fontSize: '1.2rem', marginBottom: '1.5rem', borderBottom: '1px solid #333', paddingBottom: '0.5rem' }}>Auto Apply Analytics</h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
                
                <div>
                    <h3 style={{ fontSize: '1rem', marginBottom: '1rem', color: '#ccc' }}>Execution Success</h3>
                    <div style={{ fontSize: '2rem', fontWeight: 'bold', color: data.automation_success.success_rate > 80 ? '#4caf50' : '#ff9800' }}>
                        {data.automation_success.success_rate}%
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#888' }}>{data.automation_success.success} successful out of {data.automation_success.attempts} attempts</div>
                </div>

                <div>
                    <h3 style={{ fontSize: '1rem', marginBottom: '1rem', color: '#ccc' }}>User Action Required</h3>
                    {data.user_actions.length === 0 ? (
                        <div style={{ color: '#aaa' }}>No user actions required.</div>
                    ) : (
                        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                            {data.user_actions.map(u => (
                                <li key={u.reason} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.3rem 0', borderBottom: '1px solid #333' }}>
                                    <span>{u.reason}</span>
                                    <strong>{u.count}</strong>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                <div>
                    <h3 style={{ fontSize: '1rem', marginBottom: '1rem', color: '#ccc' }}>Policy Blocks</h3>
                    {data.policy_blocks.length === 0 ? (
                        <div style={{ color: '#aaa' }}>No jobs blocked by policy.</div>
                    ) : (
                        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                            {data.policy_blocks.map(b => (
                                <li key={b.reason} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.3rem 0', borderBottom: '1px solid #333' }}>
                                    <span>{b.reason}</span>
                                    <strong>{b.count}</strong>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

            </div>
        </div>
    );
};
