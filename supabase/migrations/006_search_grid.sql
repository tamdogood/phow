CREATE TABLE search_grid_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_profile_id UUID NOT NULL REFERENCES business_profiles ON DELETE CASCADE,
  name TEXT NOT NULL,
  center_lat DECIMAL(10,7) NOT NULL,
  center_lng DECIMAL(10,7) NOT NULL,
  center_address TEXT,
  place_id TEXT,
  radius_km DECIMAL(5,2) NOT NULL DEFAULT 5,
  grid_size INT NOT NULL DEFAULT 7,
  keywords TEXT[] NOT NULL,
  frequency TEXT NOT NULL DEFAULT 'weekly',
  schedule_day INT DEFAULT 5,
  schedule_hour INT DEFAULT 9,
  timezone TEXT DEFAULT 'America/New_York',
  notify_email TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  last_run_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE search_grid_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id UUID NOT NULL REFERENCES search_grid_reports ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'running',
  avg_rank DECIMAL(4,1),
  top3_pct DECIMAL(5,2),
  points_completed INT DEFAULT 0,
  points_total INT DEFAULT 0,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

CREATE TABLE search_grid_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id UUID NOT NULL REFERENCES search_grid_runs ON DELETE CASCADE,
  report_id UUID NOT NULL,
  keyword TEXT NOT NULL,
  grid_row INT NOT NULL,
  grid_col INT NOT NULL,
  point_lat DECIMAL(10,7) NOT NULL,
  point_lng DECIMAL(10,7) NOT NULL,
  rank INT,
  total_results INT,
  top_result_name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sgr_profile ON search_grid_reports(business_profile_id);
CREATE INDEX idx_sgruns_report ON search_grid_runs(report_id);
CREATE INDEX idx_sgresults_run ON search_grid_results(run_id);
