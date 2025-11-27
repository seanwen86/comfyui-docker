Build ComfyUI images for running on Docker. Based on Ubuntu Linux and Pytorch, ComfyUI is configured with plugins and models satisfying OFFICIAL workflow templates. 

### Usage
1. download plugins, `python clone_or_update_plugins.py` 
2. build docker image, `docker build -t sean/comfy:latest .`
3. download models for official workflows, `python download_models.py`
4. `docker run -d --gpus all -p 8188:8188 -v path_to/models:/workspace/ComfyUI/models sean/comfy:latest`


### TODOs
1. Additional plugins and models are also collected and kept up-to-date. Supported plugins and the corresponding compatible virtual environment are provided.
