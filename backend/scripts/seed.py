"""
scripts/seed.py

Dev seed for ApplicationPipeline. Populates:
  - 1 test User
  - 3 Resumes (Nicole's real resume variants)
  - 1 Session (LinkedIn, remote data/backend, keyword "Staff Data Engineer")
  - 7 JDs (batch 1 = JDs 1–5, batch 2 = JDs 6–7 — tests the partial-batch boundary)

Usage:
    python -m scripts.seed              # seed if empty, skip if data exists
    python -m scripts.seed --reset      # truncate all tables and re-seed

Run from the backend/ directory.
"""

import argparse
import asyncio
import sys

from sqlalchemy import text
from sqlmodel import select

from app.database import AsyncSessionLocal
from app.models import JD, JDStatus, JDStatusSource, Resume, Session as SessionModel, SessionStatus, User
from app.services.text_cleaning import clean_jd_text


# ── Resumes ───────────────────────────────────────────────────────────────────

RESUMES = [
    {
        "label": "Pulley — BE Systems / API Design / Correctness & Durability",
        "content": """\
NICOLE L. ROWSEY nicole.rowsey@gmail.com | (480) 253-9548 | Hillsboro, OR

PROFESSIONAL SUMMARY
Staff-level backend engineer with 13+ years designing foundational systems where correctness, trust, and durability matter. I specialize turning ambiguous, high-stakes business workflows into clean APIs, well-modeled relational schemas, and event-driven services that teams build on for years. Proven record of leading cross-functional technical initiatives through influence — earning adoption by making systems demonstrably safer, easier to reason about, and scalable under real production constraints.

CORE EXPERTISE
Languages: Python, SQL (PostgreSQL, Oracle, SQL Server), C#/.NET
Backend Systems: API design, data contracts, schema design, persistence layers, auditability
Distributed Systems: Event-driven architecture, Kafka (ordering, idempotency, delivery guarantees), asynchronous workflows
Infrastructure: Kubernetes, CI/CD, production monitoring and alerting
Data Reliability: Validation, lineage, dead-letter queues, observability, operational reporting

PROFESSIONAL EXPERIENCE
Senior Data Platform Engineer, Yield Systems
Intel Corporation — Hillsboro, OR | 2024–2025
- Set technical direction for shared backend and analytics platform across multiple business units, defining data standards and contracts that enabled automated decisioning and improved operational throughput by 50%.
- Introduced machine-learning capabilities into production backend systems, deploying clustering models alongside traditional statistical methods with clear guardrails

Data Platform Engineer, Lithography Systems
Intel Corporation — Ocotillo, AZ | 2017–2024

Reticle Inspection Automation Platform — Event-Driven Reliability at Scale
- Architected a Kafka-based backend system automating critical workflows across 5+ geographically distributed sites
- Designed asynchronous ingestion, failure isolation, and automated alerting 24/7 operation
- Implemented ordering and idempotency guarantees aligned to domain assets; deployed on Kubernetes

EF Calibration Platform — APIs, Auditability, and Data Integrity
- Built a backend platform processing 40,000+ annual calibration workflows across multiple stakeholder groups
- Designed service APIs and orchestration for secure data ingestion with auditability, failure isolation, and least-privilege access
- Delivered complex capabilities incrementally while maintaining strict correctness requirements

Productivity Analytics Platform — Platform Leverage Through Adoption
- Technical lead for a 14-engineer cross-functional team building a backend analytics platform aggregating distributed systems data
- Defined shared data contracts and backend patterns enabling consistent ingestion and analysis across teams
- Drove adoption that exceeded quarterly productivity goals by 250%, with Kafka-based services delivering the largest hours-saved impact

New Product Integration Platform — Scaling Organizational Throughput
- Owned end-to-end backend systems supporting new product introductions across multiple business units
- Designed coordination and persistence layers replacing manual handoffs with reliable backend workflows
- Scaled capacity from 7 to 15 simultaneous product introductions while achieving record turnaround times

Yield Engineer / Data Systems Developer
Intel Corporation — Ocotillo, AZ | 2012–2017
- Designed and built full-stack data and backend platform standardizing transformation workflows across 7,000+ parameters and 20+ product lines
- Made early architectural decisions that enabled the platform to remain in active production 10+ years later

INDEPENDENT PROJECTS
ORToothFairy | C#.NET, PostgreSQL, REST APIs, Cloud Deployment
Flink Rightsizing Framework | Python, Kubernetes, Apache Flink

EDUCATION
Ph.D., Electrical Engineering — University of Florida, 2012
B.S.E., Electrical Engineering — Princeton University, 2006

AWARDS
2022 Mentor of the Year | 2019 Department Recognition
""",
    },
    {
        "label": "Affirm — Stakeholder Navigation / Product Thinking / Regulated Env",
        "content": """\
NICOLE L. ROWSEY nicole.rowsey@gmail.com | (480) 253-9548 | Hillsboro, OR

PROFESSIONAL SUMMARY
Staff-level backend engineer with 13+ years building API-driven platforms in regulated, high-consequence environments where multiple teams and business units depend on the same systems for critical workflows. I specialize in designing durable APIs and data contracts that evolve safely across long time horizons, navigating competing stakeholder priorities to make tradeoffs explicit, and building operational foundations — monitoring, auditability, failure isolation — that let teams ship with confidence. I thrive in ambiguity and operate as a force-multiplier: setting technical strategy, raising quality standards, and creating systems that other engineers trust and adopt.

CORE EXPERTISE
Languages: Python (Flask, pandas, ETL, API integrations), SQL (MySQL, PostgreSQL, etc.), C#/.NET
Backend Systems: API design, data contracts, schema evolution, persistence layers, auditability
Distributed Systems: Event-driven architecture, Kafka (ordering, idempotency, delivery guarantees), async workflows
Infrastructure: Kubernetes, Docker, CI/CD, monitoring/alerting, observability
Cloud Platforms: Azure, AWS (EC2, S3)
Product & Process: Stakeholder discovery, requirements negotiation, incremental delivery, adoption-driven design

PROFESSIONAL EXPERIENCE
Senior Data Platform Engineer — Yield Systems
Intel Corporation — Hillsboro, OR | 2024–2025
- Set technical direction for shared backend platform across multiple business units, defining data standards and contracts that balanced speed, quality, and operational risk
- Re-architected metrology capacity allocation and built predictive model to absorb high-risk batch surges — 50% throughput improvement while preventing downstream backpressure

Data Platform Engineer — Lithography Systems
Intel Corporation — Ocotillo, AZ | 2017–2024

Stakeholder Navigation & Access Control at Scale — EF Calibration Platform
- Led backend design across 5 stakeholder groups with conflicting priorities
- Built backend platform processing 40,000+ annual workflows with auditability, failure isolation, and least-privilege access

Product Discovery & Adoption-Driven Design — Productivity Analytics Platform
- Technical lead for 14-engineer cross-functional team
- Exceeded quarterly productivity targets by 250% and drove factory-wide adoption by scaling influence rather than authority

Event-Driven Reliability at Scale — Reticle Inspection Platform
- Architected Kafka-based backend system automating critical workflows across 5+ geographically distributed sites

Change Management & Workflow Coordination — New Product Integration Platform
- Scaled capacity from 7 to 15 simultaneous product introductions with record turnaround times

Yield Engineer / Data Systems Developer
Intel Corporation — Ocotillo, AZ | 2012–2017
- Designed full-stack data platform standardizing workflows across 7,000+ parameters and 20+ product lines — still in production 10+ years later

Independent Engineering & Consulting | 2025–Present
SaaS Healthcare Platform — ORToothFairy (C#/.NET, PostgreSQL, REST APIs)
Open-source Flink rightsizing framework for Kubernetes

EDUCATION
Ph.D., Electrical Engineering — University of Florida, 2012
B.S.E., Electrical Engineering — Princeton University, 2006

RECOGNITION
2022 Mentor of the Year | 2019 Department Recognition
""",
    },
    {
        "label": "SmarterDx — Data Platform / Kafka / Streaming / Pipeline-Heavy",
        "content": """\
NICOLE L. ROWSEY nicole.rowsey@gmail.com | (480) 253-9548 | Hillsboro, OR

PROFESSIONAL SUMMARY
Staff-level data platform engineer with 13+ years designing and building distributed systems for high-volume, mission-critical operations. Deep expertise in Python, Kafka, and event-driven architectures — architected fault-tolerant streaming pipelines processing high-stakes, security-sensitive operations across globally distributed sites. Track record of delivering complex features incrementally with a high bar for quality.

TECHNICAL SKILLS
Languages: Python (pandas, ETL pipelines, API integrations), SQL, C#/.NET Core
Streaming & Eventing: Kafka (producer/consumer design, serialization, delivery guarantees), async messaging patterns, event-driven architectures
Data Platform: Data pipeline development, ETL/ELT workflows, dbt, data quality frameworks, batch and stream processing
Databases: PostgreSQL, Oracle, SQL Server
Infrastructure: Kubernetes, containerized deployments, CI/CD automation, monitoring and alerting
Architecture: Fault-tolerant distributed systems, high-availability design, microservices, API design

EXPERIENCE
Senior Data Platform Engineer
Intel Corporation — Hillsboro, OR | Jan 2024 – Jul 2025
- Architected shared data standards and core infrastructure serving internal and external customers across multiple business units
- Improved operational throughput capacity by 50% through data-driven analysis and predictive modeling

Data Platform Engineer, Lithography Systems
Intel Corporation — Ocotillo, AZ | Aug 2017 – Jan 2024
- Reticle inspection automation: Architected Kafka-based event-driven system automating critical workflows across 5+ geographically distributed sites; deployed on Kubernetes
- EF calibration platform: Led multi-year platform modernization processing 40,000+ annual workflows; 5+ stakeholder groups; security-conscious data ingestion with auditability and least-privilege access
- Productivity analytics: Technical lead for cross-functional team of 14 engineers; exceeded quarterly productivity goals by 250%, with Kafka project delivering largest hours-saved contribution
- New product integration: Scaled capacity from 7 to 15 simultaneous product introductions with record turnaround times

Yield Engineer / Data Systems Developer
Intel Corporation — Ocotillo, AZ | Jul 2012 – Aug 2017
- Designed and built full-stack data platform standardizing workflows across 7,000+ parameters, 20+ product lines — application remains in production 10+ years later

INDEPENDENT PROJECTS
ORToothFairy | .NET MAUI, PostgreSQL, Cloud Deployment — healthcare platform, launching May 2026
Flink Rightsizing Framework | Python, Kubernetes, Apache Flink (github.com/sooperD00/flink-rightsizing-framework)
Connectome | Python, FastAPI, Claude API, SQLite, D3 — LLM orchestration layer with topic graph

EDUCATION
Ph.D., Electrical Engineering — University of Florida, 2012
B.S.E., Electrical Engineering — Princeton University, 2006

PUBLICATIONS & RECOGNITION
4 peer-reviewed publications in IEEE Transactions on Nuclear Science (2011-2012)
2022 Mentor of the Year | 2019 Department Recognition
""",
    },
]


# ── JDs ───────────────────────────────────────────────────────────────────────
# 7 JDs: batch 1 = #1–5, batch 2 = #6–7 (partial batch, tests boundary logic)

JDS = [
    {
        "number": 1,
        "company": "Honor",
        "role": "Senior Backend Engineer",
        "compensation": "$175,500–$190,000",
        "employee_count": "501–1,000",
        "link": "https://job-boards.greenhouse.io/honor/jobs/8382000002",
        "raw_text": """\
Senior Backend Engineer — Honor Technology
$175,500–$190,000 | Remote | 501–1,000 employees

About the role:
You'll work on core services that power how families find care and how Care Professionals do their work — systems that directly support Honor's mission every day.

Teams you may join:
- Workforce Team: systems supporting Care Professionals, including hiring, scheduling, and workforce optimization
- DemandGen Team: powering public digital experiences and growth channels
- Growth Team: multi-channel sales and communication stack (phone, SMS, email)

We're looking for you to bring:
- Strong backend engineering experience, with a track record of building and operating production systems.
- Experience designing relational data models and working with databases at scale.
- Familiarity with cloud platforms (AWS preferred) and service-oriented architectures.
- Experience with API design, distributed systems, and backend performance considerations.
- Proficiency in Python or transferable backend experience with a willingness to learn Python.

You care about building systems that have real-world impact. You thrive in diverse, cross-functional environments. You have a builder's mindset, evolving systems from design through operation. You enjoy mentoring others and contributing to a healthy, inclusive engineering culture.

Honor Technology's mission is to change the way society cares for older adults. Together with Home Instead, Honor delivers over 50 million hours of personalized care annually.
""",
    },
    {
        "number": 2,
        "company": "Zapier",
        "role": "Senior Software Engineer, Workflow/Backend",
        "compensation": "$174,600–$261,200",
        "employee_count": "501–1,000",
        "link": "https://jobs.ashbyhq.com/zapier/ae48a961-6ec7-43b5-8e59-9f6861fee334",
        "raw_text": """\
Senior Software Engineer, Workflow/Backend — Zapier (Runner Team)
$174,600–$261,200 + equity + bonus | Remote | 501–1,000 employees

The Runner team is responsible for reliably executing Zaps — fast. Core infrastructure powering Zapier's workflows, including scaling for high volume and reducing latency across millions of executions daily.

In this role, you'll:
- Develop and maintain Zapier's execution engine, scaling it to handle millions of daily runs
- Improve system performance, reduce latency, and strengthen failure handling
- Design and implement execution primitives that power reliable automation
- Collaborate across infrastructure, product, and platform teams on core system design

About You:
- 5+ years of professional experience developing software, including at least 2 years in a senior-level role
- Strong backend experience, ideally in Python and Django and/or TypeScript and Node.js
- Familiarity with relational databases like PostgreSQL or MySQL
- Experience designing and consuming RESTful APIs, building event-driven systems, and working with data integrations across services
- Proven ability to lead complex technical projects
- You navigate ambiguity with confidence
- You've used AI tooling for work or are willing to learn fast

This is a foundational team at the platform layer — ideal for engineers who like deep technical challenges and shipping resilient, high-scale services.
""",
    },
    {
        "number": 3,
        "company": "Ocrolus",
        "role": "Senior Software Engineer, Python",
        "compensation": "$180,000 + equity",
        "employee_count": "501–1,000",
        "link": "https://job-boards.greenhouse.io/ocrolusinc/jobs/5745522004",
        "raw_text": """\
Senior Software Engineer, Python — Ocrolus
$180,000 + equity | Remote | 501–1,000 employees | Fintech / AI / SaaS

Ocrolus provides an automation platform converting paper documents (bank statements, pay stubs, invoices) into actionable data with over 99% accuracy. Trusted by 400+ customers including Better Mortgage, Brex, PayPal, Plaid, SoFi.

Who we're looking for:
- Bachelor's degree in Computer Science or related field
- 5+ years engineering experience
- Expert in Go and/or Python and/or Java and experience in building complex systems and applications
- Solid database skills (Postgres, MySQL etc) and data modeling experience
- Experience with Web Frameworks like Spring, Flask, and related ecosystems
- Strong problem-solving and communication skills
- Can contribute best-practices and architectural leadership to backend applications
- Experience leading and owning projects from beginning to end
- Experience with agile methodologies and automated testing
- Familiarity with containerisation, microservices architecture, continuous integration, Amazon Web Services, and deployment

What you'll do:
- Designing, implementing, and maintaining Microservices using Python/Go
- Build systems, services, and tools that securely scale over millions of transactions
- Build and scale online services and data pipelines
- Collaborate with other teams on security, reliability, and automation
""",
    },
    {
        "number": 4,
        "company": "Peach",
        "role": "Senior Backend Engineer",
        "compensation": "$150,000–$195,000",
        "employee_count": "11–50",
        "link": "https://ats.rippling.com/peach-finance/jobs/c24fa972-d314-4eb3-a572-67cd715cb70e",
        "raw_text": """\
Senior Backend Engineer — Peach
$150,000–$195,000 | Remote | 11–50 employees | FinTech / Loan Management SaaS

Peach is a modern loan management and servicing platform. API-first architecture enabling lenders to bring products to market quickly while maintaining full compliance and operational efficiency. Scaling toward $100M ARR.

What You'll Do:
- Design, develop, and maintain core backend services and APIs for our loan management SaaS platform, primarily using Python and Go
- Architect and build scalable, reliable, and secure systems to support new product lines
- Collaborate with product and stakeholders to translate business requirements into robust technical solutions
- Mentor other engineers and contribute to a culture of technical excellence
- Own features from conception through deployment using CircleCI, GCP, and Kubernetes

What You'll Bring:
- 5+ years of professional backend software development experience, preferably in a SaaS or product-driven environment
- Significant professional experience with Python and a proven track record of building complex, maintainable applications
- Experience designing, building, and operating distributed systems and microservices
- Strong experience developing and consuming APIs
- A commitment to writing clean, reliable, and well-tested code
- Excellent communication skills and the ability to articulate complex technical concepts to diverse audiences

Bonus Points:
- Experience with Go (Golang)
- Hands-on experience with DevOps practices and tools (Kubernetes, Docker, Terraform)
- Experience with GCP or other major cloud providers
- Previous experience in FinTech or another highly-regulated industry
""",
    },
    {
        "number": 5,
        "company": "Peerspace",
        "role": "Senior Data Engineer",
        "compensation": "$160,000–$175,000",
        "employee_count": "51–200",
        "link": "https://jobs.lever.co/peerspace/d176dd15-fed6-455f-801c-5b7284dc93bc",
        "raw_text": """\
Senior Data Engineer — Peerspace
$160,000–$175,000 | Remote | 51–200 employees | Marketplace / Consumer Services

Peerspace is the leading online marketplace for venue rentals. $500M+ transacted. Investors: GV (Google Ventures), Foundation Capital.

We are looking for a Senior Data Engineer who approaches data with the mindset of a Software Engineer. You will take ownership of decomposing and modernizing legacy business data pipelines and building data services that expose critical information within the product.

What we are looking for:
- Software-Driven Data Engineering: Deep understanding of software design patterns and data engineering basics. Opinionated on best practices for data orchestration and storage. Apply engineering rigor (modularity, testing, maintainability) to data workflows.
- Strategic Pragmatism: Track record of balancing short-term business requirements with long-term technical health.
- Python & SQL Mastery: Highly proficient in Python, complex performant SQL.
- Architectural Grit: Track record of breaking down high-level business requirements into technical roadmaps and executing them.
- Collaborative Ownership: Proactive communicator, owning a problem from discovery to resolution.
- The Startup Spirit: Comfortable with ambiguity. Dig into the code to figure out how things work.

Bonus Points:
- Experience deploying ML pipelines and working with LLM tooling
- Experience with dbt
- Experience with real-time or near real-time data processing (streaming)

Tech Stack (not required, just FYI): GCP, BigQuery, Airflow, dbt, Metaplane, Segment, Postgres, Tableau
""",
    },
    # ── Batch 2 starts here (partial batch — tests the boundary) ──────────────
    {
        "number": 6,
        "company": "Coalition",
        "role": "Senior Software Engineer, Scanning Engine",
        "compensation": "$136,900–$201,737",
        "employee_count": "501–1,000",
        "link": "https://www.coalitioninc.com/job-posting/4665887005",
        "raw_text": """\
Senior Software Engineer, Scanning Engine — Coalition
$136,900–$201,737 | Remote | 501–1,000 employees | Cyber Insurance / B2B SaaS

Coalition is the world's first Active Insurance provider combining comprehensive insurance coverage and cybersecurity tools. $770M total funding.

Skills and Qualifications:
- Strong experience as a Senior Software Engineer working on backend or systems-level services
- Proficiency in at least one of Python or Go, with the ability and willingness to work in both languages over time
- Demonstrated experience with systems design for distributed or high-availability services, including scalability, reliability, and observability
- Hands-on experience building or maintaining scanning, detection, or similar engine-like systems (e.g., vulnerability scanning, security scanning, data processing pipelines, or similar high-throughput engines)
- Strong software engineering fundamentals: data structures, algorithms, concurrency, and performance optimization
- Experience working in a cloud-native environment (microservices, containers, CI/CD, monitoring, logging)
- Ability to collaborate effectively across teams and communicate tradeoffs clearly
- Proven track record of owning projects end-to-end
- Comfort operating in a fast-paced environment making pragmatic technical decisions while maintaining quality and security

Bonus Points: Cyber security domain knowledge in scanning through endpoints

What you'll do:
- Own end-to-end systems design for key components of the scanning engine
- Design and implement high-quality services in Python and Go
- Improve performance, scalability, and reliability of the scanning engine
- Partner with security, product, and data teams to translate detection and scanning requirements into robust systems
- Mentor and support other engineers through design feedback and knowledge sharing
""",
    },
    {
        "number": 7,
        "company": "Accompany Health",
        "role": "Principal Data Engineer",
        "compensation": "$180,000–$215,000 + equity",
        "employee_count": "201–500",
        "link": "https://www.accompanyhealth.com/careers",
        "raw_text": """\
Principal Data Engineer — Accompany Health
$180,000–$215,000 + equity | Remote | 201–500 employees | Healthcare / Value-Based Care

Accompany Health is on a mission to give patients with complex needs the dignified, high-quality care they deserve. A primary, behavioral, and social care provider. Partners with innovative payors.

Responsibilities:
- Be a data champion and empower others to leverage data to its full potential
- Work with product and stakeholders to translate business requirements into a technical roadmap and architecture
- Act as the leading data domain expert and own platform data architecture
- Lead technical design and implementation of reliable, scalable, and efficient data infrastructure
- Create and maintain optimal data pipeline architecture with high observability and robust operational characteristics
- Build infrastructure for optimal extraction, transformation, and loading of data from a wide variety of data sources using SQL
- Create data tools for analytics and data scientist teams

Required:
- Advanced working SQL knowledge and experience working with relational databases
- Experience building and optimizing big data pipelines, architectures, and data sets
- Experience performing root cause analysis on internal and external data and processes
- Strong analytic skills related to working with unstructured datasets
- Working knowledge of message queuing, stream processing, and highly scalable big data data stores
- 7+ years of experience in a Data Engineer role with a Graduate degree in a quantitative field

Tech Stack (nice to have, not required): Snowflake, SQL/NoSQL databases, Python/Golang/Java/Scala, Spark, Kafka, Airflow

Note: ORToothFairy healthcare experience is a genuine mission narrative for this role.
""",
    },
]


# ── Seed functions ────────────────────────────────────────────────────────────

async def reset_tables(db):
    """Truncate all tables in reverse FK order. Dev only."""
    print("Resetting tables...")
    tables = ["activities", "tailoring_jobs", "jds", "sessions", "resumes", "prompt_templates", "users"]
    for table in tables:
        await db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
    await db.commit()
    print("  Tables cleared.")


async def seed_user(db) -> User:
    result = await db.execute(select(User))
    existing = result.scalars().first()
    if existing:
        print(f"  User already exists: {existing.id}")
        return existing

    user = User(auth_token="dev-token-nicole")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    print(f"  Created user: {user.id}")
    return user


async def seed_resumes(db, user: User) -> list[Resume]:
    result = await db.execute(select(Resume).where(Resume.user_id == user.id))
    existing = result.scalars().all()
    if existing:
        print(f"  Resumes already exist ({len(existing)} found), skipping.")
        return existing

    created = []
    for r in RESUMES:
        resume = Resume(user_id=user.id, label=r["label"], content=r["content"].strip())
        db.add(resume)
        created.append(resume)

    await db.commit()
    for r in created:
        await db.refresh(r)
    print(f"  Created {len(created)} resumes.")
    return created


async def seed_session(db, user: User) -> SessionModel:
    result = await db.execute(select(SessionModel).where(SessionModel.user_id == user.id))
    existing = result.scalars().first()
    if existing:
        print(f"  Session already exists: {existing.id}")
        return existing

    session = SessionModel(
        user_id=user.id,
        board="LinkedIn",
        filters="Remote, Last 24 hours, $160K+",
        search_term="Staff Data Engineer",
        status=SessionStatus.active,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    print(f"  Created session: {session.id}")
    return session


async def seed_jds(db, session: SessionModel) -> list[JD]:
    result = await db.execute(select(JD).where(JD.session_id == session.id))
    existing = result.scalars().all()
    if existing:
        print(f"  JDs already exist ({len(existing)} found), skipping.")
        return existing

    created = []
    for jd_data in JDS:
        raw = jd_data["raw_text"]
        cleaned = clean_jd_text(raw)
        jd = JD(
            session_id=session.id,
            number=jd_data["number"],
            raw_text=raw,
            cleaned_text=cleaned,
            company=jd_data["company"],
            role=jd_data["role"],
            compensation=jd_data.get("compensation"),
            employee_count=jd_data.get("employee_count"),
            link=jd_data.get("link"),
            status=JDStatus.pending,
            status_source=JDStatusSource.ai,
        )
        db.add(jd)
        created.append(jd)

    await db.commit()
    for jd in created:
        await db.refresh(jd)

    print(f"  Created {len(created)} JDs:")
    for jd in created:
        batch = "batch 1" if jd.number <= 5 else "batch 2"
        print(f"    #{jd.number} {jd.company} — {jd.role} ({batch})")
    return created


# ── Entry point ───────────────────────────────────────────────────────────────

async def main(reset: bool = False):
    async with AsyncSessionLocal() as db:
        if reset:
            await reset_tables(db)

        print("\nSeeding user...")
        user = await seed_user(db)

        print("Seeding resumes...")
        await seed_resumes(db, user)

        print("Seeding session...")
        session = await seed_session(db, user)

        print("Seeding JDs...")
        await seed_jds(db, session)

        print(f"\nDone. Session ID to use in Swagger: {session.id}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the ApplicationPipeline dev database.")
    parser.add_argument("--reset", action="store_true", help="Truncate all tables before seeding.")
    args = parser.parse_args()
    asyncio.run(main(reset=args.reset))
