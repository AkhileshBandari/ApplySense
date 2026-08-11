import React from 'react';
import { AnalyticsFilters } from '../../services/analyticsApi';

interface Props {
    filters: AnalyticsFilters;
    onChange: (filters: AnalyticsFilters) => void;
}

export const AnalyticsFiltersBar: React.FC<Props> = ({ filters, onChange }) => {
    
    const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        onChange({ ...filters, [e.target.name]: e.target.value });
    };

    return (
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', padding: '1rem', background: 'var(--surface-color, #1e1e1e)', borderRadius: '8px' }}>
            <div>
                <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '0.3rem', color: '#aaa' }}>Time Range</label>
                <select name="time_range" value={filters.time_range || '30_DAYS'} onChange={handleChange} style={{ padding: '0.5rem', borderRadius: '4px', background: '#333', color: '#fff', border: 'none' }}>
                    <option value="7_DAYS">Last 7 Days</option>
                    <option value="30_DAYS">Last 30 Days</option>
                    <option value="90_DAYS">Last 90 Days</option>
                    <option value="6_MONTHS">Last 6 Months</option>
                    <option value="1_YEAR">Last 1 Year</option>
                    <option value="ALL_TIME">All Time</option>
                </select>
            </div>
            
            <div>
                <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '0.3rem', color: '#aaa' }}>Source</label>
                <select name="source" value={filters.source || ''} onChange={handleChange} style={{ padding: '0.5rem', borderRadius: '4px', background: '#333', color: '#fff', border: 'none' }}>
                    <option value="">All Sources</option>
                    <option value="LinkedIn">LinkedIn</option>
                    <option value="Indeed">Indeed</option>
                    <option value="Naukri">Naukri</option>
                </select>
            </div>
            
            <div>
                <label style={{ display: 'block', fontSize: '0.8rem', marginBottom: '0.3rem', color: '#aaa' }}>Provider</label>
                <select name="provider" value={filters.provider || ''} onChange={handleChange} style={{ padding: '0.5rem', borderRadius: '4px', background: '#333', color: '#fff', border: 'none' }}>
                    <option value="">All Providers</option>
                    <option value="Greenhouse">Greenhouse</option>
                    <option value="Lever">Lever</option>
                    <option value="Ashby">Ashby</option>
                    <option value="Workday">Workday</option>
                </select>
            </div>
        </div>
    );
};
