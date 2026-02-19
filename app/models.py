from pydantic import BaseModel
from typing import Optional


class PaginationMeta(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int


class ScoreBreakdown(BaseModel):
    completion_rate: float
    completion_rate_score: float
    avg_timeline_days: Optional[float]
    timeline_score: float
    project_volume: int
    volume_score: float
    regional_breadth: int
    breadth_score: float
    tech_diversity: int
    diversity_score: float
    active_pipeline: int
    pipeline_score: float
    track_record_years: float
    depth_score: float


class DeveloperSummary(BaseModel):
    name: str
    parent_company: Optional[str]
    score: Optional[float]
    total_projects: int
    operational: int
    withdrawn: int
    active: int
    regions: list[str]
    fuel_types: list[str]


class DeveloperDetail(BaseModel):
    name: str
    parent_company: Optional[str]
    score: Optional[float]
    score_breakdown: Optional[ScoreBreakdown]
    total_projects: int
    operational: int
    withdrawn: int
    active: int
    under_construction: int
    suspended: int
    regions: list[str]
    fuel_types: list[str]
    states: list[str]
    total_capacity_mw: float
    operational_capacity_mw: float
    first_project_date: Optional[str]
    latest_project_date: Optional[str]
    avg_capacity_mw: float


class ProjectRecord(BaseModel):
    queue_id: str
    region: str
    name: Optional[str]
    capacity_mw: Optional[float]
    fuel_type: Optional[str]
    status: Optional[str]
    state: Optional[str]
    county: Optional[str]
    poi: Optional[str]
    queue_date: Optional[str]
    cod: Optional[str]


class DeveloperListResponse(BaseModel):
    data: list[DeveloperSummary]
    meta: PaginationMeta


class DeveloperDetailResponse(BaseModel):
    data: DeveloperDetail


class ProjectListResponse(BaseModel):
    data: list[ProjectRecord]
    meta: PaginationMeta


class RankingEntry(BaseModel):
    rank: int
    name: str
    parent_company: Optional[str]
    score: float
    total_projects: int
    operational: int
    completion_rate: float


class RankingsResponse(BaseModel):
    data: list[RankingEntry]
    meta: PaginationMeta


class CompareResponse(BaseModel):
    data: list[DeveloperDetail]


class StatsResponse(BaseModel):
    total_developers: int
    scored_developers: int
    total_projects: int
    avg_score: Optional[float]
    median_score: Optional[float]
    top_regions: dict[str, int]
    top_fuel_types: dict[str, int]
    score_distribution: dict[str, int]
