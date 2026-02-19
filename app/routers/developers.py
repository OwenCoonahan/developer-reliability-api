import math
from fastapi import APIRouter, Depends, HTTPException, Query
from app.auth import verify_api_key
from app.database import (
    query_developers, get_developer, get_developer_projects,
    get_rankings, get_stats,
)
from app.models import (
    DeveloperListResponse, DeveloperDetailResponse, ProjectListResponse,
    RankingsResponse, CompareResponse, StatsResponse,
    PaginationMeta, DeveloperDetail, ScoreBreakdown,
)

router = APIRouter(prefix="/v1", dependencies=[Depends(verify_api_key)])


def make_meta(total: int, page: int, per_page: int) -> PaginationMeta:
    return PaginationMeta(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if per_page else 0,
    )


def developer_to_detail(d: dict) -> DeveloperDetail:
    breakdown = None
    if d.get("score") is not None:
        breakdown = ScoreBreakdown(
            completion_rate=d.get("completion_rate", 0),
            completion_rate_score=d.get("completion_rate_score", 0),
            avg_timeline_days=d.get("avg_timeline_days"),
            timeline_score=d.get("timeline_score", 0),
            project_volume=d.get("total_projects", 0),
            volume_score=d.get("volume_score", 0),
            regional_breadth=d.get("num_regions", 0),
            breadth_score=d.get("breadth_score", 0),
            tech_diversity=d.get("num_fuel_types", 0),
            diversity_score=d.get("diversity_score", 0),
            active_pipeline=d.get("active", 0),
            pipeline_score=d.get("pipeline_score", 0),
            track_record_years=d.get("years_since_first", 0),
            depth_score=d.get("depth_score", 0),
        )
    return DeveloperDetail(
        name=d["name"],
        parent_company=d.get("parent_company"),
        score=d.get("score"),
        score_breakdown=breakdown,
        total_projects=d.get("total_projects", 0),
        operational=d.get("operational", 0),
        withdrawn=d.get("withdrawn", 0),
        active=d.get("active", 0),
        under_construction=d.get("under_construction", 0),
        suspended=d.get("suspended", 0),
        regions=[x.strip() for x in (d.get("regions") or "").split(",") if x.strip()],
        fuel_types=[x.strip() for x in (d.get("fuel_types") or "").split(",") if x.strip()],
        states=[x.strip() for x in (d.get("states") or "").split(",") if x.strip()],
        total_capacity_mw=d.get("total_capacity_mw", 0),
        operational_capacity_mw=d.get("operational_capacity_mw", 0),
        first_project_date=d.get("first_project_date"),
        latest_project_date=d.get("latest_project_date"),
        avg_capacity_mw=d.get("avg_capacity_mw", 0),
    )


@router.get("/developers", response_model=DeveloperListResponse)
async def list_developers(
    search: Optional[str] = None,
    region: Optional[str] = None,
    fuel_type: Optional[str] = None,
    min_projects: int = Query(1, ge=1),
    sort_by: str = "score",
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
):
    data, total = query_developers(search, region, fuel_type, min_projects, sort_by, page, per_page)
    return DeveloperListResponse(data=data, meta=make_meta(total, page, per_page))


@router.get("/developers/rankings", response_model=RankingsResponse)
async def rankings(
    sort_by: str = "score",
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
):
    data, total = get_rankings(sort_by, page, per_page)
    return RankingsResponse(data=data, meta=make_meta(total, page, per_page))


@router.get("/developers/compare", response_model=CompareResponse)
async def compare(names: str = Query(..., description="Comma-separated developer names")):
    name_list = [n.strip() for n in names.split(",") if n.strip()]
    if len(name_list) < 2 or len(name_list) > 10:
        raise HTTPException(400, "Provide 2-10 developer names")
    results = []
    for name in name_list:
        d = get_developer(name)
        if d:
            results.append(developer_to_detail(d))
    if not results:
        raise HTTPException(404, "No matching developers found")
    return CompareResponse(data=results)


@router.get("/developers/{name}", response_model=DeveloperDetailResponse)
async def developer_detail(name: str):
    d = get_developer(name)
    if not d:
        raise HTTPException(404, f"Developer '{name}' not found")
    return DeveloperDetailResponse(data=developer_to_detail(d))


@router.get("/developers/{name}/projects", response_model=ProjectListResponse)
async def developer_projects(
    name: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    data, total = get_developer_projects(name, page, per_page)
    if total == 0:
        raise HTTPException(404, f"No projects found for '{name}'")
    return ProjectListResponse(data=data, meta=make_meta(total, page, per_page))


@router.get("/stats", response_model=StatsResponse)
async def stats():
    return get_stats()
