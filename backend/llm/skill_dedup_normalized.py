import sys
import os
import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    print("[WARNING] RapidFuzz tidak terinstall. Install dengan: pip install rapidfuzz")

from database.connection import get_db_context
from database.models import Skill, JobSkill, SkillType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class SkillMatchResult:
    """Hasil skill matching dari LLM extraction"""
    original_skill: str
    normalized_skill: str
    matched_skill: Optional[str]
    matched_id: Optional[int]
    match_score: float
    match_method: str
    action: str
    skill_type_id: int
    skill_type_name: str
    
    def __repr__(self):
        return (
            f"SkillMatch(original='{self.original_skill}', "
            f"normalized='{self.normalized_skill}', "
            f"matched='{self.matched_skill}', "
            f"type='{self.skill_type_name}', "
            f"score={self.match_score:.1f}%, "
            f"action='{self.action}')"
        )


# ============================================================================
# INTELLIGENT SKILL CLASSIFIER
# ============================================================================

class SkillClassifier:
    """Intelligent classifier untuk membedakan Tools vs Concepts vs Soft Skills"""
    
    # Tool indicators
    TOOL_SUFFIXES = {
        'framework', 'library', 'platform', 'service', 'tool', 'engine', 
        'api', 'sdk', 'cli', 'db', 'database', 'warehouse', 'lake',
        'cloud', 'serverless', 'container', 'orchestrator', 'scheduler',
        'pipeline', 'connector', 'adapter', 'driver', 'sdk', 'studio',
        'builder', 'designer', 'server', 'client', 'agent'
    }
    
    # Concept indicators
    CONCEPT_SUFFIXES = {
        'engineering', 'architecture', 'design', 'development', 
        'planning', 'strategy', 'analysis', 'science', 'research',
        'programming', 'coding', 'security', 'audit', 'compliance',
        'optimization', 'tuning', 'performance', 'integration', 'deployment',
        'delivery', 'modeling', 'mining', 'visualization', 'orchestration',
        'governance', 'management', 'methodology', 'framework', 'pipeline'
    }
    
    # Soft skill indicators (Indonesian & English)
    SOFT_SKILL_INDICATORS = {
        # English
        'communication', 'leadership', 'teamwork', 'collaboration',
        'problem solving', 'analytical thinking', 'critical thinking',
        'time management', 'adaptability', 'creativity', 'emotional intelligence',
        'negotiation', 'presentation', 'writing', 'attention to detail',
        'organization', 'conflict resolution', 'decision making',
        'customer service', 'interpersonal skills', 'self motivation',
        'work ethic', 'stress management', 'multitasking', 'interpersonal',
        # Indonesian
        'komunikasi', 'kepemimpinan', 'kerjasama', 'manajemen waktu',
        'pemecahan masalah', 'berpikir analitis', 'kemampuan analisis',
        'analisis', 'berpikir kritis', 'kreativitas', 'negosiasi',
        'presentasi', 'ketelitian', 'perhatian terhadap detail',
        'resolusi konflik', 'pengambilan keputusan', 'layanan pelanggan',
        'keterampilan interpersonal', 'motivasi diri', 'etos kerja',
        'profesionalisme', 'manajemen stres', 'multitugas', 'empati',
        'kemampuan', 'kerja tim', 'tim', 'waktu', 'kritis'
    }
    
    # Generic terms
    GENERIC_TERMS = {
        'databases', 'database', 'cloud', 'data', 'analytics',
        'ai', 'ml', 'programming', 'coding', 'development',
        'services', 'platform', 'tools', 'applications',
        'software', 'systems', 'infrastructure', 'network'
    }
    
    @classmethod
    def is_generic(cls, skill_name: str) -> bool:
        skill_lower = skill_name.lower().strip()
        return skill_lower in cls.GENERIC_TERMS
    
    @classmethod
    def is_soft_skill(cls, skill_name: str) -> bool:
        skill_lower = skill_name.lower().strip()
        
        # Exact match atau partial match dengan soft skill indicators
        if skill_lower in cls.SOFT_SKILL_INDICATORS:
            return True
        
        for indicator in cls.SOFT_SKILL_INDICATORS:
            if indicator in skill_lower:
                return True
        
        return False
    
    @classmethod
    def classify(cls, skill_name: str) -> Tuple[Optional[int], str]:
        if not skill_name:
            return None, "unknown"
        
        skill_clean = skill_name.strip()
        
        if cls.is_generic(skill_clean):
            return None, "GENERIC"
        
        if cls.is_soft_skill(skill_clean):
            return 1, "Soft Skill"
        
        return None, "unknown"


# ============================================================================
# SYNONYM DETECTION - FUZZY MATCHING
# ============================================================================

class SynonymDetector:
    """
    Deteksi sinonim skill menggunakan RapidFuzz (fuzzy matching)
    Membantu menggabungkan skill yang sama dengan variasi penulisan berbeda
    """
    
    # 🔥 Threshold untuk dianggap sama (0-100)
    # 90+ = hampir pasti sama
    # 80-89 = sangat mirip, kemungkinan sama
    # 70-79 = mirip, perlu dicek
    SIMILARITY_THRESHOLD = 85
    
    # 🔥 Mapping sinonim bahasa Indonesia-Inggris
    SYNONYM_MAP = {
        # Soft Skills
        "komunikasi": "communication",
        "kemampuan komunikasi": "communication",
        "kepemimpinan": "leadership",
        "kemampuan kepemimpinan": "leadership",
        "kerja tim": "teamwork",
        "kerjasama": "teamwork",
        "kerja sama": "teamwork",
        "team work": "teamwork",
        "pemecahan masalah": "problem solving",
        "kemampuan pemecahan masalah": "problem solving",
        "problem-solving": "problem solving",
        "manajemen waktu": "time management",
        "pengaturan waktu": "time management",
        "berpikir analitis": "analytical thinking",
        "kemampuan analisis": "analytical thinking",
        "analisis": "analytical thinking",
        "analytical": "analytical thinking",
        "berpikir kritis": "critical thinking",
        "critical": "critical thinking",
        "kreativitas": "creativity",
        "creative": "creativity",
        "adaptabilitas": "adaptability",
        "adaptasi": "adaptability",
        "flexibility": "adaptability",
        "negosiasi": "negotiation",
        "presentasi": "presentation",
        "public speaking": "presentation",
        "ketelitian": "attention to detail",
        "perhatian terhadap detail": "attention to detail",
        "detail oriented": "attention to detail",
        "resolusi konflik": "conflict resolution",
        "conflict management": "conflict resolution",
        "pengambilan keputusan": "decision making",
        "decision-making": "decision making",
        "layanan pelanggan": "customer service",
        "customer support": "customer service",
        "keterampilan interpersonal": "interpersonal skills",
        "interpersonal": "interpersonal skills",
        "people skills": "interpersonal skills",
        "motivasi diri": "self motivation",
        "self-motivation": "self motivation",
        "etos kerja": "work ethic",
        "professionalism": "work ethic",
        "manajemen stres": "stress management",
        "stress management": "stress management",
        "multitugas": "multitasking",
        
        # Technical Skills
        "machine learning": "machine learning",
        "ml": "machine learning",
        "deep learning": "deep learning",
        "neural network": "deep learning",
        "natural language processing": "nlp",
        "nlp": "nlp",
        "computer vision": "computer vision",
        "cv": "computer vision",
        "data engineering": "data engineering",
        "data pipeline": "data pipeline",
        "etl": "etl process",
        "elt": "etl process",
        "data warehouse": "data warehouse",
        "data lake": "data lake",
        "business intelligence": "business intelligence",
        "bi": "business intelligence",
        "data analysis": "data analysis",
        "data analytics": "data analysis",
        "data visualization": "data visualization",
        "dataviz": "data visualization",
        
        # Tech Stack
        "python3": "python",
        "py": "python",
        "js": "javascript",
        "nodejs": "javascript",
        "golang": "go",
        "csharp": "c#",
        "aws": "aws",
        "amazon web services": "aws",
        "gcp": "google cloud platform",
        "google cloud": "google cloud platform",
        "azure": "microsoft azure",
        "postgres": "postgresql",
        "psql": "postgresql",
        "mongo": "mongodb",
        "sql server": "microsoft sql server",
        "mssql": "microsoft sql server",
        "sklearn": "scikit-learn",
        "tf": "tensorflow",
        "torch": "pytorch",
        "pd": "pandas",
        "np": "numpy",
        "excel": "excel",
        "ms excel": "excel",
        "microsoft excel": "excel",
        "tableau": "tableau",
        "powerbi": "power bi",
        "power bi": "power bi",
    }
    
    @classmethod
    def get_synonym(cls, skill_name: str) -> Optional[str]:
        """Dapatkan sinonim dari skill (Indonesia -> Inggris)"""
        skill_lower = skill_name.lower().strip()
        
        # Cek exact match di synonym map
        if skill_lower in cls.SYNONYM_MAP:
            return cls.SYNONYM_MAP[skill_lower]
        
        # Cek partial match
        for key, value in cls.SYNONYM_MAP.items():
            if key in skill_lower or skill_lower in key:
                return value
        
        return None
    
    @classmethod
    def are_similar(cls, skill1: str, skill2: str, threshold: int = SIMILARITY_THRESHOLD) -> Tuple[bool, float]:
        """
        Cek apakah dua skill mirip menggunakan fuzzy matching
        
        Returns:
            (is_similar, similarity_score)
        """
        if not RAPIDFUZZ_AVAILABLE:
            return False, 0.0
        
        # Normalisasi dulu
        s1 = skill1.lower().strip()
        s2 = skill2.lower().strip()
        
        # Jika sama persis
        if s1 == s2:
            return True, 100.0
        
        # Cek synonym map
        synonym1 = cls.get_synonym(s1)
        synonym2 = cls.get_synonym(s2)
        
        if synonym1 and synonym2 and synonym1 == synonym2:
            return True, 100.0
        
        if synonym1 and synonym1 == s2:
            return True, 100.0
        
        if synonym2 and synonym2 == s1:
            return True, 100.0
        
        # Fuzzy matching
        # token_set_ratio: lebih baik untuk matching kata-kata yang urutannya berbeda
        score = fuzz.token_set_ratio(s1, s2)
        
        # Jika score tinggi, dianggap sama
        if score >= threshold:
            return True, score
        
        # Coba partial ratio (untuk kata yang sebagian sama)
        if score < threshold:
            partial_score = fuzz.partial_ratio(s1, s2)
            if partial_score >= threshold:
                return True, partial_score
        
        return False, score
    
    @classmethod
    def find_best_match(cls, skill_name: str, candidates: List[str], threshold: int = SIMILARITY_THRESHOLD) -> Tuple[Optional[str], float]:
        """
        Cari match terbaik dari daftar kandidat
        
        Returns:
            (best_match, similarity_score)
        """
        if not candidates:
            return None, 0.0
        
        if not RAPIDFUZZ_AVAILABLE:
            return None, 0.0
        
        skill_lower = skill_name.lower().strip()
        
        # Cek synonym map dulu
        synonym = cls.get_synonym(skill_lower)
        if synonym:
            # Cari apakah ada kandidat yang sama dengan synonym
            for candidate in candidates:
                if candidate.lower().strip() == synonym:
                    return candidate, 100.0
                if cls.get_synonym(candidate.lower().strip()) == synonym:
                    return candidate, 100.0
        
        # Fuzzy matching
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            is_similar, score = cls.are_similar(skill_lower, candidate, threshold)
            if is_similar and score > best_score:
                best_score = score
                best_match = candidate
        
        return best_match, best_score


# ============================================================================
# CONFIGURATION - COMPLETE & NON-GENERIC
# ============================================================================

class SkillNormalizationConfig:
    """Centralized configuration with intelligent classification"""
    
    # ── TECH STACK (skill_type_id = 3) ──────────────────────────────────────
    TECH_STACK = {
        # Programming Languages
        "Python": {"python", "python3", "py", "python programming", "python scripting", "python dev"},
        "JavaScript": {"javascript", "js", "es6", "node", "nodejs", "node.js"},
        "TypeScript": {"typescript", "ts"},
        "Java": {"java", "jdk", "jre", "java se", "java ee"},
        "C#": {"c#", "csharp", "c-sharp", "c sharp", "dotnet"},
        "C++": {"c++", "cpp", "c plus plus"},
        "Go": {"golang", "go", "go lang"},
        "PHP": {"php", "php dev"},
        "Ruby": {"ruby", "rb"},
        "Kotlin": {"kotlin"},
        "Scala": {"scala"},
        "R": {"r", "rstudio", "r language", "r stat"},
        "Swift": {"swift"},
        "Rust": {"rust"},
        "Dart": {"dart"},
        "SQL": {"sql", "tsql", "plsql", "pl/sql", "structured query language"},
        "SAS": {"sas", "sas programming", "sas analytics"},
        
        # Frontend
        "React": {"react", "reactjs", "react.js"},
        "Angular": {"angular", "angularjs"},
        "Vue.js": {"vue", "vuejs", "vue.js"},
        "Next.js": {"next.js", "nextjs"},
        "HTML": {"html", "html5"},
        "CSS": {"css", "css3", "scss", "sass"},
        "Tailwind CSS": {"tailwind", "tailwindcss"},
        "Bootstrap": {"bootstrap"},
        
        # Backend Frameworks
        "FastAPI": {"fastapi", "fast api"},
        "Flask": {"flask"},
        "Django": {"django"},
        "Spring Boot": {"spring boot", "springboot", "spring"},
        "Express.js": {"express", "expressjs"},
        "Laravel": {"laravel"},
        "ASP.NET": {"asp.net", "aspnet", ".net", "dotnet", ".net core"},
        "NestJS": {"nestjs"},
        
        # Cloud Platforms
        "AWS": {"aws", "amazon web services", "amazon aws", "ec2", "s3", "lambda", "rds"},
        "Google Cloud Platform": {"gcp", "google cloud", "google cloud platform"},
        "Microsoft Azure": {"azure", "microsoft azure", "azure cloud"},
        
        # Data Warehouses
        "Snowflake": {"snowflake"},
        "Google BigQuery": {"bigquery", "big query", "bq"},
        "Databricks": {"databricks", "data bricks"},
        
        # ETL Tools
        "dbt": {"dbt", "data build tool"},
        "Apache Airflow": {"airflow", "apache airflow", "cloud composer"},
        "Talend": {"talend"},
        "Informatica": {"informatica"},
        "Fivetran": {"fivetran"},
        "Microsoft SSIS": {"ssis", "microsoft ssis", "sql server integration services"},
        "Dagster": {"dagster"},
        "Prefect": {"prefect"},
        "MLflow": {"mlflow"},
        "Pentaho": {"pentaho"},
        "ODI": {"odi", "oracle data integrator"},
        "Datastage": {"datastage", "ibm datastage"},
        
        # Databases
        "PostgreSQL": {"postgresql", "postgres", "postgre", "psql"},
        "MySQL": {"mysql", "my sql"},
        "MariaDB": {"mariadb"},
        "MongoDB": {"mongodb", "mongo"},
        "Oracle Database": {"oracle", "oracle db"},
        "Microsoft SQL Server": {"ms sql", "mssql", "sql server", "microsoft sql"},
        "Redis": {"redis"},
        "Elasticsearch": {"elasticsearch", "elastic"},
        "Firebase": {"firebase"},
        "Apache Cassandra": {"cassandra", "apache cassandra"},
        
        # Big Data & Streaming
        "Apache Spark": {"spark", "apache spark", "pyspark"},
        "Apache Kafka": {"kafka", "apache kafka"},
        "Apache Hadoop": {"hadoop", "apache hadoop", "hdfs"},
        "Apache Flink": {"flink", "apache flink"},
        "RabbitMQ": {"rabbitmq", "rabbit mq"},
        
        # AI/ML Platforms
        "OpenAI": {"openai", "open ai", "chatgpt", "gpt api"},
        "Azure OpenAI": {"azure openai"},
        "Claude": {"claude", "anthropic claude"},
        "Google Gemini": {"gemini", "google gemini"},
        "Hugging Face": {"hugging face", "huggingface", "transformers"},
        "LangChain": {"langchain", "lang chain"},
        "LlamaIndex": {"llamaindex", "llama index"},
        "LangGraph": {"langgraph"},
        "CrewAI": {"crewai"},
        "AutoGen": {"autogen"},
        "Bedrock": {"bedrock", "aws bedrock"},
        "SageMaker": {"sagemaker", "aws sagemaker"},
        
        # Vector Databases
        "Pinecone": {"pinecone"},
        "Weaviate": {"weaviate"},
        "Milvus": {"milvus"},
        "pgvector": {"pgvector", "pg vector"},
        "Chroma": {"chroma", "chromadb"},
        "Qdrant": {"qdrant"},
        "FAISS": {"faiss"},
        
        # ML Libraries
        "TensorFlow": {"tensorflow", "tf", "keras"},
        "PyTorch": {"pytorch", "torch"},
        "Scikit-learn": {"scikit-learn", "sklearn"},
        "XGBoost": {"xgboost", "xgb"},
        "LightGBM": {"lightgbm", "lgbm"},
        "CatBoost": {"catboost"},
        "Pandas": {"pandas", "pd"},
        "NumPy": {"numpy", "np"},
        "Matplotlib": {"matplotlib", "plt"},
        "Seaborn": {"seaborn", "sns"},
        "Plotly": {"plotly"},
        "OpenCV": {"opencv", "cv2"},
        "NLTK": {"nltk"},
        "SpaCy": {"spacy"},
        "Jupyter": {"jupyter", "jupyter notebook", "jupyter lab"},
        "Streamlit": {"streamlit"},
        "Gradio": {"gradio"},
        
        # BI Tools
        "Tableau": {"tableau"},
        "Power BI": {"power bi", "powerbi", "ms power bi", "microsoft power bi"},
        "Looker": {"looker", "looker studio"},
        "Qlik": {"qlik", "qlikview", "qliksense"},
        "Google Analytics": {"google analytics", "ga4"},
        "Metabase": {"metabase"},
        "Apache Superset": {"apache superset", "superset"},
        "Grafana": {"grafana"},
        "Splunk": {"splunk"},
        "Prometheus": {"prometheus"},
        "Datadog": {"datadog"},
        
        # Productivity
        "Excel": {"excel", "ms excel", "microsoft excel", "excel 365", "advanced excel", "vlookup"},
        "PowerPoint": {"powerpoint", "ms powerpoint", "ppt"},
        "Microsoft Word": {"word", "ms word"},
        "Google Sheets": {"google sheets", "google sheet", "gsheet"},
        "Notion": {"notion"},
        "Jira": {"jira"},
        "Confluence": {"confluence"},
        "Slack": {"slack"},
        "Microsoft Teams": {"microsoft teams", "ms teams"},
        
        # DevOps
        "Docker": {"docker"},
        "Kubernetes": {"kubernetes", "k8s"},
        "Terraform": {"terraform"},
        "Ansible": {"ansible"},
        "Helm": {"helm"},
        "Jenkins": {"jenkins"},
        "GitHub Actions": {"github actions", "gh actions"},
        "GitLab CI/CD": {"gitlab ci", "gitlab ci/cd"},
        "CircleCI": {"circleci"},
        "Argo CD": {"argo", "argocd"},
        
        # Version Control
        "Git": {"git"},
        "GitHub": {"github"},
        "GitLab": {"gitlab"},
        "Bitbucket": {"bitbucket"},
        
        # OS & Servers
        "Linux": {"linux", "linux os"},
        "Ubuntu": {"ubuntu"},
        "Nginx": {"nginx"},
        "Apache HTTP Server": {"apache", "apache http"},
        
        # API & Testing
        "Postman": {"postman"},
        "Swagger": {"swagger", "openapi"},
        "Selenium": {"selenium"},
        "Cypress": {"cypress"},
        "Jest": {"jest"},
        "JUnit": {"junit"},
        "pytest": {"pytest"},
        "Playwright": {"playwright"},
        
        # IDE
        "VS Code": {"vs code", "visual studio code", "vscode"},
        "IntelliJ": {"intellij"},
        "PyCharm": {"pycharm"},
        "Eclipse": {"eclipse"},
        "Cursor": {"cursor", "cursor ai"},
        "Windsurf": {"windsurf"},
        
        # Design
        "Figma": {"figma"},
        "Adobe Photoshop": {"photoshop"},
        "Adobe Illustrator": {"illustrator"},
        "Adobe XD": {"adobe xd", "xd"},
        "Unity": {"unity"},
        "AutoCAD": {"autocad"},
    }

    # ── TECHNICAL SKILLS (skill_type_id = 2) ──────────────────────────────
    TECHNICAL_SKILLS = {
        # Data Engineering
        "Data Engineering": {"data engineering", "data engineer"},
        "ETL Process": {"etl", "elt", "extract transform load", "etl pipeline", "etl process", "data integration"},
        "Data Pipeline": {"data pipeline", "pipeline development", "data pipelines", "pipeline architecture"},
        "Data Modeling": {"data modeling", "data modelling", "dimensional modeling", "star schema", "3nf"},
        "Data Warehouse Design": {"data warehouse design", "data warehousing", "data warehouse"},
        "Data Lake Architecture": {"data lake", "data lake architecture", "data lakehouse"},
        "Streaming Data Processing": {"streaming data", "real-time streaming", "stream processing"},
        "Data Governance": {"data governance", "data quality management", "data stewardship", "data catalog"},
        "Data Quality": {"data quality", "data quality assurance", "data quality checks", "data quality control"},
        "Data Architecture": {"data architecture", "data infrastructure", "data platform"},
        "Data Orchestration": {"data orchestration", "workflow orchestration", "job scheduling"},
        "Data Lineage": {"data lineage"},
        "Data Ingestion": {"data ingestion", "data loading"},
        "Data Transformation": {"data transformation", "data wrangling", "data processing"},
        "Big Data": {"big data", "big data analytics", "big data processing", "big data management"},
        "Distributed Systems": {"distributed systems", "distributed computing"},
        
        # Data Science
        "Data Science": {"data science", "data scientist"},
        "Data Analysis": {"data analysis", "data analytics", "exploratory data analysis", "eda"},
        "Statistical Analysis": {"statistical analysis", "statistics", "statistical modeling"},
        "Data Visualization": {"data visualization", "dataviz", "dashboard development"},
        "Business Intelligence": {"business intelligence", "bi", "bi development", "bi reporting"},
        "A/B Testing": {"ab testing", "a/b testing", "split testing", "experimentation", "hypothesis testing"},
        "Predictive Analytics": {"predictive analytics", "predictive modeling", "forecasting", "prediction"},
        "Cohort & Funnel Analysis": {"cohort analysis", "funnel analysis", "customer segmentation"},
        "Marketing Analytics": {"marketing analytics", "digital analytics", "web analytics", "campaign analytics"},
        "Financial Analysis": {"financial analysis", "financial modeling", "margin analysis", "cost analysis"},
        "Credit Risk Modeling": {"credit risk modeling", "credit scoring", "credit modeling"},
        "Anomaly Detection": {"anomaly detection", "fraud detection", "fraud analytics"},
        
        # Machine Learning & AI
        "Machine Learning": {"machine learning", "ml", "ml engineering"},
        "Deep Learning": {"deep learning", "neural network", "cnn", "rnn", "lstm"},
        "NLP": {"nlp", "natural language processing", "text mining", "text analytics"},
        "Computer Vision": {"computer vision", "image processing", "object detection"},
        "LLM Engineering": {"llm", "large language model", "llm engineering", "generative ai", "gen ai"},
        "Prompt Engineering": {"prompt engineering", "prompt design", "prompt optimization"},
        "RAG": {"rag", "retrieval augmented generation", "rag pipeline", "rag architecture"},
        "AI Agents": {"ai agents", "ai agent", "autonomous agents", "agentic ai", "multi-agent"},
        "Feature Engineering": {"feature engineering", "feature selection", "feature extraction"},
        "Model Deployment": {"model deployment", "mlops", "ml deployment", "model serving"},
        "Model Evaluation": {"model evaluation", "model validation", "model performance"},
        "Recommendation Systems": {"recommendation system", "recommender system", "collaborative filtering"},
        "Time Series Analysis": {"time series", "time series analysis", "time series forecasting"},
        
        # Software Engineering
        "API Development": {"api development", "rest api", "api design", "web api"},
        "API Integration": {"api integration", "third-party integration", "system integration"},
        "Object-Oriented Programming": {"oop", "object oriented programming"},
        "Design Patterns": {"design patterns", "design pattern"},
        "SOLID Principles": {"solid", "solid principles"},
        "Clean Code": {"clean code", "clean coding"},
        "Test-Driven Development": {"tdd", "test driven development"},
        "Code Review": {"code review", "peer review"},
        "Refactoring": {"refactoring", "code refactoring"},
        "Microservices Architecture": {"microservices", "microservice", "microservice architecture"},
        "Event-Driven Architecture": {"event driven", "event-driven architecture"},
        "Domain-Driven Design": {"ddd", "domain driven design"},
        "Software Architecture": {"software architecture", "system architecture", "solution architecture"},
        "Full Stack Development": {"full stack", "full-stack", "full stack development"},
        "Frontend Development": {"frontend development", "front-end development"},
        "Backend Development": {"backend development", "back-end development"},
        "Web Development": {"web development", "web programming"},
        "Debugging": {"debugging", "troubleshooting", "error handling"},
        "Version Control": {"version control", "source control", "git workflow"},
        
        # Cloud & DevOps
        "Cloud Architecture": {"cloud architecture", "cloud computing", "cloud design"},
        "Cloud Migration": {"cloud migration", "cloud adoption"},
        "Infrastructure as Code": {"iac", "infrastructure as code"},
        "CI/CD": {"ci/cd", "ci cd", "continuous integration", "continuous delivery"},
        "DevOps": {"devops", "devsecops"},
        "Container Orchestration": {"container orchestration", "orchestration"},
        "Site Reliability Engineering": {"sre", "site reliability engineering"},
        "Monitoring & Observability": {"monitoring", "observability", "alerting"},
        "Workflow Automation": {"workflow automation", "automation", "process automation"},
        
        # Database
        "Database Design": {"database design", "schema design"},
        "Query Optimization": {"query optimization", "sql tuning", "sql optimization"},
        "Database Administration": {"database administration", "dba"},
        
        # Security
        "Information Security": {"information security", "cybersecurity", "cyber security"},
        "Cloud Security": {"cloud security", "cloud security concepts"},
        "Compliance Management": {"compliance management", "regulatory compliance"},
        
        # UI/UX
        "UI/UX Design": {"ui/ux", "ui ux", "user interface design", "user experience design"},
        "UX Research": {"ux research", "usability testing"},
        "Responsive Design": {"responsive design", "responsive web design"},
        
        # QA & Documentation
        "Technical Documentation": {"technical documentation", "technical writing"},
        "Software Testing": {"software testing", "quality assurance", "qa"},
        "Test Automation": {"test automation", "automated testing"},
        "Unit Testing": {"unit testing", "unit test"},
        
        # Agile & Methods
        "Agile Methodology": {"agile", "scrum", "kanban", "agile methodology"},
        "Product Management": {"product management", "product manager"},
        "Project Management": {"project management", "pm", "project coordination"},
        "System Design": {"system design", "system architecture"},
        "Geospatial Analysis": {"geospatial data", "gis", "spatial analysis"},
        "Analytics Engineering": {"analytics engineering", "self service analytics"},
    }

    # ── SOFT SKILLS (skill_type_id = 1) ──────────────────────────────────────
    SOFT_SKILLS = {
        "Communication": {"communication", "komunikasi", "verbal communication", "written communication", 
                         "effective communication", "strong communication", "clear communication",
                         "kemampuan komunikasi", "komunikasi efektif"},
        "Leadership": {"leadership", "kepemimpinan", "team leadership", "organizational leadership", 
                      "kemampuan kepemimpinan"},
        "Teamwork": {"teamwork", "team work", "kerjasama", "kerja tim", "collaboration", 
                    "team player", "kemampuan bekerja sama dalam tim", "kolaborasi"},
        "Problem Solving": {"problem solving", "problem-solving", "pemecahan masalah", 
                           "kemampuan pemecahan masalah", "good problem solving"},
        "Time Management": {"time management", "manajemen waktu", "prioritization", "pengaturan waktu"},
        "Adaptability": {"adaptability", "adaptable", "flexibility", "kemampuan beradaptasi", "adaptasi"},
        "Critical Thinking": {"critical thinking", "berpikir kritis", "critical analysis", "logical thinking"},
        "Creativity": {"creativity", "kreativitas", "creative thinking", "creative problem solving"},
        "Emotional Intelligence": {"emotional intelligence", "eq", "kecerdasan emosional", "empathy", "empati"},
        "Negotiation": {"negotiation", "negosiasi", "negotiation skills", "influencing"},
        "Presentation Skills": {"presentation", "public speaking", "presentasi", "kemampuan presentasi"},
        "Writing Skills": {"writing", "menulis", "kemampuan menulis", "report writing", "business writing"},
        "Analytical Thinking": {"analytical thinking", "analytical", "berpikir analitis", "kemampuan analisis", 
                               "analisis", "analytical skill", "analytical mindset"},
        "Attention to Detail": {"attention to detail", "detail oriented", "ketelitian", "perhatian terhadap detail"},
        "Organizational Skills": {"organization", "organizational", "kemampuan organisasi"},
        "Conflict Resolution": {"conflict resolution", "conflict management", "resolusi konflik"},
        "Decision Making": {"decision making", "decision-making", "pengambilan keputusan"},
        "Customer Service": {"customer service", "layanan pelanggan", "customer support"},
        "Interpersonal Skills": {"interpersonal", "interpersonal skills", "keterampilan interpersonal"},
        "Self-Motivation": {"self motivation", "self-motivation", "motivasi diri", "self-starter"},
        "Work Ethic": {"work ethic", "professionalism", "etos kerja", "profesionalisme"},
        "Stress Management": {"stress management", "manajemen stres", "kelola stres"},
        "Multitasking": {"multitasking", "multitugas"},
        "Mentoring": {"mentoring", "coaching", "mentorship", "knowledge sharing"},
        "Strategic Thinking": {"strategic thinking", "strategic planning", "strategic mindset"},
        "Stakeholder Management": {"stakeholder management", "stakeholder communication"},
        "Change Management": {"change management"},
        "Process Improvement": {"process improvement", "continuous improvement"},
        "Research Skills": {"research", "research skills", "research methodology"},
        "Fast Learner": {"fast learner", "quick learner", "growth mindset", "continuous learning"},
        "Data-Driven Decision Making": {"data driven decision making", "data driven approach"},
        "Ownership Mindset": {"ownership mindset", "ownership", "accountability"},
        "Results Orientation": {"result oriented", "results oriented", "goal driven"},
        "Proactivity": {"proactive", "proactive mindset", "initiative", "self starting"},
        "Independence": {"independence", "independent", "self sufficient"},
        "Curiosity": {"curiosity", "intellectual curiosity"},
        "Collaboration": {"collaboration", "collaborative", "cross-functional collaboration"},
    }

    # ── Merge ────────────────────────────────────────────────────────────────
    CANONICAL_SKILLS = {**TECH_STACK, **TECHNICAL_SKILLS, **SOFT_SKILLS}

    # ── Specific Fixes ──────────────────────────────────────────────────────
    SPECIFIC_FIXES = {
        # Programming Languages
        "python3": "Python", "py": "Python",
        "js": "JavaScript", "nodejs": "JavaScript",
        "golang": "Go", "csharp": "C#",
        
        # Cloud
        "aws": "AWS", "gcp": "Google Cloud Platform",
        "azure": "Microsoft Azure",
        
        # Data
        "big query": "Google BigQuery",
        "postgres": "PostgreSQL", "psql": "PostgreSQL",
        "mongo": "MongoDB", "mssql": "Microsoft SQL Server",
        "sql server": "Microsoft SQL Server",
        
        # ML
        "sklearn": "Scikit-learn", "tf": "TensorFlow",
        "torch": "PyTorch", "pd": "Pandas", "np": "NumPy",
        "ml": "Machine Learning", "nlp": "NLP",
        "llm": "LLM Engineering", "rag": "RAG",
        
        # Methods
        "etl": "ETL Process", "elt": "ETL Process",
        "tdd": "Test-Driven Development",
        "ci cd": "CI/CD", "ci/cd": "CI/CD",
        "mlops": "Model Deployment",
        
        # Excel
        "ms excel": "Excel", "microsoft excel": "Excel",
        "excel 365": "Excel", "advanced excel": "Excel",
        
        # Indonesian Soft Skills
        "kemampuan analisis": "Analytical Thinking",
        "berpikir analitis": "Analytical Thinking",
        "analisis": "Analytical Thinking",
        "pemecahan masalah": "Problem Solving",
        "berpikir kritis": "Critical Thinking",
        "komunikasi": "Communication",
        "kepemimpinan": "Leadership",
        "kerja tim": "Teamwork", "kerjasama": "Teamwork",
        "manajemen waktu": "Time Management",
        "kemampuan beradaptasi": "Adaptability", "adaptasi": "Adaptability",
        "kreativitas": "Creativity",
        "negosiasi": "Negotiation",
        "presentasi": "Presentation Skills",
        "ketelitian": "Attention to Detail",
        "perhatian terhadap detail": "Attention to Detail",
        "resolusi konflik": "Conflict Resolution",
        "pengambilan keputusan": "Decision Making",
        "layanan pelanggan": "Customer Service",
        "keterampilan interpersonal": "Interpersonal Skills",
        "motivasi diri": "Self-Motivation",
        "etos kerja": "Work Ethic", "profesionalisme": "Work Ethic",
        "manajemen stres": "Stress Management",
        "multitugas": "Multitasking",
    }

    # Normalization patterns
    NORMALIZATION_PATTERNS = [
        (r'\s+', ' '),
        (r'^[\s\-\.\(]+|[\s\-\.\)]+$', ''),
        (r'\s*\([^)]*\)', ''),
        (r'\s*\[[^\]]*\]', ''),
        (r'[,-]', ' '),
    ]
    
    INVALID_CHARS = r'[^\w\s\-\+\#\./]'
    
    @classmethod
    def get_skill_type_id(cls, skill_name: str) -> Tuple[Optional[int], str]:
        """Detect skill type with intelligent classification"""
        if not skill_name:
            return None, "unknown"
        
        skill_lower = skill_name.lower().strip()
        skill_clean = skill_name.strip()
        
        # Check specific fixes first
        if skill_lower in cls.SPECIFIC_FIXES:
            canonical = cls.SPECIFIC_FIXES[skill_lower]
            if canonical in cls.TECH_STACK:
                return 3, "Tech Stack"
            elif canonical in cls.TECHNICAL_SKILLS:
                return 2, "Technical Skill"
            elif canonical in cls.SOFT_SKILLS:
                return 1, "Soft Skill"
        
        # Check if generic
        if SkillClassifier.is_generic(skill_clean):
            return None, "GENERIC"
        
        # Check Soft Skills first
        if SkillClassifier.is_soft_skill(skill_clean):
            return 1, "Soft Skill"
        
        # Check all categories
        normalized = SkillNormalizer.normalize_skill(skill_name)
        
        for canonical, variations in cls.TECH_STACK.items():
            if normalized in {SkillNormalizer.normalize_skill(v) for v in variations}:
                return 3, "Tech Stack"
        
        for canonical, variations in cls.TECHNICAL_SKILLS.items():
            if normalized in {SkillNormalizer.normalize_skill(v) for v in variations}:
                return 2, "Technical Skill"
        
        for canonical, variations in cls.SOFT_SKILLS.items():
            if normalized in {SkillNormalizer.normalize_skill(v) for v in variations}:
                return 1, "Soft Skill"
        
        return None, "unknown"


# ============================================================================
# CORE NORMALIZER
# ============================================================================

class SkillNormalizer:
    """Skill normalization engine"""
    
    # Indonesian to English mapping
    INDO_TO_ENG_MAP = {
        "kemampuan analisis": "analytical thinking",
        "berpikir analitis": "analytical thinking",
        "analisis": "analytical thinking",
        "pemecahan masalah": "problem solving",
        "kemampuan pemecahan masalah": "problem solving",
        "berpikir kritis": "critical thinking",
        "komunikasi": "communication",
        "kemampuan komunikasi": "communication",
        "kepemimpinan": "leadership",
        "kemampuan kepemimpinan": "leadership",
        "kerja tim": "teamwork",
        "kerjasama": "teamwork",
        "kemampuan bekerja sama dalam tim": "teamwork",
        "manajemen waktu": "time management",
        "kemampuan beradaptasi": "adaptability",
        "adaptasi": "adaptability",
        "kreativitas": "creativity",
        "negosiasi": "negotiation",
        "kemampuan presentasi": "presentation",
        "presentasi": "presentation",
        "ketelitian": "attention to detail",
        "perhatian terhadap detail": "attention to detail",
        "resolusi konflik": "conflict resolution",
        "pengambilan keputusan": "decision making",
        "layanan pelanggan": "customer service",
        "keterampilan interpersonal": "interpersonal skills",
        "motivasi diri": "self motivation",
        "etos kerja": "work ethic",
        "profesionalisme": "work ethic",
        "manajemen stres": "stress management",
        "kelola stres": "stress management",
        "multitugas": "multitasking",
        "pengaturan waktu": "time management",
    }
    
    _INDO_KEYS_BY_LENGTH = sorted(INDO_TO_ENG_MAP.keys(), key=len, reverse=True)
    
    @staticmethod
    def normalize_skill(skill_name: str) -> str:
        if not skill_name or not isinstance(skill_name, str):
            return ""
        
        skill_lower = skill_name.lower().strip()
        
        # Indonesian to English mapping
        if skill_lower in SkillNormalizer.INDO_TO_ENG_MAP:
            skill_name = SkillNormalizer.INDO_TO_ENG_MAP[skill_lower]
        else:
            for indo_key in SkillNormalizer._INDO_KEYS_BY_LENGTH:
                if indo_key in skill_lower:
                    skill_name = SkillNormalizer.INDO_TO_ENG_MAP[indo_key]
                    break
        
        normalized = skill_name.lower().strip()
        normalized = normalized.replace('/', ' ')
        normalized = re.sub(SkillNormalizationConfig.INVALID_CHARS, '', normalized)
        
        for pattern, replacement in SkillNormalizationConfig.NORMALIZATION_PATTERNS:
            normalized = re.sub(pattern, replacement, normalized)
        
        return normalized.strip()
    
    @classmethod
    def get_canonical_form(cls, skill_name: str, skill_type_id: Optional[int] = None) -> Tuple[str, bool]:
        if not skill_name:
            return skill_name, False
        
        skill_lower = skill_name.lower().strip()
        
        if skill_lower in SkillNormalizationConfig.SPECIFIC_FIXES:
            return SkillNormalizationConfig.SPECIFIC_FIXES[skill_lower], True
        
        normalized = cls.normalize_skill(skill_name)
        
        if skill_type_id == 3:
            categories = [SkillNormalizationConfig.TECH_STACK]
        elif skill_type_id == 2:
            categories = [SkillNormalizationConfig.TECHNICAL_SKILLS]
        elif skill_type_id == 1:
            categories = [SkillNormalizationConfig.SOFT_SKILLS]
        else:
            categories = [
                SkillNormalizationConfig.TECH_STACK,
                SkillNormalizationConfig.TECHNICAL_SKILLS,
                SkillNormalizationConfig.SOFT_SKILLS
            ]
        
        for category in categories:
            for canonical, variations in category.items():
                if normalized in {cls.normalize_skill(v) for v in variations}:
                    return canonical, True
        
        # Fallback
        for category in (
            SkillNormalizationConfig.TECH_STACK,
            SkillNormalizationConfig.TECHNICAL_SKILLS,
            SkillNormalizationConfig.SOFT_SKILLS,
        ):
            for canonical, variations in category.items():
                if normalized in {cls.normalize_skill(v) for v in variations}:
                    return canonical, True
        
        return skill_name, False


# ============================================================================
# SKILL MATCH ENGINE - DENGAN SYNONYM DETECTION
# ============================================================================

class SkillMatchEngine:
    """Real-time skill matching dengan synonym detection"""
    
    def __init__(self):
        self.skills_cache: Dict[str, Dict] = {}
        self.canonical_lookup: Dict[str, Tuple[str, int]] = {}
        self._load_skills_cache()
        self._build_canonical_lookup()
    
    def _load_skills_cache(self):
        with get_db_context() as db:
            skills = db.query(Skill).all()
            self.skills_cache = {
                SkillNormalizer.normalize_skill(s.normalized_name): {
                    "id": s.id,
                    "name": s.name,
                    "normalized_name": s.normalized_name,
                    "skill_type_id": s.skill_type_id
                }
                for s in skills
            }
    
    def _build_canonical_lookup(self):
        self.canonical_lookup = {}
        
        for variation, canonical in SkillNormalizationConfig.SPECIFIC_FIXES.items():
            skill_type_id, _ = SkillNormalizationConfig.get_skill_type_id(canonical)
            if skill_type_id:
                normalized_var = SkillNormalizer.normalize_skill(variation)
                self.canonical_lookup[normalized_var] = (canonical, skill_type_id)
        
        all_categories = [
            (SkillNormalizationConfig.TECH_STACK, 3),
            (SkillNormalizationConfig.TECHNICAL_SKILLS, 2),
            (SkillNormalizationConfig.SOFT_SKILLS, 1),
        ]
        
        for category, type_id in all_categories:
            for canonical, variations in category.items():
                for var in variations:
                    normalized_var = SkillNormalizer.normalize_skill(var)
                    self.canonical_lookup[normalized_var] = (canonical, type_id)
    
    def match_skill(self, skill_name: str, skill_type_id: int) -> SkillMatchResult:
        """Match skill dengan synonym detection"""
        normalized = SkillNormalizer.normalize_skill(skill_name)
        
        # Check if generic
        if SkillClassifier.is_generic(skill_name):
            return SkillMatchResult(
                original_skill=skill_name,
                normalized_skill=normalized,
                matched_skill=None,
                matched_id=None,
                match_score=0.0,
                match_method="generic",
                action="rejected",
                skill_type_id=0,
                skill_type_name="GENERIC"
            )
        
        # 🔥 1. Cek canonical lookup (termasuk sinonim)
        if normalized in self.canonical_lookup:
            canonical, canonical_type_id = self.canonical_lookup[normalized]
            
            if skill_type_id != canonical_type_id:
                skill_type_id = canonical_type_id
            
            canonical_normalized = SkillNormalizer.normalize_skill(canonical)
            
            if canonical_normalized in self.skills_cache:
                cached = self.skills_cache[canonical_normalized]
                type_name = self._get_type_name(skill_type_id)
                return SkillMatchResult(
                    original_skill=skill_name,
                    normalized_skill=normalized,
                    matched_skill=cached["name"],
                    matched_id=cached["id"],
                    match_score=100.0,
                    match_method="canonical",
                    action="use_existing",
                    skill_type_id=skill_type_id,
                    skill_type_name=type_name
                )
        
        # 🔥 2. Cek synonym map langsung
        synonym = SynonymDetector.get_synonym(skill_name)
        if synonym:
            synonym_normalized = SkillNormalizer.normalize_skill(synonym)
            if synonym_normalized in self.skills_cache:
                cached = self.skills_cache[synonym_normalized]
                type_name = self._get_type_name(skill_type_id)
                return SkillMatchResult(
                    original_skill=skill_name,
                    normalized_skill=normalized,
                    matched_skill=cached["name"],
                    matched_id=cached["id"],
                    match_score=100.0,
                    match_method="synonym",
                    action="use_existing",
                    skill_type_id=skill_type_id,
                    skill_type_name=type_name
                )
        
        # 🔥 3. Fuzzy matching dengan semua skill di cache
        if RAPIDFUZZ_AVAILABLE and len(self.skills_cache) > 0:
            skill_names = list(self.skills_cache.keys())
            best_match, best_score = SynonymDetector.find_best_match(normalized, skill_names)
            
            if best_match and best_score >= SynonymDetector.SIMILARITY_THRESHOLD:
                cached = self.skills_cache[best_match]
                type_name = self._get_type_name(skill_type_id)
                return SkillMatchResult(
                    original_skill=skill_name,
                    normalized_skill=normalized,
                    matched_skill=cached["name"],
                    matched_id=cached["id"],
                    match_score=best_score,
                    match_method=f"fuzzy_{best_score:.0f}",
                    action="use_existing",
                    skill_type_id=skill_type_id,
                    skill_type_name=type_name
                )
        
        # 🔥 4. Exact match
        if normalized in self.skills_cache:
            cached = self.skills_cache[normalized]
            type_name = self._get_type_name(skill_type_id)
            return SkillMatchResult(
                original_skill=skill_name,
                normalized_skill=normalized,
                matched_skill=cached["name"],
                matched_id=cached["id"],
                match_score=100.0,
                match_method="exact",
                action="use_existing",
                skill_type_id=skill_type_id,
                skill_type_name=type_name
            )
        
        # 5. New skill
        detected_type, type_name = SkillNormalizationConfig.get_skill_type_id(skill_name)
        if detected_type:
            skill_type_id = detected_type
        else:
            type_name = "UNKNOWN"
        
        return SkillMatchResult(
            original_skill=skill_name,
            normalized_skill=normalized,
            matched_skill=None,
            matched_id=None,
            match_score=0.0,
            match_method="new",
            action="insert_new",
            skill_type_id=skill_type_id or 0,
            skill_type_name=type_name
        )
    
    def _get_type_name(self, type_id: int) -> str:
        if type_id == 3:
            return "Tech Stack"
        elif type_id == 2:
            return "Technical Skill"
        elif type_id == 1:
            return "Soft Skill"
        return "Unknown"
    
    def refresh_cache(self):
        self._load_skills_cache()
        self._build_canonical_lookup()
    
    def save_new_skill(self, skill_name: str, skill_type_id: int) -> int:
        canonical, found = SkillNormalizer.get_canonical_form(skill_name, skill_type_id)
        
        if found:
            skill_name = canonical
        
        normalized = SkillNormalizer.normalize_skill(skill_name)
        
        with get_db_context() as db:
            existing = db.query(Skill).filter(
                Skill.normalized_name == normalized,
                Skill.skill_type_id == skill_type_id
            ).first()
            
            if existing:
                return existing.id
            
            new_skill = Skill(
                name=skill_name,
                skill_type_id=skill_type_id,
                normalized_name=normalized
            )
            db.add(new_skill)
            db.flush()
            skill_id = new_skill.id
            db.commit()
            
            self.refresh_cache()
            
            return skill_id
    
    def link_skill_to_job(self, job_id: int, skill_id: int) -> bool:
        with get_db_context() as db:
            existing = db.query(JobSkill).filter(
                JobSkill.job_id == job_id,
                JobSkill.skill_id == skill_id
            ).first()
            
            if existing:
                return False
            
            job_skill = JobSkill(
                job_id=job_id,
                skill_id=skill_id
            )
            db.add(job_skill)
            db.commit()
            return True


# ============================================================================
# SKILL PROCESSOR
# ============================================================================

class SkillProcessor:
    """Main processor for skill extraction and storage flow"""
    
    def __init__(self):
        self.engine = SkillMatchEngine()
    
    def process_skill(self, skill_name: str, skill_type_id: int) -> SkillMatchResult:
        result = self.engine.match_skill(skill_name, skill_type_id)
        
        if result.action == "insert_new" and result.skill_type_id > 0:
            canonical, found = SkillNormalizer.get_canonical_form(skill_name, skill_type_id)
            if found:
                skill_to_save = canonical
            else:
                skill_to_save = result.normalized_skill
            
            skill_id = self.engine.save_new_skill(
                skill_to_save, 
                result.skill_type_id
            )
            result.matched_id = skill_id
            result.matched_skill = skill_to_save
            result.normalized_skill = SkillNormalizer.normalize_skill(skill_to_save)
            result.action = "use_existing"
        
        return result
    
    def process_job_skills(self, job_id: int, skills: List[Tuple[str, int]]) -> List[SkillMatchResult]:
        results = []
        
        for skill_name, skill_type_id in skills:
            result = self.process_skill(skill_name, skill_type_id)
            
            if result.matched_id and result.action != "rejected":
                self.engine.link_skill_to_job(job_id, result.matched_id)
            
            results.append(result)
        
        return results


# ============================================================================
# BATCH DEDUPLICATION
# ============================================================================

def normalize_by_skill_type(skill_type_id: int, skill_type_name: str):
    """Normalize skills for a specific skill type"""
    print(f"\n{'='*70}")
    print(f"🔄 NORMALIZING {skill_type_name.upper()} SKILLS (type_id: {skill_type_id})")
    print(f"{'='*70}")
    
    with get_db_context() as db:
        skills = db.query(Skill).filter(
            Skill.skill_type_id == skill_type_id
        ).all()
        
        print(f"\n📊 Total {skill_type_name} skills: {len(skills)}")
        
        if not skills:
            print(f"No {skill_type_name} skills found!")
            return 0
        
        groups = {}
        for skill in skills:
            normalized = SkillNormalizer.normalize_skill(skill.name)
            
            if normalized not in groups:
                groups[normalized] = []
            groups[normalized].append(skill)
        
        duplicate_groups = [g for g in groups.values() if len(g) > 1]
        print(f"Found {len(duplicate_groups)} duplicate groups")
        
        merged_count = 0
        renamed_count = 0
        
        for normalized_key, group in groups.items():
            canonical = min(group, key=lambda s: len(s.name))
            
            canonical_name, found = SkillNormalizer.get_canonical_form(
                canonical.name, skill_type_id
            )
            
            if found and canonical_name != canonical.name:
                print(f"\n  🔤 Rename: '{canonical.name}' → '{canonical_name}' (ID: {canonical.id})")
                canonical.name = canonical_name
                canonical.normalized_name = SkillNormalizer.normalize_skill(canonical_name)
                renamed_count += 1
            elif not canonical.normalized_name or canonical.normalized_name != normalized_key:
                canonical.normalized_name = normalized_key
            
            if len(group) > 1:
                print(f"  Canonical: {canonical.name} (ID: {canonical.id})")
                
                for skill in group:
                    if skill.id != canonical.id:
                        print(f"    Merging: {skill.name} (ID: {skill.id})")
                        job_skills = db.query(JobSkill).filter(
                            JobSkill.skill_id == skill.id
                        ).all()
                        for js in job_skills:
                            existing = db.query(JobSkill).filter(
                                JobSkill.job_id == js.job_id,
                                JobSkill.skill_id == canonical.id
                            ).first()
                            if existing:
                                db.delete(js)
                            else:
                                js.skill_id = canonical.id
                        db.delete(skill)
                        merged_count += 1
            
            db.commit()
        
        skills_without_norm = db.query(Skill).filter(
            Skill.skill_type_id == skill_type_id,
            Skill.normalized_name.is_(None)
        ).all()
        
        for skill in skills_without_norm:
            skill.normalized_name = SkillNormalizer.normalize_skill(skill.name)
        
        db.commit()
        
        final_count = db.query(Skill).filter(
            Skill.skill_type_id == skill_type_id
        ).count()
        
        print(f"\n📊 {skill_type_name} Summary:")
        print(f"  • Original: {len(skills)}")
        print(f"  • Renamed to canonical/English: {renamed_count}")
        print(f"  • Merged: {merged_count}")
        print(f"  • Final: {final_count}")
        print(f"  • Reduced: {len(skills) - final_count}")
        
        return final_count


def normalize_all_skills():
    """Process all skill types"""
    print("=" * 70)
    print("🔄 SKILL NORMALIZATION & DEDUPLICATION")
    print("=" * 70)
    
    normalize_by_skill_type(3, "Tech Stack")
    normalize_by_skill_type(2, "Technical")
    normalize_by_skill_type(1, "Soft")
    
    print(f"\n🔄 Refreshing match engine cache...")
    engine = SkillMatchEngine()
    engine.refresh_cache()
    print(f"  Cache refreshed with {len(engine.skills_cache)} skills")
    
    print("\n" + "=" * 70)
    print("✅ COMPLETE!")
    print("=" * 70)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_usage():
    """Example of how to use the system"""
    processor = SkillProcessor()
    job_id = 123
    
    test_skills = [
        # Tech Stack (dengan variasi)
        ("Python", 3), ("py", 3), ("python3", 3),
        ("JavaScript", 3), ("js", 3), ("nodejs", 3),
        ("AWS", 3), ("aws", 3), ("amazon web services", 3),
        ("Excel", 3), ("ms excel", 3), ("microsoft excel", 3),
        
        # Technical Skills (dengan variasi)
        ("Machine Learning", 2), ("ml", 2),
        ("ETL", 2), ("etl process", 2), ("extract transform load", 2),
        ("Data Analysis", 2), ("data analytics", 2),
        ("A/B Testing", 2), ("ab testing", 2), ("split testing", 2),
        
        # Soft Skills (English & Indonesian)
        ("Communication", 1), ("komunikasi", 1), ("kemampuan komunikasi", 1),
        ("Leadership", 1), ("kepemimpinan", 1),
        ("Teamwork", 1), ("kerja tim", 1), ("kerjasama", 1),
        ("Problem Solving", 1), ("pemecahan masalah", 1),
        ("Analytical Thinking", 1), ("kemampuan analisis", 1), ("analisis", 1),
        ("Time Management", 1), ("manajemen waktu", 1),
        ("Adaptability", 1), ("adaptasi", 1), ("kemampuan beradaptasi", 1),
        
        # Mixed - dengan qualifier
        ("strong communication", 1),
        ("advanced Python", 3),
        ("proficient in SQL", 3),
        ("excellent problem solving", 1),
    ]
    
    print("\n" + "=" * 80)
    print("🔍 SKILL MATCHING WITH SYNONYM DETECTION")
    print("=" * 80)
    print(f"\n📋 Menggunakan threshold similarity: {SynonymDetector.SIMILARITY_THRESHOLD}%")
    print("=" * 80)
    
    results = processor.process_job_skills(job_id, test_skills)
    
    print("\n📊 RESULTS:")
    print("-" * 80)
    
    for result in results:
        icon = {
            "Tech Stack": "🛠️",
            "Technical Skill": "🧠",
            "Soft Skill": "🤝",
            "GENERIC": "⚠️",
            "UNKNOWN": "❓"
        }.get(result.skill_type_name, "❓")
        
        status = "✅" if result.action == "use_existing" else "🆕"
        method = result.match_method if result.match_method else "new"
        
        print(f"{status} {icon} {result.original_skill:35} → {result.matched_skill or result.normalized_skill:25} [{result.skill_type_name}] (match: {method})")
    
    print("-" * 80)
    
    type_counts = {}
    method_counts = {}
    for result in results:
        type_counts[result.skill_type_name] = type_counts.get(result.skill_type_name, 0) + 1
        if result.match_method:
            method_counts[result.match_method] = method_counts.get(result.match_method, 0) + 1
    
    print("\n📊 SUMMARY BY TYPE:")
    for type_name, count in type_counts.items():
        print(f"  • {type_name}: {count} skills")
    
    print("\n📊 MATCH METHODS:")
    for method, count in method_counts.items():
        print(f"  • {method}: {count} skills")
    
    print("=" * 80)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "--example":
            example_usage()
        elif command == "--all":
            normalize_all_skills()
        elif command == "--tech-stack":
            normalize_by_skill_type(3, "Tech Stack")
        elif command == "--technical":
            normalize_by_skill_type(2, "Technical")
        elif command == "--soft":
            normalize_by_skill_type(1, "Soft")
        else:
            print("Usage:")
            print("  python -m llm.skill_dedup_normalized --example    # Show classification example")
            print("  python -m llm.skill_dedup_normalized --all        # Run full normalization")
            print("  python -m llm.skill_dedup_normalized --tech-stack # Process Tech Stack only")
            print("  python -m llm.skill_dedup_normalized --technical  # Process Technical only")
            print("  python -m llm.skill_dedup_normalized --soft       # Process Soft only")
    else:
        normalize_all_skills()