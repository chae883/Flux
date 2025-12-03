import nuke
import os
import sys
import platform
import subprocess
import datetime
import requests
import json

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from ui_notif_panel import Ui_MainWindow

# --- Configuration (From config.py) ---
WEBHOOK_URL = "https://discord.com/api/webhooks/1404285816116609094/7jm0jTlw8I5kz3yTBfKwHSypNcM5ppx_8OvDBexw0yvmGIu2hMpYYA0OCuddmc9ahrIe"
PLAYER_PATH = "C:/Program Files/DAUM/PotPlayer/PotPlayerMini64.exe"
FILE_EXPLORER_PATH = "C:/Users/tosh/AppData/Local/Anchorpoint/Anchorpoint.exe"

# --- Notification Logic ---

def send_discord_notification(fields):
    """Builds and sends a GREEN success embed to Discord."""
    if not WEBHOOK_URL:
        print("Flux Notification: No Webhook URL set.")
        return

    embed = {
        "title": "✅ Render Finished!",
        "color": 3066993, # Green
        "fields": fields,
        "footer": {"text": f"Flux Pipeline | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
    }
    payload = {"embeds": [embed]}
    headers = {"Content-Type": "application/json"}

    try:
        # Timeoutを設定してNukeがフリーズするのを防ぐ
        response = requests.post(WEBHOOK_URL, data=json.dumps(payload), headers=headers, timeout=5)
        response.raise_for_status()
    except Exception as e:
        print(f"Flux Notification Warning: Discord send failed. {e}")

# --- UI Class ---

class FluxNotificationPanel(QMainWindow):
    def __init__(self, write_node, duration_str):
        super(FluxNotificationPanel, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.Write_node = write_node
        
        # Window Settings
        # WindowStaysOnTopHint: 最前面に表示
        # Tool: タスクバーに出ないツールウィンドウ扱い（お好みで外してもOK）
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Effects
        self.op_effect = QGraphicsOpacityEffect(self)
        self.op_effect.setOpacity(0.95)
        self.setGraphicsEffect(self.op_effect)
        
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setColor(QColor(0, 0, 0, 100))
        self.ui.frame.setGraphicsEffect(self.shadow)
        
        # Center Screen
        screen = QApplication.primaryScreen().geometry()
        self.move(int(screen.center().x() - self.width()/2.0), int(screen.center().y() - self.height()/2.0))
        
        # Signals
        self.ui.pushButton_close.clicked.connect(self.close)
        self.ui.pushButton_2.clicked.connect(self.open_render_directory)
        self.ui.pushButton_3.clicked.connect(self.open_render_file)
        
        # Create Read Button
        if hasattr(self.ui, 'pushButton_CreateRead'):
            self.ui.pushButton_CreateRead.clicked.connect(self.create_read_node)
        
        # Set Info
        script_name = os.path.basename(nuke.root().name())
        self.ui.label_project_name.setText(script_name)
        self.ui.label_version.setText(f"Flux Pipeline | Duration: {duration_str}")

    def open_render_directory(self):
        path = nuke.filename(self.Write_node)
        if path:
            dir_path = os.path.dirname(path)
            self.open_explorer(dir_path)

    def open_render_file(self):
        path = nuke.filename(self.Write_node)
        if path:
            self.open_player(path)

    def open_explorer(self, path):
        path = os.path.normpath(path)
        if FILE_EXPLORER_PATH and os.path.exists(FILE_EXPLORER_PATH):
            subprocess.Popen([FILE_EXPLORER_PATH, path])
        elif platform.system() == "Windows":
            os.startfile(path)
        else:
            subprocess.Popen(["open" if platform.system() == "Darwin" else "xdg-open", path])

    def open_player(self, path):
        if PLAYER_PATH and os.path.exists(PLAYER_PATH):
            subprocess.Popen([PLAYER_PATH, path])
        else:
            if platform.system() == "Windows":
                os.startfile(path)
            else:
                subprocess.Popen(["open" if platform.system() == "Darwin" else "xdg-open", path])

    def create_read_node(self):
        file_path = nuke.filename(self.Write_node)
        if not file_path: return

        read = nuke.createNode("Read")
        read['file'].fromUserText(file_path)
        
        first = int(nuke.root()["first_frame"].getValue())
        last = int(nuke.root()["last_frame"].getValue())
        
        if "%" in file_path or "#" in file_path:
            read['first'].setValue(first)
            read['last'].setValue(last)
            read['origfirst'].setValue(first)
            read['origlast'].setValue(last)
        
        try:
            parent_node = self.Write_node.parent()
            if parent_node and parent_node.Class() == 'Group':
                read.setXpos(parent_node.xpos())
                read.setYpos(parent_node.ypos() + 120)
        except:
            pass
        
        self.close()

# --- Global Reference Management ---
# ガベージコレクションで消されないようにグローバルリストで保持するテクニック
_flux_notification_instances = []

def show_notification(write_node, start_time, first_frame, last_frame):
    # 1. Calc Duration
    end_time = datetime.datetime.now()
    duration = end_time - start_time
    duration_s = duration.total_seconds()
    
    hours, remainder = divmod(int(duration_s), 3600)
    minutes, seconds = divmod(int(remainder), 60)
    time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
    
    num_frames = (last_frame - first_frame) + 1
    avg_time_str = "N/A"
    if num_frames > 0:
        avg = duration_s / num_frames
        avg_time_str = f"{avg:.2f}s"

    # 2. Discord Notification
    script_name = os.path.basename(nuke.root().name())
    render_path = nuke.filename(write_node)
    filename = os.path.basename(render_path)
    
    fields = [
        {"name": "Script", "value": f"`{script_name}`", "inline": False},
        {"name": "File", "value": f"`{filename}`", "inline": False},
        {"name": "Range", "value": f"{first_frame}-{last_frame} ({num_frames}f)", "inline": True},
        {"name": "Duration", "value": time_str, "inline": True},
        {"name": "Avg/Frame", "value": avg_time_str, "inline": True}
    ]
    
    try:
        send_discord_notification(fields)
    except:
        pass

    # 3. Show UI (Main Thread)
    def _show_ui():
        # 古いインスタンスを掃除（メモリリーク防止）
        global _flux_notification_instances
        _flux_notification_instances = [w for w in _flux_notification_instances if w.isVisible()]
        
        # 新しいウィンドウを作成してリストに追加（これで消えない）
        window = FluxNotificationPanel(write_node, time_str)
        _flux_notification_instances.append(window)
        
        window.show()
        window.raise_()
        window.activateWindow()

    nuke.executeInMainThread(_show_ui)