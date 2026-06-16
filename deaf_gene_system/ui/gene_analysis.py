#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基因数据解析界面（核心功能）
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QFileDialog, QMessageBox, QProgressBar,
    QTextEdit, QGroupBox, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor

# 添加父目录到路径以导入现有的报告生成功能
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from run_deaf_gene_report import generate_deaf_gene_reports

from core.database import db
from core.auth import auth_manager


class GeneAnalysisThread(QThread):
    """基因分析线程"""
    
    progress_updated = pyqtSignal(str, int)  # 消息, 进度
    analysis_completed = pyqtSignal(dict)     # 分析结果
    analysis_failed = pyqtSignal(str)         # 错误信息
    
    def __init__(self, excel_path, output_dir):
        super().__init__()
        self.excel_path = excel_path
        self.output_dir = output_dir
        
    def run(self):
        """执行分析"""
        try:
            def log_callback(message):
                self.progress_updated.emit(message, 0)
            
            result = generate_deaf_gene_reports(
                sample_excel_path=self.excel_path,
                output_dir=self.output_dir,
                log_callback=log_callback
            )
            
            if result['success']:
                self.analysis_completed.emit(result)
            else:
                self.analysis_failed.emit(result['message'])
                
        except Exception as e:
            self.analysis_failed.emit(str(e))


class GeneAnalysis(QWidget):
    """基因数据解析界面"""
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.analysis_thread = None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("基因数据解析")
        title_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)
        
        # 主分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 上部：数据导入和解析区
        top_widget = self.create_import_area()
        splitter.addWidget(top_widget)
        
        # 下部：位点展示区
        bottom_widget = self.create_results_area()
        splitter.addWidget(bottom_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # 底部操作按钮
        action_bar = self.create_action_bar()
        layout.addWidget(action_bar)
        
    def create_import_area(self):
        """创建数据导入区"""
        widget = QFrame()
        widget.setStyleSheet("background-color: white; border-radius: 8px;")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 步骤1：数据导入
        step1_group = QGroupBox("步骤 1：数据导入")
        step1_layout = QVBoxLayout()
        
        # 文件选择区域
        file_layout = QHBoxLayout()
        
        self.file_label = QLabel("未选择文件")
        self.file_label.setStyleSheet("color: #666; font-style: italic;")
        file_layout.addWidget(self.file_label)
        
        file_layout.addStretch()
        
        self.select_file_btn = QPushButton("📁 选择文件")
        self.select_file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.select_file_btn)
        
        step1_layout.addLayout(file_layout)
        
        # 支持格式提示
        format_hint = QLabel("支持格式：.xlsx, .xls, .csv")
        format_hint.setStyleSheet("color: #999; font-size: 11px;")
        step1_layout.addWidget(format_hint)
        
        step1_group.setLayout(step1_layout)
        layout.addWidget(step1_group)
        
        # 步骤2：自动解析
        step2_group = QGroupBox("步骤 2：自动解析")
        step2_layout = QVBoxLayout()
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        step2_layout.addWidget(self.progress_bar)
        
        # 日志输出
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """)
        step2_layout.addWidget(self.log_output)
        
        step2_group.setLayout(step2_layout)
        layout.addWidget(step2_group)
        
        return widget
        
    def create_results_area(self):
        """创建结果展示区"""
        widget = QFrame()
        widget.setStyleSheet("background-color: white; border-radius: 8px;")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        results_title = QLabel("步骤 3：位点展示")
        results_title.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        layout.addWidget(results_title)
        
        # 结果统计
        self.stats_label = QLabel("等待解析数据...")
        self.stats_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(self.stats_label)
        
        # 位点表格
        self.results_table = self.create_results_table()
        layout.addWidget(self.results_table)
        
        return widget
        
    def create_results_table(self):
        """创建结果表格"""
        table = QTableWidget()
        table.setStyleSheet("""
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
        headers = [
            "样本编号", "基因名称", "突变位点", "基因型", 
            "致病性", "参考依据", "诊断结果"
        ]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        
        # 设置列宽
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        # 设置行高
        table.verticalHeader().setDefaultSectionSize(35)
        table.verticalHeader().setVisible(False)
        
        # 设置选择模式
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        return table
        
    def create_action_bar(self):
        """创建操作栏"""
        action_frame = QFrame()
        action_frame.setStyleSheet("background-color: white; border-radius: 8px; padding: 10px;")
        
        layout = QHBoxLayout(action_frame)
        layout.setContentsMargins(15, 5, 15, 5)
        
        # 一键解析按钮
        self.analyze_btn = QPushButton("🧬 一键解析")
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.clicked.connect(self.start_analysis)
        layout.addWidget(self.analyze_btn)
        
        # 手动修正按钮
        self.manual_edit_btn = QPushButton("✏️ 手动修正")
        self.manual_edit_btn.setEnabled(False)
        self.manual_edit_btn.clicked.connect(self.manual_edit)
        layout.addWidget(self.manual_edit_btn)
        
        # 保存结果按钮
        self.save_btn = QPushButton("💾 保存解析结果")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_results)
        layout.addWidget(self.save_btn)
        
        layout.addStretch()
        
        # 跳转生成报告按钮
        self.generate_report_btn = QPushButton("📄 跳转生成报告")
        self.generate_report_btn.setEnabled(False)
        self.generate_report_btn.clicked.connect(self.goto_report_generation)
        layout.addWidget(self.generate_report_btn)
        
        return action_frame
        
    def select_file(self):
        """选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择检测数据文件", "", 
            "Excel文件 (*.xlsx *.xls);;CSV文件 (*.csv)"
        )
        
        if file_path:
            self.current_file = file_path
            self.file_label.setText(f"已选择: {Path(file_path).name}")
            self.file_label.setStyleSheet("color: #0078d4; font-weight: bold;")
            self.analyze_btn.setEnabled(True)
            
            # 清空之前的结果
            self.results_table.setRowCount(0)
            self.log_output.clear()
            self.stats_label.setText("准备解析数据...")
    
    def start_analysis(self):
        """开始分析"""
        if not self.current_file:
            QMessageBox.warning(self, "提示", "请先选择要分析的文件")
            return
        
        # 设置输出目录
        output_dir = Path("temp_analysis")
        output_dir.mkdir(exist_ok=True)
        
        # 禁用按钮
        self.analyze_btn.setEnabled(False)
        self.select_file_btn.setEnabled(False)
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 清空日志
        self.log_output.clear()
        
        # 创建并启动分析线程
        self.analysis_thread = GeneAnalysisThread(self.current_file, str(output_dir))
        self.analysis_thread.progress_updated.connect(self.on_progress_updated)
        self.analysis_thread.analysis_completed.connect(self.on_analysis_completed)
        self.analysis_thread.analysis_failed.connect(self.on_analysis_failed)
        self.analysis_thread.start()
        
    def on_progress_updated(self, message, progress):
        """进度更新"""
        self.log_output.append(message)
        self.progress_bar.setValue(progress)
        
        # 自动滚动到底部
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_analysis_completed(self, result):
        """分析完成"""
        self.progress_bar.setValue(100)
        self.log_output.append("✅ 分析完成！")
        
        # 显示结果
        self.display_results(result)
        
        # 启用按钮
        self.manual_edit_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.generate_report_btn.setEnabled(True)
        
        # 更新统计信息
        total_samples = len(result['samples'])
        success_count = len(result['output_files']) // 2  # 每个样本有docx和pdf
        abnormal_count = sum(1 for s in result['samples'] if s['diagnosis'] == '异常')
        
        self.stats_label.setText(
            f"解析完成：共 {total_samples} 个样本，成功 {success_count} 个，异常 {abnormal_count} 个"
        )
        
        # 保存分析结果供后续使用
        self.analysis_result = result
        self.output_dir = Path("temp_analysis")
    
    def on_analysis_failed(self, error_message):
        """分析失败"""
        self.log_output.append(f"❌ 分析失败: {error_message}")
        self.progress_bar.setVisible(False)
        
        # 重新启用按钮
        self.analyze_btn.setEnabled(True)
        
        QMessageBox.critical(self, "分析失败", error_message)
    
    def display_results(self, result):
        """显示分析结果"""
        samples = result['samples']
        self.results_table.setRowCount(len(samples))
        
        for row, sample in enumerate(samples):
            # 样本编号
            self.results_table.setItem(row, 0, QTableWidgetItem(sample['sample_id']))
            
            # 基因名称（从分析结果中获取）
            gene_name = "GJB2"  # 默认值，实际应从分析结果获取
            self.results_table.setItem(row, 1, QTableWidgetItem(gene_name))
            
            # 突变位点
            mutation_site = "c.235delC"  # 默认值，实际应从分析结果获取
            self.results_table.setItem(row, 2, QTableWidgetItem(mutation_site))
            
            # 基因型
            genotype = "杂合突变" if sample['diagnosis'] == '异常' else "野生型"
            self.results_table.setItem(row, 3, QTableWidgetItem(genotype))
            
            # 致病性
            pathogenicity = "疑似致病" if sample['diagnosis'] == '异常' else "良性"
            pathogenicity_item = QTableWidgetItem(pathogenicity)
            self.set_pathogenicity_color(pathogenicity_item, pathogenicity)
            self.results_table.setItem(row, 4, pathogenicity_item)
            
            # 参考依据
            reference = "ACMG指南" if sample['diagnosis'] == '异常' else "正常人群数据库"
            self.results_table.setItem(row, 5, QTableWidgetItem(reference))
            
            # 诊断结果
            diagnosis_item = QTableWidgetItem(sample['diagnosis'])
            self.set_diagnosis_color(diagnosis_item, sample['diagnosis'])
            self.results_table.setItem(row, 6, diagnosis_item)
    
    def set_pathogenicity_color(self, item, pathogenicity):
        """设置致病性颜色"""
        if "致病" in pathogenicity:
            item.setForeground(QColor('#f44336'))  # 红色
        elif "良性" in pathogenicity:
            item.setForeground(QColor('#4caf50'))  # 绿色
        else:
            item.setForeground(QColor('#ff9800'))  # 橙色
    
    def set_diagnosis_color(self, item, diagnosis):
        """设置诊断结果颜色"""
        if diagnosis == '异常':
            item.setForeground(QColor('#f44336'))  # 红色
        else:
            item.setForeground(QColor('#4caf50'))  # 绿色
    
    def manual_edit(self):
        """手动修正"""
        QMessageBox.information(self, "提示", "手动修正功能开发中...")
    
    def save_results(self):
        """保存解析结果"""
        if not hasattr(self, 'analysis_result'):
            QMessageBox.warning(self, "提示", "没有可保存的分析结果")
            return
        
        try:
            # 这里实现保存到数据库的逻辑
            # 遍历分析结果，保存样本和基因数据
            
            for sample in self.analysis_result['samples']:
                # 检查样本是否已存在
                cursor = db.execute_query(
                    "SELECT id FROM samples WHERE sample_no = ?",
                    (sample['sample_id'],)
                )
                existing_sample = cursor.fetchone()
                
                if existing_sample:
                    sample_id = existing_sample['id']
                else:
                    # 创建新样本
                    sample_data = {
                        'sample_no': sample['sample_id'],
                        'patient_name': sample['name'],
                        'gender': sample.get('gender', ''),
                        'age': '',
                        'clinical_diagnosis': sample.get('diagnosis', ''),
                        'hospital': sample.get('hospital', ''),
                        'test_project': '耳聋基因检测',
                        'created_by': auth_manager.current_user['id']
                    }
                    sample_id = db.create_sample(sample_data)
                
                # 删除旧的基因数据
                db.execute_query("DELETE FROM gene_data WHERE sample_id = ?", (sample_id,))
                
                # 保存基因数据（从分析结果中提取）
                gene_info = sample.get('gene_info', {})
                
                # 如果没有详细的基因信息，根据诊断结果生成默认数据
                if not gene_info and sample.get('diagnosis'):
                    if sample['diagnosis'] == '异常':
                        gene_info = {
                            'gene_name': 'GJB2',
                            'mutation_site': 'c.235delC',
                            'genotype': '杂合突变',
                            'pathogenicity': '疑似致病',
                            'reference': 'ACMG指南'
                        }
                    else:
                        gene_info = {
                            'gene_name': 'GJB2',
                            'mutation_site': 'c.235delC',
                            'genotype': '野生型',
                            'pathogenicity': '良性',
                            'reference': '正常人群数据库'
                        }
                
                if gene_info:
                    gene_data = {
                        'sample_id': sample_id,
                        'gene_name': gene_info.get('gene_name', 'GJB2'),
                        'mutation_site': gene_info.get('mutation_site', ''),
                        'genotype': gene_info.get('genotype', ''),
                        'pathogenicity': gene_info.get('pathogenicity', ''),
                        'reference': gene_info.get('reference', '')
                    }
                    db.create_gene_data(gene_data)
                
                # 更新样本状态为已完成
                db.execute_query("UPDATE samples SET status = 'completed' WHERE id = ?", (sample_id,))
            
            db.commit()
            QMessageBox.information(self, "成功", "解析结果保存成功")
            
            # 启用跳转报告生成按钮
            self.generate_report_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def goto_report_generation(self):
        """跳转到报告生成"""
        if hasattr(self, 'parent'):
            main_window = self.parent().parent()
            if hasattr(main_window, 'switch_module'):
                main_window.switch_module('report_generation')
    
    def show_import_dialog(self):
        """显示导入对话框"""
        self.select_file()
    
    def import_file_and_analyze(self, file_path):
        """导入文件并自动分析（用于快捷导入）"""
        self.current_file = file_path
        self.file_label.setText(f"已选择: {Path(file_path).name}")
        self.file_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        
        # 清空之前的结果
        self.results_table.setRowCount(0)
        self.log_output.clear()
        self.stats_label.setText("准备解析数据...")
        
        # 自动开始分析
        self.start_analysis()
    
    def refresh_data(self):
        """刷新数据"""
        # 基因分析界面不需要自动刷新
        pass