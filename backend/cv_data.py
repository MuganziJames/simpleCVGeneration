"""
Pre-formatted CV text for James Muganzi.

This string is meticulously formatted to match the exact parsing rules
of the DocumentService (cvpdfgenerator.py):

  - Line 1  : Full name (first non-blank line)
  - Line 2  : Job title  (no @, +, http, .com, .io, .dev, |, or • characters)
  - Lines 3+ : Contact   (contains @ or +)
  - Lines 4+ : Portfolio (contains github, .dev, linkedin)
  - Sections : Whitelisted headers in UPPERCASE
  - Experience: "Position | Company\nDate\n- bullet"
  - Skills   : "Category: Skill1, Skill2, ..."
  - Bullets  : lines starting with -  (NOT – em-dash)
  - Blank lines separate multi-entry sections (education, certs, etc.)
"""

JAMES_MUGANZI_CV = """James Muganzi
Senior Full Stack Developer · AI Systems Engineer · Cloud & Automation Architect
muganzijames.ai.dev@gmail.com | +254 798 848 862 | Nairobi, Kenya
github.com/MuganziJames | muganzijamesdev.com

PROFESSIONAL SUMMARY
Highly driven Full Stack Software Engineer and AI Systems Specialist with proven experience building scalable digital platforms, intelligent automation systems, and machine learning-powered applications. Experienced in designing end-to-end architectures spanning modern frontend engineering, backend service design, predictive analytics pipelines, and cloud infrastructure deployment. Passionate about developing socially impactful technological solutions that improve accessibility, decision-making, and operational efficiency across emerging markets.

TECHNICAL SKILLS
Frontend: React, Angular, React Native, TypeScript, Tailwind CSS, GraphQL, REST APIs
Backend: Node.js, Python, FastAPI, MERN Stack, Microservices, Event-Driven Systems, Serverless
Data Science: Machine Learning, NLP, LLMs, RAG, Predictive Modelling, Embeddings, pgvector, Pandas, Scikit-learn
Cloud & DevOps: AWS, Terraform, Docker, Kubernetes, CI/CD, GitHub Actions, Cloud Architecture
Databases: PostgreSQL, Supabase, SQL, Redis, Data Systems
Practices: Agile, Testing Pipelines, Automation, Containerisation, Version Control

PROFESSIONAL EXPERIENCE

Junior Data Scientist | Blueprint AI
Jan 2023 – Present
- Designed and optimised machine learning models deployed across real-world client projects, ensuring analytical robustness and scalability.
- Performed advanced data preprocessing, exploratory data analysis, and predictive modelling using Python-based ecosystems including pandas and scikit-learn.
- Collaborated with multidisciplinary engineering teams to refine model evaluation strategies and improve feature engineering workflows.
- Developed analytical dashboards and visual reporting artefacts translating complex statistical findings into actionable insights for stakeholders.
- Supported continuous improvement of model lifecycle processes including monitoring, validation, and iterative pipeline optimisation.

Technical Mentor & Community Contributor | Mentor Me Collective
2024 – Present
- Provided structured technical mentorship to emerging technology professionals navigating careers in software engineering and cloud disciplines.
- Facilitated workshops, technical guidance sessions, and collaborative project reviews aligned with capacity-building frameworks.
- Contributed to global initiatives improving access to digital skills, career readiness resources, and professional development opportunities.

AI & Machine Learning Trainee | Power Learn Project
2024
- Undertook specialised training in machine learning, predictive modelling, and applied data science aligned with emerging industry practices.
- Built analytical and predictive systems integrating datasets, statistical modelling techniques, and ML algorithms to solve real-world challenges.

Software Engineering Trainee | Power Learn Project
2024
- Completed an intensive, fully funded software engineering programme developing industry-ready competencies through hands-on real-world projects.
- Gained practical experience across programming languages, data systems, blockchain fundamentals, and applied software engineering principles.
- Achieved 3rd Place recognition at the Power Learn Project Hackathon for innovation and measurable community impact.

Software Engineering Fellow | TechCrush
2024
- Engaged in structured software engineering training covering modern web development, collaborative engineering workflows, and practical system-building.
- Developed technical proficiency in responsive UIs, backend logic systems, and integrated application architectures within agile environments.

KEY PROJECTS

Ajirawise – AI Job Intelligence Platform
- Designed backend infrastructure powering a semantic job recommendation engine using embeddings and vector similarity search.
- Automated job alert delivery across WhatsApp and Telegram with AI-powered career support.
Technologies: Python, FastAPI, PostgreSQL, pgvector, OpenAI, Supabase

WorkeAfrica – AI Recruitment Matching System
- Developed semantic retrieval architecture for contextual matching of candidate profiles to job descriptions using vector database technologies.
- Built full CI/CD pipelines and deployed to DigitalOcean with enterprise-grade security and httpOnly cookie authentication.
Technologies: Python, FastAPI, PostgreSQL, pgvector, OpenAI, Next.js, TypeScript, Docker

GreenPulse – AI Climate Intelligence Platform
- Engineered predictive analytics pipelines processing environmental datasets from NASA POWER and Google Weather APIs.
- Developed entire production backend in under 12 hours during a 24-hour international hackathon.
Technologies: Python, FastAPI, OpenRouter GPT-4o, NASA POWER API, PostgreSQL, React, TailwindCSS

NutriAI East Africa – AI Nutrition Planning System
- Built optimisation-driven predictive models generating culturally contextualised and economically feasible meal recommendations for East African families.
Technologies: Python, Streamlit, NLP, Data Modeling, Scikit-learn

Rider Tracker – Real-Time Logistics Platform
- Designed real-time backend processing systems enabling live delivery tracking and logistics monitoring via geospatial API integrations.
Technologies: React Native, Expo, Google Maps API, TypeScript

EDUCATION

BSc Civil & Structural Engineering
University of Eldoret

Associate Degree in Computer Science
University of the People

CERTIFICATIONS

Google IT Automation with Python Professional Certificate
Google · 2024
- Covered Python scripting, automation engineering, configuration management, system troubleshooting, version control workflows, and scalable cloud automation strategies.

AWARDS AND ACHIEVEMENTS
- Power Learn Project Software Development Scholarship
- Tech4Africans Mobile Development Scholarship
- 3rd Place — Power Learn Project Hackathon (Innovation & Community Impact)
"""
