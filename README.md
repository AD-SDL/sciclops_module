# sciclops_module

A MADSci Node module for interfacing with the Hudson Robotics Sciclops Platecrane.

## Installation and Usage

### Python

```bash
# Create a virtual environment named .venv
python -m venv .venv
# Activate the virtual environment on Linux or macOS
source .venv/bin/activate
# Alternatively, activate the virtual environment on Windows
# .venv\Scripts\activate
# Install the module and dependencies in the venv
pip install .
# Run the environment
python -m sciclops_rest_node --host 127.0.0.1 --port 2000
```

### Docker

- We provide a `Dockerfile` and example docker compose file (`compose.yaml`) to run this node dockerized.
- There is also a pre-built image available as `ghcr.io/ad-sdl/sciclops_module`.
- You can control the container user's id and group id by setting the `USER_ID` and `GROUP_ID`

## Host setup: USB device permissions

The SciClops talks over raw USB via `libusb` / `pyusb` (vendor `0x7513`, product `0x0002`). By default, `/dev/bus/usb/*` device nodes for it are owned `root:root` with mode `0664`, which means a non-root user — including the `madsci` user inside the container — cannot open them, even with `privileged: true`. The container will fail at startup with `USBError: [Errno 13] Access denied (insufficient permissions)`.

Fix it with a udev rule on the host that grants the `dialout` group access to the device. The container image puts `madsci` in `dialout` (both Ubuntu GID 20 and Fedora GID 18) so this works on either distro:

```bash
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="7513", ATTRS{idProduct}=="0002", MODE="0660", GROUP="dialout"' \
  | sudo tee /etc/udev/rules.d/60-hudson-sciclops.rules
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=usb --attr-match=idVendor=7513
```

Verify (the bus/device path will vary — `lsusb | grep 7513` shows the current location):

```bash
$ ls -l /dev/bus/usb/003/012
crw-rw----. 1 root dialout 189, 267 May 27 12:05 /dev/bus/usb/003/012
```

The compose service should bind-mount the entire USB bus tree so device renumbering on reconnect doesn't require an edit:

```yaml
sciclops_plankton:
  image: ghcr.io/ad-sdl/sciclops_module
  privileged: true
  volumes:
    - /dev/bus/usb:/dev/bus/usb
```
