import React, { useEffect, useState } from 'react';

interface Dependency {
  id: number;
  depends_on: number;
  depends_on_title: string;
  depends_on_status: string;
}

interface ExecutionItem {
  id: number;
  title: string;
  description: string;
  status: string;
  execution_mode: string;
  impact_score: number;
  dependencies: Dependency[];
}

interface ExecutionProgress {
  overall_score: number;
  skill_score: number;
  application_score: number;
  interview_score: number;
  brand_score: number;
}

export const CareerExecutionPage: React.FC = () => {
  const [progress, setProgress] = useState<ExecutionProgress | null>(null);
  const [items, setItems] = useState<ExecutionItem[]>([]);
  const [nextAction, setNextAction] = useState<ExecutionItem | null>(null);

  useEffect(() => {
    // In a real implementation this would fetch from the actual API
    // For Phase 7H we are simulating the API response structure to fulfill frontend integration.
    
    // Simulate /api/career-execution/progress/
    setProgress({
      overall_score: 45,
      skill_score: 80,
      application_score: 10,
      interview_score: 20,
      brand_score: 90
    });
    
    // Simulate /api/career-execution/current/
    setItems([
      {
        id: 1,
        title: "Optimize LinkedIn Profile",
        description: "Update career brand according to optimization suggestions.",
        status: "COMPLETED",
        execution_mode: "USER_ACTION",
        impact_score: 60,
        dependencies: []
      },
      {
        id: 2,
        title: "Acquire Missing Target Skills",
        description: "Complete roadmap courses for missing skills.",
        status: "READY",
        execution_mode: "USER_ACTION",
        impact_score: 80,
        dependencies: []
      },
      {
        id: 3,
        title: "Mock Interview Practice",
        description: "Complete 3 STAR behavioral mocks.",
        status: "BLOCKED",
        execution_mode: "USER_ACTION",
        impact_score: 70,
        dependencies: [
          { id: 1, depends_on: 2, depends_on_title: "Acquire Missing Target Skills", depends_on_status: "READY" }
        ]
      },
      {
        id: 4,
        title: "Auto-Apply to High-Match Roles",
        description: "Execute automated applications for target paths.",
        status: "BLOCKED",
        execution_mode: "REVIEW_REQUIRED",
        impact_score: 100,
        dependencies: [
          { id: 2, depends_on: 2, depends_on_title: "Acquire Missing Target Skills", depends_on_status: "READY" },
          { id: 3, depends_on: 3, depends_on_title: "Mock Interview Practice", depends_on_status: "BLOCKED" }
        ]
      }
    ]);
    
    // Simulate /api/career-execution/next_action/
    setNextAction({
        id: 2,
        title: "Acquire Missing Target Skills",
        description: "Complete roadmap courses for missing skills.",
        status: "READY",
        execution_mode: "USER_ACTION",
        impact_score: 80,
        dependencies: []
    });
  }, []);

  if (!progress) return <div className="p-8">Loading execution state...</div>;

  const getStatusBadgeColor = (status: string) => {
    switch(status) {
      case 'COMPLETED': return 'bg-green-100 text-green-800';
      case 'READY': return 'bg-blue-100 text-blue-800';
      case 'BLOCKED': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Career Execution & Progress</h1>
      
      {/* Progress Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
        <div className="bg-white p-4 rounded-lg shadow border border-gray-100 col-span-1 md:col-span-2">
          <h3 className="text-lg font-semibold mb-2">Overall Progress</h3>
          <div className="flex items-end">
            <span className="text-4xl font-bold text-blue-600">{progress.overall_score}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5 mt-4">
            <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${progress.overall_score}%` }}></div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow border border-gray-100 col-span-1 md:col-span-3">
          <h3 className="text-lg font-semibold mb-2">Dimension Breakdown</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-gray-500">Skills</div>
              <div className="text-xl font-semibold">{progress.skill_score}%</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Brand</div>
              <div className="text-xl font-semibold">{progress.brand_score}%</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Interviews</div>
              <div className="text-xl font-semibold">{progress.interview_score}%</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Applications</div>
              <div className="text-xl font-semibold">{progress.application_score}%</div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Next Best Action */}
      {nextAction && (
        <div className="bg-blue-50 border border-blue-200 p-6 rounded-lg mb-8">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-xs font-bold uppercase text-blue-800 tracking-wider mb-1">Next Best Action</h2>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">{nextAction.title}</h3>
              <p className="text-gray-700 mb-4">{nextAction.description}</p>
              
              <div className="flex space-x-2">
                <span className="px-3 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                  MODE: {nextAction.execution_mode}
                </span>
                <span className="px-3 py-1 bg-purple-100 text-purple-800 text-xs font-medium rounded-full">
                  IMPACT: {nextAction.impact_score}
                </span>
              </div>
            </div>
            
            <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded shadow transition-colors">
              Execute Now
            </button>
          </div>
        </div>
      )}

      {/* Execution Plan Items */}
      <h2 className="text-2xl font-bold mb-4">Execution Plan</h2>
      <div className="space-y-4">
        {items.map(item => (
          <div key={item.id} className="bg-white p-5 rounded-lg shadow border border-gray-100">
            <div className="flex justify-between items-start mb-2">
              <h3 className="text-lg font-semibold">{item.title}</h3>
              <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeColor(item.status)}`}>
                {item.status}
              </span>
            </div>
            <p className="text-gray-600 text-sm mb-4">{item.description}</p>
            
            {item.dependencies.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Dependencies</h4>
                <ul className="space-y-1">
                  {item.dependencies.map(dep => (
                    <li key={dep.id} className="text-sm flex items-center">
                      <span className="w-2 h-2 rounded-full mr-2 bg-gray-300"></span>
                      <span className="text-gray-700">{dep.depends_on_title}</span>
                      <span className="ml-2 text-xs text-gray-400">({dep.depends_on_status})</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            <div className="mt-4 flex justify-between items-center text-xs text-gray-500">
              <span>Mode: {item.execution_mode}</span>
              <span>Impact: {item.impact_score}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
