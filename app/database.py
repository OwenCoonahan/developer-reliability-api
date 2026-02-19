from typing import Optional, Tuple, List
import duckdb
from contextlib import contextmanager
from app.config import get_settings

_con = None


def get_connection() -> duckdb.DuckDBPyConnection:
    global _con
    if _con is None:
        _con = duckdb.connect(get_settings().database_path, read_only=True)
    return _con


@contextmanager
def cursor():
    con = get_connection()
    try:
        yield con
    finally:
        pass  # read-only, no commit needed


def query_developers(
    search: Optional[str] = None,
    region: Optional[str] = None,
    fuel_type: Optional[str] = None,
    min_projects: int = 1,
    sort_by: str = "score",
    page: int = 1,
    per_page: int = 25,
) -> Tuple[List[dict], int]:
    con = get_connection()
    where = ["d.total_projects >= ?"]
    params: list = [min_projects]

    if search:
        where.append("d.name ILIKE ?")
        params.append(f"%{search}%")
    if region:
        where.append("d.regions ILIKE ?")
        params.append(f"%{region}%")
    if fuel_type:
        where.append("d.fuel_types ILIKE ?")
        params.append(f"%{fuel_type}%")

    where_clause = " AND ".join(where)

    # Valid sort columns
    sort_map = {
        "score": "d.score DESC NULLS LAST",
        "name": "d.name ASC",
        "total_projects": "d.total_projects DESC",
        "operational": "d.operational DESC",
        "completion_rate": "d.completion_rate DESC NULLS LAST",
    }
    order = sort_map.get(sort_by, sort_map["score"])

    count_sql = f"SELECT COUNT(*) FROM developers d WHERE {where_clause}"
    total = con.execute(count_sql, params).fetchone()[0]

    offset = (page - 1) * per_page
    sql = f"""
        SELECT d.name, d.parent_company, d.score, d.total_projects,
               d.operational, d.withdrawn, d.active, d.regions, d.fuel_types
        FROM developers d
        WHERE {where_clause}
        ORDER BY {order}
        LIMIT ? OFFSET ?
    """
    rows = con.execute(sql, params + [per_page, offset]).fetchall()

    results = []
    for r in rows:
        results.append({
            "name": r[0],
            "parent_company": r[1],
            "score": r[2],
            "total_projects": r[3],
            "operational": r[4],
            "withdrawn": r[5],
            "active": r[6],
            "regions": [x.strip() for x in (r[7] or "").split(",") if x.strip()],
            "fuel_types": [x.strip() for x in (r[8] or "").split(",") if x.strip()],
        })
    return results, total


def get_developer(name: str) -> Optional[dict]:
    con = get_connection()
    row = con.execute(
        "SELECT * FROM developers WHERE name ILIKE ? OR name ILIKE ?",
        [name, name.replace("-", " ")],
    ).fetchone()
    if not row:
        return None
    cols = [d[0] for d in con.description]
    return dict(zip(cols, row))


def get_developer_projects(
    name: str, page: int = 1, per_page: int = 50
) -> Tuple[List[dict], int]:
    con = get_connection()
    total = con.execute(
        "SELECT COUNT(*) FROM projects WHERE developer_canonical ILIKE ?", [name]
    ).fetchone()[0]
    if total == 0:
        # Try fuzzy
        total = con.execute(
            "SELECT COUNT(*) FROM projects WHERE developer_canonical ILIKE ?",
            [f"%{name}%"],
        ).fetchone()[0]
        like = f"%{name}%"
    else:
        like = name

    offset = (page - 1) * per_page
    rows = con.execute(
        """SELECT queue_id, region, name, capacity_mw, type_std, status_std,
                  state, county, poi, queue_date_std, cod_std
           FROM projects WHERE developer_canonical ILIKE ?
           ORDER BY queue_date_std DESC NULLS LAST
           LIMIT ? OFFSET ?""",
        [like, per_page, offset],
    ).fetchall()

    results = []
    for r in rows:
        results.append({
            "queue_id": r[0], "region": r[1], "name": r[2],
            "capacity_mw": r[3], "fuel_type": r[4], "status": r[5],
            "state": r[6], "county": r[7], "poi": r[8],
            "queue_date": r[9], "cod": r[10],
        })
    return results, total


def get_rankings(
    sort_by: str = "score", page: int = 1, per_page: int = 25
) -> Tuple[List[dict], int]:
    con = get_connection()
    total = con.execute(
        "SELECT COUNT(*) FROM developers WHERE score IS NOT NULL"
    ).fetchone()[0]

    sort_map = {
        "score": "score DESC",
        "completion_rate": "completion_rate DESC",
        "total_projects": "total_projects DESC",
        "operational": "operational DESC",
    }
    order = sort_map.get(sort_by, "score DESC")
    offset = (page - 1) * per_page

    rows = con.execute(
        f"""SELECT name, parent_company, score, total_projects, operational,
                   completion_rate
            FROM developers WHERE score IS NOT NULL
            ORDER BY {order}
            LIMIT ? OFFSET ?""",
        [per_page, offset],
    ).fetchall()

    results = []
    for i, r in enumerate(rows):
        results.append({
            "rank": offset + i + 1,
            "name": r[0], "parent_company": r[1], "score": r[2],
            "total_projects": r[3], "operational": r[4],
            "completion_rate": r[5] or 0,
        })
    return results, total


def get_stats() -> dict:
    con = get_connection()
    total_dev = con.execute("SELECT COUNT(*) FROM developers").fetchone()[0]
    scored_dev = con.execute("SELECT COUNT(*) FROM developers WHERE score IS NOT NULL").fetchone()[0]
    total_proj = con.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    avg_score = con.execute("SELECT AVG(score) FROM developers WHERE score IS NOT NULL").fetchone()[0]
    median_score = con.execute("SELECT MEDIAN(score) FROM developers WHERE score IS NOT NULL").fetchone()[0]

    regions = con.execute(
        "SELECT region, COUNT(*) c FROM projects GROUP BY region ORDER BY c DESC"
    ).fetchall()
    fuel_types = con.execute(
        "SELECT type_std, COUNT(*) c FROM projects WHERE type_std IS NOT NULL GROUP BY type_std ORDER BY c DESC LIMIT 10"
    ).fetchall()

    # Score distribution in buckets
    buckets = con.execute("""
        SELECT
            CASE
                WHEN score >= 80 THEN 'excellent_80_100'
                WHEN score >= 60 THEN 'good_60_79'
                WHEN score >= 40 THEN 'average_40_59'
                WHEN score >= 20 THEN 'below_avg_20_39'
                ELSE 'poor_0_19'
            END as bucket, COUNT(*)
        FROM developers WHERE score IS NOT NULL
        GROUP BY bucket ORDER BY bucket
    """).fetchall()

    return {
        "total_developers": total_dev,
        "scored_developers": scored_dev,
        "total_projects": total_proj,
        "avg_score": round(avg_score, 1) if avg_score else None,
        "median_score": round(median_score, 1) if median_score else None,
        "top_regions": {r[0]: r[1] for r in regions},
        "top_fuel_types": {r[0]: r[1] for r in fuel_types},
        "score_distribution": {r[0]: r[1] for r in buckets},
    }
