// Mock data isolated for static Career Readiness UI skeleton

export interface TargetRoleOption {
  id: string;
  label: string;
}

export interface OverviewMetrics {
  overallReadiness: number;
  readinessTrend: string;
  analysesCompleted: number;
  analysesTrend: string;
  topMatchingRole: string;
  matchPercentage: number;
  rolesExplored: number;
  rolesTrend: string;
}

export interface AnalysisHistoryRecord {
  id: string;
  role: string;
  careerLevel: string;
  readinessScore: number;
  date: string;
}

// Combined role and career level options for the target role selector
export const DEMO_TARGET_ROLES: TargetRoleOption[] = [
  { id: "software-testing", label: "Software Testing — Intern" },
  { id: "web-developer", label: "Web Developer — Junior" },
  { id: "data-analyst", label: "Data Analyst — Junior" },
];

// Illustrative dashboard overview metrics displayed in the top summary cards
export const OVERVIEW_STATS: OverviewMetrics = {
  overallReadiness: 78,
  readinessTrend: "+8% vs last month",
  analysesCompleted: 12,
  analysesTrend: "+2 this month",
  topMatchingRole: "Software\nEngineer",
  matchPercentage: 88,
  rolesExplored: 5,
  rolesTrend: "+1 new role this month",
};

// Static historical analysis records matching the demo personas
export const RECENT_ANALYSES: AnalysisHistoryRecord[] = [
  {
    id: "hist-1",
    role: "Software Testing",
    careerLevel: "Intern",
    readinessScore: 78,
    date: "Aug 12, 2026 13:05",
  },
  {
    id: "hist-2",
    role: "Web Developer",
    careerLevel: "Junior",
    readinessScore: 72,
    date: "May 28, 2026 09:44",
  },
  {
    id: "hist-3",
    role: "Data Analyst",
    careerLevel: "Junior",
    readinessScore: 65,
    date: "Jul 10, 2026 02:31",
  },
];

// Single skill match and gap evaluation conforming to C03 analysis schema
export interface ReadinessSkillResult {
  id: string;
  requiredSkillName: string;
  matchedSkillName?: string;
  matchType: "EXACT" | "RELATIONSHIP" | "MISSING" | "UNASSESSED";
  relationshipId?: string;
  coverageCredit: number;
  requiredProficiency: string;
  userProficiency?: string;
  gap?: number;
  resultStatus: "SATISFIED" | "PARTIAL" | "DEFICIENT" | "MISSING" | "UNASSESSED";
  explanation?: string;
}

// Actionable priority gap item conforming to C04 contract
export interface ReadinessPrioritySkill {
  skillId: string;
  skillName: string;
  priorityRank: number;
  learningPriority: number;
  gap: number;
  requiredProficiency?: string;
  explanation?: string;
}

// Full analysis evaluation details consumable by the results modal
export interface DetailedAnalysisResult {
  analysisId: string;
  roleId: string;
  roleName: string;
  careerLevel: string;
  readinessScore: number;
  baselineReadinessScore?: number;
  tier: "EXCELLENT" | "GOOD" | "MODERATE" | "DEVELOPING";
  explanation: string;
  totalRequirements: number;
  satisfiedCount: number;
  partialCount: number;
  missingCount: number;
  skills: ReadinessSkillResult[];
  prioritySkills: ReadinessPrioritySkill[];
}

// Illustrative detailed analysis records keyed by history record ID
export const MOCK_ANALYSIS_DETAILS: Record<string, DetailedAnalysisResult> = {
  "hist-1": {
    analysisId: "hist-1",
    roleId: "software-testing",
    roleName: "Software Engineering",
    careerLevel: "Intern",
    readinessScore: 78,
    baselineReadinessScore: 65,
    tier: "GOOD",
    explanation:
      "You demonstrate a strong foundation in core development skills and problem solving. However, a few key skills required for this role are missing or need improvement.",
    totalRequirements: 22,
    satisfiedCount: 16,
    partialCount: 0,
    missingCount: 6,
    skills: [
      {
        id: "s-1",
        requiredSkillName: "JavaScript",
        matchedSkillName: "JavaScript",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "INTERMEDIATE",
        userProficiency: "INTERMEDIATE",
        gap: 0,
        resultStatus: "SATISFIED",
        explanation: "Verified through student repository portfolio",
      },
      {
        id: "s-2",
        requiredSkillName: "HTML & CSS",
        matchedSkillName: "HTML & CSS",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "INTERMEDIATE",
        userProficiency: "ADVANCED",
        gap: 0,
        resultStatus: "SATISFIED",
        explanation: "Exceeds required tier for layout and responsive styling",
      },
      {
        id: "s-3",
        requiredSkillName: "Git & GitHub",
        matchedSkillName: "Git & GitHub",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "BEGINNER",
        userProficiency: "INTERMEDIATE",
        gap: 0,
        resultStatus: "SATISFIED",
        explanation: "Active contributor with verified branching and commit workflows",
      },
      {
        id: "s-4",
        requiredSkillName: "Problem Solving",
        matchedSkillName: "Problem Solving",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "INTERMEDIATE",
        userProficiency: "INTERMEDIATE",
        gap: 0,
        resultStatus: "SATISFIED",
        explanation: "Demonstrated through algorithmic problem sets",
      },
      {
        id: "s-5",
        requiredSkillName: "SQL Basics",
        matchedSkillName: "PostgreSQL",
        matchType: "RELATIONSHIP",
        relationshipId: "REL-SQL-01",
        coverageCredit: 0.9,
        requiredProficiency: "BEGINNER",
        userProficiency: "BEGINNER",
        gap: 0,
        resultStatus: "SATISFIED",
        explanation: "Verified through relational database querying projects",
      },
      {
        id: "s-6",
        requiredSkillName: "Unit Testing Fundamentals",
        matchedSkillName: "Manual & Unit Testing",
        matchType: "RELATIONSHIP",
        relationshipId: "REL-TEST-02",
        coverageCredit: 0.85,
        requiredProficiency: "BEGINNER",
        userProficiency: "BEGINNER",
        gap: 0,
        resultStatus: "SATISFIED",
        explanation: "Test case authoring confirmed in academic coursework",
      },
      {
        id: "s-7",
        requiredSkillName: "Node.js Basics",
        matchedSkillName: "Node.js",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "BEGINNER",
        userProficiency: "INTERMEDIATE",
        gap: 0,
        resultStatus: "SATISFIED",
        explanation: "Runtime environment and module usage verified",
      },
      {
        id: "s-8",
        requiredSkillName: "Object-Oriented Design",
        matchedSkillName: "OOP in Java",
        matchType: "RELATIONSHIP",
        relationshipId: "REL-OOP-05",
        coverageCredit: 0.95,
        requiredProficiency: "INTERMEDIATE",
        userProficiency: "INTERMEDIATE",
        gap: 0,
        resultStatus: "SATISFIED",
        explanation: "Software design principles and pattern familiarity",
      },
      {
        id: "s-9",
        requiredSkillName: "Command Line & Bash",
        matchedSkillName: "Bash Scripting",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "BEGINNER",
        userProficiency: "BEGINNER",
        gap: 0,
        resultStatus: "SATISFIED",
        explanation: "Terminal navigation and automation scripting",
      },
      {
        id: "s-10",
        requiredSkillName: "Data Structures",
        matchedSkillName: "Data Structures",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "INTERMEDIATE",
        userProficiency: "INTERMEDIATE",
        gap: 0,
        resultStatus: "SATISFIED",
        explanation: "Trees, hash tables, and graph algorithms verified",
      },
      {
        id: "s-11",
        requiredSkillName: "Code Review Practices",
        matchedSkillName: "GitHub PR Reviews",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "BEGINNER",
        userProficiency: "BEGINNER",
        gap: 0,
        resultStatus: "SATISFIED",
        explanation: "Collaborative peer review contributions confirmed",
      },
      {
        id: "s-12",
        requiredSkillName: "Agile & Scrum Basics",
        matchedSkillName: "Agile Development",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "BEGINNER",
        userProficiency: "BEGINNER",
        gap: 0,
        resultStatus: "SATISFIED",
        explanation: "Sprint participation and backlog grooming",
      },
      {
        id: "s-13",
        requiredSkillName: "HTTP Protocol & Web Concepts",
        matchedSkillName: "Web Fundamentals",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "BEGINNER",
        userProficiency: "INTERMEDIATE",
        gap: 0,
        resultStatus: "SATISFIED",
        explanation: "Headers, status codes, and browser lifecycle",
      },
      {
        id: "s-14",
        requiredSkillName: "Technical Documentation",
        matchedSkillName: "Markdown & Docs",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "BEGINNER",
        userProficiency: "INTERMEDIATE",
        gap: 0,
        resultStatus: "SATISFIED",
        explanation: "Clear README documentation and API guides",
      },
      {
        id: "s-15",
        requiredSkillName: "Debugging & DevTools",
        matchedSkillName: "Browser DevTools",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "BEGINNER",
        userProficiency: "INTERMEDIATE",
        gap: 0,
        resultStatus: "SATISFIED",
        explanation: "Network inspection and breakpoint profiling",
      },
      {
        id: "s-16",
        requiredSkillName: "Software Security Basics",
        matchedSkillName: "OWASP Principles",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "BEGINNER",
        userProficiency: "BEGINNER",
        gap: 0,
        resultStatus: "SATISFIED",
        explanation: "Authentication hygiene and injection prevention",
      },
      {
        id: "s-17",
        requiredSkillName: "React.js",
        matchType: "MISSING",
        coverageCredit: 0.0,
        requiredProficiency: "INTERMEDIATE",
        gap: 1.0,
        resultStatus: "MISSING",
        explanation: "Key modern frontend library not found in profile",
      },
      {
        id: "s-18",
        requiredSkillName: "RESTful APIs",
        matchType: "MISSING",
        coverageCredit: 0.0,
        requiredProficiency: "INTERMEDIATE",
        gap: 0.9,
        resultStatus: "MISSING",
        explanation: "API route design and response serialization needed",
      },
      {
        id: "s-19",
        requiredSkillName: "Testing (Jest)",
        matchType: "MISSING",
        coverageCredit: 0.0,
        requiredProficiency: "BEGINNER",
        gap: 0.85,
        resultStatus: "MISSING",
        explanation: "Automated assertion and mock runner required",
      },
      {
        id: "s-20",
        requiredSkillName: "CI/CD Basics",
        matchType: "MISSING",
        coverageCredit: 0.0,
        requiredProficiency: "BEGINNER",
        gap: 0.8,
        resultStatus: "MISSING",
        explanation: "Automated build and test pipeline experience needed",
      },
      {
        id: "s-21",
        requiredSkillName: "TypeScript",
        matchType: "MISSING",
        coverageCredit: 0.0,
        requiredProficiency: "INTERMEDIATE",
        gap: 0.75,
        resultStatus: "MISSING",
        explanation: "Type-safe interface modeling and compiler tooling needed",
      },
      {
        id: "s-22",
        requiredSkillName: "Postman & API Client Testing",
        matchType: "MISSING",
        coverageCredit: 0.0,
        requiredProficiency: "BEGINNER",
        gap: 0.6,
        resultStatus: "MISSING",
        explanation: "Collection testing and mock server setup needed",
      },
    ],
    prioritySkills: [
      {
        skillId: "SK-REACT-01",
        skillName: "React.js",
        priorityRank: 1,
        learningPriority: 0.88,
        gap: 1.0,
        requiredProficiency: "INTERMEDIATE",
        explanation: "Highest impact skill for entry frontend and full-stack positions",
      },
      {
        skillId: "SK-REST-02",
        skillName: "RESTful APIs",
        priorityRank: 2,
        learningPriority: 0.81,
        gap: 0.9,
        requiredProficiency: "INTERMEDIATE",
        explanation: "Essential for integrating client applications with enterprise backends",
      },
      {
        skillId: "SK-TS-03",
        skillName: "TypeScript",
        priorityRank: 3,
        learningPriority: 0.74,
        gap: 0.75,
        requiredProficiency: "INTERMEDIATE",
        explanation: "Rapidly growing industry requirement for robust software development",
      },
      {
        skillId: "SK-TEST-04",
        skillName: "Testing (Jest)",
        priorityRank: 4,
        learningPriority: 0.68,
        gap: 0.85,
        requiredProficiency: "BEGINNER",
        explanation: "Automated unit testing guarantees software reliability in production",
      },
      {
        skillId: "SK-CICD-05",
        skillName: "CI/CD Basics",
        priorityRank: 5,
        learningPriority: 0.62,
        gap: 0.8,
        requiredProficiency: "BEGINNER",
        explanation: "Continuous integration workflows accelerate shipping frequency",
      },
    ],
  },
  "hist-2": {
    analysisId: "hist-2",
    roleId: "web-developer",
    roleName: "Web Developer",
    careerLevel: "Junior",
    readinessScore: 72,
    baselineReadinessScore: 60,
    tier: "GOOD",
    explanation:
      "Good alignment with frontend layout and client script fundamentals. Strengthening component frameworks and automated testing will push your readiness to high tier.",
    totalRequirements: 18,
    satisfiedCount: 13,
    partialCount: 0,
    missingCount: 5,
    skills: [
      {
        id: "w-1",
        requiredSkillName: "HTML5 & CSS3",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "ADVANCED",
        resultStatus: "SATISFIED",
        gap: 0,
      },
      {
        id: "w-2",
        requiredSkillName: "JavaScript ES6+",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "INTERMEDIATE",
        resultStatus: "SATISFIED",
        gap: 0,
      },
      {
        id: "w-3",
        requiredSkillName: "Responsive Web Design",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "ADVANCED",
        resultStatus: "SATISFIED",
        gap: 0,
      },
      {
        id: "w-4",
        requiredSkillName: "Git & Version Control",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "INTERMEDIATE",
        resultStatus: "SATISFIED",
        gap: 0,
      },
      {
        id: "w-5",
        requiredSkillName: "Tailwind CSS",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "INTERMEDIATE",
        resultStatus: "SATISFIED",
        gap: 0,
      },
      {
        id: "w-6",
        requiredSkillName: "Web Accessibility (a11y)",
        matchType: "MISSING",
        coverageCredit: 0.0,
        requiredProficiency: "INTERMEDIATE",
        resultStatus: "MISSING",
        gap: 0.8,
      },
      {
        id: "w-7",
        requiredSkillName: "Next.js / SSR",
        matchType: "MISSING",
        coverageCredit: 0.0,
        requiredProficiency: "INTERMEDIATE",
        resultStatus: "MISSING",
        gap: 0.9,
      },
      {
        id: "w-8",
        requiredSkillName: "Testing with Playwright",
        matchType: "MISSING",
        coverageCredit: 0.0,
        requiredProficiency: "BEGINNER",
        resultStatus: "MISSING",
        gap: 0.7,
      },
    ],
    prioritySkills: [
      {
        skillId: "SK-NEXT-01",
        skillName: "Next.js / SSR",
        priorityRank: 1,
        learningPriority: 0.84,
        gap: 0.9,
      },
      {
        skillId: "SK-A11Y-02",
        skillName: "Web Accessibility (a11y)",
        priorityRank: 2,
        learningPriority: 0.76,
        gap: 0.8,
      },
      {
        skillId: "SK-PW-03",
        skillName: "Testing with Playwright",
        priorityRank: 3,
        learningPriority: 0.65,
        gap: 0.7,
      },
    ],
  },
  "hist-3": {
    analysisId: "hist-3",
    roleId: "data-analyst",
    roleName: "Data Analyst",
    careerLevel: "Junior",
    readinessScore: 65,
    baselineReadinessScore: 50,
    tier: "MODERATE",
    explanation:
      "Solid quantitative foundation with good SQL querying skills. Expanding your data visualization tooling and statistical modeling will elevate your score.",
    totalRequirements: 20,
    satisfiedCount: 13,
    partialCount: 0,
    missingCount: 7,
    skills: [
      {
        id: "d-1",
        requiredSkillName: "SQL Querying",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "INTERMEDIATE",
        resultStatus: "SATISFIED",
        gap: 0,
      },
      {
        id: "d-2",
        requiredSkillName: "Python for Data Analysis",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "INTERMEDIATE",
        resultStatus: "SATISFIED",
        gap: 0,
      },
      {
        id: "d-3",
        requiredSkillName: "Pandas & NumPy",
        matchType: "EXACT",
        coverageCredit: 1.0,
        requiredProficiency: "INTERMEDIATE",
        resultStatus: "SATISFIED",
        gap: 0,
      },
      {
        id: "d-4",
        requiredSkillName: "Power BI / Tableau",
        matchType: "MISSING",
        coverageCredit: 0.0,
        requiredProficiency: "INTERMEDIATE",
        resultStatus: "MISSING",
        gap: 0.95,
      },
      {
        id: "d-5",
        requiredSkillName: "Statistical Modeling",
        matchType: "MISSING",
        coverageCredit: 0.0,
        requiredProficiency: "INTERMEDIATE",
        resultStatus: "MISSING",
        gap: 0.85,
      },
    ],
    prioritySkills: [
      {
        skillId: "SK-BI-01",
        skillName: "Power BI / Tableau",
        priorityRank: 1,
        learningPriority: 0.89,
        gap: 0.95,
      },
      {
        skillId: "SK-STAT-02",
        skillName: "Statistical Modeling",
        priorityRank: 2,
        learningPriority: 0.79,
        gap: 0.85,
      },
      {
        skillId: "SK-ETL-03",
        skillName: "ETL Pipeline Basics",
        priorityRank: 3,
        learningPriority: 0.71,
        gap: 0.75,
      },
    ],
  },
};

// Retrieve or dynamically generate detailed analysis information for any history item
export function getAnalysisDetail(historyItem: AnalysisHistoryRecord): DetailedAnalysisResult {
  const existing = MOCK_ANALYSIS_DETAILS[historyItem.id];
  if (existing) {
    return existing;
  }

  // Fallback generator maintaining consistent metrics with the history record
  return {
    analysisId: historyItem.id,
    roleId: historyItem.role.toLowerCase().replace(/\s+/g, "-"),
    roleName: historyItem.role,
    careerLevel: historyItem.careerLevel,
    readinessScore: historyItem.readinessScore,
    baselineReadinessScore: Math.max(0, historyItem.readinessScore - 12),
    tier: historyItem.readinessScore >= 80 ? "EXCELLENT" : historyItem.readinessScore >= 70 ? "GOOD" : "MODERATE",
    explanation: `Evaluation of demonstrated competencies against current industry requirements for ${historyItem.role}.`,
    totalRequirements: 20,
    satisfiedCount: Math.round((historyItem.readinessScore / 100) * 20),
    partialCount: 0,
    missingCount: 20 - Math.round((historyItem.readinessScore / 100) * 20),
    skills: [],
    prioritySkills: [],
  };
}
