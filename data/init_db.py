#!/usr/bin/env python3
"""Extract developer data from queue.db and build scored DuckDB database."""

import os
import sys
import csv

# Add parent dir for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import duckdb

SOURCE_DB = os.environ.get(
    "SOURCE_DB",
    os.path.expanduser(
        "~/.openclaw/workspace/queue-analysis-project/tools/.data/queue.db"
    ),
)
REGISTRY_CSV = os.environ.get(
    "REGISTRY_CSV",
    os.path.expanduser(
        "~/.openclaw/workspace/queue-analysis-project/tools/.data/developer_registry.csv"
    ),
)
OUTPUT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "developers.duckdb")


def main():
    if os.path.exists(OUTPUT_DB):
        os.remove(OUTPUT_DB)

    con = duckdb.connect(OUTPUT_DB)

    # Install and load sqlite extension
    con.execute("INSTALL sqlite; LOAD sqlite;")

    print(f"Importing projects from {SOURCE_DB}...")
    con.execute(f"""
        CREATE TABLE projects AS
        SELECT
            queue_id, region, name, developer, developer_canonical, parent_company,
            capacity_mw, type_std, status_std, state, county, poi,
            queue_date_std, cod_std
        FROM sqlite_scan('{SOURCE_DB}', 'projects')
        WHERE developer_canonical IS NOT NULL AND developer_canonical != ''
    """)
    proj_count = con.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    print(f"  Imported {proj_count} projects with developer data")

    # Import registry if available
    if os.path.exists(REGISTRY_CSV):
        print(f"Importing developer registry from {REGISTRY_CSV}...")
        con.execute(f"""
            CREATE TABLE developer_registry AS
            SELECT * FROM read_csv_auto('{REGISTRY_CSV}')
        """)
        reg_count = con.execute("SELECT COUNT(*) FROM developer_registry").fetchone()[0]
        print(f"  Imported {reg_count} registry entries")

    # Build developers table with pre-computed metrics
    print("Computing developer metrics...")
    con.execute("""
        CREATE TABLE developers AS
        WITH base AS (
            SELECT
                developer_canonical AS name,
                MAX(parent_company) AS parent_company,
                COUNT(*) AS total_projects,
                COUNT(*) FILTER (WHERE status_std = 'Operational') AS operational,
                COUNT(*) FILTER (WHERE status_std = 'Withdrawn') AS withdrawn,
                COUNT(*) FILTER (WHERE status_std = 'Active') AS active,
                COUNT(*) FILTER (WHERE status_std = 'Under Construction') AS under_construction,
                COUNT(*) FILTER (WHERE status_std = 'Suspended') AS suspended,
                STRING_AGG(DISTINCT region, ', ' ORDER BY region) AS regions,
                COUNT(DISTINCT region) AS num_regions,
                STRING_AGG(DISTINCT type_std, ', ' ORDER BY type_std) FILTER (WHERE type_std IS NOT NULL) AS fuel_types,
                COUNT(DISTINCT type_std) FILTER (WHERE type_std IS NOT NULL) AS num_fuel_types,
                STRING_AGG(DISTINCT state, ', ' ORDER BY state) FILTER (WHERE state IS NOT NULL) AS states,
                COALESCE(SUM(capacity_mw), 0) AS total_capacity_mw,
                COALESCE(SUM(capacity_mw) FILTER (WHERE status_std = 'Operational'), 0) AS operational_capacity_mw,
                MIN(queue_date_std) AS first_project_date,
                MAX(queue_date_std) AS latest_project_date,
                ROUND(COALESCE(AVG(capacity_mw), 0), 2) AS avg_capacity_mw,
                -- Timeline: avg days from queue_date_std to cod_std for operational projects
                AVG(
                    DATEDIFF('day', TRY_CAST(queue_date_std AS DATE), TRY_CAST(cod_std AS DATE))
                ) FILTER (
                    WHERE status_std = 'Operational'
                    AND TRY_CAST(queue_date_std AS DATE) IS NOT NULL
                    AND TRY_CAST(cod_std AS DATE) IS NOT NULL
                    AND TRY_CAST(cod_std AS DATE) > TRY_CAST(queue_date_std AS DATE)
                ) AS avg_timeline_days,
                -- Years since first project
                DATEDIFF('day', TRY_CAST(MIN(queue_date_std) AS DATE), CURRENT_DATE) / 365.25 AS years_since_first
            FROM projects
            GROUP BY developer_canonical
        )
        SELECT
            base.*,
            -- Completion rate
            CASE WHEN (operational + withdrawn) > 0
                THEN ROUND(CAST(operational AS DOUBLE) / (operational + withdrawn), 4)
                ELSE NULL
            END AS completion_rate,
            -- Placeholder score columns (computed below)
            NULL::DOUBLE AS score,
            NULL::DOUBLE AS completion_rate_score,
            NULL::DOUBLE AS timeline_score,
            NULL::DOUBLE AS volume_score,
            NULL::DOUBLE AS breadth_score,
            NULL::DOUBLE AS diversity_score,
            NULL::DOUBLE AS pipeline_score,
            NULL::DOUBLE AS depth_score
        FROM base
    """)

    dev_count = con.execute("SELECT COUNT(*) FROM developers").fetchone()[0]
    print(f"  Created {dev_count} developer records")

    # Now compute scores using Python scoring engine
    from app.scoring import compute_score, ScoringInput

    rows = con.execute("""
        SELECT name, operational, withdrawn, total_projects, avg_timeline_days,
               num_regions, num_fuel_types, active, years_since_first
        FROM developers
    """).fetchall()

    scored = 0
    for row in rows:
        name, operational, withdrawn, total, avg_days, regions, types, active, years = row
        inp = ScoringInput(
            operational=operational or 0,
            withdrawn=withdrawn or 0,
            total_projects=total or 0,
            avg_timeline_days=avg_days,
            num_regions=regions or 0,
            num_fuel_types=types or 0,
            active_projects=active or 0,
            years_since_first=years or 0,
        )
        result = compute_score(inp)
        if result:
            con.execute("""
                UPDATE developers SET
                    score = ?, completion_rate_score = ?, timeline_score = ?,
                    volume_score = ?, breadth_score = ?, diversity_score = ?,
                    pipeline_score = ?, depth_score = ?
                WHERE name = ?
            """, [
                result["score"], result["completion_rate_score"],
                result["timeline_score"], result["volume_score"],
                result["breadth_score"], result["diversity_score"],
                result["pipeline_score"], result["depth_score"],
                name,
            ])
            scored += 1

    print(f"  Scored {scored} developers (5+ resolved outcomes)")

    # Create indexes
    con.execute("CREATE INDEX idx_dev_name ON developers(name)")
    con.execute("CREATE INDEX idx_dev_score ON developers(score)")
    con.execute("CREATE INDEX idx_proj_dev ON projects(developer_canonical)")

    con.close()
    print(f"\nDone! Database written to {OUTPUT_DB}")


if __name__ == "__main__":
    main()
