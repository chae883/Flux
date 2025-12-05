# -*- coding: utf-8 -*-
from PySide6.QtCore import (QCoreApplication, QSize, Qt)
from PySide6.QtGui import (QColor, QFont, QIcon, QPixmap)
from PySide6.QtWidgets import *
import os

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        
        MainWindow.resize(400, 240)
        
        # Transparent background setup
        MainWindow.setAttribute(Qt.WA_TranslucentBackground)
        MainWindow.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        
        # --- Main Layout for the Window ---
        self.main_layout = QVBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(10, 10, 10, 10) # Margin for shadow/border
        
        # --- Main Frame Container ---
        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setStyleSheet(u"""
            QFrame#frame {
                background-color: rgb(255, 255, 255);
                border-radius: 10px;
                border: 1px solid rgb(200, 200, 200);
            }
        """)
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frame.setFrameShadow(QFrame.Plain)
        
        # Layout inside the Frame
        self.frame_layout = QVBoxLayout(self.frame)
        self.frame_layout.setContentsMargins(15, 10, 15, 15)
        self.frame_layout.setSpacing(5)

        # --- Header Section (Close Btn + Title) ---
        self.header_layout = QHBoxLayout()
        
        # Title Label
        self.label_title = QLabel("Rendering Finished!")
        font_title = QFont("Segoe UI", 14)
        font_title.setBold(True)
        self.label_title.setFont(font_title)
        self.label_title.setStyleSheet("color: rgb(0, 170, 127);")
        self.header_layout.addWidget(self.label_title)
        
        self.header_layout.addStretch()
        
        # Close Button
        self.pushButton_close = QPushButton("X")
        self.pushButton_close.setFixedSize(20, 20)
        self.pushButton_close.setStyleSheet(u"""
            QPushButton {
                border-radius: 10px;
                background-color: rgb(128, 146, 177);
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgb(200, 80, 80);
            }
        """)
        self.header_layout.addWidget(self.pushButton_close)
        
        self.frame_layout.addLayout(self.header_layout)

        # --- Content Section (Icon + Text) ---
        self.content_layout = QHBoxLayout()
        
        # Success Icon
        self.label_icon = QLabel()
        base_path = os.path.dirname(__file__)
        icon_path = os.path.join(base_path, "icons/success.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            self.label_icon.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.label_icon.setFixedSize(64, 64)
        self.content_layout.addWidget(self.label_icon)
        
        # Script Info
        self.info_layout = QVBoxLayout()
        self.info_layout.setSpacing(2)
        
        self.label_project = QLabel("Script Name")
        font_proj = QFont("Segoe UI Semibold", 10)
        self.label_project.setFont(font_proj)
        self.label_project.setStyleSheet("color: rgb(66, 66, 66);")
        self.info_layout.addWidget(self.label_project)
        
        self.label_duration = QLabel("Duration: 00:00:00")
        font_ver = QFont("Segoe UI", 9)
        self.label_duration.setFont(font_ver)
        self.label_duration.setStyleSheet("color: rgb(120, 120, 120);")
        self.info_layout.addWidget(self.label_duration)
        
        self.info_layout.addStretch()
        self.content_layout.addLayout(self.info_layout)
        self.content_layout.addStretch()
        
        self.frame_layout.addLayout(self.content_layout)

        # --- Buttons Section ---
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(10)
        
        btn_style_dark = u"""
            QPushButton {
                border-radius: 5px;
                background-color: rgb(52, 59, 72);
                color: rgb(223, 223, 223);
                padding: 5px;
            }
            QPushButton:hover { background-color: rgb(65, 75, 90); }
        """
        
        btn_style_blue = u"""
            QPushButton {
                border-radius: 5px;
                background-color: rgb(77, 190, 217);
                color: white;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: rgb(90, 200, 230); }
        """

        # Open Folder
        self.pushButton_folder = QPushButton("Open Folder")
        self.pushButton_folder.setMinimumHeight(30)
        self.pushButton_folder.setStyleSheet(btn_style_dark)
        self.buttons_layout.addWidget(self.pushButton_folder)

        # Open File (Player)
        self.pushButton_file = QPushButton("Play")
        self.pushButton_file.setMinimumHeight(30)
        self.pushButton_file.setStyleSheet(btn_style_dark)
        self.buttons_layout.addWidget(self.pushButton_file)
        
        self.frame_layout.addLayout(self.buttons_layout)
        
        # Create Read Node (Full Width)
        self.pushButton_CreateRead = QPushButton("Create Read Node")
        self.pushButton_CreateRead.setMinimumHeight(35)
        self.pushButton_CreateRead.setStyleSheet(btn_style_blue)
        self.frame_layout.addWidget(self.pushButton_CreateRead)

        # Finalize Main Layout
        self.main_layout.addWidget(self.frame)
        MainWindow.setCentralWidget(self.centralwidget)
        
        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Flux Notification", None))