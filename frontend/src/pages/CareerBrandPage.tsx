import React, { useState, useEffect } from 'react';
import { careerBrandApi, ProfessionalProfile, ProfileAnalysis, Recommendation } from '../services/api/careerBrand';
import { AlertCircle, CheckCircle, RefreshCw, Plus } from 'lucide-react';

const CareerBrandPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<ProfessionalProfile | null>(null);
  const [analysis, setAnalysis] = useState<ProfileAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generatingFor, setGeneratingFor] = useState<string | null>(null);

  const fetchProfile = async () => {
    setLoading(true);
    setError(null);
    try {
      const profiles = await careerBrandApi.getProfiles();
      if (profiles.length > 0) {
        setProfile(profiles[0]);
        const analyses = await careerBrandApi.getAnalyses();
        if (analyses.length > 0) {
          setAnalysis(analyses[0]);
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load career brand data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleCreateMockProfile = async () => {
    try {
      setLoading(true);
      await careerBrandApi.createProfile({
        headline: 'Software Engineer',
        about: 'Passionate developer.',
        current_role: 'Engineer',
        location: 'Remote'
      });
      await fetchProfile();
    } catch (err) {
      setError('Failed to create profile');
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!profile) return;
    try {
      setLoading(true);
      const newAnalysis = await careerBrandApi.analyzeProfile(profile.id);
      setAnalysis(newAnalysis);
    } catch (err) {
      setError('Failed to analyze profile.');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (recId: string) => {
    try {
      setGeneratingFor(recId);
      await careerBrandApi.generateProposal(recId);
      await fetchProfile();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to generate proposal');
    } finally {
      setGeneratingFor(null);
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-full"><RefreshCw className="animate-spin text-accentTeal" size={32} /></div>;
  }

  if (!profile) {
    return (
      <div className="p-6">
        <h2 className="text-3xl font-bold mb-4">Career Brand</h2>
        <div className="glass-panel p-6 rounded-lg text-center">
          <AlertCircle className="mx-auto text-primaryText opacity-50 mb-4" size={48} />
          <h3 className="text-xl font-semibold mb-2">No Profile Found</h3>
          <p className="text-secondaryText mb-6">You haven't added a professional profile yet.</p>
          <button onClick={handleCreateMockProfile} className="btn-primary flex items-center mx-auto gap-2">
            <Plus size={16} /> Add Professional Profile
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h2 className="text-3xl font-bold mb-6">Career Brand Optimization</h2>
      
      {error && (
        <div className="bg-red-500/20 border border-red-500/50 text-red-100 p-4 rounded mb-6 flex items-center gap-3">
          <AlertCircle size={20} /> {error}
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="glass-panel p-6 rounded-lg">
          <h3 className="text-xl font-semibold mb-4 border-b border-cardBorder pb-2">Current Profile</h3>
          <div className="space-y-4">
            <div><span className="text-secondaryText">Headline:</span> <span className="font-medium">{profile.headline || 'Not set'}</span></div>
            <div><span className="text-secondaryText">About:</span> <span className="font-medium">{profile.about || 'Not set'}</span></div>
            <div><span className="text-secondaryText">Location:</span> <span className="font-medium">{profile.location || 'Not set'}</span></div>
          </div>
          <button onClick={handleAnalyze} className="btn-primary mt-6 flex items-center gap-2">
            <RefreshCw size={16} /> Run Optimization Analysis
          </button>
        </div>
        
        {analysis && (
          <div className="glass-panel p-6 rounded-lg border-accentTeal/30 border-2">
            <h3 className="text-xl font-semibold mb-4 border-b border-cardBorder pb-2 text-accentTeal">Recruiter Readiness</h3>
            <div className="text-center my-6">
              <div className="text-5xl font-bold text-accentTeal mb-2">{analysis.recruiter_readiness_score}<span className="text-2xl text-secondaryText">/100</span></div>
            </div>
            <div className="flex justify-between items-center bg-darkBg/50 p-3 rounded mb-2">
              <span className="text-secondaryText">Completeness</span>
              <span className="font-bold">{analysis.completeness_score}/100</span>
            </div>
            <div className="flex justify-between items-center bg-darkBg/50 p-3 rounded">
              <span className="text-secondaryText">Overall Score</span>
              <span className="font-bold">{analysis.overall_score}/100</span>
            </div>
          </div>
        )}
      </div>

      {analysis && analysis.recommendations.length > 0 && (
        <div className="glass-panel p-6 rounded-lg">
          <h3 className="text-xl font-semibold mb-4 border-b border-cardBorder pb-2">Optimization Recommendations</h3>
          <div className="space-y-4">
            {analysis.recommendations.map((item: Recommendation) => (
              <div key={item.id} className="bg-darkBg/30 p-4 rounded border border-cardBorder">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    {item.severity === 'HIGH' || item.severity === 'CRITICAL' ? (
                      <AlertCircle className="text-red-400" size={18} />
                    ) : (
                      <AlertCircle className="text-yellow-400" size={18} />
                    )}
                    <h4 className="font-semibold text-lg">{item.explanation}</h4>
                  </div>
                  <span className="text-xs px-2 py-1 bg-cardBorder rounded text-secondaryText">
                    {item.section_type || 'General'}
                  </span>
                </div>
                <p className="text-secondaryText mb-4 text-sm">Reason: {item.reason_code}</p>
                
                {item.proposed_text ? (
                  <div className="bg-accentTeal/10 border border-accentTeal/30 p-4 rounded mt-4">
                    <span className="text-accentTeal font-semibold block mb-2 flex items-center gap-1"><CheckCircle size={14}/> Proposed Change:</span>
                    <p className="mb-4">{item.proposed_text}</p>
                    <div className="flex gap-2">
                      <button className="btn-primary text-sm py-1 px-3">Accept</button>
                      <button className="btn-secondary text-sm py-1 px-3">Edit</button>
                    </div>
                  </div>
                ) : (
                  <button 
                    className="btn-secondary text-sm flex items-center gap-2"
                    onClick={() => handleGenerate(item.id)}
                    disabled={generatingFor === item.id}
                  >
                    {generatingFor === item.id ? <RefreshCw className="animate-spin" size={14} /> : <Sparkles size={14} />}
                    Generate AI Proposal
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Add Sparkles icon import
import { Sparkles } from 'lucide-react';
export default CareerBrandPage;
