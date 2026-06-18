#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 权属说明：主窗口模块，负责耳聋基因检测系统的整体布局和导航

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
from ui.sample_management import DeafGeneSampleManagement
from ui.gene_analysis import DeafGeneAnalysis
from ui.report_preview import DeafGeneReportPreview
from ui.report_review import DeafGeneReportReview
from ui.statistics import DeafGeneStatistics
from ui.system_settings import DeafGeneSysSetting
import sys 

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.deaf_gene_cur_user = auth_manager.get_user_info()
        self.deaf_gene_module_map = {}
        self.deaf_gene_nav_buttons = {}
        self._deafGeneLastSwitchTime = None
        self._deaf_gene_temp_debug = []   # 调试时用过的临时变量，暂时保留
        self.initDeafGeneMainUI()
        self.setupDeafGeneMenu()
        self.setupDeafGeneStatusBar()
        self.loadDeafGeneModules()
        
    def initDeafGeneMainUI(self):
        self.setWindowTitle(f"{SOFTWARE_INFO['name']} - {self.deaf_gene_cur_user['real_name']}")
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
        
        self.deaf_gene_sidebar = self.createDeafGeneSidebar()
        main_layout.addWidget(self.deaf_gene_sidebar)
        
        self.deaf_gene_content_area = self.createDeafGeneContentArea()
        main_layout.addWidget(self.deaf_gene_content_area)
        
        self.createDeafGeneHeaderBar()

    def createDeafGeneSidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("QFrame { background-color: #2c3e50; color: white; }")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        user_info = self.createDeafGeneUserInfo()
        layout.addWidget(user_info)
        
        nav_menu = self.createDeafGeneNavMenu()
        layout.addWidget(nav_menu)
        
        bottom_actions = self.createDeafGeneBottomActions()
        layout.addWidget(bottom_actions)
        
        sidebar.setLayout(layout)
        return sidebar
        
    def createDeafGeneUserInfo(self):
        user_frame = QFrame()
        user_frame.setFixedHeight(120)
        user_frame.setStyleSheet("QFrame { background-color: #34495e; border-bottom: 1px solid #455a64; }")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        name_label = self._createDeafGeneUserNameLabel()
        layout.addWidget(name_label)
        
        role_label = self._createDeafGeneRoleLabel()
        layout.addWidget(role_label)
        
        layout.addStretch()
        
        user_frame.setLayout(layout)
        return user_frame
    
    def _createDeafGeneUserNameLabel(self):
        name_label = QLabel(self.deaf_gene_cur_user['real_name'])
        name_label.setStyleSheet("QLabel { color: white; font-size: 14px; font-weight: bold; }")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return name_label
    
    def _createDeafGeneRoleLabel(self):
        role_label = QLabel(self.deaf_gene_cur_user['role_name'])
        role_label.setStyleSheet("QLabel { color: #bdc3c7; font-size: 12px; background-color: #0078d4; padding: 4px 12px; border-radius: 12px; }")
        role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return role_label
        
    def createDeafGeneNavMenu(self):
        nav_frame = QFrame()
        nav_frame.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(5)
        
        for module_id, module_info in UI_MODULES.items():
            if module_id in self.deaf_gene_cur_user['permissions']:
                btn = self.createDeafGeneNavButton(module_id, module_info)
                layout.addWidget(btn)
                self.deaf_gene_nav_buttons[module_id] = btn
        
        layout.addStretch()
        nav_frame.setLayout(layout)
        return nav_frame
        
    def createDeafGeneNavButton(self, module_id, module_info):
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
        btn.clicked.connect(lambda: self.switchDeafGeneModule(module_id))
        return btn
        
    def createDeafGeneBottomActions(self):
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
        logout_btn.clicked.connect(self.performDeafGeneLogout)
        layout.addWidget(logout_btn)
        
        bottom_frame.setLayout(layout)
        return bottom_frame
        
    def createDeafGeneContentArea(self):
        content_frame = QFrame()
        content_frame.setStyleSheet("background-color: #f5f5f5;")
        
        layout = QVBoxLayout(content_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.deaf_gene_header_bar = QFrame()
        self.deaf_gene_header_bar.setFixedHeight(60)
        self.deaf_gene_header_bar.setStyleSheet("QFrame { background-color: white; border-bottom: 1px solid #ddd; }")
        layout.addWidget(self.deaf_gene_header_bar)
        
        self.deaf_gene_stack = QStackedWidget()
        layout.addWidget(self.deaf_gene_stack)
        
        return content_frame
        
    def createDeafGeneHeaderBar(self):
        layout = QHBoxLayout(self.deaf_gene_header_bar)
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
        import_report_btn.clicked.connect(self.importExcelAndGenerateDeafGeneReport)
        quick_actions_layout.addWidget(import_report_btn)
        
        layout.addLayout(quick_actions_layout)
        
        self.deaf_gene_time_label = QLabel()
        self.deaf_gene_time_label.setStyleSheet("QLabel { color: #666; font-size: 12px; }")
        layout.addWidget(self.deaf_gene_time_label)
        
        self.deaf_gene_timer = QTimer()
        self.deaf_gene_timer.timeout.connect(self.updateDeafGeneTime)
        self.deaf_gene_timer.start(1000)
        self.updateDeafGeneTime()

    def setupDeafGeneMenu(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("文件")
        
        new_sample_action = QAction("新建样本", self)
        new_sample_action.triggered.connect(self.createNewDeafGeneSample)
        file_menu.addAction(new_sample_action)
        
        import_data_action = QAction("导入数据", self)
        import_data_action.triggered.connect(self.importDeafGeneData)
        file_menu.addAction(import_data_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        view_menu = menubar.addMenu("视图")
        
        for module_id, module_info in UI_MODULES.items():
            if module_id in self.deaf_gene_cur_user['permissions']:
                action = QAction(module_info['name'], self)
                action.triggered.connect(lambda checked, mid=module_id: self.switchDeafGeneModule(mid))
                view_menu.addAction(action)
        
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.showDeafGeneAbout)
        help_menu.addAction(about_action)
        
    def setupDeafGeneStatusBar(self):
        status_bar = self.statusBar()
        status_bar.setStyleSheet("QStatusBar { background-color: #0078d4; color: white; }")
        status_bar.showMessage(f"欢迎使用 {SOFTWARE_INFO['name']}")
        
    def loadDeafGeneModules(self):
        import sys
        
        print(f"[耳聋基因检测系统] 开始加载模块...", file=sys.stderr)
        
        self.deaf_gene_dashboard = Dashboard()
        self.deaf_gene_stack.addWidget(self.deaf_gene_dashboard)
        self.deaf_gene_module_map['dashboard'] = self.deaf_gene_dashboard
        
        if 'sample_management' in self.deaf_gene_cur_user['permissions']:
            self.deaf_gene_sample_management = DeafGeneSampleManagement()
            self.deaf_gene_stack.addWidget(self.deaf_gene_sample_management)
            self.deaf_gene_module_map['sample_management'] = self.deaf_gene_sample_management
            # 暂时不记录日志
            
        if 'gene_analysis' in self.deaf_gene_cur_user['permissions']:
            self.deaf_gene_analysis = DeafGeneAnalysis()
            self.deaf_gene_stack.addWidget(self.deaf_gene_analysis)
            self.deaf_gene_module_map['gene_analysis'] = self.deaf_gene_analysis
            print(f"[耳聋基因检测系统] 基因分析模块加载完成", file=sys.stderr)
        
        if 'report_generation' in self.deaf_gene_cur_user['permissions']:
            self.deaf_gene_report_preview = DeafGeneReportPreview()
            self.deaf_gene_stack.addWidget(self.deaf_gene_report_preview)
            self.deaf_gene_module_map['report_generation'] = self.deaf_gene_report_preview
            self.deaf_gene_module_map['report_preview'] = self.deaf_gene_report_preview
            # 这个模块比较重要，记录一下日志文件
            self._writeDeafGeneLog("报告生成模块已加载")
        
        if 'report_review' in self.deaf_gene_cur_user['permissions']:
            self.deaf_gene_report_review = DeafGeneReportReview()
            self.deaf_gene_stack.addWidget(self.deaf_gene_report_review)
            self.deaf_gene_module_map['report_review'] = self.deaf_gene_report_review
            
        if 'statistics' in self.deaf_gene_cur_user['permissions']:
            self.deaf_gene_statistics = DeafGeneStatistics()
            self.deaf_gene_stack.addWidget(self.deaf_gene_statistics)
            self.deaf_gene_module_map['statistics'] = self.deaf_gene_statistics
            print(f"[耳聋基因检测系统] 统计分析模块已就绪", file=sys.stderr)
        
        if 'system_settings' in self.deaf_gene_cur_user['permissions']:
            self.deaf_gene_system_settings = DeafGeneSysSetting()
            self.deaf_gene_stack.addWidget(self.deaf_gene_system_settings)
            self.deaf_gene_module_map['system_settings'] = self.deaf_gene_system_settings
        
        self.switchDeafGeneModule('dashboard')
        
    def switchDeafGeneModule(self, module_id):
        from datetime import datetime
        
        # 记录切换前的时间
        _prev_time = self._deafGeneLastSwitchTime
        
        for btn_module_id, btn in self.deaf_gene_nav_buttons.items():
            btn.setChecked(btn_module_id == module_id)
        
        if module_id in self.deaf_gene_module_map:
            target_widget = self.deaf_gene_module_map[module_id]
            self.deaf_gene_stack.setCurrentWidget(target_widget)
            
            refresh_method = getattr(target_widget, 'refreshDeafGeneData', None)
            if refresh_method:
                refresh_method()
            else:
                old_refresh = getattr(target_widget, 'refresh_data', None)
                if old_refresh:
                    old_refresh()
                else:
                    # 有些模块没有刷新方法，就不做处理了
                    pass
            
            self._deafGeneLastSwitchTime = datetime.now()
            
            # 只有某些模块切换需要记录日志
            if module_id in ['gene_analysis', 'report_generation']:
                print(f"[耳聋基因检测系统] 切换到{module_id}模块", file=sys.stderr)
            
            # 调试用的，暂时保留
            # _diff = self._deafGeneLastSwitchTime - _prev_time if _prev_time else None
            
    def updateDeafGeneTime(self):
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.deaf_gene_time_label.setText(current_time)
        
    def createNewDeafGeneSample(self):
        self.switchDeafGeneModule('sample_management')
        if hasattr(self.deaf_gene_sample_management, 'openDeafGeneAddDialog'):
            self.deaf_gene_sample_management.openDeafGeneAddDialog()
    
    def importDeafGeneData(self):
        self.switchDeafGeneModule('gene_analysis')
        if hasattr(self.deaf_gene_analysis, 'show_import_dialog'):
            self.deaf_gene_analysis.show_import_dialog()
    
    def importExcelAndGenerateDeafGeneReport(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import sys
        
        print(f"[耳聋基因检测系统] 用户尝试导入Excel文件生成报告", file=sys.stderr)
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择Excel文件",
            str(db.db_path.parent),
            "Excel文件 (*.xlsx *.xls);;CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
        
        if not hasattr(self, 'deaf_gene_analysis'):
            QMessageBox.warning(self, "权限不足", "您没有基因分析模块的访问权限")
            return
        
        try:
            self.switchDeafGeneModule('gene_analysis')
            if hasattr(self.deaf_gene_analysis, 'import_file_and_analyze'):
                self.deaf_gene_analysis.import_file_and_analyze(file_path)
                # 导入成功后记录到日志文件
                self._writeDeafGeneLog(f"Excel文件导入成功: {file_path}")
            else:
                QMessageBox.information(self, "提示", "请先在基因分析模块中完成数据解析")
                
        except AttributeError as e:
            QMessageBox.critical(self, "功能错误", f"基因分析模块缺少必要功能: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "导入错误", f"导入文件失败: {str(e)}")
            # 错误信息只显示给用户，不记录日志
            
    def performDeafGeneLogout(self):
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self, '确认退出',
            '确定要退出登录吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            auth_manager.logout()
            self._writeDeafGeneLog(f"用户{self.deaf_gene_cur_user['real_name']}退出登录")
            self._deafGeneSkipCloseConfirm = True
            self.close()
    
    def showDeafGeneAbout(self):
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
        
        if hasattr(self, '_deafGeneSkipCloseConfirm') and self._deafGeneSkipCloseConfirm:
            event.accept()
            return
        
        reply = QMessageBox.question(
            self, '确认退出',
            '确定要退出系统吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            auth_manager.logout()
            self._writeDeafGeneLog(f"用户{self.deaf_gene_cur_user['real_name']}关闭系统")
            event.accept()
        else:
            event.ignore()

    def _writeDeafGeneLog(self, message):
        """把耳聋基因系统的操作日志写入本地文件"""
        from datetime import datetime
        from pathlib import Path
        
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"deaf_gene_main_{datetime.now().strftime('%Y%m%d')}.log"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

