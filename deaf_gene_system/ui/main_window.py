#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QLabel, QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QAction, QIcon
from pathlib import Path

from config import SOFTWARE_INFO, UI_MODULES
from core.auth import auth_manager
from core.database import db
from ui.dashboard import Dashboard
from ui.sample_management import SampleManagement
from ui.gene_analysis import DeafGeneAnalysis
from ui.report_preview import ReportPreview
from ui.report_review import ReportReview
from ui.statistics import Statistics
from ui.system_settings import SystemSettings


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_user = auth_manager.get_user_info()
        self.init_ui()
        self.setup_menu()
        self.setup_status_bar()
        self.load_modules()
        
    def init_ui(self):
        self.setWindowTitle(f"{SOFTWARE_INFO['name']} - {self.current_user['real_name']}")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        icon_path = Path(__file__).parent.parent / "images" / "logo.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        self.content_area = self.create_content_area()
        main_layout.addWidget(self.content_area)
        
        self.create_header_bar()
        
    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("QFrame { background-color: #2c3e50; color: white; }")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        user_info = self.create_user_info()
        layout.addWidget(user_info)
        
        nav_menu = self.create_nav_menu()
        layout.addWidget(nav_menu)
        
        bottom_actions = self.create_bottom_actions()
        layout.addWidget(bottom_actions)
        
        sidebar.setLayout(layout)
        return sidebar
        
    def create_user_info(self):
        user_frame = QFrame()
        user_frame.setFixedHeight(120)
        user_frame.setStyleSheet("QFrame { background-color: #34495e; border-bottom: 1px solid #455a64; }")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        name_label = self._create_user_name_label()
        layout.addWidget(name_label)
        
        role_label = self._create_role_label()
        layout.addWidget(role_label)
        
        layout.addStretch()
        
        user_frame.setLayout(layout)
        return user_frame
    
    def _create_user_name_label(self):
        name_label = QLabel(self.current_user['real_name'])
        name_label.setStyleSheet("QLabel { color: white; font-size: 14px; font-weight: bold; }")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return name_label
    
    def _create_role_label(self):
        role_label = QLabel(self.current_user['role_name'])
        role_label.setStyleSheet("QLabel { color: #bdc3c7; font-size: 12px; background-color: #0078d4; padding: 4px 12px; border-radius: 12px; }")
        role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return role_label
        
    def create_nav_menu(self):
        nav_frame = QFrame()
        nav_frame.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(5)
        
        self.nav_buttons = {}
        
        for module_id, module_info in UI_MODULES.items():
            if module_id in self.current_user['permissions']:
                btn = self.create_nav_button(module_id, module_info)
                layout.addWidget(btn)
                self.nav_buttons[module_id] = btn
        
        layout.addStretch()
        nav_frame.setLayout(layout)
        return nav_frame
        
    def create_nav_button(self, module_id, module_info):
        btn = QPushButton(f"{module_info['icon']}  {module_info['name']}")
        btn.setFixedHeight(45)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ecf0f1;
                border: none;
                text-align: left;
                padding-left: 15px;
                font-size: 13px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }
            QPushButton:checked { background-color: #0078d4; color: white; }
        """)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self.switch_module(module_id))
        return btn
        
    def create_bottom_actions(self):
        bottom_frame = QFrame()
        bottom_frame.setFixedHeight(60)
        bottom_frame.setStyleSheet("QFrame { background-color: #34495e; border-top: 1px solid #455a64; }")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        logout_btn = QPushButton("退出登录")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)
        
        bottom_frame.setLayout(layout)
        return bottom_frame
        
    def create_content_area(self):
        content_frame = QFrame()
        content_frame.setStyleSheet("background-color: #f5f5f5;")
        
        layout = QVBoxLayout(content_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.header_bar = QFrame()
        self.header_bar.setFixedHeight(60)
        self.header_bar.setStyleSheet("QFrame { background-color: white; border-bottom: 1px solid #ddd; }")
        layout.addWidget(self.header_bar)
        
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        return content_frame
        
    def create_header_bar(self):
        layout = QHBoxLayout(self.header_bar)
        layout.setContentsMargins(20, 0, 20, 0)
        
        title_label = QLabel(SOFTWARE_INFO['name'])
        title_label.setStyleSheet("QLabel { color: #333; font-size: 16px; font-weight: bold; }")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        quick_actions_layout = QHBoxLayout()
        quick_actions_layout.setSpacing(10)
        
        import_report_btn = QPushButton("📊 导入Excel生成报告")
        import_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        import_report_btn.clicked.connect(self.import_excel_and_generate_report)
        quick_actions_layout.addWidget(import_report_btn)
        
        layout.addLayout(quick_actions_layout)
        
        self.time_label = QLabel()
        self.time_label.setStyleSheet("QLabel { color: #666; font-size: 12px; }")
        layout.addWidget(self.time_label)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()
        
    def setup_menu(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("文件")
        
        new_sample_action = QAction("新建样本", self)
        new_sample_action.triggered.connect(self.new_sample)
        file_menu.addAction(new_sample_action)
        
        import_data_action = QAction("导入数据", self)
        import_data_action.triggered.connect(self.import_data)
        file_menu.addAction(import_data_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        view_menu = menubar.addMenu("视图")
        
        for module_id, module_info in UI_MODULES.items():
            if module_id in self.current_user['permissions']:
                action = QAction(module_info['name'], self)
                action.triggered.connect(lambda checked, mid=module_id: self.switch_module(mid))
                view_menu.addAction(action)
        
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_status_bar(self):
        status_bar = self.statusBar()
        status_bar.setStyleSheet("QStatusBar { background-color: #0078d4; color: white; }")
        status_bar.showMessage(f"欢迎使用 {SOFTWARE_INFO['name']}")
        
    def load_modules(self):
        self.dashboard = Dashboard()
        self.stack.addWidget(self.dashboard)
        
        if 'sample_management' in self.current_user['permissions']:
            self.sample_management = SampleManagement()
            self.stack.addWidget(self.sample_management)
        
        if 'gene_analysis' in self.current_user['permissions']:
            self.gene_analysis = DeafGeneAnalysis()
            self.stack.addWidget(self.gene_analysis)
        
        if 'report_generation' in self.current_user['permissions']:
            self.report_preview = ReportPreview()
            self.stack.addWidget(self.report_preview)
        
        if 'report_review' in self.current_user['permissions']:
            self.report_review = ReportReview()
            self.stack.addWidget(self.report_review)
        
        if 'statistics' in self.current_user['permissions']:
            self.statistics = Statistics()
            self.stack.addWidget(self.statistics)
        
        if 'system_settings' in self.current_user['permissions']:
            self.system_settings = SystemSettings()
            self.stack.addWidget(self.system_settings)
        
        self.switch_module('dashboard')
        
    def switch_module(self, module_id):
        for btn_module_id, btn in self.nav_buttons.items():
            btn.setChecked(btn_module_id == module_id)
        module_map = {
            'dashboard': self.dashboard,
            'sample_management': self.sample_management,
            'gene_analysis': self.gene_analysis,
            'report_generation': self.report_preview,
            'report_preview': self.report_preview,
            'report_review': self.report_review,
            'statistics': self.statistics
        }
        
        if hasattr(self, 'system_settings'):
            module_map['system_settings'] = self.system_settings
        
        if module_id in module_map:
            self.stack.setCurrentWidget(module_map[module_id])
            if hasattr(module_map[module_id], 'refresh_data'):
                module_map[module_id].refresh_data()
    
    def update_time(self):
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)
        
    def new_sample(self):
        self.switch_module('sample_management')
        if hasattr(self.sample_management, 'show_add_dialog'):
            self.sample_management.show_add_dialog()
    
    def import_data(self):
        self.switch_module('gene_analysis')
        if hasattr(self.gene_analysis, 'show_import_dialog'):
            self.gene_analysis.show_import_dialog()
    
    def import_excel_and_generate_report(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择Excel文件",
            str(db.db_path.parent),
            "Excel文件 (*.xlsx *.xls);;CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            self.switch_module('gene_analysis')
            if hasattr(self.gene_analysis, 'import_file_and_analyze'):
                self.gene_analysis.import_file_and_analyze(file_path)
            else:
                QMessageBox.information(self, "提示", "请先在基因分析模块中完成数据解析")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")
    
    def logout(self):
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self, '确认退出',
            '确定要退出登录吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            auth_manager.logout()
            self._skip_close_confirm = True
            self.close()
    
    def show_about(self):
        from PyQt6.QtWidgets import QMessageBox
        
        contact_info = f"<p>联系电话: {SOFTWARE_INFO['contact']}</p>" if 'contact' in SOFTWARE_INFO else ""
        
        QMessageBox.about(
            self, 
            f"关于 {SOFTWARE_INFO['name']}",
            f"""
            <h3>{SOFTWARE_INFO['name']}</h3>
            <p>版本: {SOFTWARE_INFO['version']}</p>
            <p>{SOFTWARE_INFO['description']}</p>
            {contact_info}
            <p>{SOFTWARE_INFO['copyright']}</p>
            """
        )
    
    def closeEvent(self, event):
        from PyQt6.QtWidgets import QMessageBox
        
        if hasattr(self, '_skip_close_confirm') and self._skip_close_confirm:
            event.accept()
            return
        
        reply = QMessageBox.question(
            self, '确认退出',
            '确定要退出系统吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            auth_manager.logout()
            event.accept()
        else:
            event.ignore()