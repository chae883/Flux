import nuke
import nukescripts
import os
import re
import config

class FluxLoader(nukescripts.PythonPanel):
    def __init__(self):
        super(FluxLoader, self).__init__('Flux Loader')
        
        # --- 現在のコンテキスト（ショット）の特定 ---
        self.shot_root = self.determine_shot_root()
        
        # UI: ヘッダー情報
        display_path = self.shot_root if self.shot_root else "Unknown (Script not saved correctly?)"
        self.addKnob(nuke.Text_Knob('path_info', 'Shot Path:', display_path))
        self.addKnob(nuke.Text_Knob('div1', ''))

        # UI: カテゴリ選択
        self.categories = [f for f in config.FOLDER_STRUCTURE if f != 'scripts']
        self.cat_menu = nuke.Enumeration_Knob('category', 'Category', self.categories)
        self.addKnob(self.cat_menu)

        # UI: アセットリスト
        self.asset_menu = nuke.Enumeration_Knob('assets', 'Available Assets', [])
        self.addKnob(self.asset_menu)

        # UI: 更新ボタン
        self.refresh_btn = nuke.PyScript_Knob('refresh', 'Refresh Scan')
        self.refresh_btn.clearFlag(nuke.STARTLINE)
        self.addKnob(self.refresh_btn)
        
        self.addKnob(nuke.Text_Knob('div2', ''))

        # UI: 読み込みボタン
        self.load_btn = nuke.PyScript_Knob('load', 'LOAD AS READ NODE')
        self.addKnob(self.load_btn)

        # 初期スキャン実行
        self.scanned_data = {} 
        self.refresh_scan()

    def determine_shot_root(self):
        script_path = nuke.root().name()
        if script_path == 'Root':
            return None
        
        script_dir = os.path.dirname(script_path)
        shot_root = os.path.dirname(script_dir)
        
        return shot_root.replace('\\', '/')

    def refresh_scan(self):
        if not self.shot_root or not os.path.exists(self.shot_root):
            self.scanned_data = {}
            return

        for cat in self.categories:
            search_path = os.path.join(self.shot_root, cat)
            items = []
            
            if os.path.exists(search_path):
                try:
                    root_files = nuke.getFileNameList(search_path) or []
                    for f in root_files:
                        full_p = os.path.join(search_path, f)
                        if os.path.isdir(full_p):
                            sub_files = nuke.getFileNameList(full_p) or []
                            for sub in sub_files:
                                items.append(f"{f}/{sub}")
                        else:
                            items.append(f)
                except Exception as e:
                    print(f"Flux Loader Error scanning {search_path}: {e}")
            
            self.scanned_data[cat] = sorted(items)

        self.update_asset_list()

    def update_asset_list(self):
        current_cat = self.cat_menu.value()
        items = self.scanned_data.get(current_cat, [])
        
        if not items:
            items = ["(No Assets Found)"]
        
        self.asset_menu.setValues(items)
        self.asset_menu.setValue(0)

    def knobChanged(self, knob):
        if knob == self.cat_menu:
            self.update_asset_list()
        
        if knob == self.refresh_btn:
            self.refresh_scan()
            
        if knob == self.load_btn:
            self.create_read_node()

    def create_read_node(self):
        if not self.shot_root:
            nuke.message("Error: Script must be saved in a proper project structure first.")
            return

        cat = self.cat_menu.value()
        asset_str = self.asset_menu.value()
        
        if asset_str == "(No Assets Found)":
            return

        # パスの構築
        match = re.match(r'^(.*?)(\s+(\d+-\d+))?$', asset_str)
        if not match:
            return
            
        rel_path = match.group(1) 
        range_str = match.group(3)

        full_path = os.path.join(self.shot_root, cat, rel_path).replace('\\', '/')
        
        # --- Readノード作成 ---
        r = nuke.createNode('Read')
        r['file'].fromUserText(full_path)
        
        # フレームレンジ設定
        if range_str:
            try:
                start, end = map(int, range_str.split('-'))
                r['first'].setValue(start)
                r['last'].setValue(end)
                r['origfirst'].setValue(start)
                r['origlast'].setValue(end)
            except:
                pass 

        # --- 色空間の自動設定 (Config参照) ---
        # 以前のハードコーディングを廃止し、config.py経由でJSONルールを参照
        ext = os.path.splitext(rel_path)[1].lower()
        cs_map = config.LOADER_COLORSPACE_MAP
        
        if ext in cs_map:
            target_cs = cs_map[ext]
            try:
                # Nukeの設定に存在するか確認してからセット
                r['colorspace'].setValue(target_cs)
            except:
                # 存在しない場合（例: OCIO設定が違う）はコンソールに警告
                print(f"Flux Loader Warning: Colorspace '{target_cs}' not found for {ext}. Using default.")

        # --- おもてなし機能 1: ポストスタンプ制御 ---
        if config.LOADER_DISABLE_POSTAGE_STAMP:
            r['postage_stamp'].setValue(False)

        # --- おもてなし機能 2: ノード選択と位置調整 ---
        # 他のノードの選択を解除し、このノードだけを選択状態にする
        for n in nuke.selectedNodes():
            n.setSelected(False)
        r.setSelected(True)
        
        # 少しずらして配置（連続作成時に重ならないように）
        # Nukeの自動配置にお任せする手もあるが、明示的に選択しておけばユーザーが移動しやすい
        
        # パネルは開いたまま（連続ロードのため）

def show_dialog():
    FluxLoader().show()