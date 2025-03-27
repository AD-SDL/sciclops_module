#! /usr/bin/env python3
"""The server for the Hudson Platecrane/Sciclops that takes incoming WEI flow requests from the experiment application"""

from pathlib import Path

from sciclops_interface import SCICLOPS
from typing_extensions import Annotated
from madsci.node_module.rest_node_module import RestNode
from typing import Any, Optional
from madsci.common.types.node_types import RestNodeConfig
from madsci.common.types.base_types import BaseModel
from madsci.node_module.helpers import action
from madsci.common.types.action_types import ActionResult, ActionSucceeded
from madsci.common.types.location_types import Location, LocationArgument
from madsci.common.types.resource_types import Slot
from madsci.client.resource_client import ResourceClient
from madsci.common.types.auth_types import OwnershipInfo

class SciclopsConfig(RestNodeConfig):
    """Configuration for the camera node module."""

    vendor_id: int = 0x7513
    """The sciclops vendor id address, a device path in Linux/Mac."""

    product_id: int = 0x0002

    """The sciclops vendor id address, a device path in Linux/Mac."""
    
    neutral_joints: dict[str, float] = {"Z": 23.5188, "R": 109.2741, "Y": 32.7484, "P": 98.2955}
    """The neutral joint position for the arm"""

    plate_info: Optional[Any] = None
    """The specs for picking up different kinds of plates"""

    exchange_location: Optional[Any] = None
    """the location of the exchange for placing plates"""
    
    resource_manager_url: Optional[str] = None
    """the resource manager url for the sciclops"""
class SciclopsNode(RestNode):
    config_model = SciclopsConfig

    def startup_handler(self):
        """Initial run function for the app, initializes the state
        ParametersNodeLocation
        ----------
        app : FastApi
        The REST API app being initialized

        Returns
        -------
        None"""
        print("Hello, World!")
        try:
            self.resource_client = ResourceClient(self.config.resource_manager_url)
            self.gripper = self.resource_client.query_or_add_resource(resource_name="sciclops_gripper", owner=OwnershipInfo(node_id=self.node_definition.node_id), base_type="slot")
            self.sciclops = SCICLOPS(self.config, self.resource_client, self.gripper.resource_id) 
        except Exception as error_msg:
            print("------- SCICLOPS Error message: " + str(error_msg) + (" -------"))
            raise(error_msg)
        else:
            print("SCICLOPS online")

    @action(name="status")
    def status(self):
        """Action that forces the sciclops to check its status."""
        
        self.sciclops.get_status()
        return ActionSucceeded()


    @action
    def home(self):
        """Homes the sciclops"""
        self.sciclops.home()
        return ActionSucceeded()


    @action(name="get_plate")
    def get_plate(
        self,
        source: Annotated[LocationArgument, "Stack to get plate from"],
        target: Annotated[LocationArgument, "Exchange to place plate"],
    ):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        self.sciclops.get_plate(source, target)
        return ActionSucceeded()
    
    @action(name="limp")
    def limp(
        self,
        toggle: Annotated[bool, "turn on or off bool"] = False,
    ):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        self.sciclops.limp(toggle)
        return ActionSucceeded()

    @action(name="open")
    def open(
        self,
    ):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        self.sciclops.open()
        return ActionSucceeded()
    @action(name="close")
    def close(
        self,
    ):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        self.sciclops.close()
        return ActionSucceeded()
    @action(name="move")
    def move(
        self,
        target: Annotated[LocationArgument, "Target Location to move to"]
    ):
        """Get a plate from a stack position and move it to transfer point (or trash)"""  
        location = target.location
        self.sciclops.move(location["Z"], location["R"], location["Y"], location["P"])
        return ActionSucceeded()

if __name__ == "__main__":
    sciclops_node = SciclopsNode()
    sciclops_node.start_node()
