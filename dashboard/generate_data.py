#!/usr/bin/env python3
"""Generate static JSON data for the Developer Reliability Score dashboard."""

import json
import duckdb
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'developers.duckdb')
OUT_PATH = os.path.join(os.path.dirname(__file__), 'data.json')

def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    # Get top 500 developers by score
    devs = con.execute("""
        SELECT name, parent_company, total_projects, operational, withdrawn, active,
               under_construction, suspended, regions, num_regions, fuel_types, num_fuel_types,
               states, total_capacity_mw, operational_capacity_mw, first_project_date,
               latest_project_date, avg_capacity_mw, avg_timeline_days, years_since_first,
               completion_rate, score, completion_rate_score, timeline_score, volume_score,
               breadth_score, diversity_score, pipeline_score, depth_score
        FROM developers
        WHERE score IS NOT NULL
        ORDER BY score DESC
        LIMIT 500
    """).fetchall()

    dev_cols = ['name', 'parent_company', 'total_projects', 'operational', 'withdrawn', 'active',
                'under_construction', 'suspended', 'regions', 'num_regions', 'fuel_types', 'num_fuel_types',
                'states', 'total_capacity_mw', 'operational_capacity_mw', 'first_project_date',
                'latest_project_date', 'avg_capacity_mw', 'avg_timeline_days', 'years_since_first',
                'completion_rate', 'score', 'completion_rate_score', 'timeline_score', 'volume_score',
                'breadth_score', 'diversity_score', 'pipeline_score', 'depth_score']

    developers = []
    dev_names = set()
    for row in devs:
        d = dict(zip(dev_cols, row))
        # Round floats
        for k, v in d.items():
            if isinstance(v, float):
                d[k] = round(v, 4)
        developers.append(d)
        dev_names.add(d['name'])

    # Get projects for these developers
    placeholders = ','.join(['?'] * len(dev_names))
    projects = con.execute(f"""
        SELECT queue_id, region, name, developer_canonical, capacity_mw, type_std,
               status_std, state, county, queue_date_std, cod_std
        FROM projects
        WHERE developer_canonical IN ({placeholders})
        ORDER BY queue_date_std DESC
    """, list(dev_names)).fetchall()

    proj_cols = ['queue_id', 'region', 'name', 'developer', 'capacity_mw', 'type',
                 'status', 'state', 'county', 'queue_date', 'cod']

    # Group projects by developer
    dev_projects = {}
    for row in projects:
        p = dict(zip(proj_cols, row))
        if isinstance(p.get('capacity_mw'), float):
            p['capacity_mw'] = round(p['capacity_mw'], 2)
        dev = p.pop('developer')
        dev_projects.setdefault(dev, []).append(p)

    # Aggregate stats
    stats = con.execute("""
        SELECT count(*) as total_devs,
               sum(total_projects) as total_projects,
               sum(total_capacity_mw) as total_capacity
        FROM developers WHERE score IS NOT NULL
    """).fetchone()

    # Market averages for benchmarking
    averages = con.execute("""
        SELECT avg(completion_rate) as avg_completion,
               avg(avg_timeline_days) as avg_timeline,
               avg(score) as avg_score,
               avg(total_capacity_mw) as avg_capacity
        FROM developers WHERE score IS NOT NULL
    """).fetchone()

    # Region averages
    region_avgs = {}
    for dev in developers:
        for region in (dev['regions'] or '').split(', '):
            region = region.strip()
            if region:
                region_avgs.setdefault(region, {'scores': [], 'completion': [], 'timeline': []})
                region_avgs[region]['scores'].append(dev['score'] or 0)
                region_avgs[region]['completion'].append(dev['completion_rate'] or 0)
                if dev['avg_timeline_days']:
                    region_avgs[region]['timeline'].append(dev['avg_timeline_days'])

    region_benchmarks = {}
    for region, vals in region_avgs.items():
        region_benchmarks[region] = {
            'avg_score': round(sum(vals['scores']) / len(vals['scores']), 2) if vals['scores'] else 0,
            'avg_completion': round(sum(vals['completion']) / len(vals['completion']), 4) if vals['completion'] else 0,
            'avg_timeline': round(sum(vals['timeline']) / len(vals['timeline']), 1) if vals['timeline'] else 0,
            'count': len(vals['scores'])
        }

    output = {
        'developers': developers,
        'projects': dev_projects,
        'stats': {
            'total_developers': stats[0],
            'total_projects': stats[1],
            'total_capacity_gw': round(stats[2] / 1000, 1) if stats[2] else 0,
            'last_updated': '2026-02-19'
        },
        'market_averages': {
            'completion_rate': round(averages[0], 4) if averages[0] else 0,
            'avg_timeline_days': round(averages[1], 1) if averages[1] else 0,
            'avg_score': round(averages[2], 1) if averages[2] else 0,
            'avg_capacity_mw': round(averages[3], 1) if averages[3] else 0
        },
        'region_benchmarks': region_benchmarks
    }

    with open(OUT_PATH, 'w') as f:
        json.dump(output, f, separators=(',', ':'))

    print(f"Generated {OUT_PATH}")
    print(f"  {len(developers)} developers, {len(projects)} projects")
    print(f"  File size: {os.path.getsize(OUT_PATH) / 1024 / 1024:.1f} MB")

    con.close()

if __name__ == '__main__':
    main()
