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
    明示的にコンテキストを設定する（Make Officialなどで使用）
    """
    if project: os.environ[ENV_KEY_PROJECT] = project
    if seq:     os.environ[ENV_KEY_SEQ] = seq
    if shot:    os.environ[ENV_KEY_SHOT] = shot
    
    # ログ出力（確認用）
    print(f"[Flux Env] Context Set: {project} / {seq} / {shot}")

def update_env_from_script():
    """
    現在のNukeスクリプトのパスからコンテキストを推測し、環境変数を更新する。
    スクリプトが開かれたタイミングで実行されることを想定。
    """
    script_path = nuke.root().name()
    if script_path == 'Root':
        return

    # パス区切り文字の統一
    script_path = script_path.replace('\\', '/')
    
    # パターンマッチング (configの構造依存だが、ここでは標準的な構造を想定)
    # 想定構造: .../Project/ShotName/scripts/filename.nk
    # ShotName例: TMP_101_010
    
    try:
        # scriptsフォルダの親ディレクトリをショット名とする簡易ロジック
        script_dir = os.path.dirname(script_path)
        shot_dir = os.path.dirname(script_dir)
        project_dir = os.path.dirname(shot_dir)
        
        shot_name = os.path.basename(shot_dir)
        project_name = os.path.basename(project_dir)
        
        # ショット名からSeq番号などを抽出 (例: PRJ_101_010)
        parts = shot_name.split('_')
        if len(parts) >= 3:
            seq_num = parts[1]
        else:
            seq_num = ""

        # 環境変数をセット
        os.environ[ENV_KEY_PROJECT] = project_name
        os.environ[ENV_KEY_SEQ] = seq_num
        os.environ[ENV_KEY_SHOT] = shot_name
        
        # ROOTもセット (Projectのさらに上)
        root_dir = os.path.dirname(project_dir)
        os.environ[ENV_KEY_ROOT] = root_dir

        print(f"[Flux Env] Auto-detected Context: {project_name} > {shot_name}")

    except Exception as e:
        print(f"[Flux Env] Could not determine context from path: {e}")

def get_context():
    """
    現在の環境変数からコンテキストを取得
    """
    return {
        "root": os.environ.get(ENV_KEY_ROOT, ""),
        "project": os.environ.get(ENV_KEY_PROJECT, ""),
        "seq": os.environ.get(ENV_KEY_SEQ, ""),
        "shot": os.environ.get(ENV_KEY_SHOT, "")
    }