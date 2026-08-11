import React, { useState, useEffect } from 'react';
import evidenceApi from '../services/api/evidence';

const CareerEvidencePage: React.FC = () => {
  const [githubConnection, setGithubConnection] = useState<any>(null);
  const [portfolioConnection, setPortfolioConnection] = useState<any>(null);
  const [repositories, setRepositories] = useState<any[]>([]);
  const [evidence, setEvidence] = useState<any[]>([]);
  
  const [githubUsername, setGithubUsername] = useState('');
  const [githubToken, setGithubToken] = useState('');
  const [portfolioUrl, setPortfolioUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const gh = await evidenceApi.getGitHubConnection();
      setGithubConnection(gh);
      
      const port = await evidenceApi.getPortfolioConnection();
      setPortfolioConnection(port);
      
      const repos = await evidenceApi.getRepositories();
      setRepositories(repos);
      
      const evs = await evidenceApi.getSkillEvidence();
      setEvidence(evs);
    } catch (e: any) {
      setError(e.message || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleConnectGitHub = async () => {
    if (!githubUsername) return;
    try {
      setLoading(true);
      await evidenceApi.connectGitHub(githubUsername, githubToken);
      await fetchData();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSyncGitHub = async () => {
    if (!githubConnection) return;
    try {
      setLoading(true);
      await evidenceApi.syncGitHub(githubConnection.id);
      await fetchData();
    } catch (e: any) {
      setError(e.response?.data?.error || e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleConnectPortfolio = async () => {
    if (!portfolioUrl) return;
    try {
      setLoading(true);
      await evidenceApi.connectPortfolio(portfolioUrl);
      await fetchData();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzePortfolio = async () => {
    if (!portfolioConnection) return;
    try {
      setLoading(true);
      await evidenceApi.analyzePortfolio(portfolioConnection.id);
      await fetchData();
    } catch (e: any) {
      setError(e.response?.data?.error || e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReviewEvidence = async (id: number, action: 'ACCEPT' | 'REJECT') => {
    try {
      setLoading(true);
      await evidenceApi.reviewEvidence(id, action);
      await fetchData();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-gray-800">Career Evidence & Intelligence</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4">
          <strong className="font-bold">Error! </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        {/* GitHub Panel */}
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100">
          <h2 className="text-2xl font-semibold mb-4 flex items-center">
            <span className="mr-2">GitHub Integration</span>
          </h2>
          
          {githubConnection ? (
            <div>
              <p className="text-green-600 font-medium mb-2">✓ Connected as {githubConnection.github_username}</p>
              <p className="text-sm text-gray-500 mb-4">
                Status: {githubConnection.sync_status} <br/>
                Last Sync: {githubConnection.last_synced_at ? new Date(githubConnection.last_synced_at).toLocaleString() : 'Never'}
              </p>
              <button 
                onClick={handleSyncGitHub} 
                disabled={loading}
                className="bg-gray-800 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
              >
                Sync Repositories
              </button>
            </div>
          ) : (
            <div>
              <input 
                type="text" 
                placeholder="GitHub Username" 
                value={githubUsername}
                onChange={e => setGithubUsername(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded mb-3"
              />
              <input 
                type="password" 
                placeholder="Optional PAT (for private repos)" 
                value={githubToken}
                onChange={e => setGithubToken(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded mb-4"
              />
              <button 
                onClick={handleConnectGitHub} 
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded w-full"
              >
                Connect GitHub
              </button>
            </div>
          )}
        </div>

        {/* Portfolio Panel */}
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100">
          <h2 className="text-2xl font-semibold mb-4">Portfolio Integration</h2>
          
          {portfolioConnection ? (
            <div>
              <p className="text-green-600 font-medium mb-2">✓ Connected: {portfolioConnection.portfolio_url}</p>
              <p className="text-sm text-gray-500 mb-4">
                Status: {portfolioConnection.analysis_status} <br/>
                Last Analyzed: {portfolioConnection.last_analyzed_at ? new Date(portfolioConnection.last_analyzed_at).toLocaleString() : 'Never'}
              </p>
              <button 
                onClick={handleAnalyzePortfolio} 
                disabled={loading}
                className="bg-gray-800 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
              >
                Analyze Portfolio
              </button>
            </div>
          ) : (
            <div>
              <input 
                type="text" 
                placeholder="https://your-portfolio.com" 
                value={portfolioUrl}
                onChange={e => setPortfolioUrl(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded mb-4"
              />
              <button 
                onClick={handleConnectPortfolio} 
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded w-full"
              >
                Connect Portfolio
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100 mb-8">
        <h2 className="text-2xl font-semibold mb-4">Evidence Review Queue</h2>
        <p className="text-gray-600 mb-4 text-sm">
          Accepting evidence does not fabricate experience. It sends evidence through ApplySense's candidate verification workflow.
        </p>
        
        {evidence.length === 0 ? (
          <p className="text-gray-500 italic">No evidence pending review.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white">
              <thead>
                <tr>
                  <th className="py-2 px-4 border-b text-left text-sm font-semibold text-gray-600">Skill</th>
                  <th className="py-2 px-4 border-b text-left text-sm font-semibold text-gray-600">Source</th>
                  <th className="py-2 px-4 border-b text-left text-sm font-semibold text-gray-600">Context</th>
                  <th className="py-2 px-4 border-b text-left text-sm font-semibold text-gray-600">Status</th>
                  <th className="py-2 px-4 border-b text-left text-sm font-semibold text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {evidence.map(e => (
                  <tr key={e.id} className="hover:bg-gray-50">
                    <td className="py-2 px-4 border-b font-medium">{e.skill_name}</td>
                    <td className="py-2 px-4 border-b text-sm text-gray-600">
                      <span className="bg-gray-100 px-2 py-1 rounded">{e.source_type}</span>
                    </td>
                    <td className="py-2 px-4 border-b text-sm text-gray-600">
                      {e.repository_name || e.portfolio_project_title} - {e.evidence_type}
                    </td>
                    <td className="py-2 px-4 border-b text-sm">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        e.status === 'DETECTED' ? 'bg-yellow-100 text-yellow-800' :
                        e.status === 'ACCEPTED' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {e.status}
                      </span>
                    </td>
                    <td className="py-2 px-4 border-b">
                      {e.status === 'DETECTED' && (
                        <div className="flex space-x-2">
                          <button 
                            onClick={() => handleReviewEvidence(e.id, 'ACCEPT')}
                            className="bg-green-500 hover:bg-green-600 text-white text-xs py-1 px-2 rounded"
                          >
                            Accept
                          </button>
                          <button 
                            onClick={() => handleReviewEvidence(e.id, 'REJECT')}
                            className="bg-red-500 hover:bg-red-600 text-white text-xs py-1 px-2 rounded"
                          >
                            Reject
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100">
        <h2 className="text-2xl font-semibold mb-4">Discovered Repositories</h2>
        {repositories.length === 0 ? (
          <p className="text-gray-500 italic">No repositories discovered yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {repositories.map(repo => (
              <div key={repo.id} className="border border-gray-200 p-4 rounded-lg hover:shadow-md transition-shadow">
                <h3 className="font-bold text-lg mb-1 truncate">
                  <a href={repo.repository_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                    {repo.name}
                  </a>
                </h3>
                <p className="text-sm text-gray-600 mb-2 h-10 overflow-hidden">{repo.description}</p>
                <div className="flex items-center text-xs text-gray-500 space-x-3">
                  {repo.primary_language && <span>{repo.primary_language}</span>}
                  <span>★ {repo.stars}</span>
                  {repo.is_fork && <span className="bg-gray-100 px-1 rounded">Fork</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CareerEvidencePage;
