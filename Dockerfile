FROM ghcr.io/ad-sdl/madsci:v0.8.0

LABEL org.opencontainers.image.source=https://github.com/AD-SDL/hudson_platecrane_module
LABEL org.opencontainers.image.description="Drivers and REST API's for the Hudson Platecrane and Sciclops robots"
LABEL org.opencontainers.image.licenses=MIT

#########################################
# Module specific logic goes below here #
#########################################

USER root
RUN apt-get update && apt-get install -y libusb-1.0-0-dev && rm -rf /var/lib/apt/lists/*

RUN mkdir -p sciclops_module

COPY ./src sciclops_module/src
COPY ./README.md sciclops_module/README.md
COPY ./pyproject.toml sciclops_module/pyproject.toml

RUN --mount=type=cache,target=/root/.cache \
    uv pip install --python ${MADSCI_VENV}/bin/python -e ./sciclops_module

# Cross-distro serial access (driver uses libusb, but module also pulls in pyserial
# and the historical image gave madsci dialout — keep parity with peeler/sealer):
#   Ubuntu hosts: dialout = GID 20.
#   Fedora hosts: dialout = GID 18 (added as `dialout_fedora`).
RUN usermod -aG dialout madsci && \
    groupadd -g 18 dialout_fedora && \
    usermod -aG dialout_fedora madsci

CMD ["python", "sciclops_module/src/sciclops_rest_node.py"]

#########################################
