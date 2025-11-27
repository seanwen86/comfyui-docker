import argparse
import json
import os
import requests
from tqdm import tqdm
from pathlib import Path

_cur_dir = Path(__file__).parent

#  export HF_ENDPOINT="hf-mirror.com"
hf_endpoint = os.environ.get('HF_ENDPOINT', '')

def download_model(url, save_path):
    """下载单个模型文件并显示进度条"""
    
    try:
        # 发送GET请求，流式传输
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()  # 检查请求是否成功
        
        # 获取文件总大小
        file_size = int(response.headers.get('content-length', 0))
        
        # 开始下载并显示进度
        with open(save_path, 'wb') as file, tqdm(
            desc=os.path.basename(save_path),
            total=file_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as progress_bar:
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                progress_bar.update(size)
        
        return True
    except (Exception, KeyboardInterrupt) as e:
        print(f"下载失败 or Exit {os.path.basename(save_path)}: {str(e)}")
        # 下载失败时删除可能的不完整文件
        if os.path.exists(save_path):
            os.remove(save_path)
        return False

def main(json_file_path,save_dir:Path):
    """主函数: 读取JSON并下载所有模型"""
    # 读取JSON文件
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            models = json.load(f)
    except Exception as e:
        print(f"无法读取JSON文件: {str(e)}")
        return
    
    # 遍历所有模型并下载
    for model_id, model_info in models.items():
        try:
            # 提取模型信息
            name = model_info['name']
            url = model_info['url']
            directory = model_info['directory']

            # print(name, url, directory)
            
            # 创建保存目录
            sub_dir = Path(save_dir / directory)
            print(f"保存目录: {sub_dir}")
            sub_dir.mkdir(parents=True, exist_ok=True)

            
            # 构建保存路径
            save_path = sub_dir / name
            
            # 检查文件是否已存在
            if save_path.exists():
                print(f"文件已存在，跳过: {save_path}")
                continue
            
            if hf_endpoint and "huggingface.co" in url:
                url = url.replace("huggingface.co", hf_endpoint)
                
            # 下载文件
            print(f"开始下载: {name} from {url}")
            if download_model(url, save_path):
                print(f"成功下载: {save_path}\n")
                
        except KeyError as e:
            print(f"模型信息不完整 {model_id}: 缺少 {str(e)} 字段")
        except Exception as e:
            print(f"处理模型 {model_id} 时出错: {str(e)}")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="download models")
    parser.add_argument(
        "--models",
        type=Path,
        default=_cur_dir/'models.json'
    )
    parser.add_argument(
        "--save_dir",
        type=Path,
        default=_cur_dir/'models'
    )
    args = parser.parse_args()

    save_dir = args.save_dir
    json_file = args.models

    
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 检查JSON文件是否存在
    if not os.path.exists(json_file):
        print(f"cannot find json file: {json_file}")
    else:
        print(f"downloading, {len(json.load(open(json_file)))} files in total")
        main(json_file, save_dir)
        print("all downloads done")
