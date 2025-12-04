import os
import nuke
import re
import config

# 環境変数のキー定義
ENV_KEY_ROOT = "FLUX_ROOT"
ENV_KEY_PROJECT = "FLUX_PROJECT"
ENV_KEY_SEQ = "FLUX_SEQ"
ENV_KEY_SHOT = "FLUX_SHOT"

def set_global_context(project=None, seq=None, shot=None):
    if project: os.environ[ENV_KEY_PROJECT] = project
    if seq:     os.environ[ENV_KEY_SEQ] = seq
    if shot:    os.environ[ENV_KEY_SHOT] = shot
    print(f"[Flux Env] Context Set: {project} / {seq} / {shot}")

def update_env_from_script():
    """
    コンテキスト解決ロジック。
    1. 既存の環境変数を信頼する (ランチャーから起動された場合など)
    2. なければスクリプトパスから解決を試みる (Regex)
    """
    # 既に環境変数がセットされていれば何もしない (Source of Truth)
    if os.environ.get(ENV_KEY_PROJECT) and os.environ.get(ENV_KEY_SHOT):
        return

    script_path = nuke.root().name()
    if script_path == 'Root':
        return

    path = script_path.replace('\\', '/')
    
    # Regexによる解析: Project/Shot/scripts という並びを探す
    pattern = r"(?P<project>[^/]+)/(?P<shot>[^/]+)/scripts/.*$"
    match = re.search(pattern, path)
    
    if match:
        data = match.groupdict()
        project_name = data['project']
        shot_name = data['shot']
        
        parts = shot_name.split('_')
        seq_num = parts[1] if len(parts) >= 3 else ""

        # 環境変数をセット
        os.environ[ENV_KEY_PROJECT] = project_name
        os.environ[ENV_KEY_SEQ] = seq_num
        os.environ[ENV_KEY_SHOT] = shot_name
        
        # Rootの逆算 (簡易)
        if config.BASE_ROOT:
             os.environ[ENV_KEY_ROOT] = config.BASE_ROOT
        
        print(f"[Flux Env] Auto-detected Context from Path: {project_name} > {shot_name}")
    else:
        print(f"[Flux Env] Warning: Could not detect context from path. Env vars not set.")

def get_context():
    return {
        "root": os.environ.get(ENV_KEY_ROOT, ""),
        "project": os.environ.get(ENV_KEY_PROJECT, ""),
        "seq": os.environ.get(ENV_KEY_SEQ, ""),
        "shot": os.environ.get(ENV_KEY_SHOT, "")
    }