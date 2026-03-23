# =============================================================================
# Guelph Municipal GIS Pipeline
# Script 04 — Metadata Report Generation
#
# Author  : Ibrahim Mirza
# Date    : 2026
#
# Description:
#   Generates a complete metadata report for all layers in the GDB.
#   Metadata documents the origin, coordinate system, feature counts,
#   field definitions, data quality flags, and processing history of
#   each dataset.
#
#   Metadata creation is a core duty in the City of Guelph GIS Analyst
#   role and a requirement for corporate data governance. This script
#   automates what would otherwise be a manual documentation task,
#   producing a standardized report that can be submitted with any
#   dataset or used for ERP spatial data documentation.
#
#   Outputs:
#     - guelph_metadata_report.csv  : machine-readable field-level metadata
#     - guelph_layer_summary.csv    : layer-level summary for data catalogue
# =============================================================================

import arcpy
import os
import csv
import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = r"C:\your\path\to\Guelph_Municipal_GIS_Pipeline"
GDB_PATH     = os.path.join(PROJECT_ROOT, "Guelph_Municipal_GIS_Pipeline.gdb")
OUTPUT_FOLDER = os.path.join(PROJECT_ROOT, "outputs")

METADATA_CSV  = os.path.join(OUTPUT_FOLDER, "guelph_metadata_report.csv")
SUMMARY_CSV   = os.path.join(OUTPUT_FOLDER, "guelph_layer_summary.csv")

# Data source info for metadata records
DATA_SOURCE   = "City of Guelph Open Data Portal (geodatahub-cityofguelph.opendata.arcgis.com)"
PROCESSED_BY  = "Ibrahim Mirza"
PROCESS_DATE  = datetime.datetime.now().strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Generate field-level metadata
# ---------------------------------------------------------------------------

def generate_field_metadata(gdb_path):
    """
    Produces a complete field-level metadata record for every layer.
    Each row in the output CSV documents one field in one layer —
    the standard format for GIS data catalogues.
    """
    print("--- Generating Field-Level Metadata ---\n")

    arcpy.env.workspace = gdb_path
    feature_classes     = arcpy.ListFeatureClasses()
    records             = []

    for fc in feature_classes:
        path  = os.path.join(gdb_path, fc)
        desc  = arcpy.Describe(path)
        sr    = desc.spatialReference
        count = int(arcpy.GetCount_management(path).getOutput(0))

        for field in arcpy.ListFields(path):
            if field.type in ("Geometry", "OID"):
                continue

            records.append({
                "Layer_Name"       : fc,
                "Geometry_Type"    : desc.shapeType,
                "Feature_Count"    : count,
                "CRS_Name"         : sr.name,
                "CRS_Type"         : sr.type,
                "CRS_WKID"        : sr.factoryCode if sr.factoryCode else "N/A",
                "Field_Name"       : field.name,
                "Field_Type"       : field.type,
                "Field_Length"     : field.length,
                "Field_Alias"      : field.aliasName,
                "Field_Required"   : "Yes" if field.required else "No",
                "Data_Source"      : DATA_SOURCE,
                "Processed_By"     : PROCESSED_BY,
                "Process_Date"     : PROCESS_DATE,
            })

        print(f"  {fc}: {len([r for r in records if r['Layer_Name']==fc])} fields documented")

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    with open(METADATA_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["Layer_Name", "Geometry_Type", "Feature_Count",
                      "CRS_Name", "CRS_Type", "CRS_WKID",
                      "Field_Name", "Field_Type", "Field_Length",
                      "Field_Alias", "Field_Required",
                      "Data_Source", "Processed_By", "Process_Date"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"\n  {len(records)} field records written to:")
    print(f"  {METADATA_CSV}\n")
    return records


# ---------------------------------------------------------------------------
# Generate layer-level summary for data catalogue
# ---------------------------------------------------------------------------

def generate_layer_summary(gdb_path):
    """
    Produces a layer-level summary suitable for a GIS data catalogue.
    One row per layer with key descriptive information.
    """
    print("--- Generating Layer Summary ---\n")

    arcpy.env.workspace = gdb_path
    feature_classes     = arcpy.ListFeatureClasses()
    summary             = []

    layer_descriptions = {
        "Street_Centrelines"     : "City of Guelph road network centrelines with classification, speed, and asset attributes",
        "Street_Centrelines_MTM10": "Street centrelines reprojected to NAD83 CSRS MTM Zone 10 for municipal GIS operations",
        "Bus_Stops"              : "Guelph Transit bus stop locations with service type and schedule attributes",
        "Bus_Stops_MTM10"        : "Bus stops reprojected to NAD83 CSRS MTM Zone 10 for municipal GIS operations",
    }

    for fc in feature_classes:
        path  = os.path.join(gdb_path, fc)
        desc  = arcpy.Describe(path)
        sr    = desc.spatialReference
        ext   = desc.extent
        count = int(arcpy.GetCount_management(path).getOutput(0))
        flds  = [f.name for f in arcpy.ListFields(path) if f.type not in ("Geometry", "OID")]

        summary.append({
            "Layer_Name"      : fc,
            "Description"     : layer_descriptions.get(fc, "City of Guelph Open Data"),
            "Geometry_Type"   : desc.shapeType,
            "Feature_Count"   : count,
            "Field_Count"     : len(flds),
            "CRS_Name"        : sr.name,
            "CRS_WKID"       : sr.factoryCode if sr.factoryCode else "N/A",
            "Extent_XMin"     : round(ext.XMin, 2),
            "Extent_XMax"     : round(ext.XMax, 2),
            "Extent_YMin"     : round(ext.YMin, 2),
            "Extent_YMax"     : round(ext.YMax, 2),
            "CSRS_Compliant"  : "Yes" if "CSRS" in sr.name else "No",
            "Data_Source"     : DATA_SOURCE,
            "Processed_By"    : PROCESSED_BY,
            "Process_Date"    : PROCESS_DATE,
        })

        print(f"  {fc}")
        print(f"    Features  : {count:,}")
        print(f"    CRS       : {sr.name}")
        print(f"    CSRS OK   : {'Yes' if 'CSRS' in sr.name else 'No — see 03_reproject_mtm.py'}")
        print()

    with open(SUMMARY_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["Layer_Name", "Description", "Geometry_Type",
                      "Feature_Count", "Field_Count", "CRS_Name", "CRS_WKID",
                      "Extent_XMin", "Extent_XMax", "Extent_YMin", "Extent_YMax",
                      "CSRS_Compliant", "Data_Source", "Processed_By", "Process_Date"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary)

    print(f"  Layer summary written to:")
    print(f"  {SUMMARY_CSV}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(f"\n{'='*60}")
    print(f"  Guelph Municipal GIS Pipeline — 04 Metadata Report")
    print(f"  Run at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    arcpy.env.workspace       = GDB_PATH
    arcpy.env.overwriteOutput = True

    generate_field_metadata(GDB_PATH)
    generate_layer_summary(GDB_PATH)

    print(f"{'='*60}")
    print(f"  Metadata complete.")
    print(f"  Outputs saved to: {OUTPUT_FOLDER}")
    print(f"{'='*60}\n")
