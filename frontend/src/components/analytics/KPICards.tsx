import React from 'react';

interface KPIData {
    total_jobs_matched: number;
    applications_created: number;
    applications_submitted: number;
    responses: number;
    interviews: number;
    offers: number;
    rejections: number;
    response_rate: number;
    interview_rate: number;
    offer_rate: number;
    rejection_rate: number;
}

export const KPICards: React.FC<{ data: KPIData }> = ({ data }) => {
    
    const Card = ({ title, value, subtext, color }: { title: string, value: string | number, subtext?: string, color?: string }) => (
        <div style={{
            background: 'var(--surface-color, #1e1e1e)', 
            padding: '1.5rem', 
            borderRadius: '12px',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
            flex: '1',
            minWidth: '200px'
        }}>
            <h3 style={{ fontSize: '0.9rem', color: '#aaa', margin: '0 0 0.5rem 0' }}>{title}</h3>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: color || '#fff' }}>{value}</div>
            {subtext && <div style={{ fontSize: '0.8rem', color: '#888', marginTop: '0.5rem' }}>{subtext}</div>}
        </div>
    );

    return (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
            <Card title="Submitted Applications" value={data.applications_submitted} subtext={`From ${data.total_jobs_matched} matched jobs`} />
            <Card title="Responses" value={data.responses} subtext={`${data.response_rate}% response rate`} color="#4caf50" />
            <Card title="Interviews" value={data.interviews} subtext={`${data.interview_rate}% conversion`} color="#2196f3" />
            <Card title="Offers" value={data.offers} subtext={`${data.offer_rate}% offer rate`} color="#ff9800" />
            <Card title="Rejections" value={data.rejections} subtext={`${data.rejection_rate}% rejection rate`} color="#f44336" />
        </div>
    );
};
