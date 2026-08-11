import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ApplicationsPage from './ApplicationsPage';
import api from '../services/api';

vi.mock('../services/api');

const mockApplications = [
    {
        id: 1,
        status: 'DRAFT',
        match_score: 85,
        job_details: { title: 'Frontend Engineer', company: 'TechCorp', location: 'Remote', portal_type: 'Greenhouse' },
        preparation_status: '',
        submission_status: '',
        questions: [],
        notes: [],
        interviews: [],
    },
    {
        id: 2,
        status: 'REVIEW_REQUIRED',
        match_score: 92,
        job_details: { title: 'Backend Engineer', company: 'DataCo', location: 'NY', portal_type: 'Lever' },
        preparation_status: 'MISSING_INFO',
        submission_status: '',
        questions: [{ id: 1, question_text: 'Do you require sponsorship?', answer: '' }],
        notes: [],
        interviews: [],
    }
];

describe('ApplicationsPage', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        (api.get as any).mockResolvedValue({ data: mockApplications });
    });

    it('renders application board', async () => {
        render(<ApplicationsPage />);
        expect(screen.getByText('Applications')).toBeInTheDocument();
        
        await waitFor(() => {
            expect(screen.getByText('Frontend Engineer')).toBeInTheDocument();
            expect(screen.getByText('Backend Engineer')).toBeInTheDocument();
        });
    });

    it('can select an application and view details', async () => {
        render(<ApplicationsPage />);
        
        await waitFor(() => {
            expect(screen.getByTestId('app-card-1')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByTestId('app-card-1'));
        
        expect(screen.getByTestId('app-details')).toBeInTheDocument();
        expect(screen.getByTestId('prepare-btn')).toBeInTheDocument();
    });

    it('shows missing questions for REVIEW_REQUIRED', async () => {
        render(<ApplicationsPage />);
        
        await waitFor(() => {
            expect(screen.getByTestId('app-card-2')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByTestId('app-card-2'));
        
        expect(screen.getByText('Do you require sponsorship?')).toBeInTheDocument();
        expect(screen.getByText('Requires Answer')).toBeInTheDocument();
        expect(screen.getByTestId('mark-ready-btn')).toBeInTheDocument();
    });

    it('can transition REVIEW_REQUIRED to READY_TO_SUBMIT', async () => {
        (api.post as any).mockResolvedValue({ data: { status: 'READY_TO_SUBMIT' } });

        render(<ApplicationsPage />);
        
        await waitFor(() => {
            expect(screen.getByTestId('app-card-2')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByTestId('app-card-2'));
        
        const markReadyBtn = screen.getByTestId('mark-ready-btn');
        fireEvent.click(markReadyBtn);

        await waitFor(() => {
            expect(api.post).toHaveBeenCalledWith('/api/applications/tracker/2/transition/', { status: 'READY_TO_SUBMIT' });
        });
    });
});
