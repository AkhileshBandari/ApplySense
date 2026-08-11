import api from '../api';

export interface ProfessionalProfile {
  id: string;
  provider: string;
  external_profile_id?: string;
  profile_url?: string;
  headline: string;
  about: string;
  location: string;
  industry: string;
  current_role: string;
  target_role: string;
  source: string;
  sync_status: string;
  last_synced_at?: string;
  sections: ProfessionalProfileSection[];
}

export interface ProfessionalProfileSection {
  id: string;
  section_type: string;
  position: number;
  raw_content: string;
  structured_content: unknown;
  source: string;
  verification_status: string;
}

export interface Recommendation {
  id: string;
  section_type: string;
  recommendation_type: string;
  severity: string;
  reason_code: string;
  explanation: string;
  current_text: string;
  proposed_text: string;
  status: string;
}

export interface ProfileAnalysis {
  id: string;
  target_role: string;
  overall_score: number;
  completeness_score: number;
  evidence_alignment_score: number;
  keyword_alignment_score: number;
  consistency_score: number;
  recruiter_readiness_score: number;
  recommendations: Recommendation[];
}

export const careerBrandApi = {
  getProfiles: () => api.get<ProfessionalProfile[]>('/career-brand/profiles/').then((res) => res.data),
  createProfile: (data: Partial<ProfessionalProfile>) => api.post<ProfessionalProfile>('/career-brand/profiles/', data).then((res) => res.data),
  analyzeProfile: (id: string) => api.post<ProfileAnalysis>(`/career-brand/profiles/${id}/analyze/`).then((res) => res.data),
  getAnalyses: () => api.get<ProfileAnalysis[]>('/career-brand/analyses/').then((res) => res.data),
  generateProposal: (recId: string) => api.post<Recommendation>(`/career-brand/recommendations/${recId}/generate/`).then((res) => res.data),
  acceptProposal: (recId: string) => api.post<Recommendation>(`/career-brand/recommendations/${recId}/accept/`).then((res) => res.data),
  editProposal: (recId: string, proposedText: string) => api.post<Recommendation>(`/career-brand/recommendations/${recId}/edit/`, { proposed_text: proposedText }).then((res) => res.data),
  approveVersion: (profileId: string) => api.post(`/career-brand/profiles/${profileId}/approve_version/`).then((res) => res.data)
};
