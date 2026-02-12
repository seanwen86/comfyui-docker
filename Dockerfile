#ubuntu:24.04.2, python 3.12.3, pip&uv
FROM pytorch/pytorch:2.10.0-cuda13.0-cudnn9-devel

LABEL author="Sean"

ARG COMFY_VERSION=0.12.3

#  For fixing ImportError: libGL.so.1 libgthread2.0.so libOpenGL.so.0
COPY ComfyUI/ubuntu.sources /etc/apt/sources.list.d/ubuntu.sources
RUN apt update && apt install -y libgl1 libglib2.0-0 git pkg-config libcairo2-dev \ 
    libopengl0
# ffmpeg dependencies
RUN apt install -y ffmpeg libavformat-dev libavcodec-dev libavdevice-dev \
    libavutil-dev libavfilter-dev libswscale-dev libswresample-dev

#avoid error: externally-managed-environment, 
#or by passing --break-system-packages when pip install
RUN mv /usr/lib/python3.12/EXTERNALLY-MANAGED /usr/lib/python3.12/EXTERNALLY-MANAGED.bak
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple

# add comfyui and configure python env
ADD ComfyUI/ComfyUI-${COMFY_VERSION}.tar.gz /workspace/
RUN mv /workspace/ComfyUI-${COMFY_VERSION} /workspace/ComfyUI
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /workspace/ComfyUI/requirements.txt

# add comfyui plugins and configure dependencies
COPY plugins/plugins /workspace/ComfyUI/custom_nodes/
COPY plugins/requirements.txt /workspace/ComfyUI/custom_nodes/requirements.txt
COPY plugins/constraints.txt /workspace/ComfyUI/custom_nodes/constraints.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /workspace/ComfyUI/custom_nodes/requirements.txt \
    --constraint /workspace/ComfyUI/custom_nodes/constraints.txt
RUN rm -rf /workspace/ComfyUI/custom_nodes/constraints.txt \
    /workspace/ComfyUI/custom_nodes/requirements.txt
    
ENTRYPOINT [ "python", "/workspace/ComfyUI/main.py", "--listen", "0.0.0.0" ]








