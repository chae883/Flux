import nuke
import os

def convert_to_relative():
    """
    Smart Relative Path Converter
    
    1. Project Settings > Root > project directory を確認します。
    2. 設定がある場合（例: Script Directoryボタン使用時）
       -> 「../plates/img.exr」のようなシンプルできれいな相対パスに変換します。
    3. 設定がない場合
       -> 「[file dirname [value root.name]]/../plates/img.exr」という安全なTCLパスに変換します。
    
    これにより、プロジェクト設定を活用した可読性の高いパス管理が可能になります。
    """
    
    # 1. スクリプト保存チェック
    script_path = nuke.root().name()
    if script_path == 'Root':
        nuke.message("⚠️ Script not saved!\nPlease save the script first.")
        return

    # 2. 基準ディレクトリ（Base Dir）の決定
    # プロジェクト設定の project_directory を取得して評価（パス文字列にする）
    proj_dir_knob = nuke.root()['project_directory']
    proj_dir_raw = proj_dir_knob.value()
    proj_dir_abs = proj_dir_knob.evaluate()
    
    use_simple_path = False
    base_dir = ""
    
    # プロジェクトディレクトリが有効（空でなく、実在する）なら、そこを基準にする
    if proj_dir_raw and proj_dir_abs:
        use_simple_path = True
        base_dir = proj_dir_abs
    else:
        # 設定がないならスクリプトの場所を基準にする
        use_simple_path = False
        base_dir = os.path.dirname(script_path)

    # パス区切り文字の統一 (Windowsの \ を / に)
    base_dir = os.path.abspath(base_dir).replace('\\', '/')
    
    # 3. ノード処理
    nodes = nuke.selectedNodes()
    if not nodes:
        nuke.message("Please select Read nodes.")
        return

    count = 0
    skipped = 0
    
    # "Dumb"なTCLプレフィックス（除去対象）
    dumb_prefix = "[file dirname [value root.name]]"

    for node in nodes:
        if 'file' not in node.knobs():
            continue
            
        # 現在の値をそのまま取得 (#### などを壊さないため evaluate() は使わない)
        current_val = node['file'].value()
        if not current_val:
            continue
            
        # --- パスの正規化と絶対パス復元 ---
        # 既に "Dumb" 形式になっているものを "Smart" にしたい場合のために、
        # 一度絶対パスっぽい形に戻してから計算する
        
        path_for_calc = current_val.replace('\\', '/')
        
        # もし [file dirname...] が付いていたら、実際のスクリプトパスに置換して計算可能にする
        if dumb_prefix in path_for_calc:
            script_dir = os.path.dirname(script_path).replace('\\', '/')
            path_for_calc = path_for_calc.replace(dumb_prefix, script_dir)
            
        # まだ相対パスなら、絶対パス化を試みる（計算のため）
        if not os.path.isabs(path_for_calc):
            # プロジェクト設定がある前提なら、そこからの相対かもしれない
            if use_simple_path:
                path_for_calc = os.path.join(base_dir, path_for_calc)
            else:
                # 諦めてスキップ（変に触ると壊れるため）
                # ただし、絶対パスなら次の処理へ進む
                if not os.path.exists(path_for_calc): # 実在確認まではしないが、isabs判定用
                     pass 

        # --- 相対パス計算 ---
        try:
            # os.path.relpath で基準ディレクトリからの相対パスを算出
            # 例: "D:/Proj/Shot/plate.mov" from "D:/Proj/Shot/scripts" -> "../plate.mov"
            rel_path = os.path.relpath(path_for_calc, base_dir)
            rel_path = rel_path.replace('\\', '/') # Nukeは / が好き
            
            # --- 新しいパスの生成 ---
            if use_simple_path:
                # スマートモード: そのままの相対パス
                new_path = rel_path
            else:
                # セーフモード: TCLプレフィックスを付ける
                # ただし、rel_path が ../ で始まらない（同階層以下）なら ./ を付けたりするが
                # NukeのTCL結合ならそのままでOK
                new_path = f"{dumb_prefix}/{rel_path}"
            
            # 無駄な更新を避ける
            if node['file'].value() == new_path:
                continue
                
            node['file'].setValue(new_path)
            count += 1
            
        except ValueError:
            # ドライブ文字が違う場合などは相対パスにできないのでスキップ
            skipped += 1

    # 結果表示
    if count > 0:
        msg = f"Updated {count} nodes to Relative Paths!"
        if use_simple_path:
            msg += "\n(Smart Mode: Using Project Directory)"
        else:
            msg += "\n(Safe Mode: Using Script Directory TCL)"
        nuke.message(msg)
    elif skipped > 0:
        nuke.message(f"Skipped {skipped} nodes.\n(Different drive or cannot calculate relative path)")
    else:
        nuke.message("No changes needed.\n(Paths are already correct)")