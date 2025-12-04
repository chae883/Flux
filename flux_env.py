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
    """
    明示的にコンテキストを設定する
    """
    if project: os.environ[ENV_KEY_PROJECT] = project
    if seq:     os.environ[ENV_KEY_SEQ] = seq
    if shot:    os.environ[ENV_KEY_SHOT] = shot
    print(f"[Flux Env] Context Set: {project} / {seq} / {shot}")

def update_env_from_script():
    """
    現在のNukeスクリプトのパスからコンテキストを推測する（正規表現版）。
    想定パス構造: .../Project/ShotName/scripts/filename.nk
    """
    script_path = nuke.root().name()
    if script_path == 'Root':
        return

    # 正規化（Windowsのバックスラッシュ対策）
    path = script_path.replace('\\', '/')
    
    # 正規表現による堅牢なパターンマッチング
    # 構造: (任意のルート)/(プロジェクト名)/(ショット名)/scripts/(スクリプト名)
    # (?P<name>...) は名前付きグループで、後から辞書として取り出せます。
    pattern = r"^(?P<root>.+?)/(?P<project>[^/]+)/(?P<shot>[^/]+)/scripts/.*$"
    
    match = re.match(pattern, path)
    
    if match:
        data = match.groupdict()
        project_name = data['project']
        shot_name = data['shot']
        root_dir = data['root']
        
        # ショット名からSeq番号などを抽出 (例: PRJ_101_010)
        # ここは命名規則依存ですが、標準的な _ 区切りを想定
        parts = shot_name.split('_')
        seq_num = parts[1] if len(parts) >= 3 else ""

        # 環境変数をセット
        os.environ[ENV_KEY_ROOT] = root_dir
        os.environ[ENV_KEY_PROJECT] = project_name
        os.environ[ENV_KEY_SEQ] = seq_num
        os.environ[ENV_KEY_SHOT] = shot_name
        
        print(f"[Flux Env] Auto-detected Context: {project_name} > {shot_name}")
    else:
        # マッチしなかった場合の警告（旧来のディレクトリ構造で作業している場合など）
        print(f"[Flux Env] Warning: Script path does not match standard pipeline structure.\nPath: {path}")

def get_context():
    return {
        "root": os.environ.get(ENV_KEY_ROOT, ""),
        "project": os.environ.get(ENV_KEY_PROJECT, ""),
        "seq": os.environ.get(ENV_KEY_SEQ, ""),
        "shot": os.environ.get(ENV_KEY_SHOT, "")
    }