import api from '../services/api';

export interface DomainState {
    domain_name: string;
    status: string;
    last_synced_at: string;
}

export interface OperatingState {
    id: number;
    overall_readiness_score: number;
    current_primary_goal: string;
    top_blocker: string;
    execution_velocity_score: number;
    application_momentum_score: number;
    current_os_state: string;
    overall_health: string;
    domains: DomainState[];
    updated_at: string;
}

export interface UserActionItem {
    id: number;
    source_domain: string;
    blocker_type: string;
    title: string;
    description: string;
    priority: number;
    is_resolved: boolean;
    context_data: any;
    created_at: string;
}

export const getOSDashboardState = async (): Promise<OperatingState> => {
    const response = await api.get('/career-integration/state/os-dashboard/');
    return response.data;
};

export const getUserActionItems = async (): Promise<UserActionItem[]> => {
    const response = await api.get('/career-integration/action-center/');
    // Handle DRF pagination response or plain array
    return response.data.results || response.data;
};
