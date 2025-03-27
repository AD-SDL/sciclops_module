"""Driver for the Hudson Robotics Sciclops robot."""

import asyncio
import re

import usb.core
import usb.util

from madsci.common.types.node_types import RestNodeConfig
from madsci.client.resource_client import ResourceClient

class SCICLOPS:
    """
    Description:
    Python interface that allows remote commands to be executed to the Sciclops.
    """

    def __init__(self, config: RestNodeConfig, resource_client: ResourceClient, gripper_id: str):
        """Creates a new SCICLOPS driver object. The default VENDOR_ID and PRODUCT_ID are for the Sciclops robot."""
        self.VENDOR_ID = config.vendor_id
        self.PRODUCT_ID = config.product_id
        self.resource_client = resource_client
        self.gripper_id = gripper_id
        self.neutral_joints = config.neutral_joints
        self.host_path = self.connect_sciclops()
        self.exchange_location = config.exchange_location
        self.current_pos = [0, 0, 0, 0]
        self.STATUS = 0
        self.ERROR = ""
        self.plate_info = config.plate_info
        self.success_count = 0
        self.status = self.get_status()
        self.error = self.get_error()
        self.movement_state = "READY"

    def connect_sciclops(self):
        """
        Connect to USB device. If wrong device, inform user
        """
        host_path = usb.core.find(idVendor=self.VENDOR_ID, idProduct=self.PRODUCT_ID)

        if host_path is None:
            raise Exception("Could not establish connection.")

        else:
            print("Device Connected")
            return host_path

    def disconnect_robot(self):
        """Disconnects from the sciclops robot."""
        try:
            usb.util.dispose_resources(self.host_path)
        except Exception as err:
            print(err)
        else:
            print("Robot is disconnected")

    def send_command(self, command):
        """
        Sends provided command to Sciclops and stores data outputted by the sciclops.
        """

        self.host_path.write(4, command)

        response_buffer = "Write: " + command
        msg = None

        # Adds SciClops output to response_buffer
        while msg != command:
            # or "success" not in msg or "error" in msg
            try:
                response = self.host_path.read(0x83, 200, timeout=5000)
            except Exception:
                break
            msg = "".join(chr(i) for i in response)
            response_buffer = response_buffer + "Read: " + msg

        print(response_buffer)

        self.success_count = self.success_count + response_buffer.count("0000 Success")

        self.get_error(response_buffer)

        return response_buffer

    def get_error(self, response_buffer=None):
        """
        Gets error message from the feedback.
        """

        if not response_buffer:
            return

        output_line = response_buffer[response_buffer[:-1].rfind("\n") :]
        exp = r"(\d)(\d)(\d)(\d)(.*\w)"  # Format of feedback that indicates an error message
        output_line = re.search(exp, response_buffer)

        try:
            # Checks if specified format is found in the last line of feedback
            if output_line[5][5:9] != "0000":
                self.ERROR = "ERROR: %s" % output_line[5]

        except Exception:
            pass

    ################################
    # Individual Command Functions

    def get_position(self):
        """
        Requests and stores sciclops position.
        Coordinates:
        Z: Vertical axis
        R: Base turning axis
        Y: Extension axis
        P: Gripper turning axis
        """

        command = "GETPOS\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"Z:([-.\d]+), R:([-.\d]+), Y:([-.\d]+), P:([-.\d]+)"  # Format of coordinates provided in feedback
            find_current_pos = re.search(exp, out_msg)
            self.current_pos = [
                float(find_current_pos[1]),
                float(find_current_pos[2]),
                float(find_current_pos[3]),
                float(find_current_pos[4]),
            ]

            print(self.current_pos)
        except Exception:
            pass

    def get_status(self):
        """
        Checks status of Sciclops
        """

        command = "STATUS\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the status
            find_status = re.search(exp, out_msg)
            self.status = find_status[1]

            print(self.status)

        except Exception:
            pass

    async def check_complete(self):
        """
        Checks to see if current sciclops action has completed
        """
        print("Checking if complete")
        command = "STATUS\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the status
            find_status = re.search(exp, out_msg)
            self.status = find_status[1]
            self.movement_state = "READY"

            return True

        except Exception:
            self.movement_state = "BUSY"

            return False
        finally:
            await asyncio.sleep(0.1)

    async def check_complete_loop(self):
        """
        continuously runs check_complete until it returns True
        """
        a = False
        while not a:
            a = await self.check_complete()

        print("ACTION COMPLETE")

    def get_version(self):
        """
        Checks version of Sciclops
        """

        command = "VERSION\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the version
            find_version = re.search(exp, out_msg)
            self.VERSION = find_version[1]

            print(self.VERSION)

        except Exception:
            pass

    # TODO: swings outward and collides with pf400
    def reset(self):
        """
        Resets Sciclops
        """

        self.set_speed(5)

        command = "RESET\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the version
            find_reset = re.search(exp, out_msg)
            self.RESET = find_reset[1]

            print(self.RESET)

        except Exception:
            pass

    def get_config(self):
        """
        Checks configuration of Sciclops
        """

        command = "GETCONFIG\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the configuration
            find_config = re.search(exp, out_msg)
            self.CONFIG = find_config[1]

            print(self.CONFIG)

        except Exception:
            pass

    def get_grip_length(self):
        """
        Checks current length of the gripper (units unknown) of Sciclops
        """

        command = "GETGRIPPERLENGTH\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the gripper length
            find_grip_length = re.search(exp, out_msg)
            self.griplength = find_grip_length[1]

            print(self.griplength)

        except Exception:self.labware[location]
    

        command = "GETCOLLAPSEDISTANCE\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the collapsed distance
            find_collapsed_distance = re.search(exp, out_msg)
            self.COLLAPSEDDISTANCE = find_collapsed_distance[1]

            print(self.COLLAPSEDDISTANCE)

        except Exception:
            pass

    def get_steps_per_unit(self):
        """
        ???
        """

        command = "GETSTEPSPERUNIT\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"Z:([-.\d]+),R:([-.\d]+),Y:([-.\d]+),P:([-.\d]+)"  # Format of the coordinates provided in feedback
            find_steps_per_unit = re.search(exp, out_msg)
            self.STEPSPERUNIT = [
                float(find_steps_per_unit[1]),
                float(find_steps_per_unit[2]),
                float(find_stepsGET_per_unit[3]),
                float(find_steps_per_unit[4]),
            ]

            print(self.STEPSPERUNIT)

        except Exception:
            pass

    def home(self, axis=""):
        """
        Homes all of the axes. Returns to neutral position (above exchange)
        """

        # Moves axes to home position
        command = "HOME\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the success message
            home_msg = re.search(exp, out_msg)
            self.HOMEMSG = home_msg[1]

            print(self.HOMEMSG)
        except Exception:
            pass

        # Moves axes to neutral position (above exchange)
        

    def open(self):
        """
        Opens gripper
        """

        command = "OPEN\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the success message
            open_msg = re.search(exp, out_msg)
            self.OPENMSG = open_msg[1]
            print(self.OPENMSG)

        except Exception:
            pass

    def close(self):
        """
        Closes gripper
        """

        command = "CLOSE\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line is the success message
            close_msg = re.search(exp, out_msg)
            self.CLOSEMSG = close_msg[1]

            print(self.CLOSEMSG)
        except Exception:
            pass

    def check_open(self):
        """
        Checks if gripper is open
        """

        command = "GETGRIPPERISOPEN\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line answers if the gripper is open
            check_open_msg = re.search(exp, out_msg)
            self.CHECKOPENMSG = check_open_msg[1]

            print(self.CHECKOPENMSG)
        except Exception:
            pass

    def check_closed(self):
        """
        Checks if gripper is closed
        """

        command = "GETGRIPPERISCLOSED\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates that the rest of the line answers if the gripper is closed
            check_closed_msg = re.search(exp, out_msg)
            self.CHECKCLOSEDMSG = check_closed_msg[1]

            print(self.CHECKCLOSEDMSG)

        except Exception:
            pass

    def check_plate(self):
        """
        ???
        """

        command = "GETPLATEPRESENT\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates ???
            check_plate_msg = re.search(exp, out_msg)
            self.CHECKPLATEMSG = check_plate_msg[1]

            print(self.CHECKPLATEMSG)

        except Exception:
            pass

    def set_speed(self, speed):
        """
        Changes speed of Sciclops
        """

        command = "SETSPEED %d\r\n" % speed  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            exp = r"0000 (.*\w)"  # Format of feedback that indicates success message
            set_speed_msg = re.search(exp, out_msg)
            self.SETSPEEDMSG = set_speed_msg[1]
            print(self.SETSPEEDMSG)
        except Exception:
            pass

    def list_points(self):
        """
        Lists all of the preset points
        """

        command = "LISTPOINTS\r\n"  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            list_point_msg_index = out_msg.find(
                "0000"
            )  # Format of feedback that indicates success message
            self.LISTPOINTS = out_msg[list_point_msg_index + 4 :]
            print(self.LISTPOINTS)
        except Exception:
            pass

    def jog(self, axis, distance):
        """
        Moves the specified axis the specified distance.
        """

        command = "JOG %s,%d\r\n" % (axis, distance)  # Command interpreted by Sciclops
        out_msg = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            jog_msg_index = out_msg.find(
                "0000"
            )  # Format of feedback that indicates success message
            self.JOGMSG = out_msg[jog_msg_index + 4 :]
            print(self.JOGMSG)
        except Exception:
            pass

    def loadpoint(self, R, Z, P, Y):
        """
        Adds point to listpoints function
        """

        command = "LOADPOINT R:%s, Z:%s, P:%s, Y:%s, R:%s\r\n" % (
            R,
            Z,
            P,
            Y,
            R,
        )  # Command interpreted by Sciclops
        out_msg = self.send_command(command)
        try:
            # Checks if specified format is found in feedback
            loadpoint_msg_index = out_msg.find(
                "0000"
            )  # Format of feedback that indicates success message
            self.LOADPOINTMSG = out_msg[loadpoint_msg_index + 5 :]
        except Exception:
            pass

    def deletepoint(self, R, Z, P, Y):
        """
        Deletes point from listpoints function
        """

        command = "DELETEPOINT R:%s\r\n" % R  # Command interpreted by Sciclops
        out_msg = self.send_command(command)
        try:
            deletepoint_msg_index = out_msg.find(
                "0000"
            )  # Format of feedback that indicates success message
            self.DELETEPOINTMSG = out_msg[deletepoint_msg_index + 5 :]
        except Exception:
            pass

    def move(self, R, Z, P, Y):
        """
        Moves to specified coordinates
        """

        self.loadpoint(R, Z, P, Y)

        command = "MOVE R:%s\r\n" % R
        out_msg_move = self.send_command(command)

        try:
            # Checks if specified format is found in feedback
            move_msg_index = out_msg_move.find(
                "0000"
            )  # Format of feedback that indicates success message
            self.MOVEMSG = out_msg_move[move_msg_index + 4 :]
        except Exception:
            pass

        self.deletepoint(R, Z, P, Y)
        
    def move_neutral(self):
        self.move(
            R=self.neutral_joints["R"],
            Z=self.neutral_joints["Z"],
            P=self.neutral_joints["P"],
            Y=self.neutral_joints["Y"],
        )
    def get_plate(self, source, target):
        """
        Grabs plate and places on exchange. Paramater is the stack that the Sciclops is requested to remove the plate from.
        Format: "Stack<num>"
        remove lid and trash bools tell whether to remove lid from plate and whether to throw said lid in the trash or place in nest
        """

        # check to see if plate already on the exchange
        # removed for now until labware can be  edited in a file
        # if self.labware['exchange']['howmany'] != 0:
        #     print("PLATE ALREADY ON THE EXCHANGE")
        # else:
        plate_type = "96_well"
        # Move arm up and to neutral position to avoid hitting any objects
        self.open()
        self.set_speed(10)  #
        self.jog("Y", -1000)
        self.jog("Z", 1000)
        self.set_speed(12)
        self.move_neutral

        # check coordinates
        asyncio.run(self.check_complete_loop())

        # Move above desired tower
        self.set_speed(100)
        self.move(
            R=source.location["R"],
            Z=23.5188,
            P=source.location["P"],
            Y=source.location["Y"],
        )
        # check coordinates
        asyncio.run(self.check_complete_loop())

        # Remove plate from towertower_info["type"]
        self.close()
        self.set_speed(15)
        self.jog("Z", -1000)
        # move up certain amount
        self.jog("Z", 10)
        self.open()
        grab_height = self.plate_info[plate_type]["grab_tower"]
        self.jog("Z", grab_height)
        self.close()
        plate, _ = self.resource_client.pop(source.resource_id)
        self.resource_client.push(self.gripper_id, plate)
        self.set_speed(100)
        self.jog("Z", 1000)
        # check coordinates
        # asyncio.run(self.check_complete_loop())

        # Place in exchange
        self.move(
            R=target.location["R"],
            Z=23.5188,
            P=target.location["P"],
            Y=target.location["Y"],
        )
        # check coordinates
        # asyncio.run(self.check_complete_loop())
        self.jog("Z", -380)
        self.set_speed(5)
        self.jog("Z", -30)
        self.open()
        plate, _ = self.resource_client.pop(self.gripper_id)
        self.resource_client.push(target.resource_id, plate)
        self.set_speed(100)
        self.jog("Z", 1000)
        # check coordinates
        # asyncio.run(self.check_complete_loop())
        # check if lid needs to be removed
        # Move back to neutral
        self.move_neutral()
        # check coordinates
        # asyncio.run(self.check_complete_loop())

    def limp(self, limp_bool):
        """
        Turns on/off limp mode (allows someone to manually move joints)
        """
        if limp_bool:
            limp_string = "FALSE"
        else:
            limp_string = "TRUE"
        command = "LIMP %s" % limp_string  # Command interpreted by Sciclops
        self.send_command(command)


    def plate_to_stack(self, tower, add_lid):
        """Plate from exchange to stack (self, tower, plateinfo)"""
        # Move arm up and to neutral position to avoid hitting any objects
        self.open()
        self.set_speed(10)
        self.jog("Y", -1000)
        self.jog("Z", 1000)
        self.set_speed(12)
        self.move(
            R=self.labware["neutral"]["pos"]["R"],
            Z=23.5188,
            P=self.labware["neutral"]["pos"]["P"],
            Y=self.labware["neutral"]["pos"]["Y"],
        )
        asyncio.run(self.check_complete_loop())
        plate_type = self.labware["exchange"]["type"]
        if add_lid:
            self.check_for_lid()
            self.replace_lid()

        # TODO: check to see if given stack is full, use function to account for different labware, maybe checks all stacks to find one with same labware?

        # move over exchange
        self.open()
        self.move(
            R=self.labware["exchange"]["pos"]["R"],
            Z=23.5188,
            P=self.labware["exchange"]["pos"]["P"],
            Y=self.labware["exchange"]["pos"]["Y"],
        )
        # check coordinates
        asyncio.run(self.check_complete_loop())
        # grab plate
        self.set_speed(100)
        self.jog("Z", -380)
        grab_height = self.plate_info[plate_type]["grab_exchange"]
        self.jog("Z", grab_height)
        self.close()
        self.set_speed(100)
        self.jog("Z", 1000)
        asyncio.run(self.check_complete_loop())

        # move above tower, place plate in tower
        self.move(
            R=self.labware[tower]["pos"]["R"],
            Z=23.5188,
            P=self.labware[tower]["pos"]["P"],
            Y=self.labware[tower]["pos"]["Y"],
        )
        # check coordinates
        asyncio.run(self.check_complete_loop())
        self.set_speed(10)
        self.jog("Z", -1000)
        self.open()
        self.set_speed(100)
        self.jog("Z", 1000)
        # check coordinates
        asyncio.run(self.check_complete_loop())

        # move to home
        self.move(
            R=self.labware["neutral"]["pos"]["R"],
            Z=23.5188,
            P=self.labware["neutral"]["pos"]["P"],
            Y=self.labware["neutral"]["pos"]["Y"],
        )
        # check coordinates
        asyncio.run(self.check_complete_loop())

        # update labware dict
        self.labware["exchange"]["howmany"] -= 1
        self.labware[tower]["howmany"] += 1



   