Build ComfyUI images for running on Docker. Based on Ubuntu Linux and Pytorch, ComfyUI is configured with plugins and models satisfying OFFICIAL workflow templates. 

### Simple Usage
1. pull the latest image from DockerHub: `docker pull seanwen86/comfyui`, or with specific tag
2. download models: `python download_models.py`
3. run: `docker run -d --gpus all -p 8188:8188 -v path_to/models:/workspace/ComfyUI/models seanwen86/comfyui:latest`
4. visit comfyui via web browser: `127.0.0.1:8188` 

### Development Guide
go to [development_guide.md](./tutorials/development_guide.md)


### TODOs
1. Additional plugins and models are also collected and kept up-to-date. Supported plugins and the corresponding compatible virtual environment are provided.


### Contribution
1. add popular models
2. add popular plugins, and compatible python environment

### Hints
1. If downloading some models from HuggingFace fails, you can try your luck at [ModelScope](https://modelscope.cn/models).
