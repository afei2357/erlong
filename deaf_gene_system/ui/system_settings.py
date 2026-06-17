#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
系统设置界面（管理员权限）
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QTabWidget, QFrame, 
    QGroupBox, QDialog, QFormLayout, QLineEdit, QComboBox,
    QTextEdit, QFileDialog, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from core.database import db
from core.auth import auth_manager
from config import USER_ROLES, PERMISSIONS


class SystemSettings(QWidget):
    """系统设置界面"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("系统设置")
        title_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)
        
        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 3px solid #0078d4;
                font-weight: bold;
            }
        """)
        
        # 用户管理
        self.user_tab = self.create_user_management_tab()
        self.tab_widget.addTab(self.user_tab, "用户管理")
        
        # 模板管理
        self.template_tab = self.create_template_management_tab()
        self.tab_widget.addTab(self.template_tab, "模板管理")
        
        # 数据库维护
        self.database_tab = self.create_database_maintenance_tab()
        self.tab_widget.addTab(self.database_tab, "数据库维护")
        
        # 日志查看
        self.log_tab = self.create_log_view_tab()
        self.tab_widget.addTab(self.log_tab, "日志查看")
        
        layout.addWidget(self.tab_widget)
        
    def create_user_management_tab(self):
        """创建用户管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 操作按钮
        action_layout = QHBoxLayout()
        
        add_user_btn = QPushButton("➕ 新增用户")
        add_user_btn.clicked.connect(self.add_user)
        action_layout.addWidget(add_user_btn)
        
        edit_user_btn = QPushButton("✏️ 编辑用户")
        edit_user_btn.clicked.connect(self.edit_user)
        action_layout.addWidget(edit_user_btn)
        
        delete_user_btn = QPushButton("🗑️ 删除用户")
        delete_user_btn.clicked.connect(self.delete_user)
        action_layout.addWidget(delete_user_btn)
        
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
        
        # 用户表格
        self.user_table = QTableWidget()
        self.user_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 8px;
                gridline-color: #eee;
                color: #333;
            }
            QTableWidget::item {
                padding: 8px;
                color: #333;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
        """)
        
        # 设置列
        headers = ["用户名", "真实姓名", "角色", "创建时间", "最后登录"]
        self.user_table.setColumnCount(len(headers))
        self.user_table.setHorizontalHeaderLabels(headers)
        
        # 设置列宽
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # 设置行高
        self.user_table.verticalHeader().setDefaultSectionSize(40)
        self.user_table.verticalHeader().setVisible(False)
        
        # 设置选择模式
        self.user_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.user_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        layout.addWidget(self.user_table)
        
        return widget
        
    def create_template_management_tab(self):
        """创建模板管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 模板配置
        template_group = QGroupBox("报告模板配置")
        template_layout = QFormLayout()
        
        # 医院名称
        self.hospital_name_input = QLineEdit()
        self.hospital_name_input.setPlaceholderText("请输入医院名称")
        template_layout.addRow("医院名称:", self.hospital_name_input)
        
        # 报告页眉
        self.header_input = QTextEdit()
        self.header_input.setMaximumHeight(80)
        self.header_input.setPlaceholderText("请输入报告页眉内容")
        template_layout.addRow("报告页眉:", self.header_input)
        
        # 报告页脚
        self.footer_input = QTextEdit()
        self.footer_input.setMaximumHeight(80)
        self.footer_input.setPlaceholderText("请输入报告页脚内容")
        template_layout.addRow("报告页脚:", self.footer_input)
        
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)
        
        # 解读话术
        interpretation_group = QGroupBox("解读话术配置")
        interpretation_layout = QVBoxLayout()
        
        self.normal_interpretation = QTextEdit()
        self.normal_interpretation.setMaximumHeight(60)
        self.normal_interpretation.setPlaceholderText("正常结果解读话术")
        interpretation_layout.addWidget(QLabel("正常结果解读:"))
        interpretation_layout.addWidget(self.normal_interpretation)
        
        self.abnormal_interpretation = QTextEdit()
        self.abnormal_interpretation.setMaximumHeight(60)
        self.abnormal_interpretation.setPlaceholderText("异常结果解读话术")
        interpretation_layout.addWidget(QLabel("异常结果解读:"))
        interpretation_layout.addWidget(self.abnormal_interpretation)
        
        interpretation_group.setLayout(interpretation_layout)
        layout.addWidget(interpretation_group)
        
        # 保存按钮
        save_template_btn = QPushButton("💾 保存模板配置")
        save_template_btn.clicked.connect(self.save_template_config)
        layout.addWidget(save_template_btn)
        
        layout.addStretch()
        
        return widget
        
    def create_database_maintenance_tab(self):
        """创建数据库维护标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 数据库信息
        info_group = QGroupBox("数据库信息")
        info_layout = QFormLayout()
        
        self.db_path_label = QLabel()
        info_layout.addRow("数据库路径:", self.db_path_label)
        
        self.db_size_label = QLabel()
        info_layout.addRow("数据库大小:", self.db_size_label)
        
        self.backup_count_label = QLabel()
        info_layout.addRow("备份数量:", self.backup_count_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 维护操作
        action_group = QGroupBox("维护操作")
        action_layout = QVBoxLayout()
        
        # 备份数据库
        backup_btn = QPushButton("💾 备份数据库")
        backup_btn.clicked.connect(self.backup_database)
        action_layout.addWidget(backup_btn)
        
        # 还原数据库
        restore_btn = QPushButton("📂 还原数据库")
        restore_btn.clicked.connect(self.restore_database)
        action_layout.addWidget(restore_btn)
        
        # 清理日志
        cleanup_logs_btn = QPushButton("🧹 清理日志")
        cleanup_logs_btn.clicked.connect(self.cleanup_logs)
        action_layout.addWidget(cleanup_logs_btn)
        
        # 更新知识库
        update_knowledge_btn = QPushButton("📚 更新基因知识库")
        update_knowledge_btn.clicked.connect(self.update_knowledge_base)
        action_layout.addWidget(update_knowledge_btn)
        
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)
        
        layout.addStretch()
        
        return widget
        
    def create_log_view_tab(self):
        """创建日志查看标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 日志筛选
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("日志类型:"))
        self.log_type_filter = QComboBox()
        self.log_type_filter.addItem("全部", None)
        self.log_type_filter.addItem("登录日志", "login")
        self.log_type_filter.addItem("操作日志", "operation")
        self.log_type_filter.addItem("审核日志", "review")
        filter_layout.addWidget(self.log_type_filter)
        
        filter_layout.addWidget(QLabel("时间范围:"))
        self.log_date_filter = QComboBox()
        self.log_date_filter.addItem("今天", "today")
        self.log_date_filter.addItem("最近7天", "week")
        self.log_date_filter.addItem("最近30天", "month")
        self.log_date_filter.addItem("全部", "all")
        filter_layout.addWidget(self.log_date_filter)
        
        filter_layout.addStretch()
        
        refresh_logs_btn = QPushButton("🔄 刷新")
        refresh_logs_btn.clicked.connect(self.refresh_logs)
        filter_layout.addWidget(refresh_logs_btn)
        
        layout.addLayout(filter_layout)
        
        # 日志表格
        self.log_table = QTableWidget()
        self.log_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 8px;
                gridline-color: #eee;
                color: #333;
            }
            QTableWidget::item {
                padding: 8px;
                color: #333;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
        """)
        
        # 设置列
        headers = ["时间", "用户", "操作类型", "操作描述", "详细信息"]
        self.log_table.setColumnCount(len(headers))
        self.log_table.setHorizontalHeaderLabels(headers)
        
        # 设置列宽
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        # 设置行高
        self.log_table.verticalHeader().setDefaultSectionSize(40)
        self.log_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.log_table)
        
        return widget
        
    def load_settings(self):
        """加载设置"""
        try:
            # 加载用户列表
            self.load_users()
            
            # 加载数据库信息
            self.load_database_info()
            
            # 加载日志
            self.load_logs()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载设置失败: {str(e)}")
    
    def load_users(self):
        """加载用户列表"""
        try:
            cursor = db.execute_query("""
                SELECT id, username, real_name, role, created_at, last_login
                FROM users
                ORDER BY created_at DESC
            """)
            users = cursor.fetchall()
            
            self.user_table.setRowCount(len(users))
            
            for row, user in enumerate(users):
                user_dict = dict(user)
                self.user_table.setItem(row, 0, QTableWidgetItem(user_dict['username']))
                self.user_table.setItem(row, 1, QTableWidgetItem(user_dict.get('real_name', '')))
                
                role_item = QTableWidgetItem(USER_ROLES.get(user_dict['role'], user_dict['role']))
                self.set_role_color(role_item, user_dict['role'])
                self.user_table.setItem(row, 2, role_item)
                
                self.user_table.setItem(row, 3, QTableWidgetItem(self.format_datetime(user_dict.get('created_at', ''))))
                self.user_table.setItem(row, 4, QTableWidgetItem(self.format_datetime(user_dict.get('last_login', ''))))
                
        except Exception as e:
            print(f"加载用户列表失败: {e}")
    
    def set_role_color(self, item, role):
        """设置角色颜色"""
        color_map = {
            'admin': QColor('#9c27b0'),     # 紫色
            'doctor': QColor('#0078d4'),   # 蓝色
            'technician': QColor('#4caf50') # 绿色
        }
        
        color = color_map.get(role, QColor('#666'))
        item.setForeground(color)
    
    def load_database_info(self):
        """加载数据库信息"""
        try:
            from pathlib import Path
            
            db_path = db.db_path
            self.db_path_label.setText(str(db_path))
            
            # 获取文件大小
            if db_path.exists():
                size_bytes = db_path.stat().st_size
                size_mb = size_bytes / (1024 * 1024)
                self.db_size_label.setText(f"{size_mb:.2f} MB")
            else:
                self.db_size_label.setText("文件不存在")
            
            # 统计备份数量
            backup_dir = db.db_path.parent / "backups"
            if backup_dir.exists():
                backup_files = list(backup_dir.glob("*.db"))
                self.backup_count_label.setText(str(len(backup_files)))
            else:
                self.backup_count_label.setText("0")
                
        except Exception as e:
            print(f"加载数据库信息失败: {e}")
    
    def load_logs(self):
        """加载日志"""
        try:
            # 获取筛选条件
            log_type = self.log_type_filter.currentData()
            date_range = self.log_date_filter.currentData()
            
            # 构建查询条件
            conditions = []
            params = []
            
            if log_type:
                if log_type == "login":
                    conditions.append("action IN ('login', 'logout')")
                elif log_type == "operation":
                    conditions.append("action IN ('create', 'update', 'delete')")
                elif log_type == "review":
                    conditions.append("action = 'review'")
            
            if date_range and date_range != "all":
                if date_range == "today":
                    conditions.append("DATE(al.created_at) = DATE('now')")
                elif date_range == "week":
                    conditions.append("DATE(al.created_at) >= DATE('now', '-7 days')")
                elif date_range == "month":
                    conditions.append("DATE(al.created_at) >= DATE('now', '-30 days')")
            
            query = """
                SELECT al.*, u.real_name, u.username
                FROM audit_logs al
                LEFT JOIN users u ON al.user_id = u.id
            """
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY al.created_at DESC LIMIT 100"
            
            cursor = db.execute_query(query, tuple(params))
            logs = cursor.fetchall()
            
            self.log_table.setRowCount(len(logs))
            
            for row, log in enumerate(logs):
                log_dict = dict(log)
                self.log_table.setItem(row, 0, QTableWidgetItem(self.format_datetime(log_dict.get('created_at', ''))))
                self.log_table.setItem(row, 1, QTableWidgetItem(log_dict.get('real_name') or log_dict.get('username', '')))
                self.log_table.setItem(row, 2, QTableWidgetItem(log_dict.get('action', '')))
                self.log_table.setItem(row, 3, QTableWidgetItem(f"{log_dict.get('table_name', '')} {log_dict.get('action', '')}"))
                self.log_table.setItem(row, 4, QTableWidgetItem(log_dict.get('new_values', '')[:50] + '...' if len(log_dict.get('new_values', '')) > 50 else log_dict.get('new_values', '')))
                
        except Exception as e:
            print(f"加载日志失败: {e}")
    
    def add_user(self):
        """新增用户"""
        dialog = UserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            user_data = dialog.get_user_data()
            
            try:
                db.create_user(
                    username=user_data['username'],
                    password=user_data['password'],
                    role=user_data['role'],
                    real_name=user_data['real_name']
                )
                
                QMessageBox.information(self, "成功", "用户添加成功")
                self.load_users()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加用户失败: {str(e)}")
    
    def edit_user(self):
        """编辑用户"""
        current_row = self.user_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要编辑的用户")
            return
        
        username = self.user_table.item(current_row, 0).text()
        
        # 获取用户信息
        user = db.get_user_by_username(username)
        
        if user:
            dialog = UserDialog(self, user)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                user_data = dialog.get_user_data()
                
                try:
                    # 更新用户信息
                    if user_data.get('password'):
                        hashed_password = db.hash_password(user_data['password'])
                        db.execute_query(
                            "UPDATE users SET password = ? WHERE id = ?",
                            (hashed_password, user['id'])
                        )
                    
                    db.execute_query(
                        "UPDATE users SET real_name = ?, role = ? WHERE id = ?",
                        (user_data['real_name'], user_data['role'], user['id'])
                    )
                    db.commit()
                    
                    QMessageBox.information(self, "成功", "用户信息更新成功")
                    self.load_users()
                    
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"更新用户失败: {str(e)}")
    
    def delete_user(self):
        """删除用户"""
        current_row = self.user_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要删除的用户")
            return
        
        username = self.user_table.item(current_row, 0).text()
        
        # 不能删除当前登录用户
        if username == auth_manager.current_user['username']:
            QMessageBox.warning(self, "提示", "不能删除当前登录用户")
            return
        
        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除用户 "{username}" 吗？此操作不可恢复。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                db.execute_query("DELETE FROM users WHERE username = ?", (username,))
                db.commit()
                
                QMessageBox.information(self, "成功", "用户删除成功")
                self.load_users()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除用户失败: {str(e)}")
    
    def save_template_config(self):
        """保存模板配置"""
        QMessageBox.information(self, "提示", "模板配置保存功能开发中...")
    
    def backup_database(self):
        """备份数据库"""
        try:
            from pathlib import Path
            import shutil
            from datetime import datetime
            
            # 创建备份目录
            backup_dir = db.db_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"backup_{timestamp}.db"
            
            # 复制数据库文件
            shutil.copy2(db.db_path, backup_file)
            
            QMessageBox.information(self, "成功", f"数据库备份成功：{backup_file.name}")
            self.load_database_info()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"备份失败: {str(e)}")
    
    def restore_database(self):
        """还原数据库"""
        QMessageBox.information(self, "提示", "数据库还原功能开发中...")
    
    def cleanup_logs(self):
        """清理日志"""
        try:
            # 删除30天前的日志
            db.execute_query("""
                DELETE FROM audit_logs 
                WHERE DATE(created_at) < DATE('now', '-30 days')
            """)
            db.commit()
            
            QMessageBox.information(self, "成功", "日志清理完成")
            self.load_logs()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"清理日志失败: {str(e)}")
    
    def update_knowledge_base(self):
        """更新基因知识库"""
        QMessageBox.information(self, "提示", "基因知识库更新功能开发中...")
    
    def refresh_logs(self):
        """刷新日志"""
        self.load_logs()
    
    def format_datetime(self, datetime_str):
        """格式化日期时间"""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(datetime_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return datetime_str
    
    def refresh_data(self):
        """刷新数据"""
        self.load_settings()


class UserDialog(QDialog):
    """用户对话框"""
    
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.user = user
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        if self.user:
            self.setWindowTitle("编辑用户")
        else:
            self.setWindowTitle("新增用户")
        
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # 表单
        form_layout = QFormLayout()
        
        # 用户名
        self.username_input = QLineEdit()
        if self.user:
            self.username_input.setText(self.user['username'])
            self.username_input.setEnabled(False)
        else:
            self.username_input.setPlaceholderText("请输入用户名")
        form_layout.addRow("用户名*:", self.username_input)
        
        # 密码
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("请输入密码" if not self.user else "留空不修改密码")
        form_layout.addRow("密码*:" if not self.user else "密码:", self.password_input)
        
        # 真实姓名
        self.real_name_input = QLineEdit()
        if self.user:
            self.real_name_input.setText(self.user.get('real_name', ''))
        else:
            self.real_name_input.setPlaceholderText("请输入真实姓名")
        form_layout.addRow("真实姓名*:", self.real_name_input)
        
        # 角色
        self.role_combo = QComboBox()
        for role_key, role_name in USER_ROLES.items():
            self.role_combo.addItem(role_name, role_key)
        if self.user:
            index = self.role_combo.findData(self.user['role'])
            if index >= 0:
                self.role_combo.setCurrentIndex(index)
        form_layout.addRow("角色*:", self.role_combo)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.validate_and_save)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def validate_and_save(self):
        """验证并保存"""
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, "验证失败", "请输入用户名")
            return
        
        password = self.password_input.text().strip()
        if not self.user and not password:
            QMessageBox.warning(self, "验证失败", "请输入密码")
            return
        
        real_name = self.real_name_input.text().strip()
        if not real_name:
            QMessageBox.warning(self, "验证失败", "请输入真实姓名")
            return
        
        self.accept()
    
    def get_user_data(self):
        """获取用户数据"""
        return {
            'username': self.username_input.text().strip(),
            'password': self.password_input.text().strip(),
            'real_name': self.real_name_input.text().strip(),
            'role': self.role_combo.currentData()
        }