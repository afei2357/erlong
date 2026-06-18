#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 权属说明：耳聋基因检测系统入口文件，仅供内部使用

import sys
import traceback
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# QtWebEngineWidgets必须在QApplication创建之前导入，这个坑踩过好几次了
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    print(f"[WARN] QtWebEngineWidgets 导入失败，报告预览功能可能无法使用", file=sys.stderr)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon

from config import SOFTWARE_INFO

# 记录启动时间，方便看性能
_start_time = None


class DeafGeneSystemApp:
    def __init__(self):
        self.app = None
        self.main_window = None
        self._start_time = None
        
    def setup_application(self):
        self._start_time = __import__('time').time()
        
        print(f"[耳聋基因检测系统] 开始初始化应用...", file=sys.stderr)
        
        self.app = QApplication(sys.argv)
        self.app.setApplicationName(SOFTWARE_INFO["name"])
        self.app.setApplicationVersion(SOFTWARE_INFO["version"])
        self.app.setOrganizationName(SOFTWARE_INFO["company"])
        self.app.setStyle('Fusion')
        
        # 设置全局字体为微软雅黑，不然中文显示会有问题
        font = QFont("Microsoft YaHei", 9)
        self.app.setFont(font)
        
        # 加载图标，找不到也没关系
        icon_path = project_root / "images" / "logo.ico"
        if icon_path.exists():
            self.app.setWindowIcon(QIcon(str(icon_path)))
        else:
            print(f"[WARN] 图标文件不存在: {icon_path}", file=sys.stderr)
        
        # 设置样式表
        self.setup_styles()
        
        elapsed = __import__('time').time() - self._start_time
        print(f"[耳聋基因检测系统] 应用初始化完成，耗时: {elapsed:.2f}s", file=sys.stderr)
        
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
        from ui.login_dialog import DeafGeneLoginDialog
        
        print(f"[耳聋基因检测系统] 显示登录对话框...", file=sys.stderr)
        
        login_dialog = DeafGeneLoginDialog()
        if login_dialog.exec() == DeafGeneLoginDialog.DialogCode.Accepted:
            print(f"[耳聋基因检测系统] 登录成功，进入主窗口", file=sys.stderr)
            self.show_main_window()
            return True
        else:
            # 用户取消登录，不需要记录日志
            return False
            
    def show_main_window(self):
        from ui.main_window import MainWindow
        
        print(f"[耳聋基因检测系统] 创建主窗口...", file=sys.stderr)
        
        self.main_window = MainWindow()
        self.main_window.show()
        
        elapsed = __import__('time').time() - self._start_time
        print(f"[耳聋基因检测系统] 主窗口显示完成，总耗时: {elapsed:.2f}s", file=sys.stderr)
        
    def run(self):
        self.setup_application()
        if self.show_login():
            return self.app.exec()
        return 0


def main():
    global _start_time
    _start_time = __import__('time').time()
    
    # 写入启动日志到文件
    _write_deaf_gene_start_log()
    
    print(f"[耳聋基因检测系统] ============== 程序启动 ==============", file=sys.stderr)
    print(f"[耳聋基因检测系统] 项目目录: {project_root}", file=sys.stderr)
    print(f"[耳聋基因检测系统] Python版本: {sys.version}", file=sys.stderr)
    
    try:
        app = DeafGeneSystemApp()
        sys.exit(app.run())
    except Exception as e:
        print(f"[ERROR] 程序启动失败: {e}", file=sys.stderr)
        print(f"[ERROR] 详细错误信息:", file=sys.stderr)
        traceback.print_exc()
        _write_deaf_gene_error_log(f"程序启动失败: {e}")
        sys.exit(1)


def _write_deaf_gene_start_log():
    """记录耳聋基因检测系统启动日志"""
    from datetime import datetime
    
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"deaf_gene_start_{datetime.now().strftime('%Y%m%d')}.log"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 系统启动\n")


def _write_deaf_gene_error_log(message):
    """记录耳聋基因检测系统错误日志"""
    from datetime import datetime
    
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"deaf_gene_errors_{datetime.now().strftime('%Y%m%d')}.log"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")


if __name__ == "__main__":
    main()

