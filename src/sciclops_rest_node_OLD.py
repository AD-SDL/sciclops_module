#! /usr/bin/env python3
"""REST-based node for Sciclops robots"""

from typing import Any, Optional

from madsci.common.types.admin_command_types import AdminCommandResponse
from madsci.common.types.location_types import LocationArgument
from madsci.common.types.node_types import RestNodeConfig
from madsci.common.types.resource_types import Slot, Stack
from madsci.node_module.helpers import action
from madsci.node_module.rest_node_module import RestNode
from typing_extensions import Annotated

from sciclops_interface_OLD import SCICLOPS


class SciclopsConfig(RestNodeConfig):
    """Configuration for the camera node module."""

    vendor_id: int = 0x7513
    """The sciclops vendor id address, a device path in Linux/Mac."""

    product_id: int = 0x0002

    """The sciclops vendor id address, a device path in Linux/Mac."""

    neutral_joints: dict[str, float] = {
        "Z": 23.5188,
        "R": 109.2741,
        "Y": 32.7484,
        "P": 98.2955,
    }
    """The neutral joint position for the arm"""

    plate_info: Optional[Any] = None
    """The specs for picking up different kinds of plates"""

    stack_formation: list[str] = [
        "microplate_no_lid_stack",
        "microplate_no_lid_stack",
        "microplate_no_lid_stack",
        "microplate_no_lid_stack",
    ]
    """List of 4 stack types. Options: 'microplate_no_lid_stack', 'microplate_with_lid_stack', 'deep_well_plate_stack'"""


class SciclopsNode(RestNode):
    """MADSci node module for the Hudson Robotics Sciclops."""

    sciclops_interface: SCICLOPS = None
    config: SciclopsConfig = SciclopsConfig()
    config_model = SciclopsConfig

    def startup_handler(self):
        """Called to (re)initialize the node. Should be used to open connections to devices or initialize any other resources."""

        try:
            self._create_sciclops_templates()

            self.logger.log("Node initializing...")
            self.sciclops_interface = SCICLOPS(
                config=self.config,
                resource_client=self.resource_client,
                gripper_id=self.gripper_resource.resource_id,
            )

        except Exception as error_msg:
            self.logger.log_error(f"Error starting the Sciclops Node: {error_msg}")
            self.startup_has_run = False
        else:
            self.startup_has_run = True
            self.logger.log("Sciclops node initialized")

    def _create_sciclops_templates(self) -> None:
        """Create all SCICLOPS-specific resource templates."""

        # 1. Gripper slot template
        gripper_slot = Slot(
            resource_name="sciclops_finger_gripper",
            resource_class="SCICLOPSGripper",
            capacity=1,
            attributes={
                "gripper_type": "sciclops_finger",
                "handles_slas_standard": True,
                "well_formats": [96, 384, 1536],
                "description": "SCICLOPS finger gripper slot for ANSI SLAS-standard microplates",
            },
        )

        self.resource_client.init_template(
            resource=gripper_slot,
            template_name="sciclops_finger_gripper_slot",
            description="Template for SCICLOPS finger gripper slot. Used to track what the gripper is holding.",
            required_overrides=["resource_name"],
            tags=["sciclops", "gripper", "slot"],
            created_by=self.node_definition.node_id,
            version="1.0.0",
        )

        # Initialize gripper resource from template
        self.gripper_resource = self.resource_client.create_resource_from_template(
            template_name="sciclops_finger_gripper_slot",
            resource_name=f"sciclops_gripper_{self.node_definition.node_name}",
            add_to_database=True,
        )

        # 2. Exchange slot template
        exchange_slot = Slot(
            resource_name="sciclops_exchange",
            resource_class="SCICLOPSExchange",
            capacity=1,
            attributes={
                "slot_type": "exchange",
                "handles_slas_standard": True,
                "description": "SCICLOPS exchange position for plate transfer",
            },
        )

        self.resource_client.init_template(
            resource=exchange_slot,
            template_name="sciclops_exchange_slot",
            description="Template for SCICLOPS exchange slot. Transfer position for plates between robot and other devices.",
            required_overrides=["resource_name"],
            tags=["sciclops", "exchange", "slot", "transfer"],
            created_by=self.node_definition.node_id,
            version="1.0.0",
        )

        # Initialize exchange resource from template
        self.exchange_resource = self.resource_client.create_resource_from_template(
            template_name="sciclops_exchange_slot",
            resource_name=f"sciclops_exchange_{self.node_definition.node_name}",
            add_to_database=True,
        )

        # 3. Microplate stack template (no lid)
        microplate_no_lid_stack = Stack(
            resource_name="microplate_no_lid_stack",
            resource_class="SCICLOPSStack",
            capacity=30,
            attributes={
                "stack_type": "microplate_no_lid",
                "plate_format": "96_well",
                "max_capacity": 30,
                "has_lids": False,
                "handles_slas_standard": True,
                "description": "SCICLOPS stack for microplates without lids (30 plate capacity)",
            },
        )

        self.resource_client.init_template(
            resource=microplate_no_lid_stack,
            template_name="microplate_no_lid_stack",
            description="Template for SCICLOPS microplate stack without lids. Holds up to 30 ANSI SLAS-standard microplates.",
            required_overrides=["resource_name"],
            tags=["sciclops", "stack", "microplate", "no_lid"],
            created_by=self.node_definition.node_id,
            version="1.0.0",
        )

        # 4. Microplate stack template (with lid)
        microplate_with_lid_stack = Stack(
            resource_name="microplate_with_lid_stack",
            resource_class="SCICLOPSStack",
            capacity=25,
            attributes={
                "stack_type": "microplate_with_lid",
                "plate_format": "96_well",
                "max_capacity": 25,
                "has_lids": True,
                "handles_slas_standard": True,
                "description": "SCICLOPS stack for microplates with lids (25 plate capacity)",
            },
        )

        self.resource_client.init_template(
            resource=microplate_with_lid_stack,
            template_name="microplate_with_lid_stack",
            description="Template for SCICLOPS microplate stack with lids. Holds up to 25 ANSI SLAS-standard microplates with lids.",
            required_overrides=["resource_name"],
            tags=["sciclops", "stack", "microplate", "with_lid"],
            created_by=self.node_definition.node_id,
            version="1.0.0",
        )

        # 5. Deep well plate stack template
        deep_well_plate_stack = Stack(
            resource_name="deep_well_plate_stack",
            resource_class="SCICLOPSStack",
            capacity=9,
            attributes={
                "stack_type": "deep_well_plate",
                "plate_format": "deep_well",
                "max_capacity": 9,
                "has_lids": False,
                "handles_slas_standard": True,
                "description": "SCICLOPS stack for deep well blocks (9 block capacity)",
            },
        )

        self.resource_client.init_template(
            resource=deep_well_plate_stack,
            template_name="deep_well_plate_stack",
            description="Template for SCICLOPS deep well plate stack. Holds up to 9 deep well blocks.",
            required_overrides=["resource_name"],
            tags=["sciclops", "stack", "deep_well"],
            created_by=self.node_definition.node_id,
            version="1.0.0",
        )

        # 6. Stack access slot template
        stack_access_slot = Slot(
            resource_name="stack_access_slot",
            resource_class="SCICLOPSStackAccess",
            capacity=1,
            attributes={
                "slot_type": "stack_access",
                "handles_slas_standard": True,
                "description": "SCICLOPS stack access slot positioned in front of each stack",
            },
        )

        self.resource_client.init_template(
            resource=stack_access_slot,
            template_name="stack_access_slot",
            description="Template for SCICLOPS stack access slot. Positioned in front of each stack for plate access.",
            required_overrides=["resource_name"],
            tags=["sciclops", "slot", "stack_access"],
            created_by=self.node_definition.node_id,
            version="1.0.0",
        )

        self.stack_resources = []
        self.stack_access_slots = []

        for i, stack_type in enumerate(self.config.stack_formation, start=1):
            if stack_type not in [
                "microplate_no_lid_stack",
                "microplate_with_lid_stack",
                "deep_well_plate_stack",
            ]:
                self.logger.log_error(
                    f"Invalid stack type '{stack_type}' at position {i}"
                )
                raise ValueError(f"Invalid stack type: {stack_type}")

            # Create stack resource from the specified template
            stack_resource = self.resource_client.create_resource_from_template(
                template_name=stack_type,
                resource_name=f"sciclops_stack_{i}_{self.node_definition.node_name}",
                add_to_database=True,
            )
            self.stack_resources.append(stack_resource)

            # Create corresponding stack access slot
            stack_access = self.resource_client.create_resource_from_template(
                template_name="stack_access_slot",
                resource_name=f"sciclops_stack_{i}_access_{self.node_definition.node_name}",
                add_to_database=True,
            )
            self.stack_access_slots.append(stack_access)

            self.logger.log(f"Initialized stack {i} as {stack_type}")

    def shutdown_handler(self) -> None:
        """Called to shutdown the node. Should be used to close connections to devices or release any other resources."""
        try:
            self.sciclops_interface.disconnect()
            del self.sciclops_interface
            self.sciclops_interface = None
        except Exception as err:
            self.logger.log_error(f"Error shutting down the Sciclops Node: {err}")
            raise err

    def state_handler(self) -> None:
        """Periodically called to update the current state of the node."""
        if self.sciclops_interface is not None:
            # Getting robot state
            robot_status = self.sciclops_interface.get_status()
            if self.sciclops_interface.movement_state == "BUSY":
                self.node_state = {
                    "sciclops_status_code": "BUSY",
                }
            elif robot_status:
                self.node_state = {
                    "sciclops_status_code": robot_status,
                }
                self.logger.log(f"Sciclops status: {robot_status}")
            else:
                self.node_state = {
                    "sciclops_status_code": "UNKNOWN",
                }
        else:
            self.node_state = {
                "sciclops_status_code": "OFFLINE",
            }
            self.logger.error("Sciclops is not initialized.")

    @action(name="get_plate")
    def get_plate(
        self,
        source: Annotated[LocationArgument, "Stack to get plate from"],
        target: Annotated[LocationArgument, "Exchange to place plate"],
    ):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        self.sciclops_interface.get_plate(source, target)
        return

    @action(name="return_plate")
    def return_plate(
        self,
        source: Annotated[LocationArgument, "Exchange to get plate from"],
        target: Annotated[LocationArgument, "Tower to place plate"],
    ):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        self.sciclops_interface.return_plate(source, target)
        return

    @action(name="limp")
    def limp(
        self,
        toggle: Annotated[bool, "turn on or off bool"] = False,
    ):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        self.sciclops_interface.limp(toggle)
        return

    @action(name="open")
    def open(
        self,
    ):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        self.sciclops_interface.open()
        return

    @action(name="close")
    def close(
        self,
    ):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        self.sciclops_interface.close()
        return

    @action(name="move")
    def move(self, target: Annotated[LocationArgument, "Target Location to move to"]):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        location = target.location
        self.sciclops_interface.move(
            location["Z"], location["R"], location["Y"], location["P"]
        )
        return

    def get_location(self) -> AdminCommandResponse:
        """Return the current position of the sciclops"""
        try:
            return AdminCommandResponse(
                data={"location": self.sciclops_interface.get_position()}
            )
        except Exception:
            return AdminCommandResponse(success=False)

    def home(self) -> AdminCommandResponse:
        """Home the sciclops"""
        try:
            self.sciclops_interface.home()
            return AdminCommandResponse()
        except Exception:
            return AdminCommandResponse(success=False)

    def reset(self) -> AdminCommandResponse:
        """Reset the Sciclops robot"""
        self.logger.log("Resetting node...")
        result = super().reset()
        self.logger.log("Node reset.")
        return result


if __name__ == "__main__":
    sciclops_node = SciclopsNode()
    sciclops_node.start_node()
