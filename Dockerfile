FROM ghcr.io/ad-sdl/madsci

LABEL org.opencontainers.image.source=https://github.com/AD-SDL/hudson_platecrane_module
LABEL org.opencontainers.image.description="Drivers and REST API's for the Hudson Platecrane and Sciclops robots"
LABEL org.opencontainers.image.licenses=MIT

#########################################
# Module specific logic goes below here #
#########################################

RUN apt update && apt install -y libusb-1.0-0-dev && rm -rf /var/lib/apt/lists/*

RUN mkdir -p sciclops_module

COPY ./src sciclops_module/src
COPY ./README.md sciclops_module/README.md
COPY ./pyproject.toml sciclops_module/pyproject.toml

RUN --mount=type=cache,target=/root/.cache \
    pip install -e ./sciclops_module

RUN usermod -aG dialout madsci

CMD ["python", "-,", "sciclops_rest_node"]
#########################################
