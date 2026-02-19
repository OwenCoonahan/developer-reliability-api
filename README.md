# Developer Reliability Score API

A FastAPI backend that scores energy project developers based on their interconnection queue track records across US ISOs.

## What It Does

Analyzes 31,000+ projects across 9 ISOs to compute a **Developer Reliability Score (0-100)** for 5,600+ developers. The score weighs:

- **Completion rate** (30%) — Do they finish what they start?
- **Timeline to COD** (20%) — How fast do they deliver?
- **Project volume** (15%) — How experienced are they?
- **Regional breadth** (10%) — How geographically diverse?
- **Technology diversity** (10%) — Multi-technology capability
- **Active pipeline** (10%) — Current business activity
- **Track record depth** (5%) — How long in business?

Only developers with 5+ resolved outcomes (operational or withdrawn) receive scores. Currently **958 developers** are scored.

## Quick Start

```bash
# Clone and setup
cp .env.example .env
pip install -r requirements.txt

# Build the database (requires access to queue.db)
python data/init_db.py

# Run the API
uvicorn app.main:app --reload
```

## API Endpoints

All endpoints require `X-API-Key` header.

| Endpoint | Description |
|----------|-------------|
| `GET /v1/developers` | List/search developers (paginated) |
| `GET /v1/developers/rankings` | Ranked by score |
| `GET /v1/developers/compare?names=A,B,C` | Side-by-side comparison |
| `GET /v1/developers/{name}` | Full developer scorecard |
| `GET /v1/developers/{name}/projects` | Developer's projects |
| `GET /v1/stats` | Aggregate statistics |
| `GET /health` | Health check (no auth) |

### Query Parameters

**`/v1/developers`**: `search`, `region`, `fuel_type`, `min_projects`, `sort_by`, `page`, `per_page`

**`/v1/developers/rankings`**: `sort_by` (score, completion_rate, total_projects, operational), `page`, `per_page`

## Example

```bash
curl -H "X-API-Key: dev-key-change-me" http://localhost:8000/v1/developers/rankings?per_page=5
```

## Deploy to Railway

1. Push to GitHub
2. Connect repo in Railway
3. Set environment variables: `API_KEYS`, `DATABASE_PATH=data/developers.duckdb`
4. Railway auto-detects the Dockerfile

## Tech Stack

- **FastAPI** + **Pydantic v2**
- **DuckDB** (embedded analytics database)
- Source data from ISO interconnection queues via `queue-analysis-project`
