import React, { useState, useEffect } from 'react';
import api from '../services/api';

interface Weakness {
  skill: string;
  severity: string;
  reason_code: string;
}

interface InterviewSession {
  id: number;
  status: string;
  started_at: string;
  overall_readiness_score: number | null;
}

const InterviewPrepPage: React.FC = () => {
  const [readiness, setReadiness] = useState<number | string | null>(null);
  const [weaknesses, setWeaknesses] = useState<Weakness[]>([]);
  const [sessions, setSessions] = useState<InterviewSession[]>([]);
  
  const [loading, setLoading] = useState(true);

  // Session UI State
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<any>(null);
  const [answerText, setAnswerText] = useState('');
  const [evaluation, setEvaluation] = useState<any>(null);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const readRes = await api.get('/api/interview-intelligence/readiness/');
      setReadiness(readRes.data.readiness_score);

      const weakRes = await api.get('/api/interview-intelligence/weaknesses/');
      setWeaknesses(weakRes.data);

      const sessRes = await api.get('/api/interview-intelligence/sessions/');
      setSessions(sessRes.data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const startNewSession = async () => {
    try {
      // 1. Generate plan
      const planRes = await api.post('/api/interview-intelligence/plans/generate/', {
        interview_type: 'TECHNICAL',
        difficulty: 'INTERMEDIATE',
        target_role: 'Software Engineer'
      });
      
      // 2. Create session
      const sessRes = await api.post('/api/interview-intelligence/sessions/', {
        plan: planRes.data.id,
        mode: 'TEXT'
      });
      
      // 3. Start session
      const startRes = await api.post(`/api/interview-intelligence/sessions/${sessRes.data.id}/start/`);
      
      setActiveSessionId(startRes.data.id);
      
      // Fetch report to get first question
      const reportRes = await api.get(`/api/interview-intelligence/sessions/${startRes.data.id}/report/`);
      const qs = reportRes.data.session.questions;
      if (qs && qs.length > 0) {
        setCurrentQuestion(qs[0]);
      }
      
    } catch (e) {
      alert('Failed to start session');
    }
  };

  const submitAnswer = async () => {
    if (!activeSessionId || !currentQuestion) return;
    try {
      const res = await api.post(`/api/interview-intelligence/sessions/${activeSessionId}/answer/`, {
        question_id: currentQuestion.id,
        response_text: answerText
      });
      setEvaluation(res.data.evaluation);
      
      if (res.data.follow_up_question) {
        setTimeout(() => {
          setCurrentQuestion(res.data.follow_up_question);
          setAnswerText('');
          setEvaluation(null);
        }, 3000);
      } else {
        // Move to next question or complete
        // For simplicity, just complete session
        await api.post(`/api/interview-intelligence/sessions/${activeSessionId}/complete/`);
        setActiveSessionId(null);
        setCurrentQuestion(null);
        setAnswerText('');
        setEvaluation(null);
        fetchDashboard();
      }
    } catch (e) {
      alert('Failed to submit answer');
    }
  };

  if (loading) return <div className="p-8 text-white">Loading Interview Intelligence...</div>;

  return (
    <div className="p-8 text-white bg-slate-900 min-h-screen">
      <h1 className="text-3xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-indigo-500">Interview Intelligence</h1>
      
      {activeSessionId ? (
        <div className="bg-slate-800 p-6 rounded-lg border border-indigo-500">
          <h2 className="text-xl font-bold mb-4 text-indigo-400">Mock Interview Session</h2>
          {currentQuestion ? (
            <div>
              <p className="mb-4 text-lg">{currentQuestion.question_text}</p>
              <textarea 
                className="w-full h-32 bg-slate-700 text-white border border-slate-600 rounded p-2 mb-4"
                value={answerText}
                onChange={e => setAnswerText(e.target.value)}
                placeholder="Type your answer here..."
                disabled={!!evaluation}
              />
              <button 
                className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded font-semibold"
                onClick={submitAnswer}
                disabled={!!evaluation || !answerText.trim()}
              >
                Submit Answer
              </button>
              
              {evaluation && (
                <div className="mt-6 p-4 bg-slate-700 rounded border border-green-500">
                  <h3 className="font-bold text-green-400 mb-2">Feedback</h3>
                  <p className="mb-2">Score: {evaluation.overall_score}/100</p>
                  <p className="text-sm text-gray-300">{evaluation.feedback}</p>
                  {evaluation.missing_concepts?.length > 0 && (
                    <div className="mt-2 text-sm text-yellow-400">
                      <strong>Missing Concepts: </strong>
                      {evaluation.missing_concepts.join(', ')}
                    </div>
                  )}
                  {evaluation.unsupported_claims?.length > 0 && (
                    <div className="mt-2 text-sm text-red-400">
                      <strong>Unsupported Claims: </strong>
                      {evaluation.unsupported_claims.join(', ')}
                    </div>
                  )}
                  <p className="mt-2 text-xs italic text-gray-400">Preparing next question...</p>
                </div>
              )}
            </div>
          ) : (
            <p>Loading questions...</p>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
              <h2 className="text-xl font-semibold mb-4 text-white">Interview Readiness</h2>
              <div className="flex items-center space-x-6">
                <div className="w-32 h-32 rounded-full border-4 border-indigo-500 flex items-center justify-center">
                  <span className="text-3xl font-bold">{readiness || 'N/A'}</span>
                </div>
                <div className="flex-1">
                  <p className="text-gray-300 mb-4">Your interview readiness is calculated based on your performance in realistic mock interviews.</p>
                  <button 
                    onClick={startNewSession}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-2 rounded-lg font-semibold transition-colors"
                  >
                    Start Mock Interview
                  </button>
                </div>
              </div>
            </div>
            
            <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
              <h2 className="text-xl font-semibold mb-4 text-white">Session History</h2>
              <div className="space-y-4">
                {sessions.map(s => (
                  <div key={s.id} className="flex justify-between items-center p-4 bg-slate-700/50 rounded">
                    <div>
                      <span className={`px-2 py-1 text-xs rounded font-medium ${s.status === 'COMPLETED' ? 'bg-green-900/50 text-green-400' : 'bg-blue-900/50 text-blue-400'}`}>
                        {s.status}
                      </span>
                      <p className="text-sm text-gray-400 mt-2">{new Date(s.started_at || Date.now()).toLocaleDateString()}</p>
                    </div>
                    <div className="text-xl font-bold text-indigo-400">
                      {s.overall_readiness_score ? `${s.overall_readiness_score}%` : '--'}
                    </div>
                  </div>
                ))}
                {sessions.length === 0 && <p className="text-gray-400 text-sm">No sessions yet.</p>}
              </div>
            </div>
          </div>
          
          <div className="space-y-6">
            <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
              <h2 className="text-xl font-semibold mb-4 text-white">Top Weaknesses</h2>
              <ul className="space-y-3">
                {weaknesses.map((w, idx) => (
                  <li key={idx} className="flex flex-col p-3 bg-slate-700/50 rounded border-l-4 border-red-500">
                    <span className="font-semibold text-gray-200">{w.skill}</span>
                    <span className="text-xs text-red-400 uppercase tracking-wider">{w.severity} SEVERITY</span>
                  </li>
                ))}
                {weaknesses.length === 0 && <p className="text-gray-400 text-sm">No critical weaknesses identified.</p>}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InterviewPrepPage;
