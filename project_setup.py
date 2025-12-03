import nuke
import nukescripts
import config  # Updated config loader

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
        self.all_formats = nuke.formats()
        fmt_names = [f.name() for f in self.all_formats]
        
        self.format_menu = nuke.Enumeration_Knob('format_menu', 'Format Template', fmt_names)
        self.format_menu.setTooltip("Select a format to auto-fill Width and Height")
        self.addKnob(self.format_menu)

        # 2. 解像度
        self.width_k = nuke.Int_Knob('width', 'Width')
        self.height_k = nuke.Int_Knob('height', 'Height')
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

        # --- 初期値の設定 (Configから読み込み) ---
        target_fmt_name = config.DEFAULT_FORMAT
        
        if target_fmt_name in fmt_names:
            self.format_menu.setValue(target_fmt_name)
            # フォーマットオブジェクトから取得してセットしてもよいが、
            # ConfigのWidth/Heightを優先して初期セットする
            self.width_k.setValue(config.DEFAULT_WIDTH)
            self.height_k.setValue(config.DEFAULT_HEIGHT)
        else:
            self.width_k.setValue(config.DEFAULT_WIDTH)
            self.height_k.setValue(config.DEFAULT_HEIGHT)

        self.fps_k.setValue(config.DEFAULT_FPS)
        self.first_frame_k.setValue(config.DEFAULT_START)
        self.last_frame_k.setValue(config.DEFAULT_END)

    def knobChanged(self, knob):
        # ■ フォーマットプルダウンが変更されたら Width/Height を更新
        if knob == self.format_menu:
            selected_name = self.format_menu.value()
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
                    w = node.width()
                    h = node.height()
                    self.width_k.setValue(w)
                    self.height_k.setValue(h)
                    
                    node_format = node.format()
                    if node_format:
                        self.format_menu.setValue(node_format.name())
                    
                    meta = node.metadata()
                    fps_val = 24.0
                    if meta and 'input/frame_rate' in meta:
                        fps_val = float(meta['input/frame_rate'])
                    self.fps_k.setValue(fps_val)
                    
                    self.first_frame_k.setValue(node['first'].value())
                    self.last_frame_k.setValue(node['last'].value())
                    
                    info_text = f"Source: {node.name()} | {node_format.name()} ({w}x{h})"
                    self.info_label.setValue(info_text)
                else:
                    self.info_label.setValue("<font color='orange'>Error: Please select a READ node.</font>")
            except:
                self.info_label.setValue("<font color='orange'>Error: No node selected.</font>")

        # ■ Applyボタン
        if knob == self.apply_btn:
            root = nuke.root()
            
            w = int(self.width_k.value())
            h = int(self.height_k.value())
            
            selected_fmt_name = self.format_menu.value()
            
            match_found = False
            for f in self.all_formats:
                if f.name() == selected_fmt_name and f.width() == w and f.height() == h:
                    match_found = True
                    break
            
            if match_found:
                 root['format'].setValue(selected_fmt_name)
            else:
                new_format_str = f"{w} {h} Flux_Project"
                nuke.addFormat(new_format_str)
                root['format'].setValue('Flux_Project')
            
            root['fps'].setValue(self.fps_k.value())
            
            start = int(self.first_frame_k.value())
            end = int(self.last_frame_k.value())
            root['first_frame'].setValue(start)
            root['last_frame'].setValue(end)
            root['lock_range'].setValue(True)
            
            nuke.frame(start)
            self.close() 

def show_dialog():
    panel = FluxProjectSetup()
    panel.show()