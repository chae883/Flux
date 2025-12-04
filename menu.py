import nuke

# ------------------------------------------------------------------------------
# 1. Main Menu (画面上部: アクション系)
# ------------------------------------------------------------------------------
menubar = nuke.menu('Nuke')
m = menubar.addMenu('Flux')

# --- Core Tools ---
m.addCommand('Project Setup', 
             'import project_setup; project_setup.show_dialog()')

m.addCommand('Make Official', 
             'import make_official; make_official.show_dialog()')

# ★ NEW: Flux Loader (Shift+R)
m.addCommand('Flux Loader', 
             'import loader; loader.show_dialog()',
             'shift+r')

m.addSeparator()

m.addCommand('Version Up', 
             'import version_up; version_up.run()')

# Flux Write (メニューからも作れるようにしておく)
m.addCommand('Create Flux Write', 
             'import smart_write; smart_write.create_flux_write()')

m.addSeparator()

# --- Sub Menu: Utils ---
# サブメニュー "Utils" を作成
utils_menu = m.addMenu('Utils')

utils_menu.addCommand('Make Paths Relative', 
                      'import relative_path; relative_path.convert_to_relative()')

utils_menu.addCommand('Node Inspector', 
                      'import node_inspector; node_inspector.dump_node_info()')


# ------------------------------------------------------------------------------
# 2. Nodes Toolbar (画面横アイコン列: ノード作成系)
# ------------------------------------------------------------------------------
toolbar = nuke.toolbar("Nodes")
t = toolbar.addMenu('Flux', icon='Write.png') 

# Flux Write (Toolbar)
# Shift+W で呼び出し
t.addCommand('Flux Write', 
             'import smart_write; smart_write.create_flux_write()', 
             'shift+w', 
             icon='Write.png')

# Flux Loader (Toolbar)
t.addCommand('Flux Loader',
             'import loader; loader.show_dialog()',
             icon='Read.png') # 標準のReadアイコンを使用