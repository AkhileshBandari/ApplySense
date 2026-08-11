import { useState, useEffect } from 'react';
import { Target, TrendingUp, BookOpen, Layers } from 'lucide-react';
import learningApi from '../services/api/learning';

const CareerGrowth = () => {
  const [analysis, setAnalysis] = useState<any>(null);
  const [roadmap, setRoadmap] = useState<any>(null);
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [targetType, setTargetType] = useState('TARGET_ROLE');
  const [targetRole, setTargetRole] = useState('Backend Engineer');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const aRes = await learningApi.getGapAnalyses();
      if (aRes.data && aRes.data.length > 0) {
        setAnalysis(aRes.data[0]);
      }
      
      const rRes = await learningApi.getRoadmaps();
      if (rRes.data && rRes.data.length > 0) {
        setRoadmap(rRes.data[0]);
      }
      
      const pRes = await learningApi.getProjectRecommendations();
      if (pRes.data) {
        setProjects(pRes.data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleGenerateAnalysis = async () => {
    setLoading(true);
    try {
      const res = await learningApi.createGapAnalysis({ target_type: targetType, target_role: targetRole });
      setAnalysis(res.data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const handleGenerateRoadmap = async () => {
    if (!analysis) return;
    setLoading(true);
    try {
      const res = await learningApi.createRoadmap(analysis.id, 10);
      setRoadmap(res.data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };
  
  const handleGenerateProjects = async () => {
    if (!analysis) return;
    setLoading(true);
    try {
      const res = await learningApi.generateProjectRecommendations(analysis.id);
      setProjects(res.data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const updateItemStatus = async (itemId: number, status: string) => {
    try {
      await learningApi.updateRoadmapItemStatus(itemId, status);
      fetchData(); // Refresh roadmap
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold Outfit flex items-center gap-2">
          <TrendingUp className="text-accentTeal" />
          Career Growth & Intelligence
        </h1>
        <p className="text-secondaryText mt-1">Identify skill gaps, generate learning roadmaps, and build missing evidence.</p>
      </div>
      
      {/* Target Configuration */}
      <div className="glass-panel p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Target size={20} className="text-blue-400" /> Target Configuration
        </h2>
        <div className="flex flex-wrap items-center gap-4">
          <select 
            className="input-field max-w-[200px]"
            value={targetType}
            onChange={(e) => setTargetType(e.target.value)}
          >
            <option value="TARGET_ROLE">Target Role</option>
            <option value="MARKET_AGGREGATE">Market Aggregate</option>
            <option value="SPECIFIC_JOB">Specific Job (Use Job ID)</option>
          </select>
          <input 
            type="text" 
            className="input-field max-w-[300px]"
            value={targetRole} 
            onChange={(e) => setTargetRole(e.target.value)} 
            placeholder="e.g. Backend Engineer" 
          />
          <button 
            className="btn-primary" 
            onClick={handleGenerateAnalysis} 
            disabled={loading}
          >
            {loading ? 'Generating...' : 'Analyze Skill Gaps'}
          </button>
        </div>
      </div>

      {/* Skill Gap Analysis */}
      {analysis && (
        <div className="glass-panel p-6 border border-cardBorder">
          <h2 className="text-xl font-semibold mb-4">Skill Gap Overview: {analysis.target_role}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {analysis.gap_items.map((gap: any, i: number) => (
              <div key={i} className="bg-darkBg/50 p-4 rounded border border-cardBorder">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-bold text-lg">{gap.canonical_skill}</h3>
                  <span className={`text-xs px-2 py-1 rounded font-medium ${
                    gap.priority_band === 'CRITICAL' ? 'bg-red-500/20 text-red-400' :
                    gap.priority_band === 'HIGH' ? 'bg-orange-500/20 text-orange-400' :
                    'bg-blue-500/20 text-blue-400'
                  }`}>
                    {gap.priority_band}
                  </span>
                </div>
                <p className="text-sm text-secondaryText mb-2">{gap.reason}</p>
                <div className="flex gap-2 text-xs">
                  <span className="bg-gray-800 px-2 py-1 rounded">Target: {gap.requirement_state}</span>
                  <span className="bg-gray-800 px-2 py-1 rounded">Candidate: {gap.candidate_state}</span>
                </div>
              </div>
            ))}
          </div>
          {!roadmap && (
            <div className="mt-6">
              <button className="btn-secondary" onClick={handleGenerateRoadmap} disabled={loading}>
                Generate Learning Roadmap
              </button>
            </div>
          )}
        </div>
      )}
      
      {/* Learning Roadmap */}
      {roadmap && (
        <div className="glass-panel p-6 border border-cardBorder">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <BookOpen size={20} className="text-purple-400" /> Personalized Roadmap
          </h2>
          <div className="space-y-4">
            {roadmap.items.map((item: any, i: number) => (
              <div key={i} className="flex flex-col sm:flex-row justify-between items-start sm:items-center bg-darkBg/50 p-4 rounded border border-cardBorder gap-4">
                <div>
                  <h3 className="font-bold text-lg flex items-center gap-2">
                    <span className="bg-accentTeal/20 text-accentTeal w-6 h-6 rounded-full flex items-center justify-center text-sm">
                      {item.sequence}
                    </span>
                    {item.title}
                  </h3>
                  <p className="text-sm text-secondaryText mt-1">{item.objective} ({item.estimated_effort_hours}h)</p>
                  <span className="inline-block mt-2 text-xs font-medium bg-gray-800 px-2 py-1 rounded">
                    Status: {item.status}
                  </span>
                </div>
                <div>
                  {item.status !== 'COMPLETED' && (
                    <button className="btn-primary text-sm py-1.5" onClick={() => updateItemStatus(item.id, 'COMPLETED')}>
                      Mark Complete
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
          {!projects.length && (
            <div className="mt-6">
              <button className="btn-secondary" onClick={handleGenerateProjects} disabled={loading}>
                Generate Project Recommendations
              </button>
            </div>
          )}
        </div>
      )}
      
      {/* Project Recommendations */}
      {projects.length > 0 && (
        <div className="glass-panel p-6 border border-cardBorder">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Layers size={20} className="text-green-400" /> Recommended Projects
          </h2>
          <p className="text-secondaryText text-sm mb-4">Complete these projects to build verified evidence for your missing skills.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {projects.map((proj: any, i: number) => (
              <div key={i} className="bg-darkBg/50 p-4 rounded border border-cardBorder flex flex-col justify-between">
                <div>
                  <h3 className="font-bold text-lg mb-2">{proj.title}</h3>
                  <p className="text-sm text-secondaryText mb-4">{proj.description}</p>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {proj.target_skills.map((skill: string, j: number) => (
                      <span key={j} className="text-xs bg-accentTeal/10 text-accentTeal px-2 py-1 rounded">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex justify-between items-center mt-2 border-t border-cardBorder pt-2">
                  <span className="text-xs text-secondaryText">Effort: {proj.estimated_effort_hours}h</span>
                  <button className="text-accentTeal text-sm font-medium hover:underline">View Details</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CareerGrowth;
