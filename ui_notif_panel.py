# -*- coding: utf-8 -*-
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QMetaObject,
    QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter,
    QPixmap, QRadialGradient)
from PySide6.QtWidgets import *
import os

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        # ウィンドウサイズを少し縦に広げました (250 -> 280)
        MainWindow.resize(425, 280)
        font = QFont()
        font.setBold(True)
        font.setWeight(QFont.Bold)
        MainWindow.setFont(font)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        
        # メインフレーム
        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setGeometry(QRect(20, 50, 385, 220)) # 高さ拡張
        self.frame.setAutoFillBackground(False)
        self.frame.setStyleSheet(u"QFrame {\n"
"	background-color: rgb(255, 255, 255);\n"
"	border-radius : 10px;\n"
"}")
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frame.setFrameShadow(QFrame.Plain)
        
        # Version / Footer Label (位置を下げました)
        self.label_version = QLabel(self.frame)
        self.label_version.setObjectName(u"label_version")
        self.label_version.setGeometry(QRect(10, 195, 365, 20))
        font1 = QFont()
        font1.setFamily(u"Segoe UI Semibold")
        font1.setPointSize(8)
        font1.setBold(False)
        font1.setWeight(QFont.Normal)
        self.label_version.setFont(font1)
        self.label_version.setStyleSheet(u"color: rgb(166, 166, 166);")
        self.label_version.setAlignment(Qt.AlignCenter)

        # Title Label
        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(0, 45, 381, 31))
        font2 = QFont()
        font2.setFamily(u"Segoe UI")
        font2.setPointSize(15)
        self.label_3.setFont(font2)
        self.label_3.setStyleSheet(u"color: rgb(0, 170, 127);")
        self.label_3.setAlignment(Qt.AlignCenter)

        # --- Button Style ---
        btn_style = u"""
        QPushButton {
            border: 2px solid rgb(52, 59, 72);
            border-radius: 5px;
            background-color: rgb(52, 59, 72);
            color: rgb(223, 223, 223);
        }
        QPushButton:hover {
            background-color: rgb(57, 65, 80);
            border: 2px solid rgb(61, 70, 86);
        }
        QPushButton:pressed {
            background-color: rgb(35, 40, 49);
            border: 2px solid rgb(43, 50, 61);
        }
        """
        
        base_path = os.path.dirname(__file__)

        # Open Directory Button
        self.pushButton_2 = QPushButton(self.frame)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setGeometry(QRect(20, 115, 166, 30))
        self.pushButton_2.setMinimumSize(QSize(150, 30))
        font3 = QFont()
        font3.setFamily(u"Segoe UI Semibold")
        font3.setPointSize(9)
        self.pushButton_2.setFont(font3)
        self.pushButton_2.setStyleSheet(btn_style)
        
        icon = QIcon()
        icon.addFile(os.path.join(base_path, "icons/pack/cil-folder-open.png"), QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_2.setIcon(icon)

        # Project Name Label
        self.label_project_name = QLabel(self.frame)
        self.label_project_name.setObjectName(u"label_project_name")
        self.label_project_name.setGeometry(QRect(0, 75, 381, 31))
        font4 = QFont()
        font4.setFamily(u"Segoe UI Semibold")
        font4.setPointSize(10)
        self.label_project_name.setFont(font4)
        self.label_project_name.setStyleSheet(u"color: rgb(66, 66, 66);")
        self.label_project_name.setAlignment(Qt.AlignCenter)

        # Open File Button
        self.pushButton_3 = QPushButton(self.frame)
        self.pushButton_3.setObjectName(u"pushButton_3")
        self.pushButton_3.setGeometry(QRect(196, 115, 167, 30))
        self.pushButton_3.setMinimumSize(QSize(150, 30))
        self.pushButton_3.setFont(font3)
        self.pushButton_3.setStyleSheet(btn_style)
        
        icon1 = QIcon()
        icon1.addFile(os.path.join(base_path, "icons/pack/cil-media-play.png"), QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_3.setIcon(icon1)

        # Create Read Button
        self.pushButton_CreateRead = QPushButton(self.frame)
        self.pushButton_CreateRead.setObjectName(u"pushButton_CreateRead")
        self.pushButton_CreateRead.setGeometry(QRect(108, 155, 166, 30)) # 中央寄せ
        self.pushButton_CreateRead.setMinimumSize(QSize(150, 30))
        self.pushButton_CreateRead.setFont(font3)
        # スタイルを少し変えて目立たせる（青系）
        self.pushButton_CreateRead.setStyleSheet(u"""
        QPushButton {
            border: 2px solid rgb(77, 190, 217);
            border-radius: 5px;
            background-color: rgb(77, 190, 217);
            color: rgb(255, 255, 255);
        }
        QPushButton:hover {
            background-color: rgb(98, 193, 217);
            border: 2px solid rgb(98, 193, 217);
        }
        QPushButton:pressed {
            background-color: rgb(60, 150, 170);
            border: 2px solid rgb(60, 150, 170);
        }
        """)
        icon_read = QIcon()
        icon_read.addFile(os.path.join(base_path, "icons/pack/cil-movie.png"), QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_CreateRead.setIcon(icon_read)

        # Close Button
        self.pushButton_close = QPushButton(self.frame)
        self.pushButton_close.setObjectName(u"pushButton_close")
        self.pushButton_close.setGeometry(QRect(361, 4, 20, 20))
        self.pushButton_close.setMinimumSize(QSize(18, 18))
        self.pushButton_close.setFont(font3)
        self.pushButton_close.setStyleSheet(u"QPushButton {\n"
"	border: 2px solid rgb(128, 146, 177);\n"
"	border-radius: 10px;	\n"
"	background-color: rgb(128, 146, 177);\n"
"	color: rgb(223, 223, 223);\n"
"}\n"
"QPushButton:hover {\n"
"	background-color: rgb(97, 110, 134);\n"
"	border: 2px solid rgb(97, 110, 134);\n"
"}")
        icon2 = QIcon()
        icon2.addFile(os.path.join(base_path, "icons/pack/cil-x.png"), QSize(), QIcon.Normal, QIcon.Off)
        self.pushButton_close.setIcon(icon2)

        # Success Icon
        self.label_icon_success = QLabel(self.centralwidget)
        self.label_icon_success.setObjectName(u"label_icon_success")
        self.label_icon_success.setGeometry(QRect(170, 10, 80, 80))
        self.label_icon_success.setFrameShape(QFrame.NoFrame)
        self.label_icon_success.setPixmap(QPixmap(os.path.join(base_path, "icons/success.png")))
        self.label_icon_success.setScaledContents(True)
        self.label_icon_success.setAlignment(Qt.AlignCenter)
        
        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Flux Notification", None))
        self.label_version.setText(QCoreApplication.translate("MainWindow", u"Flux Pipeline | Render Complete", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"<strong>Rendering Finished!</strong>", None))
        self.pushButton_2.setText(QCoreApplication.translate("MainWindow", u"Open Folder", None))
        self.label_project_name.setText(QCoreApplication.translate("MainWindow", u"Script Name", None))
        self.pushButton_3.setText(QCoreApplication.translate("MainWindow", u"Play File", None))
        self.pushButton_CreateRead.setText(QCoreApplication.translate("MainWindow", u"Create Read", None))
        self.pushButton_close.setText("")