#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
报告生成与预览界面
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QListWidget, QListWidgetItem, 
    QTextEdit, QFileDialog, QMessageBox, QComboBox,
    QSplitter, QFrame, QGroupBox, QScrollArea, QFormLayout, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QFont

from core.database import db
from core.auth import auth_manager
from config import REPORT_TEMPLATES


class ReportGenerationThread(QThread):
    """报告生成线程"""
    
    progress_updated = pyqtSignal(str)      # 进度消息
    generation_completed = pyqtSignal(dict) # 生成完成
    generation_failed = pyqtSignal(str)     # 生成失败
    
    def __init__(self, sample_ids, template_type):
        super().__init__()
        self.sample_ids = sample_ids
        self.template_type = template_type
        
    def run(self):
        """执行报告生成"""
        try:
            # 这里集成现有的报告生成功能
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from run_deaf_gene_report import generate_deaf_gene_reports
            
            # 生成报告
            result = generate_deaf_gene_reports(
                sample_excel_path="",  # 需要从数据库获取样本数据生成临时Excel
                output_dir="temp_reports",
                log_callback=lambda msg: self.progress_updated.emit(msg)
            )
            
            if result['success']:
                self.generation_completed.emit(result)
            else:
                self.generation_failed.emit(result['message'])
                
        except Exception as e:
            self.generation_failed.emit(str(e))


class ReportPreview(QWidget):
    """报告生成与预览界面"""
    
    def __init__(self):
        super().__init__()
        self.current_sample_id = None
        self.current_template = "clinical"
        self.init_ui()
        self.load_samples()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("报告生成与预览")
        title_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)
        
        # 主分割器
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：样本选择和模板选择
        left_widget = self.create_left_panel()
        main_splitter.addWidget(left_widget)
        
        # 右侧：报告预览
        right_widget = self.create_right_panel()
        main_splitter.addWidget(right_widget)
        
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 3)
        
        layout.addWidget(main_splitter)
        
        # 底部操作栏
        action_bar = self.create_action_bar()
        layout.addWidget(action_bar)
        
    def create_left_panel(self):
        """创建左侧面板"""
        widget = QFrame()
        widget.setStyleSheet("background-color: white; border-radius: 8px;")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 样本选择
        sample_group = QGroupBox("样本选择")
        sample_layout = QVBoxLayout()
        
        self.sample_list = QListWidget()
        self.sample_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px;
                color: #333;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                color: #333;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        self.sample_list.itemClicked.connect(self.on_sample_selected)
        sample_layout.addWidget(self.sample_list)
        
        sample_group.setLayout(sample_layout)
        layout.addWidget(sample_group)
        
        # 模板选择
        template_group = QGroupBox("报告模板")
        template_layout = QVBoxLayout()
        
        self.template_combo = QComboBox()
        for template_key, template_name in REPORT_TEMPLATES.items():
            self.template_combo.addItem(template_name, template_key)
        self.template_combo.currentTextChanged.connect(self.on_template_changed)
        template_layout.addWidget(self.template_combo)
        
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)
        
        # 报告信息编辑
        info_group = QGroupBox("报告信息")
        info_layout = QFormLayout()
        
        self.report_no_input = QLineEdit()
        self.report_no_input.setPlaceholderText("自动生成")
        self.report_no_input.setEnabled(False)
        info_layout.addRow("报告编号:", self.report_no_input)
        
        self.hospital_input = QLineEdit()
        self.hospital_input.setPlaceholderText("送检单位")
        info_layout.addRow("送检单位:", self.hospital_input)
        
        self.doctor_input = QLineEdit()
        self.doctor_input.setPlaceholderText("主治医师")
        info_layout.addRow("主治医师:", self.doctor_input)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        
        return widget
        
    def create_right_panel(self):
        """创建右侧面板"""
        widget = QFrame()
        widget.setStyleSheet("background-color: white; border-radius: 8px;")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 预览标题
        preview_title = QLabel("报告预览")
        preview_title.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        layout.addWidget(preview_title)
        
        # 预览区域
        self.preview_area = QScrollArea()
        self.preview_area.setWidgetResizable(True)
        self.preview_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
        """)
        
        # 预览内容
        self.preview_content = QTextEdit()
        self.preview_content.setReadOnly(True)
        self.preview_content.setMinimumHeight(500)
        self.preview_content.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: none;
                padding: 20px;
                font-size: 12px;
                line-height: 1.6;
            }
        """)
        
        self.preview_area.setWidget(self.preview_content)
        layout.addWidget(self.preview_area)
        
        return widget
        
    def create_action_bar(self):
        """创建操作栏"""
        action_frame = QFrame()
        action_frame.setStyleSheet("background-color: white; border-radius: 8px; padding: 10px;")
        
        layout = QHBoxLayout(action_frame)
        layout.setContentsMargins(15, 5, 15, 5)
        
        # 生成报告按钮
        self.generate_btn = QPushButton("📄 生成报告")
        self.generate_btn.setEnabled(False)
        self.generate_btn.clicked.connect(self.generate_report)
        layout.addWidget(self.generate_btn)
        
        # 编辑按钮
        self.edit_btn = QPushButton("✏️ 编辑内容")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self.edit_report)
        layout.addWidget(self.edit_btn)
        
        # 添加备注按钮
        self.note_btn = QPushButton("📝 添加备注")
        self.note_btn.setEnabled(False)
        self.note_btn.clicked.connect(self.add_note)
        layout.addWidget(self.note_btn)
        
        layout.addStretch()
        
        # 导出PDF按钮
        self.export_pdf_btn = QPushButton("📑 导出PDF")
        self.export_pdf_btn.setEnabled(False)
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        layout.addWidget(self.export_pdf_btn)
        
        # 打印按钮
        self.print_btn = QPushButton("🖨️ 打印")
        self.print_btn.setEnabled(False)
        self.print_btn.clicked.connect(self.print_report)
        layout.addWidget(self.print_btn)
        
        # 保存按钮
        self.save_btn = QPushButton("💾 保存")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_report)
        layout.addWidget(self.save_btn)
        
        # 提交审核按钮
        self.submit_btn = QPushButton("✅ 提交审核")
        self.submit_btn.setEnabled(False)
        self.submit_btn.clicked.connect(self.submit_review)
        layout.addWidget(self.submit_btn)
        
        return action_frame
        
    def load_samples(self):
        """加载样本列表"""
        try:
            # 获取所有样本（包含已完成和待处理的）
            cursor = db.execute_query("""
                SELECT * FROM samples 
                ORDER BY created_at DESC
            """)
            rows = cursor.fetchall()
            
            # 转换为字典列表
            samples = [dict(row) for row in rows]
            
            self.sample_list.clear()
            
            for sample in samples:
                item = QListWidgetItem(
                    f"{sample['sample_no']} - {sample['patient_name']}"
                )
                item.setData(Qt.ItemDataRole.UserRole, sample)
                self.sample_list.addItem(item)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载样本列表失败: {str(e)}")
    
    def on_sample_selected(self, item):
        """样本选择事件"""
        sample = item.data(Qt.ItemDataRole.UserRole)
        self.current_sample_id = sample['id']
        
        # 更新报告信息
        self.report_no_input.setText(f"RPT{sample['id']:06d}")
        self.hospital_input.setText(sample.get('hospital', ''))
        
        # 启用按钮
        self.generate_btn.setEnabled(True)
        self.edit_btn.setEnabled(False)
        self.note_btn.setEnabled(False)
        self.export_pdf_btn.setEnabled(False)
        self.print_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.submit_btn.setEnabled(False)
        
        # 显示预览模板
        self.show_preview_template()
    
    def on_template_changed(self, template_name):
        """模板改变事件"""
        self.current_template = self.template_combo.currentData()
        if self.current_sample_id:
            self.show_preview_template()
    
    def show_preview_template(self):
        """显示预览模板"""
        template_content = self.get_template_content()
        self.preview_content.setHtml(template_content)
    
    def get_template_content(self):
        """获取模板内容（包含实际数据）"""
        template_name = REPORT_TEMPLATES.get(self.current_template, "临床诊断报告")
        
        # 获取样本信息和基因数据
        sample_info = None
        gene_data_list = []
        
        if self.current_sample_id:
            cursor = db.execute_query("SELECT * FROM samples WHERE id = ?", (self.current_sample_id,))
            row = cursor.fetchone()
            if row:
                sample_info = dict(row)
            
            cursor = db.execute_query("SELECT * FROM gene_data WHERE sample_id = ?", (self.current_sample_id,))
            gene_data_list = [dict(row) for row in cursor.fetchall()]
        
        # 构建检测结果表格
        gene_table_rows = ""
        for gene_data in gene_data_list:
            gene_table_rows += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{gene_data.get('gene_name', '')}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{gene_data.get('mutation_site', '')}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{gene_data.get('genotype', '')}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{gene_data.get('pathogenicity', '')}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{gene_data.get('reference', '')}</td>
            </tr>
            """
        
        # 确定检测结论
        has_mutation = any(gd.get('pathogenicity') in ['致病性', '可能致病性', '异常'] for gd in gene_data_list)
        conclusion = "检测到致病变异" if has_mutation else "未检测到明确致病变异"
        
        # 获取样本信息
        patient_name = sample_info.get('patient_name', '') if sample_info else ''
        gender = sample_info.get('gender', '') if sample_info else ''
        age = sample_info.get('age', '') if sample_info else ''
        clinical_diagnosis = sample_info.get('clinical_diagnosis', '') if sample_info else ''
        hospital = sample_info.get('hospital', '') if sample_info else ''
        
        html_content = f"""
        <div style="font-family: 'Microsoft YaHei', sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; background: white;">
            <!-- 报告头部 -->
            <div style="text-align: center; margin-bottom: 30px; border-bottom: 2px solid #0078d4; padding-bottom: 20px;">
                <h1 style="color: #333; margin: 0;">耳聋基因检测报告</h1>
                <h2 style="color: #666; font-weight: normal; margin: 10px 0;">{template_name}</h2>
            </div>
            
            <!-- 报告信息 -->
            <div style="margin-bottom: 30px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa;"><strong>报告编号：</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{self.report_no_input.text() or '待生成'}</td>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa;"><strong>送检单位：</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{hospital or self.hospital_input.text() or '待填写'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa;"><strong>受检者姓名：</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{patient_name}</td>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa;"><strong>性别：</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{gender}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa;"><strong>年龄：</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{age}</td>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa;"><strong>临床诊断：</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{clinical_diagnosis}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa;"><strong>检测项目：</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">耳聋基因检测Panel</td>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa;"><strong>报告日期：</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">2024-06-16</td>
                    </tr>
                </table>
            </div>
            
            <!-- 检测结果 -->
            <div style="margin-bottom: 30px;">
                <h3 style="color: #0078d4; border-left: 4px solid #0078d4; padding-left: 10px; margin-bottom: 15px;">检测结果</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
                    <thead>
                        <tr style="background-color: #f8f9fa;">
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">基因名称</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">突变位点</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">基因型</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">致病性</th>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">参考依据</th>
                        </tr>
                    </thead>
                    <tbody>
                        {gene_table_rows if gene_table_rows else '<tr><td colspan="5" style="padding: 20px; text-align: center; border: 1px solid #ddd;">暂无检测数据</td></tr>'}
                    </tbody>
                </table>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; border-left: 4px solid {'#f44336' if has_mutation else '#4caf50'};">
                    <p style="margin: 0; color: #333;"><strong>检测结论：</strong>{conclusion}</p>
                    <p style="margin: 10px 0 0 0; color: #666; font-size: 12px;">注：此结果基于当前检测范围，如有疑问请咨询遗传咨询师。</p>
                </div>
            </div>
            
            <!-- 结果解读 -->
            <div style="margin-bottom: 30px;">
                <h3 style="color: #0078d4; border-left: 4px solid #0078d4; padding-left: 10px; margin-bottom: 15px;">结果解读</h3>
                <div style="line-height: 1.8; color: #555;">
                    <p>1. <strong>遗传模式：</strong>常染色体隐性遗传</p>
                    <p>2. <strong>致病性分析：</strong>{'本次检测发现与耳聋相关的致病变异' if has_mutation else '本次检测未发现与耳聋相关的明确致病变异'}</p>
                    <p>3. <strong>临床建议：</strong></p>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>建议定期进行听力筛查</li>
                        <li>如有家族史，建议进行遗传咨询</li>
                        <li>避免使用耳毒性药物</li>
                    </ul>
                </div>
            </div>
            
            <!-- 报告说明 -->
            <div style="margin-bottom: 30px;">
                <h3 style="color: #0078d4; border-left: 4px solid #0078d4; padding-left: 10px; margin-bottom: 15px;">报告说明</h3>
                <div style="font-size: 11px; color: #777; line-height: 1.6;">
                    <p>1. 本报告仅对所送检样本负责，结果仅供临床参考。</p>
                    <p>2. 检测方法和范围详见检测项目说明。</p>
                    <p>3. 如有疑问，请在收到报告后7个工作日内联系本中心。</p>
                    <p>4. 本报告解释权归医学检验中心所有。</p>
                </div>
            </div>
            
            <!-- 签名区域 -->
            <div style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ddd;">
                <table style="width: 100%;">
                    <tr>
                        <td style="width: 50%; padding: 10px;">
                            <strong>检测医师：</strong>________________
                        </td>
                        <td style="width: 50%; padding: 10px;">
                            <strong>审核医师：</strong>________________
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px;">
                            <strong>报告日期：</strong>2024-06-16
                        </td>
                        <td style="padding: 10px;">
                            <strong>盖章：</strong>________________
                        </td>
                    </tr>
                </table>
            </div>
        </div>
        """
        
        return html_content
    
    def generate_report(self):
        """生成报告"""
        if not self.current_sample_id:
            QMessageBox.warning(self, "提示", "请先选择样本")
            return
        
        try:
            # 生成报告编号
            report_no = f"RPT{self.current_sample_id:06d}"
            
            # 创建报告记录
            report_data = {
                'sample_id': self.current_sample_id,
                'report_no': report_no,
                'template_type': self.current_template,
                'content': self.preview_content.toHtml(),
                'status': 'pending'
            }
            
            report_id = db.create_report(report_data)
            
            # 更新样本状态
            db.execute_query(
                "UPDATE samples SET status = 'completed' WHERE id = ?",
                (self.current_sample_id,)
            )
            db.commit()
            
            QMessageBox.information(self, "成功", "报告生成成功")
            
            # 启用操作按钮
            self.edit_btn.setEnabled(True)
            self.note_btn.setEnabled(True)
            self.export_pdf_btn.setEnabled(True)
            self.print_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            self.submit_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"报告生成失败: {str(e)}")
    
    def edit_report(self):
        """编辑报告"""
        self.preview_content.setReadOnly(False)
        QMessageBox.information(self, "提示", "现在可以编辑报告内容，编辑完成后点击保存")
    
    def add_note(self):
        """添加备注"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("添加备注")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        note_edit = QTextEdit()
        note_edit.setPlaceholderText("请输入备注内容...")
        layout.addWidget(note_edit)
        
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            note = note_edit.toPlainText()
            if note:
                # 在报告内容末尾添加备注
                current_content = self.preview_content.toHtml()
                note_html = f"""
                <div style="margin-top: 30px; padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
                    <strong>备注：</strong>{note}
                </div>
                """
                self.preview_content.setHtml(current_content + note_html)
    
    def export_pdf(self):
        """导出PDF"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存PDF报告", "", "PDF文件 (*.pdf)"
        )
        
        if file_path:
            # 这里实现PDF导出逻辑
            QMessageBox.information(self, "提示", "PDF导出功能开发中...")
    
    def print_report(self):
        """打印报告"""
        # 这里实现打印逻辑
        QMessageBox.information(self, "提示", "打印功能开发中...")
    
    def save_report(self):
        """保存报告"""
        try:
            # 更新报告内容
            db.execute_query(
                "UPDATE reports SET content = ? WHERE sample_id = ?",
                (self.preview_content.toHtml(), self.current_sample_id)
            )
            db.commit()
            
            self.preview_content.setReadOnly(True)
            QMessageBox.information(self, "成功", "报告保存成功")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def submit_review(self):
        """提交审核"""
        reply = QMessageBox.question(
            self, '确认提交',
            '确定要提交报告进行审核吗？提交后将无法修改。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 更新报告状态为待审核
                db.execute_query(
                    "UPDATE reports SET status = 'pending' WHERE sample_id = ?",
                    (self.current_sample_id,)
                )
                db.commit()
                
                QMessageBox.information(self, "成功", "报告已提交审核")
                
                # 禁用编辑按钮
                self.edit_btn.setEnabled(False)
                self.note_btn.setEnabled(False)
                self.save_btn.setEnabled(False)
                self.submit_btn.setEnabled(False)
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"提交失败: {str(e)}")
    
    def refresh_data(self):
        """刷新数据"""
        self.load_samples()