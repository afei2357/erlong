#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
样本信息管理界面
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QLineEdit, QComboBox, QTableWidget, 
    QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox, 
    QDialog, QFormLayout, QTextEdit, QDateEdit, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from core.database import db
from core.auth import auth_manager
from config import SAMPLE_STATUS


class SampleManagement(QWidget):
    """样本信息管理界面"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_samples()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("样本信息管理")
        title_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)
        
        # 工具栏
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # 搜索筛选区
        search_area = self.create_search_area()
        layout.addWidget(search_area)
        
        # 样本表格
        self.table = self.create_sample_table()
        layout.addWidget(self.table)
        
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: white; border-radius: 8px; padding: 10px;")
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 批量导入
        import_btn = QPushButton("📥 批量导入")
        import_btn.clicked.connect(self.import_samples)
        layout.addWidget(import_btn)
        
        # 单个新增
        add_btn = QPushButton("➕ 单个新增")
        add_btn.clicked.connect(self.show_add_dialog)
        layout.addWidget(add_btn)
        
        layout.addStretch()
        
        # 导出
        export_btn = QPushButton("📤 导出列表")
        export_btn.clicked.connect(self.export_samples)
        layout.addWidget(export_btn)
        
        return toolbar
        
    def create_search_area(self):
        """创建搜索筛选区"""
        search_frame = QFrame()
        search_frame.setStyleSheet("background-color: white; border-radius: 8px; padding: 10px;")
        
        layout = QGridLayout(search_frame)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # 样本编号搜索
        layout.addWidget(QLabel("样本编号:"), 0, 0)
        self.sample_no_search = QLineEdit()
        self.sample_no_search.setPlaceholderText("请输入样本编号")
        self.sample_no_search.setFixedWidth(200)
        layout.addWidget(self.sample_no_search, 0, 1)
        
        # 姓名搜索
        layout.addWidget(QLabel("受检者姓名:"), 0, 2)
        self.name_search = QLineEdit()
        self.name_search.setPlaceholderText("请输入姓名")
        self.name_search.setFixedWidth(150)
        layout.addWidget(self.name_search, 0, 3)
        
        # 状态筛选
        layout.addWidget(QLabel("状态:"), 0, 4)
        self.status_filter = QComboBox()
        self.status_filter.addItem("全部", None)
        for status_key, status_name in SAMPLE_STATUS.items():
            self.status_filter.addItem(status_name, status_key)
        self.status_filter.setFixedWidth(120)
        layout.addWidget(self.status_filter, 0, 5)
        
        # 搜索按钮
        search_btn = QPushButton("🔍 搜索")
        search_btn.clicked.connect(self.search_samples)
        layout.addWidget(search_btn, 0, 6)
        
        # 重置按钮
        reset_btn = QPushButton("🔄 重置")
        reset_btn.clicked.connect(self.reset_search)
        layout.addWidget(reset_btn, 0, 7)
        
        return search_frame
        
    def create_sample_table(self):
        """创建样本表格"""
        table = QTableWidget()
        table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 8px;
                gridline-color: #eee;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
        """)
        
        # 设置列
        headers = [
            "样本编号", "受检者姓名", "性别", "年龄", 
            "临床诊断", "送检单位", "检测项目", "状态", "操作"
        ]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        
        # 设置列宽
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        
        # 设置行高
        table.verticalHeader().setDefaultSectionSize(40)
        table.verticalHeader().setVisible(False)
        
        # 设置选择模式
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # 双击编辑
        table.cellDoubleClicked.connect(self.edit_sample)
        
        return table
        
    def load_samples(self, filters=None):
        """加载样本数据"""
        try:
            samples = db.get_samples(filters)
            self.populate_table(samples)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载样本数据失败: {str(e)}")
    
    def populate_table(self, samples):
        """填充表格数据"""
        self.table.setRowCount(len(samples))
        
        for row, sample in enumerate(samples):
            # 样本编号
            self.table.setItem(row, 0, QTableWidgetItem(sample['sample_no']))
            
            # 受检者姓名
            self.table.setItem(row, 1, QTableWidgetItem(sample['patient_name']))
            
            # 性别
            self.table.setItem(row, 2, QTableWidgetItem(sample.get('gender', '')))
            
            # 年龄
            self.table.setItem(row, 3, QTableWidgetItem(sample.get('age', '')))
            
            # 临床诊断
            self.table.setItem(row, 4, QTableWidgetItem(sample.get('clinical_diagnosis', '')))
            
            # 送检单位
            self.table.setItem(row, 5, QTableWidgetItem(sample.get('hospital', '')))
            
            # 检测项目
            self.table.setItem(row, 6, QTableWidgetItem(sample.get('test_project', '')))
            
            # 状态
            status_item = QTableWidgetItem(SAMPLE_STATUS.get(sample['status'], sample['status']))
            self.set_status_color(status_item, sample['status'])
            self.table.setItem(row, 7, status_item)
            
            # 操作按钮
            self.create_action_buttons(row, sample)
    
    def set_status_color(self, item, status):
        """设置状态颜色"""
        color_map = {
            'pending': QColor('#ff9800'),    # 橙色
            'analyzing': QColor('#2196f3'),  # 蓝色
            'completed': QColor('#4caf50'),  # 绿色
            'failed': QColor('#f44336')      # 红色
        }
        
        color = color_map.get(status, QColor('#666'))
        item.setForeground(color)
    
    def create_action_buttons(self, row, sample):
        """创建操作按钮"""
        button_widget = QWidget()
        layout = QHBoxLayout(button_widget)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # 编辑按钮
        edit_btn = QPushButton("编辑")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        edit_btn.clicked.connect(lambda: self.edit_sample(row))
        layout.addWidget(edit_btn)
        
        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_sample(sample['id']))
        layout.addWidget(delete_btn)
        
        self.table.setCellWidget(row, 8, button_widget)
    
    def show_add_dialog(self):
        """显示添加样本对话框"""
        dialog = SampleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            sample_data = dialog.get_sample_data()
            sample_data['created_by'] = auth_manager.current_user['id']
            
            try:
                sample_id = db.create_sample(sample_data)
                QMessageBox.information(self, "成功", "样本添加成功")
                self.load_samples()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加样本失败: {str(e)}")
    
    def edit_sample(self, row):
        """编辑样本"""
        sample_no = self.table.item(row, 0).text()
        
        # 获取样本详细信息
        cursor = db.execute_query(
            "SELECT * FROM samples WHERE sample_no = ?",
            (sample_no,)
        )
        sample_row = cursor.fetchone()
        
        if sample_row:
            sample = dict(sample_row)
            dialog = SampleDialog(self, sample)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                sample_data = dialog.get_sample_data()
                
                try:
                    # 更新样本信息
                    db.execute_query("""
                        UPDATE samples SET
                            patient_name = ?, gender = ?, age = ?,
                            clinical_diagnosis = ?, hospital = ?,
                            test_project = ?, family_history = ?, notes = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        sample_data['patient_name'],
                        sample_data.get('gender'),
                        sample_data.get('age'),
                        sample_data.get('clinical_diagnosis'),
                        sample_data.get('hospital'),
                        sample_data.get('test_project'),
                        sample_data.get('family_history'),
                        sample_data.get('notes'),
                        sample['id']
                    ))
                    db.commit()
                    
                    QMessageBox.information(self, "成功", "样本信息更新成功")
                    self.load_samples()
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"更新样本失败: {str(e)}")
    
    def delete_sample(self, sample_id):
        """删除样本"""
        reply = QMessageBox.question(
            self, '确认删除',
            '确定要删除这个样本吗？此操作不可恢复。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 删除相关基因数据
                db.execute_query("DELETE FROM gene_data WHERE sample_id = ?", (sample_id,))
                
                # 删除相关报告
                db.execute_query("DELETE FROM reports WHERE sample_id = ?", (sample_id,))
                
                # 删除样本
                db.execute_query("DELETE FROM samples WHERE id = ?", (sample_id,))
                db.commit()
                
                QMessageBox.information(self, "成功", "样本删除成功")
                self.load_samples()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除样本失败: {str(e)}")
    
    def search_samples(self):
        """搜索样本"""
        filters = {}
        
        sample_no = self.sample_no_search.text().strip()
        if sample_no:
            # 这里需要修改数据库查询以支持样本编号搜索
            pass
        
        name = self.name_search.text().strip()
        if name:
            # 这里需要修改数据库查询以支持姓名搜索
            pass
        
        status = self.status_filter.currentData()
        if status:
            filters['status'] = status
        
        self.load_samples(filters)
    
    def reset_search(self):
        """重置搜索"""
        self.sample_no_search.clear()
        self.name_search.clear()
        self.status_filter.setCurrentIndex(0)
        self.load_samples()
    
    def import_samples(self):
        """批量导入样本"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Excel文件", "", "Excel文件 (*.xlsx *.xls)"
        )
        
        if file_path:
            # 这里实现Excel导入逻辑
            QMessageBox.information(self, "提示", "批量导入功能开发中...")
    
    def export_samples(self):
        """导出样本列表"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存样本列表", "", "Excel文件 (*.xlsx)"
        )
        
        if file_path:
            # 这里实现Excel导出逻辑
            QMessageBox.information(self, "提示", "导出功能开发中...")
    
    def refresh_data(self):
        """刷新数据"""
        self.load_samples()


class SampleDialog(QDialog):
    """样本信息对话框"""
    
    def __init__(self, parent=None, sample=None):
        super().__init__(parent)
        self.sample = sample
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        if self.sample:
            self.setWindowTitle("编辑样本信息")
        else:
            self.setWindowTitle("新增样本信息")
        
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # 表单
        form_layout = QFormLayout()
        
        # 样本编号
        self.sample_no_input = QLineEdit()
        if self.sample:
            self.sample_no_input.setText(self.sample['sample_no'])
            self.sample_no_input.setEnabled(False)
        else:
            self.sample_no_input.setPlaceholderText("请输入样本编号")
        form_layout.addRow("样本编号*:", self.sample_no_input)
        
        # 受检者姓名
        self.patient_name_input = QLineEdit()
        if self.sample:
            self.patient_name_input.setText(self.sample['patient_name'])
        else:
            self.patient_name_input.setPlaceholderText("请输入受检者姓名")
        form_layout.addRow("受检者姓名*:", self.patient_name_input)
        
        # 性别
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["男", "女"])
        if self.sample:
            self.gender_combo.setCurrentText(self.sample.get('gender', '男'))
        form_layout.addRow("性别:", self.gender_combo)
        
        # 年龄
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("请输入年龄")
        if self.sample:
            self.age_input.setText(self.sample.get('age', ''))
        form_layout.addRow("年龄:", self.age_input)
        
        # 临床诊断
        self.diagnosis_input = QLineEdit()
        self.diagnosis_input.setPlaceholderText("请输入临床诊断")
        if self.sample:
            self.diagnosis_input.setText(self.sample.get('clinical_diagnosis', ''))
        form_layout.addRow("临床诊断:", self.diagnosis_input)
        
        # 送检单位
        self.hospital_input = QLineEdit()
        self.hospital_input.setPlaceholderText("请输入送检单位")
        if self.sample:
            self.hospital_input.setText(self.sample.get('hospital', ''))
        form_layout.addRow("送检单位:", self.hospital_input)
        
        # 检测项目
        self.project_input = QLineEdit()
        self.project_input.setPlaceholderText("请输入检测项目")
        if self.sample:
            self.project_input.setText(self.sample.get('test_project', ''))
        form_layout.addRow("检测项目:", self.project_input)
        
        layout.addLayout(form_layout)
        
        # 扩展信息
        extended_group = QGroupBox("扩展信息")
        extended_layout = QFormLayout()
        
        # 家族耳聋史
        self.family_history_input = QTextEdit()
        self.family_history_input.setMaximumHeight(80)
        self.family_history_input.setPlaceholderText("请输入家族耳聋史")
        if self.sample:
            self.family_history_input.setText(self.sample.get('family_history', ''))
        extended_layout.addRow("家族耳聋史:", self.family_history_input)
        
        # 备注
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("请输入备注信息")
        if self.sample:
            self.notes_input.setText(self.sample.get('notes', ''))
        extended_layout.addRow("备注:", self.notes_input)
        
        extended_group.setLayout(extended_layout)
        layout.addWidget(extended_group)
        
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
        # 验证必填字段
        sample_no = self.sample_no_input.text().strip()
        if not sample_no:
            QMessageBox.warning(self, "验证失败", "请输入样本编号")
            return
        
        patient_name = self.patient_name_input.text().strip()
        if not patient_name:
            QMessageBox.warning(self, "验证失败", "请输入受检者姓名")
            return
        
        self.accept()
    
    def get_sample_data(self):
        """获取样本数据"""
        return {
            'sample_no': self.sample_no_input.text().strip(),
            'patient_name': self.patient_name_input.text().strip(),
            'gender': self.gender_combo.currentText(),
            'age': self.age_input.text().strip(),
            'clinical_diagnosis': self.diagnosis_input.text().strip(),
            'hospital': self.hospital_input.text().strip(),
            'test_project': self.project_input.text().strip(),
            'family_history': self.family_history_input.toPlainText().strip(),
            'notes': self.notes_input.toPlainText().strip()
        }