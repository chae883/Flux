import nuke

def dump_node_info():
    """
    選択中のノードの全Knob情報をScript Editorに出力する。
    """
    try:
        node = nuke.selectedNode()
    except:
        nuke.message("Please select a node first.")
        return

    # 出力ヘッダー
    output = []
    output.append(f"\n{'='*60}")
    output.append(f" NODE INSPECTOR: {node.name()} ({node.Class()})")
    output.append(f"{'='*60}")
    output.append(f"{'Knob Name (Internal)':<35} | {'Value':<30} | {'Label (UI)'}")
    output.append(f"{'-'*35}-+-{'-'*30}-+-{'-'*20}")

    # 全Knobをループ
    for k_name in node.knobs():
        knob = node[k_name]
        
        # 値の取得 (エラー回避付き)
        try:
            val = str(knob.value())
        except:
            val = "<Error getting value>"
            
        # UIラベルの取得 (改行などは除去)
        try:
            label = knob.label().replace('\n', ' ')
        except:
            label = ""
            
        # 整形してリストに追加
        # 値が長すぎる場合は切り詰めるなどの処理も可能だが、今回はそのまま出す
        line = f"{k_name:<35} | {val:<30} | {label}"
        output.append(line)

    output.append(f"{'='*60}\n")
    
    # 結果を結合
    final_text = "\n".join(output)
    
    # Script Editorに出力 (print)
    print(final_text)
    
    # ユーザーへの通知 (Script Editorを見てね、というメッセージ)
    # nuke.message("Node info dumped to Script Editor.\nCheck the Output window.")
    
    # 【おまけ】クリップボードにもコピーしてあげる（神機能）
    # PySideが使えるならクリップボードへ送る
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QClipboard
        QApplication.clipboard().setText(final_text)
        nuke.message(f"Info for '{node.name()}' dumped to Script Editor\nand copied to Clipboard!")
    except:
        nuke.message(f"Info for '{node.name()}' dumped to Script Editor.")