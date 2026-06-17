#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
登录对话框
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QFrame, QMessageBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QIcon
from pathlib import Path

from config import SOFTWARE_INFO, USER_ROLES
from core.auth import auth_manager


class LoginDialog(QDialog):
    """登录对话框"""
    
    login_successful = pyqtSignal(dict)  # 登录成功信号
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(f"{SOFTWARE_INFO['name']} - 登录")
        icon_path = Path(__file__).parent.parent / "images" / "logo.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.setFixedSize(500, 600)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建头部区域
        header_widget = self.create_header()
        main_layout.addWidget(header_widget)
        
        # 创建登录区域
        login_widget = self.create_login_area()
        main_layout.addWidget(login_widget)
        
        # 创建底部区域
        footer_widget = self.create_footer()
        main_layout.addWidget(footer_widget)
        
        self.setLayout(main_layout)
        
        # 居中显示
        self.center_window()
        
    def create_header(self):
        """创建头部区域"""
        header = QFrame()
        header.setFixedHeight(200)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0078d4, stop:1 #00bcf2
                );
            }
        """)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo和标题
        logo_label = QLabel()
        logo_label.setFixedSize(80, 80)
        logo_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border-radius: 40px;
                color: #0078d4;
                font-size: 40px;
                font-weight: bold;
            }
        """)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setText("🧬")
        
        title_label = QLabel(SOFTWARE_INFO['name'])
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                margin-top: 10px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle_label = QLabel("专业的耳聋基因检测与分析系统")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                margin-top: 5px;
            }
        """)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(logo_label)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        
        header.setLayout(layout)
        return header
        
    def create_login_area(self):
        """创建登录区域"""
        login_area = QFrame()
        login_area.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 0 0 10px 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # 标题
        title_label = QLabel("用户登录")
        title_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)
        
        # 表单布局
        form_layout = QGridLayout()
        form_layout.setSpacing(15)
        
        # 用户名
        username_label = QLabel("用户名:")
        username_label.setStyleSheet("color: #666;")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        self.username_input.setFixedHeight(40)
        
        form_layout.addWidget(username_label, 0, 0)
        form_layout.addWidget(self.username_input, 0, 1)
        
        # 密码
        password_label = QLabel("密码:")
        password_label.setStyleSheet("color: #666;")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(40)
        
        form_layout.addWidget(password_label, 1, 0)
        form_layout.addWidget(self.password_input, 1, 1)
        
        # 权限选择
        role_label = QLabel("权限:")
        role_label.setStyleSheet("color: #666;")
        self.role_combo = QComboBox()
        self.role_combo.setFixedHeight(40)
        for role_key, role_name in USER_ROLES.items():
            self.role_combo.addItem(role_name, role_key)
        
        form_layout.addWidget(role_label, 2, 0)
        form_layout.addWidget(self.role_combo, 2, 1)
        
        layout.addLayout(form_layout)
        
        # 忘记密码
        forgot_password_btn = QPushButton("忘记密码?")
        forgot_password_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #0078d4;
                border: none;
                text-align: right;
                padding: 0;
                min-width: 0;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        forgot_password_btn.clicked.connect(self.forgot_password)
        layout.addWidget(forgot_password_btn, 0, Qt.AlignmentFlag.AlignRight)
        
        # 登录按钮
        self.login_btn = QPushButton("登录")
        self.login_btn.setFixedHeight(45)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)
        
        # 快捷登录提示
        hint_label = QLabel("默认账号: admin/admin123, doctor/doctor123, tech/tech123")
        hint_label.setStyleSheet("""
            QLabel {
                color: #999;
                font-size: 11px;
                text-align: center;
            }
        """)
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)
        
        login_area.setLayout(layout)
        return login_area
        
    def create_footer(self):
        """创建底部区域"""
        footer = QFrame()
        footer.setFixedHeight(40)
        footer.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-top: 1px solid #ddd;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 0, 20, 0)
        
        version_label = QLabel(f"版本 {SOFTWARE_INFO['version']}")
        version_label.setStyleSheet("color: #666; font-size: 11px;")
        
        copyright_label = QLabel(SOFTWARE_INFO['copyright'])
        copyright_label.setStyleSheet("color: #666; font-size: 11px;")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        layout.addWidget(version_label)
        layout.addStretch()
        layout.addWidget(copyright_label)
        
        footer.setLayout(layout)
        return footer
        
    def center_window(self):
        """窗口居中显示"""
        screen = self.screen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)
            
    def handle_login(self):
        """处理登录"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        selected_role = self.role_combo.currentData()
        
        # 验证输入
        if not username:
            QMessageBox.warning(self, "提示", "请输入用户名")
            self.username_input.setFocus()
            return
            
        if not password:
            QMessageBox.warning(self, "提示", "请输入密码")
            self.password_input.setFocus()
            return
            
        # 尝试登录
        result = auth_manager.login(username, password)
        
        if result['success']:
            user_info = result['user']
            
            # 检查权限是否匹配
            if user_info['role'] != selected_role:
                QMessageBox.warning(self, "提示", 
                    f"该账号的权限是 {user_info['role_name']}，请选择正确的权限")
                return
                
            # 登录成功
            self.login_successful.emit(user_info)
            self.accept()
        else:
            # 登录失败
            QMessageBox.critical(self, "登录失败", result['message'])
            
    def forgot_password(self):
        """忘记密码"""
        QMessageBox.information(self, "提示", 
            "请联系系统管理员重置密码\n\n"
            "管理员电话：400-XXX-XXXX\n"
            "或者发送邮件至：admin@hospital.com")
        
    def keyPressEvent(self, event):
        """键盘事件处理"""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.handle_login()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)