"""Developer Reliability Scoring Engine

Composite score (0-100) with weighted components:
- Completion rate:    30%  (operational / (operational + withdrawn))
- Timeline to COD:    20%  (avg days queue→COD, lower=better, benchmarked)
- Project volume:     15%  (total projects, log-scaled)
- Regional breadth:   10%  (number of ISOs)
- Tech diversity:     10%  (number of fuel types)
- Active pipeline:    10%  (current active projects)
- Track record depth:  5%  (years since first project)

Only developers with 5+ resolved outcomes are scored.
"""

import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class ScoringInput:
    operational: int
    withdrawn: int
    total_projects: int
    avg_timeline_days: Optional[float]  # None if no COD data
    num_regions: int
    num_fuel_types: int
    active_projects: int
    years_since_first: float


# Benchmarks (calibrated from typical ISO queue data)
TIMELINE_EXCELLENT = 365      # 1 year = perfect
TIMELINE_POOR = 365 * 6       # 6 years = 0 score
VOLUME_CAP = 200              # log-scaled, ~200 projects = near max
REGIONS_MAX = 9               # 9 ISOs in the dataset
FUEL_TYPES_MAX = 8            # reasonable max diversity
PIPELINE_CAP = 50             # 50+ active = max
DEPTH_MAX = 20                # 20+ years = max


def score_completion_rate(operational: int, withdrawn: int) -> float:
    resolved = operational + withdrawn
    if resolved == 0:
        return 0.0
    return (operational / resolved) * 100


def score_timeline(avg_days: Optional[float]) -> float:
    if avg_days is None or avg_days <= 0:
        return 50.0  # neutral if no data
    if avg_days <= TIMELINE_EXCELLENT:
        return 100.0
    if avg_days >= TIMELINE_POOR:
        return 0.0
    # Linear interpolation
    return 100 * (1 - (avg_days - TIMELINE_EXCELLENT) / (TIMELINE_POOR - TIMELINE_EXCELLENT))


def score_volume(total: int) -> float:
    if total <= 0:
        return 0.0
    # Log scale: log(total)/log(cap) * 100, capped at 100
    return min(100.0, (math.log1p(total) / math.log1p(VOLUME_CAP)) * 100)


def score_breadth(num_regions: int) -> float:
    return min(100.0, (num_regions / REGIONS_MAX) * 100)


def score_diversity(num_types: int) -> float:
    return min(100.0, (num_types / FUEL_TYPES_MAX) * 100)


def score_pipeline(active: int) -> float:
    if active <= 0:
        return 0.0
    return min(100.0, (math.log1p(active) / math.log1p(PIPELINE_CAP)) * 100)


def score_depth(years: float) -> float:
    if years <= 0:
        return 0.0
    return min(100.0, (years / DEPTH_MAX) * 100)


WEIGHTS = {
    "completion": 0.30,
    "timeline": 0.20,
    "volume": 0.15,
    "breadth": 0.10,
    "diversity": 0.10,
    "pipeline": 0.10,
    "depth": 0.05,
}


def compute_score(inp: ScoringInput) -> Optional[dict]:
    """Returns score dict or None if developer doesn't qualify (< 5 resolved)."""
    resolved = inp.operational + inp.withdrawn
    if resolved < 5:
        return None

    completion = score_completion_rate(inp.operational, inp.withdrawn)
    timeline = score_timeline(inp.avg_timeline_days)
    volume = score_volume(inp.total_projects)
    breadth = score_breadth(inp.num_regions)
    diversity = score_diversity(inp.num_fuel_types)
    pipeline = score_pipeline(inp.active_projects)
    depth = score_depth(inp.years_since_first)

    composite = (
        WEIGHTS["completion"] * completion
        + WEIGHTS["timeline"] * timeline
        + WEIGHTS["volume"] * volume
        + WEIGHTS["breadth"] * breadth
        + WEIGHTS["diversity"] * diversity
        + WEIGHTS["pipeline"] * pipeline
        + WEIGHTS["depth"] * depth
    )

    return {
        "score": round(composite, 1),
        "completion_rate": round(inp.operational / resolved, 4) if resolved else 0,
        "completion_rate_score": round(completion, 1),
        "avg_timeline_days": round(inp.avg_timeline_days, 1) if inp.avg_timeline_days else None,
        "timeline_score": round(timeline, 1),
        "project_volume": inp.total_projects,
        "volume_score": round(volume, 1),
        "regional_breadth": inp.num_regions,
        "breadth_score": round(breadth, 1),
        "tech_diversity": inp.num_fuel_types,
        "diversity_score": round(diversity, 1),
        "active_pipeline": inp.active_projects,
        "pipeline_score": round(pipeline, 1),
        "track_record_years": round(inp.years_since_first, 1),
        "depth_score": round(depth, 1),
    }
