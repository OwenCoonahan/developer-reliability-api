# Data Sources for Developer Reliability Enrichment

## Currently Used

### ISO Interconnection Queues (Primary Source)
- **What:** Project-level data from 9 US ISOs/regions (CAISO, ERCOT, ISO-NE, MISO, NYISO, PJM, SPP, Southeast, West)
- **Coverage:** 35,000+ projects, 5,600+ unique developers
- **Fields:** Developer name, project status, capacity, fuel type, queue date, COD, location
- **Source DB:** `queue.db` from queue-analysis-project

---

## Enrichment Sources (For Future Integration)

### 1. EIA Form 860 (Electric Generator Data)
- **URL:** https://www.eia.gov/electricity/data/eia860/
- **What:** Annual survey of all US electric generators ≥1 MW. Contains owner/operator info, plant characteristics, location, fuel type, capacity, planned additions/retirements.
- **Key tables:** Generator (3_1_Generator), Plant (2___Plant), Owner (4___Owner)
- **Developer relevance:** Maps generators to owners — cross-reference with queue developers to verify operational status and get additional detail.
- **Format:** Excel/CSV files, updated annually (~March for prior year data)
- **API:** EIA Open Data API v2: `https://api.eia.gov/v2/electricity/facility-fuel/data/`
- **Note:** This is likely what Owen referred to as "e-something-801" — EIA-860 is the primary form for generator-level data.

### 2. EIA Form 861 (Electric Sales/Revenue)
- **URL:** https://www.eia.gov/electricity/data/eia861/
- **What:** Annual data on electricity sales, revenue, customer counts by utility.
- **Developer relevance:** Limited — more useful for utility-scale context than developer scoring.

### 3. FERC eLibrary / eQR (Electric Quarterly Reports)
- **URL:** https://elibrary.ferc.gov/ and https://www.ferc.gov/industries-data/electric/power-sales-and-markets/electric-quarterly-reports-eqr
- **What:** eLibrary has all FERC filings (interconnection agreements, rate cases). eQR has wholesale electricity contract data.
- **Developer relevance:**
  - Interconnection Service Agreements (ISAs) confirm project progress
  - Power Purchase Agreements (PPAs) filed here
  - Can track developer's regulatory history
- **Parsing:** Full-text search via eLibrary; eQR data downloadable as CSV
- **Note:** "eQR" may also be what Owen meant by "e-something" — Electric Quarterly Reports at FERC.

### 4. SEC EDGAR (Public Company Filings)
- **URL:** https://www.sec.gov/cgi-bin/browse-edgar
- **Full-text search:** https://efts.sec.gov/LATEST/search-index?q=
- **What:** 10-K, 10-Q, 8-K filings for public companies
- **Developer relevance:** For publicly traded developers (NextEra, AES, Invenergy parent, etc.):
  - Pipeline disclosures in 10-K
  - Project completion updates
  - Financial health indicators
  - M&A activity affecting developer identity
- **API:** EDGAR full-text search API: `https://efts.sec.gov/LATEST/search-index?q={query}&dateRange=custom&startdt=2020-01-01`

### 5. State-Level Interconnection Data
Not all projects go through ISO queues. State-specific sources:

| State | Source | URL |
|-------|--------|-----|
| Texas (non-ERCOT) | PUCT filings | https://www.puc.texas.gov/ |
| California | CPUC interconnection | https://www.cpuc.ca.gov/industries-and-topics/electrical-energy/electric-power-procurement/rps/rps-proceeding |
| New York | NYSERDA large-scale | https://www.nyserda.ny.gov/All-Programs/Large-Scale-Renewables |
| All states | DSIRE (incentives database) | https://www.dsireusa.org/ |
| Various | Utility-specific queue data | (varies by utility) |

### 6. EPA FLIGHT (Facility Level GHG Tracking)
- **URL:** https://ghgdata.epa.gov/ghgp/
- **What:** GHG emissions data by facility
- **Developer relevance:** Can cross-reference operational plants for emissions data — useful for ESG scoring extension.

### 7. LBNL Queued Up Dataset
- **URL:** https://emp.lbl.gov/queues
- **What:** Lawrence Berkeley National Lab maintains a cleaned/analyzed version of ISO queue data
- **Developer relevance:** Excellent cross-reference; they publish annual reports on queue trends, completion rates by technology.
- **Note:** Good validation source for our scoring methodology.

### 8. S&P Global / Platts (Commercial)
- **URL:** https://www.spglobal.com/commodityinsights/
- **What:** Commercial database of power plant ownership, transactions
- **Developer relevance:** Most comprehensive but expensive ($$$). Useful for parent company mapping.

---

## Integration Priority

1. **EIA-860** — Highest value, free, structured data, validates operational status
2. **FERC eQR** — PPA and wholesale contract data, confirms commercial viability  
3. **LBNL Queued Up** — Cross-validation of our methodology
4. **SEC EDGAR** — For public company developers (financial health scoring)
5. **State-level data** — Fill gaps for non-ISO projects

## API Keys Needed
- EIA API: Free, register at https://www.eia.gov/opendata/register.php
- EDGAR: No key needed (rate-limited to 10 req/sec with User-Agent header)
- FERC eQR: Bulk download, no key needed
