#ubuntu:22.04
FROM pytorch/pytorch:2.9.0-cuda12.8-cudnn9-devel

LABEL maintainer="Sean@comfyui-docker"

ARG COMFY_VERSION=0.3.75

#  For fixing ImportError: libGL.so.1 libgthread2.0.so
COPY ComfyUI/sources.list /etc/apt/sources.list
RUN apt update && apt install -y libgl1 libglib2.0-0 git pkg-config libcairo2-dev
# ffmpeg dependencies
RUN apt install -y ffmpeg libavformat-dev libavcodec-dev libavdevice-dev \
    libavutil-dev libavfilter-dev libswscale-dev libswresample-dev

RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple

# add comfyui and configure python env
ADD ComfyUI/ComfyUI-${COMFY_VERSION}.tar.gz /workspace/
RUN mv /workspace/ComfyUI-${COMFY_VERSION} /workspace/ComfyUI
WORKDIR /workspace/ComfyUI
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# add comfyui plugins and configure dependencies
COPY plugins/plugins /workspace/ComfyUI/custom_nodes/
COPY plugins/requirements.txt /workspace/ComfyUI/custom_nodes/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /workspace/ComfyUI/custom_nodes/requirements.txt

ENTRYPOINT [ "python", "main.py", "--listen", "0.0.0.0" ]








