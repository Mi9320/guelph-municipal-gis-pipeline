# Guelph Municipal GIS Pipeline

An ArcPy automation pipeline built on City of Guelph Open Data, demonstrating
the data validation, asset preparation, coordinate system management, and 
metadata documentation workflows used in municipal GIS operations.

Built as a targeted portfolio project for the Junior GIS Analyst role at
the City of Guelph (Job ID 2026-4173).

**Author:** Ibrahim Mirza  
**GitHub:** github.com/Mi9320/guelph-municipal-gis-pipeline  
**Data Source:** [City of Guelph Open Data Portal](https://geodatahub-cityofguelph.opendata.arcgis.com)

---

## Project Overview

Municipal GIS data arrives from multiple sources in varying states of quality.
Before any dataset can be used for infrastructure planning, web mapping, or
ERP integration, it must be validated, cleaned, and documented.

This pipeline automates that preparation workflow on two City of Guelph datasets:
- **Street Centrelines** — 3,579 road segments with classification, speed, and asset attributes
- **Bus Stops** — 644 Guelph Transit stop locations with service schedule attributes

---

## Scripts

### 01_data_audit_guelph.py — Data Audit and Quality Report

Validates all layers before processing. Reports coordinate systems, feature
counts, and field inventories. Runs null checks on fields critical for ERP
asset matching — ASSETID, ROADCLASS, SPEED, SURFACEYEA — and flags records
that would fail ERP integration due to missing attributes.

**Key output:** Printed audit report + field inventory CSV

**Demonstrates:** Data validation and verification duties from the job posting

---

### 02_asset_preparation_guelph.py — Asset Preparation for ERP Integration

Prepares road and transit data for ERP system alignment by adding three
derived fields to the road centreline layer:

- `ASSET_STATUS` — ERP readiness flag: "Verified", "Needs Review", "Data Gap"
- `MAINTENANCE_PRIORITY` — derived from road class and surface age (1=Immediate, 2=Near-term, 3=Routine)
- `ROAD_CATEGORY` — simplified 4-class system for ERP work order labels

Classifies bus stops by service type for web mapping and transit system use.

**Demonstrates:** ERP data preparation, UpdateCursor operations, asset classification

---

### 03_reproject_mtm_guelph.py — Reprojection to NAD83 CSRS MTM Zone 10

Reprojects both datasets from NAD83 UTM Zone 17N to NAD83 CSRS MTM Zone 10
(EPSG: 2952) — the correct regional standard for Guelph and the Wellington
County area.

**Why MTM Zone 10:**  
Modified Transverse Mercator uses narrower 3-degree zones (vs UTM's 6-degree),
reducing scale distortion for municipal-scale work in Ontario. Combined with
the CSRS datum (vs standard NAD83), this ensures sub-metre positional accuracy
required for infrastructure records.

**Demonstrates:** Ontario coordinate system knowledge, datum transformation,
arcpy.Project_management

---

### 04_metadata_report_guelph.py — Metadata Documentation

Generates standardized metadata records for all layers — field-level detail
and layer-level summary — in CSV format. Documents CRS, feature counts, field
definitions, data source, and processing history.

**Demonstrates:** Metadata creation duties, data governance documentation

---

## Skills Demonstrated

| Skill | Where Used |
|---|---|
| `arcpy.ListFeatureClasses` + `Describe` | Layer audit and CRS validation |
| `arcpy.da.SearchCursor` | Null checks, data quality reporting |
| `arcpy.da.UpdateCursor` | Asset status classification, ERP field preparation |
| `arcpy.Project_management` | NAD83 → NAD83 CSRS MTM Zone 10 reprojection |
| `geo_transformation` parameter | Correct datum shift for Ontario |
| `csv.DictWriter` | Metadata and audit report export |
| SQL-style data classification | Maintenance priority waterfall logic |
| ERP asset preparation concepts | ASSETID validation, data gap flagging |
| Metadata creation | Standardized layer and field documentation |

---

## Setup

1. Download Street Centrelines and Bus Stops shapefiles from
   [geodatahub-cityofguelph.opendata.arcgis.com](https://geodatahub-cityofguelph.opendata.arcgis.com)
2. Import both shapefiles into a File Geodatabase: `Guelph_Pipeline.gdb`
3. Update `PROJECT_ROOT` in each script to match your local path
4. Run scripts in order: 01 → 02 → 03 → 04

**Requirements:** ArcGIS Pro 3.x, Python 3.x

---

## Output Structure

```
Guelph/
    Guelph_Pipeline.gdb
        Street_Centrelines           (original — NAD83 UTM Zone 17N)
        Street_Centrelines_MTM10     (reprojected — NAD83 CSRS MTM Zone 10)
        Bus_Stops                    (original — NAD83 UTM Zone 17N)
        Bus_Stops_MTM10              (reprojected — NAD83 CSRS MTM Zone 10)
    outputs/
        01_audit_report.csv          (field inventory)
        guelph_metadata_report.csv   (field-level metadata)
        guelph_layer_summary.csv     (layer-level metadata for data catalogue)
```

---

## Related Project

[Toronto Urban Data Pipeline](https://github.com/Mi9320/toronto-urban-data-pipeline) —
a larger 4-script pipeline processing 64,659 road segments and 25 ward boundaries
from City of Toronto Open Data.
