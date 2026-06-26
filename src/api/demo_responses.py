import math
import random
from typing import Dict, List, Any

CLUSTER_NAMES = [
    "Full-Stack Architects",
    "Data & ML Engineers",
    "Cloud-Native DevOps",
    "Frontend Craftsmen",
    "Systems & Embedded"
]

def get_seeded_random(seed: int):
    # A simple linear congruential generator to keep results consistent
    s = seed
    def rng():
        nonlocal s
        s = (s * 16807) % 2147483647
        return (s - 1) / 2147483646
    return rng

def generate_cluster_points(cx: float, cy: float, n: int, spread: float, cluster_id: int, rng) -> List[Dict[str, Any]]:
    points = []
    langs = ["Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "C++", "C#"]
    stages = ["Junior", "Mid", "Senior", "Staff", "Principal"]
    
    for _ in range(n):
        angle = rng() * math.pi * 2
        r = math.sqrt(-2 * math.log(rng() + 1e-9)) * spread
        points.append({
            "x": round(cx + r * math.cos(angle), 2),
            "y": round(cy + r * math.sin(angle), 2),
            "cluster": cluster_id,
            "salary": int(40000 + rng() * 160000),
            "experience": int(1 + rng() * 25),
            "language": langs[int(rng() * len(langs))],
            "stage": stages[int(rng() * len(stages))]
        })
    return points

# Generate default points
rng_func = get_seeded_random(42)
cluster_centers = [
    {"cx": -5, "cy": 3},
    {"cx": 4, "cy": 5},
    {"cx": -3, "cy": -4},
    {"cx": 6, "cy": -2},
    {"cx": 0, "cy": -7}
]

DEMO_UMAP_POINTS = []
for i, center in enumerate(cluster_centers):
    n_points = int(200 + rng_func() * 60)
    DEMO_UMAP_POINTS.extend(generate_cluster_points(center["cx"], center["cy"], n_points, 2.2, i, rng_func))

DEMO_CLUSTER_PROFILES = [
    {
        "id": 0,
        "name": "Full-Stack Architects",
        "count": 14231,
        "avgSalary": 128500.0,
        "avgExperience": 8.3,
        "topTechs": ["JavaScript", "TypeScript", "React", "Node.js", "PostgreSQL"],
        "description": "Versatile engineers who span the entire stack, from pixel-perfect UIs to robust backend APIs.",
        "satisfaction": 4.1,
        "remoteRatio": 0.72,
        "churnRate": 0.18
    },
    {
        "id": 1,
        "name": "Data & ML Engineers",
        "count": 12876,
        "avgSalary": 142000.0,
        "avgExperience": 6.7,
        "topTechs": ["Python", "TensorFlow", "SQL", "Spark", "Docker"],
        "description": "Data-driven builders who turn raw datasets into production ML pipelines and actionable insights.",
        "satisfaction": 4.3,
        "remoteRatio": 0.68,
        "churnRate": 0.14
    },
    {
        "id": 2,
        "name": "Cloud-Native DevOps",
        "count": 13542,
        "avgSalary": 135000.0,
        "avgExperience": 7.1,
        "topTechs": ["AWS", "Kubernetes", "Terraform", "Go", "Docker"],
        "description": "Infrastructure artisans who design, deploy, and keep planet-scale systems running 24/7.",
        "satisfaction": 3.9,
        "remoteRatio": 0.65,
        "churnRate": 0.21
    },
    {
        "id": 3,
        "name": "Frontend Craftsmen",
        "count": 12988,
        "avgSalary": 115000.0,
        "avgExperience": 5.4,
        "topTechs": ["React", "TypeScript", "CSS", "Next.js", "Figma"],
        "description": "Experience-obsessed developers who craft beautiful, accessible, and lightning-fast interfaces.",
        "satisfaction": 4.0,
        "remoteRatio": 0.78,
        "churnRate": 0.24
    },
    {
        "id": 4,
        "name": "Systems & Embedded",
        "count": 11800,
        "avgSalary": 132000.0,
        "avgExperience": 9.5,
        "topTechs": ["C++", "Rust", "C", "Linux", "Assembly"],
        "description": "Low-level specialists who write the code closest to the metal — firmware, kernels, and real-time systems.",
        "satisfaction": 3.8,
        "remoteRatio": 0.52,
        "churnRate": 0.12
    }
]

def generate_tech_forecast(name: str, base: float, growth: float, volatility: float) -> List[Dict[str, Any]]:
    rng = get_seeded_random(len(name) * 137)
    years = [2022, 2023, 2024, 2025, 2026]
    points = []
    for i, year in enumerate(years):
        is_forecast = year >= 2025
        val = min(95.0, max(2.0, base + growth * i + (rng() - 0.5) * volatility))
        points.append({
            "year": year,
            "adoption": round(val, 1),
            "low": round(max(1.0, val - 4 - rng() * 3), 1) if is_forecast else None,
            "high": round(min(98.0, val + 4 + rng() * 3), 1) if is_forecast else None,
            "isForecast": is_forecast
        })
    return points

DEMO_FORECASTS = {
    "Python": generate_tech_forecast("Python", 48, 5.2, 3),
    "JavaScript": generate_tech_forecast("JavaScript", 65, -1.5, 4),
    "TypeScript": generate_tech_forecast("TypeScript", 30, 8.5, 3),
    "Rust": generate_tech_forecast("Rust", 6, 4.8, 2),
    "Go": generate_tech_forecast("Go", 14, 3.0, 2.5),
    "Java": generate_tech_forecast("Java", 35, -2.0, 3),
    "C++": generate_tech_forecast("C++", 22, -0.5, 2),
    "C#": generate_tech_forecast("C#", 28, 0.8, 2),
    "Kotlin": generate_tech_forecast("Kotlin", 10, 3.5, 2),
    "Swift": generate_tech_forecast("Swift", 8, 2.0, 1.5),
    "PostgreSQL": generate_tech_forecast("PostgreSQL", 42, 5.0, 3),
    "MongoDB": generate_tech_forecast("MongoDB", 28, 1.5, 3),
    "Redis": generate_tech_forecast("Redis", 22, 3.0, 2),
    "MySQL": generate_tech_forecast("MySQL", 50, -3.0, 4),
    "DynamoDB": generate_tech_forecast("DynamoDB", 12, 3.5, 2),
    "React": generate_tech_forecast("React", 42, 3.5, 3),
    "Next.js": generate_tech_forecast("Next.js", 15, 7.5, 3),
    "Django": generate_tech_forecast("Django", 18, 1.5, 2),
    "FastAPI": generate_tech_forecast("FastAPI", 5, 6.5, 2),
    "Spring Boot": generate_tech_forecast("Spring Boot", 20, 0.5, 2.5),
    "GitHub Copilot": generate_tech_forecast("GitHub Copilot", 5, 12, 4),
    "ChatGPT": generate_tech_forecast("ChatGPT", 2, 15, 5),
    "TensorFlow": generate_tech_forecast("TensorFlow", 32, -1.0, 3),
    "PyTorch": generate_tech_forecast("PyTorch", 24, 5.5, 3),
    "LangChain": generate_tech_forecast("LangChain", 1, 10, 3),
    "AWS": generate_tech_forecast("AWS", 52, 2.0, 3),
    "Azure": generate_tech_forecast("Azure", 30, 3.5, 3),
    "GCP": generate_tech_forecast("GCP", 22, 2.5, 2.5),
    "Docker": generate_tech_forecast("Docker", 55, 3.0, 3),
    "Kubernetes": generate_tech_forecast("Kubernetes", 30, 5.0, 3),
}

DEMO_CHURN_RESPONSE = {
    "churn_probability": 0.37,
    "risk_tier": "Medium",
    "shap_values": [
        {"feature": "Job Satisfaction", "value": -0.18},
        {"feature": "Years Coding", "value": -0.12},
        {"feature": "Compensation", "value": 0.15},
        {"feature": "Remote Work", "value": -0.08},
        {"feature": "Org Size", "value": 0.09},
        {"feature": "AI Tool Usage", "value": -0.05},
        {"feature": "Learning Resources", "value": 0.11},
        {"feature": "Work-Life Balance", "value": 0.06}
    ],
    "recommendations": [
        "Your job satisfaction is above average, which significantly reduces churn risk.",
        "Consider negotiating compensation — it is a moderate risk factor in your profile.",
        "Increasing use of modern learning platforms could help improve retention outlook.",
        "Your experience level provides stability — senior developers tend to have lower churn."
    ]
}

DEMO_CAREER_RESPONSE = {
    "predicted_salary": 134500.0,
    "salary_range": [118000.0, 152000.0],
    "percentile": 72.0,
    "predicted_cluster": 0,
    "cluster_name": "Full-Stack Architects",
    "career_trajectory": [
        {"year": 0, "salary": 62000.0},
        {"year": 2, "salary": 78000.0},
        {"year": 5, "salary": 105000.0},
        {"year": 8, "salary": 134500.0},
        {"year": 10, "salary": 148000.0},
        {"year": 15, "salary": 172000.0}
    ],
    "comparison": [
        {"cluster": "Full-Stack Architects", "salary": 128500.0, "yours": 134500.0},
        {"cluster": "Data & ML Engineers", "salary": 142000.0, "yours": 134500.0},
        {"cluster": "Cloud-Native DevOps", "salary": 135000.0, "yours": 134500.0},
        {"cluster": "Frontend Craftsmen", "salary": 115000.0, "yours": 134500.0},
        {"cluster": "Systems & Embedded", "salary": 132000.0, "yours": 134500.0}
    ]
}

DEMO_SIMILAR_DEVS = {
    "your_cluster": {
        "id": 0,
        "name": "Full-Stack Architects",
        "match_score": 0.89,
        "description": DEMO_CLUSTER_PROFILES[0]["description"]
    },
    "cluster_scores": [
        {"name": "Full-Stack Architects", "score": 0.89},
        {"name": "Frontend Craftsmen", "score": 0.72},
        {"name": "Data & ML Engineers", "score": 0.58},
        {"name": "Cloud-Native DevOps", "score": 0.41},
        {"name": "Systems & Embedded", "score": 0.23}
    ],
    "similar_developers": [
        {
            "id": "DEV-48291",
            "stage": "Senior",
            "country": "United States",
            "language": "TypeScript",
            "salary_range": "$120K – $145K",
            "similarity": 0.94
        },
        {
            "id": "DEV-33107",
            "stage": "Senior",
            "country": "Germany",
            "language": "JavaScript",
            "salary_range": "$115K – $135K",
            "similarity": 0.91
        },
        {
            "id": "DEV-71520",
            "stage": "Staff",
            "country": "Canada",
            "language": "TypeScript",
            "salary_range": "$140K – $165K",
            "similarity": 0.88
        },
        {
            "id": "DEV-19843",
            "stage": "Mid",
            "country": "United Kingdom",
            "language": "Python",
            "salary_range": "$95K – $115K",
            "similarity": 0.85
        },
        {
            "id": "DEV-56072",
            "stage": "Senior",
            "country": "Netherlands",
            "language": "React",
            "salary_range": "$110K – $130K",
            "similarity": 0.82
        }
    ]
}
