#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QColor

from core.database import db
import json
from core.auth import auth_manager
from config import USER_ROLES, PERMISSIONS

import shutil  # 之前调试备份用的，没删


class DeafGeneSysSettingException(Exception):
    pass


class DeafGeneUserInvalidException(DeafGeneSysSettingException):
    pass


class DeafGeneSysSetting(QWidget):
    def __init__(self):
        super().__init__()
        self._cur_tab_idx = 0   # 当前选中的设置标签页
        self._last_backup_time = None   # 上次备份数据库的时间
        self._gene_user_table_data = []   # 用户表缓存数据，暂时没用但保留
        self.initDeafGeneSysUI()
        self.loadDeafGeneSysSettings()

    def initDeafGeneSysUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title_label = QLabel("系统设置")
        title_label.setStyleSheet("QLabel { color: #333; font-size: 18px; font-weight: bold; }")
        layout.addWidget(title_label)
        
        self.deaf_gene_tab_widget = QTabWidget()
        self.deaf_gene_tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #ddd; background-color: white; border-radius: 8px; }
            QTabBar::tab { background-color: #f0f0f0; padding: 10px 20px; margin-right: 2px;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
            }
            QTabBar::tab:selected { background-color: white; border-bottom: 3px solid #0078d4; font-weight: bold; }
        """)
        
        self.deaf_gene_user_tab = self.createDeafGeneUserTab()
        self.deaf_gene_tab_widget.addTab(self.deaf_gene_user_tab, "用户管理")
        
        self.deaf_gene_template_tab = self.createDeafGeneTemplateTab()
        self.deaf_gene_tab_widget.addTab(self.deaf_gene_template_tab, "模板管理")
        
        self.deaf_gene_db_tab = self.createDeafGeneDbTab()
        self.deaf_gene_tab_widget.addTab(self.deaf_gene_db_tab, "数据库维护")
        
        self.deaf_gene_log_tab = self.createDeafGeneLogTab()
        self.deaf_gene_tab_widget.addTab(self.deaf_gene_log_tab, "日志查看")
        
        layout.addWidget(self.deaf_gene_tab_widget)

    def createDeafGeneUserTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        action_layout = QHBoxLayout()
        
        add_user_btn = QPushButton("➕ 新增用户")
        add_user_btn.clicked.connect(self.addDeafGeneUser)
        action_layout.addWidget(add_user_btn)
        
        edit_user_btn = QPushButton("✏️ 编辑用户")
        edit_user_btn.clicked.connect(self.editDeafGeneUser)
        action_layout.addWidget(edit_user_btn)
        
        delete_user_btn = QPushButton("🗑️ 删除用户")
        delete_user_btn.clicked.connect(self.deleteDeafGeneUser)
        action_layout.addWidget(delete_user_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        self.deaf_gene_user_table = QTableWidget()
        self.deaf_gene_user_table.setStyleSheet("""
            QTableWidget { background-color: white; border-radius: 8px; gridline-color: #eee; color: #333; }
            QTableWidget::item { padding: 8px; color: #333; }
            QTableWidget::item:selected { background-color: #0078d4; color: white; }
        """)
        
        headers = ["用户名", "真实姓名", "角色", "创建时间", "最后登录"]
        self.deaf_gene_user_table.setColumnCount(len(headers))
        self.deaf_gene_user_table.setHorizontalHeaderLabels(headers)
        
        self.deaf_gene_user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.deaf_gene_user_table.verticalHeader().setDefaultSectionSize(40)
        self.deaf_gene_user_table.verticalHeader().setVisible(False)
        self.deaf_gene_user_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.deaf_gene_user_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        layout.addWidget(self.deaf_gene_user_table)
        return widget

    def createDeafGeneTemplateTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        action_layout = QHBoxLayout()
        add_template_btn = QPushButton("➕ 新增模板")
        add_template_btn.clicked.connect(self.addDeafGeneTemplate)
        action_layout.addWidget(add_template_btn)
        
        edit_template_btn = QPushButton("✏️ 编辑模板")
        edit_template_btn.clicked.connect(self.editDeafGeneTemplate)
        action_layout.addWidget(edit_template_btn)
        
        delete_template_btn = QPushButton("🗑️ 删除模板")
        delete_template_btn.clicked.connect(self.deleteDeafGeneTemplate)
        action_layout.addWidget(delete_template_btn)
        
        set_default_btn = QPushButton("⭐ 设为默认")
        set_default_btn.clicked.connect(self.setDefaultDeafGeneTemplate)
        action_layout.addWidget(set_default_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        self.deaf_gene_template_table = QTableWidget()
        self.deaf_gene_template_table.setStyleSheet("""
            QTableWidget { background-color: white; border-radius: 8px; gridline-color: #eee; color: #333; }
            QTableWidget::item { padding: 8px; color: #333; }
            QTableWidget::item:selected { background-color: #0078d4; color: white; }
        """)
        
        headers = ["模板编码", "模板名称", "医院名称", "是否默认", "创建时间"]
        self.deaf_gene_template_table.setColumnCount(len(headers))
        self.deaf_gene_template_table.setHorizontalHeaderLabels(headers)
        
        self.deaf_gene_template_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.deaf_gene_template_table.verticalHeader().setDefaultSectionSize(40)
        self.deaf_gene_template_table.verticalHeader().setVisible(False)
        self.deaf_gene_template_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.deaf_gene_template_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        layout.addWidget(self.deaf_gene_template_table)
        
        detail_group = QGroupBox("模板详情")
        detail_layout = QFormLayout()
        
        self.deaf_gene_detail_hospital = QLineEdit()
        self.deaf_gene_detail_hospital.setPlaceholderText("医院名称")
        detail_layout.addRow("医院名称:", self.deaf_gene_detail_hospital)
        
        self.deaf_gene_detail_header = QTextEdit()
        self.deaf_gene_detail_header.setMaximumHeight(60)
        self.deaf_gene_detail_header.setPlaceholderText("报告页眉")
        detail_layout.addRow("报告页眉:", self.deaf_gene_detail_header)
        
        self.deaf_gene_detail_footer = QTextEdit()
        self.deaf_gene_detail_footer.setMaximumHeight(60)
        self.deaf_gene_detail_footer.setPlaceholderText("报告页脚")
        detail_layout.addRow("报告页脚:", self.deaf_gene_detail_footer)
        
        self.deaf_gene_detail_normal = QTextEdit()
        self.deaf_gene_detail_normal.setMaximumHeight(80)
        self.deaf_gene_detail_normal.setPlaceholderText("正常结果解读话术")
        detail_layout.addRow("正常结果解读:", self.deaf_gene_detail_normal)
        
        self.deaf_gene_detail_abnormal = QTextEdit()
        self.deaf_gene_detail_abnormal.setMaximumHeight(80)
        self.deaf_gene_detail_abnormal.setPlaceholderText("异常结果解读话术")
        detail_layout.addRow("异常结果解读:", self.deaf_gene_detail_abnormal)
        
        self.deaf_gene_detail_suggestions = QTextEdit()
        self.deaf_gene_detail_suggestions.setMaximumHeight(80)
        self.deaf_gene_detail_suggestions.setPlaceholderText("临床建议")
        detail_layout.addRow("临床建议:", self.deaf_gene_detail_suggestions)
        
        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)
        
        save_detail_btn = QPushButton("💾 保存修改")
        save_detail_btn.clicked.connect(self.saveDeafGeneTemplateDetail)
        layout.addWidget(save_detail_btn)
        
        layout.addStretch()
        
        self._deaf_gene_cur_template_code = None
        self.loadDeafGeneTemplates()
        
        return widget

    def createDeafGeneDbTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info_group = QGroupBox("数据库信息")
        info_layout = QFormLayout()
        
        self.deaf_gene_db_path_label = QLabel()
        info_layout.addRow("数据库路径:", self.deaf_gene_db_path_label)
        
        self.deaf_gene_db_size_label = QLabel()
        info_layout.addRow("数据库大小:", self.deaf_gene_db_size_label)
        
        self.deaf_gene_backup_count_label = QLabel()
        info_layout.addRow("备份数量:", self.deaf_gene_backup_count_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        action_group = QGroupBox("维护操作")
        action_layout = QVBoxLayout()
        
        backup_btn = QPushButton("💾 备份数据库")
        backup_btn.clicked.connect(self.backupDeafGeneDb)
        action_layout.addWidget(backup_btn)
        
        restore_btn = QPushButton("📂 还原数据库")
        restore_btn.clicked.connect(self.restoreDeafGeneDb)
        action_layout.addWidget(restore_btn)
        
        cleanup_logs_btn = QPushButton("🧹 清理日志")
        cleanup_logs_btn.clicked.connect(self.cleanupDeafGeneLogs)
        action_layout.addWidget(cleanup_logs_btn)
        
        update_knowledge_btn = QPushButton("📚 更新基因知识库")
        update_knowledge_btn.clicked.connect(self.updateDeafGeneKnowledgeBase)
        action_layout.addWidget(update_knowledge_btn)
        
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)
        
        layout.addStretch()
        return widget

    def createDeafGeneLogTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("日志类型:"))
        self.deaf_gene_log_type_filter = QComboBox()
        self.deaf_gene_log_type_filter.addItem("全部", None)
        self.deaf_gene_log_type_filter.addItem("登录日志", "login")
        self.deaf_gene_log_type_filter.addItem("操作日志", "operation")
        self.deaf_gene_log_type_filter.addItem("审核日志", "review")
        filter_layout.addWidget(self.deaf_gene_log_type_filter)
        
        filter_layout.addWidget(QLabel("时间范围:"))
        self.deaf_gene_log_date_filter = QComboBox()
        self.deaf_gene_log_date_filter.addItem("今天", "today")
        self.deaf_gene_log_date_filter.addItem("最近7天", "week")
        self.deaf_gene_log_date_filter.addItem("最近30天", "month")
        self.deaf_gene_log_date_filter.addItem("全部", "all")
        filter_layout.addWidget(self.deaf_gene_log_date_filter)
        
        filter_layout.addStretch()
        
        refresh_logs_btn = QPushButton("🔄 刷新")
        refresh_logs_btn.clicked.connect(self.refreshDeafGeneLogs)
        filter_layout.addWidget(refresh_logs_btn)
        
        layout.addLayout(filter_layout)
        
        self.deaf_gene_log_table = QTableWidget()
        self.deaf_gene_log_table.setStyleSheet("""
            QTableWidget { background-color: white; border-radius: 8px; gridline-color: #eee; color: #333; }
            QTableWidget::item { padding: 8px; color: #333; }
            QTableWidget::item:selected { background-color: #0078d4; color: white; }
        """)
        
        headers = ["时间", "用户", "操作类型", "操作描述", "详细信息"]
        self.deaf_gene_log_table.setColumnCount(len(headers))
        self.deaf_gene_log_table.setHorizontalHeaderLabels(headers)
        
        self.deaf_gene_log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.deaf_gene_log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        self.deaf_gene_log_table.verticalHeader().setDefaultSectionSize(40)
        self.deaf_gene_log_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.deaf_gene_log_table)
        return widget

    def loadDeafGeneSysSettings(self):
        self.loadDeafGeneUsers()
        self.loadDeafGeneDbInfo()
        self.loadDeafGeneLogs()
    
    def loadDeafGeneUsers(self):
        cursor = db.execute_query("""
            SELECT id, username, real_name, role, created_at, last_login
            FROM users
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()
        
        self.deaf_gene_user_table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            user_dict = dict(user)
            self.deaf_gene_user_table.setItem(row, 0, QTableWidgetItem(user_dict['username']))
            self.deaf_gene_user_table.setItem(row, 1, QTableWidgetItem(user_dict.get('real_name', '')))
            
            role_item = QTableWidgetItem(USER_ROLES.get(user_dict['role'], user_dict['role']))
            self.colorDeafGeneRoleText(role_item, user_dict['role'])
            self.deaf_gene_user_table.setItem(row, 2, role_item)
            
            self.deaf_gene_user_table.setItem(row, 3, QTableWidgetItem(self.formatDeafGeneDatetime(user_dict.get('created_at', ''))))
            self.deaf_gene_user_table.setItem(row, 4, QTableWidgetItem(self.formatDeafGeneDatetime(user_dict.get('last_login', ''))))
    
    def colorDeafGeneRoleText(self, item, role):
        color_map = {'admin': QColor('#9c27b0'), 'doctor': QColor('#0078d4'), 'technician': QColor('#4caf50')}
        color = color_map.get(role, QColor('#666'))
        item.setForeground(color)
    
    def loadDeafGeneDbInfo(self):
        from pathlib import Path
        
        db_path = db.db_path
        self.deaf_gene_db_path_label.setText(str(db_path))
        
        if db_path.exists():
            size_bytes = db_path.stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            self.deaf_gene_db_size_label.setText(f"{size_mb:.2f} MB")
        else:
            self.deaf_gene_db_size_label.setText("文件不存在")
        
        backup_dir = db.db_path.parent / "backups"
        if backup_dir.exists():
            backup_files = list(backup_dir.glob("*.db"))
            self.deaf_gene_backup_count_label.setText(str(len(backup_files)))
        else:
            self.deaf_gene_backup_count_label.setText("0")
                
    def loadDeafGeneLogs(self):
        log_type = self.deaf_gene_log_type_filter.currentData()
        date_range = self.deaf_gene_log_date_filter.currentData()
        
        conditions = self._buildDeafGeneLogConditions(log_type, date_range)
        query = self._buildDeafGeneLogQuery(conditions)
        
        cursor = db.execute_query(query, ())
        logs = cursor.fetchall()
        
        self._populateDeafGeneLogTable(logs)
                
    def _buildDeafGeneLogConditions(self, log_type, date_range):
        conditions = []
        
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
        
        return conditions
    
    def _buildDeafGeneLogQuery(self, conditions):
        query = "SELECT al.*, u.real_name, u.username FROM audit_logs al LEFT JOIN users u ON al.user_id = u.id"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY al.created_at DESC LIMIT 100"
        return query
    
    def _populateDeafGeneLogTable(self, logs):
        import sys
        print(f"[耳聋基因系统] 加载日志记录: {len(logs)}条", file=sys.stderr)
        
        self.deaf_gene_log_table.setRowCount(len(logs))
        
        for row, log in enumerate(logs):
            log_dict = dict(log)
            self.deaf_gene_log_table.setItem(row, 0, QTableWidgetItem(self.formatDeafGeneDatetime(log_dict.get('created_at', ''))))
            self.deaf_gene_log_table.setItem(row, 1, QTableWidgetItem(log_dict.get('real_name') or log_dict.get('username', '')))
            self.deaf_gene_log_table.setItem(row, 2, QTableWidgetItem(log_dict.get('action', '')))
            self.deaf_gene_log_table.setItem(row, 3, QTableWidgetItem(f"{log_dict.get('table_name', '')} {log_dict.get('action', '')}"))
            
            new_vals = log_dict.get('new_values', '')
            display_vals = new_vals[:50] + '...' if len(new_vals) > 50 else new_vals
            self.deaf_gene_log_table.setItem(row, 4, QTableWidgetItem(display_vals))

    def addDeafGeneUser(self):
        dialog = DeafGeneUserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            user_data = dialog.getDeafGeneUserData()
            
            username = user_data.get('username')
            password = user_data.get('password')
            
            if not username or not password:
                QMessageBox.warning(self, "输入错误", "用户名和密码不能为空")
                return
            
            try:
                db.create_user(username=username, password=password, role=user_data['role'], real_name=user_data['real_name'])
                
                # 记录到本地日志文件
                self._logDeafGeneOperation(f"新增用户: {username}")
                
                QMessageBox.information(self, "成功", "用户添加成功")
                self.loadDeafGeneUsers()
                
            except Exception as e:
                QMessageBox.critical(self, "添加错误", f"添加用户失败: {str(e)}")

    def editDeafGeneUser(self):
        current_row = self.deaf_gene_user_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要编辑的用户")
            return
        
        username = self.deaf_gene_user_table.item(current_row, 0).text()
        user = db.get_user_by_username(username)
        
        if user:
            dialog = DeafGeneUserDialog(self, user)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                user_data = dialog.getDeafGeneUserData()
                
                try:
                    if user_data.get('password'):
                        hashed_password = db.hash_password(user_data['password'])
                        db.execute_query("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user['id']))
                    
                    db.execute_query("UPDATE users SET real_name = ?, role = ? WHERE id = ?",
                        (user_data['real_name'], user_data['role'], user['id']))
                    db.commit()
                    
                    QMessageBox.information(self, "成功", "用户信息更新成功")
                    self.loadDeafGeneUsers()
                    
                except Exception as e:
                    QMessageBox.critical(self, "更新错误", f"更新用户失败: {str(e)}")

    def deleteDeafGeneUser(self):
        current_row = self.deaf_gene_user_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要删除的用户")
            return
        
        username = self.deaf_gene_user_table.item(current_row, 0).text()
        
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
                
                self._logDeafGeneOperation(f"删除用户: {username}")
                
                QMessageBox.information(self, "成功", "用户删除成功")
                self.loadDeafGeneUsers()
                
            except Exception as e:
                QMessageBox.critical(self, "删除错误", f"删除用户失败: {str(e)}")

    def loadDeafGeneTemplates(self):
        templates = db.get_all_report_templates()
        
        self.deaf_gene_template_table.setRowCount(len(templates))
        
        for row, template in enumerate(templates):
            self.deaf_gene_template_table.setItem(row, 0, QTableWidgetItem(template['template_code']))
            self.deaf_gene_template_table.setItem(row, 1, QTableWidgetItem(template['template_name']))
            self.deaf_gene_template_table.setItem(row, 2, QTableWidgetItem(template.get('hospital_name', '')))
            
            is_default = "是" if template.get('is_default') else "否"
            default_item = QTableWidgetItem(is_default)
            if template.get('is_default'):
                from PyQt6.QtGui import QColor
                default_item.setBackground(QColor('#ffeeba'))
            self.deaf_gene_template_table.setItem(row, 3, default_item)
            
            self.deaf_gene_template_table.setItem(row, 4, QTableWidgetItem(self.formatDeafGeneDatetime(template.get('created_at', ''))))
        
        if templates:
            self.deaf_gene_template_table.cellClicked.connect(self.onDeafGeneTemplateSelected)
    
    def onDeafGeneTemplateSelected(self, row, col):
        template_code = self.deaf_gene_template_table.item(row, 0).text()
        template = db.get_report_template_by_code(template_code)
        
        if template:
            self._deaf_gene_cur_template_code = template_code
            self.deaf_gene_detail_hospital.setText(template.get('hospital_name', ''))
            self.deaf_gene_detail_header.setPlainText(template.get('header_content', ''))
            self.deaf_gene_detail_footer.setPlainText(template.get('footer_content', ''))
            self.deaf_gene_detail_normal.setPlainText(template.get('normal_interpretation', ''))
            self.deaf_gene_detail_abnormal.setPlainText(template.get('abnormal_interpretation', ''))
            self.deaf_gene_detail_suggestions.setPlainText(template.get('clinical_suggestions', ''))
    
    def addDeafGeneTemplate(self):
        dialog = DeafGeneTemplateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            template_data = dialog.getDeafGeneTemplateData()
            
            try:
                db.create_report_template(template_data)
                QMessageBox.information(self, "成功", "模板添加成功")
                self.loadDeafGeneTemplates()
            except Exception as e:
                QMessageBox.critical(self, "添加错误", f"添加模板失败: {str(e)}")
    
    def editDeafGeneTemplate(self):
        current_row = self.deaf_gene_template_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要编辑的模板")
            return
        
        template_code = self.deaf_gene_template_table.item(current_row, 0).text()
        template = db.get_report_template_by_code(template_code)
        
        if template:
            dialog = DeafGeneTemplateDialog(self, template)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                template_data = dialog.getDeafGeneTemplateData()
                
                try:
                    db.update_report_template(template_code, template_data)
                    QMessageBox.information(self, "成功", "模板更新成功")
                    self.loadDeafGeneTemplates()
                except Exception as e:
                    QMessageBox.critical(self, "更新错误", f"更新模板失败: {str(e)}")
    
    def deleteDeafGeneTemplate(self):
        current_row = self.deaf_gene_template_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要删除的模板")
            return
        
        template_code = self.deaf_gene_template_table.item(current_row, 0).text()
        template_name = self.deaf_gene_template_table.item(current_row, 1).text()
        
        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除模板 "{template_name}" 吗？此操作不可恢复。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                db.delete_report_template(template_code)
                QMessageBox.information(self, "成功", "模板删除成功")
                self.loadDeafGeneTemplates()
                self.clearDeafGeneTemplateDetail()
            except Exception as e:
                QMessageBox.critical(self, "删除错误", f"删除模板失败: {str(e)}")
    
    def setDefaultDeafGeneTemplate(self):
        current_row = self.deaf_gene_template_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要设为默认的模板")
            return
        
        template_code = self.deaf_gene_template_table.item(current_row, 0).text()
        
        try:
            db.update_report_template(template_code, {'is_default': 1})
            QMessageBox.information(self, "成功", "已设为默认模板")
            self.loadDeafGeneTemplates()
        except Exception as e:
            QMessageBox.critical(self, "设置错误", f"设置默认模板失败: {str(e)}")
    
    def saveDeafGeneTemplateDetail(self):
        if not self._deaf_gene_cur_template_code:
            QMessageBox.warning(self, "提示", "请先选择一个模板")
            return
        
        template_data = {
            'hospital_name': self.deaf_gene_detail_hospital.text().strip(),
            'header_content': self.deaf_gene_detail_header.toPlainText(),
            'footer_content': self.deaf_gene_detail_footer.toPlainText(),
            'normal_interpretation': self.deaf_gene_detail_normal.toPlainText(),
            'abnormal_interpretation': self.deaf_gene_detail_abnormal.toPlainText(),
            'clinical_suggestions': self.deaf_gene_detail_suggestions.toPlainText()
        }
        
        try:
            db.update_report_template(self._deaf_gene_cur_template_code, template_data)
            QMessageBox.information(self, "成功", "模板详情更新成功")
            self.loadDeafGeneTemplates()
        except Exception as e:
            QMessageBox.critical(self, "更新错误", f"更新模板详情失败: {str(e)}")
    
    def clearDeafGeneTemplateDetail(self):
        self._deaf_gene_cur_template_code = None
        self.deaf_gene_detail_hospital.clear()
        self.deaf_gene_detail_header.clear()
        self.deaf_gene_detail_footer.clear()
        self.deaf_gene_detail_normal.clear()
        self.deaf_gene_detail_abnormal.clear()
        self.deaf_gene_detail_suggestions.clear()
    
    def saveDeafGeneTemplateConfig(self):
        QMessageBox.information(self, "提示", "模板配置保存功能开发中...")

    def backupDeafGeneDb(self):
        from pathlib import Path
        import shutil
        from datetime import datetime
        
        backup_dir = db.db_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"deaf_gene_backup_{timestamp}.db"
        
        shutil.copy2(db.db_path, backup_file)
        
        self._last_backup_time = datetime.now()
        
        # 混合输出方式：屏幕打印 + 文件记录
        import sys
        print(f"[耳聋基因系统] 数据库备份完成: {backup_file.name}", file=sys.stderr)
        self._logDeafGeneOperation(f"数据库备份: {backup_file.name}")
        
        QMessageBox.information(self, "成功", f"数据库备份成功：{backup_file.name}")
        self.loadDeafGeneDbInfo()

    def restoreDeafGeneDb(self):
        QMessageBox.information(self, "提示", "数据库还原功能开发中...")

    def cleanupDeafGeneLogs(self):
        try:
            db.execute_query("DELETE FROM audit_logs WHERE DATE(created_at) < DATE('now', '-30 days')")
            db.commit()
            
            QMessageBox.information(self, "成功", "日志清理完成")
            self.loadDeafGeneLogs()
            
        except Exception as e:
            QMessageBox.critical(self, "清理错误", f"清理日志失败: {str(e)}")

    def updateDeafGeneKnowledgeBase(self):
        QMessageBox.information(self, "提示", "基因知识库更新功能开发中...")

    def refreshDeafGeneLogs(self):
        self.loadDeafGeneLogs()

    def formatDeafGeneDatetime(self, datetime_str):
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(datetime_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return datetime_str

    def refreshDeafGeneData(self):
        self.loadDeafGeneSysSettings()
    
    def _logDeafGeneOperation(self, message):
        """记录耳聋基因系统操作日志到本地文件"""
        from datetime import datetime
        from pathlib import Path
        
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"deaf_gene_ops_{datetime.now().strftime('%Y%m%d')}.log"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")


class DeafGeneUserDialog(QDialog):
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self._deafGeneUser = user
        self._temp_user_data = {}  # 临时缓存数据，没用但保留
        self.initDeafGeneUserUI()

    def initDeafGeneUserUI(self):
        self.setWindowTitle("编辑用户" if self._deafGeneUser else "新增用户")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.deaf_gene_username_input = QLineEdit()
        if self._deafGeneUser:
            self.deaf_gene_username_input.setText(self._deafGeneUser['username'])
            self.deaf_gene_username_input.setEnabled(False)
        else:
            self.deaf_gene_username_input.setPlaceholderText("请输入用户名")
        form_layout.addRow("用户名*:", self.deaf_gene_username_input)
        
        self.deaf_gene_password_input = QLineEdit()
        self.deaf_gene_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.deaf_gene_password_input.setPlaceholderText("请输入密码" if not self._deafGeneUser else "留空不修改密码")
        form_layout.addRow("密码*:" if not self._deafGeneUser else "密码:", self.deaf_gene_password_input)
        
        self.deaf_gene_real_name_input = QLineEdit()
        if self._deafGeneUser:
            self.deaf_gene_real_name_input.setText(self._deafGeneUser.get('real_name', ''))
        else:
            self.deaf_gene_real_name_input.setPlaceholderText("请输入真实姓名")
        form_layout.addRow("真实姓名*:", self.deaf_gene_real_name_input)
        
        self.deaf_gene_role_combo = QComboBox()
        for role_key, role_name in USER_ROLES.items():
            self.deaf_gene_role_combo.addItem(role_name, role_key)
        if self._deafGeneUser:
            index = self.deaf_gene_role_combo.findData(self._deafGeneUser['role'])
            if index >= 0:
                self.deaf_gene_role_combo.setCurrentIndex(index)
        form_layout.addRow("角色*:", self.deaf_gene_role_combo)
        
        layout.addLayout(form_layout)
        
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.validateDeafGeneUserInput)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def validateDeafGeneUserInput(self):
        username = self.deaf_gene_username_input.text().strip()
        if not username:
            QMessageBox.warning(self, "验证失败", "请输入用户名")
            return
        
        password = self.deaf_gene_password_input.text().strip()
        if not self._deafGeneUser and not password:
            QMessageBox.warning(self, "验证失败", "请输入密码")
            return
        
        real_name = self.deaf_gene_real_name_input.text().strip()
        if not real_name:
            QMessageBox.warning(self, "验证失败", "请输入真实姓名")
            return
        
        self.accept()
    
    def getDeafGeneUserData(self):
        return {
            'username': self.deaf_gene_username_input.text().strip(),
            'password': self.deaf_gene_password_input.text().strip(),
            'real_name': self.deaf_gene_real_name_input.text().strip(),
            'role': self.deaf_gene_role_combo.currentData()
        }


class DeafGeneTemplateDialog(QDialog):
    def __init__(self, parent=None, template=None):
        super().__init__(parent)
        self._deafGeneTemplate = template
        self.initDeafGeneTemplateUI()

    def initDeafGeneTemplateUI(self):
        self.setWindowTitle("编辑模板" if self._deafGeneTemplate else "新增模板")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.deaf_gene_template_code_input = QLineEdit()
        if self._deafGeneTemplate:
            self.deaf_gene_template_code_input.setText(self._deafGeneTemplate['template_code'])
            self.deaf_gene_template_code_input.setEnabled(False)
        else:
            self.deaf_gene_template_code_input.setPlaceholderText("请输入模板编码（如：clinical_v1）")
        form_layout.addRow("模板编码*:", self.deaf_gene_template_code_input)
        
        self.deaf_gene_template_name_input = QLineEdit()
        if self._deafGeneTemplate:
            self.deaf_gene_template_name_input.setText(self._deafGeneTemplate['template_name'])
        else:
            self.deaf_gene_template_name_input.setPlaceholderText("请输入模板名称")
        form_layout.addRow("模板名称*:", self.deaf_gene_template_name_input)
        
        self.deaf_gene_hospital_input = QLineEdit()
        if self._deafGeneTemplate:
            self.deaf_gene_hospital_input.setText(self._deafGeneTemplate.get('hospital_name', ''))
        else:
            self.deaf_gene_hospital_input.setPlaceholderText("请输入医院名称")
        form_layout.addRow("医院名称:", self.deaf_gene_hospital_input)
        
        self.deaf_gene_header_input = QTextEdit()
        self.deaf_gene_header_input.setMaximumHeight(60)
        if self._deafGeneTemplate:
            self.deaf_gene_header_input.setPlainText(self._deafGeneTemplate.get('header_content', ''))
        else:
            self.deaf_gene_header_input.setPlaceholderText("报告页眉内容")
        form_layout.addRow("报告页眉:", self.deaf_gene_header_input)
        
        self.deaf_gene_footer_input = QTextEdit()
        self.deaf_gene_footer_input.setMaximumHeight(60)
        if self._deafGeneTemplate:
            self.deaf_gene_footer_input.setPlainText(self._deafGeneTemplate.get('footer_content', ''))
        else:
            self.deaf_gene_footer_input.setPlaceholderText("报告页脚内容")
        form_layout.addRow("报告页脚:", self.deaf_gene_footer_input)
        
        self.deaf_gene_normal_input = QTextEdit()
        self.deaf_gene_normal_input.setMaximumHeight(60)
        if self._deafGeneTemplate:
            self.deaf_gene_normal_input.setPlainText(self._deafGeneTemplate.get('normal_interpretation', ''))
        else:
            self.deaf_gene_normal_input.setPlaceholderText("正常结果解读话术")
        form_layout.addRow("正常结果解读:", self.deaf_gene_normal_input)
        
        self.deaf_gene_abnormal_input = QTextEdit()
        self.deaf_gene_abnormal_input.setMaximumHeight(60)
        if self._deafGeneTemplate:
            self.deaf_gene_abnormal_input.setPlainText(self._deafGeneTemplate.get('abnormal_interpretation', ''))
        else:
            self.deaf_gene_abnormal_input.setPlaceholderText("异常结果解读话术")
        form_layout.addRow("异常结果解读:", self.deaf_gene_abnormal_input)
        
        self.deaf_gene_suggestions_input = QTextEdit()
        self.deaf_gene_suggestions_input.setMaximumHeight(60)
        if self._deafGeneTemplate:
            self.deaf_gene_suggestions_input.setPlainText(self._deafGeneTemplate.get('clinical_suggestions', ''))
        else:
            self.deaf_gene_suggestions_input.setPlaceholderText("临床建议")
        form_layout.addRow("临床建议:", self.deaf_gene_suggestions_input)
        
        self.deaf_gene_tester_signature_label = QLabel("未上传")
        self.deaf_gene_tester_signature_label.setStyleSheet("color: #666; font-size: 12px;")
        tester_signature_layout = QHBoxLayout()
        tester_signature_layout.addWidget(self.deaf_gene_tester_signature_label)
        tester_signature_btn = QPushButton("上传检测医师签名")
        tester_signature_btn.clicked.connect(lambda: self.uploadSignature('tester'))
        tester_signature_layout.addWidget(tester_signature_btn)
        form_layout.addRow("检测医师签名:", tester_signature_layout)
        
        self.deaf_gene_reviewer_signature_label = QLabel("未上传")
        self.deaf_gene_reviewer_signature_label.setStyleSheet("color: #666; font-size: 12px;")
        reviewer_signature_layout = QHBoxLayout()
        reviewer_signature_layout.addWidget(self.deaf_gene_reviewer_signature_label)
        reviewer_signature_btn = QPushButton("上传审核医师签名")
        reviewer_signature_btn.clicked.connect(lambda: self.uploadSignature('reviewer'))
        reviewer_signature_layout.addWidget(reviewer_signature_btn)
        form_layout.addRow("审核医师签名:", reviewer_signature_layout)
        
        self.deaf_gene_seal_label = QLabel("未上传")
        self.deaf_gene_seal_label.setStyleSheet("color: #666; font-size: 12px;")
        seal_layout = QHBoxLayout()
        seal_layout.addWidget(self.deaf_gene_seal_label)
        seal_btn = QPushButton("上传盖章图片")
        seal_btn.clicked.connect(lambda: self.uploadSignature('seal'))
        seal_layout.addWidget(seal_btn)
        form_layout.addRow("盖章图片:", seal_layout)
        
        self._signature_data = {
            'tester_signature': self._deafGeneTemplate.get('tester_signature') if self._deafGeneTemplate else None,
            'reviewer_signature': self._deafGeneTemplate.get('reviewer_signature') if self._deafGeneTemplate else None,
            'seal_image': self._deafGeneTemplate.get('seal_image') if self._deafGeneTemplate else None
        }
        
        if self._signature_data['tester_signature']:
            self.deaf_gene_tester_signature_label.setText("已上传")
        if self._signature_data['reviewer_signature']:
            self.deaf_gene_reviewer_signature_label.setText("已上传")
        if self._signature_data['seal_image']:
            self.deaf_gene_seal_label.setText("已上传")
        
        self.deaf_gene_is_default_checkbox = QCheckBox("设为默认模板")
        if self._deafGeneTemplate and self._deafGeneTemplate.get('is_default'):
            self.deaf_gene_is_default_checkbox.setChecked(True)
        form_layout.addRow("", self.deaf_gene_is_default_checkbox)
        
        layout.addLayout(form_layout)
        
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.validateDeafGeneTemplateInput)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def validateDeafGeneTemplateInput(self):
        template_code = self.deaf_gene_template_code_input.text().strip()
        if not template_code:
            QMessageBox.warning(self, "验证失败", "请输入模板编码")
            return
        
        template_name = self.deaf_gene_template_name_input.text().strip()
        if not template_name:
            QMessageBox.warning(self, "验证失败", "请输入模板名称")
            return
        
        self.accept()
    
    def uploadSignature(self, signature_type):
        from PyQt6.QtWidgets import QFileDialog
        import base64
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    image_data = f.read()
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                
                if signature_type == 'tester':
                    self._signature_data['tester_signature'] = base64_data
                    self.deaf_gene_tester_signature_label.setText("已上传")
                elif signature_type == 'reviewer':
                    self._signature_data['reviewer_signature'] = base64_data
                    self.deaf_gene_reviewer_signature_label.setText("已上传")
                elif signature_type == 'seal':
                    self._signature_data['seal_image'] = base64_data
                    self.deaf_gene_seal_label.setText("已上传")
                
                QMessageBox.information(self, "成功", "图片上传成功")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"上传失败: {str(e)}")
    
    def getDeafGeneTemplateData(self):
        return {
            'template_code': self.deaf_gene_template_code_input.text().strip(),
            'template_name': self.deaf_gene_template_name_input.text().strip(),
            'hospital_name': self.deaf_gene_hospital_input.text().strip(),
            'header_content': self.deaf_gene_header_input.toPlainText(),
            'footer_content': self.deaf_gene_footer_input.toPlainText(),
            'normal_interpretation': self.deaf_gene_normal_input.toPlainText(),
            'abnormal_interpretation': self.deaf_gene_abnormal_input.toPlainText(),
            'clinical_suggestions': self.deaf_gene_suggestions_input.toPlainText(),
            'tester_signature': self._signature_data.get('tester_signature'),
            'reviewer_signature': self._signature_data.get('reviewer_signature'),
            'seal_image': self._signature_data.get('seal_image'),
            'is_default': 1 if self.deaf_gene_is_default_checkbox.isChecked() else 0
        }
