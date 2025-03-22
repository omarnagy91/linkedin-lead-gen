# Database Schema

This document outlines the database schema for the LinkedIn Lead Generation system using Supabase (PostgreSQL).

## Tables

### jobs

Stores information about each lead generation job.

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_email TEXT NOT NULL,
    campaign_goal TEXT,
    company_urls TEXT[] NOT NULL,
    countries TEXT[] NOT NULL,
    employment_status TEXT NOT NULL,
    decision_level TEXT,
    status TEXT DEFAULT 'submitted',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### search_queries

Stores search queries generated for each job.

```sql
CREATE TABLE search_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    company TEXT NOT NULL,
    country TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    results_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### profile_urls

Stores LinkedIn profile URLs found from searches.

```sql
CREATE TABLE profile_urls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    linkedin_url TEXT NOT NULL,
    company TEXT NOT NULL,
    country TEXT NOT NULL,
    search_snippet TEXT,
    status TEXT DEFAULT 'discovered',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id, linkedin_url)
);
```

### profiles

Stores enriched profile data from ProxyCurl.

```sql
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    linkedin_url TEXT NOT NULL,
    profile_data JSONB NOT NULL,
    job_title TEXT,
    company_specific_title TEXT,
    experience_years NUMERIC,
    meets_criteria BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id, linkedin_url)
);
```

### title_selections

Stores job title selections made by user.

```sql
CREATE TABLE title_selections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    count INTEGER DEFAULT 0,
    selected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id, title, company)
);
```

### exports

Stores information about exports.

```sql
CREATE TABLE exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    google_sheet_url TEXT,
    status TEXT DEFAULT 'pending',
    profiles_exported INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
```

## Indexes

```sql
-- job_id indexes for all related tables
CREATE INDEX idx_search_queries_job_id ON search_queries(job_id);
CREATE INDEX idx_profile_urls_job_id ON profile_urls(job_id);
CREATE INDEX idx_profiles_job_id ON profiles(job_id);
CREATE INDEX idx_title_selections_job_id ON title_selections(job_id);
CREATE INDEX idx_exports_job_id ON exports(job_id);

-- URL lookup index
CREATE INDEX idx_profile_urls_url ON profile_urls(linkedin_url);
CREATE INDEX idx_profiles_url ON profiles(linkedin_url);

-- Status indexes
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_search_queries_status ON search_queries(status);
CREATE INDEX idx_profile_urls_status ON profile_urls(status);
CREATE INDEX idx_exports_status ON exports(status);

-- Title selection index
CREATE INDEX idx_title_selections_selected ON title_selections(selected);
```

## Row Level Security Policies

In production, we should set up Row Level Security to ensure users can only access their own data:

```sql
-- Enable RLS on jobs table
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Create policy for jobs table
CREATE POLICY job_user_policy ON jobs
    FOR ALL
    USING (user_email = current_user_email());

-- Similar policies for related tables
-- (implementation depends on authentication system)
```

## Functions

### update_job_timestamp

Function to automatically update the `updated_at` timestamp when a job is modified:

```sql
CREATE OR REPLACE FUNCTION update_job_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_job_timestamp
BEFORE UPDATE ON jobs
FOR EACH ROW
EXECUTE FUNCTION update_job_timestamp();
```

### aggregate_job_titles

Function to aggregate job titles for a given job:

```sql
CREATE OR REPLACE FUNCTION aggregate_job_titles(job_uuid UUID)
RETURNS TABLE (company TEXT, title TEXT, count BIGINT) AS $$
BEGIN
    RETURN QUERY
        SELECT 
            p.company,
            p.job_title,
            COUNT(*) as count
        FROM 
            profiles p
        WHERE 
            p.job_id = job_uuid
            AND p.job_title IS NOT NULL
            AND p.meets_criteria = TRUE
        GROUP BY 
            p.company, p.job_title
        ORDER BY 
            p.company, count DESC;
END;
$$ LANGUAGE plpgsql;
```
