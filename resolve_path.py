import nuke
import os
import config

def convert_to_env_absolute():
    """
    [Flux Path Resolver]
    選択したノードのファイルパスを、環境変数 FLUX_ROOT を使用した絶対パス形式に変換します。
    
    変換前: D:/Studio/WIP/private/TMP/shot010/plates/plate_v01.exr
    変換後: [getenv FLUX_ROOT]/private/TMP/shot010/plates/plate_v01.exr
    """
    
    # 環境変数 FLUX_ROOT がない場合は config から取得を試みる
    flux_root = os.environ.get('FLUX_ROOT', config.BASE_ROOT)
    
    if not flux_root:
        nuke.message("Error: FLUX_ROOT environment variable is not set.")
        return

    # パス区切り文字の統一
    flux_root = flux_root.replace('\\', '/')
    
    nodes = nuke.selectedNodes()
    if not nodes:
        nuke.message("Please select nodes (Read/Write/etc).")
        return

    count = 0
    
    for node in nodes:
        # ファイルパスを持つKnobを探す (file, proxyなど)
        for knob_name in ['file', 'proxy']:
            if knob_name not in node.knobs():
                continue
                
            knob = node[knob_name]
            current_path = knob.value()
            if not current_path:
                continue
                
            # パスの正規化
            normalized_path = current_path.replace('\\', '/')
            
            # 既に環境変数を使っているかチェック
            if '[getenv FLUX_ROOT]' in normalized_path:
                continue
            
            # パスが FLUX_ROOT で始まっているかチェック
            # 大文字小文字を無視して比較
            if normalized_path.lower().startswith(flux_root.lower()):
                # 置換処理
                # D:/Studio/WIP/abc... -> [getenv FLUX_ROOT]/abc...
                # flux_root の長さを取得してスライス
                rel_part = normalized_path[len(flux_root):]
                
                # 先頭のスラッシュ調整
                if rel_part.startswith('/'):
                    rel_part = rel_part[1:]
                    
                new_path = f"[getenv FLUX_ROOT]/{rel_part}"
                knob.setValue(new_path)
                count += 1

    if count > 0:
        nuke.message(f"Updated {count} paths to use [getenv FLUX_ROOT].\n(Absolute path via Environment Variable)")
    else:
        nuke.message("No paths needed updating.\n(Ensure your files are inside the FLUX_ROOT folder)")