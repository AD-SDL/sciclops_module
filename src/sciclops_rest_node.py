#! /usr/bin/env python3
"""The server for the Hudson Platecrane/Sciclops that takes incoming WEI flow requests from the experiment application"""

from pathlib import Path

from sciclops_driver import SCICLOPS
from typing_extensions import Annotated
from madsci.node_module.rest_node_module import RestNode
from typing import Any, Optional
from madsci.common.types.node_types import RestNodeConfig
from madsci.common.types.base_types import BaseModel
from madsci.node_module.abstract_node_module import action
from madsci.common.types.action_types import ActionResult, ActionSucceeded
from madsci.common.types.location_types import Location

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
class NodeLocation(BaseModel):
    """custom location format for the sciclops"""
    Z: float = 23.5188
    """Z joint"""
    R: float = 109.2741
    """Rotation joint"""
    Y: float = 32.7484
    """extension joint"""
    P: float = 98.2955
    """wrist joint"""
    resource_id: Optional[str] = None
    """id for the resource"""



class SciclopsNode(RestNode):
    config_model = SciclopsConfig

    def startup_handler(self):
        """Initial run function for the app, initializes the state
        Parameters
        ----------
        app : FastApi
        The REST API app being initialized

        Returns
        -------
        None"""
        print("Hello, World!")
        try:
            self.sciclops = SCICLOPS(self.config)
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
        pos: Annotated[NodeLocation, "Stack to get plate from"],
    ):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        self.sciclops.get_plate(pos)
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
        target: NodeLocation
    ):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        target = NodeLocation.model_validate(target)  
        self.sciclops.move(target.Z, target.R, target.Y, target.P)
        return ActionSucceeded()

if __name__ == "__main__":
    sciclops_node = SciclopsNode()
    sciclops_node.start_node()
