import nuke
import nukescripts
import os
import re
import glob
import config

class FluxLoader(nukescripts.PythonPanel):
    def __init__(self):
        super(FluxLoader, self).__init__('Flux Loader')
        
        self.shot_root = self.determine_shot_root()
        display_path = self.shot_root if self.shot_root else "Unknown"
        self.addKnob(nuke.Text_Knob('path_info', 'Shot Path:', display_path))
        self.addKnob(nuke.Text_Knob('div1', ''))

        # --- Asset Browser Section ---
        self.categories = [f for f in config.FOLDER_STRUCTURE if f != 'scripts']
        self.cat_menu = nuke.Enumeration_Knob('category', 'Category', self.categories)
        self.addKnob(self.cat_menu)

        self.asset_menu = nuke.Enumeration_Knob('assets', 'Available Assets', [])
        self.addKnob(self.asset_menu)

        self.refresh_btn = nuke.PyScript_Knob('refresh', 'Refresh Scan')
        self.refresh_btn.clearFlag(nuke.STARTLINE)
        self.addKnob(self.refresh_btn)
        
        self.load_btn = nuke.PyScript_Knob('load', 'LOAD AS READ NODE')
        self.addKnob(self.load_btn)

        # --- Version Manager Section (New) ---
        self.addKnob(nuke.Text_Knob('div_ver', 'Version Manager'))
        self.update_btn = nuke.PyScript_Knob('update_selected', 'Update Selected Reads to Latest')
        self.update_btn.setTooltip("Scans for higher versions (e.g. v001 -> v002) for selected Read nodes.")
        self.addKnob(self.update_btn)

        self.scanned_data = {} 
        self.refresh_scan()

    def determine_shot_root(self):
        script_path = nuke.root().name()
        if script_path == 'Root': return None
        # 正規表現を使った簡易親ディレクトリ推定も可能だが、
        # ここでは既存の相対ロジックでもLoaderとしては十分機能する
        return os.path.dirname(os.path.dirname(script_path)).replace('\\', '/')

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
                except: pass
            self.scanned_data[cat] = sorted(items)
        self.update_asset_list()

    def update_asset_list(self):
        current_cat = self.cat_menu.value()
        items = self.scanned_data.get(current_cat, [])
        if not items: items = ["(No Assets Found)"]
        self.asset_menu.setValues(items)
        self.asset_menu.setValue(0)

    def knobChanged(self, knob):
        if knob == self.cat_menu: self.update_asset_list()
        if knob == self.refresh_btn: self.refresh_scan()
        if knob == self.load_btn: self.create_read_node()
        if knob == self.update_btn: self.update_selected_reads()

    def create_read_node(self):
        if not self.shot_root:
            nuke.message("Error: Script context unknown.")
            return
        cat = self.cat_menu.value()
        asset_str = self.asset_menu.value()
        if asset_str == "(No Assets Found)": return

        match = re.match(r'^(.*?)(\s+(\d+-\d+))?$', asset_str)
        if not match: return
        rel_path = match.group(1) 
        range_str = match.group(3)
        full_path = os.path.join(self.shot_root, cat, rel_path).replace('\\', '/')
        
        r = nuke.createNode('Read')
        r['file'].fromUserText(full_path)
        
        if range_str:
            try:
                start, end = map(int, range_str.split('-'))
                r['first'].setValue(start)
                r['last'].setValue(end)
                r['origfirst'].setValue(start)
                r['origlast'].setValue(end)
            except: pass 

        ext = os.path.splitext(rel_path)[1].lower()
        cs_map = config.LOADER_COLORSPACE_MAP
        if ext in cs_map:
            try: r['colorspace'].setValue(cs_map[ext])
            except: pass

        if config.LOADER_DISABLE_POSTAGE_STAMP:
            r['postage_stamp'].setValue(False)

        for n in nuke.selectedNodes(): n.setSelected(False)
        r.setSelected(True)

    def update_selected_reads(self):
        """
        選択されたReadノードのバージョンアップを試みる
        """
        nodes = nuke.selectedNodes('Read')
        if not nodes:
            nuke.message("Please select Read nodes to update.")
            return

        updated_count = 0
        
        for node in nodes:
            file_path = node['file'].evaluate() # 変数展開済みパス
            
            # v001 などのバージョン表記を探す
            # パターン: vに続く数字
            version_match = re.search(r'[vV](\d+)', file_path)
            if not version_match:
                continue
                
            current_ver_str = version_match.group(1)
            current_ver_int = int(current_ver_str)
            padding = len(current_ver_str)
            
            # ディレクトリ内のファイルをスキャンして最大バージョンを探す
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                # ファイルパス自体がディレクトリ構造を含んでいる場合(連番フォルダなど)の考慮も必要だが
                # ここでは単純化して親ディレクトリを見る
                continue

            # 同じパターンのファイルを探す
            # 例: shot_v001.exr -> shot_v*.exr
            # 単純なglobだと誤爆するので、バージョン部分をワイルドカードにして検索
            prefix = file_path[:version_match.start()]
            suffix = file_path[version_match.end():]
            
            # 検索用パターン構築 (v*)
            search_pattern = f"{prefix}[vV]*{suffix}"
            
            # globはOS依存なので、Nukeのパス区切りをOSに合わせる必要がある場合も
            # ここでは簡易実装
            candidates = []
            
            # ※注意: 連番ファイル(####)の場合、globでは見つからないため
            # 親フォルダ自体のバージョンアップか、ファイル名のバージョンアップかを判定する必要がある
            # 今回は「ファイル名に含まれるバージョン」をインクリメントして存在確認する手法をとる（高速）
            
            found_higher = False
            next_ver_int = current_ver_int
            
            # 次のバージョンが存在するか順番にチェック（無限ループ防止で上限+10くらい）
            for i in range(1, 20):
                check_ver_int = current_ver_int + i
                check_ver_str = f"{check_ver_int:0{padding}d}"
                
                # 新しいパス候補を作成
                new_path = f"{prefix}v{check_ver_str}{suffix}"
                
                # ファイルが存在するか？ (連番の場合は #### があるので os.path.exists は使えない)
                # nuke.getFileNameList で確認するか、単純に親フォルダ内のリストを見る
                
                # 簡易チェック: Readノードにセットしてみてエラーが出ないか確認するのは重い。
                # ディレクトリ内のファイルリストを取得して確認するのが確実
                dir_files = nuke.getFileNameList(directory) or []
                
                # ファイル名部分だけ抽出
                target_filename = os.path.basename(new_path)
                
                # 連番表記 (####) を考慮したマッチングが必要
                # リスト内のアイテムと target_filename (これも #### を含む) を比較
                # nuke.getFileNameListは "name.####.exr 1-100" を返すので、スペースで切る
                
                exists = False
                for f in dir_files:
                    if f.split()[0] == target_filename:
                        exists = True
                        break
                
                if exists:
                    # 見つかったらそれを採用してさらに次を探す
                    next_ver_int = check_ver_int
                    found_higher = True
                else:
                    # 連続性が途切れたら終了
                    break
            
            if found_higher:
                new_ver_str = f"{next_ver_int:0{padding}d}"
                final_path = f"{prefix}v{new_ver_str}{suffix}"
                node['file'].setValue(final_path)
                print(f"[Flux Loader] Updated {node.name()}: v{current_ver_str} -> v{new_ver_str}")
                updated_count += 1

        if updated_count > 0:
            nuke.message(f"Updated {updated_count} Read nodes to latest versions.")
        else:
            nuke.message("No newer versions found for selected nodes.")

def show_dialog():
    FluxLoader().show()