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

We provide a `Dockerfile` and example docker compose file (`compose.yaml`) to run this node dockerized.

There is also a pre-built image avaible as `ghcr.io/ad-sdl/sciclops_module`.
