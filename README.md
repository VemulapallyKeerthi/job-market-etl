## 📊 Job Market ETL Pipeline

An automated ETL pipeline that extracts job postings from multiple job boards, transforms and cleans the raw data, loads it into a PostgreSQL database, and visualizes hiring trends on a live dashboard.
🔗 Live Dashboard: job-market-trends.streamlit.app

## 🏗️ Architecture

[Raw Jobs Table (Supabase)]

        ↓  Extract
[Python Transform Layer]
        ↓  Clean, Normalize, Enrich
[jobs_clean Table (Supabase)]
        ↓  Query
[Streamlit Dashboard]

## ⚙️ What It Does

Extract — Reads raw job postings scraped from LinkedIn and Indeed
Transform — Normalizes job titles, parses messy location strings into city/state/country/remote flag, infers seniority level and job category from title keywords, and deduplicates across sources
Load — Upserts clean records into a structured Supabase table with duplicate prevention
Observability — Logs every ETL run (jobs fetched, inserted, skipped, status) into an etl_runs table
Schedule — GitHub Actions cron job runs the pipeline automatically every day at 6 AM UTC
Dashboard — Live Streamlit app visualizing job trends, top cities, companies, categories, and seniority breakdown

## 🛠️ Tech Stack

LayerToolLanguagePython 3.12DatabaseSupabase (PostgreSQL)TransformPandasDashboardStreamlit + PlotlySchedulingGitHub ActionsDeploymentStreamlit Cloud

## 📁 Project Structure

job-market-etl/
├── transform/
│   └── clean_jobs.py       # All transformation logic
├── load/
│   ├── load_to_supabase.py # ETL orchestration + logging
│   └── create_tables.sql   # SQL schema for clean tables
├── dashboard/
│   └── app.py              # Streamlit dashboard
├── .github/
│   └── workflows/
│       └── etl.yml         # GitHub Actions schedule
├── main.py                 # Entry point
├── requirements.txt
└── .env                    # Local secrets (not committed)

## 🚀 Running Locally

1. Clone the repo
bashgit clone https://github.com/VemulapallyKeerthi/job-market-etl.git
cd job-market-etl
2. Create virtual environment
bashpython -m venv .venv
.venv\Scripts\Activate  # Windows
source .venv/bin/activate  # Mac/Linux
3. Install dependencies
bashpip install -r requirements.txt
4. Set up environment variables
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
5. Run the ETL
bashpython main.py
6. Run the dashboard
bashstreamlit run dashboard/app.py

## 📊 Dashboard Features

KPI metrics — Total jobs, companies, remote count, sources
Jobs by category — ML/AI, Data Science, Data Engineering, Analytics
Jobs by seniority — Intern, Junior, Mid, Senior, Leadership
Top hiring cities — Where the jobs are
Top hiring companies — Who's hiring the most
Remote vs On-site — Breakdown across all postings
Postings over time — Volume trend by date
Filterable job table — Browse by category, level, and source


## 🔄 Automated Schedule

The pipeline runs daily via GitHub Actions at 6:00 AM UTC. Each run logs results to the etl_runs table for full observability.