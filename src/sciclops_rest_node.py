#! /usr/bin/env python3
"""The server for the Hudson Platecrane/Sciclops that takes incoming WEI flow requests from the experiment application"""

from typing import Any, Optional

from madsci.client.resource_client import ResourceClient
from madsci.common.types.action_types import ActionSucceeded
from madsci.common.types.admin_command_types import AdminCommandResponse
from madsci.common.types.auth_types import OwnershipInfo
from madsci.common.types.location_types import LocationArgument
from madsci.common.types.node_types import RestNodeConfig
from madsci.common.types.resource_types.definitions import SlotResourceDefinition
from madsci.node_module.helpers import action
from madsci.node_module.rest_node_module import RestNode
from typing_extensions import Annotated

from sciclops_interface import SCICLOPS


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


class SciclopsNode(RestNode):
    """MADSci node module for the Hudson Robotics Sciclops."""

    sciclops_interface: SCICLOPS
    config: SciclopsConfig = SciclopsConfig()
    config_model = SciclopsConfig

    def startup_handler(self):
        """Called to (re)initialize the node. Should be used to open connections to devices or initialize any other resources."""

        try:
            self.gripper = self.resource_client.init_resource(
                SlotResourceDefinition(
                    resource_name="sciclops_gripper_"
                    + str(self.node_definition.node_name),
                    owner=OwnershipInfo(node_id=self.node_definition.node_id),
                )
            )
            self.sciclops = SCICLOPS(
                self.config, self.resource_client, self.gripper.resource_id
            )
        except Exception as error_msg:
            print("------- SCICLOPS Error message: " + str(error_msg) + (" -------"))
            raise (error_msg)
        else:
            print("SCICLOPS online")

    @action(name="status")
    def status(self):
        """Action that forces the sciclops to check its status."""

        self.sciclops.get_status()
        return ActionSucceeded()

    @action(name="get_plate")
    def get_plate(
        self,
        source: Annotated[LocationArgument, "Stack to get plate from"],
        target: Annotated[LocationArgument, "Exchange to place plate"],
    ):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        self.sciclops.get_plate(source, target)
        return 

    @action(name="return_plate")
    def return_plate(
        self,
        source: Annotated[LocationArgument, "Exchange to get plate from"],
        target: Annotated[LocationArgument, "Tower to place plate"],
    ):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        self.sciclops.return_plate(source, target)
        return 

    @action(name="limp")
    def limp(
        self,
        toggle: Annotated[bool, "turn on or off bool"] = False,
    ):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        self.sciclops.limp(toggle)
        return 

    @action(name="open")
    def open(
        self,
    ):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        self.sciclops.open()
        return 

    @action(name="close")
    def close(
        self,
    ):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        self.sciclops.close()
        return 

    @action(name="move")
    def move(self, target: Annotated[LocationArgument, "Target Location to move to"]):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        location = target.location
        self.sciclops.move(location["Z"], location["R"], location["Y"], location["P"])
        return 

    def get_location(self) -> AdminCommandResponse:
        """Return the current position of the sciclops"""
        try:
            return AdminCommandResponse(data={"location": self.sciclops.get_position()})
        except Exception:
            return AdminCommandResponse(success=False)

    def home(self) -> AdminCommandResponse:
        """Home the sciclops"""
        try:
            self.sciclops.home()
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
