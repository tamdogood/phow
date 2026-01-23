# Celery Data Pipeline Guide

This guide explains how to run the location intelligence data collection pipelines using Celery.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Starting Celery Services](#starting-celery-services)
- [Manual Task Execution](#manual-task-execution)
- [Scheduled Tasks](#scheduled-tasks)
- [Production Setup](#production-setup)
- [Monitoring](#monitoring)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Redis
Celery requires Redis as a message broker:

```bash
# Check if Redis is running
redis-cli ping  # Should return "PONG"

# Start Redis if not running
redis-server

# Or with Homebrew (macOS)
brew services start redis
```

### 2. Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Database Migration
Ensure the location intelligence migration is applied:

```sql
-- Run in Supabase SQL Editor
-- File: supabase/migrations/005_location_intelligence.sql
```

---

## Starting Celery Services

### Development Mode

#### Option 1: Separate Worker and Beat
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker
cd backend
celery -A app.workers.celery_app worker --loglevel=info

# Terminal 3: Start Celery Beat (Scheduler)
cd backend
celery -A app.workers.celery_app beat --loglevel=info
```

#### Option 2: Combined (Development Only)
```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Worker + Beat together
cd backend
celery -A app.workers.celery_app worker --beat --loglevel=info
```

### With Auto-Reload (Development)
```bash
# Install watchdog
pip install watchdog

# Auto-restart worker on code changes
cd backend
watchmedo auto-restart -d app/ -p '*.py' -- \
  celery -A app.workers.celery_app worker --loglevel=info
```

### With Specific Queues
```bash
# Run worker for specific queues
celery -A app.workers.celery_app worker \
  --loglevel=info \
  -Q data_collection,maintenance
```

---

## Manual Task Execution

### Via Python Shell

```python
# Start Python shell
python

# Import tasks
from app.workers.tasks import (
    collect_crime_data,
    collect_health_inspections,
    collect_walkscore,
    collect_search_trends,
    refresh_all_city_data,
    refresh_trends_data,
    cleanup_expired_data
)

# Trigger single city crime data collection
result = collect_crime_data.delay("New York", "NY", 40.7128, -74.0060)
print(result.status)  # 'PENDING', 'SUCCESS', 'FAILURE'
print(result.get(timeout=300))  # Wait for result (5 min timeout)

# Trigger Walk Score for a location
result = collect_walkscore.delay(40.7128, -74.0060, "New York", "Empire State Building")
print(result.get())

# Trigger health inspections
result = collect_health_inspections.delay("Chicago", "IL", 41.8781, -87.6298)
print(result.get())

# Trigger search trends
result = collect_search_trends.delay(["coffee shop", "cafe near me"], "New York")
print(result.get())

# Trigger full city data refresh (all 20 cities)
result = refresh_all_city_data.delay()
print(result.get(timeout=600))  # 10 min timeout for all cities

# Trigger trends refresh (all keyword groups)
result = refresh_trends_data.delay()
print(result.get())

# Cleanup expired data
result = cleanup_expired_data.delay()
print(result.get())
```

### Via FastAPI Endpoint (Create if needed)

```python
# backend/app/api/routes/admin.py (example)

from fastapi import APIRouter, BackgroundTasks
from app.workers.tasks import refresh_all_city_data

router = APIRouter()

@router.post("/admin/refresh-data")
async def trigger_data_refresh():
    result = refresh_all_city_data.delay()
    return {"task_id": result.id, "status": "queued"}
```

---

## Scheduled Tasks

Once Celery Beat is running, these tasks execute automatically:

| Task | Schedule | Description |
|------|----------|-------------|
| `refresh_all_city_data` | Every 24 hours | Collects crime, health, and Walk Score data for all 20 target cities |
| `refresh_trends_data` | Every 7 days | Updates Google Trends data for F&B keywords |
| `cleanup_expired_data` | Every 24 hours | Removes expired embeddings and location intelligence records |

### Target Cities (20 US Metros)
New York, Los Angeles, Chicago, Houston, Phoenix, Philadelphia, San Antonio, San Diego, Dallas, San Jose, Austin, Jacksonville, Fort Worth, Columbus, Charlotte, San Francisco, Indianapolis, Seattle, Denver, Washington DC

### Data Collection Per City
For each city, the following data is collected:
- **Crime Data** (daily refresh) - Safety scores, crime statistics
- **Health Inspections** (weekly refresh) - Restaurant health scores
- **Walk Score** (monthly refresh) - Walkability, transit, bike scores

### Trends Keywords
```python
# Default F&B trending keywords (from tasks.py)
[
    ["coffee shop", "cafe near me"],
    ["pizza delivery", "pizza restaurant"],
    ["boba tea", "bubble tea"],
    ["sushi restaurant", "japanese food"],
    ["mexican restaurant", "tacos near me"],
    ["burger restaurant", "best burgers"],
    ["healthy food", "salad restaurant"],
    ["food delivery", "takeout near me"],
]
```

---

## Production Setup

### Using Systemd (Linux)

#### Worker Service
```ini
# /etc/systemd/system/celery-worker.service

[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/phow/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A app.workers.celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  -Q data_collection,maintenance \
  --pidfile=/var/run/celery-worker.pid

[Install]
WantedBy=multi-user.target
```

#### Beat Service
```ini
# /etc/systemd/system/celery-beat.service

[Unit]
Description=Celery Beat Scheduler
After=network.target redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/phow/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A app.workers.celery_app beat \
  --loglevel=info \
  --pidfile=/var/run/celery-beat.pid

[Install]
WantedBy=multi-user.target
```

#### Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat
sudo systemctl status celery-worker celery-beat
```

### Using Supervisor

```ini
# /etc/supervisor/conf.d/celery.conf

[program:celery_worker]
command=/path/to/venv/bin/celery -A app.workers.celery_app worker --loglevel=info -Q data_collection,maintenance
directory=/path/to/phow/backend
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker_err.log

[program:celery_beat]
command=/path/to/venv/bin/celery -A app.workers.celery_app beat --loglevel=info
directory=/path/to/phow/backend
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat_err.log
```

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start celery_worker celery_beat
```

### Using Docker Compose

```yaml
# docker-compose.yml (add to existing)

services:
  celery_worker:
    build: ./backend
    command: celery -A app.workers.celery_app worker --loglevel=info
    depends_on:
      - redis
      - backend
    env_file:
      - ./backend/.env
    volumes:
      - ./backend:/app

  celery_beat:
    build: ./backend
    command: celery -A app.workers.celery_app beat --loglevel=info
    depends_on:
      - redis
      - backend
    env_file:
      - ./backend/.env
    volumes:
      - ./backend:/app
```

```bash
docker-compose up celery_worker celery_beat
```

---

## Monitoring

### Celery Flower (Web UI)

```bash
# Install Flower
pip install flower

# Start Flower
celery -A app.workers.celery_app flower --port=5555

# Open in browser
# http://localhost:5555
```

Features:
- Real-time task monitoring
- Worker statistics
- Task history and results
- Task routing visualization

### Command-Line Inspection

```bash
# Check active tasks
celery -A app.workers.celery_app inspect active

# Check scheduled tasks
celery -A app.workers.celery_app inspect scheduled

# Check registered tasks
celery -A app.workers.celery_app inspect registered

# Check worker stats
celery -A app.workers.celery_app inspect stats

# List active queues
celery -A app.workers.celery_app inspect active_queues

# Ping workers
celery -A app.workers.celery_app inspect ping
```

### Logging

```bash
# View worker logs (if using systemd)
journalctl -u celery-worker -f

# View beat logs
journalctl -u celery-beat -f

# View logs with supervisor
tail -f /var/log/celery/worker.log
tail -f /var/log/celery/beat.log
```

---

## Environment Variables

Ensure these are set in `backend/.env`:

```bash
# ===== Required for Data Collection =====

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-...

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...

# Redis (Celery broker)
REDIS_URL=redis://localhost:6379/0

# ===== Location Intelligence APIs (Phase 1 - Free) =====

# Walk Score API
WALKSCORE_API_KEY=your_key_here
# Get: https://www.walkscore.com/professional/api.php

# Crime Mapping API (optional, using Socrata instead)
CRIMEMAPPING_API_KEY=

# EIA API (utility costs)
EIA_API_KEY=
# Get: https://www.eia.gov/opendata/register.php

# ===== Scraping Infrastructure (Optional) =====

SCRAPING_PROXY_URL=
SCRAPING_API_KEY=
# Providers: ScrapingBee, Bright Data, Apify ($50-200/mo)

# ===== Celery Configuration =====

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## Troubleshooting

### Worker Not Starting

```bash
# Check Redis connection
redis-cli ping

# Check if port is available
lsof -i :6379

# Verify Celery app module
python -c "from app.workers.celery_app import celery_app; print(celery_app)"

# Check for import errors
python -m app.workers.tasks
```

### Tasks Not Executing

```bash
# Check if workers are registered
celery -A app.workers.celery_app inspect registered

# Check if tasks are queued
celery -A app.workers.celery_app inspect scheduled

# Purge all tasks (careful!)
celery -A app.workers.celery_app purge

# Check worker queues
celery -A app.workers.celery_app inspect active_queues
```

### Beat Not Scheduling

```bash
# Remove stale beat schedule file
rm celerybeat-schedule

# Check beat is running
ps aux | grep celery

# Verify schedule configuration
python -c "from app.workers.tasks import celery_app; print(celery_app.conf.beat_schedule)"
```

### Task Failures

```python
# Get task result and traceback
from app.workers.tasks import collect_crime_data

result = collect_crime_data.delay("New York", "NY", 40.7128, -74.0060)
try:
    print(result.get(timeout=60))
except Exception as e:
    print(f"Error: {e}")
    print(result.traceback)
```

### API Rate Limits

```python
# Tasks have retry logic built in (max_retries=3, countdown=60s)
# Check task logs for rate limit errors

# Adjust retry settings in tasks.py:
@celery_app.task(bind=True, max_retries=5)
def collect_crime_data(self, ...):
    try:
        # ...
    except RateLimitError as e:
        raise self.retry(exc=e, countdown=120)  # Wait 2 minutes
```

### Database Connection Issues

```bash
# Verify Supabase connection
python -c "from app.api.deps import get_supabase; db = get_supabase(); print(db)"

# Check pgvector extension
# Run in Supabase SQL Editor:
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Memory Issues

```bash
# Limit worker concurrency
celery -A app.workers.celery_app worker --concurrency=2

# Enable worker max tasks per child (prevents memory leaks)
celery -A app.workers.celery_app worker --max-tasks-per-child=100

# Monitor memory
celery -A app.workers.celery_app inspect stats
```

---

## Quick Reference

### Start All Services (Development)

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: FastAPI
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 3: Celery Worker
cd backend
celery -A app.workers.celery_app worker --loglevel=info

# Terminal 4: Celery Beat
cd backend
celery -A app.workers.celery_app beat --loglevel=info

# Terminal 5: Flower (optional)
cd backend
celery -A app.workers.celery_app flower --port=5555
```

### Common Commands

```bash
# Trigger full data refresh
python -c "from app.workers.tasks import refresh_all_city_data; refresh_all_city_data.delay()"

# Cleanup expired data
python -c "from app.workers.tasks import cleanup_expired_data; cleanup_expired_data.delay()"

# Check worker status
celery -A app.workers.celery_app inspect ping

# View all registered tasks
celery -A app.workers.celery_app inspect registered

# Monitor with Flower
celery -A app.workers.celery_app flower
```

---

## Next Steps

1. ✅ Set environment variables in `backend/.env`
2. ✅ Start Redis server
3. ✅ Start Celery worker and beat
4. ✅ Verify tasks are registered
5. ✅ Trigger a test task manually
6. ✅ Monitor execution with Flower
7. ✅ Check database for collected data

For questions or issues, check the logs or raise an issue in the repository.
