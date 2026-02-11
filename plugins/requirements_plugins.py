# read all requirements.txt in root folder of each plugin, remove duplicate dependencies and version numbers.

import pathlib
import argparse
import json
import subprocess
import sys
import chardet

_cur_dir = pathlib.Path(__file__).parent

def robust_readlines(fullpath):
    try:
        with open(fullpath, "r") as f:
            return f.readlines()
    except:
        encoding = None
        with open(fullpath, "rb") as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']

        if encoding is not None:
            with open(fullpath, "r", encoding=encoding) as f:
                return f.readlines()

        print(f"Failed to recognize encoding for: {fullpath}")
        exit(1)

def collect_requirements(plugins_path:pathlib.Path):
    # get all requirements.txt files in plugins' root folders
    #TODO if there are subfolders in plugins, get all requirements.txt files in subfolders too???
    req_files = [] 
    for dir in plugins_path.iterdir():
        if not dir.is_dir(): 
            continue

        req_files += dir.glob('requirements.txt')
    
    return req_files

def merge_requirements(req_files: list):
    merged_dependencies = []
    merged_src_urls = []

    for file in req_files:
        lines = robust_readlines(file)
        for line in lines:
            line = line.strip()
            if (not line) or line.startswith('#') or ('--extra-index-url' in line) \
                or ('http' in line and '.whl' in line): 
                continue
            line = line.split('#')[0].strip()  # remove inline comments if exists

            if ('git+http' in line) or ('http' in line and ('.zip' in line or '.tar.gz' in line)):
                merged_src_urls.append(line)
                continue

            merged_dependencies.append(line)

    # remove duplicates
    merged_dependencies = list(set(merged_dependencies))
    merged_src_urls = list(set(merged_src_urls))
    merged_dependencies.sort()
    merged_src_urls.sort()
    return merged_dependencies, merged_src_urls

def install_dep(dep:str, mirror:str, constraint_file:str=_cur_dir/'constraints.txt'):

    result = ''
    try:
        cmd = [sys.executable, "-m", "pip", "install", "--constraint", str(constraint_file)]

        if '--no-build-isolation' in dep:
            cmd.append('--no-build-isolation')
            dep = dep.replace('--no-build-isolation', '').strip()
        cmd.append(dep)
        cmd += ["-i", mirror]
        subprocess.check_call(cmd)

    except subprocess.CalledProcessError as e:
        result = f'Error: {e}\n'

    return result

def remove_version_numbers(dependencies: list):
    cleaned_deps = []
    for dep in dependencies:
        
        dep = dep.split('=')[0].strip()
        dep = dep.split('>')[0].strip()
        dep = dep.split('<')[0].strip()
        dep = dep.split('!')[0].strip()
        dep = dep.split('~')[0].strip()
        dep = dep.split('[')[0].strip() #like imageio[ffmpeg]

        # remove lines like triton-windows; sys_platform == 'win32'
        dep = dep.split(';')[0].strip() 
        cleaned_deps.append(dep)

    cleaned_deps = list(set(cleaned_deps))
    cleaned_deps.sort()

    return cleaned_deps


def remap_dependencies(dependencies: list, pip_overrides:pathlib.Path):
    with open(pip_overrides,'r') as f:
        overrides = json.load(f)

    remapped_deps = []
    for dep in dependencies:
        if dep in overrides:
            dep = overrides[dep]
        
        dep.strip()
        if not dep: continue
        
        remapped_deps.append(dep)
    remapped_deps = list(set(remapped_deps))
    remapped_deps.sort()
    return remapped_deps

def main(plugins_path:pathlib.Path, mirror:str, pip_overrides:pathlib.Path, 
         with_version:bool, start:str):

    req_files = collect_requirements(plugins_path)
    merged_deps, merged_src_urls = merge_requirements(req_files)

    if not with_version:
        merged_deps = remove_version_numbers(merged_deps)

    merged_requirements = pathlib.Path(_cur_dir / 'merged_requirements.txt')
    with open(merged_requirements, 'w', encoding='utf-8') as f:
        for dep in merged_deps:
            f.write(f"{dep}\n")
        for url in merged_src_urls:
            f.write(f"{url}\n")
    
    remapped_deps = remap_dependencies(merged_deps, pip_overrides)

    remapped_dep_file = pathlib.Path(_cur_dir / 'remapped_requirements.txt')
    with open(remapped_dep_file, 'w', encoding='utf-8') as f:
        for dep in remapped_deps:
            f.write(f"{dep}\n")
        for url in merged_src_urls:
            f.write(f"{url}\n")


    #TODO: install dependencies using pip, and print the errors if any
    # errors = []
    # for dep in remapped_deps:
    #     if start and start != dep:
    #         continue
    #     start = ''  # reset start to empty after reaching the starting package
        
    #     print(f"安装：{dep} from 镜像 {mirror} ")
    #     error = install_dep(dep, mirror)
    #     if error:
    #         print(f"安装失败：{dep} from 镜像 {mirror} , {error}")
    #         errors.append(error)

    # print(f'\n{errors}')

    # for url in merged_src_urls:
    #     print(f"Installing from source URL: {url}")
    #     error = install_dep(url, mirror)
    #     if error:
    #         print(f"Failed to install from source URL: {url}, {error}")
    #         errors.append(error)
    
             
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Collecting dependencies for all plugins")
    parser.add_argument(
        "--start",
        type=str,
        default='',
        help="Start installing from this package name",
    )
    parser.add_argument(
        "--with-version",
        action='store_true',
        help="Whether to keep version numbers when merging requirements.txt",
    )
    parser.add_argument(
        "--dir",
        type=pathlib.Path,
        default=_cur_dir / 'plugins',
        help="Path to the plugins directory",
    )
    parser.add_argument(
        "--mirror",
        type=str,
        default="https://mirrors.aliyun.com/pypi/simple",
        help="mirror url for pip install",
    )
    parser.add_argument(
        "--overrides",
        type=str,
        default=_cur_dir/"pip_overrides.json",
        help="Path to the pip-overrides.json"
    )
    parser.add_argument(
        "--install",
        action='store_true',
        help="whether to install the dependencies"
    )
    args = parser.parse_args()
    main(args.dir, args.mirror, args.overrides, args.with_version, args.start)
