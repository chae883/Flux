import nuke
import nukescripts

class FluxProjectSetup(nukescripts.PythonPanel):
    def __init__(self):
        super(FluxProjectSetup, self).__init__('Flux Project Setup')
        
        # --- UI: 情報表示エリア ---
        self.info_label = nuke.Text_Knob('info_label', '', 'Select a Read Node & Click Get')
        self.addKnob(self.info_label)
        
        self.addKnob(nuke.Text_Knob('divider0', ''))

        # --- UI: 吸い上げボタン ---
        self.get_btn = nuke.PyScript_Knob('get_from_selection', 'Get Settings from Selected Read Node')
        self.get_btn.setFlag(nuke.STARTLINE)
        self.addKnob(self.get_btn)
        
        self.addKnob(nuke.Text_Knob('divider1', ''))

        # --- UI: 設定入力エリア ---
        
        # 1. フォーマット選択プルダウン
        # Nuke内の全フォーマットを取得してリスト化
        self.all_formats = nuke.formats()
        # プルダウン用の名前リストを作成 (重複回避などでソートしても良いが、今回は標準順序)
        fmt_names = [f.name() for f in self.all_formats]
        
        self.format_menu = nuke.Enumeration_Knob('format_menu', 'Format Template', fmt_names)
        self.format_menu.setTooltip("Select a format to auto-fill Width and Height")
        self.addKnob(self.format_menu)

        # 2. 解像度 (手動入力も可能)
        self.width_k = nuke.Int_Knob('width', 'Width')
        self.height_k = nuke.Int_Knob('height', 'Height')
        # 横並びにするためにStartNewLineを外すなどの調整もできますが、今回は標準で
        self.addKnob(self.width_k)
        self.addKnob(self.height_k)
        
        # 3. FPS & フレームレンジ
        self.fps_k = nuke.Double_Knob('fps', 'FPS')
        self.first_frame_k = nuke.Int_Knob('first_frame', 'Frame Start')
        self.last_frame_k = nuke.Int_Knob('last_frame', 'Frame End')
        
        self.addKnob(self.fps_k)
        self.addKnob(self.first_frame_k)
        self.addKnob(self.last_frame_k)
        
        self.addKnob(nuke.Text_Knob('divider2', ''))

        # --- UI: 実行ボタン ---
        self.apply_btn = nuke.PyScript_Knob('apply', 'APPLY TO PROJECT')
        self.addKnob(self.apply_btn)

        # --- 初期値の設定 (ユーザー要望) ---
        # Default: 4K DCP, 24fps, 108000-108240
        
        # フォーマットを 4K_DCP に合わせる試み
        target_fmt_name = '4K_DCP' 
        if target_fmt_name in fmt_names:
            self.format_menu.setValue(target_fmt_name)
            # 4K DCP (Full Container) is usually 4096x2160
            self.width_k.setValue(4096)
            self.height_k.setValue(2160)
        else:
            # 万が一 4K_DCP がない場合はとりあえずリストの最初か、適当な値を
            self.width_k.setValue(4096)
            self.height_k.setValue(2160)

        self.fps_k.setValue(24.0)
        self.first_frame_k.setValue(108000)
        self.last_frame_k.setValue(108240)

    def knobChanged(self, knob):
        # ■ フォーマットプルダウンが変更されたら Width/Height を更新
        if knob == self.format_menu:
            selected_name = self.format_menu.value()
            # 名前からFormatオブジェクトを探す
            for f in self.all_formats:
                if f.name() == selected_name:
                    self.width_k.setValue(f.width())
                    self.height_k.setValue(f.height())
                    break

        # ■ Getボタン: Readノードから情報をコピー
        if knob == self.get_btn:
            try:
                node = nuke.selectedNode()
                if node.Class() == 'Read':
                    # 解像度
                    w = node.width()
                    h = node.height()
                    self.width_k.setValue(w)
                    self.height_k.setValue(h)
                    
                    # フォーマット名が一致するものがあればプルダウンも合わせる
                    node_format = node.format()
                    if node_format:
                        # 名前で検索してセット
                        self.format_menu.setValue(node_format.name())
                    
                    # FPS
                    meta = node.metadata()
                    fps_val = 24.0
                    if meta and 'input/frame_rate' in meta:
                        fps_val = float(meta['input/frame_rate'])
                    self.fps_k.setValue(fps_val)
                    
                    # フレームレンジ
                    self.first_frame_k.setValue(node['first'].value())
                    self.last_frame_k.setValue(node['last'].value())
                    
                    # 情報表示
                    info_text = f"Source: {node.name()} | {node_format.name()} ({w}x{h})"
                    self.info_label.setValue(info_text)
                else:
                    self.info_label.setValue("<font color='orange'>Error: Please select a READ node.</font>")
            except:
                self.info_label.setValue("<font color='orange'>Error: No node selected.</font>")

        # ■ Applyボタン
        if knob == self.apply_btn:
            root = nuke.root()
            
            # 1. 解像度
            w = int(self.width_k.value())
            h = int(self.height_k.value())
            
            # 既存のフォーマットから探すか、新規作成か
            # 基本はプルダウンで選ばれた名前を使いたいが、手動で数値を変えている可能性もある
            # なので、現在の数値と名前を使って新規フォーマット(または既存)をセットする
            
            selected_fmt_name = self.format_menu.value()
            
            # 名前と実数値が一致しているか確認（簡易チェック）
            # 一致していればそのきれいな名前を使う。一致してなければ "Flux_Project" というカスタム名にする
            match_found = False
            for f in self.all_formats:
                if f.name() == selected_fmt_name and f.width() == w and f.height() == h:
                    match_found = True
                    break
            
            if match_found:
                 # リストにあるきれいなフォーマット名（例: "4K_DCP"）をそのままセット
                 root['format'].setValue(selected_fmt_name)
            else:
                # 数値が手動でいじられているのでカスタムフォーマットとして登録
                new_format_str = f"{w} {h} Flux_Project"
                nuke.addFormat(new_format_str)
                root['format'].setValue('Flux_Project')
            
            # 2. FPS
            root['fps'].setValue(self.fps_k.value())
            
            # 3. フレームレンジ
            start = int(self.first_frame_k.value())
            end = int(self.last_frame_k.value())
            root['first_frame'].setValue(start)
            root['last_frame'].setValue(end)
            root['lock_range'].setValue(True)
            
            # タイムライン移動
            nuke.frame(start)
            
            self.close() 

def show_dialog():
    panel = FluxProjectSetup()
    panel.show()