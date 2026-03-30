#! /usr/bin/env python3
"""The server for the Hudson Platecrane/Sciclops that takes incoming WEI flow requests from the experiment application"""

from pathlib import Path
from typing import Annotated, Optional, Union
import traceback

from fastapi.datastructures import State
from madsci.common.types.action_types import ActionFailed
from madsci.common.types.location_types import LocationArgument
from madsci.common.types.node_types import NodeDefinition, RestNodeConfig
from madsci.common.types.resource_types import Slot, Stack, Collection, Resource
from madsci.node_module.helpers import action
from madsci.node_module.rest_node_module import RestNode

from sciclops_driver import SCICLOPS, SciClopsLocation
from resource_helpers.sciclops_resource_defs import plate_definitions

"""
TODO:
- Add all the SciClops locations to the location client!
- Righ now cannot replace a lid from the stack because a stack can have more than one chiid.
    Error: 'Stack' object has no attribute 'child'",



Below is the plate with lid standard that I'm working with:

        # # TESTING (create a properly formatted plate resource with lid slot)
        # test_lid = Resource(
        #     resource_name = "TEST_LID",
        #     attributes={
        #         "lid": True
        #     }
        # )
        # test_plate_resource = Collection(
        #     resource_name = "FORMATTED_TEST_PLATE3",
        #     capacity=2,
        #     children={
        #         "lid_slot": Slot(
        #             resource_name = "lid slot resource on test plate",
        #             children=[test_lid]
        #         )
        #     }
        # )
        # self.resource_client.add_resource(test_plate_resource)


"""


class SciClopsConfig(RestNodeConfig):
    """Configuration for the SciClops REST Node."""

    # TODO: What else to add here?
    default_speed: int = 100
    """The default speed for the PlateCrane robot arm to move, as a percentage."""


class SciClopsNode(RestNode):
    """A MADSci REST Node for controlling the Hudson SciClops robotic arm."""

    sciclops: Optional[SCICLOPS] = None
    """The SciClops driver instance."""
    config_model = SciClopsConfig
    """The configuration model for the SciClops REST Node."""
    config: SciClopsConfig = SciClopsConfig()
    """The default configuration for the SciClops REST Node."""
    module_version: str = "2.1.0"
    """The version of the SciClops REST Node module."""

    def startup_handler(self):
        """Initializes the SciClops driver at node startup."""
        self.sciclops = SCICLOPS()

        # Create resources.
        self._init_resource_templates()
        self._create_resources()

        # TESTING
        self._create_test_plate()



    def _init_resource_templates(
        self
    ):

        # Gripper template
        gripper_slot = Slot(
            resource_name="sciclops_gripper",
            resource_class="SciClopsGripper",
            capacity=1,
            attributes={
                "gripper_type": "sciclops_finger",
                "description": "SCICLOPS finger gripper slot for ANSI SLAS-standard microplates",
            },
        )
        self.resource_client.init_template(
            resource=gripper_slot,
            template_name="sciclops_gripper_template",
            description="Template for SciClops finger gripper slot. Used to track what the gripper is holding.",
            required_overrides=["resource_name"],
            tags=["sciclops", "gripper", "slot"],
            created_by=self.node_definition.node_id,
            version="1.0.0",
        )

        # Exchange nest template - TODO


        # Lid nest template
        lid_nest_slot = Slot(
            resource_name="lid_nest_slot",
            resource_class="SciClopsGripper",
            capacity=1,
            attributes={
                "description": "SciClops lid nest Slot resource",
            },
        )
        self.resource_client.init_template(
            resource=lid_nest_slot,
            template_name="sciclops_lid_nest_slot_template",
            description="Template for SciClops lid nest Slot.",
            required_overrides=["resource_name"],
            tags=["sciclops", "slot"],
            created_by=self.node_definition.node_id,
            version="1.0.0",
        )

        # Stack template
        sciclops_stack = Stack(
            resource_name="sciclops_stack",
            resource_class="SciClopsStack",
            attributes={
                "description": "SciClops stack.",
            },
        )
        self.resource_client.init_template(
            resource=sciclops_stack,
            template_name="sciclops_stack_template",
            description="SciClops stack template.",
            required_overrides=["resource_name"],
            tags=["sciclops", "stack"],
            created_by=self.node_definition.node_id,
            version="1.0.0",
        )


    def _create_resources(self):
        # Initialize gripper resource from template
        self.gripper_resource = self.resource_client.create_resource_from_template(
            template_name="sciclops_gripper_template",
            resource_name=f"{self.node_definition.node_name}_gripper.nest",
            add_to_database=True,
        )

        # Initialize lid nests
        self.lidnest_4 = self.resource_client.create_resource_from_template(
            template_name="sciclops_lid_nest_slot_template",
            resource_name="lidnest_4_sciclops",
            add_to_database=True,
        )
        self.lidnest_5 = self.resource_client.create_resource_from_template(
            template_name="sciclops_lid_nest_slot_template",
            resource_name="lidnest_5_sciclops",
            add_to_database=True,
        )

        # Initialize stack resources from template
        self.stack_1_resource = self.resource_client.create_resource_from_template(
            template_name = "sciclops_stack_template",
            resource_name = "stack_1",
            add_to_database = True,
        )
        self.stack_2_resource = self.resource_client.create_resource_from_template(
            template_name = "sciclops_stack_template",
            resource_name = "stack_2",
            add_to_database = True,
        )
        self.stack_3_resource = self.resource_client.create_resource_from_template(
            template_name = "sciclops_stack_template",
            resource_name = "stack_3",
            add_to_database = True,
        )
        self.stack_4_resource = self.resource_client.create_resource_from_template(
            template_name = "sciclops_stack_template",
            resource_name = "stack_4",
            add_to_database = True,
        )
        self.stack_5_resource = self.resource_client.create_resource_from_template(
            template_name = "sciclops_stack_template",
            resource_name = "stack_5",
            add_to_database = True,
        )

    def _create_test_plate(self):
        test_lid = Resource(
            resource_name = "TEST_LID",
            attributes={
                "lid": True
            }
        )
        test_plate_resource = Collection(
            resource_name = "FORMATTED_TEST_PLATE3",
            capacity=2,
            children={
                "lid_slot": Slot(
                    resource_name = "lid slot resource on test plate",
                    children=[test_lid]
                )
            }
        )
        self.resource_client.add_resource(test_plate_resource)


    @action()
    def home(self) -> None:
        """Homes the SciClops."""
        self.sciclops.home()

    @action()
    def pick(
        self,
        source: LocationArgument,
        plate_type: Optional[str] = None,
        height_offset: Annotated[int, "Height offset in mm"] = 0,
        is_lid: Annotated[bool, "Is the labware a lid?"] = False,
        has_lid: Annotated[bool, "Does the labware have a lid?"] = False,
        incremental_lift: Annotated[bool, "Incremental lift during transfer"] = False,
    ) -> None:
        """Picks labware from a location, ending in the PlateCrane gripper."""
        source.representation["name"] = source.location_name
        source = SciClopsLocation.model_validate(source.representation)

        # TESTING
        self.logger.log_info(f"{source=}")
        self.logger.log_info(f"{type(source)=}")

        # extract plate definition
        try:
            plate_def = plate_definitions[plate_type]
        except Exception as e:
            return ActionFailed(
                errors=[
                    f"Plate type {plate_type} definition does not exist in sciclops_resource_defs.py plate_definitions. {e}"
                ]
            )

        # Check state of resources in ResourceClient.
        plate_resource = None
        if (self.resource_client is not None) and (self.location_client is not None):
            # Does a plate resource exist at the source location?
            source_resource_id = self.location_client.get_location_by_name(
                source.name
            ).resource_id
            source_resource = self.resource_client.get_resource(source_resource_id)
            if len(source_resource.children) > 0:
                plate_resource = source_resource.children[0]
                # this accounts for the source resource being a stack
            else:
                return ActionFailed(
                    errors=[
                        f"No plate resource exists at source location {source.name}"
                    ]
                )

            # Is the gripper location clear?
            self.gripper_resource = self.resource_client.get_resource(
                self.gripper_resource
            )  # update the gripper resource
            if len(self.gripper_resource.children) == 1:
                return ActionFailed(
                    errors=[
                        "A resource is already in the gripper. Pick action cannot be completed."
                    ]
                )
        else:
            self.logger.log_warning(
                f"No ResourceClient and/or LocationClient present. {self.resource_client=}, {self.location_client=}"
            )

        # Physically pick the plate.
        self.sciclops.pick_plate_direct(
            source=source,
            plate_type=plate_def,
            grip_height_offset=height_offset,
            is_lid=is_lid,
            has_lid=has_lid,
            incremental_lift=incremental_lift,
        )

        # Push plate resource into gripper resource as a child.
        if plate_resource:
            self.resource_client.push(
                resource=self.gripper_resource, child=plate_resource
            )

        return None

    @action()
    def place(
        self,
        target: LocationArgument,
        plate_type: Optional[str] = None,
        height_offset: Annotated[int, "Height offset in mm."] = 0,
        is_lid: Annotated[bool, "Is the plate a lid?"] = False,
        replacing_lid: Annotated[bool, "Are you replacing a lid?"] = False,
    ) -> None:
        """Places labware at a location."""

        target.representation["name"] = target.location_name
        target = SciClopsLocation.model_validate(target.representation)

        # TESTING
        print(f"{target}")
        print(f"{type(target)}")

        # Extract plate definition
        try:
            plate_def = plate_definitions[plate_type]
        except Exception as e:
            return ActionFailed(
                errors=[
                    f"Plate type {plate_type} definition does not exist in sciclops_resource_defs.py plate_definitions. {e}"
                ]
            )

        # Check state of resources in ResourceClient.
        plate_resource = None
        if (self.resource_client is not None) and (self.location_client is not None):
            # Does a plate resource exist in the gripper?
            self.gripper_resource = self.resource_client.get_resource(
                self.gripper_resource
            )  # update the gripper resource
            if len(self.gripper_resource.children) == 1:
                plate_resource = self.gripper_resource.child
            else:
                return ActionFailed(
                    errors=[
                        "No plate resource exists in the gripper. Place action cannot be completed."
                    ]
                )

            # Is the target location clear?
            target_resource_id = self.location_client.get_location_by_name(
                target.name
            ).resource_id
            target_resource = self.resource_client.get_resource(target_resource_id)

            if len(target_resource.children) == 1 and target.location_type != "stack":
                # Do not fail the action if there's already a plate in a stack target location.
                return ActionFailed(
                    errors=[
                        f"A plate resource already exists at the target location {target.name}. The place action cannot be completed."
                    ]
                )

        else:
            self.logger.log_warning(
                f"No ResourceClient and/or LocationClient present. {self.resource_client=}, {self.location_client=}"
            )

        # Physically place the plate.
        self.sciclops.place_plate_direct(
            target=target,
            plate_type=plate_def,
            is_lid=is_lid,
            replacing_lid=replacing_lid,
            grip_height_offset=height_offset,
        )

        # Push plate resource into target resource as child.
        self.resource_client.push(
            resource=target_resource,
            child=plate_resource,
        )

        return None

    @action()
    def transfer(
        self,
        source: LocationArgument,
        target: LocationArgument,
        plate_type: Optional[str] = None,
        source_height_offset: Annotated[int, "Height offset in mm."] = 0,
        target_height_offset: Annotated[int, "Height offset in mm."] = 0,
        has_lid: Annotated[bool, "Does the plate have a lid?"] = False,
    ) -> None:
        """Transfers a plate from one location to another."""

        # Pick the plate.
        pick_result = self.pick(
            source=source,
            plate_type=plate_type,
            height_offset=source_height_offset,
            is_lid=False,  # assuming this transfer funtion is for the main labware. Remove/replace lid works for lids.
            has_lid=has_lid,
        )
        if pick_result is not None:
            # Return any ActionFailed response received.
            # Fails the action, but does not put the device into an error state.
            return pick_result

        # Place the plate.
        place_result = self.place(
            target=target,
            plate_type=plate_type,
            height_offset=target_height_offset,
            is_lid=False,  # assuming we're not using this transfer function to move lids.
            replacing_lid=False,
        )
        return place_result

    @action()
    def remove_lid(
        self,
        source: LocationArgument,
        target: LocationArgument,
        plate_type: Annotated[
            str, "Type of plate, e.g. 'flat_bottom_96well' or 'deep_96well"
        ],
        height_offset: Annotated[int, "Height offset in motor steps"] = 0,
        ignore_resource_checks: Annotated[
            bool, "True to ignore ResourceClient validations, False otherwise."
        ] = False,
    ) -> None:
        """Removes a lid from a plate."""
        source.representation["name"] = source.location_name
        target.representation["name"] = target.location_name
        source = SciClopsLocation.model_validate(source.representation)
        target = SciClopsLocation.model_validate(target.representation)

        # TESTING
        print(f"{source=}")
        print(f"{type(source)=}")

        print(f"{target=}")
        print(f"{type(target)=}")

        # Extract plate definition
        try:
            plate_def = plate_definitions[plate_type]
        except:
            return ActionFailed(
                errors=[
                    f"Plate type {plate_type} definition does not exist in sciclops_resource_defs.py plate_definitions."
                ]
            )

        # Complete MADSci resource checks.
        lid_resource = None
        plate_resource = None
        source_resource = None
        target_resource = None
        if not ignore_resource_checks:
            # TODO: Validate plate resource structure conformity with a Pydantic model.
            if (self.resource_client is not None) and (
                self.location_client is not None
            ):
                # Is a lid resource present on the source location for removal?
                source_resource_id = self.location_client.get_location_by_name(
                    source.name
                ).resource_id
                source_resource = self.resource_client.get_resource(source_resource_id)
                if len(source_resource.children) == 1:
                    plate_resource = source_resource.child
                    if "lid_slot" in plate_resource.children:
                        lid_slot_child_value = plate_resource.children["lid_slot"]
                        if isinstance(lid_slot_child_value, Slot):
                            if len(lid_slot_child_value.children) == 1:
                                lid_resource = (
                                    lid_slot_child_value.child
                                )  # collect lid resource
                                self.logger.log_info(
                                    f"Identified lid Slot resource {lid_resource.resource_id} for removal."
                                )
                            else:
                                return ActionFailed(
                                    errors=[
                                        f"No lid resource exists in the lid slot. {lid_slot_child_value}"
                                    ]
                                )
                        else:
                            return ActionFailed(
                                errors=[
                                    f"Lid slot child value is not of type Slot. {lid_slot_child_value=}"
                                ]
                            )
                    else:
                        return ActionFailed(
                            errors=f'No "lid" child exists on the plate resource {plate_resource.resource_id}'
                        )
                else:
                    return ActionFailed(
                        errors=[
                            f"No plate resource exists at source location {source.name}"
                        ]
                    )

                # Is the target location clear?
                target_resource_id = self.location_client.get_location_by_name(
                    target.name
                ).resource_id
                target_resource = self.resource_client.get_resource(target_resource_id)
                if not len(target_resource.children) == 0:
                    return ActionFailed(
                        errors=[
                            f"A plate resource already exists at the target location {target.name}. The remove lid action cannot be completed."
                        ]
                    )

                # Is the gripper location clear?
                self.gripper_resource = self.resource_client.get_resource(
                    self.gripper_resource
                )  # update the gripper resource
                if len(self.gripper_resource.children) == 1:
                    return ActionFailed(
                        errors=[
                            "A resource is already in the gripper. Pick action cannot be completed."
                        ]
                    )
            else:
                return ActionFailed(
                    errors = [f"No ResourceClient and/or LocationClient present. {self.resource_client=}, {self.location_client=}"]
                )
        else:
            self.logger.log_info("Skipping resources validation for remove lid action.")

        self.sciclops.remove_lid(
            source=source,
            target=target,
            plate_type=plate_def,
            grip_height_offset=height_offset,
        )

        # transfer the lid resource
        # TODO: this skips transferring through the gripper for now
        # since pick and place for the lid are not called separately
        if target_resource and lid_resource:
            # Push lid resource onto target Slot resource.
            try:
                self.resource_client.push(target_resource, lid_resource)
            except Exception as e:
                # Return Action Failed. Do not put device into an error state.
                return ActionFailed(
                    errors=[f"Lid resource could not be removed in ResourceClient. {e}"]
                )
        else:
            return ActionFailed(
                errors = [f"lid_resource or target_resource do not exist. {lid_resource=}, {target_resource=}"]
            )

    @action()
    def replace_lid(
        self,
        source: LocationArgument,
        target: LocationArgument,
        plate_type: Annotated[
            str, "Type of plate, e.g. 'flat_bottom_96well' or 'deep_96well'"
        ],
        height_offset: Annotated[int, "Height offset in motor steps"] = 0,
        ignore_resource_checks: Annotated[
            bool, "True to ignore ResourceClient validations, False otherwise."
        ] = False,
    ) -> None:
        """Replaces a lid on a plate."""
        source.representation["name"] = source.location_name
        target.representation["name"] = target.location_name
        source = SciClopsLocation.model_validate(source.representation)
        target = SciClopsLocation.model_validate(target.representation)

        # TESTING
        print(f"{source=}")
        print(f"{type(source)=}")

        print(f"{target=}")
        print(f"{type(target)=}")

        # Extract plate definition
        try:
            plate_def = plate_definitions[plate_type]
        except Exception as e:
            return ActionFailed(
                errors=[
                    f"Plate type {plate_type} definition does not exist in sciclops_resource_defs.py plate_definitions. {e}"
                ]
            )

        # Complete MADSci resource checks.
        lid_resource = None
        lid_slot_resource = None
        plate_resource = None
        source_resource = None
        target_resource = None
        if not ignore_resource_checks:
            # TODO: Validate plate resource structure conformity with a Pydantic model.
            if (self.resource_client is not None) and (
                self.location_client is not None
            ):
                # Check for a lid resource in the source location.
                source_resource_id = self.location_client.get_location_by_name(
                    source.name
                ).resource_id
                source_resource = self.resource_client.get_resource(source_resource_id)
                if (
                    len(source_resource.children) == 1
                ):  # source slot resource can only have one child
                    child_resource = source_resource.child
                    if "lid" in child_resource.attributes:
                        if source_resource.child.attributes["lid"] is True:
                            lid_resource = (
                                source_resource.child
                            )  # a lid exists at the source location
                        else:
                            return ActionFailed(
                                errors=[
                                    f'"lid" attribute is set to {source_resource.child.attributes["lid"]}.'
                                ]
                            )
                    else:
                        self.logger.log_warning(
                            f'Lid resource found does not conform to standard. No "lid" attribute found. {lid_resource}'
                        )
                else:
                    return ActionFailed(
                        errors=["No lid resource exists at source location."]
                    )

                # Check for a plate without a lid at the target location
                target_resource_id = self.location_client.get_location_by_name(
                    target.name
                ).resource_id
                target_resource = self.resource_client.get_resource(target_resource_id)
                if len(target_resource.children) == 1:
                    plate_resource = target_resource.child
                    if "lid_slot" in plate_resource.children:
                        if len(plate_resource.children["lid_slot"].children) != 0:
                            return ActionFailed(
                                errors=[
                                    f"A lid resource already exists on the plate resource at the target location. plate_resource={plate_resource=}"
                                ]
                            )
                        lid_slot_resource = plate_resource.children["lid_slot"]
                    else:
                        return ActionFailed(
                            errors=[
                                f"Target plate resource has no lid slot resource. {target_resource=}"
                            ]
                        )
                else:
                    return ActionFailed(
                        errors=[
                            f"No plate resource exists at the target location {target.name}. The remove lid action cannot be completed."
                        ]
                    )

                # Is the gripper location clear?
                self.gripper_resource = self.resource_client.get_resource(
                    self.gripper_resource
                )  # update the gripper resource
                if len(self.gripper_resource.children) == 1:
                    return ActionFailed(
                        errors=[
                            "A resource is already in the gripper. Pick action cannot be completed."
                        ]
                    )

            else:
                return ActionFailed(
                    errors = [f"No ResourceClient and/or LocationClient present. {self.resource_client=}, {self.location_client=}"]
                )
        else:
            self.logger.log_info(
                "Skipping resources validation for replace lid action."
            )

        self.sciclops.replace_lid(
            source=source,
            target=target,
            plate_type=plate_def,
            grip_height_offset=height_offset,
        )

        # Transfer the lid resource
        # TODO: this skips transferring through the gripper for now
        # since pick and place for the lid are not called separately
        if lid_resource and lid_slot_resource:
            # push lid resource onto the plate resource's lid slot
            try:
                self.resource_client.push(lid_slot_resource, lid_resource)
            except Exception as e:
                # Return Action Failed.Do not put device into an error state.
                return ActionFailed(
                    errors=[
                        f"Lid resource could not be replaced in ResourceClient. {e}"
                    ]
                )
        else:
            return ActionFailed(
                errors = [f"lid_resource or lid_slot_resource do not exist. {lid_resource=}, {lid_slot_resource=}"]
            )

    # @action
    # def get_current_position(self) -> list:
    #     """Returns the location joint angles of the SciClops."""
    #     # TODO: test this.
    #     return self.sciclops.get_current_position()


if __name__ == "__main__":
    sciclops_node = SciClopsNode()
    sciclops_node.start_node()
