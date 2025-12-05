import nuke
import config

def apply_defaults():
    """
    Apply default project settings (Format, FPS, OCIO) on new script load.
    新規スクリプト（Root）が開かれた時にデフォルト設定を適用する関数
    """
    # 既に保存されているスクリプトなら何もしない（設定上書き防止）
    if nuke.root().name() != 'Root':
        return

    # NukeがGUIモードでない場合（レンダリング時など）はスキップして余計なログを出さない
    if not nuke.GUI:
        return

    print("[Flux] Applying Default Project Settings...")
    root = nuke.root()

    try:
        # 1. Format
        target_fmt = config.DEFAULT_FORMAT
        
        # フォーマットが存在するかチェック
        found = False
        for f in nuke.formats():
            if f.name() == target_fmt:
                root['format'].setValue(target_fmt)
                found = True
                break
        
        if not found:
            # なければConfigの値で作る
            w = config.DEFAULT_WIDTH
            h = config.DEFAULT_HEIGHT
            nuke.addFormat(f"{w} {h} {target_fmt}")
            root['format'].setValue(target_fmt)

        # 2. FPS & Range
        root['fps'].setValue(config.DEFAULT_FPS)
        root['first_frame'].setValue(config.DEFAULT_START)
        root['last_frame'].setValue(config.DEFAULT_END)
        root['lock_range'].setValue(True)

        # 3. OCIO (Color Management)
        # Nuke 16 is OCIO by default, but we enforce the specific config
        if root.knob('colorManagement'):
            root['colorManagement'].setValue('OCIO')
            
            # OCIO Config Name from flux_config.json
            target_ocio = getattr(config, 'DEFAULT_OCIO_CONFIG', '')
            
            if target_ocio:
                # Nuke 16 allows setting the config name directly if it's a built-in one
                current = root['OCIO_config'].value()
                if current != target_ocio:
                    try:
                        root['OCIO_config'].setValue(target_ocio)
                        print(f"[Flux] Set OCIO Config to: {target_ocio}")
                    except Exception as e:
                        print(f"[Flux Warning] Could not set OCIO config: {e}")

    except Exception as e:
        print(f"[Flux Error] Failed to set defaults: {e}")