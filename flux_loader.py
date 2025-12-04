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

        # UI: カテゴリ選択 (Plates, Renders, Ref)
        # config.jsonの folder_structure から 'scripts' を除外したものを使用
        self.categories = [f for f in config.FOLDER_STRUCTURE if f != 'scripts']
        self.cat_menu = nuke.Enumeration_Knob('category', 'Category', self.categories)
        self.addKnob(self.cat_menu)

        # UI: アセットリスト (プルダウン)
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
        self.scanned_data = {} # { 'renders': ['file A', 'file B'], ... }
        self.refresh_scan()

    def determine_shot_root(self):
        """
        現在のスクリプトパスからショットのルートディレクトリを推測する。
        構造: .../ShotName/scripts/script.nk を想定
        """
        script_path = nuke.root().name()
        if script_path == 'Root':
            return None
        
        # scriptsフォルダの一つ上の階層をショットルートとする
        # 例: D:/WIP/TMP/TMP_010_010/scripts/v001.nk -> D:/WIP/TMP/TMP_010_010
        script_dir = os.path.dirname(script_path)
        shot_root = os.path.dirname(script_dir)
        
        return shot_root.replace('\\', '/')

    def refresh_scan(self):
        """
        選択されたショットルート内の各カテゴリフォルダをスキャンする
        """
        if not self.shot_root or not os.path.exists(self.shot_root):
            self.scanned_data = {}
            return

        for cat in self.categories:
            search_path = os.path.join(self.shot_root, cat)
            items = []
            
            if os.path.exists(search_path):
                # nuke.getFileNameList は連番を "name.####.exr 1001-1100" の形式で返してくれる
                # フォルダ内のフォルダも再帰的に見る簡易ロジック（1階層下まで見る）
                # まずは直下
                root_files = nuke.getFileNameList(search_path) or []
                for f in root_files:
                    # 拡張子がない、またはディレクトリっぽいものは除外するか、さらに潜る
                    # ここではシンプルに「ファイルっぽいもの」と「サブフォルダ内の連番」を探す
                    full_p = os.path.join(search_path, f)
                    if os.path.isdir(full_p):
                        # サブフォルダ（例: renders/shot_v001/）
                        sub_files = nuke.getFileNameList(full_p) or []
                        for sub in sub_files:
                            # 表示名: shot_v001/shot_v001.####.exr 1-100
                            items.append(f"{f}/{sub}")
                    else:
                        # 直下のファイル
                        items.append(f)
            
            self.scanned_data[cat] = sorted(items)

        # 現在のカテゴリスイッチに合わせてリスト更新
        self.update_asset_list()

    def update_asset_list(self):
        current_cat = self.cat_menu.value()
        items = self.scanned_data.get(current_cat, [])
        
        if not items:
            items = ["(No Assets Found)"]
        
        self.asset_menu.setValues(items)
        self.asset_menu.setValue(0) # 先頭を選択

    def knobChanged(self, knob):
        if knob == self.cat_menu:
            self.update_asset_list()
        
        if knob == self.refresh_btn:
            self.refresh_scan()
            
        if knob == self.load_btn:
            self.create_read_node()

    def create_read_node(self):
        """
        選択されたアセットからReadノードを作成し、設定を自動適用する
        """
        if not self.shot_root:
            nuke.message("Error: Script must be saved in a proper project structure first.")
            return

        cat = self.cat_menu.value()
        asset_str = self.asset_menu.value()
        
        if asset_str == "(No Assets Found)":
            return

        # パスの構築
        # asset_str は "folder/file.####.exr 1001-1050" のような形式の可能性がある
        # これを "パス部分" と "レンジ部分" に分ける必要がある
        
        # Nukeのリスト形式: "filename.ext start-end" または "filename.ext"
        match = re.match(r'^(.*?)(\s+(\d+-\d+))?$', asset_str)
        if not match:
            return
            
        rel_path = match.group(1) # "folder/file.####.exr"
        range_str = match.group(3) # "1001-1050" (存在すれば)

        full_path = os.path.join(self.shot_root, cat, rel_path).replace('\\', '/')
        
        # Readノード作成
        r = nuke.createNode('Read')
        r['file'].fromUserText(full_path) # 連番(#)を正しく解釈させる
        
        # フレームレンジ設定
        if range_str:
            try:
                start, end = map(int, range_str.split('-'))
                r['first'].setValue(start)
                r['last'].setValue(end)
                r['origfirst'].setValue(start)
                r['origlast'].setValue(end)
            except:
                pass # パース失敗時は自動検出に任せる

        # 色空間の自動設定 (簡易ルールベース)
        # configにルールがあればそれを使うのがベストだが、ここでは一般的なルールを適用
        ext = os.path.splitext(rel_path)[1].lower()
        
        if ext == '.exr':
            # EXRはリニア系 (ACEScg推奨)
            try:
                r['colorspace'].setValue('ACES - ACEScg')
            except:
                r['colorspace'].setValue('linear') # Fallback
                
        elif ext in ['.mov', '.mp4', '.jpg', '.png']:
            # 動画や一般的な画像は sRGB / Rec709
            try:
                r['colorspace'].setValue('sRGB') # または Output - sRGB
            except:
                pass

        # ノードの位置調整（見やすいように）
        r.setXpos(r.xpos())
        r.setYpos(r.ypos())
        
        # パネルは閉じない（連続して読み込む可能性があるため）

def show_dialog():
    FluxLoader().show()