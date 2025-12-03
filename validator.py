import nuke

def get_connected_read_nodes(start_node):
    """
    指定されたノードの上流にある全てのReadノードを再帰的に取得する関数。
    これにより、接続されていない「ゴミ」Readノードのエラーを無視できます。
    """
    reads = set()
    # 探索済みノードを記録して無限ループ防止
    visited = set()
    
    # 探索用スタック (最初は自身の入力ノードからスタート)
    stack = [start_node]
    
    while stack:
        node = stack.pop()
        
        if node in visited:
            continue
        visited.add(node)
        
        # Readノードならリストに追加
        if node.Class() == 'Read':
            reads.add(node)
        
        # ノードの依存関係（入力）を取得してスタックに追加
        # nuke.INPUTS: 通常のパイプ接続
        # nuke.HIDDEN_INPUTS: カメラやジオメトリなどの隠し入力も含む
        deps = node.dependencies(nuke.INPUTS | nuke.HIDDEN_INPUTS)
        for dep in deps:
            if dep not in visited:
                stack.append(dep)
                
    return list(reads)

def check_input_connected(node):
    """
    Writeノードに入力が接続されているか確認
    """
    if node.input(0) is None:
        return False, "Input is disconnected.\nWriteノードに何も接続されていません。"
    return True, ""

def check_script_saved():
    """
    スクリプトが保存されているか、未保存の変更がないか確認
    """
    if nuke.root().name() == "Root":
        return False, "Script is not saved yet.\nまだ一度も保存されていません。"
    
    if nuke.root().modified():
        return False, "Script has unsaved changes.\n未保存の変更があります。"
    
    return True, ""

def check_read_nodes(write_node):
    """
    接続されているReadノードのみのエラー状態を確認
    """
    # Writeノードに繋がっているReadノードだけを探す
    connected_reads = get_connected_read_nodes(write_node)
    
    error_nodes = []
    for read in connected_reads:
        # error() はファイルが見つからない等のエラーがある場合にTrueを返す
        if read.error():
            error_nodes.append(read.name())
    
    if error_nodes:
        msg = "Found connected Read nodes with errors (Missing frames or Read error):\n"
        msg += ", ".join(error_nodes)
        msg += "\n\n(Unconnected Read nodes were ignored)"
        return False, msg
    
    return True, ""

def check_frame_range_warning(render_start, render_end):
    """
    フレーム範囲の整合性チェック（Warningレベル）
    """
    root = nuke.root()
    root_first = int(root['first_frame'].value())
    root_last = int(root['last_frame'].value())
    
    if render_start == render_end:
        if root_first != root_last:
            msg = f"⚠️ Single Frame Warning ⚠️\n\n"
            msg += f"You are rendering only frame {render_start}.\n"
            msg += f"Project Settings are {root_first}-{root_last}.\n\n"
            msg += "Is this intentional?\n(意図的ですか？)"
            return False, msg
            
    return True, ""

def validate_render(node, start, end):
    """
    レンダリング前の総合チェックを実行するメイン関数
    戻り値: True (Go), False (Stop)
    """
    
    # --- 1. FATAL ERRORS (これらがあると即停止) ---
    
    # 1-1. 入力チェック
    ok, msg = check_input_connected(node)
    if not ok:
        nuke.message(f"🚫 Render Error 🚫\n\n{msg}")
        return False

    # 1-2. Readノードチェック (接続されているもの限定)
    ok, msg = check_read_nodes(node)
    if not ok:
        nuke.message(f"🚫 Render Error 🚫\n\n{msg}")
        return False

    # 1-3. 保存状態チェック
    ok, msg = check_script_saved()
    if not ok:
        if nuke.ask(f"⚠️ Unsaved Script ⚠️\n\n{msg}\n\nSave script and continue?\n(保存して続行しますか？)"):
            nuke.scriptSave()
        else:
            return False 

    # --- 2. WARNINGS (確認して続行可能) ---
    
    # 2-1. フレーム範囲チェック
    is_safe, warn_msg = check_frame_range_warning(start, end)
    if not is_safe:
        if not nuke.ask(warn_msg):
            return False

    # Nuke NC (Non-commercial) チェック (情報としてコンソールに出すのみ)
    if nuke.env.get('nc'):
        print("[Flux] Running in Nuke Non-commercial mode. Validator check passed.")

    return True