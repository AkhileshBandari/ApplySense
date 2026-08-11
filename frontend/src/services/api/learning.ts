import api from '../api';

export const learningApi = {
    // Gap Analysis
    createGapAnalysis: (data: any) => api.post('/learning/gap-analysis/', data),
    getGapAnalyses: () => api.get('/learning/gap-analysis/'),
    
    // Learning Roadmaps
    createRoadmap: (analysisId: number, hoursPerWeek: number) => 
        api.post('/learning/roadmaps/', { analysis_id: analysisId, hours_per_week: hoursPerWeek }),
    getRoadmaps: () => api.get('/learning/roadmaps/'),
    
    // Roadmap Items
    updateRoadmapItemStatus: (itemId: number, status: string) => 
        api.patch(`/learning/roadmap-items/${itemId}/`, { status }),
        
    // Project Recommendations
    generateProjectRecommendations: (analysisId: number) => 
        api.post('/learning/projects/generate/', { analysis_id: analysisId }),
    getProjectRecommendations: () => api.get('/learning/projects/'),
};

export default learningApi;
