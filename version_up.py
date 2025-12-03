import nuke
import nukescripts
import os

def run():
    """
    現在のスクリプトを保存し、バージョン番号を繰り上げて別名保存する。
    例: shot_v001.nk -> shot_v002.nk
    """
    # 1. 保存されていないスクリプト（Root）の場合は警告
    if nuke.root().name() == 'Root':
        nuke.message("Error: Script is not saved yet.\nPlease use 'Make Official' first.")
        return

    # 2. 現在の状態をまず上書き保存 (安全のため)
    nuke.scriptSave()
    
    # 3. バージョンアップ処理
    try:
        nukescripts.script_version_up()
        
    except Exception as e:
        nuke.message(f"Version Up Failed:\n{e}")