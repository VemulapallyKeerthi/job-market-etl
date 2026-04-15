-- Clean unified jobs table
CREATE TABLE IF NOT EXISTS jobs_clean (
  id                serial PRIMARY KEY,
  raw_job_id        int REFERENCES jobs(id),
  title             text,
  title_normalized  text,
  company           text,
  city              text,
  state             text,
  country           text,
  is_remote         boolean,
  job_level         text,
  job_category      text,
  source            text,
  posted_date       date,
  apply_link        text,
  created_at        timestamp DEFAULT now()
);

-- ETL run log table
CREATE TABLE IF NOT EXISTS etl_runs (
  id              serial PRIMARY KEY,
  run_at          timestamp DEFAULT now(),
  jobs_fetched    int,
  jobs_inserted   int,
  jobs_skipped    int,
  status          text,
  error_msg       text
);