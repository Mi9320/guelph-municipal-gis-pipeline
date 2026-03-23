#=============================================================================
# Guelph Municipal GIS Pipeline
# Script 03 — Reprojection to NAD83 CSRS MTM Zone 10
#
# Author  : Ibrahim Mirza
# Date    : 2026
#
# Description:
#   Reprojects City of Guelph datasets from NAD83 UTM Zone 17N to
#   NAD83 CSRS MTM Zone 10 — the correct regional standard for the
#   Guelph-Wellington area used by the City and surrounding municipalities.
#
#   WHY MTM Zone 10 (not UTM Zone 17N):
#     MTM (Modified Transverse Mercator) was designed specifically for
#     Ontario. It uses narrower 3-degree zones instead of UTM's 6-degree
#     zones, which reduces scale distortion significantly. For municipal
#     infrastructure work in Guelph, MTM Zone 10 provides better accuracy
#     for distance and area measurements than UTM Zone 17N.
#
#   WHY CSRS (not standard NAD83):
#     The input data is in NAD_1983_UTM_Zone_17N — the US version of NAD83.
#     Canadian municipal data should use NAD83 CSRS (the Canadian Spatial
#     Reference System), maintained by Natural Resources Canada. The two
#     datums differ by approximately 1 metre in Ontario.
#
#   EPSG: 2952 = NAD83 CSRS MTM Zone 10 (Guelph, Waterloo, Hamilton)
#=============================================================================



import arcpy
import os

PROJECT_ROOT = r"C:\your\path\to\Guelph_Municipal_GIS_Pipeline"
GDB_PATH     = os.path.join(PROJECT_ROOT, "Guelph_Municipal_GIS_Pipeline.gdb")
ROADS_INPUT  = "Street_Centrelines"
STOPS_INPUT  = "Bus_Stops"
ROADS_OUTPUT = "Street_Centrelines_MTM10"
STOPS_OUTPUT = "Bus_Stops_MTM10"
TARGET_WKID  = 2952

arcpy.env.workspace       = GDB_PATH
arcpy.env.overwriteOutput = True

target_sr = arcpy.SpatialReference(TARGET_WKID)
print(f"Target CRS: {target_sr.name}")

# Reproject roads
input_path  = os.path.join(GDB_PATH, ROADS_INPUT)
output_path = os.path.join(GDB_PATH, ROADS_OUTPUT)

if arcpy.Exists(output_path):
    arcpy.management.Delete(output_path)

arcpy.management.Project(
    in_dataset      = input_path,
    out_dataset     = output_path,
    out_coor_system = target_sr
)
print(f"Roads reprojected OK")

# Reproject stops
input_path  = os.path.join(GDB_PATH, STOPS_INPUT)
output_path = os.path.join(GDB_PATH, STOPS_OUTPUT)

if arcpy.Exists(output_path):
    arcpy.management.Delete(output_path)

arcpy.management.Project(
    in_dataset      = input_path,
    out_dataset     = output_path,
    out_coor_system = target_sr
)
print(f"Stops reprojected OK")

# Verify
for fc in [ROADS_OUTPUT, STOPS_OUTPUT]:
    desc = arcpy.Describe(os.path.join(GDB_PATH, fc))
    print(f"\n{fc}")
    print(f"  CRS : {desc.spatialReference.name}")
    print(f"  Type: {desc.spatialReference.type}")
