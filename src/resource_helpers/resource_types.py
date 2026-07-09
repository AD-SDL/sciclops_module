"""This module contains the Pydantic models for the SciClops resource types"""

from typing import Optional

from madsci.common.types.resource_types import Resource
from pydantic import BaseModel


class SciClopsLocation(BaseModel):
    """A location accessible by the SciClops"""

    name: str
    """Internal name of the location"""
    joint_angles: dict
    """List of 4 joint angles (unit: integer stepper values)"""
    location_type: str
    """Type of location, either stack or nest. This will be used to determine gripper path for interactions with the location"""
    safe_approach_height: Optional[float] = None
    """A safe height (unit: integer stepper value for Z axis) from which
    to extend the arm when approaching this location."""


class SciClopsPlate(BaseModel):
    """A MADSci plate resource with the attributes required for use with the SciClops robotic arm."""

    plate_height: float
    grip_height: float

    plate_height_with_lid: float | None = None
    lid_height: float | None = None
    lid_grip_height: float | None = None
    lid_removal_grip_height: float | None = None

    has_lid: bool
    is_lid: bool

    @classmethod
    def from_resource(cls, resource: Resource):
        """Validates that a plate resource contains the correct attributes to be SciClops compatible."""

        attrs = resource.attributes

        is_lid = resource.attributes.get("lid", False)
        has_lid = False

        if not is_lid:
            lid_slot = resource.children.get("lid_slot")
            if lid_slot is not None:
                print("There is a lid slot!")
                has_lid = any(
                    child.attributes.get("lid", False) for child in lid_slot.children
                )

        return cls(
            plate_height=attrs["plate_height"],
            grip_height=attrs["sciclops_grip_height"],
            plate_height_with_lid=attrs.get("plate_height_with_lid"),
            lid_height=attrs.get("lid_height"),
            lid_grip_height=attrs.get("sciclops_lid_grip_height"),
            lid_removal_grip_height=attrs.get("sciclops_lid_removal_grip_height"),
            has_lid=has_lid,
            is_lid=is_lid,
        )
