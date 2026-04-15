import re
import pandas as pd


def normalize_title(title: str) -> str:
    """Lowercase and strip common noise from job titles."""
    if not title:
        return ""
    title = title.lower().strip()
    title = re.sub(r'\(.*?\)', '', title)        # remove parentheses
    title = re.sub(r'[-–|,].*remote.*', '', title)  # remove "- remote" suffixes
    title = re.sub(r'\s+', ' ', title).strip()
    return title


def extract_job_level(title: str) -> str:
    """Infer seniority level from title."""
    title = title.lower()
    if any(w in title for w in ['intern', 'internship']):
        return 'intern'
    if any(w in title for w in ['junior', 'jr', 'entry']):
        return 'junior'
    if any(w in title for w in ['senior', 'sr', 'lead', 'principal', 'staff']):
        return 'senior'
    if any(w in title for w in ['manager', 'director', 'head', 'vp', 'chief']):
        return 'leadership'
    return 'mid'


def extract_job_category(title: str) -> str:
    """Categorize job based on title keywords."""
    title = title.lower()
    if any(w in title for w in ['machine learning', 'ml ', 'ai ', 'deep learning', 'llm', 'nlp']):
        return 'ML/AI'
    if any(w in title for w in ['data engineer', 'etl', 'pipeline', 'data platform']):
        return 'Data Engineering'
    if any(w in title for w in ['data analyst', 'analytics', 'business intelligence', 'bi ']):
        return 'Analytics'
    if any(w in title for w in ['data scientist', 'data science']):
        return 'Data Science'
    if any(w in title for w in ['software engineer', 'backend', 'frontend', 'full stack', 'developer']):
        return 'Software Engineering'
    return 'Other'


def parse_location(location: str):
    """Parse messy location string into components."""
    if not location:
        return None, None, None, False

    is_remote = 'remote' in location.lower()

    # Strip "Remote in" prefix
    cleaned = re.sub(r'(?i)^remote\s+in\s+', '', location).strip()

    # Remove zip codes
    cleaned = re.sub(r'\b\d{5}\b', '', cleaned).strip().strip(',').strip()

    parts = [p.strip() for p in cleaned.split(',')]

    city, state, country = None, None, 'USA'

    if len(parts) == 1:
        if parts[0] == '' or parts[0].lower() == 'remote':
            pass
        else:
            city = parts[0]
    elif len(parts) == 2:
        city, state = parts[0], parts[1]
    elif len(parts) >= 3:
        city, state = parts[0], parts[1]
        country = parts[2]
        if country.lower() in ['usa', 'us', 'united states']:
            country = 'USA'

    # Detect non-US
    if state and len(state.strip()) > 3:
        country = state.strip()
        state = None

    return city, state, country, is_remote


def clean_jobs(raw_jobs: list[dict]) -> pd.DataFrame:
    """Transform raw job records into clean structured rows."""
    cleaned = []

    for job in raw_jobs:
        city, state, country, is_remote = parse_location(job.get('location', ''))
        title = job.get('title', '')

        cleaned.append({
            'raw_job_id':       job['id'],
            'title':            title,
            'title_normalized': normalize_title(title),
            'company':          job.get('company', '').strip(),
            'city':             city,
            'state':            state,
            'country':          country,
            'is_remote':        is_remote,
            'job_level':        extract_job_level(title),
            'job_category':     extract_job_category(title),
            'source':           job.get('source', ''),
            'posted_date':      job.get('posted_date'),
            'apply_link':       job.get('apply_link', ''),
        })

    return pd.DataFrame(cleaned)