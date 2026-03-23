# =============================================================================
# Guelph Municipal GIS Pipeline
# Script 02 — Asset Preparation for ERP Integration
#
# Author  : Ibrahim Mirza
# Date    : 2026
#
# Description:
#   Prepares Guelph road and transit datasets for ERP integration by
#   classifying assets, flagging data gaps, and enriching records with
#   derived attributes. Mirrors the spatial data preparation workflow
#   required before GIS datasets can be loaded into an ERP asset
#   management system such as IBM Maximo or Esri Cityworks.
#
#   Key outputs:
#     - ASSET_STATUS field: "Verified", "Needs Review", "Data Gap"
#     - MAINTENANCE_PRIORITY: ranked by road class and surface age
#     - ROAD_CATEGORY: simplified classification for ERP work orders
#     - STOP_SERVICE_TYPE: transit service classification for web mapping
# =============================================================================

import arcpy
import os
import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = r"C:\your\path\to\Guelph_Municipal_GIS_Pipeline"
GDB_PATH     = os.path.join(PROJECT_ROOT, "Guelph_Municipal_GIS_Pipeline.gdb")

ROADS_LAYER  = "Street_Centrelines"
STOPS_LAYER  = "Bus_Stops"

CURRENT_YEAR = 2026


# ---------------------------------------------------------------------------
# Classify road assets and flag ERP readiness
# ---------------------------------------------------------------------------

def prepare_road_assets(gdb_path, layer_name):
    """
    Adds three fields to the road centreline layer:

    ASSET_STATUS — ERP integration readiness flag:
      "Verified"     : ASSETID present, ROADCLASS known, no critical nulls
      "Needs Review" : some attributes present but gaps exist
      "Data Gap"     : ASSETID missing — cannot be matched to ERP record

    MAINTENANCE_PRIORITY — derived from road class and surface age:
      1 = Immediate   : arterial/collector with surface > 20 years old
      2 = Near-term   : local roads surface > 15 years, or unknown surface year
      3 = Routine     : recently surfaced or low-traffic roads

    ROAD_CATEGORY — simplified 4-class system for web map and ERP labels:
      "Arterial", "Collector", "Local", "Other"

    These fields directly support ERP work order management by giving
    the asset management system consistent, clean attribute values.
    """
    print("--- Road Asset Preparation ---\n")

    roads_path = os.path.join(gdb_path, layer_name)
    fields     = [f.name for f in arcpy.ListFields(roads_path)]

    # Add new fields
    new_fields = [
        ("ASSET_STATUS",          "TEXT",  "Asset ERP Status",           20),
        ("MAINTENANCE_PRIORITY",  "SHORT", "Maintenance Priority (1-3)", None),
        ("ROAD_CATEGORY",         "TEXT",  "Road Category (Simplified)", 15),
    ]

    for fname, ftype, falias, flength in new_fields:
        if fname not in fields:
            print(f"  Adding field: {fname}")
            if flength:
                arcpy.management.AddField(roads_path, fname, ftype,
                                          field_alias=falias,
                                          field_length=flength)
            else:
                arcpy.management.AddField(roads_path, fname, ftype,
                                          field_alias=falias)

    print(f"\n  Running UpdateCursor on {ROADS_LAYER}...")

    # Road class → simplified category mapping
    category_map = {
        "ARTERIAL"   : "Arterial",
        "COLLECTOR"  : "Collector",
        "LOCAL"      : "Local",
        "EXPRESSWAY" : "Arterial",
        "RAMP"       : "Other",
        "LANE"       : "Other",
        "TRAIL"      : "Other",
        "PRIVATE"    : "Other",
    }

    cursor_fields = [
        "ASSETID", "ROADCLASS", "SPEED", "SURFACEYEA",
        "INSTALLYEA", "STATUS",
        "ASSET_STATUS", "MAINTENANCE_PRIORITY", "ROAD_CATEGORY"
    ]

    verified   = 0
    needs_review = 0
    data_gap   = 0

    with arcpy.da.UpdateCursor(roads_path, cursor_fields) as cursor:
        for row in cursor:
            asset_id    = row[0]
            road_class  = row[1]
            speed       = row[2]
            surface_yr  = row[3]
            install_yr  = row[4]
            status      = row[5]

            # --- ASSET_STATUS ---
            if not asset_id or asset_id.strip() == "":
                row[6] = "Data Gap"
                data_gap += 1
            elif not road_class or not speed:
                row[6] = "Needs Review"
                needs_review += 1
            else:
                row[6] = "Verified"
                verified += 1

            # --- MAINTENANCE_PRIORITY ---
            rc_upper = road_class.upper() if road_class else ""
            if surface_yr and surface_yr > 0:
                surface_age = CURRENT_YEAR - surface_yr
            else:
                surface_age = 99  # unknown — treat as old

            if rc_upper in ("ARTERIAL", "COLLECTOR", "EXPRESSWAY"):
                if surface_age > 20:
                    row[7] = 1   # Immediate
                elif surface_age > 10:
                    row[7] = 2   # Near-term
                else:
                    row[7] = 3   # Routine
            else:
                if surface_age > 15:
                    row[7] = 2
                else:
                    row[7] = 3

            # Override to priority 1 if no surface year recorded
            if not surface_yr or surface_yr == 0:
                row[7] = 2   # Cannot confirm — flag for review

            # --- ROAD_CATEGORY ---
            row[8] = category_map.get(rc_upper, "Other")

            cursor.updateRow(row)

    total = verified + needs_review + data_gap
    print(f"\n  ASSET STATUS SUMMARY:")
    print(f"  {'Verified':<20} {verified:>8,}  ({round(verified/total*100,1)}%)")
    print(f"  {'Needs Review':<20} {needs_review:>8,}  ({round(needs_review/total*100,1)}%)")
    print(f"  {'Data Gap':<20} {data_gap:>8,}  ({round(data_gap/total*100,1)}%)")
    print(f"  {'Total':<20} {total:>8,}")
    print()

    # Print maintenance priority breakdown
    priority_counts = {1: 0, 2: 0, 3: 0}
    with arcpy.da.SearchCursor(roads_path, ["MAINTENANCE_PRIORITY"]) as cursor:
        for row in cursor:
            p = row[0]
            if p in priority_counts:
                priority_counts[p] += 1

    print(f"  MAINTENANCE PRIORITY SUMMARY:")
    print(f"  Priority 1 — Immediate   : {priority_counts[1]:,} segments")
    print(f"  Priority 2 — Near-term   : {priority_counts[2]:,} segments")
    print(f"  Priority 3 — Routine     : {priority_counts[3]:,} segments")
    print()

    print(f"  [OK] Road asset preparation complete.")


# ---------------------------------------------------------------------------
# Classify bus stop service types
# ---------------------------------------------------------------------------

def prepare_stop_assets(gdb_path, layer_name):
    """
    Adds STOP_SERVICE_TYPE to bus stops based on service attributes.
    Classifies stops for web mapping display and transit system integration.

    SERVICE_TYPE values:
      "Full Service"     : operates Mon-Sat and Sunday
      "Weekday Only"     : no Sunday or holiday service
      "On Demand"        : on-demand service only
      "Limited Service"  : partial week coverage
    """
    print("--- Bus Stop Asset Preparation ---\n")

    stops_path = os.path.join(gdb_path, layer_name)
    fields     = [f.name for f in arcpy.ListFields(stops_path)]

    if "STOP_SERVICE_TYPE" not in fields:
        print("  Adding field: STOP_SERVICE_TYPE")
        arcpy.management.AddField(
            stops_path, "STOP_SERVICE_TYPE", "TEXT",
            field_alias="Stop Service Type",
            field_length=20
        )

    print(f"  Classifying {STOPS_LAYER} service types...")

    cursor_fields = ["MonSat", "Sun", "Holiday", "On_demand_", "STOP_SERVICE_TYPE"]

    full_service = 0
    weekday_only = 0
    od_count    = 0
    limited      = 0

    with arcpy.da.UpdateCursor(stops_path, cursor_fields) as cursor:
        for row in cursor:
            mon_sat   = row[0]
            sun       = row[1]
            holiday   = row[2]
            on_demand_val = row[3]

            has_monsat  = mon_sat  and mon_sat.strip().upper()  not in ("", "N", "NO")
            has_sun     = sun      and sun.strip().upper()      not in ("", "N", "NO")
            has_od= on_demand_val and on_demand_val.strip() not in ("", "None")

            if has_od and not has_monsat:
                row[4] = "On Demand"
                od_count += 1
            elif has_monsat and has_sun:
                row[4] = "Full Service"
                full_service += 1
            elif has_monsat and not has_sun:
                row[4] = "Weekday Only"
                weekday_only += 1
            else:
                row[4] = "Limited Service"
                limited += 1

            cursor.updateRow(row)

    total = full_service + weekday_only + od_count + limited
    print(f"\n  STOP SERVICE TYPE SUMMARY:")
    print(f"  Full Service    : {full_service:>5,}")
    print(f"  Weekday Only    : {weekday_only:>5,}")
    print(f"  On Demand       : {od_count:>5,}")
    print(f"  Limited Service : {limited:>5,}")
    print(f"  Total           : {total:>5,}")
    print()
    print(f"  [OK] Bus stop preparation complete.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(f"\n{'='*60}")
    print(f"  Guelph Municipal GIS Pipeline — 02 Asset Preparation")
    print(f"  Run at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    arcpy.env.workspace       = GDB_PATH
    arcpy.env.overwriteOutput = True

    prepare_road_assets(GDB_PATH, ROADS_LAYER)
    prepare_stop_assets(GDB_PATH, STOPS_LAYER)

    print(f"\n{'='*60}")
    print(f"  Script complete — ready for 03_reproject_mtm.py")
    print(f"{'='*60}\n")
