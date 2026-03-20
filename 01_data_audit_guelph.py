## =============================================================================
# Guelph Municipal GIS Pipeline
# Script 01 — Data Audit and Quality Report
#
# Author  : Ibrahim Mirza
# Date    : 2026
#
# Description:
#   Audits all layers in the Guelph File Geodatabase before any processing.
#   Reports coordinate systems, feature counts, field inventories, and
#   data quality flags. Identifies layers not meeting the NAD83 CSRS
#   standard required for municipal GIS operations in Ontario.
#
#   Designed to mirror the data validation and verification workflows
#   performed daily in a municipal GIS environment, including QA checks
#   relevant to ERP spatial data preparation.
#
# Data:
#   - Street_Centrelines (City of Guelph Open Data) — 3,579 segments
#   - Bus_Stops (City of Guelph Open Data) — 644 stops
# =============================================================================

import arcpy
import os
import csv
import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = r"C:\Users\mirza\Desktop\RESUMES AND COVER LETTERS\PROJECTS\guelph_gis_data_pipeline\Guelph_Municipal_GIS_Pipeline"
GDB_PATH     = r"C:\Users\mirza\Desktop\RESUMES AND COVER LETTERS\PROJECTS\guelph_gis_data_pipeline\Guelph_Municipal_GIS_Pipeline\Guelph_Municipal_GIS_Pipeline.gdb"
REPORT_CSV   = os.path.join(PROJECT_ROOT, "outputs", "01_audit_report.csv")


# ---------------------------------------------------------------------------
# Audit all layers — CRS, geometry, feature count, null checks
# ---------------------------------------------------------------------------

def audit_layers(gdb_path):
    """
    Loops through every feature class in the GDB and reports:
      - Coordinate system name and type
      - Whether it meets the NAD83 CSRS standard
      - Feature count
      - Extent (bounding box)

    NAD_1983_UTM_Zone_17N and NAD_1983_CSRS_UTM_Zone_17N are not the same.
    The CSRS version uses the Canadian Spatial Reference System datum
    maintained by NRCan. The difference in Ontario is ~1 metre — acceptable
    for web display, not acceptable for municipal infrastructure records.
    """
    print(f"\n{'='*60}")
    print(f"  Guelph Municipal GIS Pipeline — 01 Data Audit")
    print(f"  Run at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    arcpy.env.workspace = gdb_path
    feature_classes     = arcpy.ListFeatureClasses()

    if not feature_classes:
        print("  No feature classes found. Check GDB_PATH.")
        return []

    print(f"  GDB: {gdb_path}")
    print(f"  Layers found: {len(feature_classes)}\n")

    flagged = []

    for fc in feature_classes:
        path  = os.path.join(gdb_path, fc)
        desc  = arcpy.Describe(path)
        sr    = desc.spatialReference
        ext   = desc.extent
        count = int(arcpy.GetCount_management(path).getOutput(0))

        print(f"  --- {fc} ---")
        print(f"  Geometry  : {desc.shapeType}")
        print(f"  Features  : {count:,}")
        print(f"  CRS       : {sr.name}")
        print(f"  CRS Type  : {sr.type}")
        print(f"  Extent    : X({round(ext.XMin,1)} → {round(ext.XMax,1)})  "
              f"Y({round(ext.YMin,1)} → {round(ext.YMax,1)})")

        # NAD83 (non-CSRS) is the US standard — Canadian municipal data
        # should be in NAD83 CSRS for correct datum alignment
        if "CSRS" in sr.name:
            print(f"  CRS Status: OK — NAD83 CSRS confirmed")
        elif "NAD_1983" in sr.name and "CSRS" not in sr.name:
            print(f"  CRS Status: FLAG — NAD83 (non-CSRS) detected")
            print(f"             Will reproject to CSRS in 03_reproject_mtm.py")
            flagged.append(fc)
        else:
            print(f"  CRS Status: FLAG — Unknown CRS, review required")
            flagged.append(fc)

        print()

    print(f"  {len(flagged)} layer(s) flagged for reprojection.")
    return flagged


# ---------------------------------------------------------------------------
# Field inventory — document all fields for metadata purposes
# ---------------------------------------------------------------------------

def field_inventory(gdb_path):
    """
    Prints and saves a complete field listing for every layer.
    Output saved to CSV as a metadata documentation artifact —
    directly supporting corporate data governance requirements.
    """
    print("--- Field Inventory ---\n")

    arcpy.env.workspace = gdb_path
    feature_classes = arcpy.ListFeatureClasses() or []

    if not feature_classes:
        print("  No feature classes found.")
        return []
    records = []

    for fc in feature_classes:
        path = os.path.join(gdb_path, fc)
        print(f"  {fc}")
        print(f"  {'Field Name':<30} {'Type':<15} {'Length':<8} {'Required'}")
        print(f"  {'-'*30} {'-'*15} {'-'*8} {'-'*10}")

        for field in arcpy.ListFields(path):
            if field.type not in ("Geometry", "OID"):
                required = "Yes" if field.required else "No"
                print(f"  {field.name:<30} {field.type:<15} {field.length:<8} {required}")
                records.append({
                    "Layer"    : fc,
                    "Field"    : field.name,
                    "Type"     : field.type,
                    "Length"   : field.length,
                    "Required" : required
                })
        print()

    # Save field inventory to CSV
    out_dir = os.path.dirname(REPORT_CSV)
    os.makedirs(out_dir, exist_ok=True)

    with open(REPORT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Layer", "Field", "Type", "Length", "Required"])
        writer.writeheader()
        writer.writerows(records)

    print(f"  Field inventory saved to: {REPORT_CSV}")


# ---------------------------------------------------------------------------
# Null and data gap check — critical for ERP asset data preparation
# ---------------------------------------------------------------------------

def check_data_quality(gdb_path):
    """
    Checks key fields for null values and data gaps.
    Flags records that would cause issues during ERP integration —
    assets without IDs, road segments without classification, etc.

    This mirrors the data verification step required before spatial
    data can be loaded into an ERP asset management system.
    """
    print("--- Data Quality Check ---\n")

    # Roads — check critical fields for ERP asset alignment
    roads_path  = os.path.join(gdb_path, "Street_Centrelines")
    roads_checks = {
        "ASSETID"   : "Asset ID — required for ERP record matching",
        "ROADCLASS" : "Road classification — required for routing and maintenance",
        "SPEED"     : "Speed limit — required for traffic management",
        "STATUS"    : "Road status — required for operational records",
        "INSTALLYEA": "Install year — required for lifecycle/risk analysis",
        "SURFACEYEA": "Surface year — required for resurfacing planning",
    }

    print("  Street_Centrelines — ERP Asset Readiness Check:")
    print(f"  {'Field':<15} {'Null/Zero Count':>16} {'Total':>8} {'% Complete':>12}  Note")
    print(f"  {'-'*15} {'-'*16} {'-'*8} {'-'*12}  {'-'*35}")

    total_roads = int(arcpy.GetCount_management(roads_path).getOutput(0))

    for field, note in roads_checks.items():
        null_count = 0
        with arcpy.da.SearchCursor(roads_path, [field]) as cursor:
            for row in cursor:
                val = row[0]
                if val is None or val == "" or val == 0:
                    null_count += 1
        pct = round((1 - null_count / total_roads) * 100, 1)
        status = "OK" if null_count == 0 else f"{null_count:,} gaps"
        print(f"  {field:<15} {status:>16} {total_roads:>8,} {str(pct)+'%':>12}  {note}")

    print()

    # Bus Stops — check for service fields
    stops_path   = os.path.join(gdb_path, "Bus_Stops")
    stop_checks  = {
        "StopId"    : "Stop ID — primary key for transit system matching",
        "StopName"  : "Stop name — required for web map display",
        "Conv"      : "Connections — transit service attribute",
    }

    print("  Bus_Stops — Transit Data Quality Check:")
    print(f"  {'Field':<15} {'Null/Zero Count':>16} {'Total':>8} {'% Complete':>12}  Note")
    print(f"  {'-'*15} {'-'*16} {'-'*8} {'-'*12}  {'-'*30}")

    total_stops = int(arcpy.GetCount_management(stops_path).getOutput(0))

    for field, note in stop_checks.items():
        null_count = 0
        with arcpy.da.SearchCursor(stops_path, [field]) as cursor:
            for row in cursor:
                val = row[0]
                if val is None or val == "":
                    null_count += 1
        pct = round((1 - null_count / total_stops) * 100, 1)
        status = "OK" if null_count == 0 else f"{null_count:,} gaps"
        print(f"  {field:<15} {status:>16} {total_stops:>8,} {str(pct)+'%':>12}  {note}")

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
arcpy.env.workspace = GDB_PATH 
if __name__ == "__main__":

    arcpy.env.workspace       = GDB_PATH
    arcpy.env.overwriteOutput = True

    flagged = audit_layers(GDB_PATH)
    field_inventory(GDB_PATH)
    check_data_quality(GDB_PATH)

    print(f"\n{'='*60}")
    print(f"  Audit complete — ready for 02_asset_preparation.py")
    print(f"{'='*60}\n")

