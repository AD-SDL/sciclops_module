"""Resource definitions for the Hudson SciClops in RAPID 446. - DEPRICATED! TODO: DELETE"""

from resource_helpers.resource_types import PlateResource

# Dimensions of labware used on the BIO_Workcells
plate_definitions = {
    "flat_bottom_96well": PlateResource(
        plate_height=14,
        grip_height=1,
        plate_height_with_lid=16,
        lid_height=10,
        lid_grip_height=4,
        lid_removal_grip_height=12,
    ),
    "tip_box_180uL": PlateResource(
        plate_height=0,
        grip_height=0,
        plate_height_with_lid=0,
        lid_height=0,
        lid_grip_height=0,
        lid_removal_grip_height=0,
    ),
    "pcr_96well": PlateResource(
        plate_height=0,
        grip_height=0,
        plate_height_with_lid=0,
        lid_height=0,
        lid_grip_height=0,
        lid_removal_grip_height=0,
    ),
    "deep_96well": PlateResource(
        plate_height=40,
        grip_height=30,
        plate_height_with_lid=46,
        lid_height=9,
        lid_grip_height=4,
        lid_removal_grip_height=42,
    ),
}
