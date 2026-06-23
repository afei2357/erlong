#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
from pathlib import Path
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QFont

import csv

from core.database import db
from core.auth import auth_manager
from config import REPORT_TEMPLATES


class DeafGeneReportGenException(Exception):
    pass


class DeafGeneReportNoDataException(DeafGeneReportGenException):
    pass


class DeafGeneReportSaveException(DeafGeneReportGenException):
    pass


class DeafGeneReportGenerationWorker(QThread):
    progress_updated = pyqtSignal(str)
    generation_completed = pyqtSignal(dict)
    generation_failed = pyqtSignal(str)
    
    def __init__(self, sample_ids, template_type):
        super().__init__()
        self._deafGeneSampleIds = sample_ids
        self._deafGeneTemplateType = template_type
        self._deafGeneStartTime = None
        
    def run(self):
        self._deafGeneStartTime = time.time()
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from run_deaf_gene_report import generate_deaf_gene_reports
            
            result = generate_deaf_gene_reports(
                sample_excel_path="",
                output_dir="temp_reports",
                log_callback=lambda msg: self.progress_updated.emit(msg)
            )
            
            elapsed_time = time.time() - self._deafGeneStartTime
            print(f"[DEBUG] 报告生成耗时: {elapsed_time:.2f}s", file=sys.stderr)
            
            if result['success']:
                self.generation_completed.emit(result)
            else:
                self.generation_failed.emit(result['message'])
                
        except ImportError:
            self.generation_failed.emit("无法导入报告生成模块")
        except Exception as e:
            self.generation_failed.emit(str(e))


class DeafGeneReportPreview(QWidget):
    def __init__(self):
        super().__init__()
        self._deafGeneCurSampleId = None
        self._deafGeneCurTemplate = "clinical"
        self._deafGeneLastGenTime = None
        self._deafGeneGenCount = 0
        
        self.initDeafGeneReportUI()
        self.loadDeafGeneSamples()
        
    def initDeafGeneReportUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title_label = QLabel("耳聋基因报告预览")
        title_label.setStyleSheet("QLabel { color: #333; font-size: 18px; font-weight: bold; }")
        layout.addWidget(title_label)
        
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_widget = self.createDeafGeneLeftPanel()
        main_splitter.addWidget(left_widget)
        
        right_widget = self.createDeafGeneRightPanel()
        main_splitter.addWidget(right_widget)
        
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 3)
        
        layout.addWidget(main_splitter)
        
        action_bar = self.createDeafGeneActionBar()
        layout.addWidget(action_bar)
        
    def createDeafGeneLeftPanel(self):
        widget = QFrame()
        widget.setStyleSheet("background-color: white; border-radius: 8px;")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        sample_group = QGroupBox("样本选择")
        sample_layout = QVBoxLayout()
        
        self.deaf_gene_sample_list = QListWidget()
        self.deaf_gene_sample_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.deaf_gene_sample_list.setStyleSheet("""
            QListWidget { border: 1px solid #ddd; border-radius: 4px; padding: 4px; color: #333; }
            QListWidget::item { padding: 8px; border-radius: 4px; color: #333; }
            QListWidget::item:selected { background-color: #0078d4; color: white; }
            QListWidget::item:hover { background-color: #e3f2fd; }
        """)
        self.deaf_gene_sample_list.itemClicked.connect(self.onDeafGeneSampleSelected)
        self.deaf_gene_sample_list.itemSelectionChanged.connect(self.onDeafGeneSampleSelectionChanged)
        sample_layout.addWidget(self.deaf_gene_sample_list)
        
        sample_group.setLayout(sample_layout)
        layout.addWidget(sample_group)
        
        template_group = QGroupBox("报告模板")
        template_layout = QVBoxLayout()
        
        self.deaf_gene_template_combo = QComboBox()
        self.loadDeafGeneTemplates()
        self.deaf_gene_template_combo.currentTextChanged.connect(self.onDeafGeneTemplateChanged)
        template_layout.addWidget(self.deaf_gene_template_combo)
        
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)
        
        info_group = QGroupBox("报告信息")
        info_layout = QFormLayout()
        
        self.deaf_gene_report_no_input = QLineEdit()
        self.deaf_gene_report_no_input.setPlaceholderText("自动生成")
        self.deaf_gene_report_no_input.setEnabled(False)
        info_layout.addRow("报告编号:", self.deaf_gene_report_no_input)
        
        self.deaf_gene_hospital_input = QLineEdit()
        self.deaf_gene_hospital_input.setPlaceholderText("送检单位")
        info_layout.addRow("送检单位:", self.deaf_gene_hospital_input)
        
        self.deaf_gene_doctor_input = QLineEdit()
        self.deaf_gene_doctor_input.setPlaceholderText("主治医师")
        info_layout.addRow("主治医师:", self.deaf_gene_doctor_input)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        
        return widget
        
    def createDeafGeneRightPanel(self):
        widget = QFrame()
        widget.setStyleSheet("background-color: white; border-radius: 8px;")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        preview_title = QLabel("报告预览")
        preview_title.setStyleSheet("QLabel { color: #333; font-size: 14px; font-weight: bold; }")
        layout.addWidget(preview_title)
        
        self.deaf_gene_preview_area = QScrollArea()
        self.deaf_gene_preview_area.setWidgetResizable(True)
        self.deaf_gene_preview_area.setStyleSheet("QScrollArea { border: 1px solid #ddd; border-radius: 4px; background-color: #f8f9fa; }")
        
        self.deaf_gene_preview_content = QTextEdit()
        self.deaf_gene_preview_content.setReadOnly(True)
        self.deaf_gene_preview_content.setMinimumHeight(500)
        self.deaf_gene_preview_content.setStyleSheet("QTextEdit { background-color: white; border: none; padding: 20px; font-size: 12px; line-height: 1.6; }")
        
        self.deaf_gene_preview_area.setWidget(self.deaf_gene_preview_content)
        layout.addWidget(self.deaf_gene_preview_area)
        
        return widget
        
    def createDeafGeneActionBar(self):
        action_frame = QFrame()
        action_frame.setStyleSheet("background-color: white; border-radius: 8px; padding: 10px;")
        
        layout = QHBoxLayout(action_frame)
        layout.setContentsMargins(15, 5, 15, 5)
        
        self.deaf_gene_generate_btn = QPushButton("📄 生成报告")
        self.deaf_gene_generate_btn.setEnabled(False)
        self.deaf_gene_generate_btn.clicked.connect(self.generateDeafGeneReport)
        layout.addWidget(self.deaf_gene_generate_btn)
        
        self.deaf_gene_batch_generate_btn = QPushButton("📋 批量生成")
        self.deaf_gene_batch_generate_btn.setEnabled(False)
        self.deaf_gene_batch_generate_btn.clicked.connect(self.batchGenerateDeafGeneReports)
        layout.addWidget(self.deaf_gene_batch_generate_btn)
        
        self.deaf_gene_edit_btn = QPushButton("✏️ 编辑内容")
        self.deaf_gene_edit_btn.setEnabled(False)
        self.deaf_gene_edit_btn.clicked.connect(self.editDeafGeneReport)
        layout.addWidget(self.deaf_gene_edit_btn)
        
        self.deaf_gene_note_btn = QPushButton("📝 添加备注")
        self.deaf_gene_note_btn.setEnabled(False)
        self.deaf_gene_note_btn.clicked.connect(self.addDeafGeneNote)
        layout.addWidget(self.deaf_gene_note_btn)
        
        layout.addStretch()
        
        self.deaf_gene_export_pdf_btn = QPushButton("📑 导出PDF")
        self.deaf_gene_export_pdf_btn.setEnabled(False)
        self.deaf_gene_export_pdf_btn.clicked.connect(self.exportDeafGenePdf)
        layout.addWidget(self.deaf_gene_export_pdf_btn)
        
        self.deaf_gene_print_btn = QPushButton("🖨️ 打印")
        self.deaf_gene_print_btn.setEnabled(False)
        self.deaf_gene_print_btn.clicked.connect(self.printDeafGeneReport)
        layout.addWidget(self.deaf_gene_print_btn)
        
        self.deaf_gene_save_btn = QPushButton("💾 保存")
        self.deaf_gene_save_btn.setEnabled(False)
        self.deaf_gene_save_btn.clicked.connect(self.saveDeafGeneReport)
        layout.addWidget(self.deaf_gene_save_btn)
        
        self.deaf_gene_submit_btn = QPushButton("✅ 提交审核")
        self.deaf_gene_submit_btn.setEnabled(False)
        self.deaf_gene_submit_btn.clicked.connect(self.submitDeafGeneReview)
        layout.addWidget(self.deaf_gene_submit_btn)
        
        return action_frame
        
    def loadDeafGeneSamples(self):
        cursor = db.execute_query("""
            SELECT * FROM samples 
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        
        samples = [dict(row) for row in rows]
        
        self.deaf_gene_sample_list.clear()
        
        for sample in samples:
            item = QListWidgetItem(
                f"{sample['sample_no']} - {sample['patient_name']}"
            )
            item.setData(Qt.ItemDataRole.UserRole, sample)
            self.deaf_gene_sample_list.addItem(item)
    
    def loadDeafGeneTemplates(self):
        self.deaf_gene_template_combo.clear()
        
        db_templates = db.get_all_report_templates()
        
        if db_templates:
            for template in db_templates:
                template_name = template['template_name']
                if template.get('is_default'):
                    template_name += " (默认)"
                self.deaf_gene_template_combo.addItem(template_name, template['template_code'])
        else:
            for template_key, template_name in REPORT_TEMPLATES.items():
                self.deaf_gene_template_combo.addItem(template_name, template_key)
        
    def onDeafGeneSampleSelected(self, item):
        sample = item.data(Qt.ItemDataRole.UserRole)
        self._deafGeneCurSampleId = sample['id']
        
        self.deaf_gene_report_no_input.setText(f"RPT{sample['id']:06d}")
        self.deaf_gene_hospital_input.setText(sample.get('hospital', ''))
        
        self.deaf_gene_generate_btn.setEnabled(True)
        
    def onDeafGeneSampleSelectionChanged(self):
        selected_items = self.deaf_gene_sample_list.selectedItems()
        if len(selected_items) > 1:
            self.deaf_gene_batch_generate_btn.setEnabled(True)
            self.deaf_gene_generate_btn.setEnabled(False)
        elif len(selected_items) == 1:
            self.deaf_gene_batch_generate_btn.setEnabled(False)
            self.deaf_gene_generate_btn.setEnabled(True)
        else:
            self.deaf_gene_batch_generate_btn.setEnabled(False)
            self.deaf_gene_generate_btn.setEnabled(False)
            
        self.deaf_gene_edit_btn.setEnabled(False)
        self.deaf_gene_note_btn.setEnabled(False)
        self.deaf_gene_export_pdf_btn.setEnabled(False)
        self.deaf_gene_print_btn.setEnabled(False)
        self.deaf_gene_save_btn.setEnabled(False)
        self.deaf_gene_submit_btn.setEnabled(False)
        
        self.showDeafGenePreviewTemplate()
    
    def onDeafGeneTemplateChanged(self, template_name):
        self._deafGeneCurTemplate = self.deaf_gene_template_combo.currentData()
        if self._deafGeneCurSampleId:
            self.showDeafGenePreviewTemplate()
    
    def showDeafGenePreviewTemplate(self):
        template_content = self.getDeafGeneTemplateContent()
        self.deaf_gene_preview_content.setHtml(template_content)
    
    def getDeafGeneTemplateContent(self):
        template_data = None
        if self._deafGeneCurTemplate:
            template_data = db.get_report_template_by_code(self._deafGeneCurTemplate)
        
        if not template_data:
            template_data = db.get_default_template()
        
        template_name = template_data.get('template_name', REPORT_TEMPLATES.get(self._deafGeneCurTemplate, "临床诊断报告")) if template_data else REPORT_TEMPLATES.get(self._deafGeneCurTemplate, "临床诊断报告")
        hospital_name = template_data.get('hospital_name', '') if template_data else ''
        header_content = template_data.get('header_content', '') if template_data else ''
        footer_content = template_data.get('footer_content', '') if template_data else ''
        normal_interpretation = template_data.get('normal_interpretation', '') if template_data else ''
        abnormal_interpretation = template_data.get('abnormal_interpretation', '') if template_data else ''
        clinical_suggestions = template_data.get('clinical_suggestions', '') if template_data else ''
        tester_signature = template_data.get('tester_signature', '') if template_data else ''
        reviewer_signature = template_data.get('reviewer_signature', '') if template_data else ''
        seal_image = template_data.get('seal_image', '') if template_data else ''
        
        sample_info = None
        gene_data_list = []
        
        if self._deafGeneCurSampleId:
            cursor = db.execute_query("SELECT * FROM samples WHERE id = ?", (self._deafGeneCurSampleId,))
            row = cursor.fetchone()
            if row:
                sample_info = dict(row)
            
            cursor = db.execute_query("SELECT * FROM gene_data WHERE sample_id = ?", (self._deafGeneCurSampleId,))
            gene_data_list = [dict(row) for row in cursor.fetchall()]
        
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
        
        has_mutation = any(gd.get('pathogenicity') in ['致病性', '可能致病性', '疑似致病', '异常'] for gd in gene_data_list)
        conclusion = "检测到致病变异" if has_mutation else "未检测到明确致病变异"
        interpretation = abnormal_interpretation if has_mutation and abnormal_interpretation else (normal_interpretation if normal_interpretation else ("本次检测发现与耳聋相关的致病变异" if has_mutation else "本次检测未发现与耳聋相关的明确致病变异"))
        
        patient_name = sample_info.get('patient_name', '') if sample_info else ''
        gender = sample_info.get('gender', '') if sample_info else ''
        age = sample_info.get('age', '') if sample_info else ''
        clinical_diagnosis = sample_info.get('clinical_diagnosis', '') if sample_info else ''
        hospital = sample_info.get('hospital', '') if sample_info else ''
        
        html_content = f"""
        <div style="font-family: 'Microsoft YaHei', sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; background: white;">
            <div style="text-align: center; margin-bottom: 30px; border-bottom: 2px solid #0078d4; padding-bottom: 20px;">
                <h1 style="color: #333; margin: 0;">耳聋基因检测报告</h1>
                <h2 style="color: #666; font-weight: normal; margin: 10px 0;">{template_name}</h2>
            </div>
            
            <div style="margin-bottom: 30px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa;"><strong>报告编号：</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{self.deaf_gene_report_no_input.text() or '待生成'}</td>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa;"><strong>送检单位：</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{hospital or self.deaf_gene_hospital_input.text() or '待填写'}</td>
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
            
            <div style="margin-bottom: 30px;">
                <h3 style="color: #0078d4; border-left: 4px solid #0078d4; padding-left: 10px; margin-bottom: 15px;">结果解读</h3>
                <div style="line-height: 1.8; color: #555;">
                    <p>1. <strong>遗传模式：</strong>常染色体隐性遗传</p>
                    <p>2. <strong>致病性分析：</strong>{interpretation}</p>
                    <p>3. <strong>临床建议：</strong></p>
                    <div style="margin: 10px 0; padding-left: 20px;">{clinical_suggestions if clinical_suggestions else '<ul><li>建议定期进行听力筛查</li><li>如有家族史，建议进行遗传咨询</li><li>避免使用耳毒性药物</li></ul>'}</div>
                </div>
            </div>
            
            <div style="margin-bottom: 30px;">
                <h3 style="color: #0078d4; border-left: 4px solid #0078d4; padding-left: 10px; margin-bottom: 15px;">报告说明</h3>
                <div style="font-size: 11px; color: #777; line-height: 1.6;">
                    <p>1. 本报告仅对所送检样本负责，结果仅供临床参考。</p>
                    <p>2. 检测方法和范围详见检测项目说明。</p>
                    <p>3. 如有疑问，请在收到报告后7个工作日内联系本中心。</p>
                    <p>4. 本报告解释权归医学检验中心所有。</p>
                </div>
            </div>
            
            <div style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ddd;">
                <table style="width: 100%;">
                    <tr>
                        <td style="width: 50%; padding: 10px;">
                            <strong>检测医师：</strong><br/>
                            {'<img src="data:image/png;base64,' + tester_signature + '" style="max-width: 120px; max-height: 40px;" />' if tester_signature else '________________'}
                        </td>
                        <td style="width: 50%; padding: 10px;">
                            <strong>审核医师：</strong><br/>
                            {'<img src="data:image/png;base64,' + reviewer_signature + '" style="max-width: 120px; max-height: 40px;" />' if reviewer_signature else '________________'}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px;">
                            <strong>报告日期：</strong>2024-06-16
                        </td>
                        <td style="padding: 10px;">
                            <strong>盖章：</strong><br/>
                            {'<img src="data:image/png;base64,' + seal_image + '" style="max-width: 80px; max-height: 80px;" />' if seal_image else '________________'}
                        </td>
                    </tr>
                </table>
            </div>
        </div>
        """
        
        return html_content
    
    def generateDeafGeneReport(self):
        if not self._deafGeneCurSampleId:
            QMessageBox.warning(self, "提示", "请先选择样本")
            return
        
        cursor = db.execute_query("SELECT id FROM samples WHERE id = ?", (self._deafGeneCurSampleId,))
        if not cursor.fetchone():
            QMessageBox.warning(self, "数据错误", "样本不存在")
            return
        
        timestamp = int(time.time())
        report_no = f"RPT{timestamp}"
        
        report_data = {
            'sample_id': self._deafGeneCurSampleId,
            'report_no': report_no,
            'template_type': self._deafGeneCurTemplate,
            'content': self.deaf_gene_preview_content.toHtml(),
            'status': 'pending'
        }
        
        try:
            report_id = db.create_report(report_data)
        except Exception as e:
            QMessageBox.critical(self, "数据库错误", f"创建报告记录失败: {str(e)}")
            return
        
        try:
            db.execute_query(
                "UPDATE samples SET status = 'completed' WHERE id = ?",
                (self._deafGeneCurSampleId,)
            )
            db.commit()
        except Exception as e:
            QMessageBox.critical(self, "数据库错误", f"更新样本状态失败: {str(e)}")
            return
        
        self._deafGeneGenCount += 1
        self._deafGeneLastGenTime = timestamp
        
        QMessageBox.information(self, "成功", "报告生成成功")
        
        self.deaf_gene_edit_btn.setEnabled(True)
        self.deaf_gene_note_btn.setEnabled(True)
        self.deaf_gene_export_pdf_btn.setEnabled(True)
        self.deaf_gene_print_btn.setEnabled(True)
        self.deaf_gene_save_btn.setEnabled(True)
        self.deaf_gene_submit_btn.setEnabled(True)
    
    def batchGenerateDeafGeneReports(self):
        selected_items = self.deaf_gene_sample_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "提示", "请选择要批量生成报告的样本")
            return
        
        if len(selected_items) == 1:
            self.generateDeafGeneReport()
            return
        
        reply = QMessageBox.question(
            self, "确认批量生成",
            f"确定要为选中的 {len(selected_items)} 个样本批量生成报告吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        success_count = 0
        fail_count = 0
        
        for item in selected_items:
            sample = item.data(Qt.ItemDataRole.UserRole)
            sample_id = sample['id']
            
            cursor = db.execute_query("SELECT * FROM samples WHERE id = ?", (sample_id,))
            row = cursor.fetchone()
            if not row:
                fail_count += 1
                continue
            sample_info = dict(row)
            
            cursor = db.execute_query("SELECT * FROM gene_data WHERE sample_id = ?", (sample_id,))
            gene_data_list = [dict(row) for row in cursor.fetchall()]
            
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
            
            has_mutation = any(gd.get('pathogenicity') in ['致病性', '可能致病性', '疑似致病', '异常'] for gd in gene_data_list)
            conclusion = "检测到致病变异" if has_mutation else "未检测到明确致病变异"
            
            patient_name = sample_info.get('patient_name', '')
            gender = sample_info.get('gender', '')
            age = sample_info.get('age', '')
            clinical_diagnosis = sample_info.get('clinical_diagnosis', '')
            hospital = sample_info.get('hospital', '')
            
            template_name = REPORT_TEMPLATES.get(self._deafGeneCurTemplate, "临床诊断报告")
            html_content = f"""
            <div style="font-family: 'Microsoft YaHei', sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; background: white;">
                <div style="text-align: center; margin-bottom: 30px; border-bottom: 2px solid #0078d4; padding-bottom: 20px;">
                    <h1 style="color: #333; margin: 0;">耳聋基因检测报告</h1>
                    <h2 style="color: #666; font-weight: normal; margin: 10px 0;">{template_name}</h2>
                </div>
                <div style="margin-bottom: 30px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa;"><strong>报告编号：</strong></td>
                            <td style="padding: 8px; border: 1px solid #ddd;">RPT{int(time.time())}</td>
                            <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa;"><strong>送检单位：</strong></td>
                            <td style="padding: 8px; border: 1px solid #ddd;">{hospital}</td>
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
                <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p style="color: #666; font-size: 12px;">检测机构：某医学检验实验室</p>
                    <p style="color: #666; font-size: 12px;">联系方式：010-12345678</p>
                </div>
            </div>
            """
            
            timestamp = int(time.time() * 1000)
            report_no = f"RPT{timestamp}"
            
            report_data = {
                'sample_id': sample_id,
                'report_no': report_no,
                'template_type': self._deafGeneCurTemplate,
                'content': html_content,
                'status': 'pending'
            }
            
            try:
                db.create_report(report_data)
                db.execute_query(
                    "UPDATE samples SET status = 'completed' WHERE id = ?",
                    (sample_id,)
                )
                success_count += 1
            except Exception as e:
                fail_count += 1
            
            time.sleep(0.1)
        
        try:
            db.commit()
        except Exception as e:
            QMessageBox.critical(self, "数据库错误", f"批量提交失败: {str(e)}")
            return
        
        QMessageBox.information(self, "批量生成完成",
            f"批量生成完成！\n成功：{success_count} 份\n失败：{fail_count} 份")
        
        self.loadDeafGeneSamples()
    
    def editDeafGeneReport(self):
        self.deaf_gene_preview_content.setReadOnly(False)
        QMessageBox.information(self, "提示", "现在可以编辑报告内容，编辑完成后点击保存")
    
    def addDeafGeneNote(self):
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
                current_content = self.deaf_gene_preview_content.toHtml()
                note_html = f"""
                <div style="margin-top: 30px; padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
                    <strong>备注：</strong>{note}
                </div>
                """
                self.deaf_gene_preview_content.setHtml(current_content + note_html)
    
    def exportDeafGenePdf(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存PDF报告", "", "PDF文件 (*.pdf)"
        )
        
        if not file_path:
            return
        
        if not file_path.endswith('.pdf'):
            file_path += '.pdf'
        
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.colors import HexColor
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            import os
            
            # 注册中文字体
            font_paths = [
                'C:/Windows/Fonts/simhei.ttf',
                'C:/Windows/Fonts/msyh.ttc',
                'C:/Windows/Fonts/simsun.ttc'
            ]
            
            chinese_font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        if font_path.endswith('.ttc'):
                            pdfmetrics.registerFont(TTFont('ChineseFont', font_path, subfontIndex=0))
                        else:
                            pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        chinese_font = 'ChineseFont'
                        break
                    except:
                        continue
            
            if not chinese_font:
                chinese_font = 'Helvetica'
            
            # 创建PDF文档
            doc = SimpleDocTemplate(file_path, pagesize=A4, 
                                   leftMargin=20*mm, rightMargin=20*mm,
                                   topMargin=20*mm, bottomMargin=20*mm)
            
            # 创建样式
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                        fontName=chinese_font, fontSize=18,
                                        alignment=TA_CENTER, textColor=HexColor('#333333'),
                                        spaceAfter=20)
            subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Heading2'],
                                          fontName=chinese_font, fontSize=14,
                                          alignment=TA_CENTER, textColor=HexColor('#666666'),
                                          spaceAfter=30)
            section_style = ParagraphStyle('CustomSection', parent=styles['Heading3'],
                                           fontName=chinese_font, fontSize=12,
                                           textColor=HexColor('#0078d4'),
                                           spaceAfter=10, spaceBefore=15)
            normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'],
                                         fontName=chinese_font, fontSize=10,
                                         textColor=HexColor('#333333'),
                                         leading=14)
            
            # 获取当前样本信息
            sample_info = None
            gene_data_list = []
            if self._deafGeneCurSampleId:
                cursor = db.execute_query("SELECT * FROM samples WHERE id = ?", (self._deafGeneCurSampleId,))
                row = cursor.fetchone()
                if row:
                    sample_info = dict(row)
                
                cursor = db.execute_query("SELECT * FROM gene_data WHERE sample_id = ?", (self._deafGeneCurSampleId,))
                gene_data_list = [dict(row) for row in cursor.fetchall()]
            
            # 获取模板数据
            template_data = None
            if self._deafGeneCurTemplate:
                template_data = db.get_report_template_by_code(self._deafGeneCurTemplate)
            
            if not template_data:
                template_data = db.get_default_template()
            
            template_name = template_data.get('template_name', REPORT_TEMPLATES.get(self._deafGeneCurTemplate, "临床诊断报告")) if template_data else REPORT_TEMPLATES.get(self._deafGeneCurTemplate, "临床诊断报告")
            hospital_name = template_data.get('hospital_name', '') if template_data else ''
            normal_interpretation = template_data.get('normal_interpretation', '') if template_data else ''
            abnormal_interpretation = template_data.get('abnormal_interpretation', '') if template_data else ''
            clinical_suggestions = template_data.get('clinical_suggestions', '') if template_data else ''
            tester_signature = template_data.get('tester_signature', '') if template_data else ''
            reviewer_signature = template_data.get('reviewer_signature', '') if template_data else ''
            seal_image = template_data.get('seal_image', '') if template_data else ''
            
            # 构建PDF内容
            story = []
            
            # 标题
            story.append(Paragraph("耳聋基因检测报告", title_style))
            story.append(Paragraph(template_name, subtitle_style))
            
            # 基本信息表格
            patient_name = sample_info.get('patient_name', '') if sample_info else ''
            gender = sample_info.get('gender', '') if sample_info else ''
            age = sample_info.get('age', '') if sample_info else ''
            clinical_diagnosis = sample_info.get('clinical_diagnosis', '') if sample_info else ''
            hospital = sample_info.get('hospital', '') if sample_info else ''
            report_no = self.deaf_gene_report_no_input.text() or '待生成'
            
            from datetime import datetime
            report_date = datetime.now().strftime('%Y-%m-%d')
            
            info_data = [
                ['报告编号', report_no, '送检单位', hospital or '待填写'],
                ['受检者姓名', patient_name, '性别', gender],
                ['年龄', age, '临床诊断', clinical_diagnosis],
                ['检测项目', '耳聋基因检测Panel', '报告日期', report_date]
            ]
            
            info_table = Table(info_data, colWidths=[70*mm, 55*mm, 70*mm, 55*mm])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#f8f9fa')),
                ('BACKGROUND', (2, 0), (2, -1), HexColor('#f8f9fa')),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dddddd')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 20))
            
            # 检测结果
            story.append(Paragraph("检测结果", section_style))
            
            has_mutation = any(gd.get('pathogenicity') in ['致病性', '可能致病性', '疑似致病', '异常'] for gd in gene_data_list)
            conclusion = "检测到致病变异" if has_mutation else "未检测到明确致病变异"
            
            # 基因检测结果表格
            gene_table_data = [['基因名称', '突变位点', '基因型', '致病性', '参考依据']]
            for gene_data in gene_data_list:
                gene_table_data.append([
                    gene_data.get('gene_name', ''),
                    gene_data.get('mutation_site', ''),
                    gene_data.get('genotype', ''),
                    gene_data.get('pathogenicity', ''),
                    gene_data.get('reference', '')
                ])
            
            if not gene_data_list:
                gene_table_data.append(['', '', '暂无检测数据', '', ''])
            
            col_widths = [35*mm, 40*mm, 35*mm, 35*mm, 45*mm]
            gene_table = Table(gene_table_data, colWidths=col_widths)
            gene_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#333333')),
                ('FONTNAME', (0, 0), (-1, 0), chinese_font),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOLD', (0, 0), (-1, 0), True),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dddddd')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            story.append(gene_table)
            story.append(Spacer(1, 10))
            
            # 检测结论
            conclusion_color = HexColor('#f44336') if has_mutation else HexColor('#4caf50')
            conclusion_style = ParagraphStyle('Conclusion', parent=normal_style,
                                               backColor=HexColor('#f8f9fa'),
                                               borderColor=conclusion_color,
                                               borderWidth=0,
                                               borderPadding=10)
            story.append(Paragraph(f"<b>检测结论：</b>{conclusion}", conclusion_style))
            story.append(Paragraph("注：此结果基于当前检测范围，如有疑问请咨询遗传咨询师。", 
                                  ParagraphStyle('Note', parent=normal_style, 
                                                fontSize=8, textColor=HexColor('#666666'))))
            
            story.append(Spacer(1, 20))
            
            # 结果解读
            story.append(Paragraph("结果解读", section_style))
            interpretation = abnormal_interpretation if has_mutation and abnormal_interpretation else (normal_interpretation if normal_interpretation else ("本次检测发现与耳聋相关的致病变异" if has_mutation else "本次检测未发现与耳聋相关的明确致病变异"))
            story.append(Paragraph(f"<b>遗传模式：</b>常染色体隐性遗传", normal_style))
            story.append(Paragraph(f"<b>致病性分析：</b>{interpretation}", normal_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>临床建议：</b>", normal_style))
            
            if clinical_suggestions:
                for line in clinical_suggestions.split('\n'):
                    if line.strip():
                        story.append(Paragraph(line.strip(), normal_style))
            elif has_mutation:
                story.append(Paragraph("1. 建议进行遗传咨询，了解疾病的遗传方式及再发风险", normal_style))
                story.append(Paragraph("2. 如有生育计划，建议夫妻双方进行基因检测", normal_style))
                story.append(Paragraph("3. 建议定期进行听力监测随访", normal_style))
            else:
                story.append(Paragraph("1. 目前未检测到明确的致病变异", normal_style))
                story.append(Paragraph("2. 如有家族史或临床症状持续，建议进一步咨询", normal_style))
            
            story.append(Spacer(1, 30))
            
            # 签名区域
            from PIL import Image
            import io
            import base64
            import tempfile
            import os
            
            temp_files = []
            
            def get_signature_image(base64_data, max_width=120, max_height=40):
                if not base64_data:
                    return None
                try:
                    image_data = base64.b64decode(base64_data)
                    img = Image.open(io.BytesIO(image_data))
                    
                    width, height = img.size
                    scale = min(max_width / width, max_height / height)
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                    img.save(temp_file.name, format='PNG')
                    temp_file.close()
                    temp_files.append(temp_file.name)
                    return temp_file.name
                except:
                    return None
            
            tester_img_path = get_signature_image(tester_signature, max_width=120, max_height=40)
            reviewer_img_path = get_signature_image(reviewer_signature, max_width=120, max_height=40)
            seal_img_path = get_signature_image(seal_image, max_width=80, max_height=80)
            
            signature_data = []
            
            tester_cell = Paragraph("检测医师：", normal_style)
            if tester_img_path:
                from reportlab.platypus import Image as RLImage
                tester_cell = RLImage(tester_img_path, width=35*mm, height=10*mm)
            
            reviewer_cell = Paragraph("审核医师：", normal_style)
            if reviewer_img_path:
                from reportlab.platypus import Image as RLImage
                reviewer_cell = RLImage(reviewer_img_path, width=35*mm, height=10*mm)
            
            signature_data.append([tester_cell, reviewer_cell, Paragraph("报告日期：" + report_date, normal_style)])
            
            if seal_img_path:
                from reportlab.platypus import Image as RLImage
                seal_cell = RLImage(seal_img_path, width=20*mm, height=20*mm)
            else:
                seal_cell = Paragraph("盖章：___________", normal_style)
            
            signature_data.append([Paragraph("", normal_style), seal_cell, Paragraph("", normal_style)])
            
            signature_table = Table(signature_data, colWidths=[65*mm, 65*mm, 60*mm])
            signature_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(signature_table)
            
            # 生成PDF
            doc.build(story)
            
            # 清理临时文件（必须在PDF构建完成后）
            for path in temp_files:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except:
                    pass
            
            QMessageBox.information(self, "成功", f"PDF报告已导出到:\n{file_path}")
            
        except ImportError:
            QMessageBox.critical(self, "失败", "缺少PDF生成库，请执行: pip install reportlab")
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "导出失败", f"PDF导出过程中发生错误: {str(e)}")
    
    def printDeafGeneReport(self):
        QMessageBox.information(self, "提示", "打印功能开发中...")
    
    def saveDeafGeneReport(self):
        if not self._deafGeneCurSampleId:
            QMessageBox.warning(self, "数据错误", "未选中样本")
            return
        
        try:
            db.execute_query(
                "UPDATE reports SET content = ? WHERE sample_id = ?",
                (self.deaf_gene_preview_content.toHtml(), self._deafGeneCurSampleId)
            )
            db.commit()
            
            self.deaf_gene_preview_content.setReadOnly(True)
            QMessageBox.information(self, "成功", "报告保存成功")
            
        except Exception as e:
            QMessageBox.critical(self, "数据库错误", f"保存失败: {str(e)}")
    
    def submitDeafGeneReview(self):
        if not self._deafGeneCurSampleId:
            QMessageBox.warning(self, "数据错误", "未选中样本")
            return
        
        reply = QMessageBox.question(
            self, '确认提交',
            '确定要提交报告进行审核吗？提交后将无法修改。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                db.execute_query(
                    "UPDATE reports SET status = 'pending' WHERE sample_id = ?",
                    (self._deafGeneCurSampleId,)
                )
                db.commit()
                
                QMessageBox.information(self, "成功", "报告已提交审核")
                
                self.deaf_gene_edit_btn.setEnabled(False)
                self.deaf_gene_note_btn.setEnabled(False)
                self.deaf_gene_save_btn.setEnabled(False)
                self.deaf_gene_submit_btn.setEnabled(False)
                
            except Exception as e:
                QMessageBox.critical(self, "数据库错误", f"提交失败: {str(e)}")
    
    def refreshDeafGeneData(self):
        self.loadDeafGeneSamples()
        self.loadDeafGeneTemplates()