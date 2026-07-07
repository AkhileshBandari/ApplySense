// mockData.ts - High-Fidelity mockup records for offline previewing

export interface MockProfile {
  name: string;
  email: string;
  phone: string;
  location: string;
  linkedin: string;
  github: string;
  portfolio: string;
  bio: string;
  skills: string[];
  experience: Array<{ company: string; role: string; period: string; description: string }>;
  education: Array<{ school: string; degree: string; year: string }>;
}

export const initialProfile: MockProfile = {
  name: "B. Akhilesh",
  email: "akhilesh.b@applysense.ai",
  phone: "+91 98765 43210",
  location: "Bangalore, India",
  linkedin: "https://linkedin.com/in/akhilesh-b",
  github: "https://github.com/akhilesh-b",
  portfolio: "https://akhilesh.dev",
  bio: "Lead Software Architect with 6+ years of experience designing and deploying cloud-native web systems. Passionate about AI integrations, web scraping automation, and performance tuning.",
  skills: ["React", "TypeScript", "TailwindCSS", "Django", "Django REST Framework", "PostgreSQL", "Redis", "Docker", "Playwright", "Python", "Kubernetes", "AWS", "Electron"],
  experience: [
    {
      company: "Cognitive Systems Labs",
      role: "Lead Software Engineer",
      period: "2023 - Present",
      description: "Designed core backend services using Django REST Framework and Celery task queues. Orchestrated deployment migrations to Docker and Kubernetes, resulting in a 40% reduction in infrastructure overhead. Built automation tooling using Playwright for massive-scale portal scraping."
    },
    {
      company: "PixelTech Global",
      role: "Senior Full-Stack Developer",
      period: "2020 - 2023",
      description: "Created interactive analytics dashboards using React, TypeScript, and Chart.js. Maintained PostgreSQL query execution plans, enhancing page-load times by 30%."
    }
  ],
  education: [
    {
      school: "Indian Institute of Science (IISc)",
      degree: "M.Tech in Computer Science",
      year: "2020"
    },
    {
      school: "National Institute of Technology (NIT Warangal)",
      degree: "B.Tech in Computer Science & Engineering",
      year: "2018"
    }
  ]
};

// ---------- Applications mock data ----------

export interface MockApplication {
  id: number;
  title: string;
  company: string;
  location: string;
  portal_type: string;
  status: string;
  match_score: number;
  applied_at: string;
  notes: Array<{ id: number; date: string; content: string }>;
  interviews: Array<{ id: number; stage: string; date: string }>;
}

export const initialApplications: MockApplication[] = [
  {
    id: 1,
    title: "Senior Full-Stack Engineer",
    company: "TechNova Inc.",
    location: "Remote",
    portal_type: "LinkedIn",
    status: "Interview",
    match_score: 92,
    applied_at: "2026-05-20T10:30:00Z",
    notes: [{ id: 1, date: "2026-05-21", content: "Recruiter reached out on LinkedIn." }],
    interviews: [{ id: 1, stage: "Technical Round 1", date: "2026-06-01" }],
  },
  {
    id: 2,
    title: "Platform Engineer",
    company: "CloudSphere",
    location: "Bangalore, India",
    portal_type: "Greenhouse",
    status: "Applied",
    match_score: 85,
    applied_at: "2026-06-01T14:00:00Z",
    notes: [],
    interviews: [],
  },
  {
    id: 3,
    title: "DevOps & Infrastructure Lead",
    company: "InfraScale",
    location: "Hyderabad, India",
    portal_type: "Lever",
    status: "Under Review",
    match_score: 78,
    applied_at: "2026-06-05T08:15:00Z",
    notes: [{ id: 2, date: "2026-06-06", content: "Application acknowledged via email." }],
    interviews: [],
  },
  {
    id: 4,
    title: "React / TypeScript Frontend Engineer",
    company: "DesignWave",
    location: "Remote",
    portal_type: "Company Website",
    status: "Saved",
    match_score: 90,
    applied_at: "2026-06-10T12:00:00Z",
    notes: [],
    interviews: [],
  },
  {
    id: 5,
    title: "Backend Engineer (Python/Django)",
    company: "DataPulse AI",
    location: "Mumbai, India",
    portal_type: "LinkedIn",
    status: "Offer",
    match_score: 95,
    applied_at: "2026-04-15T09:00:00Z",
    notes: [{ id: 3, date: "2026-05-10", content: "Offer received! Reviewing compensation." }],
    interviews: [
      { id: 2, stage: "HR Screening", date: "2026-04-22" },
      { id: 3, stage: "System Design", date: "2026-05-01" },
    ],
  },
];

// ---------- Resumes mock data ----------

export interface MockResume {
  id: number;
  file_name: string;
  uploaded_at: string;
  health_score: number;
  ats_score: number;
  parsed_data: {
    skills: string[];
    experience_years: number;
  };
}

export const initialResumes: MockResume[] = [
  {
    id: 1,
    file_name: "Akhilesh_Resume_2026.pdf",
    uploaded_at: "2026-06-01T10:00:00Z",
    health_score: 91,
    ats_score: 88,
    parsed_data: {
      skills: ["React", "Python", "Django", "TypeScript", "Docker", "Kubernetes"],
      experience_years: 6,
    },
  },
  {
    id: 2,
    file_name: "Akhilesh_Resume_Backend.pdf",
    uploaded_at: "2026-05-15T08:30:00Z",
    health_score: 85,
    ats_score: 82,
    parsed_data: {
      skills: ["Python", "Django", "PostgreSQL", "Redis", "Celery"],
      experience_years: 6,
    },
  },
];

// ---------- Coach / AI mock data ----------

export interface RoadmapItem {
  skill: string;
  priority: "High" | "Medium" | "Low";
  resources: string[];
  estimated_weeks: number;
}

export const mockRoadmap: RoadmapItem[] = [
  {
    skill: "Kubernetes",
    priority: "High",
    resources: [
      "https://kubernetes.io/docs/tutorials/",
      "KodeKloud CKA Course",
    ],
    estimated_weeks: 4,
  },
  {
    skill: "Next.js",
    priority: "Medium",
    resources: [
      "https://nextjs.org/learn",
      "Vercel Next.js Templates",
    ],
    estimated_weeks: 3,
  },
  {
    skill: "GraphQL",
    priority: "Low",
    resources: [
      "https://graphql.org/learn/",
      "Apollo Server Documentation",
    ],
    estimated_weeks: 2,
  },
];

export interface InterviewPrep {
  behavioral_questions: string[];
  technical_questions: string[];
  tips: string[];
}

export const mockInterviewPrep: InterviewPrep = {
  behavioral_questions: [
    "Describe a time you led a team through a challenging deployment.",
    "How do you handle conflicting priorities between product and engineering?",
    "Tell me about a project where you had to learn a new technology quickly.",
  ],
  technical_questions: [
    "How would you design a scalable job scraping pipeline?",
    "Explain the difference between SSR and CSR in React frameworks.",
    "Walk me through optimizing a slow PostgreSQL query.",
  ],
  tips: [
    "Prepare STAR-format answers for behavioral questions.",
    "Review system design fundamentals (caching, load balancing, microservices).",
    "Practice coding problems on LeetCode focusing on graphs and dynamic programming.",
  ],
};

// ---------- Recommendations mock data ----------

export interface MockRecommendation {
  id: number;
  title: string;
  company: string;
  match_score: number;
  location: string;
}

export const mockRecommendations: MockRecommendation[] = [
  { id: 101, title: "Staff Engineer", company: "Stripe", match_score: 94, location: "Remote" },
  { id: 102, title: "Senior Platform Engineer", company: "Vercel", match_score: 91, location: "Remote" },
  { id: 103, title: "Backend Lead (Django)", company: "Notion", match_score: 89, location: "San Francisco, CA" },
  { id: 104, title: "Full-Stack Developer", company: "Razorpay", match_score: 87, location: "Bangalore, India" },
];
