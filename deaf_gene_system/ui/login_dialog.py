#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 权属说明：登录模块，内部使用


from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QFrame, QMessageBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QIcon
from pathlib import Path

from config import SOFTWARE_INFO, USER_ROLES
from core.auth import auth_manager


class DeafGeneLoginException(Exception):
    pass


class DeafGeneLoginFailedException(DeafGeneLoginException):
    pass


class DeafGeneLoginRoleMismatchException(DeafGeneLoginException):
    pass


class DeafGeneLoginDialog(QDialog):
    login_successful = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self._login_attempts = 0
        self._last_attempt_time = None
        self._temp_login_cache = {}   # 临时缓存，调试时用过
        self.initDeafGeneLoginUI()

    def initDeafGeneLoginUI(self):
        self.setWindowTitle(f"{SOFTWARE_INFO['name']} - 登录")
        icon_path = Path(__file__).parent.parent / "images" / "logo.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.setFixedSize(500, 600)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        header_widget = self.createDeafGeneLoginHeader()
        main_layout.addWidget(header_widget)
        
        login_widget = self.createDeafGeneLoginArea()
        main_layout.addWidget(login_widget)
        
        footer_widget = self.createDeafGeneLoginFooter()
        main_layout.addWidget(footer_widget)
        
        self.setLayout(main_layout)
        self.centerDeafGeneLoginWindow()

    def createDeafGeneLoginHeader(self):
        header = QFrame()
        header.setFixedHeight(200)
        header.setStyleSheet("QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0078d4, stop:1 #00bcf2); }")
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo_label = QLabel()
        logo_label.setFixedSize(80, 80)
        logo_label.setStyleSheet("QLabel { background-color: white; border-radius: 40px; color: #0078d4; font-size: 40px; font-weight: bold; }")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setText("🧬")
        
        title_label = QLabel(SOFTWARE_INFO['name'])
        title_label.setStyleSheet("QLabel { color: white; font-size: 24px; font-weight: bold; margin-top: 10px; }")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle_label = QLabel("专业的耳聋基因检测与分析系统")
        subtitle_label.setStyleSheet("QLabel { color: rgba(255, 255, 255, 0.9); font-size: 12px; margin-top: 5px; }")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(logo_label)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        
        header.setLayout(layout)
        return header

    def createDeafGeneLoginArea(self):
        login_area = QFrame()
        login_area.setStyleSheet("QFrame { background-color: white; border-radius: 0 0 10px 10px; }")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        title_label = QLabel("用户登录")
        title_label.setStyleSheet("QLabel { color: #333; font-size: 18px; font-weight: bold; }")
        layout.addWidget(title_label)
        
        form_layout = QGridLayout()
        form_layout.setSpacing(15)
        
        username_label = QLabel("用户名:")
        username_label.setStyleSheet("color: #666;")
        self.deaf_gene_username_input = QLineEdit()
        self.deaf_gene_username_input.setPlaceholderText("请输入用户名")
        self.deaf_gene_username_input.setFixedHeight(40)
        
        form_layout.addWidget(username_label, 0, 0)
        form_layout.addWidget(self.deaf_gene_username_input, 0, 1)
        
        password_label = QLabel("密码:")
        password_label.setStyleSheet("color: #666;")
        self.deaf_gene_password_input = QLineEdit()
        self.deaf_gene_password_input.setPlaceholderText("请输入密码")
        self.deaf_gene_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.deaf_gene_password_input.setFixedHeight(40)
        
        form_layout.addWidget(password_label, 1, 0)
        form_layout.addWidget(self.deaf_gene_password_input, 1, 1)
        
        role_label = QLabel("权限:")
        role_label.setStyleSheet("color: #666;")
        self.deaf_gene_role_combo = QComboBox()
        self.deaf_gene_role_combo.setFixedHeight(40)
        for role_key, role_name in USER_ROLES.items():
            self.deaf_gene_role_combo.addItem(role_name, role_key)
        
        form_layout.addWidget(role_label, 2, 0)
        form_layout.addWidget(self.deaf_gene_role_combo, 2, 1)
        
        layout.addLayout(form_layout)
        
        forgot_password_btn = QPushButton("忘记密码?")
        forgot_password_btn.setStyleSheet("QPushButton { background-color: transparent; color: #0078d4; border: none; text-align: right; padding: 0; min-width: 0; } QPushButton:hover { text-decoration: underline; }")
        forgot_password_btn.clicked.connect(self.showDeafGeneForgotPassword)
        layout.addWidget(forgot_password_btn, 0, Qt.AlignmentFlag.AlignRight)
        
        self.deaf_gene_login_btn = QPushButton("登录")
        self.deaf_gene_login_btn.setFixedHeight(45)
        self.deaf_gene_login_btn.setStyleSheet("QPushButton { background-color: #0078d4; color: white; border: none; border-radius: 6px; font-size: 14px; font-weight: bold; } QPushButton:hover { background-color: #106ebe; } QPushButton:pressed { background-color: #005a9e; }")
        self.deaf_gene_login_btn.clicked.connect(self.performDeafGeneLogin)
        layout.addWidget(self.deaf_gene_login_btn)
        
        login_area.setLayout(layout)
        return login_area

    def createDeafGeneLoginFooter(self):
        footer = QFrame()
        footer.setFixedHeight(40)
        footer.setStyleSheet("QFrame { background-color: #f5f5f5; border-top: 1px solid #ddd; }")
        
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

    def centerDeafGeneLoginWindow(self):
        screen = self.screen()
        if screen:
            screen_geometry = screen.availableGeometry()
            win_center_x = (screen_geometry.width() - self.width()) // 2
            win_center_y = (screen_geometry.height() - self.height()) // 2
            self.move(win_center_x, win_center_y)
            
    def performDeafGeneLogin(self):
        from datetime import datetime
        import sys
        
        input_username = self.deaf_gene_username_input.text().strip()
        input_password = self.deaf_gene_password_input.text().strip()
        selected_role_key = self.deaf_gene_role_combo.currentData()
        
        if not input_username:
            QMessageBox.warning(self, "输入错误", "用户名不能为空，请重新输入")
            self.deaf_gene_username_input.setFocus()
            return
            
        if not input_password:
            QMessageBox.warning(self, "输入错误", "密码不能为空，请重新输入")
            self.deaf_gene_password_input.setFocus()
            return
            
        self._login_attempts += 1
        self._last_attempt_time = datetime.now()
        
        print(f"[耳聋基因检测系统] 用户登录尝试: {input_username}, 第{self._login_attempts}次", file=sys.stderr)
        
        try:
            login_result = auth_manager.login(input_username, input_password)
            
            if login_result['success']:
                user_info = login_result['user']
                actual_role = user_info['role']
                
                if actual_role != selected_role_key:
                    QMessageBox.warning(self, "权限不匹配", 
                        f"该账号的实际权限是 {user_info['role_name']}，请选择正确的权限类型")
                    return
                    
                print(f"[耳聋基因检测系统] 用户登录成功: {input_username}, 角色: {actual_role}", file=sys.stderr)
                
                self._logLoginToFile(f"登录成功: {input_username}")
                
                self.login_successful.emit(user_info)
                self.accept()
            else:
                QMessageBox.critical(self, "登录失败", 
                    f"用户名或密码错误，已尝试 {self._login_attempts} 次\n{login_result['message']}")
                    
                self._logLoginToFile(f"登录失败: {input_username} - {login_result['message']}")
                    
        except DeafGeneLoginRoleMismatchException:
            QMessageBox.warning(self, "权限错误", "所选权限与账号实际权限不符")
        except DeafGeneLoginFailedException as e:
            QMessageBox.critical(self, "登录异常", f"登录过程出现异常: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "系统错误", f"登录失败，请联系管理员: {str(e)}")
            
    def showDeafGeneForgotPassword(self):
        QMessageBox.information(self, "忘记密码", 
            "请联系系统管理员重置密码\n\n"
            "管理员电话：13317863934\n"
            "或者发送邮件至：huangzengfei@aonebio.com.cn")
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.performDeafGeneLogin()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
    
    def _logLoginToFile(self, message):
        from datetime import datetime
        from pathlib import Path
        
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"deaf_gene_login_{datetime.now().strftime('%Y%m%d')}.log"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
