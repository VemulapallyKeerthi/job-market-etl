import os
import math
import logging
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from transform.clean_jobs import clean_jobs

load_dotenv()

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Setup logging
logging.basicConfig(
    filename='logs/etl.log',
    level=logging.INFO,
    format='%(asctime)s — %(levelname)s — %(message)s'
)


def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)


def fetch_raw_jobs(client):
    """Fetch all jobs from the raw jobs table using pagination."""
    all_jobs = []
    page_size = 1000
    offset = 0

    while True:
        response = client.table("jobs").select("*").range(offset, offset + page_size - 1).execute()
        batch = response.data
        if not batch:
            break
        all_jobs.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size

    return all_jobs


def get_existing_raw_ids(client):
    """Fetch all already-loaded raw_job_ids using pagination."""
    all_ids = set()
    page_size = 1000
    offset = 0

    while True:
        response = client.table("jobs_clean").select("raw_job_id").range(offset, offset + page_size - 1).execute()
        batch = response.data
        if not batch:
            break
        all_ids.update(row["raw_job_id"] for row in batch)
        if len(batch) < page_size:
            break
        offset += page_size

    return all_ids


def log_etl_run(client, jobs_fetched, jobs_inserted, jobs_skipped, status, error_msg=None):
    client.table("etl_runs").insert({
        "run_at": datetime.utcnow().isoformat(),
        "jobs_fetched": jobs_fetched,
        "jobs_inserted": jobs_inserted,
        "jobs_skipped": jobs_skipped,
        "status": status,
        "error_msg": error_msg
    }).execute()


def sanitize(val):
    """Convert NaN/inf floats to None for JSON safety."""
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val


def run_etl():
    logging.info("ETL run started")
    client = get_supabase_client()

    jobs_fetched = 0
    jobs_inserted = 0
    jobs_skipped = 0

    try:
        # Extract
        raw_jobs = fetch_raw_jobs(client)
        jobs_fetched = len(raw_jobs)
        logging.info(f"Fetched {jobs_fetched} raw jobs")

        # Get already loaded IDs
        existing_ids = get_existing_raw_ids(client)
        logging.info(f"Found {len(existing_ids)} already loaded jobs")

        # Filter out already loaded jobs
        new_jobs = [j for j in raw_jobs if j["id"] not in existing_ids]
        jobs_skipped = jobs_fetched - len(new_jobs)
        logging.info(f"New jobs to process: {len(new_jobs)}, Skipped: {jobs_skipped}")

        if not new_jobs:
            logging.info("No new jobs to load. ETL complete.")
            log_etl_run(client, jobs_fetched, 0, jobs_skipped, "success")
            return

        # Transform
        df = clean_jobs(new_jobs)

        # Load — sanitize all NaN/inf values before JSON serialization
        records = [
            {k: sanitize(v) for k, v in row.items()}
            for row in df.to_dict(orient="records")
        ]
        client.table("jobs_clean").insert(records).execute()
        jobs_inserted = len(records)
        logging.info(f"Inserted {jobs_inserted} clean jobs")

        log_etl_run(client, jobs_fetched, jobs_inserted, jobs_skipped, "success")
        logging.info("ETL run completed successfully")

    except Exception as e:
        logging.error(f"ETL failed: {e}")
        log_etl_run(client, jobs_fetched, jobs_inserted, jobs_skipped, "failed", str(e))
        raise