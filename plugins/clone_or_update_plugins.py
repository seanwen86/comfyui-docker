import argparse
import json
import os
from git import Repo
import pathlib
import shutil

_cur_dir = pathlib.Path(__file__).parent



def get_default_branch(repo:Repo):
    
    # 获取远程 origin 的 HEAD 引用（如 'refs/remotes/origin/main'）
    try:
        remote_head = repo.refs['origin/HEAD']
        # 提取分支名，例如从 'origin/main' 得到 'main'
        branch_name = str(remote_head.reference).split('/')[-1]
        return branch_name
    except (IndexError, KeyError, AttributeError):
        # 回退方案：尝试常见分支名
        for candidate in ['main', 'master', 'trunk', 'development']:
            if candidate in repo.remotes.origin.refs:
                return candidate
        # 如果都找不到，返回 None 或抛出异常
        raise RuntimeError("无法确定默认分支名称")


def clone_git_repository(repo_dir, git_url, commit):
        
        if os.path.exists(repo_dir):
            repo = Repo(repo_dir)
            if commit:
                repo.git.checkout(commit)
                repo.git.submodule('update', '--init', '--recursive')
            commit = repo.head.object.hexsha
            print(f"Repository already exists '{repo_dir}', do checkout {commit[:7]}.")
            return commit
        
        try:
            repo = Repo.clone_from(git_url, repo_dir, recursive=True)
            if commit:
                repo.git.checkout(commit)
        except (KeyboardInterrupt,Exception) as e:
            print(f"Failed to clone '{git_url}': {e}")
            shutil.rmtree(repo_dir,ignore_errors=True)  # Clean up partially created directory
            exit(1)

        return repo.head.object.hexsha

def update_git_repository(repo_dir):
    if not os.path.exists(repo_dir):
        print(f"Repository does not exist at '{repo_dir}', cannot pull.")
        return
    
    try:
        repo = Repo(repo_dir)
        branch = get_default_branch(repo)
        repo.git.checkout(branch)
        # origin = repo.remote(name="origin")
        # origin.pull()
        print(f'branch = {branch}')
        repo.remotes.origin.pull()
        repo.git.submodule('update', '--init', '--recursive')
    except (KeyboardInterrupt,Exception) as e:
        print(f"Failed to update '{repo_dir}' branch '{branch}': {e}")
        exit(1)
    
    return repo.head.object.hexsha # latest commit hash


#https://gh-proxy.org or https://hk.gh-proxy.org
gh_endpoint = os.environ.get('GH_ENDPOINT', None)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Process plugin object info")
    parser.add_argument('--file', type=pathlib.Path, default=_cur_dir/'plugins.json', help='the default is plugins.json, or select one from [RH, LIBAI, INTER, UN]')
    parser.add_argument('--type', type=str, default='CLONE', choices=['CLONE', 'UPDATE'], help='the default is plugins.json, or select one from [CLONE, UPDATE]')
    args = parser.parse_args()

    target_directory = _cur_dir/"plugins"
    target_directory.mkdir(exist_ok=True)

    plugins_file = pathlib.Path(args.file)
    plugins = json.loads(plugins_file.read_text(encoding='utf-8'))

    processed_plugins = []
    for plugin in plugins.keys():
        name = plugins[plugin]['name']
        git_url = plugins[plugin]['url']
        commit = plugins[plugin]['commit']

        if not git_url.endswith('.git'):
            git_url = f'{git_url}.git'

        if gh_endpoint and 'github.com' in git_url:
            git_url = f'{gh_endpoint}/{git_url}'

        print(f'plugin = {plugin}')
        print(f'save_path = {target_directory}/{plugin}')
        print(f'url = {git_url}')

        # repo_name = git_url.split("/")[-1]
        # if repo_name.endswith(".git"):
        #     repo_name = repo_name[:-4]
        repo_name = plugin
        repo_dir = os.path.join(target_directory, repo_name)
        if args.type == 'CLONE':
            # for empty commit in plugins.json
            commit = clone_git_repository(repo_dir, git_url, commit)
            plugins[plugin]['commit'] = commit
        elif args.type == 'UPDATE':
            commit = update_git_repository(repo_dir)
            # update to new commit
            plugins[plugin]['commit'] = commit
        else:
           exit(1)
        
        processed_plugins.append(plugin)
        print(f'progress: {len(processed_plugins)}/{len(plugins.keys())}\n')


    unprocessed_plugins = [plugin for plugin in plugins if plugin not in processed_plugins]
    if len(unprocessed_plugins) > 0:
        print('ERROR: unprocessed plugins exists, Checkout generated file: unprocessed_plugins.json')
        with open(_cur_dir/'unprocessed_plugins.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(unprocessed_plugins, ensure_ascii=False, indent=4))

        exit(1)

     
    with open(_cur_dir/'updated_plugins.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(plugins, ensure_ascii=False, indent=4))
    