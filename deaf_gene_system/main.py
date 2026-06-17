#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon

from config import SOFTWARE_INFO
from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow


class DeafGeneSystemApp:
    def __init__(self):
        self.app = None
        self.main_window = None
        
    def setup_application(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName(SOFTWARE_INFO["name"])
        self.app.setApplicationVersion(SOFTWARE_INFO["version"])
        self.app.setOrganizationName(SOFTWARE_INFO["company"])
        self.app.setStyle('Fusion')
        
        font = QFont("Microsoft YaHei", 9)
        self.app.setFont(font)
        
        icon_path = project_root / "images" / "logo.ico"
        if icon_path.exists():
            self.app.setWindowIcon(QIcon(str(icon_path)))
        
        self.setup_styles()
        
    def setup_styles(self):
        style = """
            QMainWindow { background-color: #f5f5f5; }
            QWidget { font-family: "Microsoft YaHei"; font-size: 9pt; }
            QTextEdit { color: #333; background-color: white; }
            QListWidget { color: #333; background-color: white; }
            QComboBox { color: #333; background-color: white; }
            
            QGroupBox {
                color: #333333;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #333333;
            }
            
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                color: #333;
            }
            
            QLineEdit:focus { border: 2px solid #0078d4; }
            
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                gridline-color: #eee;
                color: #333;
            }
            
            QTableWidget::item { padding: 4px; color: #333; }
            QTableWidget::item:selected { background-color: #0078d4; color: white; }
            
            QTabWidget::pane { border: 1px solid #ddd; background-color: white; }
            
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                color: #333;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #0078d4;
            }
            
            QStatusBar { background-color: #0078d4; color: white; }
            
            QMenuBar {
                background-color: #f0f0f0;
                border-bottom: 1px solid #ddd;
                color: #333333;
            }
            
            QMenuBar::item { padding: 4px 8px; color: #333333; }
            QMenuBar::item:selected { background-color: #0078d4; color: white; }
            
            QMenu {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #ddd;
            }
            
            QMenu::item { padding: 4px 20px; color: #333333; }
            QMenu::item:selected { background-color: #0078d4; color: white; }
            
            QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
                font-weight: normal;
            }
            
            QPushButton:hover {
                background-color: #f0f0f0;
                color: #333333;
                border: 1px solid #0078d4;
            }
            
            QPushButton:pressed { background-color: #e0e0e0; color: #333333; }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #999999;
                border: 1px solid #dddddd;
            }
            
            QMessageBox { background-color: white; color: #333; }
            QMessageBox QLabel { color: #333; }
            
            QMessageBox QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            
            QMessageBox QPushButton:hover {
                background-color: #f0f0f0;
                color: #333333;
                border: 1px solid #0078d4;
            }
            
            QMessageBox QPushButton:pressed { background-color: #e0e0e0; color: #333333; }
        """
        self.app.setStyleSheet(style)
        
    def show_login(self):
        login_dialog = LoginDialog()
        if login_dialog.exec() == LoginDialog.DialogCode.Accepted:
            self.show_main_window()
            return True
        return False
            
    def show_main_window(self):
        self.main_window = MainWindow()
        self.main_window.show()
        
    def run(self):
        self.setup_application()
        if self.show_login():
            return self.app.exec()
        return 0


def main():
    try:
        app = DeafGeneSystemApp()
        sys.exit(app.run())
    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()