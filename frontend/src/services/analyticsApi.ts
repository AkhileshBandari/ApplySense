import api from './api';

export interface AnalyticsFilters {
    time_range?: string;
    start_date?: string;
    end_date?: string;
    country?: string | null;
    source?: string | null;
    provider?: string | null;
}

export const analyticsApi = {
    getOverview: async (filters: AnalyticsFilters = {}) => {
        const response = await api.get('/api/analytics/overview/', { params: filters });
        return response.data;
    },
    
    getFunnel: async (filters: AnalyticsFilters = {}) => {
        const response = await api.get('/api/analytics/funnel/', { params: filters });
        return response.data;
    },
    
    getTrends: async (filters: AnalyticsFilters = {}) => {
        const response = await api.get('/api/analytics/trends/', { params: filters });
        return response.data;
    },
    
    getSources: async (filters: AnalyticsFilters = {}) => {
        const response = await api.get('/api/analytics/sources/', { params: filters });
        return response.data;
    },
    
    getProviders: async (filters: AnalyticsFilters = {}) => {
        const response = await api.get('/api/analytics/providers/', { params: filters });
        return response.data;
    },
    
    getResumes: async (filters: AnalyticsFilters = {}) => {
        const response = await api.get('/api/analytics/resumes/', { params: filters });
        return response.data;
    },
    
    getMarkets: async (filters: AnalyticsFilters = {}) => {
        const response = await api.get('/api/analytics/markets/', { params: filters });
        return response.data;
    },
    
    getAutomation: async (filters: AnalyticsFilters = {}) => {
        const response = await api.get('/api/analytics/automation/', { params: filters });
        return response.data;
    },
    
    getInsights: async (filters: AnalyticsFilters = {}) => {
        const response = await api.get('/api/analytics/insights/', { params: filters });
        return response.data;
    }
};
