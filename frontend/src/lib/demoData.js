// ── Cluster Colors ──────────────────────────────────────────────────
export const CLUSTER_COLORS = ['#7c3aed', '#3b82f6', '#10b981', '#f59e0b', '#ef4444']

export const CLUSTER_NAMES = [
  'Full-Stack Architects',
  'Data & ML Engineers',
  'Cloud-Native DevOps',
  'Frontend Craftsmen',
  'Systems & Embedded',
]

// ── Helper: seeded random ───────────────────────────────────────────
function seeded(seed) {
  let s = seed
  return () => {
    s = (s * 16807) % 2147483647
    return (s - 1) / 2147483646
  }
}

// ── UMAP Scatter Points ────────────────────────────────────────────
function generateClusterPoints(cx, cy, n, spread, clusterId, rng) {
  const points = []
  for (let i = 0; i < n; i++) {
    const angle = rng() * Math.PI * 2
    const r = Math.sqrt(-2 * Math.log(rng())) * spread
    points.push({
      x: +(cx + r * Math.cos(angle)).toFixed(2),
      y: +(cy + r * Math.sin(angle)).toFixed(2),
      cluster: clusterId,
      salary: Math.round(40000 + rng() * 160000),
      experience: Math.round(1 + rng() * 25),
      language: ['Python', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'Java', 'C++', 'C#'][Math.floor(rng() * 8)],
      stage: ['Junior', 'Mid', 'Senior', 'Staff', 'Principal'][Math.floor(rng() * 5)],
    })
  }
  return points
}

const rng = seeded(42)
const clusterCenters = [
  { cx: -5, cy: 3 },
  { cx: 4, cy: 5 },
  { cx: -3, cy: -4 },
  { cx: 6, cy: -2 },
  { cx: 0, cy: -7 },
]

export const umapPoints = clusterCenters.flatMap((c, i) =>
  generateClusterPoints(c.cx, c.cy, 200 + Math.floor(rng() * 60), 2.2, i, rng)
)

// ── Cluster Profiles ────────────────────────────────────────────────
export const clusterProfiles = [
  {
    id: 0,
    name: 'Full-Stack Architects',
    count: 14231,
    avgSalary: 128500,
    avgExperience: 8.3,
    topTechs: ['JavaScript', 'TypeScript', 'React', 'Node.js', 'PostgreSQL'],
    description: 'Versatile engineers who span the entire stack, from pixel-perfect UIs to robust backend APIs.',
    satisfaction: 4.1,
    remoteRatio: 0.72,
    churnRate: 0.18,
  },
  {
    id: 1,
    name: 'Data & ML Engineers',
    count: 12876,
    avgSalary: 142000,
    avgExperience: 6.7,
    topTechs: ['Python', 'TensorFlow', 'SQL', 'Spark', 'Docker'],
    description: 'Data-driven builders who turn raw datasets into production ML pipelines and actionable insights.',
    satisfaction: 4.3,
    remoteRatio: 0.68,
    churnRate: 0.14,
  },
  {
    id: 2,
    name: 'Cloud-Native DevOps',
    count: 13542,
    avgSalary: 135000,
    avgExperience: 7.1,
    topTechs: ['AWS', 'Kubernetes', 'Terraform', 'Go', 'Docker'],
    description: 'Infrastructure artisans who design, deploy, and keep planet-scale systems running 24/7.',
    satisfaction: 3.9,
    remoteRatio: 0.65,
    churnRate: 0.21,
  },
  {
    id: 3,
    name: 'Frontend Craftsmen',
    count: 12988,
    avgSalary: 115000,
    avgExperience: 5.4,
    topTechs: ['React', 'TypeScript', 'CSS', 'Next.js', 'Figma'],
    description: 'Experience-obsessed developers who craft beautiful, accessible, and lightning-fast interfaces.',
    satisfaction: 4.0,
    remoteRatio: 0.78,
    churnRate: 0.24,
  },
  {
    id: 4,
    name: 'Systems & Embedded',
    count: 11800,
    avgSalary: 132000,
    avgExperience: 9.5,
    topTechs: ['C++', 'Rust', 'C', 'Linux', 'Assembly'],
    description: 'Low-level specialists who write the code closest to the metal — firmware, kernels, and real-time systems.',
    satisfaction: 3.8,
    remoteRatio: 0.52,
    churnRate: 0.12,
  },
]

// ── Technology Forecast ─────────────────────────────────────────────
const techCategories = {
  Languages: ['Python', 'JavaScript', 'TypeScript', 'Rust', 'Go', 'Java', 'C++', 'C#', 'Kotlin', 'Swift'],
  Databases: ['PostgreSQL', 'MongoDB', 'Redis', 'MySQL', 'DynamoDB'],
  Frameworks: ['React', 'Next.js', 'Django', 'FastAPI', 'Spring Boot'],
  'AI Tools': ['GitHub Copilot', 'ChatGPT', 'TensorFlow', 'PyTorch', 'LangChain'],
  Cloud: ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes'],
}

export { techCategories }

function generateTechForecast(name, base, growth, volatility) {
  const rng2 = seeded(name.length * 137)
  const years = [2022, 2023, 2024, 2025, 2026]
  return years.map((year, i) => {
    const isForecast = year >= 2025
    const val = Math.min(95, Math.max(2, base + growth * i + (rng2() - 0.5) * volatility))
    return {
      year,
      adoption: +val.toFixed(1),
      low: isForecast ? +Math.max(1, val - 4 - rng2() * 3).toFixed(1) : null,
      high: isForecast ? +Math.min(98, val + 4 + rng2() * 3).toFixed(1) : null,
      isForecast,
    }
  })
}

export const forecastData = {
  Python: generateTechForecast('Python', 48, 5.2, 3),
  JavaScript: generateTechForecast('JavaScript', 65, -1.5, 4),
  TypeScript: generateTechForecast('TypeScript', 30, 8.5, 3),
  Rust: generateTechForecast('Rust', 6, 4.8, 2),
  Go: generateTechForecast('Go', 14, 3.0, 2.5),
  Java: generateTechForecast('Java', 35, -2.0, 3),
  'C++': generateTechForecast('C++', 22, -0.5, 2),
  'C#': generateTechForecast('C#', 28, 0.8, 2),
  Kotlin: generateTechForecast('Kotlin', 10, 3.5, 2),
  Swift: generateTechForecast('Swift', 8, 2.0, 1.5),
  PostgreSQL: generateTechForecast('PostgreSQL', 42, 5.0, 3),
  MongoDB: generateTechForecast('MongoDB', 28, 1.5, 3),
  Redis: generateTechForecast('Redis', 22, 3.0, 2),
  MySQL: generateTechForecast('MySQL', 50, -3.0, 4),
  DynamoDB: generateTechForecast('DynamoDB', 12, 3.5, 2),
  React: generateTechForecast('React', 42, 3.5, 3),
  'Next.js': generateTechForecast('Next.js', 15, 7.5, 3),
  Django: generateTechForecast('Django', 18, 1.5, 2),
  FastAPI: generateTechForecast('FastAPI', 5, 6.5, 2),
  'Spring Boot': generateTechForecast('Spring Boot', 20, 0.5, 2.5),
  'GitHub Copilot': generateTechForecast('GitHub Copilot', 5, 12, 4),
  ChatGPT: generateTechForecast('ChatGPT', 2, 15, 5),
  TensorFlow: generateTechForecast('TensorFlow', 32, -1.0, 3),
  PyTorch: generateTechForecast('PyTorch', 24, 5.5, 3),
  LangChain: generateTechForecast('LangChain', 1, 10, 3),
  AWS: generateTechForecast('AWS', 52, 2.0, 3),
  Azure: generateTechForecast('Azure', 30, 3.5, 3),
  GCP: generateTechForecast('GCP', 22, 2.5, 2.5),
  Docker: generateTechForecast('Docker', 55, 3.0, 3),
  Kubernetes: generateTechForecast('Kubernetes', 30, 5.0, 3),
}

export const TECH_COLORS = {
  Python: '#3776ab',
  JavaScript: '#f7df1e',
  TypeScript: '#3178c6',
  Rust: '#dea584',
  Go: '#00add8',
  Java: '#ed8b00',
  'C++': '#00599c',
  'C#': '#239120',
  Kotlin: '#7F52FF',
  Swift: '#FA7343',
  PostgreSQL: '#4169e1',
  MongoDB: '#47A248',
  Redis: '#DC382D',
  MySQL: '#4479A1',
  DynamoDB: '#4053D6',
  React: '#61dafb',
  'Next.js': '#ffffff',
  Django: '#092e20',
  FastAPI: '#009688',
  'Spring Boot': '#6db33f',
  'GitHub Copilot': '#8957e5',
  ChatGPT: '#10a37f',
  TensorFlow: '#ff6f00',
  PyTorch: '#ee4c2c',
  LangChain: '#1c3c3c',
  AWS: '#ff9900',
  Azure: '#0078d4',
  GCP: '#4285f4',
  Docker: '#2496ed',
  Kubernetes: '#326ce5',
}

// ── Churn Prediction Demo ───────────────────────────────────────────
export const demoChurnResult = {
  churn_probability: 0.37,
  risk_tier: 'Medium',
  shap_values: [
    { feature: 'Job Satisfaction', value: -0.18 },
    { feature: 'Years Coding', value: -0.12 },
    { feature: 'Compensation', value: 0.15 },
    { feature: 'Remote Work', value: -0.08 },
    { feature: 'Org Size', value: 0.09 },
    { feature: 'AI Tool Usage', value: -0.05 },
    { feature: 'Learning Resources', value: 0.11 },
    { feature: 'Work-Life Balance', value: 0.06 },
  ],
  recommendations: [
    'Your job satisfaction is above average, which significantly reduces churn risk.',
    'Consider negotiating compensation — it is a moderate risk factor in your profile.',
    'Increasing use of modern learning platforms could help improve retention outlook.',
    'Your experience level provides stability — senior developers tend to have lower churn.',
  ],
}

// ── Career Prediction Demo ──────────────────────────────────────────
export const demoCareerResult = {
  predicted_salary: 134500,
  salary_range: [118000, 152000],
  percentile: 72,
  predicted_cluster: 0,
  cluster_name: 'Full-Stack Architects',
  career_trajectory: [
    { year: 0, salary: 62000 },
    { year: 2, salary: 78000 },
    { year: 5, salary: 105000 },
    { year: 8, salary: 134500 },
    { year: 10, salary: 148000 },
    { year: 15, salary: 172000 },
  ],
  comparison: [
    { cluster: 'Full-Stack Architects', salary: 128500, yours: 134500 },
    { cluster: 'Data & ML Engineers', salary: 142000, yours: 134500 },
    { cluster: 'Cloud-Native DevOps', salary: 135000, yours: 134500 },
    { cluster: 'Frontend Craftsmen', salary: 115000, yours: 134500 },
    { cluster: 'Systems & Embedded', salary: 132000, yours: 134500 },
  ],
}

// ── Similar Developers Demo ─────────────────────────────────────────
export const demoSimilarDevs = {
  your_cluster: {
    id: 0,
    name: 'Full-Stack Architects',
    match_score: 0.89,
    description: clusterProfiles[0].description,
  },
  cluster_scores: [
    { name: 'Full-Stack Architects', score: 0.89 },
    { name: 'Frontend Craftsmen', score: 0.72 },
    { name: 'Data & ML Engineers', score: 0.58 },
    { name: 'Cloud-Native DevOps', score: 0.41 },
    { name: 'Systems & Embedded', score: 0.23 },
  ],
  similar_developers: [
    {
      id: 'DEV-48291',
      stage: 'Senior',
      country: 'United States',
      language: 'TypeScript',
      salary_range: '$120K – $145K',
      similarity: 0.94,
    },
    {
      id: 'DEV-33107',
      stage: 'Senior',
      country: 'Germany',
      language: 'JavaScript',
      salary_range: '$115K – $135K',
      similarity: 0.91,
    },
    {
      id: 'DEV-71520',
      stage: 'Staff',
      country: 'Canada',
      language: 'TypeScript',
      salary_range: '$140K – $165K',
      similarity: 0.88,
    },
    {
      id: 'DEV-19843',
      stage: 'Mid',
      country: 'United Kingdom',
      language: 'Python',
      salary_range: '$95K – $115K',
      similarity: 0.85,
    },
    {
      id: 'DEV-56072',
      stage: 'Senior',
      country: 'Netherlands',
      language: 'React',
      salary_range: '$110K – $130K',
      similarity: 0.82,
    },
  ],
}

// ── Countries list (abbreviated) ────────────────────────────────────
export const countries = [
  'United States', 'United Kingdom', 'Germany', 'Canada', 'India',
  'France', 'Netherlands', 'Australia', 'Brazil', 'Sweden',
  'Japan', 'Poland', 'Spain', 'Italy', 'Switzerland',
  'South Korea', 'Norway', 'Denmark', 'Finland', 'Austria',
  'Israel', 'Singapore', 'Ireland', 'Portugal', 'Belgium',
  'Czech Republic', 'New Zealand', 'Mexico', 'Argentina', 'Nigeria',
  'Ukraine', 'Romania', 'Turkey', 'Pakistan', 'Indonesia',
  'Philippines', 'Vietnam', 'Thailand', 'Colombia', 'Chile',
]

export const languages = [
  'JavaScript', 'Python', 'TypeScript', 'Java', 'C#',
  'C++', 'Go', 'Rust', 'PHP', 'Ruby',
  'Swift', 'Kotlin', 'Scala', 'R', 'Dart',
  'Elixir', 'Haskell', 'Clojure', 'Lua', 'Perl',
]

export const orgSizes = [
  '1-10 employees',
  '11-50 employees',
  '51-200 employees',
  '201-1,000 employees',
  '1,001-5,000 employees',
  '5,001-10,000 employees',
  '10,000+ employees',
  'Freelancer / Solo',
]
