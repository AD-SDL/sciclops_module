#! /usr/bin/env python3
"""The server for the Hudson Platecrane/Sciclops that takes incoming WEI flow requests from the experiment application"""

from pathlib import Path

from sciclops_driver import SCICLOPS
from typing_extensions import Annotated
from madsci.node_module.rest_node_module import RestNode
from typing import Union
from madsci.common.types.node_types import RestNodeConfig
from madsci.node_module.abstract_node_module import action
from madsci.common.types.action_types import ActionResult, ActionSucceeded


class SciclopsConfig(RestNodeConfig):
    """Configuration for the camera node module."""

    sciclops_address: Union[int, str] = 0
    """The sciclops usb address, a device path in Linux/Mac."""



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
            self.sciclops = SCICLOPS()
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
        pos: Annotated[int, "Stack to get plate from"],
        lid: Annotated[bool, "Whether plate has a lid or not"] = False,
        trash: Annotated[bool, "Whether to use the trash"] = False,
    ):
        """Get a plate from a stack position and move it to transfer point (or trash)"""
        self.sciclops.get_plate(pos, lid, trash)
        return ActionSucceeded()

if __name__ == "__main__":
    sciclops_node = SciclopsNode()
    sciclops_node.start_node()
