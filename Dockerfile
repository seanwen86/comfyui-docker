#ubuntu:24.04, python 3.12, pytorch:2.10.0, cuda13.0, cudatoolkit-13.0
# for ARCH x86_64/amd64 only
ARG BASE_IMAGE=ubuntu:24.04
FROM ${BASE_IMAGE} AS base

LABEL author="Sean"

ARG COMFYUI_VERSION=0.12.3
ARG PYTHON_VERSION=python3.12

# latest cuda version 13.1, NVIDIA GPU driver should support it
# to check using nvidia-smi 
ARG CUDA_TOOLKIT_VERSION=cuda-toolkit-13-1
ARG CUDNN_VERSION=cudnn9-cuda-13-1

# lower version of cuda for pytorch than that for system is allowed. 
# for example, cuda 13.0 for pytorch against cuda 13.1 for system
ARG PYTORCH_CUDA_VERSION=cu130
ARG CUDA_DISTRO=ubuntu2404
ARG CUDA_ARCH=x86_64

ARG CUDA_TOOLKIT_URL=https://developer.download.nvidia.cn/compute/cuda/repos/${CUDA_DISTRO}/${CUDA_ARCH}
ARG PIP_MIRROR_URL=https://mirrors.aliyun.com/pypi/simple

# required python and runtimes for comfyui plugins
# For fixing ImportError: libGL.so.1 libgthread2.0.so libOpenGL.so.0
COPY ComfyUI/ubuntu.sources /etc/apt/sources.list.d/ubuntu.sources
RUN apt update && DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends \ 
    python3 python3-pip python-is-python3 \
    libglib2.0-0 libgl1 libopengl0 libcairo2 ffmpeg \
    && apt clean && rm -rf /var/lib/apt/lists/*

#avoid error: externally-managed-environment, (safe in containers)
#or by passing --break-system-packages when pip install
RUN rm -f /usr/lib/python*/EXTERNALLY-MANAGED
RUN pip config set global.index-url ${PIP_MIRROR_URL}

WORKDIR /workspace

ENTRYPOINT ["bash"]

FROM base AS devel

# required tools and additional dependencies for development
RUN apt update && DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends \ 
    build-essential git pkg-config wget gnupg2 ca-certificates \    
    python3-dev \
#    libcairo2-dev libavformat-dev libavcodec-dev libavdevice-dev \
#    libavutil-dev libavfilter-dev libswscale-dev libswresample-dev \
    && apt clean && rm -rf /var/lib/apt/lists/*

# pytorch
COPY ComfyUI/constraints.txt /workspace/constraints.txt
RUN --mount=type=cache,id=pip-cache,target=/root/.cache/pip \
    pip install torch torchaudio torchvision \
    --index-url https://download.pytorch.org/whl/${PYTORCH_CUDA_VERSION} \
    --constraint /workspace/constraints.txt \
    && pip cache purge

# cuda toolkit for building comfyui plugins
# NO EFFECT??, --mount=type=cache,id=apt-cache,target=/var/cache/apt/archives
RUN wget -q  ${CUDA_TOOLKIT_URL}/cuda-keyring_1.1-1_all.deb \ 
    && dpkg -i cuda-keyring_1.1-1_all.deb \
    && apt update && DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends \ 
    ${CUDA_TOOLKIT_VERSION} ${CUDNN_VERSION} \
    && apt clean && rm -rf /var/lib/apt/lists/* /workspace/cuda-keyring_1.1-1_all.deb

# Set CUDA environment (always set, needed even if CUDA already)
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV CUDA_HOME=/usr/local/cuda
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH:-}
ENV PATH=${CUDA_HOME}/bin:${PATH:-}

# add comfyui and its dependencies
ADD ComfyUI/ComfyUI-${COMFYUI_VERSION}.tar.gz /workspace/
RUN mv /workspace/ComfyUI-${COMFYUI_VERSION} /workspace/ComfyUI
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /workspace/ComfyUI/requirements.txt \
    --constraint /workspace/constraints.txt \
    && pip cache purge

# add comfyui plugins and their dependencies
COPY plugins/plugins /workspace/ComfyUI/custom_nodes/
COPY plugins/requirements.txt /workspace/ComfyUI/custom_nodes/requirements.txt
RUN --mount=type=cache,id=pip-cache,target=/root/.cache/pip \
    pip install --no-build-isolation -r /workspace/ComfyUI/custom_nodes/requirements.txt \
    --constraint /workspace/constraints.txt \
    && pip cache purge
RUN rm -rf /workspace/constraints.txt \
    /workspace/ComfyUI/custom_nodes/requirements.txt

ENTRYPOINT [ "python", "/workspace/ComfyUI/main.py", "--listen", "0.0.0.0" ]

FROM base AS release

COPY --from=devel /usr/local/lib/${PYTHON_VERSION}/dist-packages \
    /usr/local/lib/${PYTHON_VERSION}/dist-packages
COPY --from=devel /workspace/ComfyUI /workspace/ComfyUI

ENTRYPOINT [ "python", "/workspace/ComfyUI/main.py", "--listen", "0.0.0.0" ]


# docker build --target devel -t seanwen86/comfyui:devel . --load
# docker build --target release -t seanwen86/comfyui:release . --load