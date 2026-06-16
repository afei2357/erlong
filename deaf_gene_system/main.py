#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
耳聋基因检测系统 - 主程序入口
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config import SOFTWARE_INFO
from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow


class DeafGeneSystemApp:
    """耳聋基因检测系统应用类"""
    
    def __init__(self):
        self.app = None
        self.main_window = None
        
    def setup_application(self):
        """设置应用程序"""
        self.app = QApplication(sys.argv)
        self.app.setApplicationName(SOFTWARE_INFO["name"])
        self.app.setApplicationVersion(SOFTWARE_INFO["version"])
        self.app.setOrganizationName(SOFTWARE_INFO["company"])
        
        # 设置应用程序样式
        self.setup_styles()
        
        # 设置字体
        font = QFont("Microsoft YaHei", 9)
        self.app.setFont(font)
        
    def setup_styles(self):
        """设置应用程序样式"""
        # 这里可以加载QSS样式文件
        style = """
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            QWidget {
                font-family: "Microsoft YaHei";
                font-size: 9pt;
            }
            
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            
            QPushButton:hover {
                background-color: #106ebe;
            }
            
            QPushButton:pressed {
                background-color: #005a9e;
            }
            
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
            }
            
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
            
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                gridline-color: #eee;
            }
            
            QTableWidget::item {
                padding: 4px;
            }
            
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
            }
            
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #0078d4;
            }
            
            QStatusBar {
                background-color: #0078d4;
                color: white;
            }
            
            QMenuBar {
                background-color: #f0f0f0;
                border-bottom: 1px solid #ddd;
            }
            
            QMenuBar::item {
                padding: 4px 8px;
            }
            
            QMenuBar::item:selected {
                background-color: #0078d4;
                color: white;
            }
        """
        self.app.setStyleSheet(style)
        
    def show_login(self):
        """显示登录界面"""
        login_dialog = LoginDialog()
        
        if login_dialog.exec() == LoginDialog.DialogCode.Accepted:
            # 登录成功，显示主窗口
            self.show_main_window()
            return True
        else:
            # 登录失败或用户取消
            return False
            
    def show_main_window(self):
        """显示主窗口"""
        self.main_window = MainWindow()
        self.main_window.show()
        
    def run(self):
        """运行应用程序"""
        self.setup_application()
        
        if self.show_login():
            return self.app.exec()
        else:
            return 0


def main():
    """主函数"""
    try:
        app = DeafGeneSystemApp()
        exit_code = app.run()
        sys.exit(exit_code)
    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()